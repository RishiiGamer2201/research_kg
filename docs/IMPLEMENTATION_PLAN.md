# Implementation Plan: AAAI 2027 Submission

**Created 2026-07-03, statuses live.** Check items off as they complete.
**Confirmed deadlines (official CFP, all 11:59 PM UTC-12):** Abstract **Jul 21** | Full paper **Jul 28** | Supplementary + code **Jul 31**.
Companion docs: [research_assessment_2026-07-03.md](design/research_assessment_2026-07-03.md) (direction analysis), [RESULTS_AND_INFERENCE.md](RESULTS_AND_INFERENCE.md) (all numbers), [paper_draft.md](paper/paper_draft.md) (draft).

---

## 0. State snapshot (updated 2026-07-03)

- Best model: **Run E (ml=160), final filtered MRR 26.69%** (H@1 18.80, H@10 41.62). Two eval bugs were fixed in W0: (1) eval max_length was hardcoded to 96 while models trained at 128 or 160; (2) support triples were missing from the filter map. Fixing both lifted the headline from a mismeasured 15.59% and flipped the winner from Run B (25.15%) to Run E. The earlier "ml=128 sweet spot" claim was an artifact of bug (1).
- Per-language (Run E, filtered): FR 35.93, ES 37.32, EN 16.98, EL 18.42, JA 17.90.
- Seed robustness DONE: seeds 42/123/777 = 26.24/26.85/26.45, mean 26.51 +/- 0.31 (tight). The honest headline is the 3-seed mean, not the single reference 26.69.
- Significance DONE: full model vs pre-enrichment baseline +12.67 MRR (bootstrap and Wilcoxon both p<0.001). The ml160 length step +1.30 is bootstrap-significant and concentrated on long-description languages.
- Cross-lingual eval added: ranking against all 56,589 entities costs only ~0.5 MRR vs same-language ranking (strong cross-lingual robustness; supports the redundant-XL-supervision hypothesis).
- Transductive SOTA comparison added: inductive FR/ES match or exceed 2022 transductive SOTA (SS-AGA) despite unseen entities.
- Gap claim verified open through EMNLP 2025. Framing locked: benchmark-first.
- GPU FREE. Next: W2 anchor eval (Gate G1), then user launches the mBERT baseline.

## 1. Locked decisions

- [x] Headline framing (A4): benchmark-first. "Multilingual KGC breaks when entities are unseen: a benchmark and first baselines." The model is the first strong baseline, not a SOTA claim.
- [x] Paper model: Run E config (ml=160, LoRA r16, CRR + HN K=7). Gate G0 decided.
- [x] External baseline: SimKGC-style mBERT through OUR pipeline (identical data, protocol, negatives; only the encoder changes). ALIGNKGC, SS-AGA, KEnS become "n/a, require seen entities" motivation rows plus cited transductive ceiling numbers.
- [x] Negative result (XL anchors): RESOLVED at Gate G1 as a measurement artifact and retracted. The paper now carries a short reproducibility caution instead of a negative-result claim. Do not reintroduce the "anchors degrade 68%" statement anywhere.
- [x] Eval protocol: tail-only ranking, within-language candidates, filtered (including support facts), disclosed explicitly in the paper.
- [x] Cut this cycle: IER, KL-GMoE adapters, CBLiP fusion, Wikidata5M-Ind.
- [x] Submission keywords (decided 2026-07-03): primary "DMKM: Knowledge Graphs, Linked Data & Semantic Web" (reviewer pool that can verify the gap claim); secondary "DMKM: Datasets & Benchmarks for Data Mining" and "NLP: Machine Translation & Multilinguality". Avoid "NLP: Datasets & Benchmarks" as primary (LLM-benchmark flooded, KGC at its scope edge) and KRR (expects symbolic machinery).

## 2. Workstreams

### W0. Correct the numbers (COMPLETE)
- [x] W0.1 Re-eval A/B/E/C/F at auto-detected max_length
- [x] W0.2 Gate G0: E (26.69) beats B (25.15) under identical protocol; E is the paper model
- [x] W0.3 Support-triple filter fix in eval; full consistent final table produced
- [x] Zero-shot row re-run under the final protocol (1.45)
- [x] Propagate corrected numbers to TASK.md, plan, results log

### W1. Seeds and significance (A2, A3) COMPLETE
- [x] Add --seed to trainer
- [x] Seed 42 trained and evaluated: 26.24
- [x] Seed 123 trained and evaluated: 26.85
- [x] Seed 777 trained and evaluated: 26.45
- [x] Full-model row: mean 26.51 +/- 0.31 (very tight); per-language means and stds in results log
- [x] Rank dumps produced (E_s777, B, Row3-HN) via eval --dump-ranks
- [x] Paired bootstrap + Wilcoxon: full model vs Row3-HN = +12.67, both p<0.001; full vs B (length step) = +1.30, bootstrap-significant, concentrated on long-description langs (JA/EL)
- [x] Cross-lingual evaluation tabulated: XL costs only ~0.5 MRR vs within-language (Table 2b in results); strong cross-lingual robustness finding
- [x] Transductive DBP-5L SOTA comparison tabulated (Table 2c in results): FR/ES inductive match/exceed transductive SOTA
- [x] Figure panel (e) updated with 3-seed mean and error bars

