# Unified Pathway: Mentor S2DN Ladder plus External Gap Plan

Written 2026-07-14. Updated 2026-07-17 with the new findings block (Section 0a), the benchmark
comparison (Section 0b), and the 96 GB lab GPU. No steps were removed; new material sits on top of
the original plan.

This is the single common pathway that merges two inputs into one plan of record:

- The mentor's bottom-up ladder in
  [IMPLEMENTATION_PLAN_S2DN_LADDER.md](IMPLEMENTATION_PLAN_S2DN_LADDER.md) (reproduce S2DN, beat it on
  English inductive KGC with a neuro-symbolic method, extend to multilingual, add self-healing).
- The external gap assessment `Claude KG.pdf`, captured and critiqued in
  [external_gap_assessment_review.md](external_gap_assessment_review.md) (self-healing as the novel
  headline, a two-paper split, a promoted structure-poor-auditing gap, and a verified competitor map).

Decision (2026-07-14): the mentor ladder is the backbone, the PDF plan is layered on top, one common
pathway. This document is a superset. Nothing load-bearing from either source is dropped; where the two
disagree the reasoning is stated here. The ladder file remains the detailed running ledger for
reproduction runs; this file is the merged strategy and the phase gates.

Style note: no emojis, no shorthand dashes.

---

## 0a. New findings since 2026-07-14 (all CPU or literature work; GPU untouched)

Each finding links to its full document. These modify emphasis, not structure; every original phase
below stands.

1. **D2 rule-to-text bridge designed with real data**
   ([D2_rule_text_bridge_design.md](D2_rule_text_bridge_design.md)). Contamination census: 2,359
   contaminated descriptions (ja 2,215, el 144); 30.4 percent sit on entities with at least one edge
   and are structurally auditable; 69.6 percent have zero edges. Mechanism specified: claim
   extraction against the KG relation vocabulary, direct edge contradiction where edges exist,
   RuleTrust rule plausibility otherwise, aggregation where one hard contradiction dominates. Worked
   example: the ja "50/50" film, fabricated Miike/Suzuki biography contradicted by starring and
   language edges.

2. **Cross-lingual structural transfer measured dead on DBP-5L.** The 1,641 zero-edge contaminated
   entities have zero alignment links, while the alignment table itself is healthy (37,723 pairs,
   all ten language pairs populated). No wiki coverage, no edges, no alignments are one and the same
   obscurity. The PDF's Gap 3 "borrow aligned neighbourhoods" mechanism cannot rescue the population
   it was meant for. Reported as a finding, and it reroutes zero-edge entities to external-evidence
   lookup (which doubles as repair).

3. **DBP-5L to GraIL converter written, run, verified** (`scripts/data_prep/convert_dbp5l_to_grail.py`).
   All five languages emitted; entity-disjoint split asserted clean (0 overlap, 0 leakage, 0 test
   triples without an unseen entity). Known quirk: about 2 percent of test triples per language
   reference out-of-vocabulary entities; decide drop-versus-extend before the first multilingual run.

4. **S2DN is not the inductive SOTA**
   ([sota_benchmark_survey_2026-07-17.md](sota_benchmark_survey_2026-07-17.md)). MorsE (2022), CATS
   (2024), MGIL (June 2026), and the foundation-model line ULTRA (ICLR 2024) postdate or outrank it.
   SS-AGA (2022) is superseded by SimRMKGC (2025) as the transductive DBP-5L anchor. The
   inductive-plus-multilingual cell remains empty, which is P1's core justification.

5. **S2DN paper contains no RuleN ensembling** (full-text verified). The RuleTrust novelty space at
   the S2DN level is open; nearest prior is GraIL's post-hoc RuleN blend, differentiated by our
   learnable in-training fusion and the inductive transfer analysis.

6. **S2DN architecture weaknesses mapped, W1 to W12**
   ([s2dn_architecture_weaknesses.md](s2dn_architecture_weaknesses.md)), per the mentor's direct
   task. Core thesis: every weakness traces to the endpoint enclosing subgraph. The paper-worthy
   synthesis: W1 (empty subgraph on isolated entities) plus W2 (text-blind) plus W9 (noise-robustness
   proven only on synthetic noise) are the same gap seen three ways, and it is exactly where this
   project lives.

7. **Lab GPU incoming: 96 GB VRAM, remote SSH** (mentor message, 2026-07-17). Removes the 16 GB
   memory wall behind the FB15k-237 v2 OOM and the batch-16 fallback. Mentor's standing instruction
   until access lands: study architecture limitations and weaknesses (finding 6 is that
   deliverable); mentor provides GPU for testing.

## 0b. New benchmark papers: their scores versus ours

Protocol warning applies throughout: S2DN and our reproductions use GraIL's 50-negative ranking on
the v1 to v4 inductive splits. MGIL/MorsE numbers may use a different candidate protocol; do not
treat cross-paper deltas as like-for-like until verified (survey Section 1).

Inductive English (GraIL splits), Hits@10 unless stated:

| Split | S2DN paper | Ours (S2DN reproduced) | Ours (RuleTrust, 1 seed) | MGIL (Jun 2026) | Strongest pre-MGIL baseline |
|---|---:|---:|---:|---:|---|
| WN18RR v1 | 87.64 | 87.23 | not run | 84.86 | MorsE 83.21 |
| WN18RR v1-v4 avg | 81.23 | 80.57 | not run | 80.90 | MorsE about 78.5 |
| FB15k-237 v1 | 67.34 | 67.80 | 71.22 | 87.17 | MorsE 82.59 |
| FB15k-237 v1 MRR | 52.10 | 53.13 | 53.19 | not reported comparably | - |
| FB15k-237 v2-v4 | 82.38 / 83.97 / 91.31 | pending (OOM wall, now lifted by 96 GB GPU) | pending | 94.98 / 94.62 / 96.01 | MorsE 94.92 / 95.00 / 95.78 |

