# Final Research Proposal: TrustMKGC

**Working title:** *TrustMKGC: Reliability-Aware Multilingual Entity-Inductive Knowledge Graph Completion under Missing and Corrupted Evidence*

**Date:** 17 July 2026

**Status:** proposed replacement for the current three-product execution ladder
**Audit scope:** the committed Windows snapshot, the live WSL training tree, `origin/main` at commit `1d7e0e3`, experiment logs, preprocessing/evaluation code, and primary research literature through 17 July 2026.

## 1. Decision

The research direction is worth continuing, but the current plan is **not yet a safe final paper plan**.

- As a research programme, it is strong: it has a useful multilingual substrate, substantial implementation work, careful failure logs, negative controls, and an interesting observation about unreliable generated descriptions.
- As one submission, it is too broad: it combines an S2DN reproduction study, a RuleTrust methods paper, a multilingual benchmark paper, a contamination detector, a repair system, and downstream QA/RAG evaluation.
- Several current headline claims are not publication-ready because of split leakage, incompatible evaluation protocols, unclean training descriptions, mutable result provenance, and missing code in the GitHub snapshot.

My recommendation is to make **one benchmark-first primary paper** and treat end-to-end self-healing as a later paper:

1. **Primary paper:** DBP5L-Ind v2 plus a reliability-aware, evidence-budgeted KGC method.
2. **Follow-up paper:** verified detection, repair, and downstream evaluation of naturally occurring or realistically annotated multilingual KB contamination.
3. **RuleTrust:** a conditional feature/ablation only. It must not block the benchmark or primary paper.

In short: **keep the problem, rebuild the scientific foundation, narrow the novelty claim, and change the execution order.**

## 2. What the current plan proposes

The current plan of record is [`pivot/UNIFIED_PATHWAY.md`](pivot/UNIFIED_PATHWAY.md). It contains three proposed products:

- **P1 — DBP-5L-Ind:** an entity-disjoint multilingual inductive KGC benchmark with a BGE-M3 text baseline.
- **P2 — self-healing multilingual KBs:** detect fabricated entity descriptions from text–structure disagreement, quarantine or repair them, and measure downstream effects.
- **P3 — RuleTrust-S2DN:** add mined Horn-rule evidence to S2DN if paired experiments establish a genuine gain.

The planned ladder is S2DN reproduction → English neuro-symbolic modification → multilingual conversion → self-healing → paper packaging. The plan itself acknowledges that this full ladder is not finishable as one realistic submission unit, and it contains an ordering contradiction: one section says to close RuleTrust seeds first, while the later status section defers seeds until the end.

## 3. What is already good

The project has several valuable assets that should be preserved:

1. **A useful multilingual data and evaluation substrate.** The existing DBP-5L pipeline already supports five languages, full-candidate text retrieval, per-language reporting, and three BGE-M3 seeds.
2. **Strong empirical discipline in the documentation.** Failed runs, evaluation bugs, negative controls, and interpretation changes are recorded rather than hidden.
3. **A real reliability signal.** Replacing questionable Japanese/Greek description backfills with cleaner or name-only text improved Japanese MRR by 1.95 points in one evaluation-time ablation. This is not yet causal evidence, but it is a worthwhile hypothesis.
4. **Reusable baselines.** The BGE-M3, mBERT, S2DN, RuleTrust, rule-mining, and conversion work can be reused after protocol fixes.
5. **Adequate hardware.** The local RTX 5070 Ti is sufficient for the text branch, and the incoming 96 GB GPU removes most capacity constraints for structural experiments.

## 4. Blocking findings from the repository and WSL audit

These issues should be resolved before more headline experiments are run.

### 4.1 The 26.51 MRR result is provisional, not the clean headline

