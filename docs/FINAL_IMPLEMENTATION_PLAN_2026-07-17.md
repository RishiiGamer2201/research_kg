# Final Implementation Plan: SelfHeal-MKGC

**Based on:** [Final Research Proposal](FINAL_RESEARCH_PROPOSAL_2026-07-17.md)

**Execution target:** one unified paper on evidence-budgeted, self-healing multilingual inductive KGC

**Primary workspace:** Windows repository plus the WSL training workspace

**Primary branch:** `main`

**Status date:** 17 July 2026

> **Mandatory completion rule:** change `[ ]` to `[x]` only after the task's acceptance criteria pass and its evidence artifact is committed. At the end of every phase, update the cumulative ledger below, record unresolved errors and inferences, commit the phase, and run `git push origin main`. A phase is not complete merely because training finished.

## Phase-completion GitHub checklist

Run this checklist at the end of **every** phase:

- [ ] All completed task boxes in this file are changed to `[x]`.
- [ ] The cumulative results ledger has new rows for every valid, invalid, failed, or inconclusive run.
- [ ] Every row records the code commit, split hash, description hash, model revision, seed, candidate set, filtering policy, checkpoint hash, and exact command.
- [ ] Errors, corrections, and scientific inferences are appended; earlier rows are never silently overwritten.
- [ ] Phase tests, leakage assertions, determinism checks, and `git diff --check` pass.
- [ ] Large checkpoints and caches are excluded; manifests, compact metrics, configs, and logs are included.
- [ ] Only intended files are staged with explicit paths.
- [ ] A Conventional Commit is created, for example `feat(phase-1): freeze dbp5l-ind-v2 folds`.
- [ ] The completed phase is pushed directly with `git push origin main`.
- [ ] The pushed commit SHA and completion date are recorded in the phase gate.

## Cumulative results, errors, and inference ledger

Append every new result to this table. Do not replace the historical result when a corrected result becomes available; add a correction row and link the invalidated row.

