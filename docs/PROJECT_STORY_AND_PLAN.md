# The Project, From Basics to the New Plan: A Study and Presentation Guide

**Written 2026-07-05, updated 2026-07-07 for the senior meeting today.** This document explains
the whole project in plain language: the fundamentals, what we originally built, what we
discovered, what the senior asked for, the new direction, the first result, the literature check,
and the venue and plan. Read it top to bottom once to learn the arc, then use the section headings
as your talking points. For the meeting, Sections 0, 6, and 10 are the briefing core.

Style note: no shorthand dashes or emojis anywhere, so it stays clean if pasted elsewhere.

---

## UPDATE 2026-07-17 (read this first; the body below is the pre-meeting narrative and is now partly superseded)

This document was written 2026-07-05/07 for the senior meeting, before the direction was settled. It
is still the best plain-language explanation of the fundamentals, the original system, and the
discoveries (Sections 1 to 5, 9, 11), so read those. But four things have changed since, and where the
body disagrees with this banner, the banner wins:

1. Direction settled: the mentor chose a bottom-up ladder, reproduce S2DN (AAAI 2025 inductive KGC),
   beat it on English inductive with neuro-symbolic modifications, extend to multilingual, then add
   self-healing. The modifications target both of S2DN's branches, not just one: rule-guided Structure
   Refining (RuleTrust, Phase B) and similarity-guided Semantic Smoothing (Phase B2), plus anything
   else that makes the architecture novel and better (mentor answer 5). RuleTrust is the first branch
   under test, not the whole contribution. Which modifications survive is decided by results, not
   pre-committed. This ladder is now merged with the external gap plan into the single plan of record,
   `docs/pivot/UNIFIED_PATHWAY.md`. Section 6 and 10 below (the "two candidate directions" and the
   venue plan) are superseded by it.

2. Venue changed: WSDM 2027 (Section 10) is NOT the target. Decision 2026-07-17 is A-star only, so
   SIGIR 2027 is primary (late-January-style deadline, gives about six months of runway), with WSDM
   and KDD Cycle 2 as fallbacks. Ignore the WSDM crunch timeline in Section 10.

3. SOTA moved: SS-AGA (2022), the transductive anchor cited throughout, is superseded by SimRMKGC
   (2025). And S2DN itself is not the current inductive SOTA (MorsE, CATS, MGIL, and the foundation
   model ULTRA postdate or outrank it). See `docs/pivot/sota_benchmark_survey_2026-07-17.md`. The paper
   must compare against those, not just S2DN.

4. Progress since: S2DN reproduced on WN18RR (v1-v4) and FB15k-237 v1 (beats paper); NELL v1-v4
   reproducing now; RuleTrust built but its gain is inside single-seed noise (seeds deferred to the
   end, run once on the locked-in models); DBP-5L to GraIL converter done; the self-healing detector
   mechanism designed with real data. Current status and next steps live in `UNIFIED_PATHWAY.md`
   Sections 0a, 0b, and 10, not here.

Current reading order: this banner, then Sections 1 to 5 and 9 and 11 below for the fundamentals, then
`docs/pivot/UNIFIED_PATHWAY.md` for the actual plan.

---

## 0. The thirty-second summary

We built a system that completes facts in a multilingual knowledge graph for entities the model
has never seen before (headline 26.51 MRR over three seeds, beating a 2019 encoder baseline).
Along the way we discovered that a knowledge base can be silently poisoned by confident, wrong,
AI-generated text, worst of all in low-resource languages, and that the graph's own structure can
catch and repair those lies. The original system becomes the foundation. The new headline is the
self-healing knowledge base: a genuinely new problem that makes multilinguality the centre of the
story, which is exactly what the senior asked for.

Current state for the meeting: the pivot already has evidence. We found about 70 percent of our
LLM-written descriptions were fabricated; a training-free structural detector separates real from
fake at ROC-AUC 0.995; and removing the contamination improved Japanese completion by 1.95 MRR.
Two independent literature sweeps confirm no one at SIGIR, KDD, or WSDM has done this. The concrete
target is WSDM 2027 (full paper Aug 24, 2026), with the fused paper reusing the finished substrate
so it is deliverable in the window.

---

## Table of contents
1. Fundamentals you must be able to explain
2. What the project was originally
3. What we actually built and the numbers
4. The journey: what we discovered and fixed
5. The senior's critique, stated fairly
6. The new direction: self-healing knowledge bases
7. Why the new direction is novel (checked against 2025 and 2026 work)
8. How the new plan aligns with what the senior wants
9. Nothing is wasted: how the old work becomes the foundation
10. The plan, the venue (WSDM 2027), and the timeline
11. Glossary and quick answers to likely questions

---

## 1. Fundamentals you must be able to explain

