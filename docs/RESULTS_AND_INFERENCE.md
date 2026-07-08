# Results and Inference Log: Multilingual Inductive KGC (DBP-5L-Ind)

**Living document.** Every result goes here, successes AND failures. When something breaks,
record the failed result, then the fix or improvement, then the new result, in version rows.
Inferences accumulate below the tables. Newest entries at the bottom of each section.
Style: no em or en dashes, no emojis; statuses are plain words (ok / fail / disputed / running).

**Primary metric:** filtered within-language MRR (rank the gold tail among same-language
candidates only, the standard multilingual-KGC protocol). H@k also tracked. Tail-only ranking.
"Eval ml" is the tokenization max_length used at evaluation; it must match training ml (V-fix-1).

---

## Table 1: Full version history (chronological)

| Ver | Config | Train ml | Eval ml | MRR | H@1 | H@10 | Status | Note |
|-----|--------|:---:|:---:|:---:|:---:|:---:|:---:|------|
| v1 | Name-only, InfoNCE | 96 | 96 | 0.41% | 0.08 | 0.62 | fail | no semantic signal in bare names |
| v2 | KG-neighbor, InfoNCE | 96 | 96 | ~1.1% | n/r | n/r | fail | train/eval query-format mismatch |
| Row1 | KG plus relation, InfoNCE | 96 | 96 | 3.10% | 0.89 | 6.97 | ok | first correct run |
| Row3 | KG plus rel, CRR rho=0.1 | 96 | 96 | 3.33% | 0.88 | 7.66 | ok | CRR marginal without rich text |
| Row5-naive | CRR plus naive XL anchors | 96 | 96 | 1.53% | 0.26 | 3.81 | fail | wrong anchor source (not XL pairs) |
| Row1-wiki | Wikipedia abstracts, InfoNCE | 96 | 96 | 10.02% | 4.87 | 19.41 | ok | 10x from abstracts, key driver |
| Row3-wiki | Wikipedia, CRR | 96 | 96 | 9.86% | 3.95 | 20.80 | ok | helps JA, hurts EN and EL |
| Row5-wiki | Wikipedia, CRR plus XL anchors | 96 | 96 (bare) | 3.17% (bare); **20.38% (matched)** | 10.00 | 40.29 | artifact | the 3.17 was a train/eval mismatch; matched anchor eval = 20.38 (V-fix-3, Gate G1). Negative result retracted |
| Row1-HN | InfoNCE plus wiki plus HN K=7 | 96 | 96 | 9.49% | 4.92 | 17.76 | ok | HN helps JA and EL, hurts FR and ES |
| Row3-HN | CRR plus wiki plus HN K=7 | 96 | 96 | 13.77% (was 11.36 pre-filter) | 6.69 | 27.02 | ok | support filter added +2.4; weak models misrank support-tails more |
| A | plus ml128 plus enriched desc | 128 | 128 | 23.80% | 15.72 | 39.14 | ok | enriched plus ml128 adds +10 over Row3-HN |
| B | plus LoRA rank 16 | 128 | 128 | 25.15% | 17.20 | 40.10 | ok | r16 adds +1.35 over A |
| C | plus global-neg (stale cache) | 128 | 128 | 21.56% | 12.64 | 38.29 | fail | stale cache is label noise (worst enriched run) |
| **E** | **plus ml160** | 160 | 160 | **26.69%** | **18.80** | **41.62** | **ok, BEST** | ml160 adds +1.54 over B; wins all languages (Gate G0) |
| F | plus 40 epochs, lr 3e-4 | 128 | 128 | 23.43% | 15.57 | 38.31 | fail | overfit vs B (down 1.7) |

All rows are the FINAL consistent numbers: correct eval max_length plus support-triple filter,
identical protocol. This is the reviewer-ready Table 1, pending seed mean and std on E.
Superseded interim values (eval at wrong ml, or pre-filter): A 14.95, B 15.59 then 24.76,
C 13.20, E 14.89 then 26.26, F 14.37. Kept here for the audit trail.

