"""DBP5L-Ind v2 / P1.6 — evaluation tracks, description views, candidate universes.

Safeguards enforced here:
  * Primary alignment-free description view: every `wikipedia_cross_lang` entity FALLS BACK
    to its native name (cross-language text injects aligned-language identity, which the
    alignment-free primary track must not see). We ASSERT zero cross_lang usage in this view
    and give it its own hash.
  * Oracle-alignment view: the full P1.5 corpus (cross-language text allowed), separately
    labelled and hashed.
  * Within-language and all-language candidate universes are recorded independently, each
    with its own persisted ordered id list + hash.
  * Target sets, the single complete known-fact filter, and candidate hashes are FIXED across
    evidence budgets (referenced from the P1.4 budget manifests, not rebuilt per budget).
  * Head / tail / combined are declared as separate directions; head prediction uses reciprocal
    relation/direction tokens in BOTH training and evaluation (implemented in the trainer +
    evaluator — this file records the track contract).

Outputs (DBP5L/ind_v2/tracks/):
  descriptions_v2_primary.json     alignment-free view (no cross-lang; name fallback)
  candidates_all.json              all-language ordered candidate universe
  candidates_within_{lang}.json    per-language ordered candidate universe (×5)
  eval_tracks_manifest.json        the full track contract with every hash

Self-check: `python3 build_v2_eval_tracks.py --selftest`.
"""
import os
import sys
import json
import time
import hashlib
import unicodedata
import argparse
from collections import defaultdict

LANGS = ["en", "fr", "es", "ja", "el"]
BUDGETS = [0, 1, 3, 5]


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split()).strip()


def _dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True)
    return _sha_bytes(open(path, "rb").read())


