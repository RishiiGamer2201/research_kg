# AAAI Research Paper Summaries

This document contains structured summaries of the 37 research papers found in `C:\Users\seast\Downloads\Research`.

---

## Batch 1: Papers 1–13 (01118 to 06924)

### 1. `01118-DingL.txt` — Global-Topological Relation Graph (TARGI)
* **Title:** Towards Global-Topological Relation Graph for Inductive Knowledge Graph Completion
* **Authors:** Ling Ding, Lei Huang, Zhizhi Yu*, Di Jin, Dongxiao He (Tianjin University)
* **Problem/Motivation:** Existing inductive KGC methods mainly focus on new entities while relations are randomly initialized, overlooking semantic correlations between relations. They also suffer from excessive reliance on relation degree and limited scope of enclosing subgraph sampling.
* **Method:** Proposes TARGI — constructs a global relation graph for each topology (6 topological patterns: HEAD, TAIL, BOTH, LOOP, PARA, SIBL) from a global graph perspective, leveraging invariance of relation structures. Uses a relation-weighted aggregator on these graphs to learn rich embeddings for new relations and entities.
* **Key Results:** Outperforms 15 SOTA methods on six inductive datasets, especially on two fully inductive datasets (FB-100, NL-100).
* **Notable Findings:** Topological structures between relation pairs vary significantly — most relation pairs exhibit 3 types of topological structures simultaneously; neglecting these leads to degraded performance.

---

### 2. `01711-LongX.txt` — EPERM
* **Title:** EPERM: An Evidence Path Enhanced Reasoning Model for Knowledge Graph Question and Answering
* **Authors:** Xiao Long, Liansheng Zhuang*, Aodi Li, Minghong Yao, Shafei Wang (USTC, Peng Cheng Laboratory)
* **Problem/Motivation:** Existing retrieval-augmented KGQA methods treat all retrieved information equally, ignoring the varying importance of different structural knowledge for reasoning. They also lack coupling between retrieval and reasoning stages.
* **Method:** Reformulates KGQA as a probabilistic graphical model with three stages: (1) Subgraph Retrieval (fine-tuned LLM); (2) Evidence Path Finding (scores/filters evidence paths); (3) Answer Prediction (reasons over weighted paths). Uses a joint fine-tuning strategy to couple retrieval and reasoning.
* **Key Results:** Achieves superior performance on benchmark KGQA datasets, with a 3.6% relative improvement in Hit@1 on WebQSP compared to SOTA methods.
* **Notable Findings:** The unified graphical model formulation creates stronger coupling between retrieval and reasoning stages, enabling the model to better leverage structural information importance.

---

### 3. `01877-MengF.txt` — DOGE
* **Title:** DOGE: LLMs-Enhanced Hyper-Knowledge Graph Recommender for Multimodal Recommendation
* **Authors:** Fanshen Meng, Zhenhua Meng, Ru Jin, Rongheng Lin*, Budan Wu (Beijing University of Posts and Telecommunications)
* **Problem/Motivation:** Current multimodal recommender systems over-rely on text modality features, underutilize image features, and rely solely on item similarity propagation in vector space, failing to capture strong real-world associations between item groups.
* **Method:** Uses multimodal LLMs to understand image information guided by text, generating cross-modal features that enhance text-image relationships. Constructs a Hyper-Knowledge Graph (HKG) encompassing user-item interactions and enhanced modality features with item-item and user-user binary/hyper-relations.
* **Key Results:** SOTA performance on three public real-world datasets with an average 7.2% improvement over the strongest baseline.
* **Notable Findings:** Cross-modal feature enhancement through LLMs effectively bridges the gap between text and image modalities, and hyper-relational knowledge graphs capture richer item associations than simple similarity propagation.

---

### 4. `02237-ZhangS.txt` — 5EL Model
* **Title:** Integrating Large Language Models and Möbius Group Transformations for Temporal Knowledge Graph Embedding on the Riemann Sphere
* **Authors:** Sensen Zhang, Xun Liang*, Simin Niu, Zhendong Niu, Bo Wu, et al. (Renmin University of China, BIT, and others)
* **Problem/Motivation:** Existing TKGE methods rely on single embedding spaces whose geometric properties limit their ability to model intricate temporal patterns (hierarchical and ring structures). LLM-based approaches focus on semantics without adequately considering temporal relationship patterns.
* **Method:** Proposes the 5EL model — embeds TKGs into projective geometric space on the Riemann Sphere, using Möbius Group transformations (translation, rotation, homothety, inversion, reflection) to model complex temporal patterns. Then uses LLMs with parameter-efficient fine-tuning to extract crucial temporal node information and enrich representations.
* **Key Results:** Significantly outperforms existing models on five advanced TKG datasets for both link prediction and time prediction tasks.
* **Notable Findings:** Projective geometric space with Möbius transformations can simultaneously capture chain, hierarchy, and ring relational patterns — a capability that single-space embeddings lack.

---