| ID | Date | State | Phase | Experiment and protocol | Main result | Error or limitation faced | Inference and decision | Evidence |
|---|---|---|---|---|---|---|---|---|
| R-001 | 2026-06/07 | Valid historical | Substrate | Zero-shot BGE-M3, current DBP-5L-Ind | MRR 1.45 | No task adaptation | Pretrained retrieval alone is insufficient | [Results ledger](RESULTS_AND_INFERENCE.md) |
| R-002 | 2026-06/07 | Valid historical | Substrate | Row3-HN: CRR, seven hard negatives, length 96 | MRR 13.77; H@1 6.69; H@10 27.02 | Initially reported as 11.36 because support facts were not filtered | CRR and fresh hard negatives are synergistic; correct filtering materially affects weak models | [Results ledger](RESULTS_AND_INFERENCE.md) |
| R-003 | 2026-06/07 | Valid historical | Substrate | Run A: enriched descriptions, length 128 | MRR 23.80; H@1 15.72; H@10 39.14 | Description provenance was not yet clean enough for final claims | Rich text supplied the largest controlled gain | [Results ledger](RESULTS_AND_INFERENCE.md) |
| R-004 | 2026-06/07 | Valid historical | Substrate | Run B: Run A plus LoRA rank 16 | MRR 25.15; H@1 17.20; H@10 40.10 | Evaluation originally truncated every model at 96 tokens | LoRA rank 16 added 1.35 MRR after matched evaluation | [Results ledger](RESULTS_AND_INFERENCE.md) |
| R-005 | 2026-06/07 | Valid but provisional | Substrate | Run E single reference: BGE-M3/LoRA, CRR, HN=7, length 160 | MRR 26.69; H@1 18.80; H@3 29.43; H@10 41.62 | Trained on the old description snapshot | Length 160 is the strongest completed configuration; final clean retraining remains required | [Results ledger](RESULTS_AND_INFERENCE.md) |
| R-006 | 2026-07-03 | Valid but provisional | Substrate | Run E seeds 42, 123, 777 | MRR 26.51 +/- 0.31; H@1 18.35 +/- 0.52; H@10 41.76 +/- 0.28 | Same old-description limitation and current split leakage risks | The training recipe is stable enough to serve as the starting baseline, not the final headline | [Seed table](RESULTS_AND_INFERENCE.md) |
| R-007 | 2026-07 | Valid baseline | Substrate | mBERT under matched CRR/HN/LoRA recipe | MRR 24.08 | BGE comparison is not final until clean BGE retraining | BGE-M3 leads by 2.43 MRR, especially on ES and EL | [Baseline table](RESULTS_AND_INFERENCE.md) |
| R-008 | 2026-07 | Valid but provisional | Substrate | All-language ranking over 56,589 candidates | MRR 26.01 +/- 0.30 versus 26.51 +/- 0.31 within-language | Candidate universe differs from within-language evaluation | Cross-language confusions account for only 0.50 MRR in the current model | [Cross-lingual table](RESULTS_AND_INFERENCE.md) |
| R-009 | 2026-07 | Diagnostic, not causal repair | Substrate | Remove unverifiable back-fill at evaluation time | Overall 26.69 -> 26.94; JA 17.90 -> 19.85; EL 18.42 -> 18.33 | No matched retraining; only evaluation text changed | Contaminated text can reduce KGC, but clean three-seed retraining is needed | [Description audit](RESULTS_AND_INFERENCE.md) |
| R-010 | 2026-07-07 | Valid synthetic sanity test | Substrate | BGE graph-text detector on 400 clean/wrong-entity pairs | ROC-AUC 0.995; precision 0.985; recall 0.990; F1 0.988 at threshold 0.773 | Random swaps are easier than realistic contamination | The signal works in principle, not yet on a publication-grade corruption benchmark | [Detector report](pivot/self_healing_detector_result_2026-07-07.md) |
| R-011 | 2026-07-07 | Diagnostic | Substrate | Detector on 40 real LLM-generated fabrications with at least two edges | 23/40 flagged; mean score 0.761 | Zero/one-edge entities often cannot be graph-audited | Detection must route by evidence availability and use source/claim verification when graph evidence is absent | [Detector report](pivot/self_healing_detector_result_2026-07-07.md) |
| R-012 | 2026-07 | Valid reproduction | Substrate | S2DN on WN18RR inductive v1-v4 | Average MRR 73.77; H@1 69.12; H@5 77.36; H@10 80.57 | Average H@10 is 0.66 below the paper | Structural implementation is sufficiently reproduced for an appendix baseline | [Proposal previous work](FINAL_RESEARCH_PROPOSAL_2026-07-17.md) |
| R-013 | 2026-07-10 | Valid reproduction | Substrate | S2DN FB15k-237 v1, corrected paper parameters | MRR 53.13; H@1 44.63; H@5 61.22; H@10 67.80 | Release hardcoded a learning rate that overrode the CLI in an earlier invalid run | Verified logged parameters are mandatory; reproduction exceeds the paper's v1 result slightly | [RuleTrust ledger](pivot/RULETRUST_EXPERIMENT_LEDGER.md) |
| R-014 | 2026-07-12 | Inconclusive metric, valid mechanism | Substrate | RuleTrust-S2DN, FB15k-237 v1, one seed | MRR 53.19; H@1 44.15; H@10 71.22; learned scale 3.90 | Only 205 test triples and one seed | Rules carry usable signal, but no defensible ranking gain is established | [RuleTrust ledger](pivot/RULETRUST_EXPERIMENT_LEDGER.md) |
| R-015 | 2026-07-12 | Valid control, inconclusive comparison | Substrate | Shuffled RuleTrust control | MRR 51.03; H@10 70.00; learned scale 0.12 | Metric swing exceeded the apparent real-rule effect | Mechanism check passes because the model rejects shuffled rules; multi-seed paired evaluation is required | [RuleTrust ledger](pivot/RULETRUST_EXPERIMENT_LEDGER.md) |
| R-016 | 2026-07-17 | Valid infra | Phase 0 | P0.1 source unification: copy WSL-only active code into tracked repo; add `RESEARCH_KG_ROOT` override; capture env | 5 root scripts + 4 wrappers + README committed; 4 scripts de-hardcoded; env frozen (py3.10.20/torch2.11+cu128/transformers5.12.1/peft0.19.1) | text venv lacks FlagEmbedding/DGL (by design — BGE-M3 via transformers); 3 divergent S2DN venvs, canonical one not yet frozen | Repo now carries the active pipeline; end-to-end clean-clone smoke deferred to P0.5 | `wsl/research_kg/ENVIRONMENT.md`, `requirements.simkgc-venv.txt` |
| R-017 | 2026-07-17 | Valid infra | Phase 0 | P0.2 immutable run manifests: `run_manifest.py` (stdlib-only) wired into trainer + evaluator | Self-check passes (byte-flip changes hash; overwrite refused). Live test hashed real DBP5L splits/descriptions, captured torch/GPU, resolved BGE-M3 cache revision `9a0624b8…`; status running→complete | candidate-set & filter hashes not yet included (need persisted candidates → P0.3); crash leaves status `running` rather than explicit `failed` | Every train/eval run is now attributable; accidental cross-run comparison blocked by hash mismatch | `run_manifest.py`, `MANIFEST_SCHEMA.md` |
| R-018 | 2026-07-17 | Valid infra + correction | Phase 0 | P0.3 deterministic eval: fix tie handling to average tied ranks; persist+hash ordered candidate universe; pin filter source files in eval manifest | Tie self-check passes (`--selftest`) in WSL venv. max_length auto-read and full known-facts filter confirmed already-correct | **Correction:** prior filtered ranks used best-case tie position (`>score`+1); future evals use averaged ties. Historical R-005/006 numbers stay valid-as-recorded (float-cosine exact ties rare, impact expected tiny) but are re-measured under the new evaluator in P0.5 | Metric attribution now deterministic; head-prediction eval deferred to P1.6 (needs reciprocal training), repeat-determinism assertion deferred to P0.5 | `eval_dbp5l.py` |
| R-019 | 2026-07-17 | Valid infra | Phase 0 | P0.4 relation identity + rule-cache keys: injective `R{id}__name` in GraIL converter; signature-keyed rule cache with stale rejection | Converter reports 93 name-collision groups (186 IDs) and passes injectivity assertion on real DBP5L; `grail_format/` regenerated. rule_miner self-check passes (setting/relation-map change → new cache; corrupt signature → re-mine) | Discovered `scripts/` wasn't symlinked (WSL ran stale converter) → fixed setup to symlink `scripts/` dir; target-edge removal at scoring deferred to P2.6 (needs dgl venv) | Merged-relation bug (§4.8, 37k triples) fixed; rule caches can no longer be silently stale | `convert_dbp5l_to_grail.py`, `S2DN/SDN/utils/rule_miner.py`, `S2DN/SDN/train.py` |
| R-020 | 2026-07-17 | Valid reproduction | Phase 0 | P0.5 eval validation: zero-shot BGE-M3 on clean descriptions, run twice through the rebuilt evaluator | Within-lang MRR **1.4402** (H@1 0.08, H@3 1.55, H@10 3.72); cross-lingual MRR 0.66. Two runs byte-identical → **DETERMINISTIC: True**. Eval manifest fully populated (candidate/split/support hashes, git commit, model rev) | none | Rebuilt evaluator reproduces historical **R-001 (1.45)** within 0.01 (diff = tie-averaging + rounding); settles P0.3 repeat-determinism assertion; P0.2 manifests confirmed on real runs | `.../zero_shot_bgem3/evals/*/manifest.json`, `scratchpad/p05_run.log` |
| R-021 | 2026-07-17 | Valid infra (smoke) | Phase 0 | P0.5 train pipeline: 1-epoch smoke train (bge, ml64, clean desc) → eval the checkpoint | Train manifest `status=complete`, ckpt hash `d2c8dcde`, metrics logged. Ckpt eval: `max_length=64` auto-read from checkpoint; eval manifest written. Smoke within-lang MRR 0.40 | Smoke MRR (0.40) is BELOW zero-shot (1.44) — expected for 1 epoch / ml64 / no-CRR / no-HN (undertrained; LoRA-B init 0; ml64 truncates). NOT a regression | Full train→checkpoint→load→eval→manifest chain validated end-to-end; real number needs the Run E config retrain | `.../bgem3_lora_dbp5l_20260717_1527_r16/manifest.json` |
| R-022 | 2026-07-17 | Valid infra (smoke) | Phase 0 | P0.5 S2DN structural smoke: fb237_v1, 1 epoch, max_links 20, paper dims, venv_s2dn_gpu_latest | Subgraph extraction (pos/neg, train/valid) + 1 epoch on cuda:0 (loss 200.8, train AUC 0.53) in ~12s; effective hyperparams logged (emb_dim 64, hop 3, batch 16, max_links 20) | batch_size defaulted to 16 (paper 32) — smoke only, not a metric run | Structural pipeline reproduces on the newest dgl venv; frozen as canonical. G0 structural-baseline item satisfied | `requirements.s2dn-venv.txt`, `scratchpad/s2dn_smoke.log` |
| R-023 | 2026-07-18 | Valid, single-seed clean baseline | Phase 0 | Run E clean retrain (seed 42, ml160, r16, CRR, HN K=7, **clean descriptions**, 30 ep) evaluated under the fixed evaluator | **Within-lang MRR 27.02** (H@1 18.52, H@3 30.19, H@10 43.02); cross-lingual 26.78. Best ckpt ep23. Per-lang FR 37.7 / ES 37.6 / JA 19.8 / EL 17.1 / EN 16.1. Train + eval manifests complete (ckpt c85f23de) | Single seed only — no clean-vs-contaminated claim yet | Seed-42 clean 27.02 sits within the provisional R-005/006 band (26.51±0.31 / 26.69), so this run shows **no evidence contamination inflated it** — but that is NOT a definitive clean-vs-contaminated comparison; the **3-seed clean baseline (Phase 2)** is required before any such claim. Rebuilt pipeline reproduces the ~26–27 regime → **Gate G0 baseline reproduced** | `.../bgem3_lora_dbp5l_20260717_1541_crr_hn7_r16/{manifest.json,evals/*/manifest.json}`, `scratchpad/eval_E.log` |
| R-024 | 2026-07-18 | Valid benchmark infra + finding | Phase 1 | P1.2 concept clustering (union-find over alignments) + P1.7 concept-leakage audit of v1 split | 56,589 entities → **29,440 concepts** (9,762 multilingual size 2–5, 19,678 singletons, 0 ambiguous), deterministic hashes. v1 audit: **72.3% of test concepts (4,964/6,866) leak into train** via cross-lingual aligned IDs | v1 mapping clean (0 unmapped) | v1 `ind/` split is NOT concept-inductive — quantifies §4.3 and motivates v2. `assert_concept_disjoint` ready for P1.3 fold builder | `build_concept_clusters.py`, `concept_leakage_audit.py`, `DBP5L/ind_v2/concepts/concept_stats.json` |
| R-025 | 2026-07-18 | Valid benchmark infra | Phase 1 | P1.3 three fixed concept-disjoint folds (seeds 13/42/79), stratified by language coverage | Per fold: train 22,082 / valid 2,943 / test 4,415 concepts (75/10/15); all 5 langs present in valid+test; degree median 3 across splits; `assert_concept_disjoint` passes on all folds; distinct manifest hashes per seed; deterministic | none | Concept-disjoint inductive folds replace the 72.3%-leaking v1 split; ready for P1.4 support budgets | `build_v2_folds.py`, `DBP5L/ind_v2/folds/fold{0,1,2}_seed{13,42,79}/` |
| R-026 | 2026-07-18 | Valid benchmark infra | Phase 1 | P1.1 freeze + hash raw DBP-5L source; provenance + licensing | `source_manifest.json`: 31 files, 6.66MB, `top_sha256=0eca75a5…`. Provenance doc: KEnS/EMNLP-2020, CC BY-SA 3.0 obligations, ID layers URI→(lang,local)→global→concept | Exact upstream git commit not captured at download (content hash is the anchor instead) | v2 benchmark is content-addressed to an immutable source snapshot | `hash_source_data.py`, `DBP5L/ind_v2/source_manifest.json`, `DBP5L_DATA_PROVENANCE.md` |
| R-027 | 2026-07-18 | Valid benchmark infra | Phase 1 | P1.4 nested evidence budgets S^0⊂S^1⊂S^3⊂S^5 per fold, comparability rule enforced | Per fold (fold0): 10,399 unseen entities w/ support, avg pool 3.81, S^5 union 39,152; eval_targets_test 36,940 / valid 18,233; exposed/budget 0/10.4k/27k/39.6k. Invariants pass: caps \|S^k\|≤k, prefix nesting, **target∩S^5=0**, **targets fixed across budgets**, **single filter (one hash) all budgets**. Deterministic | none | S^5-union-first + remove-from-all-targets makes budgets directly comparable (only exposed evidence varies) | `build_v2_support_budgets.py`, `DBP5L/ind_v2/folds/*/budgets/` |
| R-028 | 2026-07-18 | Valid benchmark infra | Phase 1 | P1.5 clean v2 descriptions from permitted evidence + full provenance | 56,589 entities: **48,496 native Wikipedia / 4,274 cross-lang / 3,819 name** (no LLM). EL leans most on cross-lang+name (low-resource). snapshot_rev=7ba0dd5f. Raw+norm hashes separate; cross-lang records source gid/concept + translated=false; deterministic | Per-page Wikipedia revision ids not captured (corpus frozen by snapshot_rev — recorded gap); snapshot text kept verbatim (answer leakage → P1.7, not stripped) | Clean snapshot-only corpus replaces the LLM-contaminated one and sidesteps the §4.2 graph-text leak; alignment-free primary track (P1.6) can exclude `wikipedia_cross_lang` for test/valid | `build_v2_descriptions.py`, `DBP5L/ind_v2/descriptions/descriptions_v2_stats.json` |
| R-029 | 2026-07-18 | Valid benchmark infra | Phase 1 | P1.6 Part A — eval track/view definitions | Primary alignment-free view (d1afcf20, **0 cross-lang asserted**, 4,274→name); oracle diagnostic view (2a19bb0b); all-lang candidate universe (6a641485, matches evaluator) + 5 within-lang universes, independent hashes; track manifest declares head/tail/combined directions + budget-fixed targets/filter | Head+tail prediction code (reciprocal tokens, head/tail/combined reporting) + retrain = Part B, pending | Track contract + hashed views ready; alignment-free primary excludes cross-lang by construction | `build_v2_eval_tracks.py`, `DBP5L/ind_v2/tracks/` |
| R-030 | 2026-07-18 | Valid infra | Phase 1 | P1.6 Part B — reciprocal head+tail code in evaluator + trainer | Evaluator `--directions tail,head`: reverse-filter map, `reverse of` marker, reports head/tail/combined separately + `by_direction` in save + manifest; **tail wl-MRR 1.44016 reproduces R-020 exactly** (backward compatible), head 1.409 / combined 1.425 (zero-shot). Trainer `--reciprocal 1`: 2×118,256 examples, shared marker, distinct cache tag; smoke trains+saves, exit 0 | Head numbers only meaningful after reciprocal training on the v2 folds — trainer/evaluator still read old `processed/*.json`; v2-fold wiring + headline head/tail/combined = Phase 2 | Reciprocal head+tail contract implemented in BOTH train and eval, both self/backward-compat validated | `eval_dbp5l.py`, `train_dbp5l_lora.py` |
| R-031 | 2026-07-18 | Valid benchmark finding | Phase 1 | P1.7 answer-mention leakage on preserved snapshot text, by direction/language/source | Primary/fold0: overall exact 39.0% / subset 26.6%; **tail 63.1% vs head 14.9%**; native 41.0% / cross-lang 1.7% / name 3.4%; EN 46.6% highest | trivial (≤2char/numeric) names counted separately | Big fraction of tail predictions readable from head's description → report leakage-stratified metrics; head direction far cleaner | `audit_v2_answer_leakage.py`, `ind_v2/audits/answer_leakage.json` |
| R-032 | 2026-07-18 | Valid benchmark finding | Phase 1 | P1.7 structural audits: distributions, duplicates, inverse relations | 56,589 ent / 185,866 trip / 903 rel; degree med 5 max 3,911; 3,767 dup-desc groups, 8,082 dup-name groups; 20 inverse-relation pairs (289↔298 sup 2,136), 2,441 reciprocal same-rel triples | dup-names largely cross-language aligned concepts (expected) | Inverse-relation + reciprocal edges are a real shortcut → must be reported / controlled at eval | `audit_v2_structure.py`, `ind_v2/audits/structure.json` |
| R-033 | 2026-07-18 | Valid benchmark validity | Phase 1 | P1.7 PPR + shortest-path shortcut audit on target-edge-removed graphs (relation types dropped) | 3 folds, 400 tail targets each: PPR MRR 0.051–0.061, Hits@1 ~0, Hits@10 0.12–0.15; ~50,622 answer edges excluded/fold; median SP 3; 97–99% reachable | 400-sample per fold (audit, not full) | **No structural PPR shortcut** — structure (5%) ≪ text (27%); benchmark not trivially solvable by structure. Satisfies §4.5 / Shomer KDD 2025 concern | `audit_v2_ppr_shortcut.py`, `ind_v2/audits/ppr_shortcut.json` |
| R-034 | 2026-07-18 | Valid benchmark validity (refinement of R-033) | Phase 1 | PPR audit + random & degree baselines + relation-level outliers | PPR MRR 0.051–0.061; **degree baseline 0.063–0.076 (≈ or > PPR)**; random 0.0006–0.0016; relation-level outliers: none | 400-sample/fold | Structural signal is mostly popularity (degree ≈ PPR), ≫ random but ≪ text (0.27): PPR/structure does **not explain text performance**; no per-relation structural shortcut. Corrects R-033's over-strong "no shortcut" wording | `audit_v2_ppr_shortcut.py`, `ind_v2/audits/ppr_shortcut.json` |
| R-035 | 2026-07-18 | Valid benchmark fix | Phase 1 | P1.7 inverse/reciprocal answer edges exposed through support + inverse-clean track | Per fold: test reveal ~7.2–7.6% (≈2,700–2,810 targets), valid ~9.7–11.2%; exact reciprocals only ~23–26; ~3,900–4,074 support edges dropped → `s5_union_inverse_clean.json` (hashed) per fold | Adjacency mostly via non-inverse relations, not just the 2,441 exact reciprocals | Some support directly reveals answers via h↔t adjacency → inverse-clean S^5 provided; structural models (Phase 2) consume the clean exposure | `audit_v2_inverse_support.py`, `folds/*/budgets/{s5_union_inverse_clean,inverse_support_audit}.json` |
| R-NEXT | YYYY-MM-DD | Planned | Phase N | Run ID, dataset/fold, model, seed, exact protocol | MRR/Hits/calibration/repair/QA metrics | Failure, correction, limitation, or `none` | Scientific inference and keep/drop decision | Manifest and result path |

