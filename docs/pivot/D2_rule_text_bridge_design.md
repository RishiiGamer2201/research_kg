# D2 Design Note: The Rule-to-Text Bridge and Structure-Poor Auditing

Written 2026-07-14. Required by [UNIFIED_PATHWAY.md](UNIFIED_PATHWAY.md) Phase D2 before any
implementation. All numbers below are measured today on the real DBP-5L assets (CPU only), not
assumed. Measurement scripts ran against `DBP5L/processed/*.json` and `DBP5L/ind/{lang}/*`.

Style note: no emojis, no shorthand dashes.

---

## 1. The measured contamination population

Contaminated set: descriptions where `entity_descriptions.json` differs from
`entity_descriptions_clean.json`.

| Quantity | Value |
|---|---:|
| Contaminated descriptions | 2,359 (ja 2,215; el 144) |
| With more than 2 edges (train plus support) | 607 (25.7 percent) |
| With 1 to 2 edges | 111 (4.7 percent) |
| With zero edges | 1,641 (69.6 percent) |
| Zero-edge entities with any cross-lingual alignment | 0 (0.0 percent) |
| Auditable directly from structure | 718 (30.4 percent) |
| Auditable after alignment-based cross-lingual transfer | 718 (still 30.4 percent) |

Two consequences, one negative and one clarifying:

1. **The PDF's cross-lingual structural transfer idea is dead on DBP-5L, measured, not argued.**
   The 1,641 zero-edge contaminated entities have zero alignment links (the alignment table itself
   is healthy: 37,723 pairs, 8,021 distinct ja entities, all ten language pairs populated). The
   entities that lack Wikipedia coverage also lack edges and also lack alignments, because all three
   are symptoms of the same thing: obscurity. There is no aligned high-resource neighbourhood to
   borrow. This falsifies the "borrow aligned structure" mechanism for exactly the population it was
   supposed to rescue. Report this as a finding in the paper; it is the quantitative form of the
   57 percent recall soft spot.

2. **The direct rule audit has a real, worthwhile target: the 30.4 percent.** 718 contaminated
   descriptions sit on entities with at least one edge, 607 of them with three or more. The bridge
   mechanism below applies to them. The remaining 69.6 percent cannot be audited from structure at
   all, by any structural method, and the paper must say so. For them the only evidence channels are
   external lookup (fuzzy match into Wikidata or native Wikipedia, which is simultaneously the repair
   path) or name-only signals, and the honest headline for the paper is the downstream-grounding
   result, exactly as the external gap assessment recommended.

---

## 2. Worked example (real, from the corpus)

Entity ja:39566, "50 フィフティ・フィフティ (2011年の映画)" (the film 50/50), degree 6.

LLM-generated description (contaminated):

> "50 フィフティ・フィフティ is a 2011 Japanese drama film directed by Takashi Miike, based on the
> novel of the same name by Kōji Suzuki. The film stars Hiroki Tamaki ... post-war Japan."

Graph edges for the same entity:

| Edge | Value |
|---|---|
| starring | セス・ローゲン (Seth Rogen) |
| starring | ジョゼフ・ゴードン＝レヴィット (Joseph Gordon-Levitt) |
| starring | アンジェリカ・ヒューストン (Anjelica Huston) |
| starring | ブライス・ダラス・ハワード (Bryce Dallas Howard) |
| language | 英語 (English) |
| distributor | サミット・エンターテインメント (Summit Entertainment) |

Every load-bearing claim in the fabricated text maps to a relation the graph populates with a
contradicting value: claimed director and claimed cast versus actual starring edges, claimed
"Japanese drama" versus `language: English`. The disagreement is computable without knowing an LLM
wrote the text.

A second example shows the required nuance: ja:39560 ("2046") has a fabricated SARS-pandemic framing,
but its named director and cast are correct and the edges confirm them. Claim-level scoring must
therefore aggregate carefully: one strongly contradicted claim should be able to flag a description
even when other claims verify.

---

## 3. The bridge mechanism (claim-level, three steps)

Rules and edges speak about triples; descriptions are text. The bridge converts the description into
candidate triples and scores each against structural evidence.

Step 1, claim extraction. From the description, extract typed claims: (entity, relation-like
predicate, value) tuples such as (X, director, "Takashi Miike"), (X, type, "drama film"),
(X, country/language, "Japanese"). Extractor options, in order of preference: (a) a small local LLM
constrained to a fixed relation vocabulary (the 358 DBP-5L relations have names in
`relation_names.json`); (b) pattern-based extraction for the dominant biography-style claims
(profession, nationality, director, author, location). The extraction target vocabulary is the KG
relation set, which makes the next step trivial.

Step 2, per-claim structural scoring. For each extracted claim (e, r, v):
- Direct check: if the graph has (e, r, x) edges, compare x against v (string plus embedding match).
  Contradiction when values are disjoint and r is functional or near-functional (director, language).
  This needs no rules at all, only edges; it covers the 50/50 example.
- Rule check (RuleTrust reuse): when the graph lacks r-edges for e, score the plausibility of
  (e, r, v) with the mined entity-independent rules over whatever edges e does have, exactly the
  `build_rule_target_score` machinery from Phase B. A claimed relation whose rule-implied plausibility
  given the observed edges is near zero is evidence against the claim. This is where the measured
  inductive-transfer property (rule AUC 0.680 on unseen entities) pays off: contaminated entities are
  exactly "unseen-like," structure-poor nodes.

Step 3, aggregation to a description-level score. A description's contamination score combines: the
count and strength of contradicted claims (weighted by relation functionality), the fraction of claims
with no supporting evidence, and the existing neighbourhood-consistency score (the current detector).
Aggregation must let a single hard contradiction dominate (the 2046 case).

Coverage statement to report with the method: applicable to the 30.4 percent of contaminated entities
with edges; the zero-edge remainder is handled by external-evidence lookup or declared unauditable,
with the split reported per language.

---

## 4. What this changes in the plan

- UNIFIED_PATHWAY Phase D2: the "cross-lingual structural transfer" task is replaced by the measured
  negative finding (this note, Section 1). The novelty claim for structure-poor auditing shifts from
  "borrow aligned neighbourhoods" to "claim-level rule evidence that transfers to structure-poor
  entities, plus an honest, quantified coverage limit."
- The three-way evidence hierarchy for the paper: direct edge contradiction (strongest, needs edges of
  the claimed relation), rule plausibility (works with any edges), external lookup (works with none,
  doubles as repair).
- Every number in Section 1 is a paper table row: the contamination population census by structure
  availability is itself a contribution, because it quantifies why detection in low-resource languages
  is hard.

## 5. Verification plan for the bridge (before any big run)

- Unit: claim extractor on the 2,359 contaminated plus a matched clean sample; report claims per
  description and extraction precision on 50 hand-checked cases.
- The decisive cheap test: on the 718 structurally auditable contaminated descriptions versus 718
  matched clean descriptions of similar degree, does the claim-level score separate them better than
  the current neighbourhood detector alone? All CPU except the extractor; if the extractor is the
  local Llama, it waits for GPU availability, the pattern-based variant does not.