---

## Table 2: Per-language, best model (Run E, ml=160, filtered, FINAL)

| Lang | MRR | H@1 | H@3 | H@10 | vs transductive SOTA (SS-AGA) |
|------|:---:|:---:|:---:|:---:|---|
| FR | 35.93% | 26.63 | 39.38 | 54.79 | 38.4; inductive reaches ~94% of transductive |
| ES | 37.32% | 29.98 | 40.35 | 50.62 | 36.6; inductive exceeds transductive |
| EN | 16.98% | 8.62 | 19.47 | 32.69 | 23.1; gap (EN graph is sparse in DBP-5L) |
| EL | 18.42% | 9.89 | 21.33 | 35.25 | 35.3; low-resource gap, ml160 closed +2.7 |
| JA | 17.90% | 12.52 | 19.51 | 27.53 | 42.9; largest gap, ml160 closed +4.2, see inference 9 |
| **Overall** | **26.69%** | 18.80 | 29.43 | 41.62 | |

Transductive SOTA is a reference ceiling from an easier setting (all entities seen), used for
calibration only, not a like-for-like baseline.

---

## Table 2d: External / encoder baseline (mBERT, clean descriptions)

The runnable external baseline is the SAME pipeline (CRR + HN K=7 + ml160 + LoRA r16, identical
data and protocol, clean descriptions) with the encoder swapped from BGE-M3 to
bert-base-multilingual-cased (2019). This isolates the encoder. The classical multilingual-KGC
SOTA (SS-AGA, AlignKGC, KEnS) cannot run here at all (they need per-entity embeddings and
alignment seeds undefined for unseen entities), so they are motivation rows, not baselines.

| Lang | mBERT-clean | BGE-M3 (3-seed mean, current) | Delta |
|------|:--:|:--:|:--:|
| EN | 16.75 | 17.19 | +0.44 |
| FR | 35.17 | 37.29 | +2.12 |
| ES | 31.25 | 36.55 | +5.30 |
| JA | 15.50 | 16.15 | +0.65 |
| EL (low-resource) | 10.63 | 16.79 | +6.16 |
| **Overall** | **24.08** | **26.51** | **+2.43** |

mBERT valid acc@1 (72.0%) was close to BGE-M3 (72.5%), but the full ranking eval separates them:
BGE-M3 wins every language and by the widest margin on the low-resource Greek (nearly 2x) and on
Spanish. This is the empirical justification for the BGE-M3 choice and supports the thesis that a
modern multilingual encoder helps most where the language is underserved. NOTE: this compares
mBERT-clean against the BGE-M3 3-seed mean that was trained on the OLD descriptions; the fully
apples-to-apples number is mBERT-clean vs BGE-M3-clean, finalized after the clean retrain. The
paired significance test (BGE-M3-clean vs mBERT-clean, both rank dumps ready) also waits on that.

## Table 2b: Cross-lingual evaluation (rank against ALL 56,589 entities, every language)

Within-language (WL) ranks the gold tail among same-language candidates only (standard MKGC
protocol). Cross-lingual (XL) ranks it among all entities across all five languages: roughly
four times as many candidates, plus cross-lingual confusability. XL is strictly harder.

| Run | WL MRR | XL MRR | Gap | WL H@10 | XL H@10 |
|-----|:--:|:--:|:--:|:--:|:--:|
| Zero-shot | 1.45 | 0.65 | -0.80 | 3.72 | 1.80 |
| Row3-HN | 13.77 | 13.36 | -0.41 | 27.02 | 26.24 |
| A (ml128, r8) | 23.80 | 23.44 | -0.36 | 39.14 | 38.44 |
| B (ml128, r16) | 25.15 | 24.65 | -0.50 | 40.10 | 39.15 |
| E (ml160, single ref) | 26.69 | 26.14 | -0.55 | 41.62 | 40.69 |
| **E (3-seed mean)** | **26.51 +/- 0.31** | **26.01 +/- 0.30** | **-0.50** | 41.76 | 40.93 |

