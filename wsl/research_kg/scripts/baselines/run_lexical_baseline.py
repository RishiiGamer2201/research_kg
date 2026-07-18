"""Phase 2 / P2.1 — lexical baselines on DBP5L-Ind v2 (CPU, vectorized, FULL target set).

Two lexical scorers, ranking within-language candidates under the frozen protocol: v2 fold
eval targets, complete known-fact filter, average tied ranks, head + tail + combined reported
separately, and split by mentioned/unmentioned.

  name_match : Jaccard(query-description tokens, candidate NAME tokens).
               A pure answer-mention detector (see ledger R-041/R-042) — NOT a retrieval model.
  bm25       : Okapi BM25 over candidate DESCRIPTIONS. A genuine lexical retrieval expert.

Scoring is vectorized with scipy sparse matmuls so the FULL target set is affordable
(the earlier loop implementation forced sub-sampling, which biased the mention rates).

Views: natural (primary), alias-masked, missing-text.

Self-check: `python3 run_lexical_baseline.py --selftest`.
"""
import os
import sys
import json
import time
import argparse
import unicodedata
from collections import defaultdict

import hashlib

import numpy as np
import scipy.sparse as sp

LANGS = ["en", "fr", "es", "ja", "el"]
K1, B = 1.5, 0.75
SAMPLE_SEED = 20260718
QUERY_BATCH = 1                      # queries scored per sparse matmul (see provenance)
TIE_POLICY = "average-tied-ranks: rank = n_> + (n_= + 1)/2, gold included in n_="
TOKENIZER = "NFC-normalize -> lowercase -> whitespace split"


TOLERANT_DECIMALS = 9        # rounding used for the tolerance-friendly hash


def _canonical_csr(M):
    """CSR in canonical form so equivalent matrices hash identically."""
    M = M.tocsr().copy()
    M.sum_duplicates()      # merge duplicate entries
    M.sort_indices()        # deterministic column order within each row
    M.eliminate_zeros()     # explicit zeros must not change the hash
    return M


def _hash_sparse(M, decimals=None):
    """Content hash of a CSR matrix over its EXACT canonical bytes.

    Pins shape, dtypes, byte order, indptr, indices and data. `decimals=None` hashes the raw
    data bytes (exact, detects any scoring drift); passing an int hashes rounded values
    instead (tolerant of cross-platform floating-point noise) and the precision is recorded
    alongside the digest by the caller.
    """
    M = _canonical_csr(M)
    data = M.data if decimals is None else np.round(M.data, decimals)
    # normalize endianness so the digest is comparable across platforms
    def _b(a):
        a = np.ascontiguousarray(a)
        if a.dtype.byteorder == ">" or (a.dtype.byteorder == "=" and sys.byteorder == "big"):
            a = a.astype(a.dtype.newbyteorder("<"))
        return a
    h = hashlib.sha256()
    h.update(json.dumps({
        "shape": list(M.shape), "nnz": int(M.nnz),
        "dtype_data": str(_b(data).dtype), "dtype_indices": str(_b(M.indices).dtype),
        "dtype_indptr": str(_b(M.indptr).dtype), "byteorder": "little",
        "rounded_decimals": decimals,
    }, sort_keys=True).encode())
    for arr in (M.indptr, M.indices, data):
        h.update(_b(arr).tobytes())
    return h.hexdigest()[:16]


def _hash_list(xs):
    return hashlib.sha256(json.dumps(list(xs), sort_keys=True).encode()).hexdigest()[:16]


def _norm(s):
    return " ".join(unicodedata.normalize("NFC", (s or "")).lower().split())


def _build_matrices(texts, vocab=None):
    """binary doc-term CSR + token counts. texts: list[str]."""
    if vocab is None:
        vocab = {}
        for t in texts:
            for w in set(t.split()):
                vocab.setdefault(w, len(vocab))
    rows, cols = [], []
    lens = np.zeros(len(texts), dtype=np.float64)
    for i, t in enumerate(texts):
        ws = t.split()
        lens[i] = len(ws)
        for w in set(ws):
            j = vocab.get(w)
            if j is not None:
                rows.append(i); cols.append(j)
    M = sp.csr_matrix((np.ones(len(rows), dtype=np.float64), (rows, cols)),
                      shape=(len(texts), max(len(vocab), 1)))
    return M, vocab, lens


