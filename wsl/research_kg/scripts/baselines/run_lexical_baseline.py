"""Phase 2 / P2.1 — cheap lexical baselines on DBP5L-Ind v2 (CPU only).

Two lexical scorers, both ranking within-language candidates under the SAME protocol as the
neural baselines (frozen matrix): v2 fold eval targets, complete known-fact filter, average
tied ranks, head + tail + combined reported separately.

  name_match : score = token overlap (Jaccard) between the query description and the
               candidate's NAME. This is the pure "answer-mention reading" baseline.
  bm25       : Okapi BM25 over candidate descriptions, query = query-entity description.

Run on all four description views so the answer-mention effect is visible:
  natural (primary), masked (alias-masked), missing (name-only)  [+ mentioned/unmentioned
  split on the natural view].

Cost: minutes on CPU. No GPU, no training.

Self-check: `python3 run_lexical_baseline.py --selftest`.
"""
import os
import sys
import json
import math
import time
import argparse
import unicodedata
from collections import defaultdict, Counter

LANGS = ["en", "fr", "es", "ja", "el"]
K1, B = 1.5, 0.75


def _norm(s):
    return " ".join(unicodedata.normalize("NFC", (s or "")).lower().split())


def _toks(s):
    return _norm(s).split()


def _avg_rank(scores, true_idx, filtered):
    """Average tied rank of true_idx, skipping `filtered` indices.
    Mirrors eval_dbp5l.compute_filtered_metrics exactly: `ties` INCLUDES the true entity,
    so rank = higher + (ties+1)/2 (== higher+1 when nothing ties with it)."""
    ts = scores[true_idx]
    higher = ties = 0
    for i, s in enumerate(scores):
        if i in filtered:
            continue
        if s > ts:
            higher += 1
        elif s == ts:
            ties += 1          # includes true_idx itself
    return higher + (ties + 1) / 2.0


def _metrics(rank):
    return {"mrr": 1.0 / rank, "h1": int(rank <= 1), "h3": int(rank <= 3), "h10": int(rank <= 10)}


def _agg(rows):
    n = len(rows)
    if n == 0:
        return {"n": 0, "mrr": 0.0, "h1": 0.0, "h3": 0.0, "h10": 0.0}
    return {"n": n, **{k: round(100 * sum(r[k] for r in rows) / n, 4)
                       for k in ("mrr", "h1", "h3", "h10")}}


