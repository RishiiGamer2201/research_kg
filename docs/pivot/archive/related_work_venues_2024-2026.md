# Related Work at SIGIR, KDD, WSDM and Neighbours (2024 to 2026)

Compiled 2026-07-07 for the self-healing knowledge base direction. Grouped by theme, with venue
and year where known, a one-line summary, and how each relates to our idea (motivation, competitor,
context, or neighbour). Read Section 1 first: it is the single most important paper to position
against. Section 9 is the gap map. Section 11 is the flat reference list.

Verification note: several 2026 arXiv identifiers were captured from search and should be
confirmed on the arXiv or ACM page before they enter a bibliography.

---

## 1. The single most important neighbour: retrieval collapse under AI pollution

**Retrieval Collapses When AI Pollutes the Web** (Yu et al., NAVER; ACM Web Conference / WWW 2026;
arXiv 2602.16136). Characterises "retrieval collapse": AI-generated content comes to dominate
search results, source diversity erodes, and low-quality or adversarial content infiltrates the
retrieval pipeline. In their controlled study a 67 percent contaminated pool produced over 80
percent contaminated exposure, a "deceptively healthy" state where accuracy looks stable while the
evidence is quietly synthetic.

Why it matters to us: this is the strongest possible motivation for our thesis, published at a top
venue, that AI pollution degrades retrieval systems. It establishes the disease. But it studies
web text corpora, measures the effect on retrieval, and stops there. It does not detect or repair
pollution, does not use knowledge graphs, and is not multilingual. Our differentiation in one
line: they show AI pollution collapses web retrieval; we detect and repair AI pollution inside a
multilingual knowledge base using the graph's own structure, and measure the downstream repair.
Cite it as motivation, not a competitor.

---

## 2. AI-generated content pollution of corpora and knowledge bases (motivation)

- **Wikipedia in the Era of LLMs: Evolution and Risks** (arXiv 2503.02879, 2025). Measures LLM
  influence on Wikipedia (1 to 2 percent in some categories) and warns RAG degrades if the KB is
  polluted. Motivation; does not build a defence.
- **WETBench: detecting task-specific machine-generated text on Wikipedia** (arXiv 2507.03373,
  2025). Multilingual, includes lower-resource languages; finds stylometric detectors struggle.
  Motivation and the failing-baseline evidence for our style-invariant signal.
- **How Good is Your Wikipedia? Auditing data quality for low-resource and multilingual NLP**
  (arXiv 2411.05527, 2024). Systematic low-resource Wikipedia quality issues incl. bot-generated
  content and script contamination. Motivation for the low-resource concentration.
- **Beyond speculation: measuring LLM-generated texts in multilingual disinformation** (arXiv
  2503.23242, 2025). Measures growing machine-generated presence across languages. Supports our
  "70 percent found in the wild, worst in low-resource" framing.

## 3. Machine-generated text detection (the baseline we differentiate from)

This whole line detects AI text by how it is written (stylometry, watermarks, curvature, learned
classifiers). We differentiate because our signal is factual agreement with structure, not style.
- **CUDRT: reliable detection of LLM-generated texts, evaluation framework** (ACM TIST, 2025).
- **Are AI Detectors Good Enough? Survey on dataset quality for machine-generated text** (arXiv
  2410.14677, 2024).
- **Beyond Easy Wins: a text-hardness-aware benchmark for LLM-generated text detection** (arXiv
  2507.15286, 2025). Shows detectors do well on easy text and poorly on hard text, reinforcing
  that stylometry is brittle.
- **GenAI Content Detection (shared task)** (arXiv 2501.08913, 2025) and **NOTAI.AI** (2603.05617,
  2026). Detection challenges and explainable variants.
Takeaway: the dominant defence is style-based and documented as brittle; a content-consistency
defence is the open lane.

## 4. Knowledge graph error detection and data quality (closest technical neighbour)

This is the nearest prior art to our detector, and the honest one to differentiate from. It finds
wrong TRIPLES (bad edges) using structure and sometimes text. We find wrong DESCRIPTIONS (bad text)
using structure as the judge, framed as AI contamination, with a repair loop.
- **Contrastive Knowledge Graph Error Detection** (CAGED; CIKM 2022, arXiv 2211.10030).
  Multi-view contrastive learning over a triple hyper-graph to score triple credibility.
