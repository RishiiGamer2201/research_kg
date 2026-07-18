# DBP5L-Ind v2 — Dataset Card (P1.8)

Concept-disjoint, evidence-budgeted, multilingual **entity-inductive** KGC benchmark derived
from DBP-5L. Built to replace the v1 split, whose "unseen" test concepts leaked into training
72.3% of the time (R-024).

## Languages & size
- Languages: **EN, FR, ES, JA, EL** (5).
- **56,589** entities · **185,866** triples · **903** relations · **29,440** concepts
  (9,762 multilingual size 2–5, 19,678 singletons; 0 same-language-collision concepts).
- Per language (entities / triples): EN 13,996/68,187 · FR 13,176/40,007 · ES 12,381/44,985 ·
  JA 11,805/22,271 · EL 5,231/10,416.
- Degree: median 5, p95 23, max 3,911. Relations: 335/903 have ≤2 triples (long tail).

## Intended use
Evaluate multilingual KGC on **unseen real-world concepts** (not just unseen IDs), under
explicit evidence budgets, with head + tail prediction, and with declared text-leakage /
structural-shortcut controls. Diagnostic tracks isolate reasoning from answer-mention reading.

## Identity layers (originals preserved)
URI (canonical DBpedia) → (lang, local_id) upstream → global_id → concept_id (min global id in
an alignment component). All recoverable from `processed/entities.json`. Relations kept verbatim
and serialized injectively `R{id}__name` (P0.4).

## Concepts & folds
- Concepts = connected components of the alignment graph (union-find, P1.2).
- **3 fixed folds**, seeds **[13, 42, 79]**; whole concepts split (never entity IDs), stratified
  by language coverage. Per fold: **train 22,082 / valid 2,943 / test 4,415 concepts** (75/10/15).
  Validation is inductive (disjoint from train); all 5 languages present in valid+test.
  `assert_concept_disjoint` passes on every fold.

## Evidence budgets (S⁰ ⊂ S¹ ⊂ S³ ⊂ S⁵)
Per unseen entity, one deterministic ordered support pool (train-connected edges first);
budgets expose prefixes k∈{0,1,3,5}. **Comparability rule:** the S⁵ union is selected first and
removed from eval targets for *every* budget; one complete known-fact filter (single hash) is
used across all budgets; only exposed evidence varies. Per fold: ~10,399 unseen entities with
support, avg pool 3.81, S⁵ union ~39k, eval_targets_test ~37k.

## Tracks (each hashed)
| Track | Description view | Note |
|---|---|---|
| **primary** (alignment-free) | `descriptions_v2_primary.json` | native Wikipedia → **native name** for cross-lang (0 cross-lang usage asserted) |
| **oracle-alignment** (diagnostic) | `descriptions_v2.json` | cross-language snapshot text allowed; never the headline |
| **alias-masked** (diagnostic) | `descriptions_v2_masked.json` | neighbour names+aliases → `[ENT]` (14.2% text removed); leak-free lower bound |
| **missing-text** | `descriptions_v2_missing_text.json` | name-only |
| **inverse-clean support** | `support_pool_inverse_clean.json` | answer-adjacency edges removed before prefixing |
| **train graph-text** (aug) | per-fold `train_graphtext.json` | train edges only |
| **corruption** | — | **Phase 4** (needs human annotation) |
Directions: **head, tail, combined** reported separately (reciprocal `reverse of` marker in
train + eval). Candidate universes: within-language (×5) + all-language, independent hashes.

## Descriptions & provenance
48,496 native Wikipedia / 4,274 cross-language / 3,819 name-only. **No LLM text.** Per-entity
provenance keeps raw+normalized hashes separately, source, URL, snapshot_rev, lang+entity_lang,
licence, retrieval method, fallback reason, and cross-language source gid/concept + translated.