### 5. `02266-LvK.txt` — Keypoint-Based KG for Vehicle Re-ID
* **Title:** Infer the Whole from a Glimpse of a Part: Keypoint-Based Knowledge Graph for Vehicle Re-Identification
* **Authors:** Kai Lv, Yunlong Li, Zhuo Chen, Shuo Wang, Sheng Han, Youfang Lin* (Beijing Jiaotong University, Zhejiang University)
* **Problem/Motivation:** Vehicle re-identification across non-overlapping cameras struggles with view-invariance — discriminative parts obscured by viewpoint changes cannot contribute to matching when comparing different orientations.
* **Method:** Constructs a vehicle knowledge graph encoding structural relationships between 20 vehicle keypoints. Given partial visible regions, a transformer-based inference model infers features for invisible keypoints conditioned on visible correspondences defined in the knowledge graph.
* **Key Results:** Outperforms SOTA on standard vehicle re-ID benchmarks (VeRi-776, VehicleID) under cross-view matching scenarios.
* **Notable Findings:** First work introducing structural priors via keypoint knowledge graphs for view-invariant vehicle re-ID. Mimics human cognitive ability to "infer the whole from a glimpse of a part."

---

### 6. `02908-ChenK.txt` — LLM-DR
* **Title:** LLM-DR: A Novel LLM-Aided Diffusion Model for Rule Generation on Temporal Knowledge Graphs
* **Authors:** Kai Chen*, Xin Song*, Ye Wang†, Liqun Gao, Aiping Li†, Xiaojuan Zhao, Bin Zhou, Yalong Xie (NUDT, Hunan University)
* **Problem/Motivation:** Rule-based TKG extrapolation methods face a vast search space for rule extraction, and LLM-based rule generation suffers from prompt sensitivity and hallucinations, leading to unreliable rule quality.
* **Method:** Proposes LLM-DR — uses conditional diffusion models in classifier-free guidance fashion to generate new rules consistent with source data distribution, refined with LLM-based semantic constraints. Employs a coarse-to-fine evaluation strategy (coarse-grained LLM filtering, fine-grained scoring).
* **Key Results:** Surpasses SOTA TKG extrapolation methods.
* **Notable Findings:** Combining diffusion models (for controllable, distribution-aware generation) with LLMs (for semantic evaluation) provides a more reliable rule generation pipeline than using LLMs alone.

---

### 7. `03121-MaT.txt` — S2DN
* **Title:** S2DN: Learning to Denoise Unconvincing Knowledge for Inductive Knowledge Graph Completion
* **Authors:** Tengfei Ma, Yujie Chen, Liang Wang, Xuan Lin, Bosheng Song*, Xiangxiang Zeng (Hunan University, Chinese Academy of Sciences, Xiangtan University)
* **Problem/Motivation:** Inductive KGC methods suffer from: (1) semantic inconsistencies of similar relations (e.g., "located in" vs "lie in"), and (2) noisy interactions in KGs from unconvincing knowledge for emerging entities.
* **Method:** Proposes S2DN (Semantic Structure-aware Denoising Network): (1) Semantic smoothing module generalizes similar relations by blurring semantics over enclosing subgraphs; (2) Structure refining module filters unreliable interactions and provides additional knowledge, retaining robust structure around target links.
* **Key Results:** Surpasses SOTA on three benchmark KGs and demonstrates superior robustness under various noise levels.
* **Notable Findings:** Addresses inductive KGC from a novel semantic-structure synergy perspective; smoothing semantically similar relations improves consistency while structure refinement filters noise adaptively.

---

### 8. `03298-WangZ.txt` — FULORA (Dual Agents)
* **Title:** Walk Wisely on Graph: Knowledge Graph Reasoning with Dual Agents via Efficient Guidance-Exploration
* **Authors:** Zijian Wang, Bin Wang*, Haifeng Jing, Huayu Li, Hongbo Dou (China University of Petroleum)
* **Problem/Motivation:** Multi-hop reasoning approaches suffer from: (1) sparse rewards making it hard for agents to learn effective policies early; (2) poor performance on sparse KGs requiring long reasoning paths.
* **Method:** Proposes FULORA — a dual-agent framework based on hierarchical reinforcement learning (HRL). High-level agent (GIANT) walks on a simplified KG to provide stage-wise hints. Low-level agent (DWARF) walks on the original KG, optimizing a value function balancing return maximization and efficient guidance integration.
* **Key Results:** Outperforms RL-based baselines on three real-world KG datasets, especially in long-distance reasoning tasks.
* **Notable Findings:** The key innovation is enabling DWARF to make independent decisions while receiving meaningful guidance from GIANT, rather than being forced to adopt similar policies.

---

### 9. `03862-HamzaA.txt` — KG-RAG for Medical NLE
* **Title:** LLaVA Needs More Knowledge: Retrieval Augmented Natural Language Generation with Knowledge Graph for Explaining Thoracic Pathologies
* **Authors:** Ameer Hamza, Abdullah, Yong Hyun Ahn, Sungyoung Lee, Seong Tae Kim* (Kyung Hee University)
* **Problem/Motivation:** Generating Natural Language Explanations (NLEs) for medical image predictions is challenging because general models lack domain-specific medical knowledge, and retrieval-based methods raise privacy concerns.
* **Method:** Proposes a Vision-Language framework augmented with a KG-based datastore (KG-RAG). The KG abstracts patient-specific details, preserving privacy while providing domain-specific knowledge. Implemented in three frameworks: KG-LLaVA (LLaVA + KG-RAG), Med-XPT, and Bio-LLaVA.
* **Key Results:** Achieves SOTA results on the MIMIC-NLE dataset across all three framework variants.
* **Notable Findings:** First KG retrieval-augmented VLM framework for thoracic pathology NLEs. The KG-based approach addresses privacy concerns by avoiding direct patient data retrieval.