- **CKRL, KGTtm** (earlier). Confidence-aware and trust-based triple noise detection.
- **EMKGEL: enhancing error detection on medical KGs via intrinsic label** (2024). Domain error
  detection; notes automatic construction introduces noise (NELL about 26 percent erroneous).
- General note across this line: targets structural errors, assumes descriptions are not the
  object of audit, and has no multilingual or contamination framing.

## 5. KG-RAG, factuality, and hallucination (downstream and application context)

Where our repair connects to LLM factuality. Useful for the downstream grounding experiment and
related work, not competition for the detector.
- **Rowen: adaptive RAG for hallucination mitigation** (SIGIR-AP 2025).
- **Knowledge Graph-Guided RAG** (arXiv 2502.06864, 2025).
- **Walk and Retrieve: zero-shot KG-walk RAG** (arXiv 2505.16849, 2025).
- **Evidence Graph Consistency in RAG: model-dependent hallucination detection** (arXiv 2606.06748,
  2026). Uses evidence-graph consistency to detect hallucination in RAG outputs; note this points
  at the LLM's output, not the KB's stored descriptions.
- **Improving Factuality via Inference-Time KG Construction** (arXiv 2509.03540, 2025). Builds KGs
  at inference for factuality; assumes constructed facts are trustworthy.
- **MultiHal: multilingual KG-grounded hallucination benchmark** (arXiv 2505.14101, 2025). Oracle
  KG paths, six high-resource European languages, no retriever, no contamination. Nearest
  multilingual KG-factuality benchmark; we differ on retrieval, low-resource, and contamination.

## 6. Multilingual and low-resource KGC (our substrate context)

- **Multilingual Knowledge Graphs and Low-Resource Languages: A Review** (TGDK / Dagstuhl, 2024).
  Good survey to frame the low-resource motivation.
- **KL-GMoE: multilingual KGC via efficient knowledge sharing** (Findings of EMNLP 2025, arXiv
  2510.07736). Transductive, custom Wikidata5M, no Greek. Substrate related work.
- **mRAKL: multilingual retrieval-augmented KG construction for low-resource languages** (Findings
  of ACL 2025, arXiv 2507.16011). Retrieval-augmented QA for low-resource mKGC (Tigrinya, Amharic).
  Nearest competitor to the completion-before-RAG alternative; constructs KGs, does not clean them.
- **KG-TRICK: unifying textual and relational completion for multilingual KGs** (COLING 2025, arXiv
  2501.03560). Completes descriptions and relations; no contamination or grounding.
- **KEnS, AlignKGC, SS-AGA** (2020 to 2022). The classical transductive DBP-5L line; cannot run on
  unseen entities (our substrate motivation).

## 7. Inductive KGC and benchmarks (substrate positioning)

- **Towards better benchmark datasets for inductive knowledge graph completion** (Shomer et al.,
  KDD 2025). Directly relevant: argues current inductive-KGC benchmarks are flawed and proposes
  better ones. This is the paper to cite and differentiate DBP-5L-Ind against, and it confirms KDD
  cares about inductive-KGC benchmark quality (good sign for the Datasets and Benchmarks track).
- **Model Graph Inductive Learning for KGC** (arXiv 2606.16509, 2026). Recent inductive method.
- **SimKGC (ACL 2022), BLP (WWW 2021), StATIK (NAACL 2022)**. The English text-based inductive line
  our substrate extends to multilingual.
- **A Benchmark for Semi-Inductive Link Prediction (Wikidata5M-SI)** (arXiv 2310.11917). Split-
  construction precedent.

---

## 8. What each venue tends to reward (for choosing the framing)

- **WSDM** (web search and data mining): web-scale data quality, retrieval, KGs. The pollution and
  retrieval angle (Section 1) plus our detector fits the "Web Mining and Content Analysis" area.
  Aug 24 2026 deadline; Findings track exists.
- **KDD** (data mining): benchmarks and datasets (dedicated track), KG mining, data quality. The
  contamination benchmark and the inductive-KGC benchmark both fit; Shomer 2025 shows appetite.
