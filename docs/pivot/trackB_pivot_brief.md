# Track B Pivot Brief: Closing the LLM Multilingual Knowledge Gap with KG Retrieval

**Date: 2026-07-04. Purpose: literature check + concrete plan for the senior meeting (Monday).**
Question posed by senior: make multilinguality the main topic; find problems LLMs face in
multilinguality and solve them with knowledge graphs.

---

## 1. What is already established (measurement side)

The problem the senior described is real, named, and actively studied:

- **X-FACTR** (Jiang et al., EMNLP 2020) and **mLAMA** (Kassner et al., 2021): cloze-probing of
  factual knowledge in 23-53 languages. Finding: outside English and a few European languages,
  probing accuracy drops below 10%. The knowledge asymmetry is large and well documented.
- **Cross-Lingual Consistency** (Qi et al., EMNLP 2023; BMLAMA benchmark): even when a model
  knows a fact in two languages, its answers are often inconsistent; introduced the RankC
  metric. Follow-ups through 2026 study why (facts stored in an English-like conceptual space;
  failures happen at language transition, not knowledge storage).
- **Better To Ask in English?** (arXiv 2504.20022, Apr 2025): GPT-4o, Gemma-2, Llama-3.1 on
  English vs 19 Indic languages (IndicQuest). LLMs answer better in English even for questions
  rooted in the local context; more hallucination in low-resource languages. Purely
  evaluative, no fix proposed.
- **Multilingual hallucination estimation** (2025) and CCFQA (2025): the gap extends to
  hallucination rates across languages.

Conclusion: measurement alone is NOT novel anymore. A pivot paper cannot stop at "we measured
the gap." It must fix it, or explain it, or both.

## 2. What is already established (fixing side)

- **Multilingual RAG**: mRAG for knowledge-intensive tasks (2504.03616); language-preference
  analysis of mRAG systems (2502.11175: retrievers prefer query-language documents, models
  prefer high-resource content); DKM-RAG (fuses translated passages); Dialectic RAG (multi-step
  reasoning to resolve cross-lingual disagreement). All TEXT-passage retrieval, none KG-based,
  none low-resource-focused.
- **Cross-lingual knowledge editing**: a full subfield (survey 2505.14393, May 2025): edit a
  fact in English, propagate to other languages. Parameter-level, not retrieval; known problems
  with propagation. Adjacent, must cite, not our lane.
- **Consistency-driven RL** (2606.06586, Jun 2026): fine-tuning to improve cross-lingual recall.
  Parameter-level fix, needs training the LLM itself.
- **KG-for-low-resource adaptation**: GrEmLIn (graph-enhanced embeddings for 87 low-resource
  languages), KG-adapters. Representation-level, not RAG, not factual QA.

## 3. The closest prior work and the exact remaining gap

**MultiHal (arXiv 2505.14101, May 2025) is the paper to beat/differentiate.** It is a
multilingual KG-grounded hallucination benchmark with a KG-RAG baseline. Verified details:
- Languages: English + Spanish, French, Italian, Portuguese, German. All high-resource
  European; produced by machine translation (NLLB). No Greek, no Japanese, no Indic, no CJK.
- KG facts come from Wikidata; the "KG-RAG" baseline appends GOLD (oracle) paths to the prompt.
  There is NO retriever; retrieval is assumed solved.
