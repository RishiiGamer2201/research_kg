# Novel Research Directions: Ideation + Novelty Verification (2026-07-05)

Context: senior wants something entirely novel, multilinguality as the main topic, KGs as the
tool. His Tamil/KG-RAG suggestion was an example, not a constraint. This doc ranks four
candidate directions. Novelty was checked by web literature sweeps covering work through
June-July 2026 explicitly (not just 2025).

---

## Idea 1 (RECOMMENDED): Self-healing knowledge bases

**One-line pitch:** knowledge bases are silently filling with confident AI-generated
fabrications, worst in low-resource languages, and the graph structure itself can detect and
repair its own contaminated text.

**The discovered phenomenon (ours, in the wild):** our KB's LLM back-filled descriptions were
about 70% fabricated (Clint Eastwood became a Greek footballer; Taipei became a dessert), the
contamination concentrated in the two low-resource languages, and it measurably hurt downstream
use (removing it gave +1.95 MRR on Japanese). Key observation: the fabricated text CONTRADICTS
the entity's own graph neighborhood (film/directing edges vs footballer text). Structure and
text are two independent witnesses of the same entity; their disagreement is a training-free
contamination signal.

**The paper:** (1) name and characterize the phenomenon (entity-level contamination of
multilingual KBs by generated text); (2) a detection method: text-graph consistency scoring
(NLI or judge between description and serialized neighborhood), no training required, works
regardless of which generator produced the text; (3) a benchmark with real in-the-wild labeled
contamination (our audit) plus controlled injections at known rates; (4) the closed loop:
detect, quarantine, re-source, and measure downstream repair on retrieval/KGC (we already have
the before/after numbers).

**Novelty verification (through Jul 2026):**
- Motivation exists and is fresh: WETBench (2507.03373) benchmarks machine-generated-text
  detection on Wikipedia incl. lower-resource languages and finds stylometric detectors
  struggle; "Wikipedia in the Era of LLMs" (2503.02879) measures 1-2% LLM influence and warns
  that RAG degrades if the knowledge base becomes polluted; "How Good is Your Wikipedia?"
  (2411.05527) audits low-resource Wikipedia quality. None uses graph structure; all are
  text-classifier or audit studies.
- Fact-checking-with-KG lane (FactKG, GraphCheck 2502.20785, hybrid pipelines 2511.03217)
  verifies external claims or LLM outputs against a KG. Nobody audits the KB's OWN textual
  layer against its structural layer.
- KG noise-detection literature targets wrong triples, not contaminated descriptions.
- Graph Fusion Across Languages (2603.21248, Mar 2026): entity alignment/fusion, no
  contamination or repair. Deterministic-KG monitoring of generative AI (2509.03857): monitors
  LLM outputs, not KBs.
- Verdict: the loop (structural self-audit of KB text, quarantine, re-source, downstream repair
  measurement, multilingual and low-resource focused) is UNCLAIMED as of this sweep.

**Why it is strong:** new named problem; training-free method orthogonal to stylometric
detectors (works even when the generator is undetectable stylistically); real labeled
contamination instead of only synthetic; measured downstream impact; timely (everyone's KB is
ingesting generated text); runs on our hardware; our benchmark/retriever work becomes the
evaluation substrate rather than dead work.

**Monday demo:** automatic detector scored against the 25 hand-labeled contaminated samples
(+25 clean controls), plus the +1.95 repair table. Buildable in a weekend on Ollama.

**Risks:** description-only KB entities (no neighborhood to check) limit coverage: quantify;
concept/common-noun entities where the LLM text was fine: the detector should pass them
(specificity test); reviewers may ask for a second KB (Wikidata slice) for generality: doable
later.

## Idea 2: Fact-level knowledge equity atlas

Probe an LLM with ALIGNED KG facts (same fact, five languages) and build the access matrix
(facts x languages): which facts exist for whom; equity metrics; analysis by script,
popularity, entity type; extendable to unseen entities.
- 2026 check: Cross-Lingual Exploration for Parametric Knowledge (2606.24579, Jun 2026) is
  analysis-only, translation-based, no KG alignment, no access matrix, no unseen entities.
  Entity-level alignment work (2510.10280) explains consistency mechanisms. IndicKLAR (May
  2026) does knowledge consistency for Indic. BMLAMA exists for balanced probing.
- Verdict: the KG-aligned fact-access-matrix framing is available but the probing space is
  crowded; better as the measurement SECTION of Idea 1 or 4 than as a standalone paper.

## Idea 3: Knowledge propagation latency for emerging entities across languages

When a new entity appears in one language's sources, how long until LLM/RAG systems can answer
about it in other languages; what controls propagation (script, alignment, source coverage).
- 2026 check: nothing found combining emerging entities x multilinguality x propagation.
- Verdict: genuinely open, but requires temporal data collection and a monitoring harness;
  right as the follow-up project, wrong for a Monday pitch.

## Idea 4: Multilingual KG-RAG with a real retriever (the earlier Track B brief)

Still open vs MultiHal (oracle paths, high-resource only, no retriever, no unseen entities),
but it improves a known recipe rather than naming a new problem. Keep as fallback or as the
application chapter of the program.

## The research program (how they compose)

Idea 2 (measure the gap) -> Idea 1 (clean and self-heal the KB) -> Idea 4 (ground the LLM with
the clean KB) -> Idea 3 (keep it current as the world changes). Lead Monday with Idea 1;
present the program as the arc. Venue for Idea 1: ACL/EMNLP (ARR) or WWW/CIKM (web/KB angle);
the dataset+method+repair-loop shape fits both.
