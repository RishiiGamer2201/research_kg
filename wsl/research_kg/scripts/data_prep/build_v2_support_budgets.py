"""DBP5L-Ind v2 / P1.4 — nested evidence budgets S^0 ⊂ S^1 ⊂ S^3 ⊂ S^5.

Comparability rule (critical — makes budgets directly comparable):
  1. Build one deterministic ORDERED support pool per unseen entity; the first 5 form S^5.
  2. The S^5 UNION over all unseen entities is selected FIRST and removed from the
     evaluation targets for EVERY budget. Targets are therefore identical across budgets.
  3. ONE complete known-true filter (all graph facts) is used for every budget.
  4. Only the evidence EXPOSED to the model varies: S^k(e) = ordered_pool(e)[:k], k∈{0,1,3,5}.
     Candidate universe and target set never change with k.

Support pool ordering (per unseen entity e), preferring train-connected, non-duplicate edges:
  key = (other_endpoint_is_seen? 0:1, relation_id, other_global_id, direction)
  → seen-neighbour edges first; deterministic tie-break. First 5 = S^5(e), |S^k(e)| ≤ k.

Per fold outputs (DBP5L/ind_v2/folds/fold{i}_seed{seed}/budgets/):
  support_pool.json     {gid: [[h,r,t], ... up to 5]}       ordered; prefix k = S^k(e)
  s5_union.json         [[h,r,t], ...]                       the removed support union
  eval_targets_test.json / eval_targets_valid.json           test/valid triples MINUS S^5 union
  budget_manifest.json  invariants (nesting, caps, no target∩S^5), per-budget counts, hashes,
                        filter = "all graph facts (train+valid+test)", filter_hash

Self-check: `python3 build_v2_support_budgets.py --selftest`.
"""
import os
import sys
import json
import time
import hashlib
import argparse
from collections import defaultdict

BUDGETS = [0, 1, 3, 5]


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _dump(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, sort_keys=True)
    return _sha_file(path)


def _load_triples(root):
    proc = os.path.join(root, "DBP5L/processed")
    triples = []
    for split in ("train", "valid", "test"):
        p = os.path.join(proc, f"{split}.json")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for line in f:
                t = json.loads(line)
                triples.append((t["h"], t["r"], t["t"]))
    # dedup exact triples, deterministic order
    return sorted(set(triples))


def _ordered_pool(e, incident, seen):
    """Deterministic ordered support pool for unseen entity e (train-connected first)."""
    keyed = []
    for (h, r, t) in incident:
        other = t if h == e else h
        direction = 0 if h == e else 1          # 0: e is head, 1: e is tail
        seen_rank = 0 if other in seen else 1   # seen neighbours first
        keyed.append(((seen_rank, r, other, direction), (h, r, t)))
    keyed.sort(key=lambda x: x[0])
    # non-duplicate already (triples deduped); cap at 5 for S^5
    return [tri for _, tri in keyed][:5]


