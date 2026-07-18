"""DBP5L-Ind v2 / P1.7 — deterministic alias-masked diagnostic description track.

The answer-mention audit (R-031) showed 63% of tail queries name the answer in the query
description. This builds a DIAGNOSTIC track that removes that crutch deterministically: in
each entity's description, every graph-neighbor entity's name (and its aliases across aligned
languages) is replaced with a placeholder `[ENT]`. Answers are graph neighbours, so this masks
answer mentions while keeping non-neighbour context.

This is a DIAGNOSTIC track — a lower bound. It over-masks (any neighbour, not only the specific
answer) and is deterministic + cacheable. The natural snapshot text stays a SEPARATE track
(descriptions_v2 / primary); its MRR must NOT be described as pure relational generalization.

Aliases: a neighbour's name in every language of its concept (P1.2) is masked, so cross-language
name leakage is covered too.

Output: DBP5L/ind_v2/tracks/descriptions_v2_masked.json + _stats.json (hash, mask counts).
Self-check: `python3 build_v2_masked_view.py --selftest`.
"""
import os
import sys
import re
import json
import time
import hashlib
import unicodedata
import argparse
from collections import defaultdict

PLACEHOLDER = "[ENT]"
MIN_NAME_LEN = 3          # don't mask ultra-short names (spurious hits)


def _norm(s):
    return " ".join(unicodedata.normalize("NFC", (s or "")).lower().split())


def _load(root):
    proc = os.path.join(root, "DBP5L/processed")
    with open(os.path.join(proc, "entities.json")) as f:
        ents = {int(g): e for g, e in json.load(f).items()}
    with open(os.path.join(root, "DBP5L/ind_v2/concepts/entity2concept.json")) as f:
        e2c = {int(k): v for k, v in json.load(f).items()}
    with open(os.path.join(root, "DBP5L/ind_v2/concepts/concepts.json")) as f:
        concepts = {int(k): v for k, v in json.load(f).items()}
    with open(os.path.join(root, "DBP5L/ind_v2/descriptions/descriptions_v2.json")) as f:
        desc = {int(g): v for g, v in json.load(f).items()}
    triples = []
    for split in ("train", "valid", "test"):
        p = os.path.join(proc, f"{split}.json")
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    d = json.loads(line)
                    triples.append((d["h"], d["t"]))
    return ents, e2c, concepts, desc, triples


def _alias_names(gid, ents, e2c, concepts):
    """Names of gid across all languages of its concept (aliases)."""
    names = set()
    cid = e2c.get(gid)
    members = concepts.get(cid, [gid]) if cid is not None else [gid]
    for m in members:
        nm = _norm(ents[m].get("name") or "")
        if len(nm) >= MIN_NAME_LEN:
            names.add(nm)
    return names


def build(root):
    ents, e2c, concepts, desc, triples = _load(root)
    neighbors = defaultdict(set)
    for (h, t) in triples:
        neighbors[h].add(t); neighbors[t].add(h)

    masked, n_masked = {}, {}
    total_orig_chars, total_removed_chars = 0, 0
    for g in sorted(ents):
        text = _norm(desc.get(g, ""))
        total_orig_chars += len(text)
        aliases = set()
        for nb in neighbors.get(g, ()):
            aliases |= _alias_names(nb, ents, e2c, concepts)
        cnt = 0
        # longest names first (Unicode-normalized) so a longer alias isn't partially eaten by a
        # shorter one; single generic placeholder token for every masked span.
        for name in sorted(aliases, key=len, reverse=True):
            pat = r"\b" + re.escape(name) + r"\b"
            text, k = re.subn(pat, PLACEHOLDER, text)
            cnt += k
            total_removed_chars += k * len(name)      # chars of original text masked out
        masked[g] = text
        n_masked[g] = cnt

    out_dir = os.path.join(root, "DBP5L/ind_v2/tracks")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "descriptions_v2_masked.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({str(g): masked[g] for g in masked}, f, ensure_ascii=False, sort_keys=True)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    total_masked = sum(n_masked.values())
    stats = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_entities": len(masked),
        "n_entities_with_masking": sum(1 for v in n_masked.values() if v > 0),
        "total_placeholders_inserted": total_masked,
        "pct_text_removed": round(100 * total_removed_chars / max(total_orig_chars, 1), 3),
        "total_original_chars": total_orig_chars,
        "total_removed_chars": total_removed_chars,
        "placeholder": PLACEHOLDER,
        "min_name_len": MIN_NAME_LEN,
        "note": "diagnostic lower-bound track; masks all graph-neighbour names+aliases; "
                "natural text is a separate track and not pure relational generalization",
        "hash": h,
    }
    with open(os.path.join(out_dir, "descriptions_v2_masked_stats.json"), "w") as f:
        json.dump(stats, f, indent=2, sort_keys=True)
    return stats


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="mask_test_")
    try:
        proc = os.path.join(d, "DBP5L/processed"); os.makedirs(proc)
        conc = os.path.join(d, "DBP5L/ind_v2/concepts"); os.makedirs(conc)
        dd = os.path.join(d, "DBP5L/ind_v2/descriptions"); os.makedirs(dd)
        ents = {"0": {"lang": "en", "name": "Alan Turing"}, "1": {"lang": "en", "name": "Cambridge"},
                "2": {"lang": "fr", "name": "Cambridge"}}
        e2c = {"0": 0, "1": 1, "2": 1}                       # 1 and 2 same concept (alias)
        concepts = {"0": [0], "1": [1, 2]}
        desc = {"0": "Alan Turing studied at Cambridge", "1": "a city", "2": "une ville"}
        json.dump(ents, open(os.path.join(proc, "entities.json"), "w"))
        json.dump(e2c, open(os.path.join(conc, "entity2concept.json"), "w"))
        json.dump(concepts, open(os.path.join(conc, "concepts.json"), "w"))
        json.dump(desc, open(os.path.join(dd, "descriptions_v2.json"), "w"))
        # 0-1 edge -> neighbour 1 (alias "cambridge") masked in desc(0)
        with open(os.path.join(proc, "train.json"), "w") as f:
            f.write(json.dumps({"h": 0, "r": 9, "t": 1}) + "\n")
        build(d)
        m = json.load(open(os.path.join(d, "DBP5L/ind_v2/tracks/descriptions_v2_masked.json")))
        assert "[ENT]" in m["0"] and "cambridge" not in m["0"], m["0"]
        assert "alan turing" in m["0"]                        # self not masked (not a neighbour)
        print("build_v2_masked_view self-check OK (neighbour names + cross-lang aliases masked)")
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
