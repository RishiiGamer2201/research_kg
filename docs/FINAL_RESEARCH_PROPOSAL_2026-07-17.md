# Final Research Proposal: SelfHeal-MKGC

**Working title:** *SelfHeal-MKGC: Evidence-Budgeted Multilingual Inductive Knowledge Graph Completion with Detection, Verified Repair, and Downstream Recovery*

**Date:** 17 July 2026

**Status:** unified benchmark, method, and self-healing paper plan
**Audit scope:** the committed Windows snapshot, the live WSL training tree, `origin/main` at commit `1d7e0e3`, experiment logs, preprocessing/evaluation code, and primary research literature through 17 July 2026.

## 1. Decision

The project will target **one unified self-healing paper** rather than separate primary and follow-up papers. The paper will connect benchmark construction, reliability-aware KGC, contamination detection, verified repair, and downstream evaluation through one falsifiable question:

> Can a multilingual inductive KGC system identify when its available evidence is unreliable, abstain or quarantine unsafe evidence, repair it from verified sources, and recover KGC and factual-QA performance without damaging clean cases?

The unified scope is ambitious but coherent if every component serves this closed loop:

1. **DBP5L-Ind v2** supplies concept-disjoint entities, explicit evidence budgets, clean text, and held-out corruption tracks.
2. **BGE-M3/LoRA experimentation** establishes a strong text baseline and tests native dense/sparse/multi-vector scoring, structure/schema-aware contrastive learning, calibrated uncertainty, joint link-description learning, Semantic Smoothing, RuleTrust, and carefully selected combinations.
3. **TrustRouter** chooses among text, structure, rules, and fallback evidence while producing calibrated uncertainty.
4. **Self-healing** converts detection into action: abstain, quarantine, retrieve a verified replacement, validate it, accept or reject the repair, and re-evaluate the affected tasks.
5. **Downstream evaluation** measures whether accepted repairs improve both KGC and one focused factual QA/RAG task.

Several current headline results remain provisional because of split leakage, incompatible protocols, unclean descriptions, and incomplete provenance. The paper therefore keeps a benchmark-first execution order, but the final submission must include the complete detect → decide → repair → verify → re-evaluate loop.

Semantic Smoothing and RuleTrust are promoted from parked ideas to **gated experimental branches**. They will be tested separately and together inside the BGE-M3/LoRA pipeline. They become main-paper method contributions only if multi-seed experiments show gains beyond tuned controls; otherwise they remain informative ablations.

## 2. What the current plan proposes

The current plan of record is [`pivot/UNIFIED_PATHWAY.md`](pivot/UNIFIED_PATHWAY.md). It contains three proposed products:

- **P1 — DBP-5L-Ind:** an entity-disjoint multilingual inductive KGC benchmark with a BGE-M3 text baseline.
- **P2 — self-healing multilingual KBs:** detect fabricated entity descriptions from text–structure disagreement, quarantine or repair them, and measure downstream effects.
- **P3 — RuleTrust-S2DN:** add mined Horn-rule evidence to S2DN if paired experiments establish a genuine gain.

