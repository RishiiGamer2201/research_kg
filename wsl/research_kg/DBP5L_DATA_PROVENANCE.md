# DBP-5L source provenance & licensing (P1.1)

Immutable record of the upstream data DBP5L-Ind v2 is built from. The benchmark is
content-addressed to this snapshot via `DBP5L/ind_v2/source_manifest.json`.

## Upstream
- **Dataset:** DBP-5L (5 languages: EN, FR, ES, JA, EL), derived from DBpedia.
- **Distribution used:** KEnS repository — https://github.com/stasl0217/KEnS (`data/`).
- **Original paper:** Chen, Zhang, Xie, Wu, Deng, Zhang, Chawla, Yu, *"Multilingual Knowledge
  Graph Completion via Ensemble Knowledge Transfer,"* Findings of EMNLP 2020 —
  https://aclanthology.org/2020.findings-emnlp.290/
- **Exact upstream commit:** NOT captured at download time. The immutable anchor for this
  project is the content hash below, not a git ref. TODO(if re-downloaded): pin the KEnS
  commit and confirm it reproduces `top_sha256`.

## Frozen snapshot (this project)
- 31 files, 6,656,272 bytes.
- **`top_sha256 = 0eca75a5a0d5eda7ceff0f9ceab4bf27a682d9b0e3c1d361c2ce202ec9d5f7db`**
  (order-independent hash of all per-file SHA-256s; full listing in `source_manifest.json`).
- Regenerate/verify: `python3 scripts/data_prep/hash_source_data.py`.

Raw layout (`DBP5L/raw/`):
- `kg/{lang}-{train,val,test}.tsv` — per-language triples (local integer ids).
- `entity/{lang}.tsv` — local id → DBpedia URI.
- `seed_alignlinks/{l1}-{l2}.tsv` — cross-language alignment pairs (local ids), 10 pairs.
- `relations.txt` — original relation vocabulary.

## Licensing & redistribution
- DBpedia content is licensed **CC BY-SA 3.0** (and GFDL). DBP-5L, as a DBpedia derivative,
  inherits these terms.
- **Obligations for releasing DBP5L-Ind v2 derived data:** (1) attribute DBpedia and the
  KEnS/DBP-5L authors; (2) release derived data under a **share-alike-compatible** license
  (CC BY-SA 3.0); (3) state changes made (concept clustering, concept-disjoint re-split,
  support budgets, description rebuild). The data card (P1.8) will carry the full attribution
  and license statement.
- Entity **descriptions** are a separate provenance track: the clean v2 descriptions come
  from permitted snapshot text only (P1.5), each with its own source/hash — never released
  as DBpedia-native unless sourced from DBpedia.

## Original identity preserved (do not collapse to processed ints)
- `entity/{lang}.tsv` keeps the **DBpedia URI** — the true original identity — alongside the
  local id. `processed/entities.json` preserves `{lang, local_id, uri}` next to the assigned
  `global_id`. Relation names are preserved verbatim in `relations.txt` and mapped injectively
  (`R{id}__name`, see P0.4), never merged.
- ID layers: **URI** (canonical) → **(lang, local_id)** (upstream) → **global_id** (this
  project's cross-language integer space) → **concept_id** (min global id in an alignment
  component, P1.2). Every layer is recoverable from `entities.json`.
