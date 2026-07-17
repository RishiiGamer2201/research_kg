# SOTA Benchmark Survey: Inductive, Multilingual, Transductive KGC (2024-2026)

Written 2026-07-17. Purpose: replace the stale SS-AGA (2022) calibration point and map the current
state of the art across the four cells the project touches. Requested because a four-year-old
transductive baseline is no longer a fair or current anchor.

Reliability note: web-search summaries returned at least one impossible number (a claim of 99.8
percent MRR on FB15k-237, which is not physically plausible; real transductive FB15k-237 MRR SOTA is
around 0.36 to 0.42). Numbers below are taken from paper pages where possible and flagged where they
are second-hand or need the PDF to confirm. Verify every figure against the source before it goes in
a paper.

Style note: no emojis, no shorthand dashes.

---

## 0. The one-paragraph answer

For the project's own cell (inductive, multilingual, low-resource) the field is still effectively
empty, which confirms the DBP-5L-Ind gap. But two of the other three anchors have moved and must be
updated: the transductive multilingual DBP-5L anchor is no longer SS-AGA (2022) but SimRMKGC (2025),
and the inductive monolingual anchor is no longer GraIL-era methods but MorsE, CATS, MGIL (2026), and
above all the foundation-model line ULTRA (ICLR 2024). The most consequential finding for the mentor
plan: S2DN, the reproduce-and-beat target, is not the inductive state of the art. Newer methods
report higher numbers on the same FB15k-237 and NELL splits, so "beat S2DN" is not "beat SOTA," and
the comparison set has to widen.

---

## 1. Inductive KGC, monolingual (WN18RR / FB15k-237 / NELL-995, GraIL v1-v4 splits)

This is S2DN's home turf and the ladder's Phase A/B cell.

| Method | Year / venue | Reported strength | Notes |
|---|---|---|---|
| GraIL | 2020, ICML | The subgraph-reasoning baseline | S2DN and everyone else compare to it |
| MorsE | 2022 (Chen et al., arXiv 2110.14170) | Meta-learning inductive embedding; degrades less than GraIL/CoMPILE as the graph gets sparser; +10-15 percent relative on FB15k-237 over KGE backbones | MGIL lists MorsE as the strongest prior baseline on WN18RR and FB15k-237 |
| S2DN | AAAI 2025 (2412.15822) | The project's target. Beats NeuralLP, DRUM, A*Net, CoMPILE, TAGT, SNRI, RMPI | Strong on WN18RR; weaker on FB15k-237/NELL than the 2026 methods below |
| CATS | 2024 (2410.16803) | Context-aware plus LLM type constraints; up to +12 percent on the three datasets | LLM-in-the-loop |
| MGIL | June 2026 (2606.16509) | Current reported SOTA. Hits@10 by version below | Model-graph entity clustering plus GNN |
| ULTRA | ICLR 2024 (Galkin, 2310.04562) | Foundation model; single pretrained model, zero-shot inductive across 57 KGs, about +15 percent relative MRR/Hits@10 over supervised SOTA in zero-shot | Fully inductive (unseen entities AND relations); the paradigm shift |
| SEMMA | 2025 (2505.20422) | Semantic-aware KG foundation model | Continues the ULTRA line |