def build(root):
    proc = os.path.join(root, "DBP5L/processed")
    desc_dir = os.path.join(root, "DBP5L/ind_v2/descriptions")
    out_dir = os.path.join(root, "DBP5L/ind_v2/tracks")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(proc, "entities.json")) as f:
        ents = {int(g): e for g, e in json.load(f).items()}
    with open(os.path.join(desc_dir, "descriptions_v2.json"), "rb") as f:
        oracle_bytes = f.read()
    oracle_desc = {int(k): v for k, v in json.loads(oracle_bytes).items()}
    oracle_hash = _sha_bytes(oracle_bytes)
    with open(os.path.join(desc_dir, "descriptions_v2_provenance.json")) as f:
        prov = {int(k): v for k, v in json.load(f).items()}

    # ── primary alignment-free view: cross-lang -> native name ──────────────────
    primary = {}
    n_fallback = 0
    for g in sorted(ents):
        if prov[g]["source"] == "wikipedia_cross_lang":
            primary[g] = _normalize(ents[g].get("name") or "")
            n_fallback += 1
        else:
            primary[g] = oracle_desc[g]
    # SAFEGUARD: assert zero cross-lang text survives in the primary view
    for g in primary:
        assert prov[g]["source"] != "wikipedia_cross_lang" or \
               primary[g] == _normalize(ents[g].get("name") or ""), \
               f"cross-lang text leaked into primary view at {g}"
    n_cross_in_primary = sum(1 for g in primary
                             if prov[g]["source"] == "wikipedia_cross_lang"
                             and primary[g] != _normalize(ents[g].get("name") or ""))
    assert n_cross_in_primary == 0, f"{n_cross_in_primary} cross-lang entries remain in primary"
    primary_hash = _dump(os.path.join(out_dir, "descriptions_v2_primary.json"),
                         {str(g): primary[g] for g in primary})

    # ── candidate universes (independent) ───────────────────────────────────────
    all_ids = sorted(ents)
    cand_all_hash = _dump(os.path.join(out_dir, "candidates_all.json"), all_ids)
    within = {}
    within_hashes = {}
    for lang in LANGS:
        ids = sorted(g for g in all_ids if ents[g]["lang"] == lang)
        within[lang] = len(ids)
        within_hashes[lang] = _dump(os.path.join(out_dir, f"candidates_within_{lang}.json"), ids)

    # ── reference the fixed P1.4 budget artifacts (targets/filter fixed across budgets) ──
    folds_root = os.path.join(root, "DBP5L/ind_v2/folds")
    budget_refs = {}
    if os.path.isdir(folds_root):
        for name in sorted(os.listdir(folds_root)):
            bm = os.path.join(folds_root, name, "budgets", "budget_manifest.json")
            if os.path.exists(bm):
                m = json.load(open(bm))
                budget_refs[name] = {
                    "filter_hash": m["filter_hash"],
                    "eval_targets_test_hash": m["output_hashes"]["eval_targets_test.json"],
                    "eval_targets_valid_hash": m["output_hashes"]["eval_targets_valid.json"],
                    "s5_union_hash": m["output_hashes"]["s5_union.json"],
                    "targets_fixed_across_budgets": m["invariants"]["targets_fixed_across_budgets"],
                    "single_filter_all_budgets": m["invariants"]["single_filter_all_budgets"],
                }

    manifest = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "directions": ["head", "tail", "combined"],
        "direction_contract": "head prediction uses reciprocal relation/direction tokens in "
                              "BOTH training and evaluation; head, tail, and combined metrics "
                              "are reported separately.",
        "budgets": BUDGETS,
        "description_views": {
            "primary_alignment_free": {
                "file": "descriptions_v2_primary.json", "hash": primary_hash,
                "cross_lang_usage": 0, "cross_lang_fallback_to_name": n_fallback,
                "note": "no wikipedia_cross_lang text; those entities use native name",
            },
            "oracle_alignment_diagnostic": {
                "file": "../descriptions/descriptions_v2.json", "hash": oracle_hash,
                "note": "cross-language snapshot text allowed; DIAGNOSTIC only, never the "
                        "primary result",
            },
        },
        "candidate_universes": {
            "all_language": {"file": "candidates_all.json", "hash": cand_all_hash,
                             "size": len(all_ids)},
            "within_language": {l: {"file": f"candidates_within_{l}.json",
                                    "hash": within_hashes[l], "size": within[l]} for l in LANGS},
        },
        "fixed_across_budgets": {
            "note": "targets, complete-known-fact filter, and candidate hashes do not vary with "
                    "evidence budget; only exposed support S^0⊂S^1⊂S^3⊂S^5 changes.",
            "per_fold_budget_refs": budget_refs,
        },
        "tracks": {
            "primary": {"desc_view": "primary_alignment_free", "candidates": ["within_language", "all_language"],
                        "directions": ["head", "tail", "combined"], "budgets": BUDGETS},
            "oracle_alignment": {"desc_view": "oracle_alignment_diagnostic", "label": "diagnostic"},
            "clean": {"desc_view": "primary_alignment_free", "label": "clean text"},
            "missing_text": {"note": "name-only / removed description; built in Phase 3"},
            "corruption": {"note": "held-out realistic corruptions; built in Phase 3/4"},
        },
    }
    manifest_hash = _dump(os.path.join(out_dir, "eval_tracks_manifest.json"), manifest)
    return {"primary_hash": primary_hash, "oracle_hash": oracle_hash,
            "cand_all_hash": cand_all_hash, "within_hashes": within_hashes,
            "n_cross_lang_fallback": n_fallback, "manifest_hash": manifest_hash,
            "primary_cross_lang_usage": 0}


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="tracks_test_")
    try:
        proc = os.path.join(d, "DBP5L/processed"); os.makedirs(proc)
        dd = os.path.join(d, "DBP5L/ind_v2/descriptions"); os.makedirs(dd)
        ents = {"0": {"lang": "en", "name": "Foo"}, "1": {"lang": "fr", "name": "Bar"},
                "2": {"lang": "ja", "name": "Baz"}, "3": {"lang": "es", "name": "Qux"},
                "4": {"lang": "el", "name": "Quux"}}
        desc = {"0": "Foo text", "1": "Foo text", "2": "Baz", "3": "Qux text", "4": "Quux"}
        prov = {"0": {"source": "wikipedia_native"}, "1": {"source": "wikipedia_cross_lang"},
                "2": {"source": "entity_name"}, "3": {"source": "wikipedia_native"},
                "4": {"source": "entity_name"}}
        json.dump(ents, open(os.path.join(proc, "entities.json"), "w"))
        json.dump(desc, open(os.path.join(dd, "descriptions_v2.json"), "w"))
        json.dump(prov, open(os.path.join(dd, "descriptions_v2_provenance.json"), "w"))

        r = build(d)
        prim = json.load(open(os.path.join(d, "DBP5L/ind_v2/tracks/descriptions_v2_primary.json")))
        # entity 1 was cross-lang ("Foo text") -> must fall back to its name "Bar"
        assert prim["1"] == "Bar", prim["1"]
        assert prim["0"] == "Foo text"           # native kept
        assert r["primary_cross_lang_usage"] == 0 and r["n_cross_lang_fallback"] == 1
        man = json.load(open(os.path.join(d, "DBP5L/ind_v2/tracks/eval_tracks_manifest.json")))
        assert man["description_views"]["primary_alignment_free"]["cross_lang_usage"] == 0
        assert man["directions"] == ["head", "tail", "combined"]
        # candidate universes independent + present for every language
        for l in LANGS:
            assert os.path.exists(os.path.join(d, f"DBP5L/ind_v2/tracks/candidates_within_{l}.json"))
        # determinism
        r2 = build(d)
        assert r2["manifest_hash"] == r["manifest_hash"], "tracks build not deterministic"
        print("build_v2_eval_tracks self-check OK (primary 0 cross-lang, oracle labelled, "
              "candidate universes independent)")
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
