# Differentiating the Two Models, with respect to Inductive + Multilingual + KGC

Written 2026-07-17. This compares the two architectures the project holds:

- S2DN, the structural inductive model ([architecture_s2dn.md](architecture_s2dn.md)), the mentor
  ladder's reproduce-and-beat target.
- The DBP-5L substrate, our textual multilingual inductive model
  ([architecture_dbp.md](architecture_dbp.md)).

The comparison is framed on the three axes that define the project's target cell: inductive,
multilingual, and the KGC task itself. The short version: both do inductive KGC, but through opposite
evidence channels (structure versus text), and only one of them is multilingual. That gap is exactly
the empty cell the project aims at.

Style note: no emojis, no shorthand dashes.

---

## 1. The core distinction in one sentence

S2DN answers "is (u, r, v) true?" by reasoning over the graph structure around the entity, while the
substrate answers "which tail fits (h, r, ?)" by encoding the entity's text and retrieving the nearest
candidate. Structure versus text is the axis everything else follows from.

## 2. Side-by-side

| Dimension | S2DN (structural) | DBP-5L substrate (textual) |
|---|---|---|
| Evidence channel | Graph structure only (text-blind) | Text only (structure used only after serialising into text) |
| How an unseen entity is represented | Its local enclosing subgraph and structural node labels | Its encoded text description (one forward pass) |
| What an unseen entity must have | Edges (a non-empty neighbourhood) | A description (some text) |
| Fails when | The entity has no edges (empty subgraph) | The entity has no text, or the text is contaminated |
| Relations | Must be seen at training (semi-inductive) | Encoded as text, so open and language-portable |
| Multilingual | No; structural features are language-agnostic but it cannot read or align multilingual text | Yes, natively, via BGE-M3's pretrained cross-lingual geometry |
| KGC framing | Binary classification of a triple, ranked against 50 negatives (GraIL protocol) | Retrieval, ranked against the full candidate pool by cosine similarity |
| Core computation | Enclosing subgraph extraction per triple; dense O(V^2) edge refining; RGNN and GCN | Encode all candidates once, cache, one matmul per query |
| Backbone | GraIL subgraph-GNN plus two denoising branches | Frozen BGE-M3 (568M) plus LoRA r16 |
| Data it runs on | WN18RR, FB15k-237, NELL-995 (English) | DBP-5L (EN, FR, ES, JA, EL) |
| Reference number | FB15k-237 v1 about 53 MRR reproduced; strong on WN18RR | 26.51 +/- 0.31 MRR on DBP-5L-Ind (3 seeds) |
| Robustness story | Denoises synthetic structural and semantic noise | Self-heals AI-contaminated text via structure |

## 3. Axis one: inductive (both, but by opposite mechanisms)

Both models are genuinely inductive: both handle entities never seen at training. The difference is the
mechanism, and the mechanisms fail in opposite places.

- S2DN is inductive through structure. A new entity is understood by the subgraph of known entities
  around it and by its structural position (distance labels to the two endpoints). This works when the
  new entity is embedded in known structure. It collapses when the new entity is isolated: no edges,
  no subgraph, no signal. Measured relevance: on DBP-5L, 69.6 percent of contaminated (low-resource,
  newly added) entities have zero edges, the exact case S2DN cannot touch.
- The substrate is inductive through text. A new entity is understood by encoding its description. This
  works when the new entity has text. It collapses when the entity has no description, or when the
  description is fabricated (the contamination problem).

The two failure modes are complementary, not overlapping. An entity with edges but no trustworthy text
is S2DN's strength and the substrate's weakness; an entity with a description but no edges is the
reverse. This complementarity is the technical reason the project treats them as two channels rather
than two competitors.

## 4. Axis two: multilingual (only the substrate, and this is the decisive gap)

This is where the two models are least equal.