The three BGE-M3 runs reported as 26.51 ± 0.31 within-language MRR used the default `entity_descriptions.json`. That file contains 1,042 Llama-3.2-generated descriptions plus other English fallbacks. The clean description file was created after those runs, and no three-seed clean BGE retrain exists. The repository itself notes that the mBERT-clean versus BGE-old comparison is not apples-to-apples in [`RESULTS_AND_INFERENCE.md`](RESULTS_AND_INFERENCE.md#table-2d-external--encoder-baseline-mbert-clean-descriptions).

The clean BGE-M3 three-seed result therefore has to be rerun before it can be used in an abstract or main table.

### 4.2 Validation information leaks into entity descriptions

[`build_entity_descriptions.py`](../wsl/research_kg/scripts/data_prep/build_entity_descriptions.py) constructs structural text from both training and validation triples. Those descriptions are then available during training while the same validation set is used for checkpoint selection. Entity descriptions must be rebuilt from **training evidence only**.

### 4.3 The split is identifier-disjoint, not concept-disjoint

[`build_dbp5l_ind.py`](../wsl/research_kg/scripts/data_prep/build_dbp5l_ind.py) samples held-out entities independently in each language and then copies cross-language alignment links unchanged. An entity can be unseen in Japanese while its aligned English representation is present in training. For a multilingual inductive claim, aligned IDs must first be grouped into real-world concept clusters and split together.

### 4.4 The existing text model does not consume the support graph

The splitter produces `support.txt`, but the BGE trainer/evaluator does not use it. The implemented task is currently:

> head description + relation → tail description

That is a valid text-based entity-disjoint KGC task, but it is not support-subgraph reasoning. The final benchmark must either expose explicit zero/few-edge tracks and build models that consume the support edges, or describe the text-only task precisely.

### 4.5 The benchmark construction needs redesign

The existing split has one random seed, selects unseen entities only from entities with sufficient degree, pools the original train/validation/test triples, uses a transductive validation split, and mixes seen→unseen, unseen→seen, and unseen→unseen queries. It reports only tail prediction. It also mixes two populations in the documentation: 44,807 entities incident to graph triples versus 56,589 ranked candidates.

Recent work shows that common random inductive splits can expose a Personalized PageRank shortcut; PPR can approach state-of-the-art neural performance without using relation types. A publishable new benchmark must explicitly audit and suppress this shortcut ([Shomer, Revolinsky, and Tang, KDD 2025](https://arxiv.org/abs/2406.11898)).

### 4.6 S2DN and RuleTrust results are not controlled yet

The committed S2DN evaluator samples fresh random negatives on each run and has no evaluation-seed option. S2DN also retains stochastic Gumbel/Relaxed-Bernoulli sampling during evaluation. Thus training seeds are not paired with identical evaluation candidates, and current metric swings cannot be assigned safely to RuleTrust.

There is a second implementation risk: the Structure Refining path detaches learned adjacency and node features while rebuilding the graph, which appears to cut the gradient to the graph learner. This requires a parameter-gradient/update audit before S2DN becomes a methods foundation.

The current RuleTrust result—MRR 0.53134 → 0.53191 and Hits@10 0.67805 → 0.71220 on one FB15k-237 v1 run—is an interesting pilot, not a contribution. Rule mining and GNN/rule combinations are already established, and full-graph rule variants can rival or exceed NBFNet ([Anil et al., LREC-COLING 2024](https://aclanthology.org/2024.lrec-main.792/)).

### 4.7 Current graph/text systems are evaluated under incompatible protocols

The BGE model uses filtered full-candidate ranking over thousands of entities. The current S2DN protocol ranks against 50 sampled candidates. These numbers cannot be compared directly. The literature likewise cautions that 50-negative Hits@10 is a loose and less informative protocol than ranking over the full graph ([Anil et al., 2024](https://aclanthology.org/2024.lrec-main.792/)).

All methods in the final paper must use the same persisted candidate set, filtering rules, head/tail queries, tie handling, and result manifest.

### 4.8 The DBP-5L → GraIL converter merges distinct relations

[`convert_dbp5l_to_grail.py`](../wsl/research_kg/scripts/data_prep/convert_dbp5l_to_grail.py) uses sanitized display names as relation identifiers. In English, 166 distinct relation IDs form 83 name-collision groups, affecting 37,039 triples. For example, two different IDs both become `composer`. Relation symbols must remain injective, such as `R{id}__sanitized_name`.

### 4.9 The detector result is a useful smoke test, not evidence of self-healing

The reported AUC 0.995 comes from distinguishing a correct description from a randomly selected wrong entity description. That is an easy sanity benchmark. The “real contamination” analysis contains only 40 structurally eligible generated descriptions and reports 57% detection recall without a matched clean precision estimate. The “about 70% hallucinated” statement comes from a manual audit of only 25 Greek cases, while the majority of generated text is Japanese.

The 2,359-description cleaning count also includes both generated descriptions and unverifiable English fallback text, so it must not be described as 2,359 LLM hallucinations. The current +1.95 Japanese MRR result is evaluation-time replacement on one contaminated-trained checkpoint, not a clean multi-seed detection→repair→retraining loop.

### 4.10 The active experiment tree is not reproducible from GitHub

The committed snapshot is missing the central BGE trainer, evaluator, anchor evaluator, detector experiment, bootstrap script, and clean-retrain launcher named in the documentation. The active WSL root is not itself a Git repository, has multiple divergent environments, and permits result files to be overwritten without recording the description source.

Before further experiments, every result must record the code commit, environment, split hash, description hash, model revision, checkpoint hash, seed, exact command, candidate set, and filtering policy.

## 5. Literature-based novelty decision

The broad topic is timely, but several proposed components are occupied:

- A BERT/BGE bi-encoder with InfoNCE and in-batch/pre-batch/hard negatives is the SimKGC family, not a new model contribution ([SimKGC, ACL 2022](https://aclanthology.org/2022.acl-long.295/)).
- CRR is the main contribution of KGCRR ([AAAI 2025](https://ojs.aaai.org/index.php/AAAI/article/view/33410)).
- Relation-aware tail anchors are already developed in RAA-KGC ([AAAI 2025](https://ojs.aaai.org/index.php/AAAI/article/view/33672)).
- Text–structure fusion and adaptive fusion exist in StATIK, MERRY, and SEMMA ([StATIK](https://aclanthology.org/2022.findings-naacl.46/), [MERRY](https://aclanthology.org/2025.findings-acl.1046/), [SEMMA](https://aclanthology.org/2025.emnlp-main.1621/)).
- Multilingual sharing/routing exists in KL-GMoE ([Findings of EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.577/)).
- Noisy descriptions for unseen entities are not new: ConMask explicitly masks relation-irrelevant or noisy text for open-world KGC ([AAAI 2018](https://ojs.aaai.org/index.php/AAAI/article/view/11535)).
- Multilingual KG text quality and LLM/translation/web-search failures are already studied by M-NTA, which introduced the human-curated WikiKGE-10 benchmark and measured downstream KGC, QA, and entity-linking effects ([EMNLP 2023](https://aclanthology.org/2023.emnlp-main.100/)). KG-TRICK later unified multilingual textual and relational completion and introduced WikiKGE10++ ([COLING 2025](https://aclanthology.org/2025.coling-main.611/)).
- Text, structure, and rules have already been combined for KG error detection by CCA and GOLD ([CCA, AAAI 2024](https://ojs.aaai.org/index.php/AAAI/article/view/28729); [GOLD, Findings of EMNLP 2023](https://aclanthology.org/2023.findings-emnlp.232/)).
- PediaTypes already contains English↔French/German DBpedia transfer with entirely new nodes and relation types, so “the multilingual-inductive cell is empty” is not defensible as an absolute claim ([Double Equivariance / PediaTypes](https://arxiv.org/abs/2302.01313)).
- Stronger inductive backbones now include ULTRA, SEMMA, TARGI, GraphOracle, ARNS, and the June 2026 MGIL preprint; S2DN alone is not a sufficient state-of-the-art comparison ([ULTRA](https://arxiv.org/abs/2310.04562), [TARGI](https://ojs.aaai.org/index.php/AAAI/article/view/33260), [GraphOracle](https://ojs.aaai.org/index.php/AAAI/article/view/38978), [ARNS](https://ojs.aaai.org/index.php/AAAI/article/view/38484), [MGIL](https://arxiv.org/abs/2606.16509)).

### Defensible novelty

The strongest claim supported by the gap analysis is:

> **A leakage-controlled, concept-disjoint multilingual entity-inductive KGC benchmark with explicit evidence budgets, together with counterfactual evidence routing and calibrated abstention under missing and corrupted text.**

This is narrower and stronger than claiming generic multilingual KGC, generic text–structure fusion, or generic self-healing. The paper should use “to our knowledge, after a documented search” and define the exact scope rather than claim an absolute first.

## 6. Final proposal

### 6.1 Abstract

Multilingual knowledge graphs are unevenly populated: newly emerging entities may have no learned embedding, few structural edges, incomplete cross-language alignments, and missing or unreliable textual descriptions. Existing multilingual KGC benchmarks are largely transductive and alignment-oriented, while common inductive benchmarks can contain structural shortcuts and often use sampled-negative evaluation. This makes it unclear whether a method genuinely transfers to unseen real-world concepts, which evidence source it relies on, or whether it can recognize when that evidence is unreliable. We propose **DBP5L-Ind v2**, a concept-disjoint multilingual entity-inductive benchmark derived from DBP-5L. It groups aligned identifiers before splitting, provides inductive validation and three official folds, exposes nested 0/1/3/5-edge support budgets, fixes text provenance to the training snapshot, and evaluates filtered full-candidate head and tail prediction. It also supplies held-out missing-text and realistically corrupted-text tracks. On this benchmark we study **TrustRouter**, a lightweight reliability-aware mixture of a multilingual text retriever, a structural inductive reasoner, and an optional relation-prototype/symbolic expert. Counterfactual evidence dropout trains the router to adapt when text, graph support, or cross-language evidence is absent or corrupted; calibrated confidence enables selective abstention or text quarantine. Evaluation emphasizes macro-language performance, robustness, calibration, and risk–coverage in addition to MRR and Hits@k, with external validation on PediaTypes and human-curated multilingual text resources. The intended contribution is not another generic fusion model, but a reproducible benchmark and decision framework for knowing which evidence to trust for unseen multilingual entities.

### 6.2 Meaning of the problem

#### Plain-language meaning

A normal KGC system learns a vector for every entity it sees during training. That assumption fails when a new person, place, organization, work, or product enters a multilingual graph. The new entity may have only a name, a few links, a description copied from another language, or an automatically generated description containing plausible but false facts.

The system therefore has two coupled tasks:

1. **Complete the graph:** predict the missing head or tail entity.
2. **Know what to trust:** decide whether text, local graph structure, cross-language evidence, or relation prototypes are reliable for this query—and abstain when none is reliable.

The key distinction is between an unseen **identifier** and an unseen **concept**. If Japanese ID `ja:123` is held out but aligned English ID `en:456` remains in training, the real-world concept is not truly unseen. The primary track must hold out the entire aligned concept cluster.

#### Formal task

For each language \(\ell\), let \(G^\ell_{train}\) be the training graph. Aligned entity identifiers form concept clusters \(C\). For a test concept \(c\), the primary track requires \(c\cap G^\ell_{train}=\varnothing\) for every language. A query is either \((h,r,?)\) or \((?,r,t)\), with:

- text evidence \(x_e\), which can be clean, missing, or corrupted;
- a nested support set \(S_e^k\), where \(k\in\{0,1,3,5\}\);
- optional cross-language evidence \(A_e\), absent in the primary alignment-free track;
- a candidate set containing all eligible entities in the evaluation universe.

The model outputs a candidate score and a calibrated trust/abstention score. It should remain accurate when evidence is clean, degrade gracefully when evidence is removed or corrupted, and identify high-risk predictions.

### 6.3 Research questions and hypotheses

**RQ1 — Benchmark validity.** How much do current DBP-5L results change under concept-disjoint splitting, inductive validation, train-only text, full head/tail ranking, and shortcut auditing?

**H1:** The corrected protocol will produce materially different—and more credible—performance than the current identifier-disjoint split.

**RQ2 — Evidence complementarity.** When do text, graph support, cross-language evidence, and relation prototypes make different correct predictions?

**H2:** Complementarity will be largest for low-resource languages and at 0/1-edge support, but will vary more by evidence quality and relation frequency than by language identity alone.

**RQ3 — Reliability-aware routing.** Can a query-specific router outperform the best single expert and static fusion under missing or corrupted evidence without harming clean performance?

**H3:** Counterfactual evidence dropout plus reliability features will improve robust macro-MRR and worst-language performance while keeping clean MRR within 0.5 absolute points of the best clean-only model.

**RQ4 — Selective prediction.** Can the system identify risky evidence and predictions well enough to abstain or quarantine text?

**H4:** TrustRouter will improve AUPRC, calibration, and risk–coverage over raw graph–text cosine and entropy-only baselines on held-out hard corruptions.

### 6.4 Solution

#### Work package 0 — Reproducibility foundation

Before new training:

1. Put the active WSL root code under Git and merge the authoritative Windows/WSL sources.
2. Commit or package the BGE trainer, evaluator, detector, significance scripts, and clean launchers.
3. Freeze the working Python/CUDA/DGL/Transformers environments.
4. Make every split, candidate set, description corpus, rule cache, and result immutable and content-addressed.
5. Add a run manifest containing code commit, input hashes, model revision, seed, command, hardware, and evaluation protocol.

#### Work package 1 — DBP5L-Ind v2

1. **Concept clustering:** build connected components from alignment links and split clusters, not individual language IDs.
2. **Strict partitions:** create disjoint training, validation, and test concept sets. Validation must be inductive and match the test distribution.
3. **Three official folds:** publish three fixed split seeds/folds rather than regenerate splits per experiment.
4. **Evidence budgets:** expose deterministic nested support sets \(S^0\subset S^1\subset S^3\subset S^5\). Enforce the cap after the global union, and remove every support edge from evaluation.
5. **Tracks:**
   - **Concept-cold primary:** the aligned concept is unseen in every language.
   - **Language-cold diagnostic:** target-language ID unseen, but evidence may exist in another language.
   - **Zero/few-edge:** 0, 1, 3, or 5 graph-support edges.
   - **Alignment-free primary** and **oracle-alignment diagnostic**.
6. **Snapshot-safe text:** primary text must come from a fixed source snapshot and may use only information legally available at training time. Structural descriptions must use training triples only.
7. **No generated text in the clean primary track:** generated descriptions become a named corruption condition, not ground truth.
8. **Shortcut and leakage audit:** assert entity/concept disjointness, alignment disjointness, relation coverage, support/evaluation separation, answer-string leakage, duplicate facts, temporal provenance, degree balance, and PPR performance.
9. **Evaluation universe:** define clearly whether all 56,589 official entities or only graph-active entities are candidates; report both only if each has a clear use case.

#### Work package 2 — Baseline matrix

Use the identical splits and evaluator for every method:

- **Sanity baselines:** exact/normalized name match, relation frequency, popularity, random, and PPR.
- **Text experts:** mBERT, XLM-R, and BGE-M3 in a SimKGC-style bi-encoder. Compare InfoNCE with CRR as an attributed objective ablation.
- **Structural experts:** at least InGram or ULTRA plus one current strong method such as GraphOracle. Include S2DN only after deterministic evaluation and gradient audits.
- **Prototype/anchor expert:** RAA-KGC or an equivalent relation-tail prototype baseline.
- **Fusion controls:** score averaging, tuned static late fusion, oracle per-query expert selection, and TrustRouter.
- **Ceilings:** transductive DBP-5L systems and oracle alignment may be reported as diagnostic ceilings, never as directly comparable inductive results.

The oracle expert selector is important: if it shows little complementarity, a learned router is unlikely to be worth building.

#### Work package 3 — TrustRouter

Let each expert \(m\) produce score \(s_m(q,c)\). A lightweight gate computes weights:

\[
s(q,c)=\sum_m w_m(z_q)s_m(q,c), \qquad \sum_m w_m(z_q)=1.
\]

The evidence vector \(z_q\) uses measurable availability and confidence rather than treating language identity as the main signal:

- support-edge count, path availability, and local degree;
- description presence, source/provenance, length, and graph–text consistency;
- relation frequency and cardinality;
- expert entropy, score margin, and disagreement;
- relation-prototype confidence;
- cross-language retrieval/alignment confidence.

Training uses **counterfactual evidence dropout**: independently mask text, support edges, alignments, and prototypes; inject realistic text corruption; and require the gate to adapt. The objective combines ranking loss, evidence-consistency loss, and calibration/selective-risk loss.

The system produces both a link prediction and \(p_{trust}\). Below a validation-calibrated threshold it may:

1. down-weight or quarantine the description;
2. fall back to graph/name evidence;
3. abstain and request review.

Automatic text correction is outside the primary claim. It becomes a follow-up only after detection and quarantine work on held-out realistic data.

RuleTrust can enter only as an optional expert or reliability feature after its cache, deterministic evaluation, open-world interpretation, and multi-seed effect are validated.

#### Work package 4 — Realistic missing/corrupted evidence

Use separate difficulty levels:

1. **Missing:** description removed; name-only.
2. **Easy sanity:** random wrong-entity description.
3. **Hard semantic swap:** type-, language-, length-, and popularity-matched wrong entity.
4. **Claim-level corruption:** alter one verifiable date, location, type, occupation, creator, or relation while preserving fluent style.
5. **Multi-generator corruption:** descriptions generated by multiple model families/prompts, with source facts hidden or contradicted.
6. **Observed-source sample:** a source-verifiable sample of naturally missing, outdated, mistranslated, or incorrect multilingual descriptions.

Thresholds must be selected on validation data and evaluated on a disjoint test set. The minimum credible annotation target is 500 cases stratified across five languages; the preferred target is 1,000, with two annotators and adjudication. If bilingual verification is unavailable, narrow the claim rather than call model-generated project artifacts “in the wild.”

### 6.5 Evaluation protocol

#### Link prediction

- Filtered **full-candidate** head and tail ranking.
- MRR and Hits@1/3/10.
- Micro average, macro average across languages, and worst-language score.
- Per-language, per-direction, per-support-budget, zero-edge, degree, relation-frequency, text-source, and corruption strata.
- Average rank for ties and a persisted candidate set.
- Mean ± standard deviation over at least three training seeds.
- Paired bootstrap confidence intervals over queries; report effect sizes, not only p-values.

#### Reliability and corruption

- AUPRC as the main detector metric under realistic class imbalance; AUROC and F1 as secondary metrics.
- Threshold selected only on validation.
- Expected Calibration Error and Brier score.
- Risk–coverage and selective MRR curves.
- Robustness curves across corruption rates and severities.
- Clean-performance cost of robustness.
- Detection→quarantine→KGC change, with the same checkpoint and candidate protocol.

#### External validation

- **PediaTypes:** multilingual DBpedia transfer with unseen nodes and relations; useful for external structural generalization.
- **Wikidata5M-Ind:** text-inductive sanity check for the text expert, with protocol differences stated explicitly.
- **WikiKGE-10/10++:** human-curated multilingual textual quality evaluation; use as an external description-quality resource, not as if it were the same KGC task.
- **WN18RR/FB15k-237/NELL:** implementation verification only, not primary evidence for the multilingual contribution.

### 6.6 Novelty

The proposed contributions are:

1. **DBP5L-Ind v2:** a concept-cluster-disjoint multilingual entity-inductive benchmark with matched inductive validation, fixed folds, explicit evidence budgets, train-time text provenance, alignment-free/oracle tracks, shortcut audits, and full head/tail ranking.
2. **Counterfactual evidence-budget routing:** a query-specific mechanism trained to change expert reliance when text, structure, alignments, or prototypes are removed or corrupted.
3. **Calibrated selective KGC:** reliability estimation, abstention, and text quarantine evaluated jointly with link prediction rather than reporting only a detector AUC.
4. **A multilingual robustness analysis:** clean, missing, and realistically corrupted evidence across five unequal-resource languages, with macro/worst-language reporting and external validation.

Claims that should **not** be made:

- “first multilingual inductive KGC” without a tightly qualified scope;
- BGE-M3, LoRA, CRR, hard negatives, anchors, generic fusion, or generic MoE as novel;
- 2,359 LLM hallucinations or a 70% global contamination rate;
- “in-the-wild” detection based only on project-generated descriptions;
- “self-healing” before a validated detection→decision→repair→re-evaluation loop exists;
- superiority based on comparing full ranking with 50 sampled negatives.

### 6.7 Datasets

| Dataset/resource | Role | Required treatment |
|---|---|---|
| **DBP-5L** (EN, FR, ES, JA, EL) | Core source for DBP5L-Ind v2 | Rebuild concept-disjoint folds; preserve all relation IDs; version alignments and text provenance |
| **Current DBP-5L-Ind** | Diagnostic only | Do not use as final benchmark; retain to quantify how corrections change results |
| **PediaTypes EN↔FR/DE** | External multilingual fully inductive validation | Use its published protocol and report sampled/full-ranking differences |
| **Wikidata5M-Ind** | External text-inductive validation | Do not compare raw MRR across different candidate universes |
| **WikiKGE-10 / WikiKGE10++** | External multilingual text-quality evidence | Use human-curated names/descriptions to validate quality signals |
| **WN18RR / FB15k-237 / NELL inductive splits** | Structural implementation checks | Persist candidates and separate these results from DBP-5L claims |
| **1,042 generated descriptions** | Corruption research material | Exclude from clean training; label source/model/prompt; verify a stratified subset |

DBP-5L’s published per-language graph sizes are approximately 80,167 triples for EN, 49,015 FR, 54,066 ES, 28,774 JA, and 13,839 EL ([SS-AGA dataset table](https://aclanthology.org/2022.acl-long.36.pdf)). The current local split contains 118,256 training triples, 13,137 validation triples, 54,473 inductive test triples, and 39,995 support edges across five languages. These local counts should be regenerated and hashed after the split redesign.

### 6.8 Compute required

#### Measured local costs

- BGE-M3 LoRA: about **9–10 GPU-hours per seed** on the RTX 5070 Ti; three seeds ≈ **30 GPU-hours**.
- mBERT clean baseline: about **3.1 GPU-hours per seed**.
- Full DBP-5L evaluation: roughly **10–30 minutes per checkpoint**, depending on mode.
- S2DN FB15k-237 v1 paper configuration: about **4.8 GPU-hours** plus evaluation.
- Current 16 GB GPU cannot run some FB15k-237 v2 S2DN settings.

#### Recommended paper budget

| Work | Estimated GPU-hours | Main machine |
|---|---:|---|
| Corrected clean BGE-M3, 3 seeds | 30 | RTX 5070 Ti |
| mBERT + XLM-R, 3 seeds | 20–30 | RTX 5070 Ti |
| Core objective/text/evidence ablations | 30–50 | RTX 5070 Ti |
| One or two structural baselines on corrected splits | 40–80 | 96 GB GPU preferred |
| Static fusion, oracle selector, TrustRouter, calibration | 40–70 | Either GPU |
| Evaluation, bootstrap, robustness curves | 5–15 | GPU + CPU |
| **Primary paper total** | **165–275** | staged across both GPUs |
| Optional S2DN/RuleTrust validation | +50–100 | 96 GB GPU |

These are engineering estimates and should be recalibrated after one profiled English run. A safe upper allocation is **350–400 GPU-hours**, but one-seed screening should eliminate weak configurations before three-seed confirmation.

#### CPU, RAM, disk, and human resources

- **CPU:** 16–32 cores for split construction, graph partitioning, PPR audits, subgraph extraction, and bootstrap analysis.
- **RAM:** 32 GB minimum; 64 GB recommended. The current WSL 15 GB allocation may bottleneck structural preprocessing.
- **Storage:** reserve 150 GB for data, caches, manifests, rank dumps, and checkpoints. Save LoRA adapters rather than 1.14 GB copies of the frozen encoder.
- **Annotation:** approximately 50–170 annotator-hours for 500–1,000 twice-labeled multilingual cases, depending on verification difficulty and adjudication.
- **Model scale:** no multi-billion-parameter MoE is required. The proposed gate is lightweight; frozen/cached expert embeddings should be used wherever possible.

### 6.9 Execution plan and go/no-go gates

#### Phase 0 — Scientific repair (1–2 weeks)

- Version active WSL code and environments.
- Fix immutable manifests/results, relation mapping, rule cache keys, S2DN candidates, and deterministic inference.
- Rebuild descriptions from train-only evidence.

**Gate G0:** a fresh machine can reproduce one text and one structural baseline from the repository.

#### Phase 1 — Benchmark v2 (2–4 weeks)

- Build concept clusters, strict train/validation/test folds, nested support budgets, and alignment tracks.
- Run leakage, degree, relation, duplicate, answer-text, and PPR audits.
- Freeze data cards and hashes.

**Gate G1:** no concept/alignment leakage; all assertions pass; PPR is reported and does not explain the benchmark; full head/tail evaluation is deterministic.

#### Phase 2 — Clean baseline suite (3–5 weeks)

- Run lexical/PPR, mBERT, XLM-R, BGE-M3, one structural KGFM, relation-anchor, and static-fusion baselines.
- Use one seed for screening, then three seeds for the locked core matrix.

**Gate G2:** clean three-seed baselines and an oracle expert-selection analysis exist. If oracle selection adds little, submit a benchmark/resource paper and stop method expansion.

#### Phase 3 — Reliability and routing (3–5 weeks)

- Build held-out missing/hard-corruption data.
- Train TrustRouter with counterfactual evidence dropout.
- Evaluate calibration, risk–coverage, and robust macro-MRR.

**Gate G3:** TrustRouter beats the best single expert and tuned static fusion with a paired 95% confidence interval under corruption, while clean MRR drops by no more than 0.5 absolute points.

#### Phase 4 — External replication and writing (2–4 weeks)

- Validate on PediaTypes and at least one text-inductive/text-quality external resource.
- Freeze tables, claims, model/data cards, and reproducibility package.

**Gate G4:** the main conclusion holds outside the new DBP-5L split. If it does not, narrow the paper to the benchmark and diagnostic findings.

#### Follow-up only — self-healing

Add automatic correction and downstream QA/RAG only after a detector identifies real/realistic errors, a repair is externally verified, and the repaired KB improves KGC or factual QA without damaging clean cases. Related work already shows multilingual machine-generated Wikipedia text is difficult to detect in realistic settings ([WETBench](https://aclanthology.org/2025.wikinlp-1.6/)) and KG denoising can improve downstream QA ([GOLD](https://aclanthology.org/2023.findings-emnlp.232/)); this raises the evidence standard for a self-healing claim.

## 7. What to keep, park, and stop claiming now

### Keep and repair

- BGE-M3/LoRA training pipeline and full evaluator.
- mBERT baseline and clean description source work.
- S2DN reproduction as an implementation appendix or structural baseline.
- Rule mining as an optional reliability feature.
- The contamination observation as motivation and a hypothesis.
- The failure ledger, provided it is tied to immutable runs.

### Park from the primary critical path

- Finishing every S2DN split before multilingual work.
- Semantic Smoothing and RuleTrust as mandatory architecture contributions.
- Full downstream RAG/QA generation before KGC and reliability evaluation are valid.
- Automatic repair of zero-edge entities without external evidence.

### Retract or relabel until proven

- Relabel 26.51 ± 0.31 as **old-description/provisional**.
- Relabel AUC 0.995 as **random-swap sanity benchmark**.
- Relabel +1.95 JA as **one-checkpoint evaluation-time text replacement**, not repair causality.
- Replace “first multilingual inductive benchmark” with a precise, qualified scope after the PediaTypes comparison.
- Replace “self-healing” with **reliability-aware detection/quarantine** until the closed loop is demonstrated.

## 8. Final recommendation

The current project should proceed, but its primary scientific object must become **DBP5L-Ind v2 and trustworthy evidence use for unseen multilingual concepts**. This preserves the strongest existing work while removing the most fragile claims.

The best paper story is:

1. Existing evaluation cannot tell whether multilingual inductive systems truly generalize or which evidence they trust.
2. DBP5L-Ind v2 fixes concept leakage, evidence budgets, text provenance, shortcut risk, and evaluation comparability.
3. Strong text and structural experts fail in different evidence regimes.
4. TrustRouter learns to route or abstain under controlled missing/corrupted evidence.
5. The result is validated across languages, evidence budgets, and an external inductive resource.

If the router fails its gate, the benchmark and empirical diagnosis remain a coherent publishable unit. If the corruption and repair work later passes its stronger gate, it becomes a separate, better-supported self-healing paper rather than an overextended section of the first one.