Readings: our reproduction is faithful (v1 within noise of paper on both datasets, slightly above on
FB15k-237). On WN18RR, S2DN and our reproduction still lead MGIL, so S2DN remains a defensible
baseline there. On FB15k-237 the MGIL/MorsE numbers are far above the S2DN line; whether that is
method or protocol must be settled before any claim. RuleTrust's +3.42 Hits@10 over our baseline is
inside single-seed noise (shuffle control moved more); seeds remain the gate.

Multilingual DBP-5L (ours is the inductive setting; all listed baselines are transductive and see
every entity in training, so they are a ceiling reference, not head-to-head):

| Method | Setting | DBP-5L result | Vs ours |
|---|---|---|---|
| Ours, BGE-M3 substrate | Inductive, unseen entities | 26.51 +/- 0.31 MRR (3 seeds); FR 37.3, ES 36.6, EN 17.2, EL 16.8, JA 16.2 | the only number in this cell |
| SS-AGA (ACL 2022) | Transductive | EL 35.3, JA 42.9 MRR (old anchor) | our FR/ES exceed its FR/ES; EL/JA gap expected, unseen vs seen |
| SimRMKGC (2025, Applied Intelligence) | Transductive | +4.0 to 7.1 percent MRR over prior methods; per-language table paywalled, PDF fetch pending | NEW ceiling anchor, replaces SS-AGA |
| KL-GMoE (EMNLP 2025 Findings) | Transductive | avg MRR 47.86 on its own EN/FR/IT/JA/ZH dataset, not DBP-5L | cite, do not calibrate |
| KG-TRICK (COLING 2025) | Transductive text+relation | evaluated mainly on WikiKGE10++, not DBP-5L | cite, do not calibrate |
| ULTRA (ICLR 2024) | Inductive cross-graph foundation model | about +15 percent relative MRR over supervised SOTA zero-shot across 57 KGs; not multilingual in the alignment sense | must be positioned against explicitly in P1/P2 related work |

## 0. The core insight that makes this one pathway, not two

The mentor ladder and the PDF share the same endgame: self-healing multilingual knowledge bases. They
only disagreed on the path. The connective tissue that fuses them is a measured property of the
mentor's own RuleTrust work:

> RuleTrust's rule evidence is entity-independent and relation-level, so it transfers to unseen
> entities almost undiminished (rule-only AUC 0.690 on train subgraphs, 0.680 on inductive test with
> unseen entities; see RULETRUST_EXPERIMENT_LEDGER.md).

That same property is exactly what the self-healing detector lacks. The detector's honest soft spot is
that it flags only about 57 percent of real fabrications, because the most-contaminated low-resource
entities have almost no neighbourhood structure to check against. A signal that survives on
structure-poor, unseen entities is precisely the tool needed there.

So the neuro-symbolic RuleTrust thread is not a separate detour. It is the mechanism that attacks the
self-healing story's weakest number. This is why the PDF's Gap 3 (auditing structure-poor entities) is
promoted from a "follow-up" to a first-class phase in this pathway: it is where the mentor's method and
the PDF's headline meet.

---

## 1. Products (what actually gets submitted)

Three coherent products come out of one line of work. Each reuses the assets before it.

| Product | What it is | Maps to | Venue target | Risk |
|---|---|---|---|---|
| P1: DBP-5L-Ind benchmark paper | First entity-disjoint inductive split of a multilingual KG, with the first strong inductive baselines and the transductive-cannot-run finding | PDF Gap 2; mentor Phase 3 substrate | SIGIR 2027 (resource track) or KDD 2027 D&B; AAAI-27 dropped (2026-07-17: A-star-only decision, SIGIR primary) | Low, essentially done |
| P2: Self-healing multilingual KBs | Named phenomenon, training-free structural detector, structure-poor auditing via transfer, GOLD-style bad-triple detection, repair loop, measured downstream grounding | PDF Gap 1 plus Gap 3; mentor Phase 4 | SIGIR 2027 PRIMARY (late-January-style deadline, CFP pending); WSDM 2027 and KDD 2027 Cycle 2 fallbacks | Medium, the novel headline |
| P3 (contingent): RuleTrust-S2DN methods note | Neuro-symbolic rule evidence for inductive link prediction, if it beats reproduced S2DN beyond noise | mentor Phase 2 and 2b | Folded into P2 as the method, or a short standalone | Contingent on the seed result |

P3 is contingent. If RuleTrust beats reproduced S2DN beyond seed noise, it is a methods contribution in
its own right and strengthens P2. If it converges to "rules transfer to unseen entities but do not beat
the GNN on this split," that is still a finding, and it redirects the rule signal into P2's
structure-poor detector (Phase D2). Either outcome feeds the pathway; neither is a dead end.

---

## 2. Phase map (merged ladder plus gaps)

Each phase lists the mentor-ladder origin, the PDF-gap origin, and the gate that must pass before the
next phase earns GPU time. Gates are the project's hard-won discipline (Section 6).

### Phase A. Finish S2DN reproduction (credibility floor)

Origin: mentor Phase 1. Not in the PDF (it did not know about it).

Verified S2DN paper targets to reproduce against (filtered):

| Dataset | Split | MRR | Hits@1 | Hits@10 |
|---|---|---:|---:|---:|
| WN18RR | V1-V4 avg | - | - | 81.23 |
| FB15k-237 | V1 | 52.10 | 43.68 | 67.34 |
| FB15k-237 | V2 | 64.80 | 55.45 | 82.38 |
| FB15k-237 | V3 | 65.07 | 56.31 | 83.97 |
| FB15k-237 | V4 | 68.44 | 60.96 | 91.31 |
| FB15k-237 | V1-V4 avg | - | - | 81.25 |