## Known leakage / shortcut audits (reported, not hidden)
- **Answer mention** (natural text): overall exact 39.0% / semantic-subset 26.6%; **tail 63.1%
  vs head 14.9%**; native 41.0% / cross-lang 1.7% / name 3.4%. Use mentioned/unmentioned metrics
  and the alias-masked track for leak-free evaluation. Natural-text MRR is **not** pure
  relational generalization.
- **Inverse/reciprocal support**: 7.2–7.6% test / 9.7–11.2% valid targets have answer revealed
  by h↔t adjacency in exposed support → inverse-clean support track provided.
- **PPR / shortest-path** (relation-free, answer edges excluded): MRR 0.05–0.06 ≈ degree
  baseline 0.06–0.076 ≫ random 0.001, but **≪ text 0.27**; no relation-level outliers. Structure
  does not explain text performance (not "no shortcut" absolutely).
- **Duplicates**: 3,767 duplicate-description groups; 8,082 duplicate-name groups (mostly
  cross-language aligned concepts). **Inverse relations**: 20 strong pairs, 2,441 reciprocal
  same-relation triples.

## Corruption taxonomy (declared here; data + annotation guide = Phase 4)
Held-out corruption families for the self-healing track, in increasing difficulty:
1. **Missing** — description removed (name-only); see the missing-text track.
2. **Easy sanity** — random wrong-entity description.
3. **Hard semantic swap** — type/language/length/popularity-matched wrong entity.
4. **Claim-level edit** — alter one verifiable date/place/type/occupation/creator/relation,
   fluent style preserved.
5. **Multi-generator** — descriptions from multiple model families/prompts, source facts
   hidden or contradicted.
6. **Observed-source** — source-verifiable naturally missing/outdated/mistranslated text.
Corruption families and generators are **held out** from training. Annotation target: 500–1,000
twice-labelled multilingual cases with adjudication (Phase 4); the full annotation guide (label
schema, adjudication rules, per-language calibration) is produced with that data.

## Licence & redistribution
DBpedia-derived → **CC BY-SA 3.0**: attribute DBpedia + KEnS/DBP-5L, share-alike, state changes
(concept clustering, concept-disjoint re-split, support budgets, description rebuild). See
`wsl/research_kg/DBP5L_DATA_PROVENANCE.md`.

## Limitations
- Per-page Wikipedia revision IDs not captured; corpus frozen by `snapshot_rev` (content hash) as
  the cutoff mechanism.
- Headline clean 3-seed baseline + trained head/tail/combined numbers on v2 come in **Phase 2**
  (trainer/evaluator fold-wiring). G1 validates the eval harness zero-shot only.
- Corruption track (self-healing) is Phase 4.

## Reproduction (deterministic; run in order, from `~/research_kg`)
```
python3 scripts/data_prep/hash_source_data.py            # source_manifest.json (top 0eca75a5)
python3 scripts/data_prep/build_concept_clusters.py      # concepts (29,440)
python3 scripts/data_prep/build_v2_folds.py              # folds [13,42,79]
python3 scripts/data_prep/build_v2_support_budgets.py    # budgets + inverse-clean
python3 scripts/data_prep/build_v2_descriptions.py       # descriptions + provenance
python3 scripts/data_prep/build_v2_eval_tracks.py        # primary/oracle views + candidates
python3 scripts/data_prep/build_v2_masked_view.py        # alias-masked diagnostic
python3 scripts/data_prep/build_v2_extra_tracks.py       # missing-text + train-graphtext
# audits
python3 scripts/data_prep/audit_v2_answer_leakage.py
python3 scripts/data_prep/audit_v2_structure.py
python3 scripts/data_prep/audit_v2_ppr_shortcut.py
python3 scripts/data_prep/audit_v2_inverse_support.py
```
Hash verification: compare `top_sha256` in `source_manifest.json`, `hashes` in
`concept_stats.json`, and each `fold_manifest.json` / `budget_manifest.json` / view stats. Every
builder has a `--selftest`.
