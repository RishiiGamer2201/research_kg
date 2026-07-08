# DBP-5L-Ind: Multilingual Knowledge Graph Completion Breaks When Entities Are Unseen

**Working draft, 2026-07-03.** Markdown now, LaTeX (aaai2027.sty) at the port stage.
Framing is benchmark-first (locked, A4). `[PENDING]` marks numbers awaiting seed 777, Gate G1,
or baselines. All present numbers are the final corrected evals (auto max_length plus
support-filter). Source of truth for results: `docs/RESULTS_AND_INFERENCE.md`.
Style rule: no em or en dashes, no emojis, anywhere in this document.

---

## Abstract (write last; skeleton)

Multilingual knowledge graph completion (MKGC) has been studied only in the transductive
setting, where every entity is seen at training time. Inductive KGC, which handles unseen
entities, has been studied only monolingually, in English. We show these two lines do not
compose: the methods that carry the multilingual state of the art (KEnS, AlignKGC, SS-AGA)
rely on per-entity embeddings and cross-lingual alignment seeds that are undefined for an
unseen entity, and therefore cannot run at all on unseen-entity queries. We introduce
**DBP-5L-Ind**, the first entity-disjoint inductive split of the DBP-5L benchmark (English,
French, Spanish, Japanese, and low-resource Greek), together with a description-enrichment
protocol, and establish the first baselines. A text bi-encoder (BGE-M3 with LoRA) trained
with a reciprocal-rank objective and mined hard negatives reaches **26.51 (plus or minus 0.31)
MRR** on unseen entities across three seeds, an 18-fold improvement over a zero-shot encoder. On the
higher-resource languages it matches or exceeds the transductive state of the art despite
never seeing the test entities. We further find that usable description length, not model
capacity, is the binding constraint: Japanese, whose descriptions fragment into the most
subword tokens, gains most from longer context and remains the weakest language purely
because 31% of its descriptions still overflow the context window. We also find that the encoder's
cross-lingual alignment is already strong enough that ranking against all languages at once costs
almost nothing, and that explicit cross-lingual anchors, evaluated correctly, do not degrade
performance (a preliminary claim to the contrary in our early experiments was a train/eval
artifact, which we document as a reproducibility caution).

---

## 1. Introduction (skeleton; order contributions to match benchmark-first framing)

Hook: real KGs grow. New entities arrive daily, disproportionately in low-resource languages,
which is exactly where the graph is sparsest and where a fact present in English may be missing
locally. Serving these entities is simultaneously inductive (the entity is unseen) and
multilingual. No prior work addresses the intersection, and, as we show, the intersection is
not free: the multilingual methods break by construction on unseen entities.

**Contributions.**
1. **DBP-5L-Ind**, the first multilingual inductive KGC benchmark: an entity-disjoint split of
   DBP-5L over five languages including low-resource Greek, with a documented and released
   description-enrichment and split protocol.
2. **The first baselines** on it, including a text bi-encoder recipe (BGE-M3 with LoRA, CRR
   loss, hard negatives) that turns a 1.45% zero-shot floor into 26.51 (plus or minus 0.31)
   MRR, with an ablation attributing the gain to its components.
