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

- [ ] Generate a unique run ID before training.
- [ ] Persist `git_commit`, dirty-tree flag, exact command, UTC start/end time, hostname/GPU, random seeds, model revision, tokenizer revision, split hash, description hash, relation-map hash, candidate-set hash, filter hash, and checkpoint hash.
- [ ] Write results atomically to a new run directory; refuse to overwrite an existing result.
- [ ] Add `status = running|complete|failed|invalidated` and `invalidates_run_id` fields.

Use SHA-256 for an artifact $a$:

$$
h(a)=\operatorname{SHA256}(\operatorname{bytes}(a)).
$$

**Acceptance:** changing one byte of a split, description, relation map, or candidate list changes the manifest and prevents accidental comparison.

**Artifacts:** JSON schema, sample manifest, validator tests.

### P0.3 Lock deterministic evaluation

- [ ] Pass `max_length` from checkpoint/config rather than hardcoding it.
- [ ] Persist candidate IDs and their order; do not reconstruct candidates from unordered containers.
- [ ] Add train, validation, test, and support triples to the filtered-known-fact map.
- [ ] Verify reciprocal head and tail query templates separately.
- [ ] Average tied ranks and test with a constructed equal-score case.
- [ ] Assert identical metrics across two consecutive evaluations of the same checkpoint.

For query $(h,r,?)$, the filtered candidate set is:

$$
\mathcal C_f(q)=\mathcal C(q)\setminus
\{t'\ne t:(h,r,t')\in E_{\mathrm{known}}\}.
$$

**Acceptance:** deterministic metrics and passing unit cases for filtering, support facts, ties, head prediction, and tail prediction.

### P0.4 Repair relation identity and caches

- [ ] Preserve relation IDs with an injective serialization such as `R{id}__sanitized_name`.
- [ ] Detect and report relation-name collisions instead of merging them.
- [ ] Include dataset/fold/relation-map/target-edge policy in rule-cache keys.
- [ ] Remove the target edge before mining paths, rules, or support features.

**Acceptance:** the number of serialized relation IDs equals the number of source IDs; collision tests pass; stale caches are rejected.

### P0.5 Reproduce one baseline end to end

- [ ] Run a small deterministic smoke configuration.
- [ ] Run one complete historical BGE configuration using a frozen diagnostic split.
- [ ] Compare the new evaluator with the recorded historical ranks and explain every difference.
- [ ] Run one S2DN smoke test with logged effective hyperparameters.

### Gate G0

- [ ] A clean clone reproduces one text and one structural baseline.
- [ ] All P0 acceptance criteria pass.
- [ ] Results/errors/inferences are appended to the top ledger.
- [ ] Phase 0 commit is pushed to `main`.
- [ ] Record pushed SHA: `________________` and date: `________________`.

## 3. Phase 1 - DBP5L-Ind v2 benchmark

**Goal:** build a concept-disjoint, evidence-budgeted, provenance-safe benchmark suitable for final claims.

### P1.1 Freeze source data and licensing

- [ ] Download and hash the public [DBP-5L data](https://github.com/stasl0217/KEnS/tree/main/data).
- [ ] Record the exact upstream commit and original [KEnS paper](https://aclanthology.org/2020.findings-emnlp.290/).
- [ ] Document DBpedia and DBP-5L redistribution obligations before releasing derived data.
- [ ] Preserve original entity/relation IDs alongside processed IDs.

### P1.2 Build real-world concept clusters

- [ ] Load every seed alignment pair and build connected components with union-find.
- [ ] Detect components containing duplicate IDs from the same language; quarantine ambiguous components.
- [ ] Add canonical concept IDs that are stable across folds.
- [ ] Store provenance for every union operation.

If $a\sim b$ denotes an alignment edge, concept membership is its transitive closure:

$$
C(e)=\{v:e\sim^*v\}.
$$

**Acceptance:** no entity belongs to two concepts; ambiguous same-language collisions are reported; cluster construction is deterministic.

### P1.3 Construct three fixed folds

- [ ] Split concept IDs into train, validation, and test using three published seeds.
- [ ] Stratify approximately by language coverage, degree, and relation support without moving individual members of a concept.
- [ ] Make validation inductive; do not tune on entities present in training.
- [ ] Persist exact concept lists and split manifests.

**Acceptance:** pairwise concept intersection is empty and every language has usable validation/test queries at each supported evidence budget.

### P1.4 Construct nested support budgets

- [ ] Build a deterministic ordered support pool for every unseen entity.
- [ ] Prefer training-connected, non-target, non-duplicate edges; record the ordering rule.
- [ ] Materialize $k\in\{0,1,3,5\}$ prefixes after global deduplication.
- [ ] Remove all selected support edges from evaluation targets and add them to filtering.

**Acceptance:** nesting assertions, caps, no target overlap, and identical regenerated hashes.

### P1.5 Rebuild descriptions from permitted evidence

- [ ] Define source priority: native verified snapshot, verified cross-language snapshot, native entity name.
- [ ] Remove all LLM-generated text from the clean benchmark.
- [ ] For train entities, allow graph-derived text from training triples only.
- [ ] For validation/test entities, exclude validation/test answer edges and snapshot information collected after the benchmark cutoff.
- [ ] Record source URL/snapshot ID, language, retrieval time, content hash, and fallback reason per entity.

**Acceptance:** automated leakage probes cannot reconstruct held-out answers from description-generation inputs; every description has provenance.

### P1.6 Create evaluation tracks

- [ ] Primary: alignment-free, full-candidate, head and tail prediction.
- [ ] Oracle alignment: allow aligned counterpart evidence and label it diagnostic.
- [ ] Within-language and all-language candidate sets.
- [ ] Evidence budgets 0/1/3/5.
- [ ] Clean, missing-text, and held-out corruption tracks.

### P1.7 Run shortcut and leakage audits

- [ ] Concept/alignment leakage audit.
- [ ] Exact and near-duplicate entity/description audit.
- [ ] Inverse-relation and reciprocal-triple audit.
- [ ] Answer-string and relation-template leakage audit.
- [ ] Degree, relation-frequency, component-size, and language-coverage distributions.
- [ ] Personalized PageRank and shortest-path shortcut baselines.

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
