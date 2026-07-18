"""DBP5L-Ind v2 / P1.2 — real-world concept clusters via union-find.

The v1 split held out entity IDs per language and copied alignment links unchanged,
so an entity could be "unseen" in JA while its aligned EN counterpart stayed in train
(§4.3: identifier-disjoint, not concept-disjoint). For a multilingual *inductive*
claim we must split whole aligned concepts, never individual language IDs.

This builds the concept partition (fold-independent) that the fold builder (P1.3) splits:
  concept = connected component of the alignment graph over global entity IDs.
  Unaligned entities are singleton concepts.
  canonical concept_id = min global id in the component (stable across folds).

Same-language collision = a component containing >= 2 entities of the same language.
A real-world concept should have at most one entity per language, so such components are
flagged (ambiguous alignment) and, unless --keep-ambiguous, quarantined (not emitted as
clean concepts) so they can't silently leak between splits.

Inputs  (under $RESEARCH_KG_ROOT/DBP5L/processed):
  alignments.json  : [{"e1":gid,"lang1":..,"e2":gid,"lang2":..}, ...]  (seed alignment pairs)
  entities.json    : {gid: {"lang":..,"local_id":..,"name":..,...}}     (full entity universe)

Outputs (under $RESEARCH_KG_ROOT/DBP5L/ind_v2/concepts):
  concepts.json          : {concept_id: [sorted member gids]}   (clean, non-ambiguous)
  entity2concept.json    : {gid: concept_id}                     (clean members only)
  ambiguous_concepts.json: {concept_id: {"members":[...],"langs":{lang:[gids]}}}
  union_provenance.jsonl : one line per union edge {"a":gid,"b":gid,"lang_a","lang_b"}
  concept_stats.json     : counts, size histogram, hashes of the above

Self-check: `python3 build_concept_clusters.py --selftest`.
"""
import os
import sys
import json
import time
import hashlib
import argparse
from collections import defaultdict


