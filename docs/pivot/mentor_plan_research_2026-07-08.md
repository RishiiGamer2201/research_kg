# Mentor Plan and Deep Research (2026-07-08)

This note records what changed after the mentor meeting: the new bottom-up ladder, what the three
selected papers actually give us, how the mentor's suggested topics fit, and the practical next
step. The short version is:

> Reproduce S2DN first, beat it on English inductive KGC with a stronger denoising architecture,
> then extend to multilingual, then add text self-healing.

That is strategically safer than starting with the full multilingual self-healing story. It gives
us a published AAAI 2025 anchor, a concrete score to beat, and a path where every later step is
motivated by the previous one.

---

## 1. Mentor's Ladder

1. Reproduce S2DN from `03121-MaT.pdf`, the AAAI 2025 paper.
2. Modify S2DN and beat its English inductive KGC scores.
3. Move the improved model to multilingual KGC.
4. Once multilingual scores are solid, add self-healing and contaminated-text repair.

This is not a rejection of the self-healing idea. It reorders the work. S2DN denoises noisy graph
structure and relation semantics; our self-healing idea denoises contaminated entity text. The
final story can become:

> Robust multilingual inductive KGC under both structural contamination and textual contamination.

That is much stronger than "we added multilinguality to inductive KGC."

Deadline reality: finishing the full ladder by around 18 July is not realistic. A narrow result
such as "reproduce S2DN and implement one principled improvement" might be possible if setup is
kind. The full multilingual plus self-healing version is a SIGIR or later-cycle target.

---

## 2. Paper 1: S2DN, AAAI 2025

Local file: `C:\Users\admin\Downloads\03121-MaT.pdf`

Sources:
- Paper page: https://arxiv.org/abs/2412.15822
- Official code: https://github.com/xiaomingaaa/SDN
- GraIL data and base code: https://github.com/kkteru/grail

Full title: **S2DN: Learning to Denoise Unconvincing Knowledge for Inductive Knowledge Graph
Completion**.

### What Problem It Solves

Inductive KGC means the model must predict links for entities not seen during training. S2DN says
existing subgraph reasoning models, especially GraIL-style methods, miss two noise sources:

1. **Semantic inconsistency:** relations that mean similar things are treated too separately.
   Example in the paper: `located_in` and `lie_in` can express similar semantics.
2. **Noisy interactions:** local enclosing subgraphs contain irrelevant or unreliable links that
   hurt reasoning.

This is close to our mentor's question about "poisoned" or contaminated knowledge, but S2DN is
mostly about noisy triples and relations, not fabricated multilingual descriptions.

### Architecture

S2DN extracts the enclosing subgraph around a candidate triple `(u, r, v)`, following GraIL. Then
it runs two branches:

1. **Semantic Smoothing module**
   - Learns to blur or merge similar relations.
   - Uses Gumbel Softmax so relation smoothing is trainable while still acting like a discrete
     relation-selection operation.
   - Runs an RGNN over the smoothed relation graph and produces `h_sem`.

2. **Structure Refining module**
   - Scores possible node-pair edges by reliability.
   - Treats edges as Bernoulli random variables with learned probabilities.
   - Removes edges below a reliability threshold and keeps/refines helpful interactions.
   - Runs a GNN over the refined subgraph and produces `h_str`.

Finally it concatenates `h_sem` and `h_str`, passes them through an MLP, and scores whether the
target link is true.

Plain-language version:

> One branch asks "which relations are semantically close enough to share signal?" The other asks
> "which local edges should I trust?" The final prediction uses both.

### Exact Headline Results From The Paper

The paper reports filtered Hits@1, Hits@10, and MRR in percentage. For the first reproduction, we
should target WN18RR and FB15k-237 first because those tables are explicit in the main paper pages.

**WN18RR, average Hits@10**

| Model | Avg Hits@10 |
|---|---:|
| DRUM | 64.15 |
| NeuralLP | 64.15 |
| A*Net | 72.06 |
| CoMPILE | 74.43 |
| TAGT | 73.28 |
| SNRI | 79.19 |
| RMPI | 73.34 |
| S2DN | **81.23** |
| S2DN without Semantic Smoothing | 78.49 |
| S2DN without Structure Refining | 76.31 |

Key WN18RR per-version S2DN MRR:

| Split | Hits@1 | Hits@10 | MRR |
|---|---:|---:|---:|
| V1 | 74.73 | 87.64 | 79.89 |
| V2 | 78.23 | 85.60 | 81.16 |
| V3 | 52.89 | 69.52 | 58.10 |
| V4 | 75.33 | 82.15 | 78.04 |

**FB15k-237, average Hits@10**

| Model | Avg Hits@10 |
|---|---:|
| DRUM | 55.11 |
| NeuralLP | 55.16 |
| A*Net | 76.57 |
| CoMPILE | 78.95 |
| TAGT | 77.61 |
| SNRI | 79.87 |
| RMPI | 78.00 |
| S2DN | **81.25** |
| S2DN without Semantic Smoothing | 79.68 |
| S2DN without Structure Refining | 78.97 |

Key FB15k-237 per-version S2DN MRR:

| Split | Hits@1 | Hits@10 | MRR |
|---|---:|---:|---:|
| V1 | 43.68 | 67.34 | 52.10 |
| V2 | 55.45 | 82.38 | 64.80 |
| V3 | 56.31 | 83.97 | 65.07 |
| V4 | 60.96 | 91.31 | 68.44 |

### Noise Robustness Results

S2DN tests both semantic noise and structural noise. It injects noise at 15 percent, 35 percent,
and 50 percent, then reports Hits@10 degradation.

For WN18RR-V1, clean S2DN Hits@10 is 87.64. Under 50 percent noise:

- semantic noise: S2DN drops to 83.12
- structural noise: S2DN drops to 84.98

For FB15k-237-V1, clean S2DN Hits@10 is 67.34. Under 50 percent noise:

- semantic noise: S2DN drops to 64.97
- structural noise: S2DN drops to 64.89

This is important for our story because S2DN already claims robustness to contaminated KGs. To beat
it, our modification should be a stronger denoising idea, not just a bigger encoder bolted on.

### Reproduction Status

What I verified locally:

- S2DN official repo is cloned at `external/SDN`.
- Its README says to run:
  - `python train.py -d WN18RR_v1 -e sdn_wn_v1`
  - `python test_ranking.py -d WN18RR_v1_ind -e sdn_wn_v1`
- The S2DN repo itself does **not** include the expected `data/` folder.
- The original GraIL repo is cloned at `external/grail`, and it **does** contain the required
  `WN18RR_v1..v4`, `fb237_v1..v4`, and `nell_v1..v4` folders plus the inductive test folders.
- S2DN README and `requirements.txt` disagree:
  - README lists `torch==2.0.0`, `dgl==1.1.2`, `networkx==3.0`, `lmdb==1.4.1`.
  - `requirements.txt` lists older GraIL-style versions: `torch==1.4.0`, `dgl==0.4.2`,
    `networkx==2.4`, `lmdb==0.98`.

Main risk: dependency compatibility, especially DGL and CUDA on the current GPU/WSL setup. Data is
now findable; runtime is the real first blocker.

---

## 3. Paper 2: GOLD, EMNLP Findings 2023

Local file: `C:\Users\admin\Downloads\2023.findings-emnlp.232.pdf`

Sources:
- ACL Anthology: https://aclanthology.org/2023.findings-emnlp.232/
- Code: https://github.com/HKUST-KnowComp/GOLD

Full title: **GOLD: A Global and Local-aware Denoising Framework for Commonsense Knowledge Graph
Noise Detection**.

What it contributes:

- Detects noisy triples in commonsense KGs.
- Combines three signals:
  1. entity semantic information
  2. global logical rules
  3. local graph structure
- Evaluates with AUC and top-k precision.

Why it matters:

GOLD is the cleanest match for your mentor's "heuristic ontology alignment and rule mining
prediction inference" direction. It proves that rule-level global evidence plus local structure is
a valid KG denoising architecture, not just an idea we invented in discussion.

How to use it in our work:

- Use mined rules as priors in S2DN's Structure Refining module.
- Use rule confidence as an additional reliability score for edges.
- Use contradictions or low-rule-support triples as candidates for removal/quarantine.

Plain-language version:

> GOLD says "do not judge a triple only by its embedding; judge it by whether the graph's rules and
> nearby structure support it."

That is exactly the principle we can inject into S2DN.

---

## 4. Paper 3: LLM_sim, GenAIK 2025

Local file: `C:\Users\admin\Downloads\2025.genaik-1.9.pdf`

Source:
- ACL Anthology: https://aclanthology.org/2025.genaik-1.9/