Status:
- [x] WN18RR v1-v4 reproduced (avg Hits@10 80.57 vs paper 81.23, 0.66 below).
- [x] FB15k-237 v1 paper-param reproduced and beats paper (MRR 53.13 vs 52.10, Hits@1 44.63 vs 43.68,
      Hits@10 67.80 vs 67.34).
- [ ] FB15k-237 v2 at batch 16 (`sdn_fb_v2_paper_bs16_gpu`), documented as paper params except reduced
      batch for 16 GB memory. Batch 32 OOMs on the RTX 5070 Ti; the paper used RTX 2080 Ti / 3090.
      If batch 16 still OOMs, use batch 8.
      2026-07-17 update: the lab's 96 GB GPU (remote SSH incoming) removes this wall. Once access
      lands, prefer running v2 to v4 at TRUE paper settings (batch 32) there; the batch-16 fallback
      stays as the local-GPU contingency only.
- [ ] FB15k-237 v3, v4.
- [ ] Batch-size consistency decision: if v2-v4 need batch 16, rerun v1 at batch 16 too, or report v1
      at both batch sizes and state the deviation, so the FB15k-237 average is over one batch size.
      With the 96 GB GPU this decision likely dissolves: everything at batch 32, single protocol.
- [ ] NELL v1-v4, last, only after WN18RR and FB15k-237 are stable.

Cross-check assets already on disk (independent second data path if the S2DN loader misbehaves):
CBLiP and a Phase-0 WN18RR setup exist at `~/research_kg/CBLiP/` and `~/research_kg/WN18RR/`.

Gate A: do not make any "beat S2DN" claim until at least FB15k-237 is reproduced across versions. This
is the mentor's explicit rule and it protects P3 and P2's method section.

SOTA reality check (2026-07-17, see [sota_benchmark_survey_2026-07-17.md](sota_benchmark_survey_2026-07-17.md)):
S2DN is NOT the inductive SOTA. MorsE (2022), CATS (2024), MGIL (June 2026) and the foundation-model
line ULTRA (ICLR 2024) postdate or outrank it on parts of the same benchmark. Beating S2DN is a valid
milestone but is not beating SOTA; the paper's baseline table must include MorsE and a foundation-model
point (ULTRA fine-tuned). Before any cross-paper number, confirm the FB15k-237 evaluation protocol
matches (S2DN uses GraIL 50-negative ranking; MGIL/MorsE numbers may not be directly comparable).

### Phase B. RuleTrust-S2DN, Structure Refining branch (the current blocker)

Origin: mentor Phase 2 and 2c. This is where work is actually stuck today.

Scoping check (for defensible novelty):
- [x] Written 2026-07-14, the paragraph to defend: RuleTrust-S2DN injects mined rule confidence as a
      learnable, in-training evidence term at the link-prediction score of a subgraph GNN, and its
      claim rests on a measured property: the rule signal is entity-independent and survives the
      inductive shift (AUC 0.690 train, 0.680 unseen) exactly where GNN evidence degrades. It is not
      GOLD (standalone noise scoring with rules plus structure, not link prediction), not NeuralLP or
      DRUM (end-to-end differentiable rule learners, already S2DN baselines, replacing the GNN rather
      than feeding it), not GraIL+RuleN (post-hoc blend of two separately trained scorers with a
      hand-tuned mixing weight, no transfer analysis), and not UniKER or RulE (transductive
      embedding-space fusion, no subgraph GNN, no unseen entities). The finding is the contribution;
      the fusion is the instrument.
- [ ] CRITICAL prior-art check: score-level fusion of rule scores with neural scores is a known
      family. GraIL itself post-hoc ensembles with RuleN (the scripts sit in our own repo,
      `external/grail/ruleN/` and `external/grail/ensembling/blend.py`), and UniKER (EMNLP 2021) and
      RulE (2024) fuse rule confidence with embedding scores. "Rule score plus GNN score" is NOT the
      contribution. The defensible novelty is narrower and must be stated as such: (a) a learnable
      in-training fusion weight (`rule_scale`) rather than a post-hoc blend, so the model itself
      reports the marginal value of symbolic evidence; and (b) the measured finding that the rule
      signal is entity-independent and survives the inductive shift (AUC 0.690 train vs 0.680 unseen)
      exactly where the GNN degrades. The finding is the contribution; the fusion is the instrument.
- [x] Checked 2026-07-14: the S2DN paper (03121-MaT, 9 pages, full-text search) contains zero
      mentions of RuleN, ensembling, or blending. Its baselines are standalone only (NeuralLP, DRUM,
      A*Net, CoMPILE, TAGT, SNRI, RMPI); GraIL appears only as motivation and in the Figure 1 noise
      comparison, not in the main tables. So S2DN itself does no symbolic-neural fusion, and the
      RuleTrust addition is not already occupied at the S2DN level. The GraIL original paper does
      report a post-hoc GraIL+RuleN ensemble (hence the blend scripts in `external/grail/`), so cite
      it and differentiate: post-hoc blend of two separately trained scorers versus a learnable
      in-training fusion weight, plus the inductive transfer analysis neither reports.

Components (built):
- [x] `rule_miner.py` (v2): length-1 and length-2 Horn rules with inverse literals, mines
      `(x, r1, z) + (z, r2, y) -> (x, r, y)`; cache `ruletrust_rules_v2.json`.
- [x] `rule_features.py` / `build_rule_target_score`: max rule confidence supporting the target pair,
      edge-list based (not dense) to avoid hundreds of MB per FB15k-237 subgraph.
- [x] CLI flags: `--use-rule-trust`, `--rule-weight`, `--rule-conf-threshold`, `--rule-min-support`,
      `--rule-cache`, `--rule-trust-mode {score,adjacency,both}`, `--rule-shuffle`, `--rule-no-inverse`,
      `--rule-max-len`. Liveness instrumentation via `RULETRUST_DEBUG`.