class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        self.add(x)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def _sha256_json(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(root, keep_ambiguous=False):
    processed = os.path.join(root, "DBP5L/processed")
    out_dir = os.path.join(root, "DBP5L/ind_v2/concepts")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(processed, "alignments.json")) as f:
        alignments = json.load(f)
    with open(os.path.join(processed, "entities.json")) as f:
        entities = json.load(f)
    gid_lang = {int(g): e["lang"] for g, e in entities.items()}
    all_gids = sorted(gid_lang.keys())

    uf = UnionFind()
    for g in all_gids:            # seed every entity so singletons become their own concept
        uf.add(g)

    # Deterministic union order: sort edges by (min,max) gid.
    edges = []
    for a in alignments:
        e1, e2 = int(a["e1"]), int(a["e2"])
        edges.append((min(e1, e2), max(e1, e2), a.get("lang1"), a.get("lang2")))
    edges.sort()

    prov_path = os.path.join(out_dir, "union_provenance.jsonl")
    with open(prov_path, "w") as pf:
        for lo, hi, la, lb in edges:
            if lo not in gid_lang or hi not in gid_lang:
                continue  # alignment references an entity not in entities.json — skip, record nothing
            merged = uf.union(lo, hi)
            pf.write(json.dumps({"a": lo, "b": hi, "lang_a": la, "lang_b": lb,
                                 "merged": merged}) + "\n")

    # Gather components.
    comp = defaultdict(list)
    for g in all_gids:
        comp[uf.find(g)].append(g)

    concepts = {}          # concept_id -> sorted members  (clean)
    entity2concept = {}
    ambiguous = {}         # concept_id -> {members, langs}
    for members in comp.values():
        members = sorted(members)
        cid = members[0]   # canonical id = min gid (fold-independent, stable)
        langs = defaultdict(list)
        for g in members:
            langs[gid_lang[g]].append(g)
        has_collision = any(len(v) > 1 for v in langs.values())
        if has_collision and not keep_ambiguous:
            ambiguous[cid] = {"members": members, "langs": dict(langs)}
        else:
            concepts[cid] = members
            for g in members:
                entity2concept[g] = cid

    # ── invariants ────────────────────────────────────────────────────────────
    seen = set()
    for cid, members in concepts.items():
        for g in members:
            assert g not in seen, f"entity {g} in two concepts"
            seen.add(g)
    # every clean entity maps back to its concept
    assert all(entity2concept[g] in concepts for g in entity2concept)

    def _dump(name, obj):
        p = os.path.join(out_dir, name)
        with open(p, "w") as f:
            json.dump(obj, f, sort_keys=True)
        return p

    p_c = _dump("concepts.json", {str(k): v for k, v in concepts.items()})
    p_e = _dump("entity2concept.json", {str(k): v for k, v in entity2concept.items()})
    p_a = _dump("ambiguous_concepts.json", {str(k): v for k, v in ambiguous.items()})

    sizes = defaultdict(int)
    for m in concepts.values():
        sizes[len(m)] += 1
    n_multi = sum(1 for m in concepts.values() if len(m) > 1)
    stats = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_entities_total": len(all_gids),
        "n_alignment_edges": len(edges),
        "n_clean_concepts": len(concepts),
        "n_multilingual_concepts": n_multi,
        "n_singleton_concepts": len(concepts) - n_multi,
        "n_ambiguous_concepts": len(ambiguous),
        "n_entities_in_ambiguous": sum(len(v["members"]) for v in ambiguous.values()),
        "n_entities_clean": len(entity2concept),
        "size_histogram": {str(k): sizes[k] for k in sorted(sizes)},
        "keep_ambiguous": keep_ambiguous,
        "hashes": {"concepts.json": _sha256_json(p_c),
                   "entity2concept.json": _sha256_json(p_e),
                   "ambiguous_concepts.json": _sha256_json(p_a),
                   "union_provenance.jsonl": _sha256_json(prov_path)},
    }
    _dump("concept_stats.json", stats)
    return stats


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="concept_test_")
    try:
        proc = os.path.join(d, "DBP5L/processed")
        os.makedirs(proc)
        # 6 entities: A(en0)-B(fr1)-C(ja2) one concept; D(en3)-E(fr4) another;
        # F(en5) singleton; plus a same-language collision G(en6)-H(en7) via alignment.
        entities = {
            "0": {"lang": "en"}, "1": {"lang": "fr"}, "2": {"lang": "ja"},
            "3": {"lang": "en"}, "4": {"lang": "fr"}, "5": {"lang": "en"},
            "6": {"lang": "en"}, "7": {"lang": "en"},
        }
        aligns = [
            {"e1": 0, "lang1": "en", "e2": 1, "lang2": "fr"},
            {"e1": 1, "lang1": "fr", "e2": 2, "lang2": "ja"},   # transitive: 0-1-2 one concept
            {"e1": 3, "lang1": "en", "e2": 4, "lang2": "fr"},
            {"e1": 6, "lang1": "en", "e2": 7, "lang2": "en"},   # same-language collision
        ]
        json.dump(entities, open(os.path.join(proc, "entities.json"), "w"))
        json.dump(aligns, open(os.path.join(proc, "alignments.json"), "w"))

        s = build(d, keep_ambiguous=False)
        assert s["n_entities_total"] == 8, s
        # concept {0,1,2} (canonical 0), {3,4} (canonical 3), singletons {5}
        # {6,7} is a same-language collision -> quarantined, NOT a clean concept.
        concepts = json.load(open(os.path.join(d, "DBP5L/ind_v2/concepts/concepts.json")))
        e2c = json.load(open(os.path.join(d, "DBP5L/ind_v2/concepts/entity2concept.json")))
        assert concepts["0"] == [0, 1, 2], concepts
        assert concepts["3"] == [3, 4], concepts
        assert concepts["5"] == [5], concepts
        assert "6" not in concepts and "6" not in e2c, "collision must be quarantined"
        assert s["n_clean_concepts"] == 3, s          # {0..},{3,4},{5}
        assert s["n_multilingual_concepts"] == 2, s
        assert s["n_ambiguous_concepts"] == 1, s
        assert s["n_entities_in_ambiguous"] == 2, s
        # no entity in two concepts
        seen = set()
        for m in concepts.values():
            for g in m:
                assert g not in seen
                seen.add(g)
        # determinism: rebuild -> identical hashes
        s2 = build(d, keep_ambiguous=False)
        assert s2["hashes"] == s["hashes"], "concept build is not deterministic"
        print("build_concept_clusters self-check OK "
              f"(clean={s['n_clean_concepts']} multi={s['n_multilingual_concepts']} "
              f"ambiguous={s['n_ambiguous_concepts']})")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("RESEARCH_KG_ROOT",
                                                     os.path.expanduser("~/research_kg")))
    ap.add_argument("--keep-ambiguous", action="store_true",
                    help="emit same-language-collision components as concepts instead of quarantining")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selfcheck()
        sys.exit(0)
    st = build(args.root, keep_ambiguous=args.keep_ambiguous)
    print(json.dumps(st, indent=2))