---

### 10. `05582-JianY.txt` — APKGC
* **Title:** APKGC: Noise-enhanced Multi-Modal Knowledge Graph Completion with Attention Penalty
* **Authors:** Yue Jian, Xiangyu Luo, Zhifei Li*, Miao Zhang, Yan Zhang, Kui Xiao, Xiaoju Hou (Hubei University, Guangdong Industry Polytechnic University)
* **Problem/Motivation:** Multimodal KGC methods face: (1) lack of robustness — treating noise purely as interference rather than leveraging it; (2) attention partial over-trust — language models assign disproportionately high attention to semantically meaningless tokens.
* **Method:** Proposes APKGC with two strategies: (1) Adaptive noise sampling — dynamically samples noisy multimodal information during training; (2) Attention over-trust penalty — penalizes attention scores of tokens with disproportionately high attention.
* **Key Results:** Improves Hit@1 by 3.3% on DB15K and 3.4% on MKG-W compared to existing SOTA MMKGC models.
* **Notable Findings:** Counter-intuitively, incorporating noise as a training signal rather than rejecting it improves model robustness.

---

### 11. `05893-TangX.txt` — MAB-enhanced RAG
* **Title:** Adapting to Non-Stationary Environments: Multi-Armed Bandit Enhanced Retrieval-Augmented Generation on Knowledge Graphs
* **Authors:** Xiaqiang Tang, Jian Li*, Nan Du, Sihong Xie* (HKUST Guangzhou, Tencent Hunyuan)
* **Problem/Motivation:** KG-based RAG systems in real-world deployment face: (1) non-stationary environments (evolving queries, backend model upgrades); (2) need to balance multiple objectives (efficiency, coverage, reasoning power) for user satisfaction.
* **Method:** Proposes a Multi-objective Multi-Armed Bandit (MAB) enhanced RAG framework. Each retrieval method (dense retrieval, SPARQL generation, LLM agents) is treated as a "bandit arm." Uses DistilBERT as query encoder, epsilon-greedy arm selection, and Generalized Gini Index for reward aggregation.
* **Key Results:** Significantly outperforms baselines in non-stationary settings on two benchmark KGQA datasets.
* **Notable Findings:** Real-time user feedback enables continuous adaptation without requiring complete labeled datasets or periodic fine-tuning.

---

### 12. `06832-LuY.txt` — KEDKG
* **Title:** Knowledge Editing with Dynamic Knowledge Graphs for Multi-Hop Question Answering
* **Authors:** Yifan Lu, Yigeng Zhou, Jing Li*, Yequan Wang, Xuebo Liu, Daojing He, Fangming Liu, Min Zhang (HIT Shenzhen, BAAI, Pengcheng Laboratory)
* **Problem/Motivation:** Knowledge editing for MHQA struggles with: (1) inaccurate retrieval due to semantic similarity matching; (2) secondary editing conflicts — updated facts can contradict previously edited knowledge, introducing noise.
* **Method:** Proposes KEDKG — (1) Dynamic Knowledge Graph Construction: converts edited knowledge into structured triples, supporting dynamic modifications; (2) KG-Augmented Generation: uses CoT-inspired question decomposition into sub-questions and fine-grained retrieval.
* **Key Results:** Surpasses previous SOTA knowledge editing methods on benchmark datasets, delivering more accurate and reliable answers.
* **Notable Findings:** First approach to automatically construct dynamic knowledge graphs specifically for knowledge editing. Addresses the secondary editing conflict problem.

---

### 13. `06924-WangW.txt` — Imagine
* **Title:** Imagine: Image-Guided 3D Part Assembly with Structure Knowledge Graph
* **Authors:** Weihao Wang, Yu Lan, Mingyu You*, Bin He (Tongji University)
* **Problem/Motivation:** Existing 3D part assembly methods primarily memorize part poses during training, leading to inaccuracies in complex assemblies and poor generalization. Image-derived structural knowledge can be incomplete (occlusion) and ambiguous.
* **Method:** Proposes Imagine — derives a structure knowledge graph from the assembly image, then refines it through understanding 3D parts. Co-evolution paradigm allows the graph and assembly to progressively evolve together.
* **Key Results:** Achieves SOTA performance on both synthetic and realistic datasets with strong generalization to novel images and categories.
* **Notable Findings:** The co-evolution paradigm between the knowledge graph and assembly process is novel, helping overcome occlusion and view-dependency limitations of pure image-based approaches.

---

## Batch 2: Papers 14–25 (07528 to 12094)

### 14. `07528-XuK.txt` — KGCRR
* **Title:** KGCRR: An Effective Metric-Driven Knowledge Graph Completion Framework by Designing a Novel Upper Bound Function with Adaptive Approximation to Reciprocal Rank
* **Authors:** Kuan Xu, Kuo Yang, Jian Liu, Xiangkui Lu, Jun Wu, Xuezhong Zhou (Beijing Jiaotong University)
* **Problem/Motivation:** Most KGE methods overlook the inconsistency between the ranking metric (MRR) and the optimization objective functions, leading to sub-optimal KGC performance. Directly optimizing RR suffers from gradient vanishing.
* **Method:** Proposes KGCRR, a KGC framework with a new objective function called CRR that serves as an upper bound to RR. CRR introduces a "parameter-pressure ρ" to shift the sigmoid function, plus a log transformation to emphasize top-ranking positions.
* **Key Results:** Average MRR improvement of 19.06% across seven KGE methods on FB15k-237 and WN18RR.
* **Notable Findings:** CRR's parameter ρ is proven to monotonically reduce the gap between CRR and RR loss. CRR mitigates gradient vanishing issues that make direct RR optimization impractical.

