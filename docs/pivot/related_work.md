# Related Work (canonical): SIGIR, KDD, WSDM and Close Neighbours, 2024 to 2026

Compiled 2026-07-07 by merging two independent literature sweeps: a theme-and-arXiv sweep and a
DBLP proceedings sweep of SIGIR, KDD, and WSDM. This is the single authoritative related-work
document; the two source drafts are archived under `docs/pivot/archive/`.

The pivot this positions against:

> LLM-generated text contaminates multilingual knowledge bases, worst in low-resource languages.
> A KB can self-audit its descriptions by checking graph-text consistency, quarantine the bad
> text, re-source it, and measure the downstream repair on retrieval, KG completion, and grounding.

Caveat: 2026 proceedings are only partially indexed as of this date; treat 2026 as a live sweep.
Several arXiv identifiers came from search and should be confirmed on the arXiv or ACM page before
they enter a bibliography.

---

## 1. Bottom line

Two independent sweeps, built by different methods, reached the same conclusion, which lets us
state the gap with confidence:

> No SIGIR, KDD, or WSDM 2024 to 2026 paper studies AI-generated contaminated entity descriptions
> inside a multilingual KB, detects them by graph-text disagreement, repairs them, and measures
> downstream multilingual grounding. The neighbouring spaces are active, but this exact target is
> defensible if we avoid over-claiming.

Best framing per venue:

| Venue | Best framing for us |
|---|---|
| KDD | Contaminated multilingual KBs as a data-quality, benchmark, and knowledge-discovery problem |
| SIGIR | Cleaning the KB before retrieval improves RAG faithfulness and grounded generation |
| WSDM | Web-scale multilingual retrieval and KG-backed web data quality |

The two closest things to be honest about: (a) the WWW 2026 retrieval-collapse paper establishes
our disease at a top venue (Section 2), and (b) KG error detection is the closest technical
neighbour, but it finds bad triples, not bad descriptions (Section 5).

---

## 2. The single most important neighbour: retrieval collapse under AI pollution

**Retrieval Collapses When AI Pollutes the Web** (Yu et al., NAVER; ACM Web Conference / WWW 2026;
arXiv 2602.16136). Characterises "retrieval collapse": AI-generated content comes to dominate
search results, source diversity erodes, and low-quality or adversarial content infiltrates the
pipeline. In their controlled study a 67 percent contaminated pool produced over 80 percent
contaminated exposure, a deceptively healthy state where accuracy looks stable while the evidence
is quietly synthetic.

Why it matters: this is the strongest possible motivation for our thesis, published at a top venue,
that AI pollution degrades retrieval systems. It establishes the disease. But it studies web text
corpora, only measures the effect on retrieval, does not detect or repair, does not use knowledge
graphs, and is not multilingual.

One-line differentiation: they show AI pollution collapses web retrieval; we detect and repair AI
pollution inside a multilingual KB using the graph's own structure, and measure the downstream
repair. Cite as motivation, not competitor.

---

## 3. KDD related work (venue-verified)

### RAG benchmarks: CRAG and CRAG-MM (KDD Cup challenge track)
- CRAG: Comprehensive RAG Benchmark, KDD Cup 2024 (arXiv 2406.04744). Realistic RAG with web and
  KG-search APIs; studies entity popularity, temporal dynamism, question complexity; shows strong
  RAG systems remain unreliable.
- KDD Cup 2024 winning and solution papers (arXiv 2410.00005, 2409.15337, 2408.05141).
- CRAG-MM / KDD Cup 2025, multimodal multiturn (arXiv 2509.09681).
Note: these are challenge track, not KDD main research track; cite as benchmark context.
Positioning: CRAG evaluates whether RAG can use evidence; we ask whether the KB evidence itself is
contaminated before retrieval.

### Inductive KGC benchmarks (directly relevant to our substrate)
- Towards better benchmark datasets for inductive knowledge graph completion (Shomer et al., KDD
  2025). Argues current inductive-KGC benchmarks are flawed and proposes better ones. This is the
  paper to cite and differentiate DBP-5L-Ind against, and it proves KDD's appetite for
  inductive-KGC benchmark quality, which supports aiming at the Datasets and Benchmarks track.

### KG data layer for LLM systems (motivation that the data layer dominates quality)
- AssetOpsBench (arXiv 2506.03828) and Knowledge Graphs as the Missing Data Layer for LLM-Based
  Industrial Asset Operations (arXiv 2605.26874). Argue deterministic graph data layers beat raw
  tool-augmented LLMs. Positioning: graph data layers improve LLM systems, so when that layer is
  contaminated it must be audited.

Why KDD fits: data quality, benchmarks and datasets, graph data mining, practical downstream
utility.

---

## 4. SIGIR related work (venue-verified)

### RAG and retrieval-evidence quality
- SIGIR 2024 RAG session: The Power of Noise (redefining retrieval for RAG), IM-RAG (multi-round
  RAG via inner monologues), Towards a Search Engine for Machines, IR-RAG workshop.