Full title: **Refining Noisy Knowledge Graph with Large Language Models**.

What it contributes:

- Uses Llama 3 to detect noisy triples.
- Prompts the LLM to generate corrected candidate triples.
- Keeps generation constrained by preserving the original relation and one entity.
- Selects the best repair using sentence-transformer cosine similarity against reference triples.

Why it matters:

This paper directly answers your mentor's second question:

> If we clean poisoned knowledge after finding it, how are we repairing it and using what?

LLM_sim repairs with constrained LLM generation plus similarity filtering. Our current repair is
different: we quarantine bad text and re-source it from native Wikipedia or fall back to the entity
name. For future self-healing, we can compare:

1. re-source from trusted evidence
2. LLM repair with constraints
3. LLM repair plus KG-consistency filtering

My view: use LLM_sim later, not for the first S2DN reproduction. It is useful for the self-healing
stage, but it is not the fastest path to beating S2DN on English inductive KGC.

---

## 5. The Mentor's Two Questions, Answered Cleanly

### Q1. If we find poisoned text, how and using what do we find it?

Current answer from our project:

- Encode the entity description with BGE-M3.
- Encode the entity's graph neighbourhood as text with BGE-M3.
- If description and graph-neighbourhood embeddings disagree, flag the description.
- This is training-free and got ROC-AUC 0.995 on the controlled contamination benchmark in
  `docs/pivot/self_healing_detector_result_2026-07-07.md`.

Stronger future answer:

- For graph/triple noise: use S2DN-style structure refining.
- For rule-level noise: use GOLD-style global rule and local structure scoring.
- For text contamination: use graph-text consistency, optionally with an LLM judge as a second
  opinion.

### Q2. If we clean it after finding it, how and using what do we repair it?

Current answer from our project:

- Quarantine suspicious descriptions.
- Re-source from native-language Wikipedia when available.
- If no trusted source is available, fall back to the plain entity name rather than hallucinated
  generated text.
- This already improved Japanese completion by 1.95 MRR.

Stronger future answer:

- For bad triples: infer corrected facts using mined rules and KGC.
- For bad descriptions: re-source from trusted text first; if unavailable, use constrained LLM
  repair and accept it only if graph-text consistency improves.
- For multilingual repair: use ontology/entity alignment and fuzzy search to locate the same
  entity in a stronger language graph or source.

---

## 6. How The Mentor's Suggested Topics Fit

### Fuzzy Search

Relevance: medium.

Use it for:

- matching noisy entity names to canonical entity IDs
- alias matching during repair
- finding candidate Wikipedia/Wikidata pages
- cross-lingual entity lookup when spelling or script differs

It is a tool, not the paper's novelty. For scalable implementation, a fuzzy search engine, n-gram
index, BK-tree, or vector index is usually more directly useful than a plain B+ tree.

### Heuristic Ontology Alignment

Relevance: medium now, high later for multilingual.

Use it for:

- aligning relations/classes across datasets or languages
- grouping semantically similar relations before smoothing
- creating schema-level priors for S2DN's Semantic Smoothing module

This can make Semantic Smoothing less black-box: instead of learning all relation blur weights
from scratch, we can initialize or regularize them using ontology/schema similarity.

### Rule Mining, Prediction, and Inference

Relevance: very high.

Use it for:

- mining rules such as `(x, born_in, y) -> (x, nationality, y_country)` where applicable
- scoring whether a triple has symbolic support
- detecting contradictions or unsupported edges
- giving S2DN's Structure Refining module a rule-confidence prior

This is probably the best first modification to beat S2DN: keep S2DN's two branches, but make the
structure branch neuro-symbolic by adding rule support as a reliability signal.

Useful source:
- AnyBURL: https://arxiv.org/abs/2004.04412

### Neurosymbolic AI

Relevance: very high.

This is the best umbrella for the modified architecture:

> Neural subgraph reasoning plus symbolic rule priors plus semantic/textual consistency.

S2DN is already neural denoising. GOLD shows rules help denoising. Our detector shows text-graph
agreement helps catch contamination. Combining these gives a real architecture story:

> Trust-S2DN: a semantic, structural, and symbolic denoising network for inductive KGC.

That is more publishable than "we changed the dataset."

### Gephi

Relevance: low as a method, useful for analysis.

Use it to:

- visualize enclosing subgraphs
- compare original GraIL subgraphs vs S2DN refined subgraphs
- show contamination clusters
- produce an intuitive paper/presentation figure