- The substrate is multilingual by construction. BGE-M3's pretraining aligns the five languages and
  their scripts in one vector space, so the same query can retrieve a correct tail described in another
  language at a cost of only 0.5 MRR, with no explicit alignment engineering. The low-resource language
  (Greek) is carried by the encoder: BGE-M3 16.79 versus an mBERT rerun 10.63.
- S2DN is not multilingual and has no natural path to become so on its own terms. Its node features are
  structural (distance labels), which are language-agnostic in the trivial sense that they ignore
  language entirely, but that is the problem: it cannot use multilingual text, cannot exploit
  cross-lingual entity alignment, and requires a shared relation vocabulary. Applied to a multilingual
  KG it would treat each language graph as an isolated structural problem, gaining nothing from the
  cross-lingual signal that is the whole point of the multilingual setting.

Consequence: of the two models, only the substrate occupies the multilingual axis today. S2DN brings
structural inductive reasoning that the substrate lacks, but it brings it in a monolingual,
text-blind form. Making structural inductive reasoning multilingual is unsolved, and it is the cell the
project targets (the SOTA survey confirms this intersection is empty).

## 5. Axis three: the KGC task framing (classification versus retrieval)

Both do link prediction, but they pose it differently, which changes what "beating" each other even
means.

- S2DN frames KGC as binary classification: score one triple, trained with sampled negatives, evaluated
  by ranking the gold against 50 sampled negatives. The metric is sensitive to the negative sampler and
  the 50-candidate protocol, which is why cross-paper numbers (S2DN versus MGIL versus MorsE) are not
  directly comparable without checking the protocol.
- The substrate frames KGC as retrieval: encode the query, rank the gold tail against the entire
  candidate pool (up to 14k same-language, or all 56,589 cross-lingual) by cosine similarity. Ranking
  against the full pool is a harder, more realistic protocol than 50 negatives.

So the two reference numbers (S2DN's about 53 on FB15k-237 v1, the substrate's 26.51 on DBP-5L-Ind) are
not on the same scale, the same data, or the same protocol, and must never be compared directly. They
measure inductive KGC quality in two different worlds.

## 6. Why the project needs both: the synthesis

The differentiation is not to pick a winner; it is to show the two models are two halves of the target.

The target cell is inductive AND multilingual KGC. Neither model fills it alone:
- S2DN is inductive but monolingual and text-blind.
- The substrate is inductive and multilingual but structure-blind, so it is weak exactly where text is
  sparse or poisoned (the low-resource, zero-edge, contaminated case).

The project fuses them along the ladder:
1. Reproduce and improve S2DN on English (the structure channel), which is the mentor ladder.
2. Carry that structural inductive reasoning into the multilingual setting by converting DBP-5L-Ind into
   the GraIL/S2DN format (converter done and verified), giving a structure channel alongside the
   substrate's text channel in the same multilingual data.
3. Exploit the fact that the two channels are independent: when structure and text disagree about the
   same entity, that disagreement is the self-healing signal. The substrate provides the text channel
   and the downstream metric; S2DN-style structural reasoning (and the mined rules on top of it)
   provides the structure channel that judges the text, and that survives on the entities the text
   channel cannot (rule evidence transfers to unseen entities at AUC 0.68).

In one line: S2DN is the structure channel, the substrate is the text channel, only the substrate is
multilingual today, and the research contribution is making structural inductive reasoning multilingual
and using it to heal the text channel where it is weakest.

## 7. Summary table: who owns which axis

| Axis | S2DN | Substrate | Project move |
|---|---|---|---|
| Inductive | Yes (structural) | Yes (textual) | Keep both; use their complementary failure modes as two channels |
| Multilingual | No | Yes (native) | Bring S2DN's structural reasoning into the multilingual data (the empty cell) |
| KGC framing | Classification vs 50 negs | Retrieval vs full pool | Report each in its own protocol; never compare the raw numbers |
| Robustness | Synthetic noise denoising | Real AI-contamination self-healing | Fuse: structure judges contaminated text (self-healing) |