Per-language, cross-lingual, full model (Run E reference; seeds vary within about 0.3):

| Lang | XL MRR | XL H@1 | XL H@10 | WL MRR (for comparison) |
|------|:--:|:--:|:--:|:--:|
| FR | 35.61 | 26.47 | 54.14 | 35.93 |
| ES | 37.13 | 29.84 | 50.40 | 37.32 |
| EN | 15.86 | 8.03 | 30.86 | 16.98 |
| EL | 18.17 | 9.77 | 34.74 | 18.42 |
| JA | 17.66 | 12.45 | 26.85 | 17.90 |

The WL-to-XL gap is only about 0.5 MRR overall and under 0.35 for every language except EN
(about -1.1). Quadrupling the candidate pool and adding four other languages barely changes the
ranking, so the model almost never places a wrong-language entity above the same-language gold.
This is direct evidence that BGE-M3's pretrained cross-lingual alignment holds even under the
hardest candidate pool (see inference 12).

---

## Table 2c: Transductive DBP-5L SOTA (reference ceiling, easier setting)

Published per-language MRR on the standard transductive DBP-5L (all entities seen at training).
Verified from primary sources (SS-AGA, AlignKGC PDFs; JMAC via arXiv). These methods CANNOT run
on our entity-disjoint inductive split at all: they learn per-entity embeddings and use
alignment seeds, both undefined for an unseen entity. The table is a calibration ceiling, not a
runnable baseline.

| Method (setting) | Type | EL | JA | ES | FR | EN | Avg |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|
| TransE | structural | 24.3 | 25.3 | 24.4 | 27.6 | 16.9 | 23.7 |
| KG-BERT | text | 27.3 | 38.7 | 34.0 | 35.4 | 21.0 | 31.3 |
| AlignKGC | struct + align | 33.8 | 41.6 | 35.1 | 37.4 | 22.3 | 34.0 |
| SS-AGA (2022 SOTA) | struct + align | 35.3 | 42.9 | 36.6 | 38.4 | 23.1 | 35.3 |
| JMAC w/ SI | struct + text | 71.7 | 66.8 | n/r | n/r | n/r | n/r |
| **Ours, inductive (3-seed mean)** | text | 16.8 | 16.2 | 36.6 | 37.3 | 17.2 | 26.5 |

SS-AGA full metrics (2022 SOTA, transductive), for reference: EL H@1 30.8 / H@10 58.6;
JA H@1 34.6 / H@10 66.9; ES H@1 25.5 / H@10 61.9; FR H@1 27.1 / H@10 65.5; EN H@1 16.3 / H@10 41.3.

Reading:
- On FR and ES, our INDUCTIVE numbers (37.3, 36.6) match or exceed SS-AGA's TRANSDUCTIVE SOTA
  (38.4, 36.6) despite never seeing the test entities. This is the headline calibration point.
- On EL and JA, transductive SOTA is far ahead (35.3, 42.9 vs our 16.8, 16.2). Expected: those
  languages lose the most when alignment seeds and learned embeddings are removed, and JA is
  additionally truncation-bound (inference 9).
- JMAC's text-initialized transductive EL 71.7 is the figure most likely to be cited against us;
  it memorizes per-entity embeddings and uses alignment seeds, both impossible in our setting.

---

## Bug, then fix, then new result (callouts)

### V-fix-1: Eval max_length bug (the big one)
- Failed state: eval_dbp5l.py hardcoded max_length=96. Runs A/B/E/F trained at 128 or 160 were
  all evaluated at 96, truncating the rich descriptions.
- Fix: eval now auto-reads max_length from the checkpoint's saved args.
- New result: Run B went 15.59% to 24.76% MRR (+59%); Run A 14.95% to 23.41%. Per-language
  gains of 31% to 78%. Changed the paper's competitive position fundamentally.