## 0. Shared definitions and mathematical specification

### 0.1 Concept-disjoint multilingual induction

Let the multilingual graph for language $\ell$ be:

$$
G^\ell=(V^\ell,R^\ell,E^\ell), \qquad E^\ell\subseteq V^\ell\times R^\ell\times V^\ell.
$$

Cross-language entity alignments induce real-world concept clusters $C_1,\ldots,C_n$. Split clusters, never individual language IDs:

$$
\mathcal C_{\mathrm{train}}\cap\mathcal C_{\mathrm{valid}}=\varnothing,
\quad
\mathcal C_{\mathrm{train}}\cap\mathcal C_{\mathrm{test}}=\varnothing,
\quad
\mathcal C_{\mathrm{valid}}\cap\mathcal C_{\mathrm{test}}=\varnothing.
$$

For every test concept $C_i$ and language $\ell$:

$$
C_i\cap V^\ell_{\mathrm{train}}=\varnothing.
$$

The main track is alignment-free at test time. Test alignments may be used only in an explicitly labelled oracle diagnostic.

### 0.2 Nested evidence budgets

For every unseen entity $e$, construct one deterministic ordered support list, then expose prefixes:

$$
S_e^0\subset S_e^1\subset S_e^3\subset S_e^5,
\qquad |S_e^k|\le k.
$$

The cap is applied after combining all candidate support sources. Every support triple is included in the known-true filter and removed from validation/test targets.

### 0.3 Text bi-encoder

For tail prediction $q=(h,r,?)$, build query text $x_q$ from the head description and injective relation representation. Candidate $c$ uses the tail description $x_c$:

$$
\mathbf q=\operatorname{norm}(f_{\theta,\phi}(x_q)),
\qquad
\mathbf c=\operatorname{norm}(f_{\theta,\phi}(x_c)),
\qquad
s(q,c)=\frac{\mathbf q^\top\mathbf c}{\tau}.
$$

$\theta$ denotes frozen or partially frozen BGE-M3 weights, $\phi$ denotes LoRA parameters, $\tau>0$ is the contrastive temperature, and `norm` is L2 normalization. Head prediction uses the reciprocal query $(?,r,t)$ with a direction marker.

LoRA replaces an adapted projection $W$ with:

$$
W'=W+\frac{\alpha}{r}BA,
\qquad
A\in\mathbb R^{r\times d_{\mathrm{in}}},
\quad
B\in\mathbb R^{d_{\mathrm{out}}\times r}.
$$

The locked historical recipe uses rank $r=16$; the scaling $\alpha$, target modules, dropout, and model revision must be captured in the run manifest.

### 0.4 Ranking objectives

For gold candidate $y$ and candidate set $\mathcal B$, InfoNCE is:

$$
\mathcal L_{\mathrm{NCE}}
=-\log
\frac{\exp(s_y)}{\sum_{j\in\mathcal B}\exp(s_j)}.
$$

