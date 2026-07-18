"""DBP5L-Ind v2 / P1.7 — PPR & shortest-path structural shortcut audit.

Common random inductive splits can leak a Personalized-PageRank shortcut: pure graph
structure (ignoring relation types) predicts the answer, so a model can score well without
reasoning (Shomer, Revolinsky & Tang, KDD 2025). We test for it here.

Traversal graph (STRICT): all graph facts MINUS every validation/test eval-target edge, so
no answer edge (nor the specific target edge) is ever traversed. It is therefore the training-
internal edges plus the exposed support (S^5) union only. Edges are made undirected and
relation types are DROPPED (structure only).

For a deterministic sample of tail eval-targets (h, r, t):
  * PPR from h (restart prob 1-alpha); rank the within-language candidates of t by PPR mass;
    report filtered structural MRR / Hits@1 / Hits@10 against t.
  * BFS shortest-path length h->t on the same graph.
If structural MRR/Hits are high, the split has a shortcut and must be reported (not hidden).

Self-check: `python3 audit_v2_ppr_shortcut.py --selftest`.
"""
import os
import sys
import json
import time
import random
import hashlib
import argparse
from collections import defaultdict, deque

import numpy as np
import scipy.sparse as sp

ALPHA = 0.85          # PPR damping (restart prob = 1 - ALPHA)
N_ITER = 60
SAMPLE_PER_FOLD = 400
SAMPLE_SEED = 20260718


def _load_triples(root):
    proc = os.path.join(root, "DBP5L/processed")
    triples = []
    for split in ("train", "valid", "test"):
        p = os.path.join(proc, f"{split}.json")
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    d = json.loads(line)
                    triples.append((d["h"], d["r"], d["t"]))
    return triples


def _build_ppr_graph(all_triples, excluded_edges, n):
    """Undirected, relation-dropped adjacency over [0,n); excludes answer edges."""
    rows, cols = [], []
    for (h, r, t) in all_triples:
        if (h, r, t) in excluded_edges:
            continue                      # never traverse a valid/test answer edge
        rows += [h, t]; cols += [t, h]    # undirected
    A = sp.csr_matrix((np.ones(len(rows), dtype=np.float64), (rows, cols)), shape=(n, n))
    A.data[:] = 1.0
    deg = np.asarray(A.sum(axis=1)).ravel()
    deg[deg == 0] = 1.0
    Dinv = sp.diags(1.0 / deg)
    P = (Dinv @ A).T.tocsr()              # column-stochastic transition (P^T for power iter)
    return A, P


def _ppr(P, source, n):
    e = np.zeros(n); e[source] = 1.0
    pi = e.copy()
    for _ in range(N_ITER):
        pi = (1 - ALPHA) * e + ALPHA * (P @ pi)
    return pi


def _bfs_dist(A, s, t, cap=6):
    if s == t:
        return 0
    seen = {s}; q = deque([(s, 0)])
    indptr, indices = A.indptr, A.indices
    while q:
        u, d = q.popleft()
        if d >= cap:
            continue
        for v in indices[indptr[u]:indptr[u + 1]]:
            if v == t:
                return d + 1
            if v not in seen:
                seen.add(v); q.append((v, d + 1))
    return -1