- [x] Score fusion (the design that works): `output = fc(g_rep) + rule_scale * rule_target_score`, with
      `rule_scale` a learnable scalar initialised to 0, so training starts bit-identical to baseline.
      The measured-inert adjacency variant is retained only as an ablation control.

Runs so far:
- [x] Main run mode=score: `rule_scale` learned 3.90, Hits@10 +3.42, MRR flat, but inside single-seed
      noise.
- [x] Shuffle control: mechanism passes (`rule_scale` collapses 3.90 to 0.12; val AUC orders real >
      baseline > shuffle), but metric claim not supported (a should-be-baseline run swung 2+ points).

Required next and ablations:
- [ ] REQUIRED NEXT: 3 to 5 seeds each of baseline and RuleTrust mode=score on fb237_v1, for an error
      bar. This is the single gating experiment for the whole neuro-symbolic thread.
- [ ] Negative control mode=adjacency (must equal baseline; if it improves, our inertness measurement
      is wrong).
- [ ] Weaker miner `--rule-no-inverse` (forward-only length-2), confidence threshold sweep {0.01, 0.1,
      0.3, 0.5}, support threshold sweep {1, 2}, rule body length 1 vs 2.
- [ ] Generalisation across splits fb237_v2-v4 at fixed batch size.
- [ ] WN18RR excluded as a testbed (only 5 rules, none above 0.5 confidence): report as a finding, not
      a gap.

Gate B (branch point):
- If RuleTrust beats reproduced S2DN beyond seed noise on MRR or Hits@10: P3 is real; carry the method
  into P2 and consider a short methods note.
- If `rule_scale` stays clearly positive but metrics are flat: record "entity-independent rule signal
  is real but redundant with the GNN on rule-rich splits"; carry the transfer property into Phase D2
  where structure is scarce and the redundancy disappears.
- Either way, do not multilingualize (Phase C) until Gate B resolves.

### Phase B2. RuleTrust-S2DN, Semantic Smoothing branch (deferred second branch)

Origin: mentor Phase 2b. The mentor research note recommends a two-branch modification; Phase B keeps
Semantic Smoothing intact to isolate the Structure Refining effect first. This branch is deferred, not
dropped.

- [ ] Decision needed with the mentor: are both branches expected, or is beating S2DN with the
      Structure Refining branch alone sufficient for milestone 2?
- [ ] If pursued: initialize or regularize the Gumbel-Softmax relation-smoothing weights using a
      relation similarity matrix instead of learning all blur weights from scratch, so semantically or
      ontologically similar relations are easier to smooth together while unrelated relations stay
      apart.
- [ ] Relation similarity sources to try: relation-name text embeddings (BGE-M3), co-occurrence
      statistics, and heuristic ontology or schema alignment across relations.
- [ ] Ablation: Structure Refining branch only, Semantic Smoothing branch only, both branches.
- [ ] Trigger: try this branch if Phase B alone does not beat S2DN, or stack it for additional gain.

### Phase C. Multilingual bridge and the benchmark product (P1)

Origin: mentor Phase 3; crystallizes PDF Gap 2. Do this only after English RuleTrust-S2DN beats or
meaningfully matches S2DN.