Before the project, be fluent in these four ideas. If you can explain them simply, you control
the room.

**Knowledge graph (KG).** A KG stores facts as triples: (head, relation, tail). For example
(Clint Eastwood, directed, Unforgiven). Entities are nodes; relations are labelled edges.
Wikidata, DBpedia, and Freebase are large public KGs.

**Knowledge graph completion (KGC).** KGs are always incomplete. KGC predicts missing facts.
The standard task is link prediction: given (head, relation, ?), rank all candidate entities for
the missing tail. Quality is measured by whether the correct tail is ranked near the top.

**Metrics.** MRR (mean reciprocal rank): if the correct answer is at rank r, the score is 1/r,
averaged over all test queries. Higher is better, 100 percent is perfect. Hits@k: the fraction
of queries where the correct answer is in the top k. We report MRR and Hits@1, 3, 10. "Filtered"
means we remove other known-true answers from the ranking so the model is not penalised for
ranking a different correct answer highly.

**Transductive versus inductive.** This distinction is the heart of the original project.
- Transductive: every entity is seen during training. The model learns a fixed vector (an
  embedding) for each entity. It cannot say anything about an entity it never saw, because that
  entity has no vector.
- Inductive: some entities are unseen at training time. The model must handle a brand-new entity
  the moment it appears. The trick that makes this possible: represent an entity by encoding its
  text (its name and description) with a language model, rather than by a memorised vector. A new
  entity is handled by reading its description on the fly.

**Multilingual KGC.** The KG exists in several languages, each as its own sub-graph, with some
entities linked across languages (alignment links). Low-resource languages have small, sparse
sub-graphs. In our data the five languages are English, French, Spanish, Japanese, and Greek,
with Greek as the low-resource one.

One sentence that ties it together: our original task was to complete facts about unseen entities
(inductive) in a knowledge graph that spans several languages including a low-resource one
(multilingual).

---

## 2. What the project was originally

**The original thesis.** Two lines of research existed separately. Inductive KGC had been done,
but only in English. Multilingual KGC had been done, but only transductively (all entities seen).
Nobody had combined them: unseen entities, described in multiple languages, including a
low-resource one. So the plan was to be first at that intersection, build the benchmark for it,
and train a model that works there on a single consumer GPU (a 16 GB RTX 5070 Ti).

**The two deliverables of the original plan.**
1. A benchmark, DBP-5L-Ind: the first entity-disjoint inductive split of the standard DBP-5L
   multilingual dataset. "Entity-disjoint" means we hold out a set of entities entirely from
   training and only test on them, which forces the inductive setting.
2. A model: a text bi-encoder. We take BGE-M3 (a strong multilingual text encoder, 568 million
   parameters, built on XLM-RoBERTa), fine-tune it cheaply with LoRA (small trainable adapters,
   about 8 million parameters, the backbone frozen), and train it with a contrastive objective so
   that a query like "[head description] [relation]" lands near the correct tail entity's
   description in vector space. We added two refinements from recent papers: the CRR loss (a loss
   function that directly optimises ranking) and hard-negative mining (training against the most
   confusable wrong answers).

**How it works in one picture.** Encode every candidate entity's description into a vector once
and cache it. For a query (head, relation, ?), encode the query text into a vector, and rank
candidates by cosine similarity. A never-before-seen entity simply gets encoded from its text and
dropped into the index. No retraining needed. That is what makes it inductive, and because
BGE-M3 is multilingual, it is multilingual for free.

---

## 3. What we actually built and the numbers

**The benchmark, DBP-5L-Ind.** From DBP-5L (56,589 entities, five languages, about 226k triples),
we hold out 20 percent of entities per language as unseen. Result: 35,848 training entities,
8,959 unseen test entities, 118,256 training triples, 54,473 evaluation triples. Each unseen
entity keeps a few support edges as context. We also enrich every entity with a text description
from three sources: its name, a serialisation of its graph neighbourhood, and native-language
Wikipedia abstracts.

**The final model and result.** The best configuration is BGE-M3 plus LoRA rank 16, trained with
CRR loss and hard negatives, reading descriptions up to 160 tokens long. Its score, averaged over
three random seeds, is 26.51 MRR with a standard deviation of 0.31 (very stable). For comparison:

| Configuration | MRR | Meaning |
|---|---|---|
| Zero-shot BGE-M3 (no fine-tuning) | 1.45 | the floor |
| Our full model (3 seeds) | 26.51 | 18 times the floor |
| mBERT baseline (older encoder, same recipe) | 24.08 | shows the modern encoder matters |

**Per-language, our model.** French 37.3, Spanish 36.6, English 17.2, Greek 16.8, Japanese 16.2.

