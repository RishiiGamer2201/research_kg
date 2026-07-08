# ACM Venue Sweep: SIGIR, KDD, WSDM Related Work

Date: 2026-07-07  
Scope: SIGIR, KDD, and WSDM papers or challenge lines from 2024, 2025, and available 2026
material related to the self-healing multilingual KB pivot.

Current pivot:

> LLM-generated text can contaminate multilingual knowledge bases, especially in low-resource
> languages. A KB can self-audit descriptions by checking graph-text consistency, quarantine bad
> text, re-source it, and measure downstream retrieval/KGC/grounding repair.

Important caveat: 2026 proceedings are partially indexed as of 2026-07-07. Treat 2026 as a live
sweep, not a closed bibliography.

---

## 1. Bottom Line

| Venue | Best framing for us |
|---|---|
| **KDD** | Contaminated multilingual KBs as a data-quality, benchmark, and knowledge-discovery problem |
| **SIGIR** | Cleaning KBs improves retrieval, RAG faithfulness, and grounded answer generation |
| **WSDM** | Web search, multilingual retrieval, RAG systems, and KG-backed web data quality |

Main finding:

> I did not find a direct SIGIR/KDD/WSDM 2024-2026 paper that specifically studies
> **AI-generated contaminated entity descriptions inside multilingual KBs**, detects them by
> **graph-text disagreement**, repairs them, and measures downstream multilingual grounding.

The neighbouring spaces are active, but our exact target is still defensible if we avoid
over-claiming.

---

## 2. KDD-Related Work

### CRAG: Comprehensive RAG Benchmark, KDD Cup 2024