- [x] Converter from DBP-5L-Ind to S2DN/GraIL folder format: written and run 2026-07-14 (CPU only).
      Script: `scripts/data_prep/convert_dbp5l_to_grail.py` (in WSL home and the repo mirror).
      Output: `~/research_kg/DBP5L/grail_format/dbp5l_{lang}_v1` and `..._v1_ind` for all five
      languages. Mapping: base train graph from `train.txt`; validation from `valid.txt`; inductive
      support graph from `support.txt`; inductive evaluation triples from `test.txt`; transductive
      test and `_ind` valid are placeholders (unused by S2DN's inductive eval).
- [x] Entity-disjoint split asserted, all five languages, 2026-07-14: declared train/test entity
      overlap 0; unseen entities leaking into the train graph 0; test triples with no unseen entity
      0. The split is clean.
- [ ] Known data quirk to resolve before the first multilingual run: 123 to 329 test triples per
      language (about 2 percent) reference entities outside train, support, and declared-test
      vocabulary. Decide: drop them (document the count) or extend the support graph. Do not let the
      S2DN loader crash on them silently.
- [ ] Run graph-only RuleTrust-S2DN per language, English first, then all five.
- [ ] Compare against the existing BGE-M3 substrate (3-seed mean 26.51 MRR, best single 26.69) as the
      text-based reference point. Add text or BGE-M3 features only after graph-only multilingual runs
      work.
- [ ] Update the transductive multilingual ceiling: SS-AGA (2022) is superseded by SimRMKGC (2025,
      Applied Intelligence), the current DBP-5L SOTA (+4.0 to 7.1 percent MRR over prior). Fetch its
      PDF for exact per-language numbers. Keep the honest framing: transductive methods see all
      entities and cannot run in the inductive setting, so they are a ceiling reference, not a
      head-to-head competitor.
- [ ] Assemble P1: the benchmark, the inductive baselines, the transductive-cannot-run finding (KEnS,
      AlignKGC, SS-AGA structurally cannot run on unseen entities), significance (+12.67 MRR vs
      pre-enrichment, p<0.001), cross-lingual robustness, transductive-ceiling calibration.

Gate C: frame P1 benchmark-first, not SOTA-first (the senior's critique applies here directly). P1 can
be written and submitted in parallel with Phase D once the multilingual graph runs exist.

### Phase D. Self-healing headline (P2)

Origin: mentor Phase 4; PDF Gap 1 plus the promoted Gap 3. The novel headline. Reuse existing WSL
assets rather than rebuilding.

Assets already present:
- Contaminated descriptions: `DBP5L/processed/entity_descriptions.json`.
- Clean descriptions: `entity_descriptions_clean.json`.
- Backup and no-LLM: `entity_descriptions_backup.json`, `entity_descriptions_nollm.json`.
- Detector: `detector_experiment.py`; result `logs/detector_result.json` (ROC-AUC 0.995).

D1. Detector hardening (PDF recommendation 3):
- [ ] Realistic-fabrication injection set: generate believable wrong biographies, not wrong-entity
      swaps, so the positive class matches the real failure mode. This also closes the "synthetic
      noise" gap we criticize CCA for.
- [ ] Add an LLM-judge detector variant beside the embedding/NLI one.
- [ ] Report precision, recall, F1 by language and by script, not just aggregate ROC-AUC.

D2. Structure-poor auditing (the synthesis, promoted Gap 3):
- [x] Rule-to-text bridge designed with real data, 2026-07-14: see
      [D2_rule_text_bridge_design.md](D2_rule_text_bridge_design.md). Mechanism: claim extraction
      against the KG relation vocabulary, per-claim scoring (direct edge contradiction where edges of
      the claimed relation exist; RuleTrust rule plausibility otherwise, reusing
      `build_rule_target_score`), aggregation where one hard contradiction can dominate. Worked
      example: ja "50/50" film, fabricated Miike/Suzuki biography contradicted by starring and
      language edges.
- [x] Contamination census measured, 2026-07-14 (CPU): 2,359 contaminated descriptions (ja 2,215,
      el 144); 30.4 percent sit on entities with at least one edge and are structurally auditable;
      69.6 percent have zero edges. This quantifies the 57 percent recall soft spot.
- [x] Cross-lingual structural transfer: MEASURED DEAD on DBP-5L. The 1,641 zero-edge contaminated
      entities have zero alignment links (the alignment table itself is healthy: 37,723 pairs, all
      ten language pairs populated). No wiki coverage, no edges, and no alignments are symptoms of
      the same obscurity. Report as a finding; the borrow-aligned-neighbourhood mechanism cannot
      rescue the population it was meant for. Zero-edge entities route to external-evidence lookup
      (which doubles as repair) or are declared unauditable, split reported per language.
- [ ] Use RuleTrust's entity-independent relation-level rule evidence to score contamination for
      entities with few edges, where the neighbourhood detector fails (the 30.4 percent, and the
      claim-level mechanism above).
- [ ] Decisive cheap test (mostly CPU): 718 auditable contaminated vs 718 degree-matched clean
      descriptions; does the claim-level score beat the neighbourhood detector alone?
- [ ] GOLD-style bad-triple detection: flag contradictions and low-rule-support edges as removal or
      quarantine candidates, reusing the Phase B rule miner. This covers structural noise and
      complements the text detector.
- [ ] Target metric: lift real-fabrication recall above the current 57 percent, reported specifically
      on ja and el.

Standing reviewer threat to name in the paper, not hide: the contamination is self-inflicted (our own
Llama 3.2 backfill). "You polluted your own KB then cleaned it" is the obvious attack. The answer is
designed in, not argued: the realistic-fabrication injection set (D1) shows the detector works beyond
our specific accident, the Wikidata slice (D3) shows the phenomenon is not DBP-5L-specific, and the WWW
2026 pollution paper shows the ecosystem-level version of the same failure is already measured in the
wild. State all three explicitly in the limitations section.

D3. Repair loop and downstream grounding (connects detection to impact):
- [ ] Quarantine flagged text.
- [ ] Repair with native-language Wikipedia when available (recovered 45 percent for us). Use fuzzy
      search (n-gram index, BK-tree, or vector index) to match noisy entity names and aliases to
      canonical entity IDs and to locate candidate Wikipedia or Wikidata pages.
- [ ] Otherwise use an aligned high-resource description via ontology or entity alignment plus fuzzy
      search when spelling or script differs. Final fallback: entity name only, never hallucinated
      text.
- [ ] Optional later: constrained LLM repair (LLM_sim style), accepted only if graph-text consistency
      improves.
- [ ] Downstream LLM factual-QA with versus without the cleaned KB. This is the result to lead with if
      D1/D2 recall stays soft.
- [ ] Generality: a second KB (a Wikidata slice) so the phenomenon is not DBP-5L-specific.

Evaluation for P2:
- [ ] Detector ROC-AUC, precision, recall, F1 (controlled injection set and real subset).
- [ ] Before and after DBP-5L-Ind MRR.
- [ ] Per-language repair impact, focus on ja and el.

Gate D: the self-healing section must be solid across languages, not a single ROC-AUC number. If recall
on structure-poor entities stays near 57 percent even after D2, foreground the honest coverage limit
and make D3 downstream grounding the headline.

### Phase E. Packaging and submission

Origin: PDF venue analysis plus the two-paper split.

- [ ] Related work built on the captured competitor map (Section 4): differentiate explicitly from CCA
      (AAAI 2024) and the AISTATS 2025 denoiser; reviewers will anchor there.
- [ ] Fresh literature sweep immediately before submission (mid-2026 search-surfaced arXiv IDs may be
      imprecise; verify every ID, author list, and venue).
- [ ] Romanize Greek and Japanese examples or embed them in figures (AAAI has no CJK package; check the
      final venue's template).
- [ ] Freeze P2 abstract before the WSDM date; keep the Findings track and KDD Cycle 2 as safety nets.
- [ ] Optional analysis figures: Gephi visualizations of original GraIL subgraphs versus S2DN refined
      subgraphs, and contamination clusters, for the paper and for understanding model decisions.

---

## 3. Reproduction infrastructure (environment, blockers, patches)

Origin: mentor ladder Section 0 and the compatibility notes. Kept here so a fresh session does not
rediscover these the hard way.

Environments (isolated so the DBP-5L pipeline is never at risk):
- `venv_s2dn_gpu_latest`: active GPU path. Python 3.10, PyTorch 2.11.0+cu128, DGL 2.4.0+cu121 (installed
  with dependency override), LMDB 2.2.1, NetworkX 3.4.2. Verified: CUDA tensors and DGL graphs run on
  the RTX 5070 Ti.
- `venv_s2dn`: CPU fallback. PyTorch 2.1.0+cu121, DGL 2.1.0 CPU wheel. Does not support sm_120; used
  only for correctness sanity checks.

Blockers to watch:
- WSL GPU/NVML: `Failed to initialize NVML` and `torch.cuda.is_available()` False were transient, fixed
  by `wsl --shutdown` then reopen. If it breaks again, check the Windows NVIDIA driver and `wsl --update`.
- DGL on Blackwell is the real reproduction risk. The S2DN README pins `dgl==1.1.2` and the repo
  `requirements.txt` pins `dgl==0.4.2`, neither of which supports sm_120. The working path is a DGL 2.x
  wheel with S2DN's DGL API calls patched forward.
- LMDB cache path does not encode `--max_links`, so a smoke run and a full run can collide on the same
  `subgraphs_*` cache. Delete partial caches before and after smoke runs.

Compatibility patches applied to the modern stack:
- `managers/evaluator.py`: unwrap `(score, kl_loss)` before metric calculation.
- `test_ranking.py`: unwrap tuple outputs; `torch.load(..., weights_only=False)` for PyTorch 2.6+;
  normalize loaded model `params.device` so CPU ranking does not mix CPU graph features with CUDA graphs.
- `subgraph_extraction/graph_sampler.py`: LMDB map size handling, writer env close, `num_workers=0`.
- `subgraph_extraction/datasets.py`: LMDB env cache and `max_dbs=6`.
- `train.py`: removed hardcoded `params.lr = 0.01` and `params.batch_size = 32` so paper hyperparameters
  are honored.

Launcher and collection tooling (in `scripts/` and WSL `S2DN/scripts/`):
`check_env.sh`, `check_gpu_env.py`, `start_*_detached.py` (Popen `start_new_session=True`),
`start_eval_only_detached.py` (resume ranking without retraining), `run_fb237_paper_split_gpu.sh` and
`start_fb237_paper_split_detached.py` (optional batch-size argument), `collect_reproduction_results.py`
(prefers `_paper`, then `_paper_bs16`, then `_paper_bs8`, never invalid default-param logs).

---

## 4. The AAAI 2025/2026 KG landscape and competitor map (from the PDF)

Origin: PDF sections 3, 4, and Details. Kept in full so the related-work section and the novelty
argument are not reconstructed from memory.

Nine landscape clusters (the PDF's map): KG completion/embeddings; inductive KGC; temporal KGs;
multimodal KGs; LLM+KG and GraphRAG (the fastest-growing and most crowded); KGQA/reasoning; entity
alignment; hyper-relational/n-ary KGs; and the smallest, KG error detection/denoising/quality, which is
exactly where our evidence lives. Scale: AAAI 2026 accepted 4,167 of 23,680 submissions (17.6 percent,
lowest in three years; up from 12,957 and 23.4 percent at AAAI 2025).

Representative named works: KGCRR (AAAI 2025, the CRR loss the substrate uses); Relation-Aware Anchor
KGC (AAAI 2025); TruthfulRAG (AAAI 2026); "You Don't Need Pre-built Graphs for RAG" (AAAI 2026); KG
Error Detection with Contrastive Confidence Adaption (AAAI 2024); Type-Information-Assisted
Self-Supervised KG Denoising (AISTATS 2025).

The four nearest papers and the one-line differentiation for each (reviewers will anchor here):
- CCA, Liu, Liu and Hu (Nanjing University), AAAI 2024, Vol. 38(8) pp. 8824-8831,
  doi:10.1609/aaai.v38i8.28729. Text plus graph structure from triplet reconstruction, but synthetic
  noise, monolingual English, detection only, no downstream impact. The paper reviewers will most cite
  against us. We find AI-fabricated descriptions, not bad edges.
- Type-Information-Assisted Self-Supervised KG Denoising, AISTATS 2025, arXiv 2503.09916. Structure-only
  self-supervised noise detection; no text, so no structure-vs-text disagreement; no multilingual, no
  repair, no grounding.
- TruthfulRAG, AAAI 2026. Resolves factual conflicts at RAG inference time, not contamination stored in
  a KB; no low-resource focus.
- Retrieval Collapses When AI Pollutes the Web, WWW 2026 short paper. Proves AI pollution degrades
  retrieval; proposes no detection, no KG signal, no repair. Motivates our direction rather than
  occupying it.

Adjacent but further: mRAKL (Findings of ACL 2025, constructs low-resource KGs via RAG, assumes
evidence is trustworthy), KG-TRICK (COLING 2025, fills missing text/links, does not audit
contamination), FactNet (2026, prevents contamination by deterministic construction rather than
detecting or repairing it).

Four-pillar novelty claim (use as a supporting point, not the thesis, per the critique): no verified
AAAI 2025/2026 or SIGIR/KDD/WSDM/WWW/ACL/EMNLP 2025-2026 paper combines all of (1) detecting
AI-fabricated contamination in a KB's own descriptions, (2) using structure-vs-text disagreement as the
signal, (3) concentrated in low-resource/non-Latin scripts, (4) with a measured downstream
completion/grounding effect plus repair.

Confidence caveats (from the PDF): AAAI 2026 accepted 4,167 papers and could not be enumerated fully, so
a niche partial-overlap KG-quality paper could exist; confidence in the four-pillar "open" verdict is
high, medium that zero partially-overlapping AAAI-26 papers exist. The repo snapshot is dated
2026-07-07, so a fresh sweep immediately before submission is essential. Our own reported numbers
(70 percent contamination, ROC-AUC 0.995, plus 1.95 MRR, 26.51 MRR) are single-run or on controlled
benchmarks and are not independently reproduced.

---

## 5. Mentor topic coverage map (nothing silently dropped)

Origin: mentor ladder Section 9. Every topic the mentor named, and where it lands, so each can be
defended in the next meeting.

| Mentor topic | Relevance | Where it lives in this pathway |
|---|---|---|
| Rule mining, prediction, inference | Very high | Phase B `rule_miner.py`; Phase D2 GOLD-style triple quarantine |
| Neurosymbolic AI | Very high | Phase B and B2 are the neurosymbolic layer; the umbrella framing for P2/P3 |
| Heuristic ontology alignment | Medium now, high later | Phase B2 relation similarity; Phase C cross-language alignment; Phase D2/D3 cross-lingual lookup |
| Fuzzy search | Medium (a tool, not the novelty) | Phase D3 name and alias matching, cross-lingual and cross-script lookup |
| Gephi | Low as method, useful for analysis | Phase E figures: GraIL vs refined subgraphs, contamination clusters |
| B+ trees (Abdul Bari) | Low for novelty, foundational | Scalability study: entity ID lookup, alias/adjacency indexes. Note n-gram index / BK-tree / vector index are usually more directly useful for fuzzy and vector retrieval |

The three mentor-meeting papers and their role:
- S2DN (03121-MaT, AAAI 2025): the reproduce-and-beat target. Phases A, B, B2.
- GOLD (EMNLP Findings 2023): method source for rule-plus-structure denoising; motivates the Phase B
  rule prior and the Phase D2 contradiction quarantine; the closest neighbour to differentiate against
  in the Phase B scoping check.
- LLM_sim (GenAIK 2025): repair baseline; Phase D3 optional constrained LLM repair, compared against
  re-sourcing. Deliberately not used for reproduction.

---

## 6. Cross-cutting discipline (the gates that are not optional)

Traps already paid for in hours (from RULETRUST_EXPERIMENT_LEDGER "Do Not Repeat" and the ladder). They
apply to every phase.

- Verify logged hyperparameters, not the command line, before any long run. The released S2DN code had a
  hardcoded `params.lr = 0.01` that silently overrode the CLI and invalidated a 4h46m run. Grep the
  training script for assignments to `params.*` after argument parsing.
- A smoke test proves the code executes, not that a change has any effect. The first RuleTrust prior
  passed a one-epoch smoke run while being provably inert. Always add an assertion or diff that shows
  the change alters the output.
- Seeds before metric claims. Single-seed swings on the 205-triple fb237_v1 test set exceed the effects
  we chase; one triple is worth about 0.5 points of Hits@k. Treat any gain below roughly 1 MRR point
  from one seed as not real.
- Training runs longer than one hour are handed to the user to launch, via `scripts/start_*_detached.py`.
  `nohup ... &` inside `wsl -- bash -lc` does not survive the session. Writing shell scripts into WSL
  through a `wsl bash -lc` heredoc strips `$1` and `${VAR}`; write via the UNC path and verify with
  `cat -A`.
- Rule mining uses the training graph only, with the target edge removed from the subgraph. Assert both
  in code, not by assumption.
- Do not over-claim novelty. Claim a defensible gap with evidence, not absolute first. The four-pillar
  combination is a supporting point, not the thesis.
- The existing DBP-5L pipeline stays the source of truth for multilingual text baselines and
  contamination experiments; S2DN work stays in its isolated `venv_s2dn` environments.
- Do not add multilinguality until English RuleTrust-S2DN beats or meaningfully matches S2DN; do not add
  LLM repair until graph-text self-healing evaluation is stable.

---

## 7. Consolidated test and verification plan

Origin: mentor ladder Section 6, extended to cover the merged phases.

Environment:
- [ ] WSL path exists; `nvidia-smi` works; `torch.cuda.is_available()` True.
- [ ] `venv_s2dn` imports torch, dgl, lmdb, networkx; dgl sees the GPU (or the documented CPU fallback).

Reproduction:
- [ ] FB15k-237 v2-v4 and NELL training and ranking complete; result tables carry Hits@1, Hits@10, MRR;
      averages computed at a fixed batch size.

RuleTrust:
- [ ] Rule mining creates deterministic cached rule files.
- [ ] `--use-rule-trust` absent, and mode=adjacency, match baseline behavior.
- [ ] mode=score seed sweep produces an error bar; ablations show whether rule priors help.

Multilingual:
- [ ] Converter preserves the entity-disjoint inductive split; per-language folders load without parser
      errors; graph-only runs complete for English then all five; compared against the BGE-M3 substrate.

Self-healing:
- [ ] Existing detector result reproducible; controlled realistic-fabrication injection benchmark reports
      ROC-AUC and per-language precision/recall/F1; real contamination subset reports flag rate;
      structure-poor recall lift reported for ja and el; cleaned descriptions improve or preserve
      multilingual KGC; low-resource impact reported separately.

---

## 8. How every PDF gap and mentor item is now accounted for

| Source item | Disposition in this pathway |
|---|---|
| PDF Gap 1: self-healing multilingual KBs | P2, Phase D1 and D3. The headline. |
| PDF Gap 2: DBP-5L-Ind benchmark plus baselines | P1, Phase C. Separable lower-risk product. |
| PDF Gap 3: auditing structure-poor entities | Promoted into P2, Phase D2, fused with RuleTrust transfer. |
| PDF Gap 4: completion-before-RAG | Explicitly not pursued; crowded (mRAKL, KG-TRICK). Recorded so it is not revisited. |
| PDF competitor map and nine clusters | Section 4; Phase E related work. |
| PDF venue timing and confidence caveats | Section 4 and Section 9. |
| PDF 57 percent recall soft spot | The design driver for Phase D2. |
| PDF two-paper split | Products P1 and P2. |
| PDF monitoring trigger | Section 9.3. |
| Mentor Phase 1 reproduction | Phase A. |
| Mentor Phase 2 Structure Refining | Phase B. |
| Mentor Phase 2b Semantic Smoothing | Phase B2. |
| Mentor Phase 3 multilingual bridge | Phase C. |
| Mentor Phase 4 self-healing | Phase D. |
| Mentor topics (fuzzy search, Gephi, B+ trees, ontology, neurosymbolic) | Section 5. |
| Mentor papers S2DN, GOLD, LLM_sim | Section 5. |
| Environment, blockers, compatibility patches | Section 3. |

---

## 9. Venue, sequencing, and strategic monitoring

### 9.1 Deadlines (updated 2026-07-17: decision is A-star only, SIGIR primary)

- SIGIR 2027: PRIMARY target for P2 (and P1 if bundled or as a resource paper). Historically a
  late-January deadline; 2027 dates not yet posted. Action: watch for the CFP and pin the date the
  moment it appears. The roughly six months of runway is what makes "reproduce all three datasets
  plus working modifications plus multilingual plus self-healing" realistic.
- WSDM 2027 full paper (about Aug 24, 2026): demoted from primary to fallback. Take it only if Gate B
  and Phase D both land unusually early and the paper is genuinely ready; do not compress the work to
  chase it.
- KDD 2027 Cycle 2 (about Feb 2027): fallback, fits KG data-quality work.
- AAAI-27 (full papers July 28, 2026): effectively out; kept only as the record of why it was dropped
  (two-week window, 7 pages, no CJK package).
- ISWC and WWW remain natural homes if all else slips.

### 9.2 Recommended ordering (updated 2026-07-17 for the 96 GB lab GPU)

1. Close Gate B (RuleTrust seeds) first. It is the current blocker and decides whether P3 exists and how
   P2's method reads. Small, high-information experiment. Run on the lab GPU when access lands.
2. In parallel, start Phase D1 detector hardening, independent of the S2DN thread and on the P2 critical
   path for WSDM.
3. Finish Phase A reproduction (FB15k-237 v2-v4, NELL) as background GPU work between the above; on the
   96 GB GPU run at true paper settings (batch 32) so no batch-size deviation needs documenting.
4. Phase C multilingual bridge and P1 assembly after Gate B resolves (converter already done and
   verified, Section 0a finding 3).
5. Phase E packaging into the WSDM window for P2, later cycle for P1.

GPU split once the lab machine is up: lab 96 GB takes the long training runs (reproduction, seed
sweeps, multilingual); the local RTX 5070 Ti keeps CPU-adjacent and small jobs (rule mining,
detector scoring, claim extraction with the local Llama). Mentor's standing instruction while SSH is
being set up: architecture limitations and weaknesses study, delivered as
[s2dn_architecture_weaknesses.md](s2dn_architecture_weaknesses.md); the 96 GB test plan is its
Section 5.

### 9.3 Strategic monitoring trigger (PDF recommendation 1)

If a competing AAAI-26, WWW-26, or SIGIR-26 paper surfaces that couples structural contamination
detection plus repair on multilingual KBs, pivot the P2 framing toward Gap 3 (structure-poor auditing),
where the field is emptier. The fresh pre-submission sweep (Phase E) is where this is checked.

---

## 10. Immediate next three actions (updated 2026-07-17)

1. When lab GPU SSH lands: launch the RuleTrust seed sweep (3 to 5 seeds each of baseline and
   RuleTrust mode=score on fb237_v1) and queue FB15k-237 v2 to v4 at true paper batch 32. Gate B
   closes here. (Blocker.)
2. Until then, CPU work: the D2 decisive cheap test (pattern-based claim extractor; 718 auditable
   contaminated vs 718 degree-matched clean; does the claim-level score beat the neighbourhood
   detector alone?), and the realistic-fabrication injection set spec.
3. Resolve the converter's 2 percent out-of-vocabulary test-triple quirk (drop and document, or
   extend support), so Phase C is launch-ready the moment Gate B resolves.

Superseded but kept for the record: the pre-2026-07-17 action list queued FB15k-237 v2 at batch 16 on
the local 16 GB GPU; the 96 GB lab GPU makes batch 32 the preferred path, with batch 16 as
contingency.

Open questions: ANSWERED 2026-07-17. Questions kept for the record, answers inline.

1. What does "beat S2DN" mean? Answer: S2DN was chosen as the recent, best-aligned paper; the plan is
   to beat its score, then take the improved model to inductive plus multilingual and aim for best in
   that field. So the S2DN frame stays, modifications inside it are the vehicle, and the endgame is
   the multilingual-inductive cell (which the survey confirms is still empty). The SOTA caveat from
   Section 0a stands: beating S2DN is the milestone, not the SOTA claim; the baseline table still
   needs MorsE and a foundation-model point.
2. Reproduction scope? Answer: reproduce all three (WN18RR, FB15k-237, NELL), and make working
   modifications alongside, not after. Phase A full scope confirmed; Phase B runs in parallel rather
   than strictly behind it.
3. Is RuleTrust the agreed modification? Answer: only results decide. Gate B stays purely empirical;
   no pre-commitment to the rule mechanism if seeds do not support it.
4. Venue? Answer: A-star only, so SIGIR. P2 targets SIGIR 2027 (historically a late-January deadline,
   2027 dates not yet posted). This replaces WSDM as primary and removes the August crunch; WSDM and
   KDD Cycle 2 remain fallbacks. Watch for the SIGIR 2027 CFP.
5. Both neuro-symbolic branches (B/B2)? Answer: anything that makes the architecture novel and
   better. Not tied to the two-branch framing; the measured score-level fusion is acceptable if it
   wins, B2 Semantic Smoothing guidance is pursued if it adds, dropped if it does not. Results
   arbitrate, same as answer 3.

Deadline reality (from ladder Section 8, still true): the full ladder is not finishable in one venue
cycle. The realistic first submittable unit is "reproduce S2DN and land one principled improvement on
English inductive KGC." The mentor said there is no hurry, which fits; the WSDM window is the target
for P2 only if Phases B and D land cleanly, otherwise KDD Cycle 2 without drama.