### W2. Resolve the XL-anchor negative result (Gate G1) COMPLETE
- [x] Anchor-aware eval script written and syntax-checked (eval_dbp5l_anchors.py); mirrors training anchor sourcing (n_anchors=4, XL EN-first, averaged query)
- [x] Ran matched eval + bare control on crr_xl checkpoint
- [x] Gate G1 DECIDED: the negative result was a MEASUREMENT ARTIFACT (train/eval mismatch). Bare control 3.84, matched anchors 20.38. Negative result RETRACTED. Reframed in the paper as a reproducibility caution (a silently anchor-less eval of an anchor-trained model fabricates a spurious collapse), not a claim that anchors hurt. A controlled anchor study is future work.

### W3. Baselines and encoder ablation (Table 1 baseline block + Table 4 encoder justification)
All optional items now COMMITTED. Owner tag: (U) = user runs the >1h training, (C) = Claude runs.
- [x] run_baselines.sh written: mbert-full, mbert-simkgc, xlmr-full variants
- [x] Eval tokenizer fix: eval now uses each checkpoint's own encoder tokenizer
- [x] Token-cache-per-encoder fix (mBERT was loading BGE-M3 token ids; CUDA assert). Re-launched.
- [~] (U) mbert-full training (RUNNING, ~2.8h, seed 42): the encoder-isolation baseline
- [ ] (C) eval mbert-full + rank dump; add to Table 1; bootstrap full-model vs mbert
- [ ] (U) mbert-simkgc: `bash run_baselines.sh mbert-simkgc` (InfoNCE only, SimKGC-faithful recipe, ~3h)
- [ ] (U) xlmr-full: `bash run_baselines.sh xlmr-full` (XLM-R base encoder point, ~5h)
- [ ] (C) zero-shot LaBSE and zero-shot mE5 rows (eval only, ~30 min GPU each)
- [ ] (C) TransE structural collapse row via PyKEEN on the split (CPU; unseen entities get no embedding, MRR near random). Motivation row.
- [ ] (C) Assemble Table 4 (encoder ablation): zero-shot vs LoRA-FT for mBERT / XLM-R / mE5 / LaBSE / BGE-M3; retro-justifies the BGE-M3 choice

### Infrastructure (2026-07-04)
- [x] Trainer saves a full-state `last_checkpoint.pt` every epoch (model, optimizer, scheduler, RNG, epoch). `--resume <path>` continues from the last completed epoch in the same run dir. Pass the same flags as the original run. (Old `best_model.pt` is weights-only and cannot resume.)
- [x] Token cache keyed by encoder AND descriptions file (prevents stale-cache crashes when swapping either).
- [x] `--desc-path` on both trainer and eval for description ablations.

### W4. Analysis and robustness (all COMMITTED)
- [x] W4.1 JA error analysis: JA is truncation-bound, not coverage-bound (median 119 subword tokens; 31% of descriptions exceed ml=160; coverage is 100% rich for every language)
- [ ] W4.2 Hard-negative true-tail masking fix, then (U) single retrain of paper config (~5h). CAVEAT: if it beats the 26.51 seed mean it becomes the new headline and needs a fresh 3-seed chain (another ~15h) for a defensible mean; if within noise, keep current headline and note the fix as a one-line robustness check. Decide after the single run.
- [ ] W4.3 (C) LLM-description spot check: sample 50 of the 1,042 Llama-generated descriptions, grade factuality, report percentage acceptable in the appendix and the datasheet
- [ ] W4.4 (C) Document known minor limitations: in-batch duplicate tails, optimistic tie-breaking, transductive valid set, tail-only ranking

### W5. Paper
- [x] Draft skeleton with verified content: paper_draft.md (Sections 2, 3, 4 substantially written; 1, 6, abstract as skeletons; PENDING markers for open numbers)
- [x] AAAI-27 CFP facts verified; AuthorKit27 downloaded; checklist answer map built (Section 6 below)
- [ ] USER: register/verify OpenReview profile (registration opened Jun 17; moderation can take days)
- [ ] Section 5 Experiments: write once seed stats + Gate G1 + mbert baseline land
- [ ] Section 1 Introduction and Section 6 Conclusion full prose
- [ ] Abstract (last)
- [ ] Figures: export architecture figure panels; per-language chart with error bars; ablation chart
- [ ] LaTeX port to aaai2027.sty (7 pages main content max; references only on pages 8-9; no CJK package, so JA/EL examples need romanization or figure-embedded text; no hyperref)
- [ ] Reproducibility checklist .tex filled from the Section 6 answer map
- [ ] Double-blind anonymization pass
- [ ] Abstract frozen Jul 19, submitted by Jul 20 (deadline Jul 21, keep one buffer day)
- [ ] Full paper submitted by Jul 27 (deadline Jul 28)
- [ ] Supplementary: code + DBP-5L-Ind release (license, datasheet, LLM-fill disclosure) by Jul 30 (deadline Jul 31)

