"""DBP5L-Ind v2 / P1.5 — clean descriptions from permitted evidence + full provenance.

Source priority per entity:
  1. native verified snapshot  — Wikipedia abstract in the entity's own language
     (frozen corpus `entity_descriptions_wiki.json`; text present and != the bare name).
  2. verified cross-language snapshot — if native is missing, borrow the native abstract of
     an aligned concept member (P1.2 clusters). Text is used AS-IS (not machine translated),
     so `translated=false`; we record the source member gid, its language, and the concept.
  3. native entity name — last-resort fallback.
No LLM-generated text enters the clean corpus (the contaminated `entity_descriptions.json`
is excluded entirely).

Text is kept verbatim — answer mentions are NOT stripped here. Exact/semantic answer
leakage is quantified separately in P1.7 (do not silently edit the snapshot).

Provenance recorded per entity (both hashes kept separately):
  raw_text_hash, norm_text_hash, source, source_url, snapshot_rev, snapshot_date, lang
  (of the text), entity_lang, licence, retrieval_method, fallback_reason,
  cross_lang_source_gid, cross_lang_concept, translated

Snapshot caveat: individual Wikipedia revision ids were not captured at fetch time. The whole
abstract corpus is frozen and `snapshot_rev` = its SHA-256 (corpus-level revision); per-page
revision ids are a recorded provenance gap (see fallback_reason on native entries).

Outputs (DBP5L/ind_v2/descriptions/):
  descriptions_v2.json            {gid: normalized_text}   (this is what models consume)
  descriptions_v2_provenance.json {gid: {...all fields...}}
  descriptions_v2_stats.json

Self-check: `python3 build_v2_descriptions.py --selftest`.
"""
import os
import sys
import json
import time
import hashlib
import argparse
import unicodedata
from collections import defaultdict

LANGS = ["en", "fr", "es", "ja", "el"]
LICENCE = "CC BY-SA 3.0"
RETRIEVAL = "prefetched Wikipedia abstract corpus (entity_descriptions_wiki.json)"


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split()).strip()


def _uri_to_url(uri):
    return uri or None


