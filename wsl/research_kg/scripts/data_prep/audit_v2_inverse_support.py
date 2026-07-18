"""DBP5L-Ind v2 / P1.7 — inverse/reciprocal answer edges exposed through support.

A target (h, r, t) is directly revealed if the exposed support (S^5 union) contains any edge
connecting h and t — the exact reverse (t, r, h), an inverse-relation edge (t, r', h), or any
other h<->t link. Such adjacency lets a model read the answer off the support graph instead of
reasoning. We count these and emit an INVERSE-CLEAN support exposure that drops every such
h<->t edge from the budgets (targets and the complete filter are unchanged — only exposed
evidence shrinks), i.e. an inverse-clean primary track.

Per fold (DBP5L/ind_v2/folds/<fold>/budgets/):
  reads   s5_union.json, eval_targets_{test,valid}.json
  writes  s5_union_inverse_clean.json         (S^5 with answer-adjacency edges removed)
          inverse_support_audit.json          (counts, by direction)

Self-check: `python3 audit_v2_inverse_support.py --selftest`.
"""
import os
import sys
import json
import time
import hashlib
import argparse
from collections import defaultdict


def _dump(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, sort_keys=True)
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def audit_fold(fold_budget_dir):
    s5 = [tuple(x) for x in json.load(open(os.path.join(fold_budget_dir, "s5_union.json")))]
    tgt_test = [tuple(x) for x in json.load(open(os.path.join(fold_budget_dir, "eval_targets_test.json")))]
    tgt_valid = [tuple(x) for x in json.load(open(os.path.join(fold_budget_dir, "eval_targets_valid.json")))]

    # undirected h<->t adjacency present in exposed support, mapped to the support triples
    pair_to_support = defaultdict(list)
    for (a, r, b) in s5:
        pair_to_support[frozenset((a, b))].append((a, r, b))

    def count(targets):
        n_reveal, n_exact_recip, revealed_support = 0, 0, set()
        for (h, r, t) in targets:
            key = frozenset((h, t))
            if key in pair_to_support:
                n_reveal += 1
                for tri in pair_to_support[key]:
                    revealed_support.add(tri)
                    if tri == (t, r, h):
                        n_exact_recip += 1
        return n_reveal, n_exact_recip, revealed_support

    rev_test, exact_test, sup_test = count(tgt_test)
    rev_valid, exact_valid, sup_valid = count(tgt_valid)
    revealed = sup_test | sup_valid                      # support edges to drop

    s5_clean = [list(tri) for tri in s5 if tri not in revealed]
    clean_hash = _dump(os.path.join(fold_budget_dir, "s5_union_inverse_clean.json"), sorted(s5_clean))
    audit = {
        "s5_union_size": len(s5),
        "test_targets": len(tgt_test),
        "test_answer_revealed_by_support": rev_test,
        "test_reveal_rate": round(rev_test / max(len(tgt_test), 1), 4),
        "test_exact_reciprocal": exact_test,
        "valid_targets": len(tgt_valid),
        "valid_answer_revealed_by_support": rev_valid,
        "valid_reveal_rate": round(rev_valid / max(len(tgt_valid), 1), 4),
        "support_edges_dropped_for_inverse_clean": len(revealed),
        "s5_union_inverse_clean_size": len(s5_clean),
        "s5_union_inverse_clean_hash": clean_hash,
    }
    _dump(os.path.join(fold_budget_dir, "inverse_support_audit.json"), audit)
    return audit


def build(root):
    folds_root = os.path.join(root, "DBP5L/ind_v2/folds")
    out = {"built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "folds": {}}
    for name in sorted(os.listdir(folds_root)):
        bdir = os.path.join(folds_root, name, "budgets")
        if os.path.isdir(bdir):
            out["folds"][name] = audit_fold(bdir)
    out_dir = os.path.join(root, "DBP5L/ind_v2/audits"); os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "inverse_support.json")
    json.dump(out, open(p, "w"), indent=2, sort_keys=True)
    return out


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="inv_sup_")
    try:
        bd = os.path.join(d, "b"); os.makedirs(bd)
        # target (1,r,2). support has the exact reciprocal (2,r,1) -> reveals answer.
        # support (3,r,4) is unrelated -> stays.
        json.dump([[2, 9, 1], [3, 9, 4]], open(os.path.join(bd, "s5_union.json"), "w"))
        json.dump([[1, 9, 2]], open(os.path.join(bd, "eval_targets_test.json"), "w"))
        json.dump([], open(os.path.join(bd, "eval_targets_valid.json"), "w"))
        a = audit_fold(bd)
        assert a["test_answer_revealed_by_support"] == 1 and a["test_exact_reciprocal"] == 1, a
        assert a["support_edges_dropped_for_inverse_clean"] == 1, a
        clean = json.load(open(os.path.join(bd, "s5_union_inverse_clean.json")))
        assert [2, 9, 1] not in clean and [3, 9, 4] in clean, clean
        print("audit_v2_inverse_support self-check OK (reciprocal answer edge detected + dropped)")
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