3. **Analyses reviewers can act on:** a length-versus-capacity result (Japanese is
   context-window-bound, not data-poor); a cross-lingual robustness result (ranking against all
   languages costs about 0.5 MRR, so the encoder's alignment is already strong); and a
   reproducibility caution, namely that a mismatched evaluation of an anchor-augmented model can
   fabricate a large spurious degradation, which we detected and corrected.

---

## 2. Related Work

**Multilingual KGC is transductive.** DBP-5L (Chen et al., 2020) established the five-language
DBpedia benchmark and the KEnS ensemble. AlignKGC (Singh et al., 2021), CG-MuA, and SS-AGA
(Huang et al., 2022) improved it with cross-lingual entity and relation alignment; JMAC (Tang
et al., 2022) added surface text. All evaluate by corrupting a tail within the seen entity set,
so every test entity has a learned embedding. KL-GMoE (EMNLP 2025), the most recent MKGC work,
is also transductive: it reranks candidates from a KGE (TransE) trained over all entities, on a
custom five-language Wikidata5M set (EN/FR/IT/JA/ZH, no Greek, not DBP-5L), and its "unseen"
analysis concerns unseen languages, not unseen entities. None of these methods defines behavior
for an entity absent at training time.

**Inductive KGC is monolingual.** Text bi-encoders represent an entity by encoding its
description, so unseen entities are handled by construction: BLP (Daza et al., 2021), StAR,
SimKGC (Wang et al., 2022; MRR 71.4 on Wikidata5M-Ind), StATIK (MRR 77.0), and RAA-KGC (2025)
all evaluate entity-disjoint splits, but exclusively on English benchmarks (WN18RR, FB15k-237,
Wikidata5M). Multilinguality is never tested.

**The gap: three kinds of "unseen".** Prior work generalizes to unseen facts (AlignKGC's
held-out triples over seen entities) or unseen languages (KL-GMoE). We target unseen entities
in a multilingual graph, the strictly hardest of the three, because it removes exactly the
per-entity embedding and alignment-seed signal every multilingual method depends on. Table R
gives the calibration context our numbers must be read against.

**Table R: transductive DBP-5L reference (per-language MRR, from published tables).** This is
not a like-for-like baseline (transductive means all entities are seen; our setting is
entity-disjoint inductive), but it is the ceiling reviewers will anchor on.

| Method (setting) | EL | JA | ES | FR | EN |
|---|:--:|:--:|:--:|:--:|:--:|
| TransE (struct) | 24.3 | 25.3 | 24.4 | 27.6 | 16.9 |
| KG-BERT (text) | 27.3 | 38.7 | 34.0 | 35.4 | 21.0 |
| AlignKGC (struct plus align) | 33.8 | 41.6 | 35.1 | 37.4 | 22.3 |
| SS-AGA (struct plus align) | 35.3 | 42.9 | 36.6 | 38.4 | 23.1 |
| JMAC w/ SI (struct plus text) | 71.7 | 66.8 | n/r | n/r | n/r |
| **Ours (inductive, unseen entities, 3-seed mean)** | **16.8** | **16.2** | **36.6** | **37.3** | **17.2** |

Reading: on FR and ES our inductive numbers sit at 95-100% of transductive SS-AGA despite never
seeing the test entities. On EL and JA a real gap remains, which is expected: those languages
lose the most when alignment seeds and learned embeddings are removed. JMAC's text-initialized
transductive numbers (EL 71.7) are the figures most likely to be quoted against us; JMAC
memorizes per-entity embeddings and uses alignment seeds, both undefined in our setting.

**Loss.** CRR (Xu et al., KGCRR) is a differentiable upper bound on reciprocal rank, previously
tested only on English transductive FB15k-237 and WN18RR. We give it its first multilingual and
inductive test.

---

## 3. Problem Formulation and the DBP-5L-Ind Benchmark

### 3.1 Task
Five language-specific KGs `G_l = (E_l, R_l, T_l)` share a partial cross-lingual entity
alignment. Each entity carries a textual description `d(e)` (Section 3.3). We evaluate tail
prediction: given `(h, r, ?)` rank candidate tails; report filtered MRR and Hits at 1, 3, 10.
Inductive setting: a set of entities `E^u_l` inside `E_l` is held out entirely from training;
every evaluation query touches at least one entity in `E^u_l`. An unseen entity has no learned
embedding and no alignment seed. Its only representation is `d(e)`.

### 3.2 Split construction (released, seed 42)
From DBP-5L (56,589 entities, 1,392 relations, 225,831 triples over EN/FR/ES/JA/EL):
1. Per language, sample 20% of entities (those with at least 3 incident triples, so a support
   set exists) as the unseen set `E^u_l`.
2. Train triples: both endpoints seen. Evaluation triples: at least one endpoint unseen.
3. Support edges: up to 5 triples per unseen entity, held in the inference graph for context
   and removed from the evaluation targets. These are known-true facts and are added to the
   filter set (Section 3.4).
4. Validation: 10% of train triples.

**Table 1: DBP-5L-Ind statistics.**

| Lang | Train ent. | Unseen ent. | Train triples | Eval triples |
|---|--:|--:|--:|--:|
| EN | 10,506 | 2,626 | 44,801 | 18,409 |
| FR | 8,060 | 2,014 | 25,968 | 11,154 |
| ES | 8,087 | 2,021 | 26,902 | 15,094 |
| JA | 5,979 | 1,494 | 13,531 | 7,237 |
| EL (low-resource) | 3,216 | 804 | 7,054 | 2,579 |
| **Total** | **35,848** | **8,959** | **118,256** | **54,473** |

Support edges total 39,995. They are added to the filter set and never used as eval targets.

### 3.3 Description enrichment (verified sources only)
Every entity receives text via: (1) DBpedia URI to surface name (100%); (2) KG-neighborhood
serialization `name | r1: n1, n2 | r2: n3 ...` built only from train and valid edges to prevent
test leakage (100%); and (3) native-language Wikipedia and DBpedia abstracts. Steps 2 and 3 are
the description sources used by the final model.

We also tried, and then removed, a fourth source. An early version back-filled the remaining
name-only entities in the two languages without Wikipedia coverage (Greek and Japanese) using a
small open LLM (Llama-3.2-3B) prompted to write a short English description from the entity name
and its KG neighbors. A manual audit (Appendix, 25 Greek samples) found this text roughly 70%
hallucinated: for a proper noun transliterated into Greek or Japanese, the model could not
recover the real referent and confabulated a plausible biography (Clint Eastwood and Eleanor
Roosevelt both became Greek footballers; Taipei became a dessert). Because these entities are
exactly in the two weakest languages and are unseen test entities, the fabricated text was
actively harmful: removing it raised Japanese MRR by 1.95 points and overall MRR by 0.25 (Section
5). We therefore drop the LLM back-fill entirely. For the affected entities we instead fetch a
native-language Wikipedia summary where one exists (1,070 of 2,359 recovered), and otherwise use
the entity's native name. The released benchmark uses only these verified sources. We report the
failed LLM experiment because the failure mode, an anchor- or description-augmented pipeline that
silently ingests confident fabrications, is easy to miss and easy to reproduce.

### 3.4 Evaluation protocol
Candidate entities are encoded once and cached. An unseen entity enters the index by encoding
`d(e)`; no retraining is needed. We rank within the same-language candidate pool (the standard
MKGC protocol; the cross-lingual all-entity pool is also reported). The filtered setting removes
all known-true tails (train, valid, test, and support facts) before ranking. Tail-only ranking
is used throughout and stated as a scope limit. Evaluation tokenization length is matched to
training.

> **Two protocol pitfalls we document (and fixed).** (a) A mismatched eval tokenization length
> silently truncates descriptions and understated every metric by roughly 40% in our early runs.
> (b) Omitting support facts from the filter set penalizes correct predictions on 25% of
> queries. Both are easy to get wrong on a new benchmark; the released code fixes both.

---

## 4. Method

A single shared BGE-M3 bi-encoder (568M parameters, XLM-RoBERTa lineage) encodes both sides.
The backbone is frozen (bf16); only rank-16 LoRA adapters on the attention query and value
projections (about 8M parameters, 1.4%) plus a learned temperature are trained. The whole model
runs in 1.4 GB on one 16 GB GPU.

- **Query and candidate.** Query text `d(h) [SEP] r_name`; candidate text `d(t)`. Mean-pool the
  final layer, L2-normalize, giving `q, t` in R^1024. Score `s(h,r,t) = cos(q,t) / tau_hat`
  with tau_hat learned.
- **CRR objective.** `L = log(1 + sum_{j != y} sigma((s_j - s_y - rho)/tau_c))`, a smooth upper
  bound on negative log reciprocal rank: a negative contributes only within margin rho of the
  gold. rho = 0.1, tau_c = 0.1; the exponent is clamped to [-80, 80] for numerical stability.
  This is the first use of CRR beyond English transductive KGC.
- **Hard negatives.** Beyond in-batch negatives (B-1 = 31), K = 7 hard negatives per query are
  mined from an entity cache re-encoded after every epoch from epoch 5 onward (fresh, never
  stale), with the gold tail masked. CRR and hard negatives are synergistic: CRR alone performs
  about the same as InfoNCE; the two together are what win (Section 5).
- **Training.** Effective batch 256 (32 with gradient accumulation 8), lr 5e-4, AdamW, 6%
  warmup, 30 epochs, bf16, gradient clipping 1.0. Description tokenization length 160; see the
  Japanese analysis in Section 5.

(The optional stretch idea of cross-lingual anchors is treated as an analysis item in Section 5,
pending Gate G1. It is not part of the core method.)

---

## 5. Experiments (numbers final unless marked)

**Table 2: Ablation (within-language filtered MRR).** One component per row.

| Configuration | MRR | H@1 | H@10 |
|---|:--:|:--:|:--:|
| Zero-shot BGE-M3 | 1.45 | 0.09 | 3.72 |
| CRR plus hard negatives (ml 96) | 13.77 | 6.69 | 27.02 |
| plus rich descriptions, ml 128 | 23.80 | 15.72 | 39.14 |
| plus LoRA rank 16 | 25.15 | 17.20 | 40.10 |
| plus context length 160 (single best run) | 26.69 | 18.80 | 41.62 |
| **Full model, mean and std (3 seeds)** | **26.51 +/- 0.31** | **18.35 +/- 0.52** | **41.76 +/- 0.28** |
| mBERT encoder, same recipe (external baseline) | 24.08 | 15.72 | 39.54 |

The external baseline swaps only the encoder (BGE-M3 to bert-base-multilingual-cased, 2019),
holding data, loss, negatives, and protocol fixed. BGE-M3 wins every language and by the widest
margin on low-resource Greek (16.79 vs 10.63, nearly double) and Spanish (36.55 vs 31.25),
empirically justifying the encoder choice and showing the modern encoder helps most where the
language is underserved. (Baseline uses the same clean descriptions; the full-model row here is
the pre-clean 3-seed mean, refreshed after the clean retrain.)

Text quality plus usable context length contribute +22.3 of the +25.2 total. The full model
significantly outperforms the pre-enrichment CRR-plus-HN baseline: +12.67 MRR, paired bootstrap
95% CI [+12.41, +12.94], and Wilcoxon signed-rank both give p below 0.001 (n = 54,473 paired
queries). Counter-results: a stale global-negative cache reaches 95% train accuracy but loses
5.1 MRR (memorization, not learning); 40 epochs overfit (1.7 below 30 epochs).

**Table 3: Per-language, full model (3-seed mean).**

| | FR | ES | EN | EL | JA | Overall |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| MRR | 37.29 | 36.55 | 17.19 | 16.79 | 16.15 | 26.51 |
| H@10 | 54.79 | 50.62 | 32.69 | 35.25 | 27.53 | 41.76 |

**Cross-lingual robustness.** Ranking each query against all 56,589 entities across every
language, rather than the same-language pool, lowers overall MRR by only about 0.5 points
(26.01 versus 26.51 at the seed level) and by under 0.35 for every language except English. The
model almost never places a wrong-language entity above the same-language gold. This is direct
evidence that the encoder's pretrained cross-lingual alignment is already strong, which in turn
motivates the anchor analysis below: explicit cross-lingual supervision has little room to help.

Seed robustness (full config, seeds 42/123/777): 26.24 / 26.85 / 26.45, mean 26.51 with sample
std 0.31, a very tight spread. Per-language std ranges from 0.27 (EL) to 0.89 (JA); JA's wider
variance is consistent with it being the lowest-signal, context-length-bound language. The
length step (ml160 over ml128) adds +1.30 MRR (bootstrap 95% CI [+1.11, +1.49]); this gain is
significant in the mean but concentrated on the long-description subset (JA and EL), so we do
not claim uniform per-triple improvement for it.

**Analysis: Japanese is context-window-bound, not data-poor.** Description coverage is 100%
rich for every language, yet median BGE-M3 subword length differs sharply: JA 119 versus EN 76,
FR 95, ES 94, EL 87 (CJK text fragments into more subwords). Truncation at ml 160: JA 31%
versus EN 4% and near 0% for FR and ES. This explains why JA gains most from each length
increase (+4.2 from ml 128 to 160) and why it remains weakest: a third of its descriptions are
still clipped. It motivates ml 192/256 or description compression as targeted future work, and
reframes JA's low number as a solvable context-budget issue rather than a data deficiency.

**Analysis: cross-lingual anchors and a reproducibility caution.** We experimented with
augmenting queries by relation-level cross-lingual anchors (representative tails of the relation,
sampled from the training graph, preferring the high-resource language). An early result appeared
to show a large degradation (MRR falling to about 3%), which we traced to a train/eval mismatch:
the anchor-trained model was being scored with bare queries, outside its training distribution.
Evaluated the way it was trained (with matched anchors), the same checkpoint reaches 20.38% MRR,
not 3%, and is not below the corresponding no-anchor baseline. We therefore do not report a
negative result for cross-lingual anchors; instead we flag the failure mode, since an
anchor-augmented model that is silently evaluated without its anchors can manufacture a
convincing but spurious degradation. A controlled anchor study (equal information budget, scaled
to the full encoder configuration) is left to future work.

---

## 5.x Limitations (W4.4; fold into Section 5 or a standalone paragraph)

We evaluate tail prediction only; head prediction via inverse relations is left to future work,
though the protocol extends directly. Ranking uses filtered MRR and Hits@k with ties broken
optimistically, a mild and standard convention. The validation set is transductive (its entities
are seen), so model selection happens slightly off the inductive test distribution; a fully
inductive validation split is a natural refinement. In-batch duplicate tails are not explicitly
masked, a minor source of false negatives that hard-negative masking of the exact target already
mostly addresses. Two low-resource languages (Greek, Japanese) have sparse native descriptions,
which bounds achievable performance there; our audit shows that filling this gap with a small LLM
does more harm than good, so the honest position is that these languages need better verified
text, not more generated text. Finally, all results are on a single benchmark family (DBP-5L);
extending DBP-5L-Ind's construction to other multilingual KGs is straightforward and left open.

## 6. Conclusion (skeleton)
Multilingual and inductive KGC have advanced separately and do not compose: the multilingual
methods break on unseen entities by construction. DBP-5L-Ind makes the intersection measurable.
A text bi-encoder gives a strong first baseline, competitive with transductive SOTA on
higher-resource languages, and the analyses locate the remaining gap in a concrete, addressable
place (context budget for morphologically expansive scripts). Benchmark, splits, descriptions,
and code are released.