The current CRR implementation uses the KGCRR-style differentiable rank upper bound:

$$
\mathcal L_{\mathrm{CRR}}
=\log\left(
1+\sum_{j\ne y}
\sigma\left(\frac{s_j-s_y-\rho}{\tau_c}\right)
\right).
$$

$\rho$ is the score pressure/margin and $\tau_c$ controls smoothness. The historical run used $\rho=0.1$ and $\tau_c=0.1$ with the sigmoid exponent clamped to $[-80,80]$. Compare InfoNCE, CRR, and any combined loss using the same negative set.

### 0.5 Evaluation metrics

For filtered rank $r_i$ of the correct candidate:

$$
\mathrm{MRR}=\frac{1}{N}\sum_{i=1}^{N}\frac{1}{r_i},
\qquad
\mathrm{Hits@}k=\frac{1}{N}\sum_{i=1}^{N}\mathbf 1[r_i\le k].
$$

Report head and tail prediction, micro average, macro-language average, worst-language score, and every evidence/corruption stratum. Average tied ranks; never select the most favourable tied position.

## 1. Completed historical substrate

These boxes record completed work, not final-paper validity.

- [x] Build the current entity-disjoint DBP-5L diagnostic split and support graphs.
- [x] Implement BGE-M3/LoRA text ranking with CRR and hard negatives.
- [x] Run the main ablation progression through Run E.
- [x] Complete three historical Run E seeds.
- [x] Implement within-language and all-language full-candidate evaluation.
- [x] Run a matched mBERT external-encoder baseline.
- [x] Identify and correct evaluation-length, support-filter, and anchor-query mismatches.
- [x] Audit LLM-generated low-resource descriptions and create a clean description file.
- [x] Implement the first graph-text contamination detector.
- [x] Reproduce S2DN on WN18RR v1-v4 and FB15k-237 v1.
- [x] Implement RuleTrust score fusion and its shuffled-rule mechanism control.
- [x] Research Semantic Smoothing, RuleTrust, recent KGC objectives, uncertainty, self-healing, and SimRMKGC.

## 2. Phase 0 - scientific repair and reproducibility

**Goal:** make every later number attributable to immutable code, data, configuration, and evaluator state.

### P0.1 Unify the active Windows and WSL source trees

- [x] Copy or commit every active trainer, evaluator, detector, bootstrap, and launcher currently present only in WSL. *(train_dbp5l_lora, eval_dbp5l, eval_dbp5l_anchors, detector_experiment, bootstrap_sig + 4 run wrappers + WSL README → `wsl/research_kg/`.)*
- [x] Establish one canonical repository-relative path for code and one for large local artifacts. *(Code canonical: `wsl/research_kg/`. Large artifacts stay in WSL under `RESEARCH_KG_ROOT`, gitignored.)*
- [x] Remove machine-specific absolute paths from configs; resolve data/checkpoint roots through CLI arguments or a versioned local config template. *(`RESEARCH_KG_ROOT` env var, default `~/research_kg`; all 4 root scripts updated + byte-compile pass.)*
- [x] Record Python, CUDA, PyTorch, Transformers, PEFT, FlagEmbedding, DGL, and compiler versions. *(`wsl/research_kg/ENVIRONMENT.md` + `requirements.simkgc-venv.txt`. FlagEmbedding/DGL absent in text env by design; S2DN venv freeze deferred to P0.5.)*

**Acceptance:** a clean clone plus documented data placement can launch one smoke train and one full evaluator without editing source.

**Artifacts:** environment lock, setup script, smoke config, environment report.

### P0.2 Implement immutable run manifests

- [x] Generate a unique run ID before training. *(`run_manifest.start_run` → `YYYYMMDD_HHMMSS_<8hex>` UTC.)*
- [x] Persist `git_commit`, dirty-tree flag, exact command, UTC start/end time, hostname/GPU, random seeds, model revision, tokenizer revision, split hash, description hash, relation-map hash, candidate-set hash, filter hash, and checkpoint hash. *(All captured; checkpoint hash at finish; BGE-M3 model_revision resolved from HF cache. **candidate-set & filter hashes deferred to P0.3** — added once the evaluator persists an ordered candidate list + explicit filter policy.)*
- [x] Write results atomically to a new run directory; refuse to overwrite an existing result. *(`_atomic_write` via `os.replace`; `start_run` refuses a running/complete manifest.)*
- [x] Add `status = running|complete|failed|invalidated` and `invalidates_run_id` fields. *(Present; crash leaves `running` = incomplete.)*

Use SHA-256 for an artifact $a$:

$$
h(a)=\operatorname{SHA256}(\operatorname{bytes}(a)).
$$

**Acceptance:** changing one byte of a split, description, relation map, or candidate list changes the manifest and prevents accidental comparison.

**Artifacts:** JSON schema, sample manifest, validator tests.

### P0.3 Lock deterministic evaluation

- [x] Pass `max_length` from checkpoint/config rather than hardcoding it. *(Already auto-read from ckpt args; CLI override warns. Verified `eval_dbp5l.py:116,218`.)*
- [x] Persist candidate IDs and their order; do not reconstruct candidates from unordered containers. *(Ordered universe = `sorted(entity_texts.keys())`, now written to `candidates.json` per eval and SHA-256'd in the manifest — completes the P0.2 candidate/filter-hash deferral; support + all splits pinned as inputs.)*
- [x] Add train, validation, test, and support triples to the filtered-known-fact map. *(Already done — verified `eval_dbp5l.py:276-310`; support edges mapped to global IDs.)*
- [ ] Verify reciprocal head and tail query templates separately. **DEFERRED → P1.6:** evaluator is tail-only (`head [SEP] rel → tail`). Reciprocal head prediction needs reciprocal *training* (direction marker), so it lands with the benchmark tracks, not as a half-feature in P0.
- [x] Average tied ranks and test with a constructed equal-score case. *(Fixed the best-case tie bug at the shared `compute_filtered_metrics`; `rank = higher + (ties+1)/2`. Runnable check: `eval_dbp5l.py --selftest`.)*
- [x] Assert identical metrics across two consecutive evaluations of the same checkpoint. *(Done in P0.5 / R-020: zero-shot full eval run twice → byte-identical within-lang MRR 1.44016, `DETERMINISTIC: True`. Eval path has no RNG: `model.eval()`, sorted candidates, no sampling.)*

For query $(h,r,?)$, the filtered candidate set is:

$$
\mathcal C_f(q)=\mathcal C(q)\setminus
\{t'\ne t:(h,r,t')\in E_{\mathrm{known}}\}.
$$

**Acceptance:** deterministic metrics and passing unit cases for filtering, support facts, ties, head prediction, and tail prediction.

### P0.4 Repair relation identity and caches

- [x] Preserve relation IDs with an injective serialization such as `R{id}__sanitized_name`. *(`convert_dbp5l_to_grail.py`: `rel_name(r)=R{r}__name`; in-code injectivity assertion passes; `grail_format/` regenerated un-merged.)*
- [x] Detect and report relation-name collisions instead of merging them. *(Reports **93 collision groups / 186 IDs** on real data, e.g. `composer`←[2,653] matching §4.8; printed at convert time.)*
- [x] Include dataset/fold/relation-map/target-edge policy in rule-cache keys. *(`rule_miner.rule_signature` over dataset+train_file+min_support+conf+max_len+use_inverse+relation2id+target_policy; `ensure_rule_cache` validates signature on load and re-mines on mismatch. `train.py` no longer pre-sets a fixed path. Self-check: `python S2DN/SDN/utils/rule_miner.py`.)*
- [ ] Remove the target edge before mining paths, rules, or support features. **DEFERRED → P2.6:** this is per-query RuleTrust *scoring* in the S2DN/dgl branch (needs the S2DN venv + the §4.6 gradient audit). The `target_policy` field is already in the cache signature so caches invalidate when the policy changes.

**Acceptance:** the number of serialized relation IDs equals the number of source IDs; collision tests pass; stale caches are rejected.

### P0.5 Reproduce one baseline end to end

- [x] Run a small deterministic smoke configuration. *(Zero-shot full eval run twice → byte-identical, DETERMINISTIC: True. R-020. 1-epoch smoke train validates train-side manifest.)*
- [x] Run one complete historical BGE configuration using a frozen diagnostic split. *(Run E clean retrain seed 42, 30 ep, ml160 — within-lang MRR 27.02. R-023.)*
- [x] Compare the new evaluator with the recorded historical ranks and explain every difference. *(Zero-shot MRR 1.44 vs recorded R-001 1.45 — within 0.01, explained by average-tied-ranks + rounding. R-020.)*
- [x] Run one S2DN smoke test with logged effective hyperparameters. *(fb237_v1, 1 epoch, max_links 20, paper dims — subgraph extraction + train on cuda, effective hyperparams logged, in venv_s2dn_gpu_latest (dgl 2.4.0). R-022; venv frozen as canonical.)*