It will not beat scores, but it can help us understand why the model is making decisions.

### B+ Trees From Abdul Bari

Relevance: low for model novelty, useful foundation.

B+ trees are an indexing structure. They help with ordered lookup/range queries in databases. For
our work, the conceptual link is efficient retrieval:

- fast lookup of entity IDs
- indexing aliases
- scalable candidate retrieval
- possibly storing adjacency lists or relation indexes

But B+ trees are not the main research contribution here. If the mentor asked this, he may want
stronger CS fundamentals for explaining indexing and retrieval at scale.

---

## 7. Best Modification Idea To Beat S2DN

My strongest recommendation:

> Build a neuro-symbolic S2DN variant where Structure Refining is guided by rule confidence, and
> Semantic Smoothing is guided by relation/schema/text similarity.

Working name: **Trust-S2DN** or **RuleTrust-S2DN**.

Architecture:

1. Start with S2DN's enclosing subgraph.
2. Mine rules from the training graph using AnyBURL, AMIE-style rules, or a lightweight local rule
   miner.
3. For each edge in the enclosing subgraph, compute:
   - neural reliability from S2DN
   - rule support confidence
   - relation semantic similarity to the query relation
4. Combine these into the edge reliability probability used by Structure Refining.
5. Regularize Semantic Smoothing so semantically/ontologically similar relations are easier to
   smooth together, while unrelated relations stay apart.
6. Train and evaluate exactly like S2DN first.

Why this is promising:

- It directly uses the mentor's topics.
- It modifies the architecture he liked rather than abandoning it.
- It gives a clear reason scores might improve: S2DN learns trust only from neural local signals;
  we add symbolic global evidence.
- It creates a bridge to self-healing: later, text consistency becomes another trust signal.

What not to do first:

- Do not immediately add multilingual data.
- Do not immediately add LLM repair.
- Do not beat S2DN with a completely different giant text model unless the mentor says "any method
  is fine." His wording sounds like he wants the S2DN architecture modified.

---

## 8. Practical Next Step

Immediate reproduction plan:

1. Copy or symlink `external/grail/data` into `external/SDN/data`.
2. Create a clean environment in WSL.
3. Try the newer README dependency set first:
   - PyTorch 2.0.0
   - DGL 1.1.2
   - NetworkX 3.0
   - LMDB 1.4.1
4. If it fails because the code is actually GraIL-old, fall back to the older `requirements.txt`
   set or patch the code forward.
5. Run WN18RR_v1 first:
   - `python train.py -d WN18RR_v1 -e sdn_wn_v1`
   - `python test_ranking.py -d WN18RR_v1_ind -e sdn_wn_v1`
6. Compare against the paper target:
   - WN18RR-V1 S2DN: Hits@1 74.73, Hits@10 87.64, MRR 79.89.
7. Only after v1 works, run v2/v3/v4 and average.

Success criterion for reproduction:

> We can run the official code end to end and land close to the paper's WN18RR-V1 ranking numbers.

If we cannot reproduce exactly, we document the reason: dependency drift, missing random seeds,
different negative sampling, or code/data mismatch.

---

## 9. Decisions To Ask The Mentor

1. When he says "beat S2DN," does he want a modification inside the S2DN architecture, or is any
   model allowed?
2. Is WN18RR enough for the first reproduction checkpoint, or does he expect WN18RR, FB15k-237,
   and NELL all reproduced?
3. Does he agree that the first modification should be neuro-symbolic rule-guided denoising?
4. For the late-August venue, does he mean WSDM rather than SIGIR? SIGIR-style deadlines are
   usually not late August, so this needs confirmation before we plan the paper calendar.

---

## 10. My Recommendation

Do exactly what the mentor asked, but frame it as a staged research program:

1. **Week 1:** reproduce S2DN on WN18RR_v1, then all WN18RR splits.
2. **Week 2:** add one rule-guided trust signal to Structure Refining and try to beat WN18RR.
3. **Week 3:** extend to FB15k-237 and NELL if runtime allows.
4. **After that:** multilingual extension.
5. **Final layer:** self-healing contaminated descriptions using graph-text consistency and
   constrained repair.

The key strategic sentence:

> We are not abandoning multilingual self-healing. We are building the stronger English inductive
> denoising backbone first, because without beating a strong AAAI 2025 denoising baseline, the
> multilingual/self-healing layer will look like a dataset change rather than a model contribution.