def build_fold(root, fold_dir, triples, seen, unseen_test, unseen_valid):
    incident = defaultdict(list)
    for (h, r, t) in triples:
        if h in unseen_test or h in unseen_valid:
            incident[h].append((h, r, t))
        if t in unseen_test or t in unseen_valid:
            incident[t].append((h, r, t))

    # 1+2. ordered pool + S^5 union (selected FIRST)
    pool = {}
    s5_union = set()
    for e in sorted(incident):
        p = _ordered_pool(e, incident[e], seen)
        pool[e] = p
        s5_union.update(p)

    # eval targets = split-eligible triples MINUS the S^5 union (fixed across all budgets)
    def targets(unseen_set):
        out = [list(tr) for tr in triples
               if (tr[0] in unseen_set or tr[2] in unseen_set) and tr not in s5_union]
        return sorted(out)
    tgt_test = targets(unseen_test)
    tgt_valid = targets(unseen_valid)

    # ── inverse-clean ordered pools (P1.7) ──────────────────────────────────────
    # Drop support edges whose endpoints form an eval-target pair (h<->t adjacency reveals the
    # answer). Removal happens BEFORE prefixing, so the cleaned 0/1/3/5 prefixes stay nested and
    # budget capacity stays valid. Targets and the complete filter are unchanged.
    target_pairs = ({frozenset((h, t)) for (h, r, t) in tgt_test} |
                    {frozenset((h, t)) for (h, r, t) in tgt_valid})
    clean_pool = {e: [edge for edge in p if frozenset((edge[0], edge[2])) not in target_pairs]
                  for e, p in pool.items()}
    s5_union_clean = set()
    per_budget_exposed_clean = {k: 0 for k in BUDGETS}
    for e, p in clean_pool.items():
        s5_union_clean.update(p)
        for k in BUDGETS:
            sk = p[:k]
            assert len(sk) <= k and sk == p[:k]        # cap + prefix nesting by construction
            per_budget_exposed_clean[k] += len(sk)

    # ── invariants ────────────────────────────────────────────────────────────
    per_budget_exposed = {}
    for k in BUDGETS:
        exposed = 0
        for e, p in pool.items():
            sk = p[:k]
            assert len(sk) <= k, f"|S^{k}({e})|={len(sk)} > {k}"        # cap
            if k > 0:                                                    # nesting: prefix
                assert sk[:-1] == p[:k - 1] or len(p) < k
            exposed += len(sk)
        per_budget_exposed[k] = exposed
    # strict nesting S^0 ⊂ S^1 ⊂ S^3 ⊂ S^5 on a sampled entity set (prefix property holds by construction)
    for e, p in list(pool.items())[:1000]:
        s0, s1, s3, s5 = p[:0], p[:1], p[:3], p[:5]
        assert s0 == s5[:0] and s1 == s5[:1] and s3 == s5[:3], f"nesting broken for {e}"
    # no target overlaps the support union, in either split
    s5_list = set(map(tuple, (tuple(x) for x in s5_union)))
    assert all(tuple(t) not in s5_list for t in tgt_test), "test target ∩ S^5 union non-empty"
    assert all(tuple(t) not in s5_list for t in tgt_valid), "valid target ∩ S^5 union non-empty"

    os.makedirs(fold_dir, exist_ok=True)
    hashes = {}
    hashes["support_pool.json"] = _dump(os.path.join(fold_dir, "support_pool.json"),
                                        {str(e): [list(x) for x in pool[e]] for e in pool})
    hashes["s5_union.json"] = _dump(os.path.join(fold_dir, "s5_union.json"),
                                    sorted([list(x) for x in s5_union]))
    hashes["eval_targets_test.json"] = _dump(os.path.join(fold_dir, "eval_targets_test.json"), tgt_test)
    hashes["eval_targets_valid.json"] = _dump(os.path.join(fold_dir, "eval_targets_valid.json"), tgt_valid)
    # inverse-clean ordered pools + union (nested 0/1/3/5 prefixes valid on the cleaned pools)
    hashes["support_pool_inverse_clean.json"] = _dump(
        os.path.join(fold_dir, "support_pool_inverse_clean.json"),
        {str(e): [list(x) for x in clean_pool[e]] for e in clean_pool})
    hashes["s5_union_inverse_clean.json"] = _dump(
        os.path.join(fold_dir, "s5_union_inverse_clean.json"),
        sorted([list(x) for x in s5_union_clean]))

    # one complete known-true filter across all budgets = every graph fact
    filter_hash = hashlib.sha256(
        json.dumps(sorted([list(t) for t in triples]), sort_keys=True).encode()).hexdigest()

    manifest = {
        "budgets": BUDGETS,
        "n_unseen_with_support": len(pool),
        "s5_union_size": len(s5_union),
        "eval_targets_test": len(tgt_test),
        "eval_targets_valid": len(tgt_valid),
        "exposed_edges_per_budget": per_budget_exposed,
        "avg_support_pool_size": round(sum(len(p) for p in pool.values()) / max(len(pool), 1), 3),
        "inverse_clean": {
            "s5_union_size": len(s5_union_clean),
            "exposed_edges_per_budget": per_budget_exposed_clean,
            "note": "answer-adjacency edges removed BEFORE prefixing -> nested 0/1/3/5 valid",
        },
        "invariants": {"nesting": "S^0⊂S^1⊂S^3⊂S^5 (prefix)", "caps": "|S^k|≤k",
                       "targets_fixed_across_budgets": True,
                       "target_intersect_s5_union": 0,
                       "single_filter_all_budgets": True},
        "filter": "all graph facts (train+valid+test), identical for every budget",
        "filter_hash": filter_hash,
        "output_hashes": hashes,
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _dump(os.path.join(fold_dir, "budget_manifest.json"), manifest)
    return manifest


def build(root):
    triples = _load_triples(root)
    folds_root = os.path.join(root, "DBP5L/ind_v2/folds")
    summary = {"folds": []}
    for name in sorted(os.listdir(folds_root)):
        fdir = os.path.join(folds_root, name)
        if not os.path.isdir(fdir):
            continue
        seen = set(json.load(open(os.path.join(fdir, "train_entities.json"))))
        unseen_test = set(json.load(open(os.path.join(fdir, "test_entities.json"))))
        unseen_valid = set(json.load(open(os.path.join(fdir, "valid_entities.json"))))
        man = build_fold(root, os.path.join(fdir, "budgets"), triples, seen, unseen_test, unseen_valid)
        summary["folds"].append({"fold": name, **{k: man[k] for k in
                                 ("s5_union_size", "eval_targets_test", "eval_targets_valid",
                                  "exposed_edges_per_budget")}})
    _dump(os.path.join(folds_root, "budgets_summary.json"), summary)
    return summary


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="budget_test_")
    try:
        proc = os.path.join(d, "DBP5L/processed"); os.makedirs(proc)
        fdir = os.path.join(d, "DBP5L/ind_v2/folds/fold0_seed13"); os.makedirs(fdir)
        # seen entities 0,1,2 ; unseen test 100 with edges to seen 0,1,2 and unseen 101
        rows = [(0, 5, 100), (1, 6, 100), (2, 7, 100), (100, 8, 101),
                (0, 5, 101), (3, 9, 100), (4, 9, 100), (10, 9, 100)]  # 100 has 7 incident, 101 has 2
        with open(os.path.join(proc, "train.json"), "w") as f:
            for h, r, t in rows:
                f.write(json.dumps({"h": h, "r": r, "t": t}) + "\n")
        json.dump([0, 1, 2, 3, 4, 10], open(os.path.join(fdir, "train_entities.json"), "w"))
        json.dump([100, 101], open(os.path.join(fdir, "test_entities.json"), "w"))
        json.dump([], open(os.path.join(fdir, "valid_entities.json"), "w"))

        m1 = build(d)
        bm = json.load(open(os.path.join(fdir, "budgets/budget_manifest.json")))
        pool = json.load(open(os.path.join(fdir, "budgets/support_pool.json")))
        # entity 100 has 7 incident edges -> S^5 pool capped at 5; seen-neighbour edges first
        assert len(pool["100"]) == 5, pool["100"]
        # every support edge for 100 must NOT be an eval target
        s5 = {tuple(x) for x in json.load(open(os.path.join(fdir, "budgets/s5_union.json")))}
        tgt = {tuple(x) for x in json.load(open(os.path.join(fdir, "budgets/eval_targets_test.json")))}
        assert s5.isdisjoint(tgt), "targets overlap S^5 union"
        # nesting/caps recorded, exposed counts monotonic in k
        ex = bm["exposed_edges_per_budget"]
        assert ex["0"] == 0 and ex["1"] <= ex["3"] <= ex["5"], ex
        assert bm["invariants"]["target_intersect_s5_union"] == 0
        # determinism
        h1 = json.load(open(os.path.join(d, "DBP5L/ind_v2/folds/budgets_summary.json")))
        build(d)
        h2 = json.load(open(os.path.join(d, "DBP5L/ind_v2/folds/budgets_summary.json")))
        assert h1 == h2, "budget build not deterministic"
        print("build_v2_support_budgets self-check OK (S^5 union first, targets fixed, filter single)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("RESEARCH_KG_ROOT",
                                                     os.path.expanduser("~/research_kg")))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selfcheck()
        sys.exit(0)
    print(json.dumps(build(args.root), indent=2))