---

### 15. `07973-WangJ.txt` — Hybrid-Driving
* **Title:** Hybrid-Driving: An Autonomous Driving Decision Framework Integrating Large Language Models, Knowledge Graphs and Driving Rules
* **Authors:** Jiabao Wang, Zepeng Wu, Qian Dong, Lingzhong Meng, Yunzhi Xue, Yukuan Yang (Chinese Academy of Sciences)
* **Problem/Motivation:** LLMs have strong reasoning for autonomous driving but suffer from hallucination, making standalone LLM-based decision-making unsafe. Existing methods lack comprehensive integration of domain-specific driving expertise (KGs + rules).
* **Method:** Proposes Hybrid-Driving, integrating LLMs with a Scenario Evolution Knowledge Graph (SEKG) and driving rules. Uses TTC-based scenario node construction with observation area division, SEKG-based action risk prediction, rule-based action filtering, and prompt engineering.
* **Key Results:** Hybrid-Driving improves decision success rates by ≥37.5% over LLM alone, ≥7.5% over DiLu, and ≥11% over RL methods across Highway-Env scenarios.
* **Notable Findings:** Driving rules alone provide stronger improvement than SEKG alone, but combining both achieves best results. The SEKG built for one scenario generalizes to different lane/density settings.

---

### 16. `08231-YangC.txt` — SPAC
* **Title:** SPAC: Sparse Partitioning and Adaptive Core Tensor Pruning Model for Knowledge Graph Completion
* **Authors:** Chuhong Yang, Bin Li, Nan Wu (Beijing Institute of Technology)
* **Problem/Motivation:** Tensor decomposition (TD) models for KGC face a trade-off: sparse core tensors limit interaction between embedding components; dense core tensors cause overfitting and high cost.
* **Method:** Proposes SPAC with three components: (1) Sparse partitioning using hybrid core tensors with main cores (dense interactions) and auxiliary cores (sparse interactions); (2) A gating mechanism to enable inter-group interaction; (3) Adaptive pruning during training that dynamically adjusts core tensor shape.
* **Key Results:** SOTA on FB15k-237, WN18RR, and YAGO3-10 among TD models with fewer parameters (e.g., 2x faster than Tucker with half the parameters).
* **Notable Findings:** The gating mechanism and adaptive pruning are both crucial. Combining sparse (auxiliary) and dense (main) interactions outperforms purely dense or purely sparse approaches.

---

### 17. `08276-XuD.txt` — AMAR
* **Title:** Harnessing Large Language Models for Knowledge Graph Question Answering via Adaptive Multi-Aspect Retrieval-Augmentation (AMAR)
* **Authors:** Derong Xu, Xinhang Li, Ziheng Zhang, et al. (USTC, CityU Hong Kong, Tencent YouTu Lab, Peking University)
* **Problem/Motivation:** LLMs struggle with hallucination in KGQA. Retrieval from KGs introduces noise, especially from multiple knowledge aspects (entities, relations, subgraphs). Previous works failed to align commonalities across aspects.
* **Method:** Proposes AMAR framework that retrieves multi-aspect knowledge and converts them to prompt embeddings. Features a self-alignment module to align commonalities among multi-aspect retrieval data, and a relevance gating module using siamese networks to filter retrieval noise.
* **Key Results:** SOTA on WebQSP (F1=81.2) and CWQ (F1=78.5), outperforming 22 baselines.
* **Notable Findings:** Relations are the most impactful retrieval aspect. Converting retrieval to prompt embeddings is far superior to directly appending text as context.

---

### 18. `08507-AAAI26.ChengY-NLP.txt` — CogGRAG
* **Title:** Human Cognition Inspired RAG with Knowledge Graph for Complex Problem Solving (CogGRAG)
* **Authors:** Yao Cheng, Yibo Zhao, Jiapeng Zhu, Yao Liu, Xing Sun, Xiang Li (East China Normal University; Tencent Youtu Lab)
* **Problem/Motivation:** Standard RAG relies on vector similarity matching and fails to capture relational dependencies for multi-step reasoning. Existing graph-based RAG methods lack holistic reasoning structures and verification mechanisms.
* **Method:** Proposes CogGRAG, a human-cognition-inspired graph-based RAG framework: (1) Top-down problem decomposition via tree-structured mind map construction; (2) Structured retrieval at local and global levels guided by the mind map; (3) Bottom-up reasoning with dual-LLM self-verification.
* **Key Results:** Best results on HotpotQA (F1=35.5%) and CWQ (F1=55.8%) using LLaMA2-13B.
* **Notable Findings:** CogGRAG's advantage comes from decomposing problems before retrieval (avoiding error propagation) and the self-verification mechanism.

---