- SIGIR 2025 LiveRAG Challenge report (arXiv 2507.04942) and team solutions (CIIR 2506.10844,
  RMIT-ADM+S 2506.14516, TopClustRAG 2506.15246). Direct evidence SIGIR cares about end-to-end RAG
  correctness and faithfulness.
- Rowen: adaptive RAG for hallucination mitigation (SIGIR-AP 2025).
Positioning: SIGIR RAG work studies how to retrieve and rank evidence; we detect when the evidence
corpus itself is polluted before retrieval begins.

### KG completion, KG datasets, KG search at SIGIR
- SIGIR 2024: NativE (multimodal KGC in the wild), Contrast then Memorize (inductive multimodal KGC
  with semantic-neighbour retrieval, a genuine neighbour to our substrate), EditKG (editing KGs for
  recommendation), Amazon-KG (KG-enhanced cross-domain recommendation dataset), Untargeted
  Adversarial Attack on KG Embeddings, personal-KG QA, SpherE (interpretable KG embedding for set
  retrieval).
Positioning: SIGIR has strong KG completion and KG dataset work, but the integrity of the entity
descriptions consumed by text-based KG systems is under-studied.

Why SIGIR fits: retrieval evidence quality, RAG faithfulness, ranking, KG search.

---

## 5. WSDM related work (venue-verified) and the closest technical neighbour

### WSDM context
- WSDM 2024 surveys and tutorials: RAG in the era of LLMs, a short survey on multilinguality in
  LLMs, ontology-learning perspective on domain adaptation, search engines meet LLMs, LLMs for
  recommendation. Broad framing lane, useful to justify importance for a web and search audience.
- WSDM 2024 KG papers: reliable KG path representation learning, structural graph wordification for
  LMs, plus KG-enhanced recommendation and reasoning. WSDM is receptive to KG-enhanced search and
  recommendation.

### Knowledge graph error detection (the closest technical neighbour, be honest)
This line finds wrong TRIPLES (bad edges) using structure and sometimes text. We find wrong
DESCRIPTIONS (bad text) using structure as the judge, framed as AI contamination, with a repair
loop. A reviewer will probe exactly this boundary.
- Contrastive KG Error Detection (CAGED; CIKM 2022, arXiv 2211.10030).
- KG Error Detection with Contrastive Confidence Adaption (arXiv 2312.12108).
- CKRL, KGTtm (earlier), EMKGEL for medical KGs (2024); note NELL is about 26 percent erroneous, a
  useful statistic on automatic-construction noise.

Why WSDM fits: web search, web data quality, multilingual retrieval, practical LLM search systems.
WSDM 2027 deadline is abstract Aug 17, paper Aug 24, 2026; a Findings track exists.

---

## 6. Cross-venue neighbours we must still cite

### AI pollution of corpora and Wikipedia quality (motivation)
- Wikipedia in the Era of LLMs: Evolution and Risks (arXiv 2503.02879, 2025). Warns RAG degrades if
  the KB is polluted.
- WETBench: detecting machine-generated text on Wikipedia incl. low-resource (arXiv 2507.03373,
  2025). Finds stylometric detectors struggle; the failing-baseline evidence for our style-invariant
  signal.
- How Good is Your Wikipedia? auditing low-resource and multilingual data quality (arXiv 2411.05527,
  2024).
- Measuring LLM-generated texts in multilingual disinformation (arXiv 2503.23242, 2025).

### Machine-generated text detection (the baseline we differentiate from)
Style-based and documented brittle, which is why a content-consistency signal is the open lane.
- CUDRT (ACM TIST 2025). Are AI Detectors Good Enough? survey (arXiv 2410.14677, 2024). Beyond Easy
  Wins hardness-aware benchmark (arXiv 2507.15286, 2025). GenAI Content Detection shared task (arXiv
  2501.08913, 2025).

### Multilingual factuality and KG grounding
- MultiHal: multilingual KG-grounded hallucination benchmark (arXiv 2505.14101, 2025). Oracle KG
  paths, six high-resource European languages, no retriever, no contamination.
- Evidence Graph Consistency in RAG (arXiv 2606.06748, 2026). Points at LLM outputs, not KB text.
- Improving Factuality via Inference-Time KG Construction (arXiv 2509.03540, 2025). Trusts the
  constructed facts.

### Multilingual, low-resource, inductive KGC (substrate)
- Multilingual KGs and Low-Resource Languages: A Review (TGDK / Dagstuhl 2024).
- KL-GMoE (EMNLP Findings 2025, arXiv 2510.07736), mRAKL (ACL Findings 2025, arXiv 2507.16011),
  KG-TRICK (COLING 2025, arXiv 2501.03560). mRAKL constructs KGs; KG-TRICK completes text and
  relations; neither cleans contamination.
- KEnS, AlignKGC, SS-AGA (2020 to 2022): classical transductive DBP-5L; cannot run on unseen
  entities (our substrate motivation).