MGIL Hits@10 by version (from the paper's Table 2):

| Dataset | v1 | v2 | v3 | v4 |
|---|---:|---:|---:|---:|
| WN18RR | 84.86 | 83.90 | 77.02 | 77.81 |
| FB15k-237 | 87.17 | 94.98 | 94.62 | 96.01 |
| NELL-995 | 84.40 | 97.37 | 98.80 | 95.48 |

Compare against S2DN's own reported Hits@10: WN18RR v1 87.64 (S2DN higher than MGIL here),
FB15k-237 v1 67.34 (MGIL 87.17, far higher), v4 91.31 (MGIL 96.01). The WN18RR-versus-FB15k-237
inconsistency is a warning, not a clean verdict: it strongly suggests the two papers use different
evaluation protocols on FB15k-237 (GraIL's 50-negative ranking versus full-candidate ranking, or a
classification-style Hits). Do not claim "MGIL beats S2DN" until the protocols are confirmed
identical. What is safe to say now: S2DN is not obviously the inductive SOTA, and MorsE, CATS, MGIL,
and ULTRA all postdate or outrank it on parts of this benchmark.

Action for the ladder: Phase A reproduction stays valid (reproducing S2DN is still the credibility
floor), but the paper's baseline table for any "beat" claim must include MorsE and at least one
foundation-model point (ULTRA fine-tuned), not just S2DN. Verify the FB15k-237 evaluation protocol
S2DN uses against MGIL/MorsE before writing any comparison.

---

## 2. Multilingual KGC, transductive (DBP-5L)

This is the substrate's calibration cell. The SS-AGA anchor is outdated.

| Method | Year / venue | DBP-5L result | Status |
|---|---|---|---|
| KEnS | 2020, EMNLP | Ensemble knowledge transfer | Original DBP-5L baseline |
| AlignKGC | 2021 | Joint relation+entity alignment | Older |
| SS-AGA | ACL 2022 | The project's current comparison point | SUPERSEDED as anchor |
| JMAC | 2022 | Joint completion + alignment | Older |
| SimRMKGC | 2025, Applied Intelligence (Springer, 10.1007/s10489-025-06782-x) | +4.0 to 7.1 percent MRR and +3.5 to 7.0 percent Hits@1 over prior methods on DBpedia-5L | CURRENT DBP-5L transductive SOTA; use as the new anchor |
| KG-TRICK | COLING 2025 (2501.03560) | Unifies text + relation completion, mBART-large-50, WikiKGE10++ (25k entities, 10 languages) | Evaluated mainly on Wikidata5M/WikiKGE, not DBP-5L primarily |
| KL-GMoE | EMNLP 2025 findings (2510.07736) | Avg MRR 47.86 on its OWN 5-language set (EN/FR/IT/JA/ZH), not DBP-5L | Not a direct DBP-5L comparison; grouped MoE + iterative reranking |

Key correction: SimRMKGC (2025) is the current transductive DBP-5L SOTA and replaces SS-AGA as the
number to calibrate against. Its exact per-language MRR/Hits table is behind the Springer paywall;
the PDF is needed to fill the substrate's calibration table properly. KL-GMoE, despite looking like
the newest multilingual method, uses a different dataset, so it is not a drop-in DBP-5L comparison
(worth citing, not worth calibrating against).

Action: pull the SimRMKGC PDF and record its per-language DBP-5L MRR/Hits@1 as the new transductive
ceiling in RESULTS_AND_INFERENCE. Keep the honest framing already in the substrate docs: these are
transductive (all entities seen) and structurally cannot run in the inductive setting, so they are a
ceiling reference, not a head-to-head competitor.

---

## 3. Inductive multilingual KGC (the project's own cell)

Searched directly (inductive + multilingual + unseen entities + low-resource, 2024-2026). Result:
no method occupies this cell. The nearest things are:

- Foundation models (ULTRA, SEMMA): inductive across graphs and relation vocabularies, but not
  multilingual in the DBP-5L sense (cross-lingual entity alignment, low-resource script transfer).
  They generalize across KGs, not across languages of the same KG.
- KL-GMoE, KG-TRICK: multilingual but transductive (entities seen at training).
- mRAKL (Findings ACL 2025): low-resource multilingual via RAG, but constructs the KG.

Verdict: the inductive-plus-multilingual intersection that DBP-5L-Ind targets remains open. This is
the strongest single piece of evidence for P1 (the benchmark paper). It also means there is no
external baseline that runs natively in the project's exact setting, which is both the opportunity
and the reason the paper must supply the first baselines itself.

Caveat: a fresh sweep is still required immediately before submission; foundation-model papers are
appearing fast and one could annex this cell by adding multilingual pretraining graphs.

---

## 4. Transductive KGC, monolingual (FB15k-237 / WN18RR)

Least central to the project, included for completeness. Honest current range:

- FB15k-237 MRR SOTA is roughly 0.36 to 0.42 (NBFNet about 0.415; ULTRA fine-tuned about 0.37;
  text-based SimKGC about 0.34). WN18RR MRR roughly 0.55 to 0.68 depending on structure- versus
  text-based (SimKGC Hits are high on WN18RR).
- SATKGC (2024, 2407.12703): structure-aware contrastive LM training, about +5 percent Hits@1.
- Adaptive knowledge-distillation structure-text method (accepted Feb 2026): reports beating prior
  on most WN18RR/FB15k-237 splits.
- DISCARD: the "FMS 99.8 percent MRR on FB15k-237" search hit. That number is not physically
  plausible for this benchmark and almost certainly reflects a leakage bug or a misreport. Do not
  cite it.

This cell is mature and crowded; it is a reference range, not a target.

---

## 5. Strategic implications for the plan

1. Update the anchors in RESULTS_AND_INFERENCE and UNIFIED_PATHWAY: transductive multilingual anchor
   becomes SimRMKGC (2025), not SS-AGA (2022). Add the inductive monolingual anchors MorsE, CATS,
   MGIL, ULTRA.
2. S2DN is not the inductive SOTA. Reproducing and beating it is still a valid milestone (the mentor
   asked for it, and it is a defensible engineering floor), but the paper cannot claim SOTA from
   beating S2DN alone. Widen the comparison set, and verify the FB15k-237 evaluation protocol before
   any cross-paper claim.
3. The foundation-model line (ULTRA, SEMMA) is the real threat and the real opportunity. Threat: a
   single pretrained model does zero-shot inductive KGC across arbitrary graphs, which could subsume
   the "train a per-graph inductive model" framing. Opportunity: none of them is multilingual in the
   cross-lingual-alignment, low-resource-script sense, so the project's multilingual-inductive and
   self-healing angles sit outside what foundation models currently do. Position against ULTRA
   explicitly rather than ignoring it.
4. The inductive-multilingual cell is still open, which is the benchmark paper's core justification.
5. Two verification TODOs before any of this is paper-ready: (a) fetch the SimRMKGC PDF for exact
   DBP-5L per-language numbers; (b) confirm MGIL/MorsE evaluation protocol matches S2DN's on
   FB15k-237, since the numbers are not obviously comparable.

---

## 6. Sources

- MGIL, Model Graph Inductive Learning, arXiv 2606.16509 (June 2026).
- S2DN, AAAI 2025, arXiv 2412.15822.
- MorsE, Meta-Knowledge Transfer for Inductive KG Embedding, arXiv 2110.14170 (2022).
- CATS, Context-aware Inductive KGC with Latent Type Constraints, arXiv 2410.16803 (2024).
- ULTRA, Towards Foundation Models for KG Reasoning, arXiv 2310.04562 (ICLR 2024).
- SEMMA, Semantic-Aware KG Foundation Model, arXiv 2505.20422 (2025).
- SimRMKGC, Applied Intelligence, Springer 10.1007/s10489-025-06782-x (2025).
- KG-TRICK, arXiv 2501.03560 (COLING 2025).
- KL-GMoE, arXiv 2510.07736 (EMNLP 2025 findings).
- SS-AGA, ACL 2022, aclanthology.org/2022.acl-long.36.
- SATKGC, arXiv 2407.12703 (2024).