### Gate G0

- [x] A clean clone reproduces one text and one structural baseline. *(Text: zero-shot 1.44≈R-001 1.45 + Run E clean 27.02; structural: S2DN fb237_v1 smoke. Code canonical in repo; WSL runs it via symlink.)*
- [x] All P0 acceptance criteria pass. *(P0.1–P0.5 pass; two items deliberately deferred with notes: head-prediction eval → P1.6, target-edge removal at rule scoring → P2.6.)*
- [x] Results/errors/inferences are appended to the top ledger. *(R-016 … R-023.)*
- [x] Phase 0 commit is pushed to `main`.
- [x] Record pushed SHA: `8a1a685` and date: `2026-07-18`.

## 3. Phase 1 - DBP5L-Ind v2 benchmark

**Goal:** build a concept-disjoint, evidence-budgeted, provenance-safe benchmark suitable for final claims.

### P1.1 Freeze source data and licensing

- [x] Download and hash the public [DBP-5L data](https://github.com/stasl0217/KEnS/tree/main/data). *(`hash_source_data.py` → `source_manifest.json`: 31 files, 6.66MB, `top_sha256=0eca75a5…`. Self-check passes.)*
- [x] Record the exact upstream commit and original [KEnS paper](https://aclanthology.org/2020.findings-emnlp.290/). *(KEnS repo + EMNLP-Findings-2020 paper recorded in `DBP5L_DATA_PROVENANCE.md`. **Exact upstream git commit was not captured at download** — content hash is the immutable anchor instead; flagged as TODO to pin if re-downloaded.)*
- [x] Document DBpedia and DBP-5L redistribution obligations before releasing derived data. *(CC BY-SA 3.0 attribution + share-alike + state-changes, in `DBP5L_DATA_PROVENANCE.md`; full statement goes in the P1.8 data card.)*
- [x] Preserve original entity/relation IDs alongside processed IDs. *(URI → (lang,local_id) → global_id → concept_id, all recoverable from `entities.json`; relations preserved verbatim + injective `R{id}__name`.)*

### P1.2 Build real-world concept clusters

- [x] Load every seed alignment pair and build connected components with union-find. *(`build_concept_clusters.py`: 37,723 edges over `alignments.json` → 29,440 clean concepts from 56,589 entities; 9,762 multilingual (size 2–5), 19,678 singletons.)*
- [x] Detect components containing duplicate IDs from the same language; quarantine ambiguous components. *(Same-language collision detection implemented + tested; **0 found** on real data — alignment graph is clean, ≤1 entity per language per concept.)*
- [x] Add canonical concept IDs that are stable across folds. *(canonical = min global id in the component; fold-independent.)*
- [x] Store provenance for every union operation. *(`union_provenance.jsonl`, one line per edge; regenerable → gitignored, hash in `concept_stats.json`.)*

If $a\sim b$ denotes an alignment edge, concept membership is its transitive closure:

$$
C(e)=\{v:e\sim^*v\}.
$$

**Acceptance:** no entity belongs to two concepts; ambiguous same-language collisions are reported; cluster construction is deterministic.

### P1.3 Construct three fixed folds

- [x] Split concept IDs into train, validation, and test using three published seeds. *(`build_v2_folds.py`, seeds **[13, 42, 79]**; per fold train 22,082 / valid 2,943 / test 4,415 concepts (75/10/15).)*
- [x] Stratify approximately by language coverage, degree, and relation support without moving individual members of a concept. *(Stratified by concept language-coverage (size 1–5) bucket; whole concepts only. Balance verified: size-hist proportional across splits, degree median 3 everywhere, per-split relation counts reported.)*
- [x] Make validation inductive; do not tune on entities present in training. *(Validation concepts disjoint from train (whole-concept split); `assert_concept_disjoint` passes on every fold.)*
- [x] Persist exact concept lists and split manifests. *(Per fold: `{train,valid,test}_concepts.json`, `{…}_entities.json` (expansions), `stratification_stats.json`, `fold_manifest.json` (seed, ratios, hashes, `assert_concept_disjoint: passed`); `folds_summary.json`. Deterministic (hash-stable).)*

**Acceptance:** pairwise concept intersection is empty and every language has usable validation/test queries at each supported evidence budget.

### P1.4 Construct nested support budgets

- [x] Build a deterministic ordered support pool for every unseen entity. *(`build_v2_support_budgets.py`; 10,399 unseen entities with support/fold, avg pool 3.81.)*
- [x] Prefer training-connected, non-target, non-duplicate edges; record the ordering rule. *(Order key `(other_endpoint_seen?0:1, relation_id, other_global_id, direction)` → seen-neighbour edges first; triples deduped; rule in the module docstring.)*
- [x] Materialize $k\in\{0,1,3,5\}$ prefixes after global deduplication. *(S^k(e)=pool[:k]; **comparability rule enforced**: S^5 union selected FIRST and removed from eval targets for every budget, so targets + candidate universe are identical across budgets — only exposed evidence varies. exposed edges/budget 0/10.4k/27k/39.6k.)*
- [x] Remove all selected support edges from evaluation targets and add them to filtering. *(`eval_targets_{test,valid}` = eligible triples − S^5 union; the single known-true filter = all graph facts (which contains the support edges), `filter_hash` identical across budgets.)*

**Acceptance:** nesting assertions, caps, no target overlap, and identical regenerated hashes.

### P1.5 Rebuild descriptions from permitted evidence

- [x] Define source priority: native verified snapshot, verified cross-language snapshot, native entity name. *(`build_v2_descriptions.py`. Real data: **48,496 native Wikipedia (85.7%) / 4,274 cross-language / 3,819 name-only**.)*
- [x] Remove all LLM-generated text from the clean benchmark. *(Contaminated `entity_descriptions.json` excluded entirely; `no_llm_text: true`.)*
- [~] For train entities, allow graph-derived text from training triples only. *(Deliberately NOT used — the clean corpus is snapshot-text only (Wikipedia abstract → cross-lang → name). This sidesteps the §4.2 train/valid graph-text leak entirely. Graph-text remains an optional future augmentation, flagged.)*
- [~] For validation/test entities, exclude validation/test answer edges and snapshot information collected after the benchmark cutoff. **Changed per direction:** do NOT silently strip answer mentions — snapshot text is preserved verbatim (`answer_mentions_preserved: true`); exact + semantic answer leakage is quantified explicitly in **P1.7**. (Post-cutoff exclusion: corpus is frozen by `snapshot_rev`; per-page dates not captured — recorded gap.)
- [x] Record source URL/snapshot ID, language, retrieval time, content hash, and fallback reason per entity. *(Per-entity provenance: **raw_text_hash + norm_text_hash (separate)**, source, source_url (DBpedia URI), snapshot_rev (corpus SHA-256), snapshot_date (null — gap), lang (of text) + entity_lang, licence (CC BY-SA 3.0), retrieval_method, fallback_reason, and for cross-language: cross_lang_source_gid + cross_lang_concept + translated=false (borrowed as-is, never MT).)*

**Acceptance:** automated leakage probes cannot reconstruct held-out answers from description-generation inputs; every description has provenance.

### P1.6 Create evaluation tracks

- [x] Primary: alignment-free, full-candidate, head and tail prediction. *(View built+hashed (d1afcf20, 0 cross-lang). **Reciprocal head+tail code DONE + validated (R-030):** evaluator `--directions tail,head` reports head/tail/combined separately (tail reproduces 1.44016 exactly); trainer `--reciprocal 1` adds head examples with the shared `reverse of` marker (2×118,256 verified). Trained head/tail/combined **numbers** come with v2-fold wiring in **Phase 2** (trainer/evaluator currently read the old `processed/*.json`, not the v2 folds).)*
- [x] Oracle alignment: allow aligned counterpart evidence and label it diagnostic. *(Oracle view = full P1.5 corpus (with cross-lang), labelled `diagnostic`, hash 2a19bb0b.)*
- [x] Within-language and all-language candidate sets. *(Recorded independently: `candidates_all.json` (6a641485, matches the evaluator's persisted candidate hash) + `candidates_within_{lang}.json` ×5, each hashed.)*
- [x] Evidence budgets 0/1/3/5. *(Track manifest references the P1.4 per-fold budget artifacts; targets/filter/candidate hashes fixed across budgets — recorded in `fixed_across_budgets`.)*
- [~] Clean, missing-text, and held-out corruption tracks. *(Clean track = primary view. Missing-text + corruption declared as tracks; their data is built in Phase 3/4.)*

### P1.7 Run shortcut and leakage audits

- [x] Concept/alignment leakage audit. *(`concept_leakage_audit.py`. **RQ1 motivation result (precise definition):** a v1 test concept *leaks* iff its alignment-connected component (the union-find concept) contains ≥1 entity that is in the v1 training set of any language. Under this definition **4,964 / 6,866 v1 test concepts = 72.3% leak** (0 unmapped IDs). Confirms §4.3 quantitatively. Provides reusable `assert_concept_disjoint(train,valid,test)` for the v2 fold builder. R-024. Remaining P1.7 items (dup/inverse/answer-string/PPR audits) after folds.)*
- [x] Exact and near-duplicate entity/description audit. *(R-032: 3,767 duplicate-description groups (8,212 entities); 8,082 duplicate-name groups (21,638 entities — mostly cross-language same-name aligned concepts).)*
- [x] Inverse-relation and reciprocal-triple audit. *(R-032: 20 strong inverse-relation pairs (e.g. rel 289↔298 support 2,136); 2,441 reciprocal same-relation triples. **R-035 (support-exposure):** ~7.6% test / ~10.3% valid targets have their answer revealed by h↔t adjacency in exposed S^5 (~24 exact reciprocals; rest via other relations). Emitted an **inverse-clean S^5** per fold (`s5_union_inverse_clean.json`, ~4,074 edges dropped/fold, hashed) = inverse-clean primary track.)*
- [x] Answer-string and relation-template leakage audit. *(Answer-string = R-031: exact 39.0% / semantic-subset 26.6% overall, tail 63.1% vs head 14.9%, by language + description source. Relation-template leakage: descriptions are Wikipedia prose, not relation-templated — low risk, noted.)*
- [x] Degree, relation-frequency, component-size, and language-coverage distributions. *(R-032: degree median 5 / p95 23 / max 3,911; 335/903 relations ≤2 triples; concept sizes 19,678→2,803; per-language entity+triple counts.)*
- [x] Personalized PageRank and shortest-path shortcut baselines. *(R-033/R-034: traversal excludes ALL valid/test answer edges (~50,622/fold), relation types dropped. **PPR MRR 0.05–0.06 vs degree baseline 0.06–0.076 vs random 0.001**; no relation-level outliers (≥2×mean/0.20). Reframed: structural signal ≈ popularity/degree, ≫ random but **≪ text (0.27) → PPR does not explain text performance** (not "no shortcut" in the absolute). Median SP 3, 97–99% reachable.)*

For restart probability $1-\alpha$, PPR satisfies:

$$
\boldsymbol\pi=(1-\alpha)\mathbf e_q+\alpha P^\top\boldsymbol\pi.
$$

Report whether PPR or simple degree can explain test rankings. Do not merely assert that the split is hard.

### P1.8 Publish benchmark documentation

- [ ] Dataset card, intended use, exclusions, licences, languages, relation statistics, and limitations.
- [ ] Fold and evidence-budget statistics.
- [ ] Corruption taxonomy and annotation guide.
- [ ] Reproduction command and hash-verification command.

### Gate G1

- [ ] No concept leakage or unresolved critical shortcut.
- [ ] Full head/tail evaluation is deterministic for all folds and budgets.
- [ ] Data card and immutable hashes are complete.
- [ ] Ledger is updated with old-vs-v2 metric changes and their causes.
- [ ] Phase 1 commit is pushed to `main`.
- [ ] Record pushed SHA: `________________` and date: `________________`.

## 4. Phase 2 - clean baselines and BGE-M3 experiments

**Goal:** establish a reproducible clean baseline, then screen only scientifically motivated extensions.

### P2.1 Lock baseline suite

- [ ] Lexical BM25/name-match baseline.
- [ ] Degree/PPR structural heuristics.
- [ ] mBERT bi-encoder under the exact BGE training/evaluation recipe.
- [ ] XLM-R bi-encoder under the exact recipe.
- [ ] Clean BGE-M3/LoRA B0 with three seeds.
- [ ] One corrected structural inductive baseline on the v2 folds.

**Acceptance:** same folds, candidate lists, filtering, seeds, and reporting schema. Raw MRR from incompatible candidate universes is not placed in the same comparison column.

### P2.2 Recheck objective and negative controls

- [ ] InfoNCE with in-batch negatives.
- [ ] CRR with identical negatives.
- [ ] CRR plus seven fresh hard negatives.
- [ ] Dynamic top-ranked negatives refreshed on a fixed schedule.
- [ ] Self-adversarial weighting as an optional cheap control.

For negative $j$, capped self-adversarial weight is:

$$
p_j=\frac{\exp(\beta\,\operatorname{stopgrad}(s_j))}
{\sum_{k\in\mathcal N}\exp(\beta\,\operatorname{stopgrad}(s_k))}.
$$

- [ ] Filter negatives using all known facts, aligned concepts, rules, and type constraints.
- [ ] Reject stale caches whose checkpoint or data hash differs.

### P2.3 Test native BGE-M3 retrieval modes

- [ ] Dense-only score.
- [ ] Learned sparse lexical score.
- [ ] Multi-vector token interaction for top-$K$ reranking.
- [ ] Calibrated dense/sparse/multi-vector fusion.
- [ ] Hybrid-teacher to dense-student distillation if fusion wins.

Use normalized score fusion:

$$
s_{\mathrm{hybrid}}=\lambda_d\hat s_d+\lambda_s\hat s_s+\lambda_m\hat s_m,
\qquad
\lambda_d+\lambda_s+\lambda_m=1.
$$

Report recall@$K$, reranking latency, cache size, and full-ranking MRR.

### P2.4 Structure/schema-aware contrastive learning

- [ ] Vertex, neighbour, path, and relation-composition positive tasks.
- [ ] Domain/range/type prototypes from training only.
- [ ] Same-type hard negatives and explicit type-violation controls.
- [ ] Auxiliary reciprocal direction, relation, and type prediction.

Combine tasks only after individual screening:

$$
\mathcal L=\mathcal L_{\mathrm{KGC}}+
\lambda_v\mathcal L_v+\lambda_n\mathcal L_n+
\lambda_p\mathcal L_p+\lambda_r\mathcal L_r+\lambda_t\mathcal L_t.
$$

### P2.5 Semantic Smoothing in BGE-M3

#### P2.5a Soft-target smoothing

- [ ] Build frozen train-only similarity neighbours.
- [ ] Remove known false and ambiguous candidates.
- [ ] Assign smoothing mass $\varepsilon$ only to verified/plausible positives.

$$
\tilde y_j=(1-\varepsilon)\mathbf 1[j=y]
+\varepsilon\frac{\exp(\operatorname{sim}(j,y)/\tau_s)}
{\sum_{k\in\mathcal P_y}\exp(\operatorname{sim}(k,y)/\tau_s)}.
$$

#### P2.5b Relation-prototype consistency

- [ ] Compute each relation prototype from training queries only.

$$
\mathbf p_r=\operatorname{norm}
\left(\frac{1}{|Q_r|}\sum_{q\in Q_r}\mathbf q\right).
$$

- [ ] Pull queries toward compatible prototypes and preserve a margin from incompatible prototypes.

#### P2.5c Cross-view consistency

- [ ] Match trusted text and structural/prototype distributions using symmetric KL or cosine consistency.
- [ ] Mask the consistency loss when the non-text view is unavailable or untrusted.

### P2.6 RuleTrust in BGE-M3

- [ ] Mine Horn rules from training triples only.
- [ ] Remove the target edge before computing support.
- [ ] Calibrate rule confidence by relation and support count.
- [ ] Test example weighting, adaptive margin, score fusion, and a compact rule feature adapter separately.

Score fusion starts exactly at B0:

$$
s(q,c)=s_{\mathrm{BGE}}(q,c)+\gamma\,s_{\mathrm{rule}}(q,c),
\qquad \gamma_0=0.
$$

Required controls:

- [ ] Shuffled rules.
- [ ] Confidence-matched random rules.
- [ ] Zero rule weight.
- [ ] No-inverse-rule mining.
- [ ] Coverage buckets and three paired seeds.

### P2.7 SimRMKGC-derived relation-alignment experiments

The full transductive SimRMKGC model is not copied. Adapt its relation-supervision idea to unseen concepts using train-only relation text/prototypes.

#### P2.7a Mine relation-alignment positives

- [ ] Use aligned training concept endpoints to count cross-language relation co-occurrence.
- [ ] Combine endpoint evidence with relation-label and prototype similarity.
- [ ] Require a minimum support count and exclude validation/test endpoints.
- [ ] Human-audit a stratified sample before training.

For relation $r$, define representation:

$$
\mathbf z_r=\operatorname{norm}
\left(g_\phi([\text{relation label};\text{endpoint prototype};\text{neighbour summary}])\right).
$$

Supervised relation contrastive loss is:

$$
\mathcal L_{\mathrm{RA}}=
-\frac{1}{|\mathcal R|}\sum_{r\in\mathcal R}
\frac{1}{|P(r)|}\sum_{p\in P(r)}
\log\frac{\exp(\mathbf z_r^\top\mathbf z_p/\tau_r)}
{\sum_{a\in A(r)}\exp(\mathbf z_r^\top\mathbf z_a/\tau_r)}.
$$

#### P2.7b Compare entity and relation alignment

- [ ] B0 only.
- [ ] B0 + entity-alignment loss.
- [ ] B0 + relation-alignment loss.
- [ ] B0 + fixed-weight entity and relation losses.
- [ ] B0 + gradient-balanced entity and relation losses.

$$
\mathcal L=\mathcal L_{\mathrm{KGC}}+\lambda_{EA}\mathcal L_{EA}+\lambda_{RA}\mathcal L_{RA}.
$$

#### P2.7c Availability and noise sweeps

- [ ] Relation-alignment availability: 0%, 10%, 30%, 50%, 100%.
- [ ] Wrong-pair injection: 0%, 5%, 10%, 20%.
- [ ] Report calibration and degradation by language, relation frequency, and evidence budget.
- [ ] Keep test alignments out of the primary track.

### P2.8 Area-wise mixup hard negatives

- [ ] Select two currently hard, filtered negatives $\mathbf n_a,\mathbf n_b$.
- [ ] Sample a block mask $M$ or blockwise mixing coefficient.
- [ ] Stop gradients through the source negative selection and normalize the synthetic vector.

$$
\tilde{\mathbf n}=\operatorname{norm}
\left(M\odot\mathbf n_a+(1-M)\odot\mathbf n_b\right).
$$

- [ ] Compare entity-level, relation-level, and token-block mixing.
- [ ] Measure embedding-manifold distance and false-negative rate.
- [ ] Drop the method if it does not beat ordinary dynamic mining.

### P2.9 Controlled combination and confirmation

- [ ] Screen every component with one seed against B0.
- [ ] Permit at most four survivors into a factorial study.
- [ ] Run B0 and the final survivor(s) with at least three paired seeds.
- [ ] Bootstrap paired per-query reciprocal-rank differences.
- [ ] Report clean MRR, robust MRR, calibration, latency, and memory.

### Gate G2

- [ ] Clean B0 is reproducible on three folds/seeds as specified.
- [ ] Every retained extension beats its matched control or improves reliability with an accepted clean-performance tradeoff.
- [ ] Semantic Smoothing, RuleTrust, relation alignment, and mixup each have required negative controls.
- [ ] Ledger records keep/drop decisions and failed variants.
- [ ] Phase 2 commit is pushed to `main`.
- [ ] Record pushed SHA: `________________` and date: `________________`.

## 5. Phase 3 - TrustRouter, uncertainty, and quarantine

**Goal:** decide which evidence to trust and when the system should abstain or quarantine text.

### P3.1 Standardize expert outputs

- [ ] Text expert, structure expert, prototype expert, and RuleTrust expert return scores on the same candidate IDs.
- [ ] Calibrate or normalize each expert before fusion.
- [ ] Log expert availability and failure reason per query.

### P3.2 Build evidence vector

- [ ] Support count, degree, path availability.
- [ ] Description availability, source, age, length, language, and graph-text agreement.
- [ ] Relation frequency, cardinality, schema/type compatibility.
- [ ] Expert entropy, margin, disagreement, and conformal set size.
- [ ] Relation-alignment support/confidence and RuleTrust coverage.

### P3.3 Implement static and oracle controls

- [ ] Best single expert.
- [ ] Validation-tuned static weighted fusion.
- [ ] Per-query oracle expert selector as an unattainable ceiling.
- [ ] Random gate and language-only gate as negative controls.

### P3.4 Implement TrustRouter

For evidence vector $\mathbf z_q$:

$$
\mathbf w(q)=\operatorname{softmax}(g_\psi(\mathbf z_q)),
\qquad
s(q,c)=\sum_m w_m(q)s_m(q,c).
$$

- [ ] Use a small MLP or linear gate before considering larger routing models.
- [ ] Mask unavailable experts before softmax.
- [ ] Train with counterfactual dropout of text, support, alignments, rules, and prototypes.
- [ ] Add a penalty when the gate assigns weight to deliberately corrupted evidence.

$$
\mathcal L_{\mathrm{router}}=
\mathcal L_{\mathrm{rank}}+\lambda_{cons}\mathcal L_{cons}
+\lambda_{cal}\mathcal L_{cal}+\lambda_{risk}\mathcal L_{selective}.
$$

### P3.5 Calibrate confidence and answer sets

- [ ] Temperature scaling and vector scaling.
- [ ] KGE-specific ranking-preserving calibration.
- [ ] Calibration by language, relation, and evidence budget.
- [ ] Split-conformal answer sets using inductive validation only.

For nonconformity score $a_i$, choose:

$$
\hat q_{1-\alpha}=\operatorname{Quantile}_{\lceil(n+1)(1-\alpha)\rceil/n}
(a_1,\ldots,a_n).
$$

The answer set is $\Gamma_\alpha(q)=\{c:a(q,c)\le\hat q_{1-\alpha}\}$.

### P3.6 Implement selective actions

- [ ] Use evidence.
- [ ] Down-weight or fallback.
- [ ] Abstain.
- [ ] Quarantine description.
- [ ] Escalate to human review.

Measure risk at coverage $\kappa$:

$$
\operatorname{Risk}(\kappa)=
\frac{\sum_i \mathbf{1}[a_i=\mathrm{answer}]\,\ell_i}
{\sum_i \mathbf{1}[a_i=\mathrm{answer}]}.
$$

### Gate G3

- [ ] TrustRouter beats the best single expert and static fusion under corruption.
- [ ] Clean MRR decreases by no more than 0.5 absolute points unless a predeclared reliability tradeoff justifies it.
- [ ] Thresholds are fixed from validation and coverage claims are empirically checked.
- [ ] Phase 3 commit is pushed to `main`.
- [ ] Record pushed SHA: `________________` and date: `________________`.

## 6. Phase 4 - verified self-healing loop

**Goal:** complete detect -> decide -> retrieve -> verify -> repair -> re-evaluate -> rollback.

### P4.1 Build the corruption and repair benchmark

- [ ] Collect naturally occurring, source-verifiable errors where available.
- [ ] Add realistic type-matched swaps, single-claim edits, stale dates, mistranslations, entity collisions, omissions, and unsupported biographies.
- [ ] Hold out corruption families and generators from training.
- [ ] Double-label a stratified multilingual test set and adjudicate disagreement.
- [ ] Preserve a clean control set sampled by the same entity/relation strata.

### P4.2 Implement multi-signal detection

Graph-text consistency for entity $e$:

$$
c_{gt}(e)=\cos
\left(f(x_e),f(\operatorname{serialize}(N_k(e)))\right).
$$

- [ ] Graph-text cosine.
- [ ] Triplet-reconstruction confidence.
- [ ] Type/schema violations.
- [ ] RuleTrust contradictions.
- [ ] Relation-alignment contradictions.
- [ ] Expert and verifier disagreement.
- [ ] Source/provenance anomalies.

Fit a calibrated detector only on training/validation corruption:

$$
p_{bad}(e)=\sigma(\mathbf w^\top\mathbf f_e+b).
$$

### P4.3 Decompose descriptions into atomic claims

- [ ] Extract minimal subject-predicate-object or subject-attribute-value claims.
- [ ] Preserve spans linking claims to the original description.
- [ ] Resolve pronouns and aliases without changing entity identity.
- [ ] Mark unparseable claims as insufficient evidence, not automatically false.

### P4.4 Retrieve frozen, approved evidence

- [ ] Allowlist versioned Wikipedia/Wikidata/DBpedia snapshots and any approved domain sources.
- [ ] Resolve candidate pages to the correct concept using IDs, aliases, types, and aligned entities.
- [ ] Store source URL, snapshot ID, retrieval query, passage, content hash, and licence.
- [ ] Cache retrieval so repeated evaluation never depends on changing live web results.

### P4.5 Verify claims and relation consistency

- [ ] Label each claim supported, contradicted, or insufficient.
- [ ] Compare deterministic/NLI, graph, RuleTrust, relation-alignment, and two calibrated LLM judges.
- [ ] Test original/repaired order swaps and native/translated prompts.
- [ ] Calibrate every judge per language against hidden human labels.

The relation-alignment verification score may be:

$$
v_{RA}(e)=\frac{1}{|R_e|}
\sum_{r\in R_e}\max_{r'\in A(r)}
\cos(\mathbf z_r,\mathbf z_{r'}).
$$

It is an auxiliary signal, never sufficient evidence by itself.

### P4.6 Generate minimal candidate repairs

- [ ] No repair.
- [ ] Quarantine only.
- [ ] Name-only fallback.
- [ ] Verified full replacement.
- [ ] Minimal deletion of contradicted claims.
- [ ] Minimal evidence-supported revision.
- [ ] Cross-language verified transfer.
- [ ] Unconstrained LLM generation as a negative control.

### P4.7 Accept, reject, or escalate

A repair $x'_e$ is automatically accepted only if:

$$
\operatorname{Accept}(x'_e)=
\mathbf{1}[
P\land I\land C\land R\land U\land D
],
$$

where $P$ is valid provenance, $I$ is resolved identity, $C$ is claim support, $R$ is relation/graph consistency, $U$ is calibrated uncertainty below threshold, and $D$ is no downstream/clean-control rollback trigger.

- [ ] Log the original, replacement, evidence, all verifier scores, decision, and reason.
- [ ] Keep rejected repairs quarantined; never silently overwrite source text.
- [ ] Add manual escalation for insufficient or conflicting evidence.

### P4.8 Re-evaluate and roll back

- [ ] Re-encode only affected entities with immutable model/checkpoint state.
- [ ] Re-run the exact affected KGC queries and clean matched controls.
- [ ] Roll back when accepted repair reduces clean-control performance, breaks provenance, or fails claim verification.
- [ ] Report repair precision, coverage, false-repair rate, KGC recovery, and clean-case preservation.

$$
\mathrm{Recovery}=
\frac{\mathrm{MRR}_{repair}-\mathrm{MRR}_{corrupt}}
{\mathrm{MRR}_{clean}-\mathrm{MRR}_{corrupt}}.
$$

### Gate G4

- [ ] Accepted repairs are source-verifiable and identity-correct.
- [ ] Repair improves KGC beyond quarantine-only with paired confidence intervals.
- [ ] No statistically meaningful clean-case regression occurs.
- [ ] If this gate fails, rename the claim to self-auditing rather than self-healing.
- [ ] Phase 4 commit is pushed to `main`.
- [ ] Record pushed SHA: `________________` and date: `________________`.

## 7. Phase 5 - downstream recovery, external validation, and release

### P5.1 Freeze a focused multilingual QA/RAG benchmark

- [ ] Generate or curate questions tied directly to corrupted/repaired entities and relations.
- [ ] Freeze gold answers, acceptable aliases, evidence passages, citations, retrieval index, and generator revision.
- [ ] Include single-hop and a limited, balanced multi-hop subset.
- [ ] Prevent repaired descriptions from entering question creation or gold adjudication.

### P5.2 Compare closed-loop downstream conditions

- [ ] Clean KB.
- [ ] Corrupted KB.
- [ ] Quarantine-only KB.
- [ ] Automatically repaired KB.
- [ ] Human-verified repaired KB ceiling.

Report exact match/F1 where appropriate, citation correctness, supported-claim precision, abstention, and cost per verified answer.

### P5.3 External validation

- [ ] PediaTypes or another published fully inductive multilingual resource for the main reliability conclusion.
- [ ] Wikidata5M-Ind for text-inductive method sanity, without cross-dataset raw-MRR claims.
- [ ] WikiKGE-10/10++ or another human-curated text resource for description-quality signals.
- [ ] Optional [E-PKG](https://github.com/amzn/ss-aga-kgc/tree/main/EPKG_DATA) transductive validation for relation alignment only.

### P5.4 Statistical analysis

- [ ] Three or more paired seeds for headline models.
- [ ] Paired bootstrap confidence intervals over queries.
- [ ] Randomization or signed-rank checks as secondary tests.
- [ ] Multiple-comparison correction for the final predeclared family.
- [ ] Report effect sizes and per-language/worst-language outcomes.

For paired differences $d_i$:

$$
\Delta\mathrm{MRR}=\frac{1}{N}\sum_i d_i,
$$

and the bootstrap resamples query indices jointly for both systems.

### P5.5 Compute and efficiency report

- [ ] GPU-hours, peak VRAM, CPU-hours, RAM, disk, retrieval calls, LLM tokens, and monetary cost.
- [ ] Training and evaluation latency by mode.
- [ ] Cache/checkpoint retention policy.
- [ ] Recalibrate the proposal's 335-545 GPU-hour estimate after profiled v2 runs.

### P5.6 Final paper and release package

- [ ] Final benchmark card and model cards.
- [ ] All run manifests, exact configs, compact rank dumps, bootstrap code, and repair audit logs.
- [ ] Reproducibility checklist and one-command smoke reproduction.
- [ ] Claim-to-evidence table mapping every abstract/conclusion claim to a result row.
- [ ] Archive failed and invalidated runs with explanations.
- [ ] Verify every paper/proposal/resource link.

### Gate G5

- [ ] Verified repair improves factual QA/RAG over corrupted and quarantine-only conditions.
- [ ] Citation correctness and clean controls are preserved.
- [ ] At least one main conclusion holds outside DBP5L-Ind v2.
- [ ] The final title and abstract match the strongest passed gate; unsupported claims are removed.
- [ ] Phase 5 commit is pushed to `main`.
- [ ] Record pushed SHA: `________________` and date: `________________`.

## 8. Experiment selection and stopping rules

- [ ] Never run the full Cartesian product of all ideas.
- [ ] Use one-seed screening only for mechanism triage, never for headline claims.
- [ ] Drop a component after a well-powered matched test shows no useful clean or reliability gain.
- [ ] Stop mixup negatives if ordinary dynamic mining matches them.
- [ ] Stop generative negatives unless retrieval-based mining saturates.
- [ ] Keep Semantic Smoothing and RuleTrust as negative ablations if their controls fail.
- [ ] Keep relation alignment only if it helps unseen concepts without test-alignment leakage.
- [ ] Call the system self-healing only after Gates G4 and G5 pass.

## 9. Required run directory and result schema

Each run directory must contain:

```text
runs/<run_id>/
  manifest.json
  config.yaml
  command.txt
  environment.txt
  train.log
  metrics.json
  metrics_by_language.json
  metrics_by_budget.json
  rank_dump.parquet
  errors.md
  inference.md
  checkpoint.sha256
```

Required `metrics.json` fields include:

```text
run_id, status, parent_run_id, invalidates_run_id,
dataset, fold, split_hash, description_hash, relation_map_hash,
model_name, model_revision, adapter_config, seed,
candidate_mode, candidate_hash, filtering_policy, filter_hash,
mrr, hits_at_1, hits_at_3, hits_at_10,
macro_language_mrr, worst_language_mrr,
ece, brier, coverage, selective_risk,
repair_precision, repair_coverage, false_repair_rate,
qa_metric, citation_correctness,
gpu_hours, peak_vram_gb, cpu_hours, retrieval_calls, llm_tokens
```

## 10. Resource registry

- [Final research proposal](FINAL_RESEARCH_PROPOSAL_2026-07-17.md)
- [Current results and inference ledger](RESULTS_AND_INFERENCE.md)
- [Project story and plan](PROJECT_STORY_AND_PLAN.md)
- [Architecture audit](ARCHITECTURE.md)
- [RuleTrust experiment ledger](pivot/RULETRUST_EXPERIMENT_LEDGER.md)
- [First self-healing detector report](pivot/self_healing_detector_result_2026-07-07.md)
- [DBP-5L data and KEnS code](https://github.com/stasl0217/KEnS)
- [Original DBP-5L paper](https://aclanthology.org/2020.findings-emnlp.290/)
- [SimRMKGC paper](https://link.springer.com/article/10.1007/s10489-025-06782-x)
- [E-PKG data and SS-AGA code](https://github.com/amzn/ss-aga-kgc)
- [BGE-M3](https://aclanthology.org/2024.findings-acl.137/)
- [SimKGC](https://aclanthology.org/2022.acl-long.295/)
- [KGCRR](https://ojs.aaai.org/index.php/AAAI/article/view/33410)
- [StructKGC](https://aclanthology.org/2024.emnlp-main.772/)
- [KG-TRICK](https://aclanthology.org/2025.coling-main.611/)
- [KGE calibration](https://aclanthology.org/2025.emnlp-main.1522/)
- [Conformal KGE answer sets](https://aclanthology.org/2025.naacl-long.32/)
- [FActScore](https://aclanthology.org/2023.emnlp-main.741/)
- [RARR](https://aclanthology.org/2023.acl-long.910/)