def audit_fold(root, fold_dir, all_triples, gid_lang, within_ids, n):
    tgt_test = [tuple(x) for x in json.load(open(os.path.join(fold_dir, "budgets/eval_targets_test.json")))]
    tgt_valid = [tuple(x) for x in json.load(open(os.path.join(fold_dir, "budgets/eval_targets_valid.json")))]
    excluded = set(tgt_test) | set(tgt_valid)          # no answer edges in traversal
    A, P = _build_ppr_graph(all_triples, excluded, n)

    # filter map over the TRAVERSAL graph only (train + support), never valid/test answers
    filt = defaultdict(set)
    for (h, r, t) in all_triples:
        if (h, r, t) not in excluded:
            filt[(h, r)].add(t)

    rng = random.Random(SAMPLE_SEED)
    sample = sorted(set(tgt_test))
    rng.shuffle(sample)
    sample = sample[:SAMPLE_PER_FOLD]

    rr, h1, h10, sp_lens, reach = [], [], [], [], 0
    for (h, r, t) in sample:
        lang = gid_lang.get(t, "en")
        cands = within_ids.get(lang, [])
        if t not in cands or h >= n:
            continue
        pi = _ppr(P, h, n)
        known = filt.get((h, r), set())
        # rank t among same-language candidates by PPR score (filtered)
        t_score = pi[t]
        higher = sum(1 for c in cands if c != t and c not in known and pi[c] > t_score)
        ties = sum(1 for c in cands if c != t and c not in known and pi[c] == t_score)
        rank = higher + (ties + 1) / 2.0
        rr.append(1.0 / rank); h1.append(int(rank <= 1)); h10.append(int(rank <= 10))
        d = _bfs_dist(A, h, t)
        if d >= 0:
            sp_lens.append(d); reach += 1
    m = len(rr)
    return {
        "n_sampled": m,
        "ppr_mrr": round(sum(rr) / m, 4) if m else 0,
        "ppr_hits1": round(sum(h1) / m, 4) if m else 0,
        "ppr_hits10": round(sum(h10) / m, 4) if m else 0,
        "reachable_frac": round(reach / m, 4) if m else 0,
        "median_shortest_path": (sorted(sp_lens)[len(sp_lens) // 2] if sp_lens else -1),
        "excluded_answer_edges": len(excluded),
    }


def build(root):
    all_triples = _load_triples(root)
    proc = os.path.join(root, "DBP5L/processed")
    with open(os.path.join(proc, "entities.json")) as f:
        ents = {int(g): e for g, e in json.load(f).items()}
    gid_lang = {g: e["lang"] for g, e in ents.items()}
    n = max(ents) + 1
    within_ids = defaultdict(list)
    for g in sorted(ents):
        within_ids[ents[g]["lang"]].append(g)
    within_ids = {l: set(v) for l, v in within_ids.items()}

    folds_root = os.path.join(root, "DBP5L/ind_v2/folds")
    out = {"built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "alpha": ALPHA, "sample_per_fold": SAMPLE_PER_FOLD, "folds": {}}
    for name in sorted(os.listdir(folds_root)):
        fdir = os.path.join(folds_root, name)
        if os.path.isdir(fdir) and os.path.exists(os.path.join(fdir, "budgets")):
            print(f"[{time.strftime('%H:%M:%S')}] auditing {name} ...", flush=True)
            out["folds"][name] = audit_fold(root, fdir, all_triples, gid_lang, within_ids, n)
            print(f"[{time.strftime('%H:%M:%S')}] {name}: {out['folds'][name]}", flush=True)
    out_dir = os.path.join(root, "DBP5L/ind_v2/audits"); os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "ppr_shortcut.json")
    json.dump(out, open(p, "w"), indent=2, sort_keys=True)
    out["hash"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    json.dump(out, open(p, "w"), indent=2, sort_keys=True)
    return out


def _selfcheck():
    # chain 0-1-2-3 (relations arbitrary). Exclude the answer edge (0,r,3). PPR from 0 should
    # still reach 3 via 1-2, and BFS distance 0->3 == 3.
    triples = [(0, 9, 1), (1, 9, 2), (2, 9, 3), (0, 7, 3)]
    excluded = {(0, 7, 3)}
    A, P = _build_ppr_graph(triples, excluded, 4)
    pi = _ppr(P, 0, 4)
    assert pi[1] > 0 and pi[3] > 0, pi            # reachable without the answer edge
    assert _bfs_dist(A, 0, 3) == 3, _bfs_dist(A, 0, 3)
    # the excluded edge really is gone: with it, distance would be 1
    A2, _ = _build_ppr_graph(triples, set(), 4)
    assert _bfs_dist(A2, 0, 3) == 1
    print("audit_v2_ppr_shortcut self-check OK (answer edge excluded from traversal)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("RESEARCH_KG_ROOT",
                                                     os.path.expanduser("~/research_kg")))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selfcheck()
        sys.exit(0)
    r = build(args.root)
    print(json.dumps(r, indent=2))