Source: [CRAG: Comprehensive RAG Benchmark](https://arxiv.org/abs/2406.04744)

Why it matters:

- CRAG evaluates realistic retrieval-augmented generation.
- It includes web search and KG-search style APIs.
- It studies entity popularity, temporal dynamism, and question complexity.
- It shows that even strong RAG systems remain far from fully reliable.

Relation to us:

- CRAG asks whether RAG systems can use external evidence.
- We ask whether the external evidence layer is clean enough to trust.

Positioning:

> CRAG evaluates whether RAG systems can use evidence; our work studies whether the KB evidence
> itself has been contaminated before retrieval.

### KDD Cup 2024 CRAG Solution Papers

Sources:

- [Winning Solution For Meta KDD Cup 24](https://arxiv.org/abs/2410.00005)
- [Revisiting the Solution of Meta KDD Cup 2024: CRAG](https://arxiv.org/abs/2409.15337)
- [A Hybrid RAG System with Comprehensive Enhancement on Complex Reasoning](https://arxiv.org/abs/2408.05141)

Why they matter:

- These show KDD-style systems using retrieval, APIs, and KG-like evidence to reduce
  hallucination.
- They are useful baselines for how people operationalize factual QA benchmarks.

Relation to us:

- They optimize retrieval and answer generation.
- They do not audit the KB/entity-description layer itself.

Positioning:

> KDD Cup systems improve how evidence is selected and used; our system improves whether the
> evidence repository is trustworthy in the first place.

### CRAG-MM / KDD Cup 2025

Source: [DB3 Team's Solution For Meta KDD Cup 25](https://arxiv.org/abs/2509.09681)

Why it matters:

- Extends CRAG-style evaluation to multimodal and multiturn settings.
- Uses web sources and image-indexed knowledge graphs.
- Useful for arguing that KDD values realistic benchmark construction and hallucination control.

Relation to us:

- It is downstream RAG evaluation.
- Our contribution is upstream KB self-auditing and repair.

### AssetOpsBench and KG Data Layer for LLM Agents

Sources:

- [AssetOpsBench](https://arxiv.org/abs/2506.03828)
- [Knowledge Graphs as the Missing Data Layer for LLM-Based Industrial Asset Operations](https://arxiv.org/abs/2605.26874)

Why it matters:

- Strong KDD-style motivation that the data layer behind an LLM can dominate system quality.
- The KG data-layer work argues that deterministic graph handlers can outperform raw
  tool-augmented LLM baselines.

Relation to us:

- Their focus is industrial operations and structured data.
- Our focus is multilingual KB text contamination.

Positioning:

> Recent KDD-style work shows that graph data layers improve LLM systems; we show that when this
> graph layer contains contaminated descriptions, the data layer itself must be audited.

---

## 3. SIGIR-Related Work

### SIGIR 2024 RAG Session

Source: [DBLP SIGIR 2024 proceedings](https://dblp.org/db/conf/sigir/sigir2024.html)

Relevant papers:

- [The Power of Noise: Redefining Retrieval for RAG Systems](https://dblp.org/rec/conf/sigir/CuconasuTSFCMTS24)
- [IM-RAG: Multi-Round Retrieval-Augmented Generation Through Learning Inner Monologues](https://dblp.org/rec/conf/sigir/YangRCGZYZ24)
- [Towards a Search Engine for Machines](https://dblp.org/rec/conf/sigir/SalemiZ24)
- [IR-RAG @ SIGIR24](https://dblp.org/rec/conf/sigir/PetroniSST24)

Why it matters:

- SIGIR already has a strong RAG/retrieval evaluation lane.
- Reviewers understand retrieval quality, context quality, and grounded generation.

Relation to us:

- These papers optimize retrieval/generation.
- Our method is pre-retrieval evidence quality control.

Positioning:

> SIGIR RAG work studies how to retrieve and rank evidence; our work detects when the evidence
> corpus itself has been polluted before retrieval begins.

### SIGIR 2025 LiveRAG Challenge

Sources:

- [SIGIR 2025 LiveRAG Challenge Report](https://arxiv.org/abs/2507.04942)
- [CIIR@LiveRAG 2025](https://arxiv.org/abs/2506.10844)
- [RMIT-ADM+S at LiveRAG 2025](https://arxiv.org/abs/2506.14516)
- [TopClustRAG at LiveRAG 2025](https://arxiv.org/abs/2506.15246)

Why it matters:

- LiveRAG is direct evidence that SIGIR cares about end-to-end RAG quality.
- It evaluates correctness and faithfulness style behaviour.

Relation to us:

- LiveRAG assumes a fixed evidence corpus.
- We ask whether the corpus/KB can detect and repair poisoned descriptions.

Positioning:

> LiveRAG evaluates how systems use retrieved evidence; our work asks whether the evidence
> repository can self-detect and repair contaminated entity descriptions.

### SIGIR 2024 KG Completion, KG Datasets, and KG Search

Source: [DBLP SIGIR 2024 proceedings](https://dblp.org/db/conf/sigir/sigir2024.html)

Relevant papers:

- [NativE: Multi-modal Knowledge Graph Completion in the Wild](https://dblp.org/rec/conf/sigir/ZhangCGXHLZC24)
- [Contrast then Memorize: Semantic Neighbor Retrieval-Enhanced Inductive Multimodal KGC](https://dblp.org/rec/conf/sigir/ZhaoZZQSC24)
- [EditKG: Editing Knowledge Graph for Recommendation](https://dblp.org/rec/conf/sigir/TangGW0WFZ24)
- [Amazon-KG: A Knowledge Graph Enhanced Cross-Domain Recommendation Dataset](https://dblp.org/rec/conf/sigir/WangXTLYL24)
- [Untargeted Adversarial Attack on Knowledge Graph Embeddings](https://dblp.org/rec/conf/sigir/Zhao0RLGL24)
- [A Question-Answering Assistant over Personal Knowledge Graph](https://dblp.org/rec/conf/sigir/LiuDZGWW24)
- [SpherE: Expressive and Interpretable Knowledge Graph Embedding for Set Retrieval](https://dblp.org/rec/conf/sigir/LiAH24)

Why it matters:

- SIGIR publishes KG completion, KG datasets, adversarial KG work, personal KG QA, and KG
  recommendation.
- "Contrast then Memorize" is especially relevant because it is inductive KGC with semantic
  neighbour retrieval.

Relation to us:

- These works treat KG representation and retrieval.
- They generally do not treat entity-description contamination as the central data-quality
  problem.

Positioning:

> SIGIR has strong KG completion and KG dataset work, but the integrity of entity descriptions
> consumed by text-based KG systems remains under-studied.

---

## 4. WSDM-Related Work

### WSDM 2024: KG, RAG, and Multilingual Retrieval Context

Source: [DBLP WSDM 2024 proceedings](https://dblp.org/db/conf/wsdm/wsdm2024.html)

Relevant items:

- [Retrieval-Augmented Generation in the Era of Large Language Models](https://dblp.org/rec/conf/wsdm/YuWZYXCLCYZZ24)
- [A Short Survey on Multilinguality in Large Language Models](https://dblp.org/rec/conf/wsdm/ZhaoSAC24)
- [Do LLMs Really Adapt to Domains? An Ontology Learning Perspective](https://dblp.org/rec/conf/wsdm/ChenZ24)
- [When Search Engine Services meet Large Language Models](https://dblp.org/rec/conf/wsdm/MaoD24)
- [A Survey on Large Language Models for Recommendation](https://dblp.org/rec/conf/wsdm/WuZLLHB24)

Why it matters:

- WSDM has a strong tutorial/survey lane around RAG, LLMs, multilinguality, and web search.
- Useful for framing the problem for web/search audiences.

Relation to us:

- These are broad surveys/tutorials, not direct competitors.
- They help justify the importance of multilingual and retrieval-grounded systems.

### WSDM 2024 KG Recommendation / KG Reasoning Papers

Source: [DBLP WSDM 2024 proceedings](https://dblp.org/db/conf/wsdm/wsdm2024.html)

Relevant papers:

- [Multi-View Empowered Structural Graph Wordification for Language Models](https://dblp.org/rec/conf/wsdm/HuFLPL0QL24)
- [Reliable Knowledge Graph Path Representation Learning](https://dblp.org/rec/conf/wsdm/LiWDWZG24)
- [Modeling User Fatigue for Sequential Recommendation](https://dblp.org/rec/conf/wsdm/LiuL0QSZ24)
- [Multi-Behavior Hypergraph-Enhanced Transformer for Sequential Recommendation](https://dblp.org/rec/conf/wsdm/YuanGCLLJL24)

Why it matters:

- WSDM is receptive to KG-enhanced recommender/search systems.
- These are less direct than SIGIR/KDD for our contamination idea.

### WSDM 2025: Evidence and RAG Direction

Source: [DBLP record for "Can Large Language Models Unlock Novel Scientific Research Ideas?"](https://dblp.org/rec/conf/wsdm/SiADWR25)

Relevant direction:

- [Can Large Language Models Unlock Novel Scientific Research Ideas?](https://dblp.org/rec/conf/wsdm/SiADWR25)

Why it matters:

- The paper studies LLM-generated research ideas and indirectly relates to evaluation of
  generated content.
- It is not about KB contamination, but useful for showing WSDM interest in LLM-produced
  knowledge artifacts.

Note:

- WSDM 2025/2026 full related-work coverage should be refreshed once the full proceedings are
  easier to query. Current search did not reveal a direct self-healing-KB competitor.

---

## 5. Papers Outside These Venues That We Still Must Cite

These are not necessarily SIGIR/KDD/WSDM papers, but they are too close to ignore.

### KB Contamination / Machine-Generated Text / Wikipedia Quality

- [WETBench: Detecting Task-Specific Machine-Generated Text on Wikipedia](https://arxiv.org/abs/2507.03373)  
  Important because stylometric machine-text detection struggles, especially in lower-resource
  settings. Our detector uses graph-text factual agreement instead of writing style.

- [Wikipedia in the Era of LLMs: Evolution and Risks](https://arxiv.org/abs/2503.02879)  
  Important because it warns that RAG can degrade if KBs are polluted by LLM-generated text.

- [How Good is Your Wikipedia?](https://arxiv.org/abs/2411.05527)  
  Important for low-resource Wikipedia quality and multilingual data-quality framing.

### Multilingual Factuality and KG Grounding

- [MultiHal](https://arxiv.org/abs/2505.14101)  
  Multilingual KG-grounded hallucination benchmark. Closest to the KG-grounded hallucination
  framing, but not a KB self-audit and repair loop.

- [mRAKL](https://arxiv.org/abs/2507.16011)  
  Low-resource multilingual retrieval-augmented KG construction. Constructs/augments KGs; does
  not clean contaminated descriptions.

- [KG-TRICK](https://arxiv.org/abs/2501.03560)  
  Multilingual textual and relational KG completion. Related to KG text completion, but not
  contamination detection/repair.

- [KG Error Detection with Contrastive Confidence Adaption](https://arxiv.org/abs/2312.12108)  
  Important near-neighbour: detects bad triples using text/structure, while we detect bad
  descriptions using graph structure.

---

## 6. Competitor Matrix

| Line of work | What it solves | What it does not solve |
|---|---|---|
| CRAG / LiveRAG / RAG challenges | How to answer using retrieved evidence | Whether the KB evidence itself is contaminated |
| SIGIR RAG papers | Retrieval, ranking, context construction | Upstream entity-description integrity |
| KG completion papers | Missing link prediction | False natural-language descriptions attached to entities |
| KG error detection | Bad triples / noisy edges | Bad descriptions / LLM-fabricated biographies |
| Machine-generated text detection | Whether text looks generated | Whether text contradicts the graph |
| Multilingual factuality benchmarks | LLM performance gaps across languages | Repairing contaminated multilingual KBs |

Our defensible gap:

> A multilingual KB self-audit loop for AI-generated entity-description contamination, using
> graph-text consistency, with quarantine, re-sourcing, and downstream repair measurement.

---

## 7. Recommended Venue Positioning

### KDD Version

Title shape:

> Self-Healing Multilingual Knowledge Bases: Detecting and Repairing LLM-Generated Entity
> Description Contamination

Contribution shape:

1. Characterize LLM-generated contamination in multilingual KB descriptions.
2. Build a benchmark with real and controlled contamination.
3. Propose graph-text consistency detection.
4. Repair the KB and measure downstream KGC/RAG gains.

Why KDD:

- data quality,
- benchmark/dataset,
- graph data mining,
- practical downstream utility.

### SIGIR Version

Title shape:

> Before Retrieval: Self-Auditing Multilingual Knowledge Bases for Faithful KG-RAG

Contribution shape:

1. Show contaminated KB descriptions poison retrieval/grounding.
2. Detect contamination using graph-text consistency.
3. Repair evidence sources.
4. Measure retrieval and LLM-grounded QA improvements.

Why SIGIR:

- retrieval evidence quality,
- RAG faithfulness,
- ranking,
- KG search.

### WSDM Version

Title shape:

> Web-Scale Multilingual KB Self-Auditing for Reliable Retrieval-Augmented Systems

Contribution shape:

1. Web KB contamination phenomenon.
2. Multilingual/low-resource concentration.
3. Search/retrieval impact.
4. Practical repair loop.

Why WSDM:

- web search,
- web data quality,
- multilingual retrieval,
- practical LLM search systems.

---

## 8. Next Search Tasks

1. Refresh SIGIR 2026 official accepted papers once proceedings are fully indexed.
2. Refresh KDD 2026 accepted papers after the official program/proceedings are public.
3. Refresh WSDM 2026 proceedings and search for "knowledge graph", "RAG", "hallucination",
   "generated text", "multilingual", and "data quality".
4. Add exact BibTeX entries for all must-cite papers.
5. Build the related-work section around the competitor matrix rather than a flat list.