### 19. `09868-XiaT.txt` — LACT
* **Title:** Improving Complex Reasoning over Knowledge Graph with Logic-Aware Curriculum Tuning (LACT)
* **Authors:** Tianle Xia, Liang Ding, Guojia Wan, Yibing Zhan, Bo Du, Dacheng Tao (Wuhan University; NTU)
* **Problem/Motivation:** Complex logical reasoning over incomplete KGs is challenging. Embedding-based methods have limited information, and prompt-based LLM approaches suffer from hallucination and high cost.
* **Method:** Proposes LACT, a fine-tuning framework for LLMs: (1) Binary Tree Decomposition (BTD) for data augmentation — decomposes complex EFO1 queries into chains of sub-queries; (2) Curriculum Learning — divides training into three stages (easy/medium/hard) with graduated difficulty ratios.
* **Key Results:** Average +5.5% MRR over previous SOTA methods. Consistently outperforms GQE, Q2B, BetaE, CQD, etc., across FB15K, FB15K-237, and NELL995.
* **Notable Findings:** BTD significantly reduces training perplexity and loss compared to undecomposed queries. Curriculum learning greatly alleviates difficulty gaps between query types.

---

### 20. `10684-AAAI26.HuQ-NLP.txt` — SAR
* **Title:** SAR: A Structure-Aligned Reasoning Framework for Temporal Knowledge Graph Question Answering
* **Authors:** Qianyi Hu, Jiaxue Liu, Xinhui Tu, Shoujin Wang (Central China Normal University; UTS)
* **Problem/Motivation:** TKGQA struggles with structural misalignment: plain-text queries on structured TKGs retrieve semantically similar but structurally incorrect facts, causing critical inaccuracies.
* **Method:** Proposes SAR, an iterative agent-based architecture with three modules: (1) Reasoning and Answer Generation using ReAct-inspired LLM agent; (2) Structure-Aligned Evidence Retrieval with temporal filtering, structured query decomposition, and chronological re-ranking; (3) Iterative Answer Verification.
* **Key Results:** Hits@1 = 78.2% on MultiTQ (vs. 60.7% for TempAgent), 91.7% on CronQuestions.
* **Notable Findings:** Structural alignment is crucial — SAR's structured retrieval prevents the common error of matching semantically similar but structurally wrong facts.

---

### 21. `11174-DuttaS.txt` — CBLiP
* **Title:** Replacing Paths with Connection-Biased Attention for Knowledge Graph Completion (CBLiP)
* **Authors:** Sharmishtha Dutta, Alex Gittens, Mohammed J. Zaki, Charu C. Aggarwal (RPI; IBM)
* **Problem/Motivation:** Inductive KG completion models using path encoding achieve better performance but at the cost of time complexity, memory overhead, and many hyperparameters.
* **Method:** Proposes CBLiP, a Transformer-based model that eliminates explicit path encoding. Uses: (1) Connection-biased attention — constructs an adjacency matrix encoding entity-sharing connections, injecting this as bias into Transformer attention; (2) Entity role embeddings — assigns simple {head, tail, other} role vectors.
* **Key Results:** Hits@10 up to 97.30% (v1) on WN18RR inductive. Competitive or superior to path-based models (NBFNet) while being faster.
* **Notable Findings:** Connection-biased attention implicitly captures path information and relative distances. Simple 3-role entity embeddings are surprisingly effective.

---

### 22. `11461-WangZ.txt` — Rule-Guided GNN
* **Title:** Rule-Guided Graph Neural Networks for Explainable Knowledge Graph Reasoning
* **Authors:** Zhe Wang, Suxue Ma, Kewen Wang, Zhiqiang Zhuang (Griffith University; Tianjin University)
* **Problem/Motivation:** Existing explainable GNN and rule-mining approaches extract rules from trained models, but these rules typically have low confidence. No existing model satisfies all four properties: efficient extraction, soundness, high confidence, and rule-guided training.
* **Method:** Proposes a new family of monotonic GNNs where parameters directly correspond to rules (R1–R8). Uses standard confidence degrees of rules to regularize GNN parameters during training (rule injection). Formally proves soundness of extracted rules.
* **Key Results:** Outperforms other rule mining (DRUM) and explainable GNN models (MGNN, INDIGO) in link prediction accuracy on FB15K-237 and NELL-995.
* **Notable Findings:** Rules injected during training effectively guide the model — extracted rules closely correlate with injected rules, and the standard confidence of extracted rules averages much higher.

---

### 23. `11468-GaoY.txt` — MCKGC
* **Title:** Mixed-Curvature Multi-Modal Knowledge Graph Completion (MCKGC)
* **Authors:** Yuxiao Gao, Fuwei Zhang, Zhao Zhang, Xiaoshuang Min, Fuzhen Zhuang (Beihang University)
* **Problem/Motivation:** Multi-modal KGC methods focus on modality-level fusion but neglect modeling complex structures (hierarchical, circular, chain patterns) in KGs. Euclidean space alone is insufficient.
* **Method:** Proposes MCKGC with two modules: (1) Modality Information Mixed-Curvature Module (MIMCM) — maps three modalities into three curvature spaces (hyperbolic, hyperspherical, Euclidean); (2) Progressive Fusion Module (PFM) — uses modality-level gates and space-level gates.
* **Key Results:** SOTA on DB15K (MRR=39.92, 5.4% improvement over MyGO), MKG-W, and MKG-Y.
* **Notable Findings:** All three curvature spaces contribute. Mixed-curvature perspective provides a significant edge over single-space multi-modal methods.

