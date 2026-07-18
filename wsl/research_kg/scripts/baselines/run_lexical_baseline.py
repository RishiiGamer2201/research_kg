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

import numpy as np
import scipy.sparse as sp

LANGS = ["en", "fr", "es", "ja", "el"]
K1, B = 1.5, 0.75
SAMPLE_SEED = 20260718


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

    # per-language candidate side
    state = {}
    for l, ids in by_lang.items():
        idx = {g: i for i, g in enumerate(ids)}
        if method == "name_match":
            texts = [name.get(g, "") for g in ids]
            M, vocab, lens = _build_matrices(texts)
            state[l] = (ids, idx, M.T.tocsr(), vocab, lens)      # binary V x C
        else:
            texts = [desc.get(g, "") for g in ids]
            _, vocab, _ = _build_matrices(texts)
            W = _bm25_weights(texts, vocab)
            state[l] = (ids, idx, W.T.tocsr(), vocab, None)      # weights V x C

    out = {d: [] for d in ("tail", "head")}
    mention = {d: {"mentioned": [], "unmentioned": []} for d in ("tail", "head")}
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
            m = _metrics(_ranks(scores, idx[ans], mask))
            out[direction].append(m)
            an = name.get(ans, "")
            mentioned = len(an) >= 3 and an in desc.get(q_ent, "")
            mention[direction]["mentioned" if mentioned else "unmentioned"].append(m)

    res = {d: _agg(out[d], ci=sampled) for d in ("tail", "head")}
    res["combined"] = _agg(out["tail"] + out["head"], ci=sampled)
    res["by_mention"] = {d: {b: _agg(mention[d][b], ci=sampled) for b in ("mentioned", "unmentioned")}
                         for d in ("tail", "head")}
    res["sampled"] = sampled
    res["n_targets"] = len(targets)
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
        print("run_lexical_baseline self-check OK (vectorized; rank identity verified)")
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
    ap.add_argument("--out", default="DBP5L/ind_v2/audits/lexical_baselines_full.json")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selfcheck(); sys.exit(0)

    views = {
        "natural": "DBP5L/ind_v2/tracks/descriptions_v2_primary.json",
        "masked": "DBP5L/ind_v2/tracks/descriptions_v2_masked.json",
        "missing": "DBP5L/ind_v2/tracks/descriptions_v2_missing_text.json",
    }
    out = {"built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "max_targets_per_fold": args.max_targets or "full", "results": {}}
    for fold in args.folds.split(","):
        for method in args.methods.split(","):
            for vname, vrel in views.items():
                t0 = time.time()
                r = run(args.root, fold, os.path.join(args.root, vrel), method,
                        args.max_targets or None)
                out["results"].setdefault(fold, {}).setdefault(method, {})[vname] = r
                bm = r["by_mention"]
                print(f"[{fold}/{method}/{vname}] n={r['n_targets']} combined={r['combined']['mrr']:.3f} "
                      f"| tail {r['tail']['mrr']:.3f} (m {bm['tail']['mentioned']['mrr']:.2f}/"
                      f"u {bm['tail']['unmentioned']['mrr']:.2f}) "
                      f"| head {r['head']['mrr']:.3f} (m {bm['head']['mentioned']['mrr']:.2f}/"
                      f"u {bm['head']['unmentioned']['mrr']:.2f}) [{time.time()-t0:.0f}s]", flush=True)
    p = os.path.join(args.root, args.out)
    json.dump(out, open(p, "w"), indent=2, sort_keys=True)
    print("wrote", p)