- SimKGC (ACL 2022), BLP (WWW 2021), StATIK (NAACL 2022): English text-based inductive line our
  substrate extends. Wikidata5M-SI semi-inductive benchmark (arXiv 2310.11917).

---

## 7. Competitor matrix

| Line of work | What it solves | What it does not solve (our opening) |
|---|---|---|
| Retrieval collapse (WWW 2026) | shows AI pollution degrades web retrieval | no detection, no repair, no KG, not multilingual |
| CRAG / LiveRAG / RAG challenges | how to answer using retrieved evidence | whether the KB evidence is contaminated |
| SIGIR RAG papers | retrieval, ranking, context construction | upstream entity-description integrity |
| KG completion papers | missing link prediction | false descriptions attached to entities |
| KG error detection | bad triples and noisy edges | bad descriptions and LLM-fabricated biographies |
| Machine-generated text detection | whether text looks generated | whether text contradicts the graph |
| Multilingual factuality benchmarks | LLM performance gaps across languages | repairing contaminated multilingual KBs |

Our defensible open gap:

> A multilingual KB self-audit loop for AI-generated entity-description contamination, using
> graph-text consistency, with quarantine, re-sourcing, and downstream repair measurement,
> concentrated on low-resource languages.

---

## 8. Recommended venue positioning

### KDD
Title shape: Self-Healing Multilingual Knowledge Bases: Detecting and Repairing LLM-Generated
Entity-Description Contamination.
Contributions: characterise the contamination; build a benchmark with real and controlled
contamination; graph-text consistency detection; repair and measure downstream KGC and RAG gains.

### SIGIR
Title shape: Before Retrieval: Self-Auditing Multilingual Knowledge Bases for Faithful KG-RAG.
Contributions: show contaminated descriptions poison retrieval and grounding; detect via graph-text
consistency; repair evidence; measure retrieval and grounded-QA improvements.

### WSDM (nearest deadline, Aug 24 2026)
Title shape: Web-Scale Multilingual KB Self-Auditing for Reliable Retrieval-Augmented Systems.
Contributions: the web KB contamination phenomenon; its low-resource concentration; the retrieval
impact; the practical repair loop. Open with the WWW 2026 retrieval-collapse motivation.

---

## 9. Calibration and what to verify

- KDD Cup CRAG papers are challenge track, not KDD main research track. Cite as benchmark context.
- Drop or footnote low-relevance items (for example the WSDM 2025 "novel scientific ideas" paper).
- Confirm all 2026 arXiv identifiers and venue attributions on the source page before citing.
- Refresh once SIGIR 2026, KDD 2026, and WSDM 2026 proceedings are fully indexed; search each for
  knowledge graph, RAG, hallucination, generated text, multilingual, and data quality.
- Add exact BibTeX entries for the must-cite set before writing the related-work section.

## 10. Flat reference list (verify before citing)

Motivation and pollution: Retrieval Collapses (WWW 2026) https://arxiv.org/abs/2602.16136 ;
Wikipedia in the Era of LLMs https://arxiv.org/abs/2503.02879 ; WETBench
https://arxiv.org/abs/2507.03373 ; How Good is Your Wikipedia https://arxiv.org/abs/2411.05527 ;
multilingual disinformation https://arxiv.org/abs/2503.23242

MGT detection: CUDRT https://dl.acm.org/doi/10.1145/3779427 ; AI Detectors survey
https://arxiv.org/abs/2410.14677 ; hardness-aware benchmark https://arxiv.org/abs/2507.15286 ;
GenAI detection task https://arxiv.org/abs/2501.08913

KG error detection: CAGED https://arxiv.org/abs/2211.10030 ; Contrastive Confidence Adaption
https://arxiv.org/abs/2312.12108

RAG and factuality: CRAG https://arxiv.org/abs/2406.04744 ; CRAG-MM https://arxiv.org/abs/2509.09681 ;
LiveRAG report https://arxiv.org/abs/2507.04942 ; Evidence Graph Consistency in RAG
https://arxiv.org/abs/2606.06748 ; Inference-Time KG Construction https://arxiv.org/abs/2509.03540 ;
MultiHal https://arxiv.org/abs/2505.14101

Multilingual, low-resource, inductive KGC: Low-Resource KG review (TGDK 2024)
https://drops.dagstuhl.de/entities/document/10.4230/TGDK.1.1.10 ; KL-GMoE
https://arxiv.org/abs/2510.07736 ; mRAKL https://arxiv.org/abs/2507.16011 ; KG-TRICK
https://arxiv.org/abs/2501.03560 ; Shomer KDD 2025 inductive benchmark (search title) ;
Wikidata5M-SI https://arxiv.org/abs/2310.11917

SIGIR, KDD, WSDM proceedings: SIGIR 2024 https://dblp.org/db/conf/sigir/sigir2024.html ; WSDM 2024
https://dblp.org/db/conf/wsdm/wsdm2024.html ; AssetOpsBench https://arxiv.org/abs/2506.03828 ; KG
data layer https://arxiv.org/abs/2605.26874