---

### 24. `11795-LiangX.txt` — FastToG
* **Title:** Fast Think-on-Graph: Wider, Deeper and Faster Reasoning of Large Language Model on Knowledge Graph (FastToG)
* **Authors:** Xujian Liang, Zhaoquan Gu (BUPT; Peng Cheng Lab)
* **Problem/Motivation:** Existing Graph RAG methods are either too narrow/shallow (failing on complex problems) or too computationally expensive (requiring LLM calls at each step).
* **Method:** Proposes FastToG, a Graph RAG paradigm where LLMs think "community by community." Uses Local Community Search (LCS) with community detection, modularity-based coarse pruning, semantic LLM fine pruning, and Community-to-Text conversion.
* **Key Results:** Outperforms ToG by 4.4% on CWQ (45.0% with gpt-4o-mini) and 5.9% with Llama-3-70B. Significant reduction in average reasoning depth.
* **Notable Findings:** Community-based reasoning dramatically reduces the number of LLM calls. Max community size of 4 provides the best accuracy-efficiency trade-off.

---

### 25. `12094-LiM.txt` — CATS
* **Title:** Context-aware Inductive Knowledge Graph Completion with Latent Type Constraints and Subgraph Reasoning (CATS)
* **Authors:** Muzhi Li, Cehao Yang, Chengjin Xu, et al. (CUHK; IDEA Research; Cambridge)
* **Problem/Motivation:** Inductive KGC with unseen entities is challenging. Path-based methods depend heavily on reasoning paths (unavailable for 30% of query triples in FB15k-237). Existing methods fail to utilize entity types, paths, and neighboring facts.
* **Method:** Proposes CATS with two LLM-based modules: (1) Type-Aware Reasoning (TAR) — evaluates whether candidate entities match latent type constraints by sampling triples; (2) Subgraph Reasoning (SR) — selects relevant paths via degree-based filtering and neighboring facts via embedding similarity, then prompts LLM.
* **Key Results:** Outperforms SOTA (APST) in 16/18 settings. On WN18RR inductive: MRR=0.982 (vs 0.908 for APST). On FB15k-237 inductive: MRR=0.882 (vs 0.764).
* **Notable Findings:** First LLM-based inductive KGC solution handling unseen entities without external knowledge or prior inference results. TAR alone provides strong performance, validating latent type constraints.

---

## Batch 3: Papers 26–37 (12492 to 29004)

### 26. `12492-AoT.txt` — LightPROF
* **Title:** LightPROF: A Lightweight Reasoning Framework for Large Language Model on Knowledge Graph
* **Authors:** Tu Ao, Yanhua Yu, Yuling Wang, Yang Deng, Zirui Guo, Liang Pang, Pinghui Wang, Tat-Seng Chua, Xiao Zhang, Zhen Cai (BUPT, NUS, SMU, etc.)
* **Problem/Motivation:** Existing KG-based LLM reasoning methods inject KG knowledge only as text into prompts, ignoring structural information, and rely on large models leading to high resource consumption.
* **Method:** Proposes LightPROF: (1) Retrieval: uses relation-based constrained BFS to retrieve a reasoning graph; (2) Embedding: a Transformer-based Knowledge Adapter extracts and integrates textual and structural information into dense "knowledge soft prompts"; (3) Reasoning: combines soft prompts with hard text prompts. Only the Knowledge Adapter is trained.
* **Key Results:** On WebQSP, LightPROF (LLaMa3-8B) achieves 83.8% Hits@1 vs. 75.1% for SOTA UniKGQA. On CWQ, it achieves 59.3% vs. 57.6% for ToG (LLaMa2-70B). Uses ~98% fewer input tokens than StructGPT.
* **Notable Findings:** First framework to transform both KG text and structure into embeddings for LLM prompting. Small-scale LLMs (7B/8B) outperform large models (70B) with this approach.

---

### 27. `12669-WangZ.txt` — STLC-KG
* **Title:** STLC-KG: A Social Text Steganalysis Method Combining Large-Scale Language Models and Common-Sense Knowledge Graphs
* **Authors:** Zhuang Wang, Linna Zhou, Xuekai Chen, Zhili Zhou, Zhongliang Yang (BUPT, Guangzhou Univ.)
* **Problem/Motivation:** Existing social text steganalysis techniques analyze individual texts in isolation. Single-text information is too limited to achieve good detection, especially with advanced LLM-based steganography.
* **Method:** Proposes STLC-KG: (1) Semantic Extraction: fine-tunes ChatGLM2-6B using parameter-efficient methods; (2) Knowledge Encoding: links text entities to ConceptNet, builds a knowledge feature subgraph, and encodes it using a 2-layer Graph Attention Network (GAT).
* **Key Results:** STLC-KG achieves highest detection accuracy on TWEET, MOVIE, and NEWS datasets with average improvement of 4.18% over previous SOTA.
* **Notable Findings:** First work to combine LLMs with knowledge graphs for text steganography detection. Commonsense knowledge graphs can reveal factual inconsistencies that LLM-generated stego text produces.

---

