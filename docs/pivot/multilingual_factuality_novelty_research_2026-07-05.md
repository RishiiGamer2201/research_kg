# Multilingual Factuality Pivot: Novelty Ideas, Sources, and Senior Pitch

Date: 2026-07-05  
Purpose: preserve the deeper literature synthesis and the stronger research directions for the
senior meeting. This file focuses on making **multilinguality the main topic** and using
knowledge graphs as the technical solution, rather than presenting the work as only
"inductive KGC plus multilingual data."

---

## 1. Honest Assessment

The weak version of the current project is:

> Inductive knowledge graph completion already exists. We made it multilingual.

That framing is probably not strong enough for a top venue because it can look like a dataset
change plus a modest architecture change.

The stronger version is:

> Multilingual LLMs fail because factual knowledge is unevenly stored, retrieved, and expressed
> across languages. We use multilingual knowledge graphs to complete missing cross-lingual
> evidence for unseen or underrepresented entities, then ground LLM answers in the user's
> language.

This reframes the project from **knowledge graph completion** to **multilingual factuality and
low-resource language grounding**, with inductive MKGC as the engine inside the system.

---

## 2. Main Research Problem

Large language models can answer a fact correctly in English but fail, hallucinate, or become
inconsistent when the same query is asked in a lower-resource or typologically different
language. This happens because factual knowledge is not equally available across languages in:

- model pretraining data,
- multilingual KGs,
- entity descriptions,
- retrieval corpora,
- entity aliases and alignments,
- local/cultural knowledge sources.

The key phenomenon to name is:

> **Asymmetric multilingual factual coverage**

Meaning: a fact may exist in one language graph or high-resource source, but be missing or
weakly represented in another language. A user asking in the weaker language receives a worse
answer even though the fact exists somewhere in the multilingual ecosystem.

---

## 3. Recommended Paper Direction

Working title:

> **Inductive Cross-Lingual Evidence Graph Completion for Low-Resource Multilingual LLM Grounding**

Shorter alternative:

> **Cross-Lingual Evidence Completion for Multilingual LLM Factuality**

Core idea:

1. A user asks a factual question in a target language.
2. The system detects the language, entity, and relation intent.
3. It retrieves same-language KG evidence if available.
4. If evidence is missing, it retrieves aligned high-resource KG evidence.
5. An inductive MKGC module predicts missing tail facts for unseen or underrepresented entities.
6. A verifier checks graph consistency and confidence.
7. The LLM answers in the original language using completed KG evidence.

The novelty is not "we do KGC." The novelty is:

> **Completion-before-generation for multilingual factual grounding.**

Most RAG systems retrieve existing text. Most MKGC systems stop at ranking triples. This system
uses KG completion to reconstruct missing cross-lingual evidence before the LLM generates an
answer.

---

## 4. Architecture

```text
Low-resource user query
        |
        v
Language + intent parser
        |
        v
Entity linker / unseen entity creator
        |
        v
Cross-lingual evidence retriever
  - same-language KG facts
  - aligned high-resource KG facts
  - entity descriptions
  - support triples
        |
        v
Inductive MKGC completion module
  - BGE-M3 encoder
  - LoRA adaptation
  - CRR objective
  - hard negatives
  - unseen entity support facts
        |
        v
Graph consistency verifier
  - relation constraints
  - alignment consistency
  - confidence thresholds
  - contradiction checks
        |
        v
Grounded multilingual LLM answer
  - answer in user's language
  - cite/support KG evidence
  - abstain when evidence is weak
```

---

## 5. Strong Novelty Ideas

### Idea 1: Completion-Before-RAG

Most KG-RAG systems retrieve existing facts. They do not ask what happens when the target
language KG is incomplete. Our system first completes the missing cross-lingual evidence, then
uses it for LLM grounding.

Research claim:

> Retrieval alone cannot fix multilingual factual gaps when the target-language evidence is
> missing. Inductive cross-lingual KG completion can reconstruct evidence before generation.

### Idea 2: Asymmetric Factual Coverage Benchmark

Build or derive a benchmark where the same fact is available in one language graph but missing
or sparse in another. Measure:

- whether the LLM answers correctly in each language,
- whether translation-to-English helps,
- whether same-language KG-RAG helps,
- whether cross-lingual KG-RAG helps,
- whether KG completion before RAG helps most.

Research claim:

> Multilingual factuality should be evaluated by fact availability asymmetry, not only by
> final answer accuracy.

### Idea 3: Unseen Entity Multilingual Grounding