def build(root):
    proc = os.path.join(root, "DBP5L/processed")
    out_dir = os.path.join(root, "DBP5L/ind_v2/descriptions")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(proc, "entities.json")) as f:
        ents = json.load(f)
    ents = {int(g): e for g, e in ents.items()}
    with open(os.path.join(proc, "entity_descriptions_wiki.json"), "rb") as f:
        wiki_bytes = f.read()
    snapshot_rev = hashlib.sha256(wiki_bytes).hexdigest()
    wiki = {int(k): v for k, v in json.loads(wiki_bytes).items()}
    with open(os.path.join(root, "DBP5L/ind_v2/concepts/entity2concept.json")) as f:
        e2c = {int(k): v for k, v in json.load(f).items()}

    def native_text(g):
        name = (ents[g].get("name") or "").strip()
        t = (wiki.get(g) or "").strip()
        return t if (t and t != name) else None

    # precompute concept -> members with native snapshot text (for cross-lang fallback)
    concept_members = defaultdict(list)
    for g, c in e2c.items():
        concept_members[c].append(g)

    descriptions, provenance = {}, {}
    src_counts = defaultdict(int)
    per_lang_source = defaultdict(lambda: defaultdict(int))
    for g in sorted(ents):
        e = ents[g]
        elang = e["lang"]
        name = (e.get("name") or "").strip()
        cross_gid, cross_concept, text_lang, fallback = None, None, elang, None

        raw = native_text(g)
        if raw is not None:
            source = "wikipedia_native"
            fallback = "per_page_revision_id_not_captured"  # honest snapshot-granularity gap
        else:
            # cross-language snapshot from an aligned concept member (deterministic: min gid w/ text)
            borrowed = None
            for m in sorted(concept_members.get(e2c.get(g, g), [])):
                if m == g:
                    continue
                mt = native_text(m)
                if mt is not None:
                    borrowed = (m, mt); break
            if borrowed is not None:
                cross_gid, raw = borrowed[0], borrowed[1]
                cross_concept = e2c.get(g)
                text_lang = ents[cross_gid]["lang"]
                source = "wikipedia_cross_lang"
            else:
                raw = name
                source = "entity_name"
                fallback = "no_snapshot_text_native_or_crosslang"

        norm = _normalize(raw)
        descriptions[g] = norm
        provenance[g] = {
            "source": source,
            "source_url": _uri_to_url(e.get("uri")),
            "snapshot_rev": snapshot_rev,
            "snapshot_date": None,                 # not captured; corpus frozen by snapshot_rev
            "lang": text_lang,                     # language of the TEXT
            "entity_lang": elang,
            "licence": LICENCE,
            "retrieval_method": RETRIEVAL,
            "fallback_reason": fallback,
            "cross_lang_source_gid": cross_gid,
            "cross_lang_concept": cross_concept,
            "translated": False,                   # cross-lang text borrowed as-is, never MT
            "raw_text_hash": _sha(raw),
            "norm_text_hash": _sha(norm),
        }
        src_counts[source] += 1
        per_lang_source[elang][source] += 1

    def _dump(name, obj):
        p = os.path.join(out_dir, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, sort_keys=True)
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        return h

    h_desc = _dump("descriptions_v2.json", {str(g): descriptions[g] for g in descriptions})
    h_prov = _dump("descriptions_v2_provenance.json", {str(g): provenance[g] for g in provenance})
    stats = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_entities": len(descriptions),
        "snapshot_rev": snapshot_rev,
        "by_source": dict(src_counts),
        "by_language_source": {l: dict(per_lang_source[l]) for l in LANGS},
        "licence": LICENCE,
        "no_llm_text": True,
        "answer_mentions_preserved": True,   # leakage quantified in P1.7, not stripped here
        "hashes": {"descriptions_v2.json": h_desc, "descriptions_v2_provenance.json": h_prov},
    }
    _dump("descriptions_v2_stats.json", stats)
    return stats


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="desc_test_")
    try:
        proc = os.path.join(d, "DBP5L/processed"); os.makedirs(proc)
        conc = os.path.join(d, "DBP5L/ind_v2/concepts"); os.makedirs(conc)
        # 4 entities: 0(en) native text; 1(fr) aligned to 0, no native -> cross-lang from 0;
        # 2(ja) no text, no aligned text -> name; 3(es) native text.
        ents = {"0": {"lang": "en", "name": "Foo", "uri": "http://dbpedia.org/resource/Foo"},
                "1": {"lang": "fr", "name": "Foo_fr", "uri": "u1"},
                "2": {"lang": "ja", "name": "Bar", "uri": "u2"},
                "3": {"lang": "es", "name": "Baz", "uri": "u3"}}
        wiki = {"0": "Foo is a thing.", "1": "Foo_fr", "2": "Bar", "3": "Baz is a place."}
        e2c = {"0": 0, "1": 0, "2": 2, "3": 3}     # 0 and 1 same concept
        json.dump(ents, open(os.path.join(proc, "entities.json"), "w"))
        json.dump(wiki, open(os.path.join(proc, "entity_descriptions_wiki.json"), "w"))
        json.dump(e2c, open(os.path.join(conc, "entity2concept.json"), "w"))

        s = build(d)
        prov = json.load(open(os.path.join(d, "DBP5L/ind_v2/descriptions/descriptions_v2_provenance.json")))
        desc = json.load(open(os.path.join(d, "DBP5L/ind_v2/descriptions/descriptions_v2.json")))
        assert prov["0"]["source"] == "wikipedia_native", prov["0"]
        assert prov["1"]["source"] == "wikipedia_cross_lang" and prov["1"]["cross_lang_source_gid"] == 0
        assert prov["1"]["lang"] == "en" and prov["1"]["entity_lang"] == "fr"
        assert desc["1"] == "Foo is a thing."          # borrowed as-is, normalized
        assert prov["2"]["source"] == "entity_name" and desc["2"] == "Bar"
        assert prov["3"]["source"] == "wikipedia_native"
        # raw vs norm hashes are separate fields and present
        assert prov["0"]["raw_text_hash"] and prov["0"]["norm_text_hash"]
        assert s["no_llm_text"] and s["answer_mentions_preserved"]
        # determinism
        s2 = build(d)
        assert s2["hashes"] == s["hashes"], "description build not deterministic"
        print("build_v2_descriptions self-check OK "
              f"(native/cross-lang/name routing + provenance; sources={s['by_source']})")
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