### 28. `13014-ZhuM.txt` — SEmPI
* **Title:** Representation Learning Based Predicate Invention on Knowledge Graphs
* **Authors:** Man Zhu, Pengfei Huang, Lei Gu, Xiaolong Xu, Jingyu Han (NJUPT, NUAA, NJUST)
* **Problem/Motivation:** Predicate invention (PI) — automatically creating new predicate symbols from existing vocabulary — is a core challenge in ILP. Existing approaches are logic-based and don't scale well.
* **Method:** Formalizes the ReLPI problem. Proposes SEmPI: (1) Learns predicate embeddings as diagonal matrices using a DistMult-style scoring function; (2) Trains an MLP classifier jointly with embeddings using a loss capturing embedding quality and predicate existence; (3) Generates candidate predicate embeddings via matrix operations (transitive = multiplication, conjunctive = averaging, inverse = inversion) and classifies them.
* **Key Results:** Superior recall over TransE-DNN, DistMult-DNN, and ComplEx-DNN baselines on FB15k and DRKG. Prediction precision on FB15k reaches 0.82.
* **Notable Findings:** Novel formulation bridging representation learning and predicate invention. SEmPI scales significantly better than traditional ILP approaches on large fact-abundant KGs.

---

### 29. `13275-TianS.txt` — KGA (KG Alignment)
* **Title:** A Systematic Exploration of Knowledge Graph Alignment with Large Language Models in Retrieval Augmented Generation
* **Authors:** Shiyu Tian, Shuyue Xing, Xingrui Li, Yangyang Luo, Caixia Yuan, Wei Chen, Huixing Jiang, Xiaojie Wang (BUPT, LI Auto Inc.)
* **Problem/Motivation:** When using KGs for RAG, KGs must be linearized to text (KG Alignment / KGA). This is typically treated as a trivial step, but it critically impacts performance.
* **Method:** Systematically studies KGA: (1) Graph transformation (graph-to-graph): studies 81 graph features; (2) Linearization (graph-to-text): studies 13 formats, 13 orders, and 14 templates across 15 LLMs. Uses mechanistic interpretability (information flow routes) to analyze how LLMs process KGs.
* **Key Results:** Centrality features most strongly affect generation quality. Formats are the most influential linearization factor. Combining optimal factors achieves 7.3% average improvement on KGQA (up to 91.35% on GPT-4o with GraphextQA).
* **Notable Findings:** LLMs process KGs through a unique mechanism (circuit), different from processing natural language. Separators play a critical role — they exhibit "BOS features" that summarize prior information without adding linguistic content.

---

### 30. `13891-YuanD.txt` — RAA-KGC
* **Title:** Knowledge Graph Completion with Relation-Aware Anchor Enhancement
* **Authors:** Duanyang Yuan, Sihang Zhou, Xiaoshu Chen, Dong Wang, Ke Liang, Xinwang Liu, Jian Huang (NUDT)
* **Problem/Motivation:** Text-based KGC methods map (head, relation) queries and candidate entities into embeddings, but provide no context information about what the target entity should look like.
* **Method:** Proposes RAA-KGC: (1) Generates anchor entities by randomly sampling from the relation-aware entity set; (2) Creates anchor-enhanced queries by appending anchor entity descriptions; (3) Uses a bi-encoder (BERT-based) with contrastive learning over query embeddings.
* **Key Results:** On WN18RR: MRR 59.74% (+4.43% over SimKGC). On Wikidata5M-Trans: MRR 34.15% (+4.97%). RAA boosts SimKGC by ~7% MRR and InsKGC by ~3.4% MRR.
* **Notable Findings:** Relation-aware entities capture important concept information about target entities. The anchor enhancement works as a plug-and-play module that can be applied to both text-based and triple-based KGC methods.

---