**Calibration against the easier transductive setting.** The 2022 transductive state of the art
(SS-AGA) scores Greek 35.3 and Japanese 42.9, but those methods see all entities during training
and cannot run at all in our unseen-entity setting. On the higher-resource languages our
inductive numbers actually reach or exceed their transductive numbers (French, Spanish), which is
a strong result. On the low-resource languages a gap remains, which is expected.

**The honest reading of these results.** The system works and the benchmark is real. But the
model is a careful assembly of existing parts (BGE-M3, LoRA, CRR, hard negatives are all borrowed
or standard). The contribution is the benchmark plus the first baselines plus the empirical
findings, not a new architecture. Hold this thought; it is exactly what the senior objected to.

---

## 4. The journey: what we discovered and fixed

This section matters because it shows research maturity, and two of the discoveries are what led
to the new idea. Present these as "we did not just run experiments, we found and corrected real
problems."

**Discovery 1: an evaluation bug that hid the true performance.** Our evaluation was truncating
descriptions to 96 tokens while the model was trained on longer text. Fixing it lifted the
headline from a mismeasured 15.59 to the correct 24.76 (and later 26.51 across seeds). It also
reversed a wrong conclusion: we had thought longer context did not help, when in fact it did,
especially for Japanese, whose text uses many tokens.

**Discovery 2: a false negative result, caught before publication.** We had a finding that
"explicit cross-lingual anchors hurt performance a lot" (a drop to about 3 percent). On
investigation this was an artifact: the model was trained one way and evaluated another way.
Evaluated correctly, the same model scored about 20 percent, not 3. We retracted the claim.
Publishing it would have been wrong, and reviewers familiar with that technique would have caught
it. We caught it ourselves.

**Discovery 3, the important one: the knowledge base was contaminated with AI-generated lies.**
To fill descriptions for entities that lacked Wikipedia coverage (only the low-resource Greek and
Japanese entities needed this), we had used a small LLM (Llama 3.2) to generate descriptions.
When we audited them, about 70 percent were confident fabrications. The model could not recognise
a foreign name written in Greek or Japanese script, so it invented a plausible biography.
Examples we verified by hand:
- Clint Eastwood (written in Greek) became "a Greek professional footballer for PAOK."
- Taipei, the city, became "a traditional Cypriot dessert."
- Eleanor Roosevelt became "a Greek actress."
- William Henry Harrison, a US president, became "a Governor of Barbados."

And crucially: when we removed this fabricated text, Japanese performance improved by 1.95 MRR.
The lies were actively hurting the system, and the harm was concentrated in the weakest,
lowest-resource languages.

**Discovery 4: cross-lingual robustness.** When we rank a query against all 56,589 entities in
every language at once, instead of just the same-language candidates, performance drops by only
about half a point. The model almost never confuses a wrong-language entity for the right one.
This says the encoder's built-in cross-lingual alignment is already strong.

Discoveries 3 and 4 are the seeds of the new direction.

---

## 5. The senior's critique, stated fairly

He raised three things, and he is substantially right on the main one.

1. "Inductive KGC was already done; you are making basic architecture changes and just swapping
   the dataset." Correct that the architecture is not novel. Partly incomplete in that inductive
   KGC was done only in English, and the dataset swap is what breaks all prior multilingual
   methods, which is itself a finding. But his core instinct stands: the paper answers "can this
   be done" and the answer is a slightly anticlimactic "yes, with a good encoder."