The old ladder is S2DN reproduction → English neuro-symbolic modification → multilingual conversion → self-healing → paper packaging. This proposal replaces that product sequence with one dependency-driven pipeline: repair the benchmark → lock clean BGE/structural baselines → screen Semantic Smoothing and RuleTrust → train reliability routing → detect and quarantine corruption → perform verified repair → measure KGC and factual-QA recovery. S2DN reproduction is supporting evidence, not a separate product that blocks the multilingual paper.

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
- The current pipeline uses only BGE-M3's dense vector even though the model was trained for dense, learned-sparse, and multi-vector retrieval with cross-mode self-distillation ([BGE-M3](https://aclanthology.org/2024.findings-acl.137/)). This creates a low-cost experiment opportunity before changing the backbone.
- Structure-aware and schema-aware contrastive work suggests that vertex, neighborhood, path, relation composition, type constraints, and schema-guided negatives can add supervision absent from triple-only text training ([StructKGC](https://aclanthology.org/2024.emnlp-main.772/); [Prior Relational Schema](https://aclanthology.org/2024.lrec-main.1139/)).
- Multilingual knowledge sharing and iterative reranking are already demonstrated in transductive MKGC ([KL-GMoE](https://aclanthology.org/2025.findings-emnlp.577/)); the research opportunity here is to test whether lightweight shared/language-specific adapters and reranking transfer to concept-inductive entities.
- Calibration and conformal answer sets now provide stronger uncertainty baselines than raw softmax confidence ([KGE Calibrator](https://aclanthology.org/2025.emnlp-main.1522/); [Conformalized Answer Set Prediction](https://aclanthology.org/2025.naacl-long.32/)).
- Description repair should be claim-level and source-grounded: FActScore decomposes text into atomic facts, SAFE adds search-grounded verification, and RARR retrieves evidence before minimally revising unsupported content ([FActScore](https://aclanthology.org/2023.emnlp-main.741/); [SAFE](https://papers.neurips.cc/paper_files/paper/2024/hash/937ae0e83eb08d2cb8627fe1def8c751-Abstract-Conference.html); [RARR](https://aclanthology.org/2023.acl-long.910/)).
- LLM-as-a-judge cannot be treated as gold in this project: multilingual judges are inconsistent across equivalent languages and weaker for low-resource languages ([How Reliable is Multilingual LLM-as-a-Judge?](https://aclanthology.org/2025.findings-emnlp.587/)). It is therefore an ablated verifier calibrated against human labels, not the final authority.

### Defensible novelty

The strongest unified claim to test is:

> **A leakage-controlled, concept-disjoint multilingual inductive KGC system that operates under explicit evidence budgets, detects unreliable evidence, selects or abstains through calibrated routing, repairs quarantined descriptions from verified sources, and demonstrates recovery in KGC and factual QA.**

The novelty is the evaluated closed loop rather than any isolated component. BGE-M3, LoRA, Semantic Smoothing, Horn rules, routing, retrieval, and QA are established ideas individually. The proposed contribution is their controlled use in a multilingual concept-inductive setting, with verification and downstream recovery determining whether a repair is accepted. The paper should use “to our knowledge, after a documented search” and define this exact scope rather than claim an absolute first.

## 6. Final proposal

### 6.1 Abstract

Multilingual knowledge graphs are unevenly populated: newly emerging entities may have no learned embedding, few structural edges, incomplete alignments, and missing or unreliable textual descriptions. Existing multilingual KGC benchmarks are largely transductive, while common inductive benchmarks may contain structural shortcuts and rarely test whether a system can recognize, repair, and recover from corrupted evidence. We propose **DBP5L-Ind v2**, a concept-disjoint multilingual entity-inductive benchmark with inductive validation, three fixed folds, nested 0/1/3/5-edge support budgets, snapshot-safe text, full-candidate head/tail evaluation, and held-out missing and realistically corrupted evidence. We first build a BGE-M3/LoRA text expert and test two gated extensions: similarity-guided **Semantic Smoothing** and symbolic **RuleTrust**, individually and jointly. A calibrated **TrustRouter** then combines text, structure, prototypes, and rule evidence under counterfactual evidence dropout. When confidence is low, the system abstains or quarantines the description; a self-healing controller retrieves candidate replacements from approved sources, verifies graph-text and source consistency, accepts only threshold-qualified repairs, and otherwise rolls back or requests review. The complete loop is evaluated by KGC recovery, calibration and risk–coverage, repair precision, clean-case preservation, and one focused factual QA/RAG task, with external validation on an additional multilingual resource. The intended contribution is an evidence-budgeted multilingual KGC benchmark and a verified detect → repair → re-evaluate system, not merely another generic fusion model.

### 6.2 Meaning of the problem

#### Plain-language meaning

A normal KGC system learns a vector for every entity it sees during training. That assumption fails when a new person, place, organization, work, or product enters a multilingual graph. The new entity may have only a name, a few links, a description copied from another language, or an automatically generated description containing plausible but false facts.

The system therefore has four coupled tasks:

1. **Complete the graph:** predict the missing head or tail entity.
2. **Know what to trust:** decide whether text, local graph structure, cross-language evidence, or relation prototypes are reliable for this query—and abstain when none is reliable.
3. **Repair unreliable evidence:** quarantine a suspect description, retrieve a candidate replacement from approved sources, and verify it before changing the KB.
4. **Prove recovery:** show that an accepted repair improves KGC and factual QA/RAG while leaving clean cases unchanged.

The key distinction is between an unseen **identifier** and an unseen **concept**. If Japanese ID `ja:123` is held out but aligned English ID `en:456` remains in training, the real-world concept is not truly unseen. The primary track must hold out the entire aligned concept cluster.

#### Formal task

For each language $\ell$, let $G^\ell_{\mathrm{train}}$ be the training graph. Aligned entity identifiers form concept clusters $C$. For a test concept $c$, the primary track requires $c\cap G^\ell_{\mathrm{train}}=\varnothing$ for every language. A query is either $(h,r,?)$ or $(?,r,t)$, with:

- text evidence $x_e$, which can be clean, missing, or corrupted;
- a nested support set $S_e^k$, where $k\in\{0,1,3,5\}$;
- optional cross-language evidence $A_e$, absent in the primary alignment-free track;
- a candidate set containing all eligible entities in the evaluation universe.

The model outputs a candidate score and a calibrated trust/abstention score. For quarantined text it also outputs a repair decision with provenance, verification evidence, and an accept/reject/rollback state. It should remain accurate when evidence is clean, degrade gracefully when evidence is removed or corrupted, and improve after verified repair without modifying clean evidence unnecessarily.

### 6.3 Research questions and hypotheses

**RQ1 — Benchmark validity.** How much do current DBP-5L results change under concept-disjoint splitting, inductive validation, train-only text, full head/tail ranking, and shortcut auditing?

**H1:** The corrected protocol will produce materially different—and more credible—performance than the current identifier-disjoint split.

**RQ2 — Evidence complementarity.** When do text, graph support, cross-language evidence, and relation prototypes make different correct predictions?

**H2:** Complementarity will be largest for low-resource languages and at 0/1-edge support, but will vary more by evidence quality and relation frequency than by language identity alone.

**RQ3 — Reliability-aware routing.** Can a query-specific router outperform the best single expert and static fusion under missing or corrupted evidence without harming clean performance?

**H3:** Counterfactual evidence dropout plus reliability features will improve robust macro-MRR and worst-language performance while keeping clean MRR within 0.5 absolute points of the best clean-only model.

**RQ4 — Selective prediction.** Can the system identify risky evidence and predictions well enough to abstain or quarantine text?

**H4:** TrustRouter will improve AUPRC, calibration, and risk–coverage over raw graph–text cosine and entropy-only baselines on held-out hard corruptions.

**RQ5 — BGE-M3 method extensions.** Which retrieval mode, contrastive structure/schema signal, negative-mining strategy, calibration method, Semantic Smoothing variant, or RuleTrust mechanism improves a BGE-M3/LoRA bi-encoder under clean, sparse, and corrupted evidence?

**H5:** BGE hybrid scoring and structure/schema-aware supervision will provide the strongest general gains; similarity-guided smoothing will help sparse and semantically related relations, while rule confidence will help high-precision rule-covered queries. Combined mechanisms will help only when calibrated and gated rather than applied uniformly.

**RQ6 — Closed-loop self-healing.** Can the system detect, repair, verify, and recover from multilingual description contamination without damaging clean entities?

**H6:** Verified repair will increase post-corruption KGC MRR and factual-QA accuracy over quarantine-only and unverified generation, while keeping the false-repair rate and clean-case regression below validation-set thresholds.

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
4. **Evidence budgets:** expose deterministic nested support sets $S^0\subset S^1\subset S^3\subset S^5$. Enforce the cap after the global union, and remove every support edge from evaluation.
5. **Tracks:**
   - **Concept-cold primary:** the aligned concept is unseen in every language.
   - **Language-cold diagnostic:** target-language ID unseen, but evidence may exist in another language.
   - **Zero/few-edge:** 0, 1, 3, or 5 graph-support edges.
   - **Alignment-free primary** and **oracle-alignment diagnostic**.
6. **Snapshot-safe text:** primary text must come from a fixed source snapshot and may use only information legally available at training time. Structural descriptions must use training triples only.
7. **No generated text in the clean primary track:** generated descriptions become a named corruption condition, not ground truth.
8. **Shortcut and leakage audit:** assert entity/concept disjointness, alignment disjointness, relation coverage, support/evaluation separation, answer-string leakage, duplicate facts, temporal provenance, degree balance, and PPR performance.
9. **Evaluation universe:** define clearly whether all 56,589 official entities or only graph-active entities are candidates; report both only if each has a clear use case.

#### Work package 2A — Baseline matrix

Use the identical splits and evaluator for every method:

- **Sanity baselines:** exact/normalized name match, relation frequency, popularity, random, and PPR.
- **Text experts:** mBERT, XLM-R, and BGE-M3 in a SimKGC-style bi-encoder. Compare InfoNCE with CRR as an attributed objective ablation.
- **Structural experts:** at least InGram or ULTRA plus one current strong method such as GraphOracle. Include S2DN only after deterministic evaluation and gradient audits.
- **Prototype/anchor expert:** RAA-KGC or an equivalent relation-tail prototype baseline.
- **Fusion controls:** score averaging, tuned static late fusion, oracle per-query expert selection, and TrustRouter.
- **Ceilings:** transductive DBP-5L systems and oracle alignment may be reported as diagnostic ceilings, never as directly comparable inductive results.

The oracle expert selector is important: if it shows little complementarity, a learned router is unlikely to be worth building.

#### Work package 2B — BGE-M3/LoRA experimental ladder

The clean BGE-M3/LoRA model is the anchor baseline. New mechanisms must be introduced one at a time, with identical data, candidates, seeds, and evaluation:

| Experiment | Change from clean BGE-M3/LoRA | Main purpose |
|---|---|---|
| B0 | Clean BGE-M3 + LoRA + standard contrastive objective | Locked baseline |
| B1 | CRR versus InfoNCE and calibrated hard-negative variants | Objective control |
| B2 | Relation-aware description/query templates and prototype anchors | Strong text control |
| B3 | Semantic Smoothing only | Test soft semantic supervision |
| B4 | RuleTrust loss weighting only | Test rule confidence during training |
| B5 | RuleTrust score adapter only | Test symbolic evidence at ranking time |
| B6 | Semantic Smoothing + RuleTrust | Test complementarity or interference |
| B7 | Evidence dropout + corruption-aware training | Prepare the expert for routing and healing |

**Semantic Smoothing for BGE-M3.** Because BGE-M3 is a text bi-encoder rather than S2DN's relation GNN, the S2DN layer should not be copied literally. Implement three controlled variants:

1. **Soft-target smoothing:** distribute a small target mass to semantically related valid entities or relations using frozen description/relation similarity, excluding known false candidates.
2. **Relation-prototype consistency:** encourage queries for related relations to remain close to their train-only relation prototypes while preserving a margin between incompatible relations.
3. **Cross-view consistency:** require the text embedding to agree with a structural/prototype view when that view is available and trusted.

The smoothing coefficient must be tuned on inductive validation. Similarity neighbors and prototypes must be built from training evidence only, and false-negative filtering must be applied before soft targets are formed.

**RuleTrust for BGE-M3.** Test symbolic rules through mechanisms compatible with the bi-encoder:

1. **Example weighting:** multiply the ranking loss by a calibrated function of rule confidence and support.
2. **Adaptive margin:** require a larger positive/negative margin when high-confidence rules support the positive or contradict the negative.
3. **Score adapter:** add a normalized rule score through a learnable scalar initialized to zero, mirroring the controlled S2DN pilot.
4. **Rule feature token/adapter:** inject a compact relation-rule feature into the query adapter without converting entity IDs into memorized embeddings.

Rules must be mined from training triples only, relation IDs must remain injective, and the target edge must be removed when computing support. Required controls are shuffled rules, confidence-matched random rules, zero rule weight, coverage buckets, and no-inverse rules.

**Selection rule.** Screen variants with one seed, then run at least three paired seeds for B0, the best smoothing model, the best RuleTrust model, and their combination. A component survives only if it improves clean or robust macro-MRR with a paired confidence interval, or materially improves calibration/repair coverage without an unacceptable clean-performance cost. Otherwise it remains a negative ablation.

#### Work package 2C — Literature-derived KGC experiment portfolio

The following experiments were selected from related inductive, transductive, multilingual, contrastive, and uncertainty-aware KGC work. They are ranked by expected scientific value relative to implementation cost. “Priority 0” experiments should be completed before expanding the architecture; “Priority 1” experiments are screened only after the clean baseline is locked; “Priority 2” experiments are optional if the simpler version saturates.

| ID | Priority | Experiment | Paper basis | Adaptation to this project | Main test |
|---|:---:|---|---|---|---|
| K1 | 0 | **Native BGE-M3 dense/sparse/multi-vector KGC** | [BGE-M3](https://aclanthology.org/2024.findings-acl.137/) supports dense, learned-sparse, and multi-vector retrieval with cross-mode self-distillation | Compare dense-only, sparse-only, multi-vector reranking, learned score fusion, and hybrid-teacher→dense-student distillation | Do lexical and token-level signals recover low-resource or long-description errors missed by the current single dense vector? |
| K2 | 0 | **Structure-aware supervised contrastive tasks** | [StructKGC](https://aclanthology.org/2024.emnlp-main.772/) uses vertex-, neighbor-, path-, and relation-composition-level contrastive tasks | Add train-only neighbor/path/relation-composition positives to BGE fine-tuning; ablate each task and all tasks | Can local structure improve text representations without requiring a full GNN at inference? |
| K3 | 0 | **Schema/type-guided negatives** | [Prior Relational Schema](https://aclanthology.org/2024.lrec-main.1139/) uses schema interactions and schema-guided negatives for inductive KGC | Build domain/range/type prototypes from training only; sample same-type hard negatives and explicit type-violating controls | Does relation schema sharpen unseen-entity ranking and improve corruption detection? |
| K4 | 0 | **False-negative-safe dynamic mining** | [Generative hard-negative mining](https://aclanthology.org/2023.findings-acl.362/) and [positive-set expansion](https://aclanthology.org/2025.r2lm-1.17/) show benefits from harder negatives and additional plausible positives | Refresh top-ranked negatives during training; filter known/likely positives using graph facts, alignments, rules, and type constraints; optionally expand positives only when two independent signals agree | Can harder multilingual confusables improve discrimination without repeating the stale-cache failure? |
| K5 | 0 | **Calibrated and conformal answer sets** | [KGE Calibrator](https://aclanthology.org/2025.emnlp-main.1522/) targets ranking-preserving probability calibration; [conformalized KGE answer sets](https://aclanthology.org/2025.naacl-long.32/) provide coverage-controlled candidate sets | Compare temperature/vector scaling, KGEC-style calibration, and relation/language/evidence-budget conformal sets | Can abstention use statistically meaningful coverage rather than an arbitrary score threshold? |
| K6 | 0 | **Joint link-and-description completion** | [KG-TRICK](https://aclanthology.org/2025.coling-main.611/) unifies multilingual relational and textual completion | Add auxiliary masked-description reconstruction, source-language→target-language description completion, and relation prediction; never expose test descriptions | Does learning KGC and description quality together improve both induction and later repair verification? |
| K7 | 1 | **Shared plus language-specific LoRA experts** | [KL-GMoE](https://aclanthology.org/2025.findings-emnlp.577/) combines grouped multilingual experts with iterative entity reranking | Use one shared LoRA plus small language/script/resource-group adapters and a sparse gate; add leave-one-language-out and imbalance tests | Is language-specific capacity useful beyond a shared multilingual encoder, especially for EL and JA? |
| K8 | 1 | **Two-stage iterative entity reranking** | [KL-GMoE](https://aclanthology.org/2025.findings-emnlp.577/) iterative reranking and [BGE-M3](https://aclanthology.org/2024.findings-acl.137/) multi-vector scoring motivate a retriever→reranker design | Dense retrieval produces top-K; rerank with BGE multi-vector interaction, a compact cross-encoder, or structure/rule features | Does top-K reranking improve full-ranking MRR enough to justify latency? Report recall@K and cost. |
| K9 | 1 | **Sparse-entity pseudo-neighbor augmentation** | [SLiNT](https://aclanthology.org/2025.findings-emnlp.736/) uses structure-guided pseudo-neighbors and dynamic hard contrastive learning | Retrieve train entities with similar text/type and transfer only relation prototypes or confidence-weighted summaries—not unverified edges | Can zero/one-edge entities benefit without fabricating graph facts or leaking aligned concepts? |
| K10 | 1 | **Perturbation stability regularization** | [Stability and Generalization of Subgraph Reasoners](https://openreview.net/forum?id=NE6Px91RkQ) links structural perturbation stability to inductive generalization | Apply nested support-edge dropout, description sentence dropout, and relation-label paraphrases; penalize excessive score/rank changes when semantics are preserved | Does local stability predict and improve robustness under evidence budgets? |
| K11 | 1 | **Reciprocal and auxiliary relation/type prediction** | [Multi-task PLM KGC](https://aclanthology.org/2020.coling-main.153/) combines link, relation, and relevance objectives | Train head and tail directions jointly with relation and entity-type auxiliary heads; compare shared versus separate adapters | Does auxiliary relational supervision reduce lexical shortcutting? |
| K12 | 2 | **Self-adversarial negative weighting** | [RotatE](https://openreview.net/forum?id=HkgEQnRqYQ) introduced self-adversarial negative sampling | Weight filtered negatives by current model hardness with a capped temperature and stop-gradient | Is this cheaper than a generator while matching dynamic-mining gains? |
| K13 | 2 | **Full generative-negative model** | [Generative hard-negative mining](https://aclanthology.org/2023.findings-acl.362/) uses a sequence-to-sequence generator to produce diverse difficult negatives | Train only if K4 saturates; resolve generated strings to existing entity IDs and discard unresolved or potentially true candidates | Does a generator add useful hardness beyond retrieval-based mining? |
| K14 | 0 | **Inductive cross-lingual relation-alignment contrastive learning** | [SimRMKGC](https://link.springer.com/article/10.1007/s10489-025-06782-x) makes relation alignment a central supervised-contrastive objective on transductive DBP-5L | Encode relation labels, train-only endpoint prototypes, and neighbourhood summaries with BGE-M3; mine positive relation pairs only from aligned training concepts; compare relation-alignment only, entity-alignment only, their fixed-weight combination, and gradient-balanced multi-task training | Does relation supervision transfer across languages to unseen concepts without requiring test-entity embeddings or oracle alignments? |
| K15 | 1 | **Area-wise mixup hard negatives** | [SimRMKGC](https://link.springer.com/article/10.1007/s10489-025-06782-x) uses generated area-wise mixup hard negatives for relation alignment | Mix blocks or token-level vectors from two false-negative-filtered hard negatives, apply stop-gradient and L2 normalization, and exclude known facts, aligned concepts, rule-supported candidates, and type-compatible plausible positives | Do synthetic near-boundary negatives improve discrimination beyond K4 dynamic mining without moving training off the BGE embedding manifold? |

**KGC experiment controls.** Every experiment uses the same DBP5L-Ind v2 fold, description snapshot, candidate set, filtering rules, and seed. Report gains by language, evidence budget, relation frequency, description source, and rule/type coverage. For any auxiliary target derived from structure, recompute it from training triples only. Relation-alignment experiments use only training-concept alignments in the primary track; test alignments are restricted to a separately labelled oracle diagnostic. Screen K1–K6 and K14 independently against B0, then screen K15 only against B0 and the best alignment model. At most four surviving components enter a factorial combination study.

#### Work package 3 — TrustRouter

Let each expert $m$ produce score $s_m(q,c)$. A lightweight gate computes weights:

$$
s(q,c)=\sum_m w_m(z_q)s_m(q,c), \qquad \sum_m w_m(z_q)=1.
$$

The evidence vector $z_q$ uses measurable availability and confidence rather than treating language identity as the main signal:

- support-edge count, path availability, and local degree;
- description presence, source/provenance, length, and graph–text consistency;
- relation frequency and cardinality;
- expert entropy, score margin, and disagreement;
- relation-prototype confidence;
- cross-language retrieval/alignment confidence.

Training uses **counterfactual evidence dropout**: independently mask text, support edges, alignments, and prototypes; inject realistic text corruption; and require the gate to adapt. The objective combines ranking loss, evidence-consistency loss, and calibration/selective-risk loss.

The system produces both a link prediction and $p_{\mathrm{trust}}$. Below a validation-calibrated threshold it may:

1. down-weight or quarantine the description;
2. fall back to graph/name evidence;
3. abstain and request review.

Automatic text correction is part of the unified paper, but it is activated only after the detector and quarantine thresholds pass on held-out realistic validation data. RuleTrust and Semantic Smoothing may enter the final BGE expert or router features only after deterministic multi-seed validation.

#### Work package 4 — Realistic missing/corrupted evidence and closed-loop self-healing

Use separate difficulty levels:

1. **Missing:** description removed; name-only.
2. **Easy sanity:** random wrong-entity description.
3. **Hard semantic swap:** type-, language-, length-, and popularity-matched wrong entity.
4. **Claim-level corruption:** alter one verifiable date, location, type, occupation, creator, or relation while preserving fluent style.
5. **Multi-generator corruption:** descriptions generated by multiple model families/prompts, with source facts hidden or contradicted.
6. **Observed-source sample:** a source-verifiable sample of naturally missing, outdated, mistranslated, or incorrect multilingual descriptions.

Thresholds must be selected on validation data and evaluated on a disjoint test set. The minimum credible annotation target is 500 cases stratified across five languages; the preferred target is 1,000, with two annotators and adjudication. If bilingual verification is unavailable, narrow the claim rather than call model-generated project artifacts “in the wild.”

The self-healing controller then executes a logged state machine:

1. **Detect:** estimate contamination probability and prediction uncertainty.
2. **Decide:** keep, down-weight, quarantine, or abstain.
3. **Retrieve:** obtain candidate descriptions from an allowlist such as a fixed Wikipedia/Wikidata snapshot or another licensed authoritative source.
4. **Verify:** check source provenance, entity identity, claim-level consistency with trusted graph facts, cross-source agreement, and language quality.
5. **Repair:** accept only if the candidate passes a validation-calibrated threshold; otherwise retain quarantine or request review.
6. **Re-evaluate:** rerun affected KGC queries and a fixed factual QA/RAG set.
7. **Rollback:** reject the repair if clean controls regress, provenance is missing, or the repair fails downstream verification.

Compare verified retrieval against no repair, quarantine-only, name-only fallback, nearest-language transfer, and unconstrained LLM generation. Every repair must preserve the original text, replacement text, source URL/snapshot ID, verifier scores, decision, and rollback history.

#### Work package 4B — Literature-derived self-healing experiment portfolio

| ID | Priority | Experiment | Paper basis | Adaptation and required control |
|---|:---:|---|---|---|
| S1 | 0 | **Multi-signal contamination detector** | [CCA](https://ojs.aaai.org/index.php/AAAI/article/view/28729) combines textual and structural evidence to distinguish semantically similar errors | Compare BGE graph–text cosine, triplet-reconstruction confidence, type/schema violation, RuleTrust contradiction, model disagreement, and their calibrated ensemble. Ablate every signal and test hard type-matched corruption. |
| S2 | 0 | **Atomic-claim verification** | [FActScore](https://aclanthology.org/2023.emnlp-main.741/) decomposes text into atomic facts; [SAFE](https://papers.neurips.cc/paper_files/paper/2024/hash/937ae0e83eb08d2cb8627fe1def8c751-Abstract-Conference.html) verifies claims through search-augmented reasoning | Split each description into atomic claims; retrieve frozen-source evidence per claim; label supported, contradicted, or insufficient. Compare atomic verification with whole-description judging. Human-label a stratified test set. |
| S3 | 0 | **Retrieve-and-minimally-revise repair** | [RARR](https://aclanthology.org/2023.acl-long.910/) retrieves attribution and edits unsupported content while preserving the original | Compare deletion, full replacement, and minimal claim-level editing. Measure edit distance, supported-claim gain, preservation of already-correct claims, KGC recovery, and rollback rate. |
| S4 | 0 | **Multilingual source ensemble** | [M-NTA](https://aclanthology.org/2023.emnlp-main.100/) shows MT, web search, and LLMs each struggle alone and combines sources for multilingual KG text | Compare native Wikipedia/Wikidata, cross-language transfer, machine translation, approved web retrieval, and LLM synthesis. Require source attribution and two-signal agreement before acceptance. |
| S5 | 0 | **Calibrated LLM-as-a-judge panel** | [How Reliable is Multilingual LLM-as-a-Judge?](https://aclanthology.org/2025.findings-emnlp.587/) finds cross-language inconsistency and worse low-resource reliability | Compare pointwise and pairwise judging, original/repaired order swaps, native versus translated prompts, self-judge versus cross-model judge, and evidence-present versus evidence-absent prompts. Use two model families plus deterministic/NLI checks; calibrate against human labels per language. An LLM vote alone cannot accept a repair. |
| S6 | 0 | **Joint KGC↔KGE cycle-consistency verifier** | [KG-TRICK](https://aclanthology.org/2025.coling-main.611/) treats relational and textual completion as mutually beneficial | Accept a repair only if it improves description→relation/tail prediction and graph→description claim recovery while remaining source-supported. Compare source verification alone with source + cycle consistency. |
| S7 | 1 | **Human-example-conditioned RAG faithfulness judge** | [FaithJudge](https://aclanthology.org/2025.emnlp-industry.54/) uses diverse human-annotated hallucination examples to improve RAG faithfulness evaluation | Build a small multilingual bank of supported/unsupported QA answers; compare zero-shot judge, example-conditioned judge, NLI, and human decisions. Report judge accuracy and calibration before using it as a downstream metric. |
| S8 | 1 | **Realistic corruption curriculum** | [WETBench](https://aclanthology.org/2025.wikinlp-1.6/) studies realistic multilingual machine-generated text, while CCA motivates semantically similar errors | Train on easy random swaps only after including type-matched swaps, single-claim edits, mistranslations, stale dates, entity collisions, and multiple generators. Hold out corruption families to test transfer rather than memorization. |
| S9 | 1 | **Multilingual KG-grounded QA transfer** | [MultiHal](https://arxiv.org/abs/2505.14101) is a 2025 preprint with multilingual multi-hop KG paths for hallucination evaluation | Use it as external diagnostic evidence, not the primary benchmark. Compare plain QA, corrupted-KG RAG, quarantined-KG RAG, and repaired-KG RAG with fixed retrieval and generation settings. |
| S10 | 1 | **Conformal escalation policy** | [Conformal KGE answer sets](https://aclanthology.org/2025.naacl-long.32/) and [KGE Calibrator](https://aclanthology.org/2025.emnlp-main.1522/) motivate explicit coverage-controlled uncertainty | Use relation/language/evidence-budget calibration to choose automatic accept, quarantine, or human review. Measure empirical coverage, repair set size, automation rate, and false-repair rate. |
| S11 | 2 | **Judge disagreement as a training signal** | The [multilingual judge study](https://aclanthology.org/2025.findings-emnlp.587/) suggests disagreement itself is informative | Feed cross-model, cross-language, NLI, graph, and source disagreement to TrustRouter; test whether it predicts false repairs better than mean judge score. Do not add multi-agent generation unless this simple disagreement feature helps. |
| S12 | 0 | **Reliability-aware relation-alignment verifier** | [SimRMKGC](https://link.springer.com/article/10.1007/s10489-025-06782-x) shows that relation alignment improves multilingual completion when alignment supervision is available | Use relation-prototype agreement as both a detector feature and a repair acceptance signal. Corrupt 5%, 10%, and 20% of mined relation pairs; compare unweighted, similarity-weighted, RuleTrust-weighted, calibrated rejection, and quarantine-then-realignment policies. A repair cannot be accepted from relation agreement alone; source and claim verification remain mandatory. |

**Self-healing acceptance rule.** A proposed repair is accepted only when source provenance is valid, entity identity is resolved, atomic claims pass the selected verifier, the calibrated policy permits automatic action, and KGC/QA clean controls do not trigger rollback. LLM-as-a-judge is an experimental verifier and explanation generator, not ground truth. The primary test set remains human-adjudicated and hidden from prompt/example selection.

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

#### Repair and downstream recovery

- Repair precision, recall, acceptance rate, false-repair rate, and human-adjudicated factual correctness.
- Provenance coverage and verifier agreement for accepted repairs.
- KGC recovery: corrupted → quarantined → repaired MRR and Hits@k on the same queries.
- Clean preservation: change in KGC and detector behavior for untouched clean entities.
- Factual QA/RAG exact match or F1, citation correctness, and unsupported-answer rate before corruption, after corruption, after quarantine, and after verified repair.
- Repair efficiency: GPU time, retrieval calls, verifier calls, and human-review rate per accepted repair.
- Rollback rate and reasons.

#### External validation

- **PediaTypes:** multilingual DBpedia transfer with unseen nodes and relations; useful for external structural generalization.
- **Wikidata5M-Ind:** text-inductive sanity check for the text expert, with protocol differences stated explicitly.
- **WikiKGE-10/10++:** human-curated multilingual textual quality evaluation; use as an external description-quality resource, not as if it were the same KGC task.
- **WN18RR/FB15k-237/NELL:** implementation verification only, not primary evidence for the multilingual contribution.

### 6.6 Novelty

The proposed contributions are:

1. **DBP5L-Ind v2:** a concept-cluster-disjoint multilingual entity-inductive benchmark with matched inductive validation, fixed folds, explicit evidence budgets, train-time text provenance, alignment-free/oracle tracks, shortcut audits, and full head/tail ranking.
2. **A controlled BGE-M3/LoRA extension study:** Semantic Smoothing, RuleTrust, and leakage-safe cross-lingual relation-alignment contrastive learning adapted to a multilingual text bi-encoder and evaluated separately, jointly, and under missing/corrupted evidence.
3. **Counterfactual evidence-budget routing:** a query-specific mechanism trained to change expert reliance when text, structure, alignments, prototypes, or rules are removed or corrupted.
4. **Calibrated selective KGC:** reliability estimation, abstention, and text quarantine evaluated jointly with link prediction rather than reporting only a detector AUC.
5. **Verified self-healing:** a provenance-preserving detect → decide → retrieve → verify → repair → re-evaluate → rollback loop.
6. **Downstream recovery evidence:** multilingual KGC and focused factual QA/RAG measured before corruption, after corruption, after quarantine, and after verified repair.

Claims that should **not** be made:

- “first multilingual inductive KGC” without a tightly qualified scope;
- BGE-M3, LoRA, CRR, hard negatives, anchors, generic fusion, or generic MoE as novel;
- 2,359 LLM hallucinations or a 70% global contamination rate;
- “in-the-wild” detection based only on project-generated descriptions;
- superiority of Semantic Smoothing or RuleTrust without paired multi-seed controls;
- “self-healing” unless the complete validated loop improves downstream performance and preserves clean cases;
- superiority based on comparing full ranking with 50 sampled negatives.

### 6.7 Datasets

| Dataset/resource | Role | Required treatment |
|---|---|---|
| **DBP-5L** (EN, FR, ES, JA, EL) | Core source for DBP5L-Ind v2 | Rebuild concept-disjoint folds; preserve all relation IDs; version alignments and text provenance |
| **E-PKG** (DE, EN, ES, FR, IT, JA) | Optional external transductive test for relation-alignment transfer | Use only for external KGC validation; do not use as the primary verified-repair benchmark because authoritative entity-level source provenance is not guaranteed |
| **Current DBP-5L-Ind** | Diagnostic only | Do not use as final benchmark; retain to quantify how corrections change results |
| **PediaTypes EN↔FR/DE** | External multilingual fully inductive validation | Use its published protocol and report sampled/full-ranking differences |
| **Wikidata5M-Ind** | External text-inductive validation | Do not compare raw MRR across different candidate universes |
| **WikiKGE-10 / WikiKGE10++** | External multilingual text-quality evidence | Use human-curated names/descriptions to validate quality signals |
| **Verified repair and QA set** | Closed-loop evaluation | Build from source-verifiable natural/realistic corruptions; freeze questions, evidence, gold answers, and citations before repair |
| **WN18RR / FB15k-237 / NELL inductive splits** | Structural implementation checks | Persist candidates and separate these results from DBP-5L claims |
| **1,042 generated descriptions** | Corruption research material | Exclude from clean training; label source/model/prompt; verify a stratified subset |

DBP-5L’s published per-language graph sizes are approximately 80,167 triples for EN, 49,015 FR, 54,066 ES, 28,774 JA, and 13,839 EL ([SS-AGA dataset table](https://aclanthology.org/2022.acl-long.36.pdf)). The current local split contains 118,256 training triples, 13,137 validation triples, 54,473 inductive test triples, and 39,995 support edges across five languages. These local counts should be regenerated and hashed after the split redesign.

**SimRMKGC resource audit.** SimRMKGC uses the standard transductive DBP-5L and E-PKG datasets, not DBP5L-Ind v2. The public [DBP-5L files](https://github.com/stasl0217/KEnS/tree/main/data) contain per-language entities, train/validation/test triples, seed entity alignments, and the relation vocabulary; the associated [KEnS repository](https://github.com/stasl0217/KEnS) is an older baseline, not SimRMKGC code. The public [E-PKG files](https://github.com/amzn/ss-aga-kgc/tree/main/EPKG_DATA) and [SS-AGA code](https://github.com/amzn/ss-aga-kgc) likewise predate SimRMKGC. The SimRMKGC paper's Data Availability statement links these datasets but no official implementation, and no public repository under the exact method name or title was found as of 17 July 2026. Therefore K14, K15, and S12 require a clean-room reimplementation of the verified mechanisms rather than importing an unverified third-party reproduction.

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
| Priority-0 KGC portfolio screening (K1–K6) | 70–120 | RTX 5070 Ti |
| Paired confirmation of BGE variants, 3 seeds | 40–80 | RTX 5070 Ti / 96 GB GPU |
| One or two structural baselines on corrected splits | 40–80 | 96 GB GPU preferred |
| Static fusion, oracle selector, TrustRouter, calibration | 40–70 | Either GPU |
| Priority-0 self-healing portfolio (S1–S6) | 60–100 | Either GPU + CPU |
| Evaluation, bootstrap, robustness curves | 5–15 | GPU + CPU |
| **Unified paper total** | **335–545** | staged across both GPUs |
| Optional Priority-1 screening | +40–80 | Only after Priority-0 gates |

These are engineering estimates and should be recalibrated after one profiled English run. A safe upper allocation is **650 GPU-hours**, but one-seed screening must eliminate weak variants before three-seed confirmation. Only B0 and at most four surviving KGC components receive factorial and multi-seed evaluation. Priority-1 experiments do not begin until the corresponding Priority-0 gate passes.

#### CPU, RAM, disk, and human resources

- **CPU:** 16–32 cores for split construction, graph partitioning, PPR audits, subgraph extraction, and bootstrap analysis.
- **RAM:** 32 GB minimum; 64 GB recommended. The current WSL 15 GB allocation may bottleneck structural preprocessing.
- **Storage:** reserve 250 GB for data, dense/sparse/multi-vector caches, manifests, rank dumps, repair evidence, judge traces, and checkpoints. Save LoRA adapters rather than 1.14 GB copies of the frozen encoder.
- **Annotation:** approximately 100–250 annotator-hours for 500–1,000 twice-labeled multilingual corruption/repair cases plus a focused factual-QA set, depending on verification difficulty and adjudication.
- **LLM/search budget:** track tokens, retrieval calls, judge calls, and cost per verified repair. Cache source evidence and judge prompts; never let changing web results enter a frozen test run.
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

#### Phase 2 — Clean baselines and BGE experimentation (4–7 weeks)

- Run lexical/PPR, mBERT, XLM-R, clean BGE-M3/LoRA, one structural KGFM, relation-anchor, and static-fusion baselines.
- Screen BGE objective, hard-negative, relation-template, and prototype variants.
- Evaluate BGE-M3 dense, sparse, multi-vector, and hybrid scoring before adding new encoders.
- Screen structure-aware contrastive tasks, schema-guided negatives, false-negative-safe dynamic mining, calibration/conformal sets, and joint link-description completion.
- Screen SimRMKGC-derived relation-alignment contrastive training; compare entity-only, relation-only, fixed joint, and gradient-balanced joint losses. After selecting the best alignment model, sweep 0/10/30/50/100% training-alignment availability and only then test area-wise mixup negatives.
- Test Semantic Smoothing, RuleTrust loss weighting, RuleTrust score adaptation, and their combination.
- Use one seed for screening, then at least three paired seeds for the locked baseline and surviving variants.

**Gate G2:** the clean BGE baseline is reproducible; every surviving extension beats its matched control in clean or robust macro-MRR/calibration with a paired confidence interval; shuffled/zero-weight controls pass. Weak variants are removed rather than accumulated, and at most four components proceed to combination experiments.

#### Phase 3 — Reliability, routing, and corruption benchmark (3–5 weeks)

- Build held-out missing, natural, and realistically corrupted evidence with multilingual annotation.
- Train TrustRouter with counterfactual evidence dropout.
- Compare standard calibration, KGE-specific calibration, and relation/language/evidence-budget conformal answer sets.
- Evaluate calibration, empirical coverage, set size, risk–coverage, robust macro-MRR, and quarantine decisions.

**Gate G3:** TrustRouter beats the best single expert and tuned static fusion under corruption, while clean MRR drops by no more than 0.5 absolute points and detector thresholds remain fixed from validation.

#### Phase 4 — Verified self-healing loop (3–5 weeks)

- Implement the Priority-0 detector and verifier portfolio: multi-signal detection, atomic claims, source retrieval, minimal revision, multilingual source ensemble, LLM-judge calibration, KGC↔KGE cycle consistency, and reliability-aware relation-alignment verification.
- Implement source-allowlisted retrieval, provenance capture, graph-text verification, accept/reject thresholds, and rollback.
- Compare no repair, quarantine-only, name-only, cross-language transfer, unconstrained generation, and verified retrieval.
- Re-evaluate KGC after every intervention and audit false repairs on clean controls.

**Gate G4:** accepted repairs are source-verifiable, improve post-corruption KGC over quarantine-only with paired confidence intervals, and do not cause a statistically meaningful clean-case regression. If this gate fails, the system may be called self-auditing but not self-healing.

#### Phase 5 — Downstream recovery, external validation, and writing (3–5 weeks)

- Build one focused multilingual factual QA/RAG evaluation tied to the affected entities and relations.
- Measure before corruption, after corruption, after quarantine, and after verified repair.
- Validate the main reliability or repair conclusion on PediaTypes and/or one human-curated multilingual text resource.
- Freeze tables, claims, model/data cards, repair logs, and the reproducibility package.

**Gate G5:** verified repair improves factual QA/RAG over both corrupted and quarantine-only conditions, preserves citation correctness and clean controls, and at least one main conclusion holds outside DBP5L-Ind v2.

## 7. What to keep, park, and stop claiming now

### Keep, repair, and extend

- BGE-M3/LoRA training pipeline and full evaluator.
- mBERT baseline and clean description source work.
- S2DN reproduction as an implementation appendix or structural baseline.
- Rule mining as both a BGE training/ranking feature and an optional router expert.
- Semantic Smoothing adapted to BGE-M3 through soft targets, prototypes, or cross-view consistency.
- The contamination observation as motivation and a hypothesis.
- Detection, quarantine, source-verified repair, rollback, and one downstream factual QA/RAG task as one closed loop.
- The failure ledger, provided it is tied to immutable runs.

### Park from the primary critical path

- Finishing every S2DN split before multilingual work.
- More than one downstream QA/RAG benchmark before the focused task is valid.
- Large generative repair models when verified retrieval or name-only fallback is sufficient.
- Automatic repair of zero-edge entities without external evidence.

### Retract or relabel until proven

- Relabel 26.51 ± 0.31 as **old-description/provisional**.
- Relabel AUC 0.995 as **random-swap sanity benchmark**.
- Relabel +1.95 JA as **one-checkpoint evaluation-time text replacement**, not repair causality.
- Replace “first multilingual inductive benchmark” with a precise, qualified scope after the PediaTypes comparison.
- Treat Semantic Smoothing and RuleTrust as proposed BGE experiments until paired controls demonstrate value.
- Use “self-healing” as the target system name, but make the final scientific claim conditional on passing Gates G4 and G5.

## 8. Final recommendation

The project should proceed as **one unified paper on evidence-budgeted, self-healing multilingual inductive KGC**. DBP5L-Ind v2 remains the scientific foundation; BGE-M3/LoRA experimentation supplies the main text method; TrustRouter supplies calibrated decisions; and the verified repair loop supplies the self-healing claim.

The best paper story is:

1. Existing evaluation cannot tell whether multilingual inductive systems truly generalize or which evidence they trust.
2. DBP5L-Ind v2 fixes concept leakage, evidence budgets, text provenance, shortcut risk, and evaluation comparability.
3. BGE-M3/LoRA is strengthened and stress-tested through its native dense/sparse/multi-vector modes, structure/schema-aware contrastive learning, calibrated uncertainty, joint link-description learning, Semantic Smoothing, and RuleTrust.
4. TrustRouter uses calibrated or conformal uncertainty to choose between use, fallback, quarantine, abstention, and human escalation.
5. The system decomposes suspect text into claims, retrieves and verifies replacement evidence, minimally repairs or replaces it, accepts or rolls back the change, and measures KGC recovery.
6. Accepted repairs improve one focused factual QA/RAG task without damaging clean cases.
7. The result is validated across languages, evidence budgets, corruption types, and an external resource.

This remains one paper only if the closed loop passes the gates. The benchmark, BGE experiments, detector, and repair system must share the same entities, evidence states, evaluator, and central hypothesis; unrelated S2DN reproduction details belong in an appendix. If verified repair or downstream recovery fails, the submission must narrow its title and claims to reliability-aware/self-auditing KGC rather than presenting an incomplete loop as self-healing.

## 9. Previous work and results to date

This section records what had actually been completed by 17 July 2026. It distinguishes measured results from planned work. The primary evidence sources are the [results and inference ledger](RESULTS_AND_INFERENCE.md), the [project story and plan](PROJECT_STORY_AND_PLAN.md), the [S2DN implementation ladder](pivot/IMPLEMENTATION_PLAN_S2DN_LADDER.md), the [RuleTrust experiment ledger](pivot/RULETRUST_EXPERIMENT_LEDGER.md), and the [first detector report](pivot/self_healing_detector_result_2026-07-07.md).

### 9.1 Repository, data, and benchmark construction

The project was organized as a Windows-side research and documentation repository with a committed [WSL training snapshot](../wsl/README.md). The training snapshot contains the multilingual text pipeline, DBP-5L data products, S2DN reproduction, experiment launchers, logs, and result artifacts.

An entity-disjoint inductive version of DBP-5L was built for English, French, Spanish, Japanese, and Greek. Approximately 20% of the entities in each language were held out from training. The resulting local split contains the following counts, recorded in [`stats.json`](../wsl/research_kg/DBP5L/ind/stats.json):

| Language | Total entities | Train entities | Unseen test entities | Train triples | Validation triples | Test triples | Support triples |
|---|---:|---:|---:|---:|---:|---:|---:|
| EN | 13,132 | 10,506 | 2,626 | 44,801 | 4,977 | 18,409 | 11,980 |
| FR | 10,074 | 8,060 | 2,014 | 25,968 | 2,885 | 11,154 | 9,008 |
| ES | 10,108 | 8,087 | 2,021 | 26,902 | 2,989 | 15,094 | 9,081 |
| JA | 7,473 | 5,979 | 1,494 | 13,531 | 1,503 | 7,237 | 6,503 |
| EL | 4,020 | 3,216 | 804 | 7,054 | 783 | 2,579 | 3,423 |
| **Total** | **44,807** | **35,848** | **8,959** | **118,256** | **13,137** | **54,473** | **39,995** |

The completed data work includes:

- the [DBP-5L inductive split builder](../wsl/research_kg/scripts/data_prep/build_dbp5l_ind.py);
- multilingual entity-description construction and coverage analysis;
- support graphs for unseen entities;
- a [DBP-5L-to-GraIL/S2DN converter](../wsl/research_kg/scripts/data_prep/convert_dbp5l_to_grail.py);
- filtered evaluation with support triples included as known true facts; and
- within-language and all-language candidate ranking modes.

This is a working research benchmark, but it is not yet the proposed DBP5L-Ind v2. The current split still requires the concept-level leakage, provenance, PPR-shortcut, inverse-relation, and deterministic-manifest repairs specified earlier in this proposal.

### 9.2 BGE-M3/LoRA multilingual inductive KGC baseline

The main completed text model is a BGE-M3 bi-encoder fine-tuned with LoRA. It encodes an unseen head's description and relation as a query and ranks candidate tail descriptions. The strongest configuration uses CRR, seven hard negatives, LoRA rank 16, and a maximum sequence length of 160 tokens.

The controlled ablation path was:

| Stage | Main addition | Filtered within-language MRR | Change |
|---|---|---:|---:|
| Zero-shot BGE-M3 | No task fine-tuning | 1.45 | — |
| Row3-HN | CRR + hard negatives, length 96 | 13.77 | +12.32 |
| A | Enriched descriptions, length 128 | 23.80 | +10.03 |
| B | LoRA rank 16 | 25.15 | +1.35 |
| E | Length 160 | 26.69 | +1.54 |

The single-reference Run E achieved 26.69 MRR, 18.80 Hits@1, 29.43 Hits@3, and 41.62 Hits@10. Its per-language MRR was 35.93 FR, 37.32 ES, 16.98 EN, 18.42 EL, and 17.90 JA.

Three independent seeds produced MRR values of 26.24, 26.85, and 26.45. The resulting headline was **26.51 ± 0.31 MRR**, with **18.35 ± 0.52 Hits@1** and **41.76 ± 0.28 Hits@10**. Per-language three-seed MRR was 37.29 FR, 36.55 ES, 17.19 EN, 16.79 EL, and 16.15 JA. This result is stable, but it was trained on the old description collection and must therefore remain labelled provisional until the clean three-seed retrain is complete.

The main empirical findings were:

- Wikipedia-style descriptions increased MRR from 3.10 to 10.02, showing that rich text was the largest early driver.
- CRR alone was similar to InfoNCE on rich text, but CRR combined with hard negatives reached 13.77 MRR.
- Increasing context length from 128 to 160 raised MRR from 25.15 to 26.69. The gain was concentrated in Japanese and Greek.
- A stale global-negative cache reduced MRR to 21.56 despite approximately 95% training accuracy, demonstrating harmful label noise or memorization.
- Extending training to 40 epochs reduced MRR to 23.43, indicating overfitting.

For statistical validation, the full recipe exceeded the pre-enrichment Row3-HN model by 12.67 MRR with a paired 95% bootstrap confidence interval of [12.41, 12.94]. The length-160 model exceeded length 128 by 1.30 MRR with a bootstrap interval of [1.11, 1.49], although the one-sided Wilcoxon result was not significant (`p = 0.31`), meaning that the gain was concentrated rather than uniform across queries.

### 9.3 Baselines and cross-lingual evaluation

An mBERT baseline was run using the same CRR, hard-negative, LoRA, description, and evaluation recipe. It achieved 24.08 overall MRR, compared with the provisional BGE-M3 three-seed mean of 26.51. The per-language comparison was:

| Language | mBERT-clean MRR | BGE-M3 provisional MRR | Difference |
|---|---:|---:|---:|
| EN | 16.75 | 17.19 | +0.44 |
| FR | 35.17 | 37.29 | +2.12 |
| ES | 31.25 | 36.55 | +5.30 |
| JA | 15.50 | 16.15 | +0.65 |
| EL | 10.63 | 16.79 | +6.16 |
| **Overall** | **24.08** | **26.51** | **+2.43** |

This comparison supports BGE-M3, especially for Greek and Spanish, but it is not fully apples-to-apples until the BGE-M3 clean retrain is finished.

The all-language evaluator ranked each answer against 56,589 multilingual candidates. Across three seeds, within-language MRR was 26.51 ± 0.31 and all-language MRR was 26.01 ± 0.30, a reduction of only 0.50. Hits@10 changed from 41.76 to 40.93. This indicates that the encoder rarely ranks an entity from the wrong language above the correct answer.

A relation-anchor experiment initially appeared to collapse from 15.59 to 3.17 MRR. The cause was a train/evaluation mismatch: the model was trained with anchor-augmented queries but evaluated with bare queries. Matched anchor-aware evaluation reached 20.38 MRR, while the bare-query control reached 3.84. The original negative conclusion was retracted; a controlled anchor study is still pending.

### 9.4 Evaluation and reproducibility fixes

Several important engineering errors were identified and corrected before publication:

1. The evaluator hardcoded a sequence length of 96 even for models trained at 128 or 160. Correcting it raised Run B from 15.59 to 24.76 MRR and established that length 160, not 128, was the better setting.
2. The filter map omitted 39,995 support triples. Of the test queries, 25.25% had a support-tail that should have been filtered. Adding support facts raised the strongest model from 26.26 to 26.69 MRR and Row3-HN from 11.36 to 13.77.
3. Anchor-trained queries were evaluated in the wrong format. Matched evaluation changed the anchor result from an apparent 3.17 MRR failure to 20.38 MRR.
4. The S2DN release contained a hardcoded learning rate that overrode the command line. One 4-hour-46-minute run was invalidated; later runs verified the logged hyperparameters rather than trusting the launch command.

These fixes are part of the contribution's reproducibility record: they prevent attractive but false conclusions from entering the paper.

### 9.5 Description audit and clean-description repair

The first description collection included 1,042 descriptions generated with Llama 3.2 3B for low-resource Greek and Japanese entities. A manual audit of 25 Greek examples found approximately 17 clearly hallucinated, three partially correct, and five accurate: an error rate close to 70%. Proper names were often converted into plausible but false biographies.

An evaluation-time removal test replaced unverifiable English back-fill for 2,359 Greek and Japanese entities. Without retraining, overall MRR increased from 26.69 to 26.94, Japanese MRR increased from 17.90 to 19.85 (**+1.95**), Greek changed from 18.42 to 18.33 (-0.09), and the untouched languages remained identical. This is evidence that the contaminated descriptions hurt ranking, but it is not yet a clean-retraining causal result.

A clean description file was then constructed. Of the 2,359 affected entities, 1,070 (45%) recovered a native-language Wikipedia summary and 1,289 (55%) fell back to the native entity name. LLM-generated and unverifiable cross-lingual English fallback text was removed. The clean three-seed BGE-M3 retrain remains pending.

### 9.6 Graph-text contamination detector

A training-free detector was implemented using BGE-M3 cosine similarity between an entity description and a serialization of its graph neighborhood. Lower agreement indicates possible contamination.

On a controlled set of 400 clean versus wrong-entity description pairs, mean cosine similarity was 0.885 for clean descriptions and 0.663 for injected descriptions. The detector achieved:

- ROC-AUC: **0.995**;
- best threshold: **0.773**;
- precision: **0.985**;
- recall: **0.990**; and
- F1: **0.988**.

For 40 real Llama-generated fabrications with at least two graph edges, the mean score was 0.761 and 23 of 40 (57%) were flagged at the same threshold. The strong AUC must be described as a random wrong-entity injection sanity benchmark, not as proof of realistic contamination detection. The 57% result exposes the central coverage limitation: the most contaminated entities often have almost no graph structure to audit.

### 9.7 S2DN reproduction

The structural branch reproduced S2DN on the GraIL inductive splits. WN18RR v1-v4 completed with the following average:

| Result | MRR | Hits@1 | Hits@5 | Hits@10 |
|---|---:|---:|---:|---:|
| Reproduced WN18RR v1-v4 average | 73.77 | 69.12 | 77.36 | 80.57 |
| S2DN paper reference | — | — | — | 81.23 |

The reproduced average Hits@10 was 0.66 points below the paper. Individual v1 results were 79.95 MRR, 74.73 Hits@1, 84.84 Hits@5, and 87.23 Hits@10; v3, the hardest split, reached 57.02 MRR and 68.84 Hits@10.

On FB15k-237 v1, the corrected paper-parameter run achieved 53.13 MRR, 44.63 Hits@1, 61.22 Hits@5, and 67.80 Hits@10. The paper reported 52.10 MRR, 43.68 Hits@1, and 67.34 Hits@10, so the reproduction was +1.03 MRR, +0.95 Hits@1, and +0.46 Hits@10 above the paper's v1 result.

FB15k-237 v2 with paper settings did not fit the 16 GB RTX 5070 Ti, and NELL v1-v4 was not completed. Therefore S2DN is reproduced on WN18RR v1-v4 and FB15k-237 v1, not across the entire benchmark suite.

### 9.8 RuleTrust work

RuleTrust was implemented as an entity-independent symbolic score added to the S2DN graph score through one learnable scalar initialized at zero. The model size increased from 122,896 to 122,897 parameters. The rule miner was improved from 142 rules covering 62 of 180 head relations to 462 rules covering 93 relations.

On FB15k-237 v1, with the target edge removed, rule support occurred for 38.8% of positive training subgraphs and 36.1% of positive unseen-entity test cases, compared with 0.8% and 0.1% of negatives. Rule-only AUC was 0.690 on training cases and 0.680 on inductive test cases, showing that the relation-level signal transfers to unseen entities.

The completed single-seed experiments were:

| Run | Learned rule scale | Validation AUC | MRR | Hits@1 | Hits@10 |
|---|---:|---:|---:|---:|---:|
| S2DN baseline | — | 0.8527 | 53.13 | 44.63 | 67.80 |
| RuleTrust | 3.90 | 0.8586 | 53.19 | 44.15 | 71.22 |
| Shuffled-rule control | 0.12 | 0.8317 | 51.03 | 41.22 | 70.00 |

The real-rule run raised Hits@10 by 3.42 and MRR by 0.06, while Hits@1 fell by 0.49. The learned scale of 3.90, versus 0.12 for shuffled rules, shows that the model distinguishes genuine from corrupted rules. However, the shuffled control moved MRR by -2.10 and Hits@10 by +2.20 despite nearly ignoring its rules. On the 205-triple test set, this variance is larger than the apparent effect. Consequently, RuleTrust has a verified live mechanism but **no defensible ranking improvement yet**; paired three-to-five-seed validation on a locked design remains required.

### 9.9 Semantic Smoothing status

The original S2DN Semantic Smoothing module is present in the reproduced S2DN architecture. A new similarity-guided Semantic Smoothing modification was designed as a second research branch, but it has not yet been implemented and evaluated as a controlled contribution in BGE-M3/LoRA. The revised plan now makes this a formal BGE experiment through soft-target smoothing, relation-prototype consistency, and cross-view consistency. It will be tested against the clean baseline, alone, with RuleTrust alone, and with both combined. These remain proposed experiments—not completed results—and must pass the controls and selection rule in Work Package 2B.

### 9.10 Current evidence boundary

The completed work establishes a functioning multilingual inductive dataset, a stable provisional BGE-M3/LoRA result, an mBERT comparison, cross-lingual evaluation, a partial S2DN reproduction, a live but statistically unproven RuleTrust mechanism, a real description-contamination finding, and a strong controlled detector sanity check.

It does not yet establish a clean three-seed BGE-M3 headline, a leakage-audited DBP5L-Ind v2 benchmark, a RuleTrust performance gain, a new Semantic Smoothing gain, realistic contamination detection, automatic verified repair, or external-dataset generalization. Those are the remaining experiments governed by the gates in Section 6.9.
