"""DBP5L-Ind v2 / P1.3 — three fixed concept-disjoint folds.

Splits CONCEPT ids (never entity ids) into train / valid / test on three published
seeds. Whole concepts move together, so train/valid/test are concept-disjoint by
construction (verified with assert_concept_disjoint). Validation is inductive: its
concepts are unseen in train, drawn from the same stratified population as test.

Stratification: bucket concepts by language coverage (concept size = #languages, 1..5),
then split each bucket by ratio. This keeps multilingual vs singleton concepts balanced
across train/valid/test rather than dumping all size-5 concepts into one split. Degree and
relation-support distributions are reported per split to show balance (they are not used to
move concept members, per the "no splitting a concept" rule).

Per fold we publish: concept lists, entity expansions, stratification statistics, the seed,
content hashes, and the passing assert_concept_disjoint result.

Inputs  ($RESEARCH_KG_ROOT/DBP5L): ind_v2/concepts/{concepts.json,entity2concept.json},
        processed/entities.json, processed/{train,valid,test}.json (triples for degree/relations)
Outputs ($RESEARCH_KG_ROOT/DBP5L/ind_v2/folds/fold{i}_seed{seed}/):
        {train,valid,test}_concepts.json, {train,valid,test}_entities.json,
        stratification_stats.json, fold_manifest.json
        + folds_summary.json at ind_v2/folds/

Self-check: `python3 build_v2_folds.py --selftest`.
"""
import os
import sys
import json
import time
import random
import hashlib
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concept_leakage_audit import assert_concept_disjoint  # noqa: E402

LANGS = ["en", "fr", "es", "ja", "el"]
FOLD_SEEDS = [13, 42, 79]           # the three official DBP5L-Ind v2 fold seeds
TEST_FRAC, VALID_FRAC = 0.15, 0.10  # per stratum; train = remainder


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _dump(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, sort_keys=True)
    return _sha256_file(path)


def _load_graph(root):
    proc = os.path.join(root, "DBP5L/processed")
    conc_dir = os.path.join(root, "DBP5L/ind_v2/concepts")
    with open(os.path.join(conc_dir, "concepts.json")) as f:
        concepts = {int(k): v for k, v in json.load(f).items()}
    with open(os.path.join(conc_dir, "entity2concept.json")) as f:
        e2c = {int(k): v for k, v in json.load(f).items()}
    with open(os.path.join(proc, "entities.json")) as f:
        gid_lang = {int(g): e["lang"] for g, e in json.load(f).items()}
    # entity degree + per-concept relation set from the full graph
    degree = defaultdict(int)
    concept_rels = defaultdict(set)
    for split in ("train", "valid", "test"):
        p = os.path.join(proc, f"{split}.json")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for line in f:
                t = json.loads(line)
                h, r, tail = t["h"], t["r"], t["t"]
                degree[h] += 1
                degree[tail] += 1
                if h in e2c:
                    concept_rels[e2c[h]].add(r)
                if tail in e2c:
                    concept_rels[e2c[tail]].add(r)
    return concepts, e2c, gid_lang, degree, concept_rels


def _split_stats(cids, concepts, gid_lang, degree, concept_rels):
    ents, size_hist, per_lang, degs, rels = [], defaultdict(int), defaultdict(int), [], set()
    for c in cids:
        members = concepts[c]
        size_hist[len(members)] += 1
        rels |= concept_rels.get(c, set())
        for g in members:
            ents.append(g)
            per_lang[gid_lang[g]] += 1
            degs.append(degree.get(g, 0))
    degs.sort()
    n = len(degs)
    def q(f):
        return degs[min(int(f * n), n - 1)] if n else 0
    return sorted(ents), {
        "n_concepts": len(cids),
        "n_entities": len(ents),
        "size_histogram": {str(k): size_hist[k] for k in sorted(size_hist)},
        "entities_per_language": {l: per_lang.get(l, 0) for l in LANGS},
        "degree": {"min": q(0), "p25": q(.25), "median": q(.5), "p75": q(.75),
                   "max": (degs[-1] if n else 0), "mean": round(sum(degs) / n, 2) if n else 0},
        "n_distinct_relations": len(rels),
    }