2. "Multilingual is bolted onto knowledge graph completion; make multilingual the main topic."
   This is good taste. A setting ("we added languages") is weaker than a problem ("here is
   something that goes wrong in multilingual settings, and here is how we fix it").

3. "Find something entirely novel, a problem not introduced before." Fair, and the honest way to
   meet it is not to combine two existing labels (which is what multilingual-plus-inductive was),
   but to name a phenomenon nobody has named.

The right response is to concede point 1 openly (it disarms the objection and shows maturity),
and to answer points 2 and 3 with the new direction below.

---

## 6. The pivot: two candidate directions, the competitor check, and the recommendation

There are two serious pivot proposals on the table. Both are written up in the `docs/design`
folder. This section lays out both fairly, then the competitor reality check, then the
recommended fused direction. Read it as a decision, not a foregone conclusion.

### 6.1 The phenomenon we actually discovered (the seed of everything)

In Discovery 3 we saw our own KB polluted with confident, wrong, AI-generated text, roughly 70
percent of the LLM-written descriptions, concentrated in the low-resource Greek and Japanese
entities, and we measured that removing it improved Japanese by 1.95 MRR. We also noticed why the
lies are catchable: the Clint Eastwood entity had a fabricated description saying "Greek
footballer," but its graph edges say he directed films and won an Academy Award. The text and the
structure describe the same entity independently, and they disagree. That disagreement is a
signal you can compute without knowing an LLM wrote the text and without any external web access.

### 6.2 Direction A: Self-healing knowledge bases

Named problem: structural self-contamination of multilingual KBs by generated text.
Method: score each description against a serialisation of the entity's graph neighbourhood
(textual entailment or a local model as judge); low agreement flags likely contamination;
quarantine, re-source from a trustworthy channel, and measure the downstream repair.
Paper shape: a named problem, a training-free detector, a benchmark (our real found cases plus
controlled injections), and a demonstrated repair. We already hold the audit and the plus-1.95.
File: `docs/pivot/novel_directions_2026-07-05.md`.

### 6.3 Direction B: Completion-before-RAG for multilingual factuality

Named problem: asymmetric multilingual factual coverage (a fact exists in one language's graph
but is missing or sparse in another, so a user asking in the weaker language gets a worse answer).
Method: a system that detects language and entity intent, retrieves same-language then aligned
high-resource KG evidence, uses inductive MKGC to complete missing cross-lingual evidence, runs a
graph-consistency verifier, and grounds the LLM's answer in the user's language.
Paper shape: a new task/benchmark for low-resource factual QA under missing evidence, plus the
completion-before-generation system, evaluated against vanilla LLM, translate-to-English, and
plain KG-RAG. Reuses our MKGC model as the completion engine.
File: `docs/pivot/multilingual_factuality_novelty_research_2026-07-05.md`.

### 6.4 Competitor reality check (verified 2025 and 2026)

This is the honest part. Neither direction is virgin territory, and the senior must not be
promised "entirely novel" and then shown a near-scoop. In a field this active, what is achievable
is a defensible novel framing plus a gap plus evidence, not absolute first.

For Direction B (completion-before-RAG):
- mRAKL (Findings of ACL 2025) already reformulates low-resource multilingual KGC as
  retrieval-augmented QA, on low-resource languages (Tigrinya, Amharic), and shows RAG helps
  (+4.9 and +8.8 points). It is published. Direction B's remaining novelty over it is unseen or
  inductive entities plus actual LLM answer-grounding plus the verifier, which is a large system
  for an incremental margin over an existing paper.
- KG-TRICK (COLING 2025) already unifies textual and relational completion for multilingual KGs
  across 10 languages. It owns the "complete the descriptions too" territory Direction B leans on.
- Consequence: Direction B is more crowded and more incremental than its brief implies, and the
  senior's own critique ("you combined existing things") could recur.

For Direction A (self-healing):
- There is adjacent prior art in KG error detection that combines text and structure (for example
  "KG Error Detection with Contrastive Confidence Adaption," 2023, and medical-KG error
  detection). Honest recalibration: the raw primitive of text-structure consistency for KB
  quality is not new.
- The defensible distinction that remains: existing error detection finds wrong TRIPLES (bad
  edges) using text as a helper; ours finds wrong DESCRIPTIONS (bad text) using trusted structure
  as the judge, framed specifically as AI-generated contamination, concentrated in low-resource
  languages, with a repair loop and a measured downstream effect. mRAKL and KG error detection
  have nothing on AI-contamination of multilingual KBs or its downstream grounding impact.

### 6.5 The recommended fused direction

Take the novel, evidence-backed core of Direction A and the multilingual-factuality framing of
Direction B, and drop Direction B's heavy multi-stage system. The single defensible claim we can
actually support, which no competitor covers, is:

> Multilingual knowledge bases are being polluted by confident LLM-generated text, worst in
> low-resource languages, and this pollution measurably degrades downstream cross-lingual
> grounding. We characterise the phenomenon, detect it using the graph's own structure, and show
> that repairing it improves multilingual factual grounding.

Why this is the best of the three options:
- It leads with a phenomenon, not a system combination, so it survives the "you just combined
  things" critique.
- It is fundamentally multilingual: the pollution concentrates in low-resource languages, and the
  repair helps most there. This meets the senior's main ask.
- It connects to LLM factuality and grounding (Direction B's framing) through the
  repair-improves-grounding result, so it is not "just data cleaning."
- We have evidence in hand today: the 70 percent audit and the plus-1.95 repair. The competitors
  do not have this.
- It is executable on our single GPU with data we already own: a detector, a repair loop, and a
  grounding evaluation, not a semester-long pipeline.

Clean one-line differentiation to say out loud: mRAKL constructs the KG, we clean it; KG error
detection finds bad edges, we find AI-fabricated descriptions and measure cross-lingual grounding;
completion-before-RAG assumes the evidence is trustworthy, we show it often is not.

### 6.6 The method of the fused direction, step by step

1. Characterise the phenomenon: measure contamination rate by language and script on our KB and
   at least one controlled injection set, showing the low-resource concentration.
2. Detect: for each entity with structure, serialise its graph neighbourhood into a short factual
   statement and score the description's consistency with it (NLI-based and judge-based variants).
   Report precision and recall against labelled cases. Training-free.
3. Repair: quarantine flagged text, re-source from a trustworthy channel (native-language
   Wikipedia recovered 45 percent for us; the rest fall back to the plain name).
4. Measure downstream: show that the repaired KB improves cross-lingual grounding and completion,
   most for low-resource languages. We already have the first such number (plus 1.95 on Japanese).

### 6.7 Honest limits

It only works for entities that have graph structure to check against; a brand-new entity with a
description but no edges cannot be audited this way, and we quantify that coverage. It assumes the
structure is more trustworthy than the text, which is usually true in curated KGs but is an
assumption we state and test. A reviewer will want a second KB (a Wikidata slice) for generality,
which is a later experiment.

---

## 7. Novelty status, stated honestly (checked against 2025 and 2026 work)

The verdict on "entirely novel": in this field, in mid-2026, truly virgin territory is rare. Both
candidate directions have near neighbours (Section 6.4). The winning position is not "nobody has
ever touched this" but "here is a real problem, framed in a way these specific neighbours do not
cover, with evidence they do not have." Present it that way; do not over-claim.

What the literature actually supports for the fused direction:
- WETBench (2025) benchmarks detecting machine-generated text on Wikipedia including low-resource
  languages and finds stylometric detectors struggle. Our signal is factual agreement with the
  graph, which works even when writing style is undetectable, so this is an opening, not a rival.
- "Wikipedia in the Era of LLMs" (2025) warns that RAG degrades if the KB is polluted, then stops.
  Nobody builds the defence and measures the downstream repair.
- Fact-checking with KGs (GraphCheck and others) verifies external claims or LLM outputs against a
  KG; it points the checker outward. We point it inward, at the KB's own descriptions.
- The near neighbours to name and differentiate from: mRAKL, KG-TRICK, and the KG-error-detection
  line (Section 6.4).

Full ideation and sources are in `docs/pivot/novel_directions_2026-07-05.md`,
`docs/pivot/multilingual_factuality_novelty_research_2026-07-05.md`, and
`docs/pivot/trackB_pivot_brief.md`.

---

## 8. How the recommended plan aligns with what the senior wants

Map his three asks to the fused direction directly:

- "Make multilingual the main topic, not an add-on." Met. The phenomenon is multilingual by
  nature: contamination concentrates in low-resource languages and the repair helps most there.
- "Solve a real problem that people face." Met. Knowledge bases and the systems built on them are
  ingesting confident AI-generated falsehoods, with no working defence. Anyone building RAG or
  training on scraped multilingual KBs faces this now.
- "Something entirely novel." Answered honestly: we name a phenomenon and give it a training-free
  structural detection signal plus a repair loop, framed and evidenced in a way the near
  neighbours (mRAKL, KG-TRICK, KG error detection, MultiHal) do not cover. We differentiate from
  each explicitly rather than claiming absolute first.

The honest framing gift still applies: "You were right that the architecture was not the
contribution. We looked at what we actually discovered, checked it against the 2025 and 2026
literature including the close papers, and the discovery, cleaned of over-claiming, is the new
direction." Naming your own competitors is what makes a senior trust the pitch.

---

## 9. Nothing is wasted: how the old work becomes the foundation

Every asset of the original project feeds the new one:
- The multilingual knowledge graph (DBP-5L and our inductive split) is the KB we audit and clean.
- The graph-neighbourhood serialisation code is exactly the structural statement the detector
  compares against.
- The trained BGE-M3 retriever becomes the downstream system on which we measure repair, and can
  serve as the re-sourcing retriever.
- The per-language and Japanese analyses become the motivation: they show where contamination
  concentrates and hurts.
- The contamination we already found and hand-labelled, and the plus-1.95 repair we already
  measured, are the first data points of the new benchmark and the first evidence of the fix.

So the previous work stops being the headline and becomes the substrate. The original KGC paper
can still be finished for its own venue in parallel, or folded in as the completion task on which
repair is demonstrated.

---

## 10. The plan, the venue, and the timeline (current as of the meeting today, 2026-07-07)

The senior meeting moved from Monday to today. State of play to brief him on: the substrate work
is done, the pivot has its first real result, the literature is mapped, and there is a concrete
venue with a real but workable deadline. Below is what to present and the plan if he approves.

### What to present today (the fused direction, Section 6.5)
1. The phenomenon: KB pollution by LLM text, worst in low-resource languages, with the concrete
   examples (Clint Eastwood becomes a Greek footballer, Taipei becomes a Cypriot dessert).
2. Two numbers already in hand:
   - The problem: roughly 70 percent of the LLM back-filled descriptions are fabricated (audited).
   - The detector: text-versus-structure consistency reaches ROC-AUC 0.995 and F1 0.988 on a
     controlled benchmark, and flags 57 percent of the real fabrications even though those entities
     have almost no structure to check against (script and result:
     `pivot/self_healing_detector_result_2026-07-07.md`).
   - The repair: removing contamination improved Japanese completion by 1.95 MRR.
   So the full loop is already evidenced: problem, detection, repair.
3. The literature check: the canonical map is `pivot/related_work.md`. Two independent sweeps
   agree that no SIGIR, KDD, or WSDM 2024 to 2026 paper does KB self-audit of AI-contaminated
   descriptions via graph-text disagreement with a repair loop. The strongest motivation paper,
   Retrieval Collapses When AI Pollutes the Web (WWW 2026), proves at a top venue that AI pollution
   degrades retrieval, then stops short of detection, repair, KGs, or multilinguality.
4. Name the competitors and differentiate in one line each: mRAKL (constructs KGs, we clean them),
   KG-TRICK (completes multilingual KG text, does not audit contamination), KG error detection
   (finds bad edges, we find fabricated descriptions), MultiHal (oracle paths, high resource, no
   retriever). Naming them yourself is what earns trust.

### The venue: WSDM 2027 (confirmed target)
The senior flagged an end-of-August deadline for a 2027 venue. Verified: that is WSDM 2027,
abstract Aug 17, full paper Aug 24, 2026, conference Feb 2027 in Hong Kong. WSDM is A-star and fits
(web mining and content analysis, retrieval, KGs, web data quality), and it has a Findings track as
a safety net. That is about six to seven weeks out, a real crunch but far more workable than AAAI's
was. Fallbacks if it slips: WSDM Findings, or KDD 2027 Cycle 2 (historically around February 2027;
KDD has a Datasets and Benchmarks track and the Shomer 2025 paper shows appetite for inductive-KGC
benchmarks) and SIGIR 2027 (late-January style deadline, not yet posted). ISWC and WWW are also
natural homes.

### Why the fused paper is the right scope for six to seven weeks
Lead with the self-healing contamination story (the novelty the senior wants), and use the already
complete substrate (benchmark, model, three seeds, significance, mBERT baseline, all analyses) as
the empirical backbone and downstream task. Roughly 80 percent of the experiments already exist, so
the genuinely new work is finishing the detector section and writing. This satisfies the novelty
critique and is actually deliverable in the window.

### If he approves: the six-to-seven-week shape
- Weeks 1 to 2: finish the detector section. Add a realistic-fabrication injection set (generate
  believable wrong bios rather than wrong-entity swaps, so the positives match the real failure
  mode), report precision and recall by language and script, and add an LLM-judge variant beside
  the embedding one.
- Weeks 2 to 3: the downstream grounding experiment (LLM factual QA with and without the cleaned
  KB) to connect detection to impact.
- Weeks 3 to 5: writing, using this doc and ARCHITECTURE.md as the skeleton and RESULTS_AND_INFERENCE
  for numbers.
- Week 6: WSDM and ACM template, reproducibility, and a buffer. Freeze the abstract before Aug 17.
Honest caveat to state: six to seven weeks solo is tight, and the self-healing section must be
solid rather than a single number. The Findings track and the February KDD cycle are the safety
nets.

**Practical note on compute.** Nothing new is training. The clean 3-seed retrain of the substrate
model can finish whenever; its numbers become the retriever and baseline evidence in whichever
story we tell.

---

## 11. Glossary and quick answers to likely questions

**Glossary.**
- Triple: (head, relation, tail), the atomic fact.
- Embedding: a vector representing an entity or text.
- Bi-encoder: two text encoders (here, one shared) that map query and candidate into the same
  vector space so similarity can be computed.
- LoRA: low-rank adapters, a cheap way to fine-tune a big frozen model.
- Inductive: handling entities unseen during training.
- MRR, Hits@k: ranking quality metrics.
- Stylometry: detecting machine text by writing style; the failing baseline for our problem.
- NLI (natural language inference): deciding whether one statement entails, contradicts, or is
  neutral to another; our consistency-scoring tool.

**Likely questions and crisp answers.**
- "Why can the graph be trusted over the text?" In curated KGs the structural edges are added and
  reviewed more carefully than free-text descriptions, and edges come from many independent
  contributors. We state this as an assumption and can test robustness to noisy structure.
- "What if the entity has no edges?" We cannot audit it structurally; we report that coverage
  limit and treat those separately.
- "Is this just fact-checking?" No. Fact-checking verifies external claims or LLM outputs against
  a KG. We audit the KB's own descriptions against the KB's own structure; the checker points
  inward.
- "Isn't this just KG error detection?" Existing error detection finds wrong triples (bad edges),
  using text as a helper. We find wrong descriptions (bad text) using trusted structure as the
  judge, framed as AI-generated contamination, focused on low-resource languages, with a repair
  loop and a measured downstream effect. Different target, different framing, evidence they lack.
- "Isn't mRAKL already multilingual KGC with retrieval?" Yes, and we cite it. mRAKL constructs or
  completes the KG. We clean an already-contaminated KG and measure the effect on grounding. It
  assumes its evidence is trustworthy; our whole point is that increasingly it is not.
- "Is any of this entirely novel?" Honest answer: the raw primitive of text-structure consistency
  is not new, and the multilingual factuality space is active. What is new is the framing
  (AI-contamination of multilingual KBs), the inward-pointing self-audit with repair, and the
  evidence in hand. We claim a defensible gap, not absolute first.
- "How is this multilingual and not just English?" The contamination is created and concentrated
  in low-resource, often non-Latin-script languages, precisely because the generator fails there;
  the repair helps most there. The problem is multilingual by nature.
- "What have you actually shown already?" Real contamination found and labelled in our own KB
  (about 70 percent of the LLM-written descriptions), and a measured downstream repair of plus
  1.95 MRR on Japanese from removing it.

---

## 12. Resources and papers

These are the papers we actually used or surfaced during the project and the literature checks.
Grouped by role. Links are arXiv or publisher pages. IDs of the form 25xx or 26xx are 2025 and
2026 preprints respectively.

### 12.1 The original project: methods, encoders, and the dataset
- DBP-5L benchmark and KEnS (multilingual KG completion via ensemble), Chen et al., 2020:
  https://arxiv.org/abs/2010.03158
- SS-AGA, multilingual KGC with self-supervised adaptive graph alignment (transductive SOTA we
  calibrate against), Huang et al., 2022: https://arxiv.org/abs/2203.14987
- AlignKGC, joint multilingual KGC with entity and relation alignment, Singh et al., 2021:
  https://arxiv.org/abs/2104.08804
- JMAC, multilingual KGC with joint text and structure (adds surface information), 2022:
  https://arxiv.org/abs/2210.08922
- KL-GMoE, multilingual KGC via efficient knowledge sharing (Findings of EMNLP 2025):
  https://arxiv.org/abs/2510.07736
- SimKGC, simple contrastive KGC with pretrained language models (our bi-encoder ancestor), Wang
  et al., ACL 2022: https://arxiv.org/abs/2203.02167
- BLP, inductive entity representations from text (entity-disjoint split methodology), Daza et
  al., WWW 2021: https://arxiv.org/abs/2010.03496
- StATIK, structure and text for inductive KGC, NAACL 2022 Findings:
  https://aclanthology.org/2022.findings-naacl.46/
- RAA-KGC, relation-aware anchor enhancement for KGC (the anchor idea), 2025:
  https://github.com/DayanaYuan/RAA-KGC
- KGCRR / CRR loss, metric-driven KGC with an upper bound on reciprocal rank (our loss):
  see the AAAI 2025 KGCRR paper (in our `Research` folder as 07528-XuK)
- BGE-M3, multilingual multi-granularity text embeddings (our encoder):
  https://arxiv.org/abs/2402.03216

### 12.2 The multilingual factual gap in LLMs (measurement)
- X-FACTR, multilingual factual knowledge retrieval from LMs, Jiang et al., EMNLP 2020:
  https://aclanthology.org/2020.emnlp-main.479/
- mLAMA, multilingual factual probing, Kassner et al., 2021: https://arxiv.org/abs/2102.00894
- Cross-Lingual Consistency of Factual Knowledge (BMLAMA, RankC), Qi et al., EMNLP 2023:
  https://arxiv.org/abs/2310.10378
- Better To Ask in English? factual accuracy on low-resource Indic languages, 2025:
  https://arxiv.org/abs/2504.20022
- Consistency-Driven Reinforcement Learning for cross-lingual factual recall, 2026:
  https://arxiv.org/abs/2606.06586
- CCFQA, cross-lingual and cross-modal factuality benchmark, 2025:
  https://arxiv.org/abs/2508.07295
- Cross-Lingual Exploration for Parametric Knowledge, 2026:
  https://arxiv.org/abs/2606.24579
- On the Entity-Level Alignment in Crosslingual Consistency, 2025:
  https://arxiv.org/abs/2510.10280

### 12.3 Multilingual and KG-grounded RAG (the closest "fixing" line)
- MultiHal, multilingual KG-grounded evaluation of LLM hallucinations (nearest neighbour to a
  KG-RAG pivot), 2025: https://arxiv.org/abs/2505.14101
- Multilingual RAG for knowledge-intensive tasks, 2025: https://arxiv.org/abs/2504.03616
- Investigating Language Preference of Multilingual RAG Systems, 2025:
  https://arxiv.org/abs/2502.11175
- ALIGNed-LLM, infusing KG embeddings for factual accuracy, 2025:
  https://arxiv.org/abs/2507.13411
- MLPQ, path question answering over multilingual KGs:
  https://www.sciencedirect.com/science/article/abs/pii/S221457962300014X

### 12.4 Cross-lingual knowledge editing (adjacent parameter-level lane)
- Editing Across Languages, a survey of multilingual knowledge editing, 2025:
  https://arxiv.org/abs/2505.14393
- Edit Once, Update Everywhere, cross-lingual knowledge synchronisation, 2025:
  https://arxiv.org/abs/2502.14645
- CLM-Bench, benchmarking cross-lingual misalignment in knowledge editing, 2026:
  https://arxiv.org/abs/2601.17397

### 12.5 Script barrier and romanization (why non-Latin scripts fail)
- RomanLens, the role of latent romanization in LLM multilinguality, 2025:
  https://arxiv.org/abs/2502.07424
- Large Reasoning Models Struggle to Transfer Knowledge Across Scripts, 2026:
  https://arxiv.org/abs/2603.17070
- Script Gap, native versus Roman script triage on Indian languages, 2025:
  https://arxiv.org/abs/2512.10780
- Prompting with Phonemes, enhancing multilinguality for non-Latin scripts, 2024:
  https://arxiv.org/abs/2411.02398
- Scripts Through Time, a survey of transliteration in NLP, 2026:
  https://arxiv.org/abs/2604.18722

### 12.6 The new direction: KB contamination, detection, and Wikipedia quality
- WETBench, detecting task-specific machine-generated text on Wikipedia (stylometry struggles),
  2025: https://arxiv.org/abs/2507.03373
- Wikipedia in the Era of LLMs: Evolution and Risks (RAG degrades if the KB is polluted), 2025:
  https://arxiv.org/abs/2503.02879
- How Good is Your Wikipedia? auditing data quality for low-resource and multilingual NLP, 2024:
  https://arxiv.org/abs/2411.05527
- Continuous Monitoring of Generative AI via Deterministic Knowledge Graph Structures, 2025:
  https://arxiv.org/abs/2509.03857
- HalluMat, detecting hallucinations in LLM-generated content via multi-stage verification, 2025:
  https://arxiv.org/abs/2512.22396

### 12.7 Fact-checking with knowledge graphs (related but points outward, not inward)
- GraphCheck, multipath fact-checking with entity-relationship graphs, 2025:
  https://arxiv.org/abs/2502.20785
- FactKG, fact verification via reasoning on knowledge graphs, 2023:
  https://arxiv.org/abs/2305.06590
- Hybrid fact-checking integrating KGs and LLMs, 2025: https://arxiv.org/abs/2511.03217

### 12.8b The nearest competitors to name and differentiate from (verified directly)
- mRAKL, multilingual retrieval-augmented KG construction for low-resource languages, Findings of
  ACL 2025 (nearest competitor to the completion-before-RAG direction; constructs the KG, does not
  clean it): https://arxiv.org/abs/2507.16011
- KG-TRICK, unifying textual and relational completion for multilingual KGs, COLING 2025 (owns
  multilingual KG text+relation completion; no LLM grounding, no contamination):
  https://arxiv.org/abs/2501.03560
- KG Error Detection with Contrastive Confidence Adaption, 2023 (the KG-error-detection line;
  finds wrong triples using text+structure, not contaminated descriptions):
  https://arxiv.org/abs/2312.12108
- The alternative multilingual-factuality pivot brief (Direction B), in this repository:
  `docs/pivot/multilingual_factuality_novelty_research_2026-07-05.md`

### 12.8 Our own internal documents (in this repository)
- `docs/pivot/novel_directions_2026-07-05.md`: the four candidate directions and the novelty
  verification behind Idea 1.
- `docs/pivot/trackB_pivot_brief.md`: the multilingual KG-RAG alternative and its literature.
- `docs/design/research_assessment_2026-07-03.md`: the honest publishability assessment of the
  original project.
- `docs/RESULTS_AND_INFERENCE.md`: every experimental result and inference, including the
  contamination audit and the plus-1.95 repair.
- `docs/IMPLEMENTATION_PLAN.md`: the current execution plan and AAAI-27 facts.

Note on precise citations: a few arXiv identifiers here were captured from mid-2026 search
results; before anything goes into a paper, verify each identifier, author list, and venue on the
arXiv or ACL Anthology page, since search-surfaced IDs occasionally point to a different version
or a renamed paper.
