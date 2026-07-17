# S2DN Architecture: Limitations and Weaknesses

Written 2026-07-17 for the mentor task ("read all the limitations of architecture and what the
weaknesses are, work on that") ahead of the lab's new 96 GB VRAM GPU. Grounded in the S2DN paper
(AAAI 2025, 03121-MaT / arXiv 2412.15822), the current SOTA survey
([sota_benchmark_survey_2026-07-17.md](sota_benchmark_survey_2026-07-17.md)), and our own measured
diagnostics from the RuleTrust work and the DBP-5L contamination census.

Style note: no emojis, no shorthand dashes. Every weakness is tagged [paper] (from S2DN's own text or
tables), [measured] (from our runs), or [survey] (from newer methods).

---

## 0. One-paragraph summary

S2DN's core mechanism is an enclosing subgraph between the two endpoint entities, refined two ways
(relation smoothing and edge reliability) and scored as a binary classification. Every important
weakness follows from that one design choice. It cannot reason when an emerging entity has no
neighbourhood (the enclosing subgraph is empty), it is text-blind (node features are structural, not
descriptions), it is only semi-inductive (unseen entities but shared relations), its structure module
is dense and memory-heavy (the reason FB15k-237 v2 OOMs at batch 32), and both of its modules add
only modest, dataset-dependent gains over the subgraph-GNN baseline. Its headline strength,
noise-robustness, is measured only against synthetic noise, which is exactly the opening for our
self-healing direction. It is also no longer the inductive state of the art. The good news: almost
every weakness is a direct opportunity for this project.

---

## 1. Architecture recap (so this note stands alone)

Given a target triple (u, r, v) with u or v an emerging entity:

1. Enclosing subgraph. Take k-hop neighbours of u and v, keep the nodal intersection
   V = N_k(u) intersect N_k(v), and the triples among V. This is GraIL's construction, unchanged.
2. Semantic Smoothing (SS). Blur semantically similar relations into a shared representation with a
   Gumbel-Softmax over relations (w = softmax(E W^T + b), smoothed R-tilde, E-tilde = R-tilde E),
   run an RGNN, pool to h_sem. A KL trade-off term guards against over-smoothing.
3. Structure Refining (SR). Treat every node pair in V as an independent Bernoulli edge with
   reliability pi_ij = sigmoid(Z(i) Z(j)^T), Z = MLP(node features); concrete-relaxation
   reparameterization; drop edges with pi < 0.5; run an L-layer GCN, pool to h_str.
4. Score. p(u,r,v) = sigmoid(MLP([h_sem concat h_str])). Trained as binary classification with
   sampled negatives, cross-entropy plus the KL term plus L2.

Node features are GraIL's double-radius vertex labelling (distance to u and v). No entity text is
used anywhere.

---

## 2. Architectural and conceptual weaknesses (the core of the mentor task)

### W1. The enclosing subgraph is empty for isolated emerging entities [paper][measured]
V = N_k(u) intersect N_k(v). If the emerging entity has zero or very few edges, there is no
intersection and no subgraph to reason over. S2DN then has essentially no signal. This is not a corner
case in low-resource multilingual data: on our DBP-5L contamination census, 69.6 percent of the
contaminated entities (1,641 of 2,359) have zero edges, and all of them lack cross-lingual alignment
links too. S2DN structurally cannot help exactly the entities that matter most for the multilingual
and self-healing story. This is the single most important architectural limit and it is the same soft
spot as our own detector.

### W2. Text-blindness [paper]
Node features are purely structural (double-radius labelling). S2DN cannot read an entity's name or
description, so it cannot use the one signal that survives when structure is absent, and it cannot do
anything with multilingual text. For a KG where the emerging entity comes with a description but few
edges (the common low-resource case), S2DN throws that description away. This is why the BGE-M3 text
substrate and the self-healing text layer are complementary rather than competing: they operate on the
channel S2DN ignores.

### W3. Only semi-inductive: unseen entities, but shared relations [survey]
S2DN inherits GraIL's assumption that the relation vocabulary is identical between training and test.
It generalizes to new entities, not to new relations or new KGs. Fully-inductive and foundation
methods (RMPI, InGram, and above all ULTRA, ICLR 2024) lift this restriction and transfer zero-shot
across arbitrary graphs and relation vocabularies. For DBP-5L this is survivable because relation IDs
are shared across languages, but it caps the method's generality and it is the axis on which ULTRA
simply supersedes the whole GraIL/S2DN family.

### W4. Structure Refining is dense and memory-heavy [paper][measured]
SR models all node pairs as Bernoulli variables, producing a "weighted fully connected graph" that the
paper itself calls "computationally intensive," then prunes edges below 0.5. The dense O(|V|^2) object
is the memory bottleneck. Measured on our side: FB15k-237 subgraphs carry on the order of 3.3e5 node
pairs each (about 1.3e7 across a batch), and this is precisely why FB15k-237 v2 with dim 64, hop 3,
batch 32 OOMs on a 16 GB GPU while v1 fits. The architecture's structure branch does not scale
gracefully with subgraph size.

### W5. Structure Refining is largely redundant with the GNN attention [measured]
We instrumented the refined adjacency directly. Rule-supported pairs are about 0.02 percent of node
pairs, and injecting a prior into the SR probabilities changed the end-to-end output by about 1e-4
against a nondeterminism floor of 1e-6, i.e. essentially inert. A typed graph path that SR would
up-weight is already scored highly by the ReLU dot-product attention in the RGNN, so SR is re-deriving
signal the semantic branch already has. This matches S2DN's own ablation: removing SR costs only about
2 to 3 Hits@10 points (WN18RR 81.23 to 76.31; FB15k-237 81.25 to 78.97). The module is real but
marginal, and it was the direct reason we moved our rule evidence to the score rather than into SR.

### W6. Semantic Smoothing assumes relation redundancy that is not always present [paper][measured]
SS helps only when the relation set contains semantically mergeable relations (their example:
located_in and lie_in). On relation-poor graphs there is little to smooth: WN18RR has 11 relations and
is rule-barren (we mined only 5 length-2 rules, none above 0.5 confidence). The transition matrix in
their Figure 4 shows smoothing concentrating on a handful of relation pairs. Over-smoothing is a real
risk (it can collapse genuinely distinct relations), which is why they need the KL trade-off term as a
guard, and the Gumbel-Softmax temperature is an unanalyzed sensitive hyperparameter. SS is a
dataset-dependent gain, not a universal one, and its benefit is small where relations are already
distinct.

### W7. Both modules give modest, dataset-dependent gains [paper]
From S2DN's own Tables 1 and 2, neither module dominates and the two matter differently per dataset:
on WN18RR, SS matters more (w/o SS 78.49 vs w/o SR 76.31 average Hits@10); the full model's edge over
the stronger ablation is only a few points. The architecture is an incremental refinement of subgraph
GNNs, not a step change, which is consistent with the senior's general critique of the field.

### W8. Classification framing and negative-sampling and protocol dependence [paper][survey]
S2DN scores links as binary classification with sampled negatives and ranks against a small candidate
set (GraIL's 50-negative protocol). Results are sensitive to the negative sampler, and the 50-negative
ranking is not directly comparable to full-candidate ranking used by some newer methods. This is why
MGIL's reported FB15k-237 Hits@10 (about 87 to 96) looks far above S2DN's (about 67 to 91): likely a
protocol difference, not a like-for-like gap. The dependence itself is a weakness: the metric is only
as trustworthy as the candidate set.

### W9. Noise-robustness is only demonstrated against synthetic noise [paper]
S2DN's headline is denoising "unconvincing knowledge," and Tables 3 and 4 show it degrades less than
RMPI as noise rises. But the noise is synthetic: relations randomly replaced with other relations, and
triples randomly sampled from all entity-relation-entity combinations. That is the same synthetic-noise
weakness we flag against CCA. S2DN never faces realistic, semantically plausible, AI-generated
contamination, which is the noise that actually appears in modern KBs. Its robustness claim is untested
against the failure mode our project is about.

---

## 3. Empirical and reproduction weaknesses [measured]

### W10. Hardcoded hyperparameters silently override the CLI
The released code hardcodes params.lr = 0.01 and params.batch_size = 32 after argument parsing, so
paper hyperparameters (dim 64, lr 5e-4, in the appendix only) are ignored unless the code is patched. A
4h46m FB15k-237 run was invalidated by this before we caught it. The lesson is generic: grep the
training script for assignments to params.* after parsing.

### W11. Tiny inductive test sets, single-seed reporting, wide error bars
fb237_v1's inductive test set is 205 triples; one triple is worth roughly 0.5 Hits@k points. S2DN's
main tables report single numbers with no seeds or standard deviations. Our own shuffle control showed
a should-be-baseline run swinging more than 2 points in Hits@10 and MRR, so run-to-run variance exceeds
the small per-version deltas the paper relies on. Several of S2DN's reported advantages may not be
statistically distinguishable.

### W12. It is no longer the inductive SOTA [survey]
MorsE (2022), CATS (2024), MGIL (June 2026), and the foundation-model line ULTRA (ICLR 2024) postdate
or outrank S2DN on parts of the same benchmark. S2DN's genuine, defensible strengths narrow to WN18RR
and to noise-robustness (against synthetic noise, per W9).

---

## 4. Weakness-to-opportunity map (why this helps the project)

| S2DN weakness | Our move |
|---|---|
| W1 empty subgraph for isolated entities | The 69.6 percent zero-edge population becomes the honest coverage finding; entity-independent rule evidence (transfers to unseen, AUC 0.68) and external-lookup repair cover part of it |
| W2 text-blindness | BGE-M3 substrate and the self-healing text detector operate on the channel S2DN ignores; graph-text disagreement is only possible because S2DN-style structure and text are independent |
| W4 dense SR memory | The new 96 GB GPU removes the FB15k-237 v2 to v4 and NELL OOM wall; also validates our edge-list rule scoring over a dense adjacency |
| W5 SR redundant/inert | Already acted on: rule evidence moved to the score, not SR (Phase 2c) |
| W6 SS dataset-dependent | Phase B2 relation-similarity guidance for SS is where a principled improvement can live, if pursued |
| W8 protocol dependence | Fix the evaluation protocol before any cross-paper claim; report full-ranking alongside 50-negative |
| W9 synthetic-noise-only robustness | The realistic-fabrication injection set is the direct differentiator; test S2DN-style denoising against believable AI-generated noise, where it has never been evaluated |
| W12 not SOTA | Widen the baseline table (MorsE, MGIL, ULTRA); frame the contribution as the finding, not as beating S2DN |

The most paper-worthy single insight: W1, W2, and W9 are the same gap seen three ways. S2DN denoises
structure it can see, ignores text, and is only tested on synthetic noise; the low-resource emerging
entity has little structure, arrives as text, and is contaminated by realistic AI text. The method and
the problem miss each other exactly where our project lives.

---

## 5. What the 96 GB GPU unblocks (test plan for when it lands)

The new GPU (remote SSH, being set up around 2026-07-17) removes the memory wall that shaped several
findings. Note: NELL v1-v4 does NOT need it, NELL runs at S2DN defaults (dim 32, batch 16) and fits
16 GB, so it is reproducing on the local GPU now; only FB15k-237 v2-v4 (dim 64, batch 32) needs the
96 GB machine. In priority order:

1. Reproduce FB15k-237 v2, v3, v4 at true paper settings (dim 64, batch 32, hop 3), which 16 GB could
   not fit. Closes the last of Phase A and lets the FB15k-237 average be computed at a single batch
   size (removes W10/W4 as confounds).
2. Run the deferred RuleTrust paired-seed sweep (3 to 5 seeds, baseline vs mode=score) once the design
   is locked, the gating experiment for the whole neuro-symbolic thread (addresses W11).
3. Test S2DN and S2DN-style denoising against the realistic-fabrication injection set rather than
   synthetic noise (directly probes W9), on both English and the multilingual bridge.
4. Larger enclosing subgraphs (higher hop, more max_links) to see whether SR's contribution grows when
   there is more structure to refine, or stays inert (probes W4/W5 at scale).

Protocol caution carried from the survey: before comparing any of these numbers to MGIL, MorsE, or
ULTRA, confirm the ranking protocol (50-negative vs full-candidate) matches.

---

## 6. Two-line brief for the mentor meeting

S2DN's every weakness traces to one choice, the endpoint enclosing subgraph: it dies on isolated
emerging entities, ignores text, only handles seen relations, has a dense memory-heavy structure module
that is largely redundant with its own GNN, and its noise-robustness is proven only against synthetic
noise. It is also no longer the inductive SOTA (MorsE, MGIL, ULTRA). All of this points the project at
the channel S2DN cannot use: text on structure-poor, low-resource, AI-contaminated entities.