- No per-language gap analysis (their own limitation: "multilinguality limited in typological
  diversity"); no unseen/emerging entities; injection method their own future work.

**Therefore the following combination is open as of mid-2026:**
1. KG-RAG for multilingual factuality with a REAL multilingual dense retriever over the KG
   (one shared embedding space, no translate-then-retrieve), instead of oracle paths.
2. Low-resource and typologically diverse target languages (Greek, Japanese; CJK + Greek
   script) with a per-language gap analysis: measure where the LLM fails, show retrieval gains
   concentrate exactly there.
3. **Unseen/emerging entities**: facts about entities the retriever was never trained on (our
   inductive split). Story: "a new entity appears in Tamil/Greek news today; the LLM has never
   seen it in any language; the KG ingests it; can retrieval make the LLM answer?" Nobody in
   the mRAG or MultiHal line touches this.
4. Retrieval-language policy analysis: retrieve native-language KG facts vs English-pivot facts
   vs cross-lingual retrieval (our cross-lingual eval showed the shared space costs only
   ~0.5 MRR; that finding becomes directly relevant).

Items 1+2+3 together are a defensible, problem-driven paper: "LLMs fail on low-resource and
emerging-entity facts; a single multilingual KG retriever closes most of the gap." Our existing
assets (DBP-5L-Ind, trained BGE-M3 retriever, per-language analyses) are the substrate.

## 4. Weekend experiment (evidence for Monday)

All local, no training, uses Ollama + our retriever + DBP-5L:
1. Sample ~500 test triples per language (EN/FR/ES/JA/EL) with unseen entities.
2. Template each into a QA prompt in the native language ("What is the capital of X?" style,
   from relation names; a translated template per relation type, or use the native entity
   names directly).
3. Ask a local LLM (llama3.2:3b now; qwen2.5 7b if available) with no context. Score exact/alias
   match against the gold tail. This yields the per-language knowledge-gap table.
4. Re-ask with top-k facts retrieved by OUR bi-encoder from the KG (support graph + train graph)
   prepended. Score again. This yields the gap-closing table, split by language and by
   seen/unseen entity.
5. Deliverable: one table + one chart: accuracy per language, vanilla vs KG-grounded, with the
   low-resource and unseen-entity deltas highlighted.

Risks to control: templated QA quality in JA/EL (use simple copular templates + native entity
names; imperfect grammar is acceptable for a prototype); answer matching (string + alias set
from the KG; report H@1-style accuracy); small LLM may be weak everywhere (also test one
stronger model via Ollama if bandwidth allows).

## 5. What to tell the senior (positioning)

- Concede: the current paper's architecture is not the contribution; it is a benchmark +
  first-baselines paper, and the acceptance risk assessment agrees with his instinct.
- Show: the measurement problem he described is real and named in the literature (X-FACTR,
  mLAMA, Better-To-Ask-In-English), so the pivot has a well-defined community; and the fix he
  sketched (KG grounding) has exactly one close competitor (MultiHal), which is high-resource
  only, oracle-grounded, and translation-based. Our differentiators: real retriever,
  low-resource focus, unseen entities.
- Bring: the weekend prototype table (Section 4) as first evidence, plus this brief.
- Venue implication: this line publishes at ACL/EMNLP/NAACL (ARR); MultiHal and Better-To-Ask
  are 2025 preprints, the field is hot but the specific combination is open. AAAI-27 (abstract
  Jul 21) is not a realistic target for the pivot; ARR (ACL/NAACL 2027 cycle) is. The current
  paper can still be finished for AAAI-27 in parallel or parked as the benchmark backbone of
  the pivot paper.

## 6. Must-cite list for the pivot

1. MultiHal (2505.14101): closest; KG-grounded multilingual hallucination benchmark, oracle paths.
2. Better To Ask in English? (2504.20022): the gap on low-resource Indic languages.
3. X-FACTR (Jiang et al. 2020) and mLAMA (Kassner et al. 2021): foundational gap measurement.
4. Cross-Lingual Consistency / BMLAMA (Qi et al., EMNLP 2023) + the 2026 mechanistic follow-ups.
5. Multilingual RAG line: 2504.03616 (mRAG knowledge-intensive), 2502.11175 (language
   preference), DKM-RAG, Dialectic RAG.
6. Multilingual knowledge editing survey (2505.14393) as the parameter-level alternative lane.
7. Consistency-driven RL (2606.06586) as the training-level alternative lane.
8. MLPQ / multilingual KGQA surveys for the KGQA-classic lane.
9. Our own substrate line: DBP-5L (Chen et al. 2020), SimKGC, BGE-M3.