Many real entities are emerging, local, or under-described in low-resource languages. The LLM
has not memorized them, and the KG may only contain a few support facts.

Our existing DBP-5L-Ind work becomes useful here because it already evaluates unseen entities.

Research claim:

> Low-resource factual grounding is hardest for unseen entities; inductive MKGC provides a
> structured bridge from sparse support facts to grounded LLM answers.

### Idea 4: Cross-Lingual Consistency Verifier

Ask the same factual query in multiple languages. If the LLM gives different answers, use KG
alignment and graph completion to decide which answer is supported.

Research claim:

> Cross-lingual inconsistency can be reduced by verifying answers against a completed
> multilingual evidence graph.

### Idea 5: Low-Resource Evidence Routing

Design a routing module that decides where evidence should come from:

- native-language KG,
- aligned high-resource KG,
- entity descriptions,
- text retrieval,
- completed KG facts,
- abstention.

Research claim:

> The right evidence source depends on language-resource level, entity coverage, and relation
> type. A multilingual evidence router can improve grounding efficiency and accuracy.

### Idea 6: Multilingual Hallucination Reduction with Completed KGs

Evaluate hallucination reduction, not only KGC ranking. The output system should reduce:

- wrong entity answers,
- wrong relation answers,
- unsupported claims,
- language fallback to English,
- cross-language answer inconsistency.

Research claim:

> Completed multilingual KGs reduce hallucination by giving the LLM structured evidence where
> parametric memory and text retrieval are weak.

### Idea 7: Language-Faithful Factual Answering

The answer must be both correct and produced in the user's language. A system that translates
everything into English may answer correctly but still fail the multilingual user experience.

Research claim:

> Multilingual factuality requires both evidence correctness and language fidelity.

---

## 6. Best Positioning for the Senior

Say this:

> You are right that "inductive KGC but multilingual" may look like a dataset-level extension.
> I want to reframe the work around multilingual factual grounding. The problem is that LLMs
> answer inconsistently across languages because factual evidence is unevenly available. Our KG
> completion model becomes a component that reconstructs missing cross-lingual evidence for
> unseen or underrepresented entities before the LLM answers. So the main contribution is not
> just MKGC; it is low-resource multilingual factuality through inductive cross-lingual evidence
> completion.

Short version:

> We are not just completing multilingual KGs. We are completing missing multilingual evidence
> so that LLMs can answer factual questions reliably in low-resource languages.

---

## 7. Monday Deliverables

Prepare these three things:

1. **New architecture diagram**

   ```text
   Low-resource query
   -> entity/relation grounding
   -> cross-lingual KG retrieval
   -> inductive KG completion
   -> graph verifier
   -> grounded LLM answer
   ```

2. **One-page novelty statement**

   Main problem: asymmetric multilingual factual coverage.

   Main method: inductive cross-lingual evidence graph completion.

   Main outcome: more factual and language-faithful LLM answers in lower-resource languages.

3. **Small prototype table**

   Compare:

   - Vanilla LLM
   - Translate-to-English + LLM
   - KG-RAG without completion
   - KG-RAG + inductive KG completion
   - KG-RAG + completion + verifier

---

## 8. Evaluation Plan

### KGC Component Metrics

- MRR
- Hits@1
- Hits@3
- Hits@10
- within-language ranking
- cross-lingual ranking
- seen vs unseen entity split
- high-resource vs low-resource language split

### LLM Grounding Metrics

- exact answer accuracy
- alias-aware answer accuracy
- F1 or semantic similarity
- hallucination rate
- unsupported claim rate
- abstention correctness
- evidence precision
- evidence recall
- cross-lingual consistency
- target-language fidelity

### Key Ablations

- no KG evidence,
- text RAG only,
- KG retrieval only,
- KG retrieval + cross-lingual alignment,
- KG retrieval + inductive completion,
- KG retrieval + completion + verifier,
- native-language evidence only,
- English-pivot evidence only,
- mixed cross-lingual evidence.

---

## 9. Prototype Experiment for This Week

Use the current DBP-5L-Ind model and test triples.

Steps:

1. Sample 50-100 factual triples per language from DBP-5L-Ind test.
2. Convert triples into simple QA prompts in EN, FR, ES, JA, and EL.
3. Ask a local or API LLM without context.
4. Ask again with same-language KG facts retrieved.
5. Ask again with cross-lingual retrieved facts.
6. Ask again with completed KG evidence from our inductive model.
7. Measure answer accuracy and hallucination/unsupported-answer rate.

Expected table shape:

| Method | EN | FR | ES | JA | EL | Avg | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| Vanilla LLM | TBD | TBD | TBD | TBD | TBD | TBD | parametric memory only |
| Translate-to-English | TBD | TBD | TBD | TBD | TBD | TBD | English pivot |
| KG-RAG | TBD | TBD | TBD | TBD | TBD | TBD | retrieval only |
| KG-RAG + completion | TBD | TBD | TBD | TBD | TBD | TBD | our main method |
| KG-RAG + completion + verifier | TBD | TBD | TBD | TBD | TBD | TBD | full system |

---

## 10. Sources and Why They Matter

### Closest Multilingual KG / MKGC Papers

- [KL-GMoE: Multilingual Knowledge Graph Completion via Efficient Multilingual Knowledge Sharing](https://arxiv.org/abs/2510.07736)  
  Very close MKGC paper. Uses LLM-based multilingual knowledge sharing and reports gains over
  MKGC SOTA. Important because it makes plain "better MKGC" a crowded direction.

- [Multilingual Knowledge Graph Completion from Pretrained Language Models with Knowledge Constraints](https://arxiv.org/abs/2406.18085)  
  Shows PLM-based MKGC with global/local knowledge constraints. Important related work for
  multilingual KGC with pretrained models.

- [KG-TRICK: Unifying Textual and Relational Information Completion of Knowledge for Multilingual Knowledge Graphs](https://arxiv.org/abs/2501.03560)  
  Unifies textual and relational completion in multilingual KGs. Important because it also
  connects KG text and relation completion, but does not focus on LLM factual grounding.

- [mRAKL: Multilingual Retrieval-Augmented Knowledge Graph Construction for Low-Resourced Languages](https://arxiv.org/abs/2507.16011)  
  Reformulates multilingual KGC as QA for low-resource languages. Relevant because it connects
  retrieval, QA, and mKGC, but does not center multilingual LLM factuality with inductive
  evidence completion.

### Multilingual Hallucination and Factuality

- [MultiHal: Multilingual Dataset for Knowledge-Graph Grounded Evaluation of LLM Hallucinations](https://arxiv.org/abs/2505.14101)  
  Closest benchmark. Uses KG paths for multilingual hallucination evaluation. Our difference:
  real retrieval, lower-resource/typologically diverse languages, unseen entities, and
  completion-before-generation.

- [HalluVerse25: Fine-grained Multilingual Benchmark Dataset for LLM Hallucinations](https://arxiv.org/abs/2503.07833)  
  Fine-grained hallucination dataset for English, Arabic, and Turkish. Useful for hallucination
  categories: entity-level, relation-level, sentence-level.

- [Halluverse-M3: A Multitask Multilingual Benchmark for Hallucination in LLMs](https://arxiv.org/abs/2602.06920)  
  2026 multilingual hallucination benchmark across QA and dialogue summarization. Useful to
  show hallucination detection is active, but mitigation with completed KGs is still open.

- [KGHaluBench: A Knowledge Graph-Based Hallucination Benchmark](https://arxiv.org/abs/2602.19643)  
  KG-based hallucination benchmark. Useful related work for KG-generated factual evaluation,
  but not specifically multilingual inductive grounding.

- [MUCH: A Multilingual Claim Hallucination Benchmark](https://arxiv.org/abs/2511.17081)  
  Claim-level multilingual uncertainty/hallucination benchmark. Useful for claim-level
  unsupported answer evaluation.

### Cross-Lingual Consistency and Knowledge Barriers

- [Cross-Lingual Consistency of Factual Knowledge in Multilingual Language Models](https://arxiv.org/abs/2310.10378)  
  Shows factual knowledge varies across languages and proposes ranking-based consistency.
  Foundational for our cross-lingual consistency motivation.

- [Evaluating Knowledge-based Cross-lingual Inconsistency in Large Language Models](https://arxiv.org/abs/2407.01358)  
  Evaluates semantic, accuracy, and timeliness inconsistency across languages. Useful for
  motivating verifier metrics.

- [Crosslingual Capabilities and Knowledge Barriers in Multilingual Large Language Models](https://arxiv.org/abs/2406.16135)  
  Shows LLMs struggle with deeper cross-lingual knowledge transfer even when surface
  multilingual ability looks strong.

- [Do Multilingual Language Models Think Better in English?](https://arxiv.org/abs/2308.01223)  
  Shows translate/self-translate can improve multilingual performance, implying models often
  fail to use their full multilingual capability directly.

### Low-Resource and Local Knowledge Benchmarks

- [BLEnD: A Benchmark for LLMs on Everyday Knowledge in Diverse Cultures and Languages](https://arxiv.org/abs/2406.09948)  
  Shows LLMs lack culture-specific and local knowledge, especially for underrepresented
  cultures/languages.

- [MultiLoKo: A Multilingual Local Knowledge Benchmark for LLMs Spanning 31 Languages](https://arxiv.org/abs/2504.10356)  
  Shows large differences between languages and strong effects from question language. Very
  relevant to the "ask in Tamil/low-resource language" concern.

- [Learn Globally, Speak Locally: Bridging the Gaps in Multilingual Reasoning](https://arxiv.org/abs/2507.05418)  
  Studies multilingual reasoning fidelity and language-consistency rewards. Useful because it
  makes "answering in the target language" a measurable requirement.

### KG-RAG and Factuality

- [Improving Factuality in LLMs via Inference-Time Knowledge Graph Construction](https://arxiv.org/abs/2509.03540)  
  Dynamically constructs KGs at inference time for factuality. Adjacent to our idea, but not
  focused on multilingual low-resource evidence completion.

- [KERAG: Knowledge-Enhanced Retrieval-Augmented Generation for Advanced Question Answering](https://arxiv.org/abs/2509.04716)  
  KG-based RAG pipeline for broader subgraph retrieval and QA. Useful RAG baseline/related
  work, but not multilingual inductive MKGC.

- [MultiRAG: A Knowledge-guided Framework for Mitigating Hallucination in Multi-source RAG](https://arxiv.org/abs/2508.03553)  
  Handles conflicting multi-source retrieval with graph-guided reliability. Relevant for our
  verifier and contradiction-handling section.

- [Knowledge Graph-Guided Retrieval Augmented Generation](https://arxiv.org/abs/2502.06864)  
  Uses KG-guided chunk expansion and organization. Useful related work for KG-enhanced RAG,
  but mainly text-chunk oriented.

### KG Adaptation for Low-Resource Languages

- [Adapting Multilingual LLMs to Low-Resource Languages with Knowledge Graphs via Adapters](https://arxiv.org/abs/2407.01406)  
  Uses graph knowledge from linguistic ontologies with adapters for low-resource language
  tasks. Related but representation-level, not inference-time factual grounding.

- [MKG-Rank: Enhancing Large Language Models with Knowledge Graph for Multilingual Medical QA](https://arxiv.org/abs/2503.16131)  
  KG-enhanced multilingual medical QA. Strong evidence that KG grounding can help multilingual
  QA, but it is domain-specific and not focused on open-domain unseen entities.

---

## 11. How This Differs from Existing Work

| Existing line | What it does | Gap we target |
|---|---|---|
| Multilingual KGC | completes missing KG facts | usually stops at triple ranking, not LLM grounding |
| Multilingual hallucination benchmarks | measure hallucination across languages | often benchmark/evaluate, not complete missing evidence |
| KG-RAG | retrieves structured or text evidence | assumes evidence exists and can be retrieved |
| Cross-lingual consistency work | measures inconsistent facts across languages | usually does not use KG completion as mitigation |
| Translate-to-English prompting | pivots to English | can lose local language fidelity and entity nuance |
| Low-resource KG adaptation | improves representations | not a full answer-generation grounding system |

Our claimed open gap:

> No existing line fully combines low-resource multilingual factuality, unseen entity handling,
> real KG retrieval, inductive KG completion, graph verification, and target-language grounded
> answer generation.

---

## 12. Suggested Contributions

1. Define the problem of **asymmetric multilingual factual coverage** for LLM factuality.
2. Introduce a benchmark/task for low-resource factual QA under missing target-language KG
   evidence and unseen entities.
3. Propose **inductive cross-lingual evidence graph completion** before LLM answer generation.
4. Add a graph consistency verifier to reduce unsupported claims and cross-language
   contradictions.
5. Demonstrate gains over vanilla LLM, translate-to-English prompting, KG-RAG, and MKGC-only
   baselines.

---

## 13. Final Recommended Framing

Do not abandon DBP-5L-Ind. Reuse it as the evidence-completion module.

Old framing:

> We propose multilingual inductive KGC.

New framing:

> We study multilingual factuality failures in LLMs caused by asymmetric evidence availability.
> We propose a KG-based system that retrieves and completes missing cross-lingual evidence for
> unseen entities before generating grounded answers in the user's language.

This makes the paper about a real multilingual failure mode, with KGs as the solution.