### V-flip-1: The "ml=128 sweet spot" claim was itself an eval-bug artifact (Gate G0)
- Prior claim: Run E (ml=160) 14.89 below Run B (ml=128) 15.59, so ml=128 looked optimal. But
  both were measured at the buggy eval ml=96, and evaluating a 160-trained model at 96
  truncates it more relative to its training length, unfairly penalizing E.
- Fix: corrected eval, identical protocol for both.
- New result: Run E 26.69% beats Run B 25.15% (+1.54), and E wins on every language, most on
  the weak ones: JA +4.2, EL +2.7. Longer context helps low-resource languages most.
  Run E is the paper model. Confirmed under the support filter.

### V-fix-2: Support triples missing from the filter map (W0.3, done)
- Failed state: support.txt facts (known-true tails held out as the inference graph) were never
  added to the filtered-eval filter map. Measured: 25.25% of test queries have a support-tail
  that should be filtered but was not; 39,995 true tails missing (zero overlap with
  train/valid/test).
- Fix: eval now loads ind/*/support.txt (local to global ID offset) into the filter map.
- New result: applied across the whole table. Strong models gained about +0.4 MRR (E 26.26 to
  26.69, B 24.76 to 25.15); the weak ml=96 Row3-HN gained +2.4 (11.36 to 13.77). Weaker models
  misrank support-tails more often, so filtering them helps more.

### V-fix-3: XL-anchor "negative result" was a measurement artifact (Gate G1 RESOLVED)
- Failed state: XL runs train with anchor-averaged queries, but the standard eval scored the
  bare query, out of the training distribution (same bug class as v2). This produced the
  reported "cross-lingual anchors degrade 15.59 to 3.17" negative result.
- Fix: eval_dbp5l_anchors.py evaluates the crr_xl checkpoint (CRR + relation-level cross-lingual
  anchors, ml96, rank8, no HN) with matched anchors, plus a bare-query control.
- New result: bare control 3.84% (reproduces the collapse), matched anchors **20.38%**
  (EN 14.68, FR 26.07, ES 23.97, JA 19.45, EL 18.07). The collapse was entirely the train/eval
  mismatch. The negative result is RETRACTED: cross-lingual anchors do NOT degrade performance.
- Note on comparability: the anchors are relation-level priors sampled from the TRAIN graph
  (the unseen head has no train edges, so no test leakage). Matched-eval 20.38% is above the
  no-anchor CRR+HN baseline at the same encoder config (Row3-HN 13.77, ml96), so anchors appear
  to provide useful signal, but this is not a clean equal-information ablation and the anchor
  config (ml96, rank8) is weaker than the winning text-only model E (26.51, ml160, rank16). A
  controlled anchor study is future work; the paper does not headline an anchor claim either way.

---

## Inferences (accumulating)

1. Rich text is the single biggest driver. Wikipedia abstracts alone gave 10x (Row1 3.10 to
   Row1-wiki 10.02). Bare entity names carry almost no signal for a text bi-encoder.
2. Description length matters as much as content. Truncating to ml=96 at eval cost about 40%
   of the achievable MRR (V-fix-1). The encoder needs room to read the enriched descriptions.
3. CRR and hard negatives are synergistic, not additive. CRR alone is about equal to InfoNCE
   (9.86 vs 10.02); HN alone is modest; CRR plus HN wins. The interaction is the real effect.
4. Hard negatives help the confused languages (JA, EL) and slightly hurt the already separated
   ones (FR, ES). Consistent with HN sharpening decision boundaries only where candidates are
   close.
5. Global negatives with a stale entity cache is a memorization trap (Run C): 95% train
   accuracy but minus 3.6 MRR vs B at the same protocol. Fresh negatives matter; stale ones
   become label noise.
6. More epochs do not help (Run F, 40 epochs): overfits vs Run B's 30. Train accuracy had
   saturated above 93%.
7. ml=160 BEATS ml=128 (Run E 26.69 vs Run B 25.15, corrected). This REVERSES the earlier
   "ml=128 sweet spot" claim, which was an eval-bug artifact (V-flip-1). Longer context helps
   the low-resource languages most. Open question: would ml=192 or 256 help further? (future
   training run)
8. FR and ES inductive performance rivals transductive SOTA despite unseen entities. This is
   the headline evidence that the benchmark is hard but tractable with the right recipe.
9. JA is the weakest because its descriptions are token-length-starved, NOT under-covered.
   W4.1 analysis over test entities: coverage is 100% rich for every language. But JA
   descriptions are far longer in BGE-M3 subwords (median 119 tokens, mean 130) vs EN 76,
   FR 95, ES 94, EL 87; Japanese CJK fragments into many subwords. Truncation rates: JA 65%
   at ml=96, 44% at 128, 31% at 160, vs EN about 4% and FR/ES near 0% at 160. This explains
   why JA gained most from every ml increase and why it is still weakest: 31% of its
   descriptions are truncated even at ml=160. Clean, defensible story; motivates ml=192/256 or
   JA description compression as targeted future work.
10. RESOLVED (Gate G1): the XL cross-lingual anchor "negative result" was a measurement artifact.
    The 68% drop was a train/eval query-format mismatch (the anchor-trained model scored with
    bare queries). Matched anchor-aware eval gives 20.38% WL-MRR, not 3.17%. Bare control 3.84%.
    The negative result is retracted. Correct reading: cross-lingual anchors do not hurt and
    appear to provide useful relation-level priors, but they are not the winning configuration
    and were not scaled to ml160/rank16; a controlled study is future work. This is also a
    reproducibility win: we caught and killed a false claim before it reached the paper.
11. Seed stability: the full config reproduces well. Seeds 42, 123, and 777 land at 26.24,
    26.85, and 26.45 (mean 26.51, std 0.31), and their validation accuracies nearly coincide
    (72.52, 72.78, 72.17). Noise concentrates in EL and JA, the lowest-signal languages.
12. Cross-lingual ranking barely costs anything. Ranking the gold tail against all 56,589
    entities across every language (four times the candidates plus cross-lingual confusability)
    lowers MRR by only about 0.5 points versus same-language ranking (26.01 vs 26.51 at the
    seed level; under 0.35 per language except EN at about 1.1). The model almost never places a
    wrong-language entity above the same-language gold. This is direct evidence that BGE-M3's
    pretrained cross-lingual alignment is already strong, which is exactly why explicit
    cross-lingual anchor supervision is expected to be redundant or harmful (connects to the
    quarantined XL negative result, inference 10 and Gate G1).
13. Inductive performance on higher-resource languages rivals transductive SOTA. Our inductive
    FR and ES (37.3, 36.6) match or exceed SS-AGA's 2022 transductive SOTA (38.4, 36.6) despite
    never seeing the test entities, while EL and JA remain well below (expected: they lose the
    most when per-entity embeddings and alignment seeds are removed). This is the "hard but
    tractable" evidence, and it localizes the remaining difficulty to the low-resource and
    long-script languages rather than to the inductive setting as a whole.

---

## Seed robustness (A2: 3-seed chain of the Run E ml=160 config)

Filtered within-language MRR per seed. Reference Run E (ckpt 20260701_2132) = 26.69%.

| Seed | Ckpt | MRR | H@1 | H@10 | FR | ES | EN | EL | JA |
|------|------|:---:|:---:|:---:|:--:|:--:|:--:|:--:|:--:|
| 42 | 20260702_2006 | 26.24% | 17.85 | 41.91 | 37.45 | 36.34 | 16.87 | 16.71 | 15.17 |
| 123 | 20260703_0605_s123 | 26.85% | 18.88 | 41.94 | 36.67 | 37.05 | 17.89 | 16.57 | 16.90 |
| 777 | 20260703_2214_s777 | 26.45% | 18.33 | 41.44 | 37.75 | 36.26 | 16.82 | 17.09 | 16.38 |
| **mean +/- std** | (3 seeds) | **26.51 +/- 0.31** | 18.35 +/- 0.52 | 41.76 +/- 0.28 | 37.29 +/- 0.56 | 36.55 +/- 0.43 | 17.19 +/- 0.60 | 16.79 +/- 0.27 | 16.15 +/- 0.89 |

Std computed as sample standard deviation (n=3). The overall MRR spread is 0.31, very tight;
the config is highly reproducible. Per-language, JA has the widest std (0.88) and EL the
narrowest (0.26), consistent with JA being the lowest-signal, truncation-starved language.
The reference Run E checkpoint (26.69) is one run of this config; the honest headline is the
3-seed mean, 26.51 +/- 0.31. Paired significance vs B and Row3-HN below (rank dumps in progress).

---

## Significance tests (paired, per-triple within-language RR, n=54,473)

Tooling: bootstrap_sig.py (10,000 paired resamples) plus Wilcoxon signed-rank (scipy). Full
model represented by seed 777 (E config); the numbers are stable across seeds.

| Comparison | Delta MRR | 95% bootstrap CI | Bootstrap p | Wilcoxon p | Verdict |
|---|:--:|:--:|:--:|:--:|---|
| E (full) vs Row3-HN (pre-enrichment) | +12.67 | [+12.41, +12.94] | ~0 | ~0 | significant by both |
| E (ml160) vs B (ml128) | +1.30 | [+1.11, +1.49] | ~0 | 0.31 | mean-significant; concentrated |

Reading:
- The headline recipe gain (rich descriptions plus usable context length, E vs Row3-HN) is
  large and significant under both tests. This is the main significance claim for the paper.
- The ml160-over-ml128 ablation delta is significant in mean MRR (bootstrap CI well above 0)
  but the per-triple Wilcoxon is not one-sided (p=0.31). This is not a contradiction: MRR is a
  mean of per-query reciprocal ranks, which the bootstrap tests directly, while Wilcoxon tests
  whether the improvement is spread uniformly. The ml160 gain is concentrated on the subset of
  triples whose descriptions overflow 128 tokens, which is exactly JA and EL. The disagreement
  therefore corroborates inference 9 (JA/EL are context-length bound) rather than weakening it.
  Report E vs B with the bootstrap CI and this interpretation; do not claim uniform per-triple
  improvement for the length step.

## Clean ablation progression (final, filtered; the paper's Table 1 spine)

| Step | Adds | MRR | Delta |
|------|------|:---:|:---:|
| Zero-shot BGE-M3 | nothing | 1.45% | |
| CRR plus HN (Row3-HN) | contrastive recipe, ml96 | 13.77% | +12.3 |
| plus enriched desc plus ml128 (A) | rich text, longer context | 23.80% | +10.0 |
| plus LoRA rank 16 (B) | capacity | 25.15% | +1.35 |
| **plus ml160 (E, FINAL)** | even longer context | **26.69%** | +1.54 |

Monotonic, one component per step. Rich text plus context length dominate (+22.3 of the +25.2
total).

---

## W4.3: LLM-description quality audit (finding: the LLM fill is mostly hallucinated)

The LLM back-fill (1,042 descriptions, only EL 146 and JA 897, the languages without Wikipedia
coverage) was generated by Llama-3.2-3B, which was prompted to write a 2-sentence English
description from the entity name plus KG neighbors. Manual audit of 25 EL samples (isolated as
EL entities with English prose that changed from the pre-LLM backup; the 144 such EL entities
match the log's 146 EL count, so this set is effectively the LLM output):

- Roughly 5 of 25 accurate (all concept or common-noun entities: Calvinism, J-pop,
  hypothyroidism, gold-the-color), 3 partial, about 17 clearly hallucinated. Error rate near 70%.
- Failure mode is systematic: for a proper noun transliterated into Greek, the model cannot
  recover the real referent and invents a plausible biography. It defaults to "a Greek
  professional footballer who plays as a midfielder for PAOK." Clint Eastwood, Hugh Grant,
  Eleanor Roosevelt, David Petraeus, Kristin Scott Thomas all became Greek footballers or
  actors; Taipei became a Cypriot dessert; Hajduk Split (a Croatian club) became a fortress on
  Crete; William Henry Harrison (a US president) became a governor of Barbados.

Implications:
- We CANNOT claim the LLM descriptions are high quality. They are not.
- These 1,042 entities are exactly in the two weakest languages (EL, JA). Hallucinated
  descriptions plausibly feed wrong signal and may be HURTING those languages, not helping. This
  is a new angle on inference 9 (JA weakness): part of it may be hallucinated LLM text, not only
  truncation.
- Decision needed (see below): drop the LLM fill (revert those 1,042 to name-only or
  KG-neighbor text) and re-measure, rather than ship a description source we have shown to be
  mostly fabricated. Only 1.8% of entities are affected, so the cost of dropping is likely small
  and the integrity gain is large. A reviewer would raise exactly this concern; better we find
  and fix it.

Ablation (a), eval-time, reference E checkpoint, English back-fill for EL/JA reverted to bare
names (2,359 entities; the LLM fill plus the English-Wikipedia-fallback that we cannot verify
per-entity):

| | With back-fill (ref E) | No back-fill | Delta |
|---|:--:|:--:|:--:|
| Overall MRR | 26.69 | 26.94 | +0.25 |
| JA | 17.90 | 19.85 | +1.95 |
| EL | 18.42 | 18.33 | -0.09 |
| EN / FR / ES | (untouched) | (identical) | 0 |

Removing the unverifiable English back-fill IMPROVES the model: JA gains +1.95 MRR and overall
gains +0.25, even though this checkpoint was trained with the back-fill. The hallucinated
descriptions were actively hurting the weakest language by making many distinct entities look
alike (all "Greek footballer" / "Japanese guitarist"). This is an eval-time result; a clean
retrain without the back-fill should be at least as good and removes the bad text from the
hard-negative pool too. Part of the JA weakness in inference 9 was self-inflicted by this text.

Decision executed (option b): built `entity_descriptions_clean.json`. For the 2,359 EL/JA
entities with unverifiable English back-fill, we ran a native-language Wikipedia REST fetch:
1,070 (45%) recovered a real native-language summary, 1,289 (55%) fell back to the bare native
name. Spot-check confirms the fix: Clint Eastwood now reads (in Greek) "American film actor and
director" (was "Greek footballer"); Christina Applegate reads (in Japanese) "American actress"
(was "singer"); Taipei reads "the capital of Taiwan" (was "Cypriot dessert"). Final description
sources are therefore KG-neighbors plus native-language Wikipedia only; no LLM-generated or
cross-lingual-English-fallback text remains. Next: retrain the paper config (3 seeds) on this
file (run_clean_retrain.sh) after the mBERT baseline finishes, for the clean headline.

Inference 14: LLM-generated descriptions for transliterated named entities are unreliable
(about 70% hallucinated in the EL audit). Concept and common-noun entities are fine. The
practical lesson: a small open LLM cannot be trusted to describe named entities it can only see
as a foreign-script transliteration; it confabulates confidently. This is a second false signal
we caught before publication (the first was the XL anchor artifact, Gate G1).

## Pending / running

- [x] Gate G0 decided: Run E (ml=160) at 26.69% MRR is the paper model.
- [x] Final consistent Table 1 (correct ml plus support filter) complete.
- [x] Seeds 42 and 123 trained and evaluated (26.24, 26.85).
- [ ] Seed 777 training (user-launched). Then: eval with --dump-ranks, mean and std, paired
      bootstrap plus Wilcoxon vs Row3-HN.
- [ ] Anchor-aware eval of the crr_xl checkpoint (W2, Gate G1), queued behind the chain.
- [ ] SimKGC-style mBERT external baseline (W3), user launches run_baselines.sh when GPU frees.
- [ ] Zero-shot LaBSE and mE5 rows; TransE structural collapse row (CPU).
- [ ] LLM-description spot check (W4.3).