### 31. `16037-AAAI26.JiangW-NLP.txt` — LUCID
* **Title:** From Chaos to Clarity: A Knowledge Graph-Driven Audit Dataset Generation Framework for LLM Unlearning
* **Authors:** Weipeng Jiang, Juan Zhai, Shiqing Ma, Ziyan Lei, Xiaofei Xie, Yige Wang, Chao Shen (Xi'an Jiaotong Univ., UMass Amherst, SMU)
* **Problem/Motivation:** Evaluating LLM unlearning is unreliable because existing benchmarks use ad-hoc question generation from unstructured text, leading to audit inadequacy and knowledge redundancy.
* **Method:** Proposes LUCID, a 3-stage framework: (1) KG Construction: converts forget and retain corpora into KGs; (2) Redundancy Removal: identifies and eliminates overlapping triples between forget-KG and retain-KG; (3) Question Synthesis: uses LLM with dual-input prompting to generate targeted QA pairs.
* **Key Results:** Detected 142× to 1,242× more knowledge memorization cases than MUSE. Knowledge redundancy inflated performance metrics. KG redundancy removal reduced ~31.7%–33.7% of facts.
* **Notable Findings:** Current unlearning methods are far less effective than previously thought due to insufficient testing. Knowledge deduplication is essential for accurate unlearning assessment.

---

### 32. `16594-CaoY.txt` — DPCL-Diff
* **Title:** DPCL-Diff: A Temporal Knowledge Graph Reasoning Model Using Graph Node Diffusion and Dual-Domain Periodic Contrastive Learning
* **Authors:** Cao Y. et al.
* **Problem/Motivation:** Temporal KG reasoning (TKGR) must handle evolving facts over time. Existing methods struggle with capturing periodic patterns in temporal data and modeling structural evolution.
* **Method:** Proposes DPCL-Diff with two key components: (1) GNDiff (Graph Node Diffusion): uses a diffusion process on graph nodes to model structural evolution; (2) DPCL (Dual-Domain Periodic Contrastive Learning): captures periodic patterns in both time and frequency domains using contrastive learning.
* **Key Results:** Achieves SOTA performance on temporal KG reasoning benchmarks, outperforming existing methods on metrics like MRR and Hits@k.
* **Notable Findings:** Combining diffusion-based structural modeling with periodic contrastive learning in dual domains effectively captures complex temporal dynamics in KGs.

---

### 33. `17262-NiB.txt` — UAG
* **Title:** UAG: Uncertainty Aware Knowledge-Graph Reasoning
* **Authors:** Ni B. et al.
* **Problem/Motivation:** LLM-based KG question answering lacks uncertainty quantification. When LLMs retrieve and reason over KGs, they provide no reliable confidence estimates.
* **Method:** Proposes UAG (Uncertainty Aware knowledge-Graph reasoning), which integrates conformal prediction into KG-LLM pipelines for multi-hop KGQA. This provides statistically-guaranteed prediction sets that contain the correct answer with a user-specified probability.
* **Key Results:** Demonstrates effective uncertainty quantification on multi-hop KGQA benchmarks while maintaining reasoning accuracy.
* **Notable Findings:** Conformal prediction can be successfully applied to KG-LLM reasoning pipelines, providing calibrated uncertainty estimates without requiring model retraining.

---

### 34. `17985-AAAI26.NingY-NLP.txt` — ARoG
* **Title:** ARoG: Abstraction Reasoning on Graph — A Privacy-Protected RAG Framework for KGQA
* **Authors:** Ning Y. et al.
* **Problem/Motivation:** Using KGs with LLM-based RAG for QA exposes sensitive entity information to external LLM APIs, creating privacy risks.
* **Method:** Proposes ARoG, which anonymizes entities by replacing them with abstract identifiers before sending them to LLMs. Uses relation abstraction and structure abstraction to preserve reasoning capability while hiding specific entity information. Answers are de-anonymized locally.
* **Key Results:** Achieves competitive QA performance compared to non-private baselines while fully protecting entity-level privacy.
* **Notable Findings:** LLMs can effectively reason over abstracted/anonymized KG structures, suggesting that relational and structural patterns carry sufficient information for many QA tasks without needing specific entity identities.

---

### 35. `24144-AAAI26.CaoY-NLP.txt` — DCTR
* **Title:** DCTR: Dual-Constraint Subgraph Optimization for KG-RAG
* **Authors:** Cao Y. et al.
* **Problem/Motivation:** When retrieving KG subgraphs for RAG, existing methods either retrieve too much irrelevant information or miss important structural connections.
* **Method:** Proposes DCTR, a dual-constraint subgraph optimization method that simultaneously enforces structural integrity (ensuring connectivity) and information salience (ensuring relevancy). These constraints jointly optimize the retrieved KG subgraph.
* **Key Results:** Outperforms existing KG-RAG methods on KGQA benchmarks by providing LLMs with higher-quality, better-structured KG context.
* **Notable Findings:** Both structural and content-level constraints are necessary — using either alone underperforms the combined approach.

---

### 36. `25667-AAAI26.ParkM-NLP.txt` — ProgRAG
* **Title:** ProgRAG: A Hallucination-Resistant Progressive Retrieval and Reasoning Framework for Multi-hop KGQA
* **Authors:** Park M. et al.
* **Problem/Motivation:** Multi-hop KGQA is prone to hallucination when LLMs attempt to answer complex questions requiring multiple reasoning steps. Retrieving all information at once can overwhelm the model.
* **Method:** Proposes ProgRAG, which decomposes complex multi-hop questions into simpler sub-questions and progressively retrieves and reasons step-by-step. Each step retrieves only the relevant KG information needed for that sub-question.
* **Key Results:** Significantly reduces hallucination rates compared to single-pass retrieval methods while maintaining or improving accuracy on multi-hop KGQA benchmarks.
* **Notable Findings:** Progressive, decomposition-based retrieval is more robust than one-shot retrieval for multi-hop reasoning. Step-by-step verification helps catch and prevent error propagation.

---

### 37. `29004-AAAI26.LiuS-NLP.txt` — TruthfulRAG
* **Title:** TruthfulRAG: Using Knowledge Graphs to Resolve Factual-Level Knowledge Conflicts in RAG
* **Authors:** Liu S. et al.
* **Problem/Motivation:** RAG systems face knowledge conflicts between the LLM's parametric knowledge and externally retrieved information.
* **Method:** Proposes TruthfulRAG, which uses KGs as an authoritative knowledge source to arbitrate conflicts. Uses query-based graph retrieval to extract relevant KG facts, and entropy-based filtering to identify and resolve conflicts by measuring information entropy.
* **Key Results:** Improves factual accuracy on QA benchmarks with known knowledge conflicts, outperforming standard RAG and other conflict-resolution approaches.
* **Notable Findings:** KGs serve as effective "ground truth" arbiters for resolving conflicts in RAG systems. Entropy-based filtering is a practical, computationally efficient method for identifying unreliable retrieved passages.