def _bm25_weights(texts, vocab):
    """candidate-side BM25 weight matrix (docs x vocab)."""
    rows, cols, vals = [], [], []
    dl = np.array([len(t.split()) for t in texts], dtype=np.float64)
    avgdl = dl.mean() if len(dl) else 1.0
    N = len(texts)
    df = np.zeros(max(len(vocab), 1), dtype=np.float64)
    tfs = []
    for t in texts:
        c = defaultdict(int)
        for w in t.split():
            j = vocab.get(w)
            if j is not None:
                c[j] += 1
        tfs.append(c)
        for j in c:
            df[j] += 1
    idf = np.log(1 + (N - df + 0.5) / (df + 0.5))
    for i, c in enumerate(tfs):
        for j, f in c.items():
            w = idf[j] * f * (K1 + 1) / (f + K1 * (1 - B + B * (dl[i] / (avgdl or 1.0))))
            rows.append(i); cols.append(j); vals.append(w)
    return sp.csr_matrix((vals, (rows, cols)), shape=(N, max(len(vocab), 1)))


def _ranks(scores, gold_idx, filtered_mask):
    """Average tied rank, mirroring eval_dbp5l: rank = n_> + (n_= + 1)/2 with gold in n_=."""
    s = scores.copy()
    s[filtered_mask] = -np.inf
    gs = s[gold_idx]
    n_gt = int(np.sum(s > gs))
    n_eq = int(np.sum(s == gs))          # includes gold
    return n_gt + (n_eq + 1) / 2.0


def _metrics(rank):
    return {"mrr": 1.0 / rank, "h1": int(rank <= 1), "h3": int(rank <= 3), "h10": int(rank <= 10)}


def _agg(rows, ci=True):
    n = len(rows)
    if n == 0:
        return {"n": 0, "mrr": 0.0, "h1": 0.0, "h3": 0.0, "h10": 0.0}
    out = {"n": n, **{k: round(100 * sum(r[k] for r in rows) / n, 4)
                      for k in ("mrr", "h1", "h3", "h10")}}
    if ci:  # normal-approx 95% CI on MRR (only meaningful if sampling was used)
        v = np.array([r["mrr"] for r in rows], dtype=np.float64)
        out["mrr_ci95"] = round(100 * 1.96 * v.std(ddof=1) / np.sqrt(n), 4) if n > 1 else 0.0
    return out