- **SIGIR** (information retrieval): retrieval, RAG, factuality, evaluation. The retrieval-repair
  and grounding angle fits; the RAG-hallucination line (Section 5) lives here.

## 9. The gap map

| Line of work | What it does | What it does NOT do (our opening) |
|---|---|---|
| Retrieval collapse (WWW 2026) | shows AI pollution degrades web retrieval | no detection, no repair, no KG, not multilingual |
| MGT detection | detect AI text by style | fails on fluent text; ignores factual consistency with structure |
| KG error detection | find wrong triples | does not audit descriptions; no contamination or multilingual framing |
| KG-RAG / factuality | ground or check LLM outputs | trusts the KB; points outward at outputs, not inward at KB text |
| Multilingual and inductive KGC | complete missing facts | assumes clean text; no contamination detection or repair |

Our specific open combination: detect AI-contaminated descriptions inside a multilingual KB using
the graph's own structure (training-free), concentrated on low-resource languages, and measure the
downstream repair on completion and grounding. No single line above covers this.

## 10. How to use this for the paper

- Related work spine: pollution motivation (Section 1 and 2), the failing style-based defence
  (Section 3), the closest technical neighbour KG error detection (Section 4), and the downstream
  factuality context (Section 5). Then state the gap (Section 9).
- Substrate positioning: cite Shomer KDD 2025 on inductive-KGC benchmarks and the multilingual
  line (Section 6 and 7), and frame DBP-5L-Ind as the first multilingual entity-disjoint inductive
  benchmark that also serves as the contamination testbed.

## 11. Reference list (verify identifiers before citing)

Motivation and pollution
- Retrieval Collapses When AI Pollutes the Web, WWW 2026: https://arxiv.org/abs/2602.16136
- Wikipedia in the Era of LLMs, 2025: https://arxiv.org/abs/2503.02879
- WETBench, 2025: https://arxiv.org/abs/2507.03373
- How Good is Your Wikipedia?, 2024: https://arxiv.org/abs/2411.05527
- Measuring LLM-generated multilingual disinformation, 2025: https://arxiv.org/abs/2503.23242

Machine-generated text detection
- CUDRT (ACM TIST 2025): https://dl.acm.org/doi/10.1145/3779427
- Are AI Detectors Good Enough? (survey), 2024: https://arxiv.org/abs/2410.14677
- Beyond Easy Wins (hardness-aware benchmark), 2025: https://arxiv.org/abs/2507.15286
- GenAI Content Detection shared task, 2025: https://arxiv.org/abs/2501.08913

KG error detection and quality
- Contrastive KG Error Detection (CAGED), 2022: https://arxiv.org/abs/2211.10030
- Enhancing Error Detection on Medical KGs (EMKGEL), 2024: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10968158/

KG-RAG, factuality, hallucination
- Rowen (SIGIR-AP 2025): https://dl.acm.org/doi/10.1145/3767695.3769500
- Knowledge Graph-Guided RAG, 2025: https://arxiv.org/abs/2502.06864
- Walk and Retrieve, 2025: https://arxiv.org/abs/2505.16849
- Evidence Graph Consistency in RAG, 2026: https://arxiv.org/abs/2606.06748
- Improving Factuality via Inference-Time KG Construction, 2025: https://arxiv.org/abs/2509.03540
- MultiHal, 2025: https://arxiv.org/abs/2505.14101

Multilingual, low-resource, inductive KGC and benchmarks
- Multilingual KGs and Low-Resource Languages: A Review (TGDK 2024): https://drops.dagstuhl.de/entities/document/10.4230/TGDK.1.1.10
- KL-GMoE, EMNLP Findings 2025: https://arxiv.org/abs/2510.07736
- mRAKL, ACL Findings 2025: https://arxiv.org/abs/2507.16011
- KG-TRICK, COLING 2025: https://arxiv.org/abs/2501.03560
- Towards better benchmark datasets for inductive KGC, KDD 2025: search "Shomer KDD 2025 inductive knowledge graph completion benchmark"
- Model Graph Inductive Learning for KGC, 2026: https://arxiv.org/abs/2606.16509
- Wikidata5M-SI semi-inductive benchmark: https://arxiv.org/abs/2310.11917