## 3. Single-GPU schedule (revised 2026-07-04, with committed optionals)

| Order | Job | Owner | Hours |
|---|---|---|---|
| RUNNING | mbert-full training (encoder-isolation baseline) | U | ~2.8 |
| next | eval mbert-full + rank dump + bootstrap vs full model | C | ~0.3 |
| then | zero-shot LaBSE + mE5 rows (eval only) | C | ~1 |
| then | mbert-simkgc training (InfoNCE-faithful) | U | ~3 |
| then | xlmr-full training (encoder point) | U | ~5 |
| then | eval those two + assemble Table 4 | C | ~0.5 |
| then | W4.2 masking-fix single retrain (see caveat) | U | ~5 |
| CPU anytime | TransE collapse row (PyKEEN, CPU) | C | ~2 |
| CPU now | W4.3 LLM spot-check, W4.4 limitations (no GPU) | C | ~1 |
| buffer | Gate G1 surprises, mbert-simkgc variant | open |

## 4. Decision gates

- [x] G0 (decided): E vs B at identical protocol. E wins on every language. E is the paper model.
- [x] G1 DECIDED: matched anchor eval recovered the model (3.84 bare to 20.38 matched). The negative result was a train/eval artifact, retracted. Reframed as a reproducibility caution.
- [ ] G2: mbert baseline lands. Table 1 baseline block frozen.
- [ ] G3: seed std known. If std > 1 MRR point, soften delta claims and lean harder on the benchmark contribution (current spread suggests ~0.3, likely fine).

## 5. Risks

| Risk | Mitigation |
|---|---|
| mbert LoRA target names mismatch (injection finds 0 layers) | Check "Injected LoRA into N layers" in the first log lines; adjust target_modules if N=0 |
| Gate G1 kills the negative result | Benchmark framing unaffected; Section 5 loses one finding |
| Seed 777 diverges from 42/123 | Report honestly; variance reporting is itself a checklist item |
| 7-page limit too tight | Benchmark-first framing has one headline table; push ablation detail to appendix/supplementary |
| OpenReview profile moderation delay | Register now (user action, flagged above) |

## 6. AAAI-27 submission facts (verified from official CFP and AuthorKit27, 2026-07-03)

**Deadlines (11:59 PM UTC-12):** abstract Jul 21; paper Jul 28; supplementary/code Jul 31; Phase-1 rejections Sep 24; author feedback Oct 19-25; decisions Nov 30; camera-ready Dec 14; conference Feb 16-23 2027, Montreal.

**Format (AuthorKit27, template 2027.1):** aaai2027.sty; 7 pages main content, max 9 total, pages 8-9 references only. Fonts come from the style file. Forbidden packages include hyperref, CJK (JA/EL example strings need romanization, translation, or figure-embedded text), geometry, setspace, wrapfig.

**Process:** OpenReview. Author registration opened Jun 17: register and verify the profile now. Two-phase review; Phase 1 is 2 human reviews plus 1 AI-generated non-decisional review, so abstract and intro clarity get machine-read too. Max 10 simultaneous submissions per author. Generative-AI use permitted "judiciously"; authors responsible; no fabricated references.

**Reproducibility checklist answer map:**

| Item | Our answer / evidence |
|---|---|
| 1.1-1.3 structure, opinions vs facts, pedagogy | yes; write with this in mind |
| 2 theoretical contributions | no (skips that whole section) |
| 3 datasets: motivation, novel data appendix, public release with research license, citations | yes; DBP-5L-Ind released with license and datasheet (supplementary, due Jul 31); DBP-5L cited; LLM-generated fills disclosed |
| 4.1 hyperparameter ranges tried plus selection criterion | yes; full run history is in RESULTS_AND_INFERENCE.md (ml 96/128/160, rank 8/16, K 7/15, lr, epochs) |
| 4.2-4.5 code including preprocessing, comments, release | yes; build/preprocess/train/eval scripts go to supplementary |
| 4.6 seed method described | yes; --seed flag, seeds 42/123/777 |
| 4.7 computing infrastructure | yes; RTX 5070 Ti 16 GB, WSL2 Ubuntu, Python 3.10, PyTorch 2.11 cu128 |
| 4.8 metrics formally described and motivated | yes; filtered MRR and Hits@k, defined in Section 3.4 |
| 4.9 number of runs per result | yes; 3 seeds for the full model, 1 for ablation rows (state explicitly) |
| 4.10 variation beyond averages | yes; mean and std |
| 4.11 statistical tests | yes; paired bootstrap plus Wilcoxon signed-rank (bootstrap_sig.py, scipy verified present) |
| 4.12 final hyperparameters listed | yes; Section 4 plus appendix table |

## 7. Explicitly out of scope this cycle

IER reranking, KL-GMoE adapters, CBLiP fusion, Wikidata5M-Ind, head-prediction retraining, unshared towers. All are future-work material; several form the follow-up paper's core.
