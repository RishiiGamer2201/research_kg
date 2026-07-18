"""DBP5L-Ind v2 / P1.7 (concept & alignment leakage) — audit + reusable assertion.

Two jobs:
 1. `audit_v1()` quantifies the §4.3 defect: the v1 `ind/` split held out entity IDs
    per language, so a concept can be UNSEEN in one language yet SEEN (in training) via
    an aligned ID in another language. We count how many test concepts leak into train.
 2. `assert_concept_disjoint(...)` is the invariant the v2 fold builder (P1.3) must pass:
    the concept sets of train / valid / test are pairwise disjoint. Importable + tested.

v1 IDs in `ind/{lang}/entities_{train,test}.txt` are per-language LOCAL ids; we map
(lang, local_id) -> global id via entities.json, then global id -> concept.

Self-check: `python3 concept_leakage_audit.py --selftest`.
"""
import os
import sys
import json
import argparse
from collections import defaultdict

LANGS = ["en", "fr", "es", "ja", "el"]


def assert_concept_disjoint(train_concepts, valid_concepts, test_concepts):
    """Raise AssertionError if any concept appears in more than one split.
    Args are iterables of concept ids. Returns the three sets on success."""
    tr, va, te = set(train_concepts), set(valid_concepts), set(test_concepts)
    tv, tt, vt = tr & va, tr & te, va & te
    assert not tv, f"{len(tv)} concept(s) in BOTH train and valid, e.g. {sorted(tv)[:5]}"
    assert not tt, f"{len(tt)} concept(s) in BOTH train and test, e.g. {sorted(tt)[:5]}"
    assert not vt, f"{len(vt)} concept(s) in BOTH valid and test, e.g. {sorted(vt)[:5]}"
    return tr, va, te


def _load_entity2concept(root):
    p = os.path.join(root, "DBP5L/ind_v2/concepts/entity2concept.json")
    with open(p) as f:
        return {int(k): v for k, v in json.load(f).items()}


def _local_to_global(root):
    """(lang, local_id) -> global_id, from entities.json."""
    with open(os.path.join(root, "DBP5L/processed/entities.json")) as f:
        ents = json.load(f)
    m = {}
    for g, e in ents.items():
        m[(e["lang"], e["local_id"])] = int(g)
    return m


def _read_ids(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [int(float(x)) for x in f.read().split()]


def audit_v1(root):
    """Quantify concept leakage in the existing v1 ind/ split."""
    e2c = _load_entity2concept(root)
    l2g = _local_to_global(root)
    ind = os.path.join(root, "DBP5L/ind")

    train_concepts, test_concepts = set(), set()
    unmapped = 0
    for lang in LANGS:
        for local_id in _read_ids(os.path.join(ind, lang, "entities_train.txt")):
            g = l2g.get((lang, local_id))
            if g is None or g not in e2c:
                unmapped += 1; continue
            train_concepts.add(e2c[g])
        for local_id in _read_ids(os.path.join(ind, lang, "entities_test.txt")):
            g = l2g.get((lang, local_id))
            if g is None or g not in e2c:
                unmapped += 1; continue
            test_concepts.add(e2c[g])

    leaked = train_concepts & test_concepts
    return {
        "v1_train_concepts": len(train_concepts),
        "v1_test_concepts": len(test_concepts),
        "v1_leaked_concepts": len(leaked),          # concept unseen in one lang but trained in another
        "v1_leak_rate_of_test": round(len(leaked) / max(len(test_concepts), 1), 4),
        "unmapped_ids": unmapped,
        "example_leaked": sorted(leaked)[:10],
    }


def _selfcheck():
    # disjoint -> ok
    assert_concept_disjoint({1, 2}, {3}, {4, 5})
    # overlap -> raises
    for a, b, c in [({1, 2}, {2}, {3}), ({1}, {2}, {1}), ({1}, {2, 3}, {3})]:
        try:
            assert_concept_disjoint(a, b, c)
            raise SystemExit("expected AssertionError")
        except AssertionError:
            pass
    print("concept_leakage_audit self-check OK (disjointness assertion works)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("RESEARCH_KG_ROOT",
                                                     os.path.expanduser("~/research_kg")))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selfcheck()
        sys.exit(0)
    print(json.dumps(audit_v1(args.root), indent=2))
