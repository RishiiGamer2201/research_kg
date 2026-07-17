#!/usr/bin/env python3
"""Convert DBP-5L-Ind splits to S2DN/GraIL folder format.

Mapping (UNIFIED_PATHWAY Phase C):
  dbp5l_{lang}_v1/train.txt      <- ind/{lang}/train.txt   (base train graph)
  dbp5l_{lang}_v1/valid.txt      <- ind/{lang}/valid.txt
  dbp5l_{lang}_v1/test.txt       <- ind/{lang}/valid.txt   (placeholder; transductive test unused by inductive eval)
  dbp5l_{lang}_v1_ind/train.txt  <- ind/{lang}/support.txt (inductive support graph)
  dbp5l_{lang}_v1_ind/valid.txt  <- ind/{lang}/test.txt    (placeholder; unused by test_ranking)
  dbp5l_{lang}_v1_ind/test.txt   <- ind/{lang}/test.txt    (inductive evaluation triples)

Entities become "E{local_id}", relations use relation_names.json names (fallback "R{id}").
Asserts the entity-disjoint inductive split before writing anything.

Usage: python3 convert_dbp5l_to_grail.py [--base DBP5L_DIR] [--out OUT_DIR]
"""
import argparse
import json
import os
import sys

LANGS = ["en", "fr", "es", "ja", "el"]


def read_triples(path):
    triples = []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 3:
                triples.append((int(parts[0]), int(parts[1]), int(parts[2])))
    return triples


def read_ids(path):
    with open(path) as f:
        return {int(line.strip()) for line in f if line.strip()}


def ents_of(triples):
    s = set()
    for h, _, t in triples:
        s.add(h)
        s.add(t)
    return s


def write_triples(path, triples, rel_name):
    with open(path, "w") as f:
        for h, r, t in triples:
            f.write(f"E{h}\t{rel_name(r)}\tE{t}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.path.expanduser("~/research_kg/DBP5L"))
    ap.add_argument("--out", default=os.path.expanduser("~/research_kg/DBP5L/grail_format"))
    args = ap.parse_args()

    rel_names = {}
    rn_path = os.path.join(args.base, "processed", "relation_names.json")
    if os.path.exists(rn_path):
        raw = json.load(open(rn_path))
        # sanitize: GraIL splits on tab only, but keep names token-safe
        for k, v in raw.items():
            rel_names[int(k)] = str(v).strip().replace("\t", "_").replace(" ", "_")

    # §4.8 fix: relation symbols MUST stay injective. Using the sanitized display name
    # alone merged distinct relation IDs that share a name (EN: 166 IDs -> 83 name groups,
    # 37,039 triples). Prefix the numeric ID so the symbol is unique per relation.
    def rel_name(r):
        base = rel_names.get(r, "")
        return f"R{r}__{base}" if base else f"R{r}"

    # Detect & report display-name collisions instead of silently merging them.
    from collections import defaultdict
    name_groups = defaultdict(list)
    for rid, nm in rel_names.items():
        name_groups[nm].append(rid)
    collisions = {nm: sorted(ids) for nm, ids in name_groups.items() if len(ids) > 1}
    if collisions:
        n_ids = sum(len(v) for v in collisions.values())
        print(f"[relations] {len(collisions)} display-name collision group(s) covering "
              f"{n_ids} relation IDs; injective 'R{{id}}__name' keeps them distinct:")
        for nm, ids in sorted(collisions.items())[:10]:
            print(f"  '{nm}' <- ids {ids}")
    # Injectivity guarantee: distinct source IDs -> distinct symbols.
    _syms = {rel_name(r) for r in rel_names}
    assert len(_syms) == len(rel_names), "relation serialization is not injective"

    failures = 0
    for lang in LANGS:
        ind = os.path.join(args.base, "ind", lang)
        train = read_triples(os.path.join(ind, "train.txt"))
        valid = read_triples(os.path.join(ind, "valid.txt"))
        support = read_triples(os.path.join(ind, "support.txt"))
        test = read_triples(os.path.join(ind, "test.txt"))
        ents_train_file = read_ids(os.path.join(ind, "entities_train.txt"))
        ents_test_file = read_ids(os.path.join(ind, "entities_test.txt"))

        train_ents = ents_of(train)
        test_ents_in_triples = ents_of(test)

        # Assertion 1: declared train/test entity sets are disjoint.
        overlap_declared = ents_train_file & ents_test_file
        # Assertion 2: no unseen (declared-test) entity appears in the train graph.
        leak_train = train_ents & ents_test_file
        # Assertion 3: every test triple touches at least one unseen entity.
        no_unseen = [tr for tr in test if tr[0] not in ents_test_file and tr[2] not in ents_test_file]
        # Assertion 4: test triples are answerable from support graph vocabulary.
        support_ents = ents_of(support)
        known = support_ents | train_ents | ents_test_file
        dangling = [tr for tr in test if tr[0] not in known or tr[2] not in known]

        print(f"[{lang}] train={len(train)} valid={len(valid)} support={len(support)} test={len(test)}")
        print(f"[{lang}] declared train/test entity overlap: {len(overlap_declared)}")
        print(f"[{lang}] unseen entities leaking into train graph: {len(leak_train)}")
        print(f"[{lang}] test triples with no unseen entity: {len(no_unseen)}")
        print(f"[{lang}] test triples dangling outside known vocab: {len(dangling)}")

        if overlap_declared or leak_train:
            print(f"[{lang}] FAIL: entity-disjoint split violated, not writing output", file=sys.stderr)
            failures += 1
            continue

        trans_dir = os.path.join(args.out, f"dbp5l_{lang}_v1")
        ind_dir = os.path.join(args.out, f"dbp5l_{lang}_v1_ind")
        os.makedirs(trans_dir, exist_ok=True)
        os.makedirs(ind_dir, exist_ok=True)
        write_triples(os.path.join(trans_dir, "train.txt"), train, rel_name)
        write_triples(os.path.join(trans_dir, "valid.txt"), valid, rel_name)
        write_triples(os.path.join(trans_dir, "test.txt"), valid, rel_name)  # placeholder, unused
        write_triples(os.path.join(ind_dir, "train.txt"), support, rel_name)
        write_triples(os.path.join(ind_dir, "valid.txt"), test, rel_name)  # placeholder, unused
        write_triples(os.path.join(ind_dir, "test.txt"), test, rel_name)
        print(f"[{lang}] wrote {trans_dir} and {ind_dir}")

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