def build_fold(root, seed, fold_index, concepts, e2c, gid_lang, degree, concept_rels):
    # stratify by concept size (language coverage), deterministic within stratum
    by_size = defaultdict(list)
    for c in sorted(concepts):
        by_size[len(concepts[c])].append(c)
    train_c, valid_c, test_c = [], [], []
    rng = random.Random(seed)
    for size in sorted(by_size):
        bucket = by_size[size][:]      # already sorted by concept id → deterministic base order
        rng.shuffle(bucket)
        n = len(bucket)
        n_test = int(round(n * TEST_FRAC))
        n_valid = int(round(n * VALID_FRAC))
        test_c += bucket[:n_test]
        valid_c += bucket[n_test:n_test + n_valid]
        train_c += bucket[n_test + n_valid:]
    train_c, valid_c, test_c = sorted(train_c), sorted(valid_c), sorted(test_c)

    # invariant: concept-disjoint
    assert_concept_disjoint(train_c, valid_c, test_c)

    out_dir = os.path.join(root, f"DBP5L/ind_v2/folds/fold{fold_index}_seed{seed}")
    os.makedirs(out_dir, exist_ok=True)
    hashes, stats = {}, {}
    for name, cids in (("train", train_c), ("valid", valid_c), ("test", test_c)):
        ents, st = _split_stats(cids, concepts, gid_lang, degree, concept_rels)
        hashes[f"{name}_concepts.json"] = _dump(os.path.join(out_dir, f"{name}_concepts.json"), cids)
        hashes[f"{name}_entities.json"] = _dump(os.path.join(out_dir, f"{name}_entities.json"), ents)
        stats[name] = st
    _dump(os.path.join(out_dir, "stratification_stats.json"), stats)

    manifest = {
        "fold_index": fold_index,
        "seed": seed,
        "ratios": {"train": round(1 - TEST_FRAC - VALID_FRAC, 2),
                   "valid": VALID_FRAC, "test": TEST_FRAC},
        "stratified_by": "concept language-coverage (size 1..5)",
        "n_concepts": {"train": len(train_c), "valid": len(valid_c), "test": len(test_c)},
        "assert_concept_disjoint": "passed",
        "concepts_source_hash": _sha256_file(
            os.path.join(root, "DBP5L/ind_v2/concepts/concepts.json")),
        "output_hashes": hashes,
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _dump(os.path.join(out_dir, "fold_manifest.json"), manifest)
    return manifest, stats


def build(root):
    concepts, e2c, gid_lang, degree, concept_rels = _load_graph(root)
    summary = {"n_concepts_total": len(concepts), "fold_seeds": FOLD_SEEDS, "folds": []}
    for i, seed in enumerate(FOLD_SEEDS):
        man, stats = build_fold(root, seed, i, concepts, e2c, gid_lang, degree, concept_rels)
        # every language must have test + valid queries available (entities present)
        for split in ("valid", "test"):
            for l in LANGS:
                assert stats[split]["entities_per_language"][l] > 0, \
                    f"fold{i} {split}: no {l} entities"
        summary["folds"].append({"seed": seed, "n_concepts": man["n_concepts"],
                                 "manifest_hash": _sha256_file(os.path.join(
                                     root, f"DBP5L/ind_v2/folds/fold{i}_seed{seed}/fold_manifest.json"))})
    _dump(os.path.join(root, "DBP5L/ind_v2/folds/folds_summary.json"), summary)
    return summary


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="folds_test_")
    try:
        proc = os.path.join(d, "DBP5L/processed"); os.makedirs(proc)
        conc = os.path.join(d, "DBP5L/ind_v2/concepts"); os.makedirs(conc)
        # 100 concepts across sizes 1 and 2, 5 languages represented
        entities, concepts, e2c = {}, {}, {}
        gid = 0
        for c in range(100):
            size = 1 if c % 2 else 2
            members = []
            for s in range(size):
                lang = LANGS[(c + s) % 5]
                entities[str(gid)] = {"lang": lang, "local_id": gid, "global_id": gid}
                members.append(gid); e2c[str(gid)] = c; gid += 1
            concepts[str(c)] = members
        json.dump(entities, open(os.path.join(proc, "entities.json"), "w"))
        json.dump(concepts, open(os.path.join(conc, "concepts.json"), "w"))
        json.dump(e2c, open(os.path.join(conc, "entity2concept.json"), "w"))
        # a couple of triples so degree/relations are non-empty
        with open(os.path.join(proc, "train.json"), "w") as f:
            f.write(json.dumps({"h": 0, "r": 1, "t": 2, "lang": "en"}) + "\n")
            f.write(json.dumps({"h": 2, "r": 3, "t": 4, "lang": "fr"}) + "\n")

        s1 = build(d)
        assert len(s1["folds"]) == 3
        for i, seed in enumerate(FOLD_SEEDS):
            fd = os.path.join(d, f"DBP5L/ind_v2/folds/fold{i}_seed{seed}")
            tr = json.load(open(os.path.join(fd, "train_concepts.json")))
            va = json.load(open(os.path.join(fd, "valid_concepts.json")))
            te = json.load(open(os.path.join(fd, "test_concepts.json")))
            assert len(tr) + len(va) + len(te) == 100
            assert set(tr).isdisjoint(va) and set(tr).isdisjoint(te) and set(va).isdisjoint(te)
            man = json.load(open(os.path.join(fd, "fold_manifest.json")))
            assert man["assert_concept_disjoint"] == "passed" and man["seed"] == seed
        # different seeds → different test sets
        te0 = json.load(open(os.path.join(d, f"DBP5L/ind_v2/folds/fold0_seed{FOLD_SEEDS[0]}/test_concepts.json")))
        te1 = json.load(open(os.path.join(d, f"DBP5L/ind_v2/folds/fold1_seed{FOLD_SEEDS[1]}/test_concepts.json")))
        assert te0 != te1, "different seeds should give different folds"
        # determinism: rebuild fold 0 → identical hash
        h_before = json.load(open(os.path.join(d, "DBP5L/ind_v2/folds/folds_summary.json")))["folds"][0]["manifest_hash"]
        build(d)
        h_after = json.load(open(os.path.join(d, "DBP5L/ind_v2/folds/folds_summary.json")))["folds"][0]["manifest_hash"]
        assert h_before == h_after, "fold build not deterministic"
        print("build_v2_folds self-check OK (3 disjoint folds, deterministic, per-seed distinct)")
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