def run(root, fold, view_path, method, max_targets=None):
    proc = os.path.join(root, "DBP5L/processed")
    ents = {int(g): e for g, e in json.load(open(os.path.join(proc, "entities.json"))).items()}
    desc = {int(g): _norm(v) for g, v in json.load(open(view_path)).items()}
    name = {g: _norm(e.get("name") or "") for g, e in ents.items()}
    fdir = os.path.join(root, "DBP5L/ind_v2/folds", fold)
    targets = [tuple(x) for x in json.load(open(os.path.join(fdir, "budgets/eval_targets_test.json")))]
    sampled = False
    if max_targets and len(targets) > max_targets:
        import random as _r
        targets = _r.Random(SAMPLE_SEED).sample(targets, max_targets)
        sampled = True

    fwd, rev = defaultdict(set), defaultdict(set)
    for split in ("train", "valid", "test"):
        p = os.path.join(proc, f"{split}.json")
        if os.path.exists(p):
            for line in open(p):
                d = json.loads(line)
                fwd[(d["h"], d["r"])].add(d["t"]); rev[(d["r"], d["t"])].add(d["h"])

    by_lang = defaultdict(list)
    for g, e in ents.items():
        by_lang[e["lang"]].append(g)
    for l in by_lang:
        by_lang[l].sort()

    # per-language candidate side (+ provenance so batching/vocab changes are detectable)
    state = {}
    prov_lang = {}
    for l, ids in by_lang.items():
        idx = {g: i for i, g in enumerate(ids)}
        if method == "name_match":
            texts = [name.get(g, "") for g in ids]
            M, vocab, lens = _build_matrices(texts)
            CT = M.T.tocsr()
            state[l] = (ids, idx, CT, vocab, lens)               # binary V x C
        else:
            texts = [desc.get(g, "") for g in ids]
            _, vocab, _ = _build_matrices(texts)
            W = _bm25_weights(texts, vocab)
            CT = W.T.tocsr()
            state[l] = (ids, idx, CT, vocab, None)               # weights V x C
        prov_lang[l] = {
            "n_candidates": len(ids),
            "candidate_order_hash": _hash_list(ids),
            "vocab_size": len(vocab),
            "vocab_hash": _hash_list(sorted(vocab)),
            # exact = raw canonical bytes (catches any scoring drift);
            # tolerant = rounded, for cross-platform float noise. Precision recorded.
            "sparse_matrix_exact_hash": _hash_sparse(CT),
            "sparse_matrix_tolerant_hash": _hash_sparse(CT, decimals=TOLERANT_DECIMALS),
            "sparse_matrix_tolerant_decimals": TOLERANT_DECIMALS,
        }

    out = {d: [] for d in ("tail", "head")}
    mention = {d: {"mentioned": [], "unmentioned": []} for d in ("tail", "head")}
    rank_rows = []          # per-query records, schema-matched to eval_dbp5l --dump-ranks
    for (h, r, t) in targets:
        for direction in ("tail", "head"):
            q_ent, ans = (h, t) if direction == "tail" else (t, h)
            if ans not in ents or q_ent not in ents:
                continue
            lang = ents[ans]["lang"]
            if ents[q_ent]["lang"] != lang:
                continue
            ids, idx, CT, vocab, cand_lens = state[lang]
            qtok = set(desc.get(q_ent, "").split())
            cols = [vocab[w] for w in qtok if w in vocab]
            if cols:
                qv = sp.csr_matrix((np.ones(len(cols)), (np.zeros(len(cols)), cols)),
                                   shape=(1, CT.shape[0]))
                inter = np.asarray((qv @ CT).todense()).ravel()
            else:
                inter = np.zeros(len(ids))
            if method == "name_match":
                union = len(qtok) + cand_lens - inter
                scores = np.divide(inter, np.maximum(union, 1e-9))
            else:
                scores = inter                                   # BM25 weights already applied
            known = fwd.get((h, r), set()) if direction == "tail" else rev.get((r, t), set())
            mask = np.zeros(len(ids), dtype=bool)
            for k in known:
                if k in idx and k != ans:
                    mask[idx[k]] = True
            rk = _ranks(scores, idx[ans], mask)
            m = _metrics(rk)
            out[direction].append(m)
            an = name.get(ans, "")
            mentioned = len(an) >= 3 and an in desc.get(q_ent, "")
            mention[direction]["mentioned" if mentioned else "unmentioned"].append(m)
            rank_rows.append({"h": h, "r": r, "t": t, "lang": lang, "direction": direction,
                              "mentioned": bool(mentioned), "rank": rk, "rr": m["mrr"]})

    res = {d: _agg(out[d], ci=sampled) for d in ("tail", "head")}
    res["combined"] = _agg(out["tail"] + out["head"], ci=sampled)
    res["by_mention"] = {d: {b: _agg(mention[d][b], ci=sampled) for b in ("mentioned", "unmentioned")}
                         for d in ("tail", "head")}
    res["sampled"] = sampled
    res["n_targets"] = len(targets)
    res["rank_rows"] = rank_rows            # per-query RRs for paired bootstrap comparison
    # Reproducibility provenance: batching, matrix/vocab/candidate-order hashes and the tie
    # policy, so a change in batching or tokenization cannot silently alter rankings.
    res["provenance"] = {
        "query_batch_size": QUERY_BATCH,
        "scoring": "scipy.sparse CSR matmul (query binary vector x candidate matrix)",
        "tokenizer": TOKENIZER,
        "tie_policy": TIE_POLICY,
        "bm25_k1": K1, "bm25_b": B,
        "filter": "complete known-fact filter (train+valid+test), direction-specific",
        "view_hash": hashlib.sha256(open(view_path, "rb").read()).hexdigest()[:16],
        "targets_hash": _hash_list(sorted(map(list, targets))),
        "sample_seed": (SAMPLE_SEED if sampled else None),
        "per_language": prov_lang,
    }
    return res


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="lex_test_")
    try:
        proc = os.path.join(d, "DBP5L/processed"); os.makedirs(proc)
        fdir = os.path.join(d, "DBP5L/ind_v2/folds/f0/budgets"); os.makedirs(fdir)
        ents = {"0": {"lang": "en", "name": "Alan Turing"}, "1": {"lang": "en", "name": "Cambridge"},
                "2": {"lang": "en", "name": "Zebra"}}
        view = {"0": "studied at cambridge", "1": "a city", "2": "an animal"}
        json.dump(ents, open(os.path.join(proc, "entities.json"), "w"))
        vp = os.path.join(d, "view.json"); json.dump(view, open(vp, "w"))
        with open(os.path.join(proc, "train.json"), "w") as f:
            f.write(json.dumps({"h": 0, "r": 9, "t": 1}) + "\n")
        json.dump([[0, 9, 1]], open(os.path.join(fdir, "eval_targets_test.json"), "w"))
        r = run(d, "f0", vp, "name_match")
        assert r["tail"]["n"] == 1 and r["tail"]["mrr"] == 100.0, r["tail"]
        assert r["by_mention"]["tail"]["mentioned"]["n"] == 1, r["by_mention"]
        assert r["sampled"] is False and r["n_targets"] == 1
        # rank identity: no ties, nothing higher -> rank 1
        s = np.array([0.1, 0.9, 0.5]); m = np.zeros(3, dtype=bool)
        assert _ranks(s, 1, m) == 1.0
        # all tied -> averaged rank (3+1)/2 = 2
        assert _ranks(np.array([0.5, 0.5, 0.5]), 0, m) == 2.0
        # filtering removes a higher competitor
        assert _ranks(np.array([0.9, 0.5, 0.1]), 1, np.array([True, False, False])) == 1.0
        rb = run(d, "f0", vp, "bm25")
        assert rb["tail"]["n"] == 1
        # provenance present and sensitive to a view/vocabulary change
        pv = r["provenance"]
        for k in ("query_batch_size", "tokenizer", "tie_policy", "view_hash",
                  "targets_hash", "per_language"):
            assert k in pv, k
        assert pv["per_language"]["en"]["candidate_order_hash"] and \
               pv["per_language"]["en"]["sparse_matrix_exact_hash"] and \
               pv["per_language"]["en"]["sparse_matrix_tolerant_hash"] and \
               pv["per_language"]["en"]["vocab_hash"]
        # EXACT hash must catch drift far below the tolerant rounding precision;
        # the tolerant hash is allowed to absorb it.
        A = sp.csr_matrix(np.array([[1.0, 0.0], [0.0, 2.0]]))
        Bm = A.copy(); Bm.data = Bm.data + 1e-12
        assert _hash_sparse(A) != _hash_sparse(Bm), "exact hash missed sub-epsilon drift"
        assert _hash_sparse(A, TOLERANT_DECIMALS) == _hash_sparse(Bm, TOLERANT_DECIMALS)
        # canonicalization: explicit zeros / duplicate entries must not change the digest
        C = sp.csr_matrix((np.array([1.0, 0.0, 2.0]),
                           (np.array([0, 0, 1]), np.array([0, 1, 1]))), shape=(2, 2))
        assert _hash_sparse(C) == _hash_sparse(A), "canonical form not stable"
        # a real value change must move BOTH hashes
        D = A.copy(); D.data = D.data * 2
        assert _hash_sparse(D) != _hash_sparse(A)
        assert _hash_sparse(D, TOLERANT_DECIMALS) != _hash_sparse(A, TOLERANT_DECIMALS)
        json.dump({"0": "studied at oxford", "1": "a city", "2": "an animal"}, open(vp, "w"))
        pv2 = run(d, "f0", vp, "name_match")["provenance"]
        assert pv2["view_hash"] != pv["view_hash"], "view change must change view_hash"
        # bm25 matrix is built from descriptions -> its hash must move with the view
        pvb = run(d, "f0", vp, "bm25")["provenance"]["per_language"]["en"]
        assert pvb["vocab_hash"] != rb["provenance"]["per_language"]["en"]["vocab_hash"], \
            "vocabulary hash must change when the description view changes"
        print("run_lexical_baseline self-check OK (vectorized; rank identity + provenance verified)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("RESEARCH_KG_ROOT",
                                                     os.path.expanduser("~/research_kg")))
    ap.add_argument("--folds", default="fold0_seed13,fold1_seed42,fold2_seed79")
    ap.add_argument("--methods", default="name_match,bm25")
    ap.add_argument("--max-targets", type=int, default=0,
                    help="0 = FULL target set (default); >0 = deterministic random sample")
    ap.add_argument("--out-dir", default="DBP5L/ind_v2/audits/lexical/LEX-RUN-002",
                    help="run-scoped output dir; each cell is written atomically as it "
                         "completes, plus a resumable completion index")
    ap.add_argument("--resume", action="store_true",
                    help="skip cells already present in the completion index")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selfcheck(); sys.exit(0)

    views = {
        "natural": "DBP5L/ind_v2/tracks/descriptions_v2_primary.json",
        "masked": "DBP5L/ind_v2/tracks/descriptions_v2_masked.json",
        "missing": "DBP5L/ind_v2/tracks/descriptions_v2_missing_text.json",
    }
    # Run-scoped output: each cell written atomically as it completes + a resumable index, so an
    # end-of-run failure can never discard already-valid cells (see failed run LEX-RUN-001).
    out_dir = os.path.join(args.root, args.out_dir)
    cells_dir = os.path.join(out_dir, "cells")
    os.makedirs(cells_dir, exist_ok=True)
    index_path = os.path.join(out_dir, "completion_index.json")

    def _atomic_write(path, obj):
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)

    index = {"cells": {}, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if args.resume and os.path.exists(index_path):
        index = json.load(open(index_path))
        print(f"resuming: {len(index['cells'])} cell(s) already complete", flush=True)

    for fold in args.folds.split(","):
        for method in args.methods.split(","):
            for vname, vrel in views.items():
                key = f"{fold}__{method}__{vname}"
                cell_path = os.path.join(cells_dir, key + ".json")
                if args.resume and key in index["cells"] and os.path.exists(cell_path):
                    print(f"[{key}] skipped (already complete)", flush=True)
                    continue
                t0 = time.time()
                r = run(args.root, fold, os.path.join(args.root, vrel), method,
                        args.max_targets or None)
                r["cell"] = {"fold": fold, "method": method, "view": vname,
                             "seconds": round(time.time() - t0, 1),
                             "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                # per-query ranks go to their own file so cells stay small; the cell keeps the path
                ranks_dir = os.path.join(out_dir, "ranks"); os.makedirs(ranks_dir, exist_ok=True)
                ranks_path = os.path.join(ranks_dir, key + ".json")
                _atomic_write(ranks_path, r.pop("rank_rows"))
                r["rank_dump"] = os.path.relpath(ranks_path, out_dir)
                _atomic_write(cell_path, r)                      # cell is durable from here on
                index["cells"][key] = {"path": os.path.relpath(cell_path, out_dir),
                                       "combined_mrr": r["combined"]["mrr"],
                                       "n_targets": r["n_targets"],
                                       "completed_utc": r["cell"]["completed_utc"]}
                index["updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                _atomic_write(index_path, index)                 # index updated after the cell
                bm = r["by_mention"]
                print(f"[{key}] n={r['n_targets']} combined={r['combined']['mrr']:.3f} "
                      f"| tail {r['tail']['mrr']:.3f} (m {bm['tail']['mentioned']['mrr']:.2f}/"
                      f"u {bm['tail']['unmentioned']['mrr']:.2f}) "
                      f"| head {r['head']['mrr']:.3f} (m {bm['head']['mentioned']['mrr']:.2f}/"
                      f"u {bm['head']['unmentioned']['mrr']:.2f}) [{r['cell']['seconds']:.0f}s]",
                      flush=True)

    # aggregate view (convenience only — the cells + index are the source of truth)
    agg = {"built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "max_targets_per_fold": args.max_targets or "full", "results": {}}
    for key, meta in sorted(index["cells"].items()):
        fold, method, vname = key.split("__")
        agg["results"].setdefault(fold, {}).setdefault(method, {})[vname] = \
            json.load(open(os.path.join(out_dir, meta["path"])))
    _atomic_write(os.path.join(out_dir, "results.json"), agg)
    print("wrote", os.path.join(out_dir, "results.json"),
          f"({len(index['cells'])} cells)")
