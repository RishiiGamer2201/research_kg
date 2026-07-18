"""DBP5L-Ind v2 / P1.7 — structural audits: distributions, duplicates, inverse relations.

Reports (all deterministic):
  distributions      : entity-degree quantiles, relation-frequency top/tail, concept
                       (component) size histogram, per-language entity + triple coverage.
  duplicates         : exact duplicate descriptions (same normalized text) and exact
                       duplicate names (same normalized name) — near-dup risk for leakage.
  inverse_relations  : relation pairs (r, r') that appear reciprocally — (h,r,t) with (t,r',h)
                       — above a support threshold, plus same-relation reciprocal triples
                       (h,r,t)&(t,r,h). These are the classic inverse-edge shortcut.

Uses the whole graph for degree/relation stats; concept sizes come from the P1.2 clusters.

Self-check: `python3 audit_v2_structure.py --selftest`.
"""
import os
import sys
import json
import time
import hashlib
import unicodedata
import argparse
from collections import defaultdict, Counter


def _norm(s):
    return " ".join(unicodedata.normalize("NFC", (s or "")).lower().split())


def _load_triples(proc):
    triples = []
    for split in ("train", "valid", "test"):
        p = os.path.join(proc, f"{split}.json")
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    d = json.loads(line)
                    triples.append((d["h"], d["r"], d["t"]))
    return triples


def _q(sorted_vals, f):
    if not sorted_vals:
        return 0
    return sorted_vals[min(int(f * len(sorted_vals)), len(sorted_vals) - 1)]


def distributions(triples, ents, concepts):
    deg = defaultdict(int)
    relfreq = Counter()
    lang_ent = Counter(e["lang"] for e in ents.values())
    lang_trip = Counter()
    for (h, r, t) in triples:
        deg[h] += 1; deg[t] += 1; relfreq[r] += 1
        lang_trip[ents[h]["lang"]] += 1
    dv = sorted(deg.values())
    sizes = Counter(len(m) for m in concepts.values())
    return {
        "n_entities": len(ents), "n_triples": len(triples), "n_relations": len(relfreq),
        "degree": {"min": _q(dv, 0), "p25": _q(dv, .25), "median": _q(dv, .5),
                   "p75": _q(dv, .75), "p95": _q(dv, .95), "max": (dv[-1] if dv else 0)},
        "relation_freq_top5": relfreq.most_common(5),
        "relations_freq_le2": sum(1 for c in relfreq.values() if c <= 2),
        "concept_size_histogram": {str(k): sizes[k] for k in sorted(sizes)},
        "entities_per_language": dict(lang_ent),
        "triples_per_language": dict(lang_trip),
    }


def duplicates(ents, oracle_desc):
    by_desc, by_name = defaultdict(list), defaultdict(list)
    for g, e in ents.items():
        d = _norm(oracle_desc.get(g, ""))
        if d:
            by_desc[d].append(g)
        by_name[_norm(e.get("name") or "")].append(g)
    dup_desc = {k: v for k, v in by_desc.items() if len(v) > 1}
    dup_name = {k: v for k, v in by_name.items() if len(v) > 1 and k}
    return {
        "n_dup_description_groups": len(dup_desc),
        "n_entities_in_dup_descriptions": sum(len(v) for v in dup_desc.values()),
        "n_dup_name_groups": len(dup_name),
        "n_entities_in_dup_names": sum(len(v) for v in dup_name.values()),
        "example_dup_names": [{"name": k, "gids": v[:6]} for k, v in list(dup_name.items())[:5]],
    }


def inverse_relations(triples, min_support=20):
    pair_rels = defaultdict(set)          # (h,t) -> relations forward
    fwd = set()
    for (h, r, t) in triples:
        pair_rels[(h, t)].add(r)
        fwd.add((h, r, t))
    inv_counts = Counter()                # (r, r') where (h,r,t) and (t,r',h) co-occur
    recip_same = 0                        # (h,r,t) and (t,r,h) both present
    for (h, r, t) in triples:
        for r2 in pair_rels.get((t, h), ()):     # reverse pair
            inv_counts[(r, r2)] += 1
            if r2 == r:
                recip_same += 1
    strong = [{"rel_a": a, "rel_b": b, "support": c}
              for (a, b), c in inv_counts.most_common() if c >= min_support][:20]
    return {
        "n_inverse_relation_pairs_ge_support": len(strong),
        "min_support": min_support,
        "top_inverse_pairs": strong[:10],
        "reciprocal_same_relation_triples": recip_same,
    }


def build(root):
    proc = os.path.join(root, "DBP5L/processed")
    with open(os.path.join(proc, "entities.json")) as f:
        ents = {int(g): e for g, e in json.load(f).items()}
    with open(os.path.join(root, "DBP5L/ind_v2/concepts/concepts.json")) as f:
        concepts = {int(k): v for k, v in json.load(f).items()}
    with open(os.path.join(root, "DBP5L/ind_v2/descriptions/descriptions_v2.json")) as f:
        oracle_desc = {int(g): v for g, v in json.load(f).items()}
    triples = _load_triples(proc)
    out = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "distributions": distributions(triples, ents, concepts),
        "duplicates": duplicates(ents, oracle_desc),
        "inverse_relations": inverse_relations(triples),
    }
    out_dir = os.path.join(root, "DBP5L/ind_v2/audits"); os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "structure.json")
    json.dump(out, open(p, "w"), indent=2, sort_keys=True)
    out["hash"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    json.dump(out, open(p, "w"), indent=2, sort_keys=True)
    return out


def _selfcheck():
    triples = [(0, 1, 2), (2, 1, 0), (0, 3, 4)]      # (0,1,2)&(2,1,0) reciprocal same-rel
    ents = {0: {"lang": "en", "name": "A"}, 1: {"lang": "fr", "name": "A"},   # dup name "a"
            2: {"lang": "en", "name": "B"}, 3: {"lang": "en", "name": "C"},
            4: {"lang": "en", "name": "D"}}
    inv = inverse_relations(triples, min_support=1)
    assert inv["reciprocal_same_relation_triples"] == 2, inv
    assert any(p["rel_a"] == 1 and p["rel_b"] == 1 for p in inv["top_inverse_pairs"]), inv
    dup = duplicates(ents, {0: "same text", 1: "same text", 2: "x"})
    assert dup["n_dup_name_groups"] == 1                     # "a" shared by 0,1
    assert dup["n_dup_description_groups"] == 1              # "same text" shared by 0,1
    d = distributions(triples, ents, {0: [0, 1], 1: [2], 2: [3], 3: [4]})
    assert d["n_triples"] == 3 and d["n_relations"] == 2, d
    print("audit_v2_structure self-check OK (distributions, duplicates, inverse relations)")


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