def run(root, fold, view_path, method, max_targets=None):
    proc = os.path.join(root, "DBP5L/processed")
    ents = {int(g): e for g, e in json.load(open(os.path.join(proc, "entities.json"))).items()}
    desc = {int(g): _norm(v) for g, v in json.load(open(view_path)).items()}
    name = {g: _norm(e.get("name") or "") for g, e in ents.items()}
    fdir = os.path.join(root, "DBP5L/ind_v2/folds", fold)
    targets = [tuple(x) for x in json.load(open(os.path.join(fdir, "budgets/eval_targets_test.json")))]
    if max_targets:
        targets = targets[:max_targets]

    # complete known-fact filter (identical to the neural protocol)
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

    # BM25 stats per language over candidate descriptions
    bm25_state = {}
    if method == "bm25":
        for l, ids in by_lang.items():
            df = Counter()
            docs, dl = {}, {}
            for g in ids:
                t = _toks(desc.get(g, ""))
                docs[g] = Counter(t); dl[g] = len(t)
                df.update(set(t))
            avgdl = (sum(dl.values()) / max(len(dl), 1)) or 1.0
            N = len(ids)
            idf = {w: math.log(1 + (N - c + 0.5) / (c + 0.5)) for w, c in df.items()}
            bm25_state[l] = (docs, dl, avgdl, idf)

    out = {d: [] for d in ("tail", "head")}
    mention = {d: {"mentioned": [], "unmentioned": []} for d in ("tail", "head")}
    for (h, r, t) in targets:
        for direction in ("tail", "head"):
            q_ent, ans = (h, t) if direction == "tail" else (t, h)
            lang = ents[ans]["lang"]
            cands = by_lang[lang]
            if ans not in ents or lang != ents[q_ent]["lang"]:
                continue
            qt = _toks(desc.get(q_ent, ""))
            qset = set(qt)
            if method == "name_match":
                scores = []
                for c in cands:
                    ct = set(_toks(name.get(c, "")))
                    scores.append(len(qset & ct) / len(qset | ct) if (qset | ct) else 0.0)
            else:
                docs, dl, avgdl, idf = bm25_state[lang]
                scores = []
                for c in cands:
                    d_tf, d_len = docs[c], dl[c]
                    s = 0.0
                    for w in qset:
                        f = d_tf.get(w, 0)
                        if f:
                            s += idf.get(w, 0.0) * f * (K1 + 1) / (f + K1 * (1 - B + B * d_len / avgdl))
                    scores.append(s)
            idx = {g: i for i, g in enumerate(cands)}
            known = fwd.get((h, r), set()) if direction == "tail" else rev.get((r, t), set())
            filtered = {idx[k] for k in known if k in idx and k != ans}
            m = _metrics(_avg_rank(scores, idx[ans], filtered))
            out[direction].append(m)
            ans_name = name.get(ans, "")
            mentioned = len(ans_name) >= 3 and ans_name in desc.get(q_ent, "")
            mention[direction]["mentioned" if mentioned else "unmentioned"].append(m)

    res = {d: _agg(out[d]) for d in ("tail", "head")}
    res["combined"] = _agg(out["tail"] + out["head"])
    res["by_mention"] = {d: {b: _agg(mention[d][b]) for b in ("mentioned", "unmentioned")}
                         for d in ("tail", "head")}
    return res


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="lex_test_")
    try:
        proc = os.path.join(d, "DBP5L/processed"); os.makedirs(proc)
        fdir = os.path.join(d, "DBP5L/ind_v2/folds/f0/budgets"); os.makedirs(fdir)
        ents = {"0": {"lang": "en", "name": "Alan Turing"}, "1": {"lang": "en", "name": "Cambridge"},
                "2": {"lang": "en", "name": "Zebra"}}
        # query description mentions the ANSWER's name but not the query entity's own name,
        # so name_match must rank the mentioned answer first.
        view = {"0": "studied at cambridge", "1": "a city", "2": "an animal"}
        json.dump(ents, open(os.path.join(proc, "entities.json"), "w"))
        vp = os.path.join(d, "view.json"); json.dump(view, open(vp, "w"))
        with open(os.path.join(proc, "train.json"), "w") as f:
            f.write(json.dumps({"h": 0, "r": 9, "t": 1}) + "\n")
        json.dump([[0, 9, 1]], open(os.path.join(fdir, "eval_targets_test.json"), "w"))
        r = run(d, "f0", vp, "name_match")
        # desc(0) contains "cambridge" -> name_match ranks entity 1 first for tail
        assert r["tail"]["n"] == 1 and r["tail"]["mrr"] == 100.0, r["tail"]
        assert r["by_mention"]["tail"]["mentioned"]["n"] == 1, r["by_mention"]
        assert r["by_mention"]["tail"]["unmentioned"]["n"] == 0
        print("run_lexical_baseline self-check OK (name_match ranks mentioned answer first)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("RESEARCH_KG_ROOT",
                                                     os.path.expanduser("~/research_kg")))
    ap.add_argument("--folds", default="fold0_seed13,fold1_seed42,fold2_seed79")
    ap.add_argument("--methods", default="name_match,bm25")
    ap.add_argument("--max-targets", type=int, default=3000,
                    help="sample cap per fold (CPU baseline; 0 = all)")
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
           "max_targets_per_fold": args.max_targets, "results": {}}
    for fold in args.folds.split(","):
        for method in args.methods.split(","):
            for vname, vrel in views.items():
                t0 = time.time()
                r = run(args.root, fold, os.path.join(args.root, vrel), method,
                        args.max_targets or None)
                out["results"].setdefault(fold, {}).setdefault(method, {})[vname] = r
                print(f"[{fold}/{method}/{vname}] combined MRR={r['combined']['mrr']:.3f} "
                      f"tail={r['tail']['mrr']:.3f} head={r['head']['mrr']:.3f} "
                      f"({time.time()-t0:.0f}s)", flush=True)
    p = os.path.join(args.root, "DBP5L/ind_v2/audits/lexical_baselines.json")
    json.dump(out, open(p, "w"), indent=2, sort_keys=True)
    print("wrote", p)
