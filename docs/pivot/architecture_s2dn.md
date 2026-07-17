# Architecture: S2DN (the structural inductive model)

Written 2026-07-17. Standalone description of S2DN (Learning to Denoise Unconvincing Knowledge for
Inductive KGC, AAAI 2025, 03121-MaT / arXiv 2412.15822), the model the mentor ladder reproduces and
modifies. Its weaknesses are in [s2dn_architecture_weaknesses.md](s2dn_architecture_weaknesses.md);
this doc is the neutral "what it is." Compared against our own model in
[differentiate.md](differentiate.md).

Style note: no emojis, no shorthand dashes.

---

## 1. What task it solves

Inductive knowledge graph completion, framed as binary classification. Given a candidate triple
(u, r, v) where u or v is an emerging (unseen at training) entity, predict the probability that the
triple is true. It reasons entirely over local graph structure; it reads no entity text.

Datasets: WN18RR, FB15k-237, NELL-995, each in the GraIL inductive splits v1-v4, where the training
graph and the test graph share the relation vocabulary but have disjoint entity sets.

## 2. The pipeline, end to end

```text
target triple (u, r, v)
  -> enclosing subgraph extraction (GraIL construction)          [Section 3]
  -> two parallel branches on that subgraph:
        Semantic Smoothing  -> RGNN  -> h_sem                     [Section 4]
        Structure Refining  -> GCN   -> h_str                     [Section 5]
  -> score: p(u,r,v) = sigmoid(MLP([h_sem concat h_str]))         [Section 6]
  -> train: binary cross-entropy + KL smoothing term + L2         [Section 6]
```

## 3. Enclosing subgraph extraction (the foundation, inherited from GraIL)

For the target (u, r, v), take the k-hop neighbourhoods of u and of v, keep the nodal intersection
V = N_k(u) intersect N_k(v), and induce the triples among V. This subgraph is the only input the rest
of the model sees. Node features are GraIL's double-radius vertex labelling: each node is labelled by
its shortest-path distances to u and to v, a purely structural, text-free feature. Default k (hop) is
3.

Consequence to remember: if the emerging entity has no neighbourhood, the intersection is empty and
there is nothing to reason over. Everything below assumes a non-trivial subgraph exists.

## 4. Semantic Smoothing branch (denoise relational semantics)

Purpose: KGs contain semantically inconsistent relations (their example: located_in and lie_in mean
the same thing). Smoothing merges similar relations into a shared representation so the model is not
confused by surface relation identity.

Mechanism:
- Over the subgraph's relation set, compute smoothing weights w = softmax(E W^T + b), where E is the
  |R| x dim relation embedding matrix and W is trainable.
- Sample a smoothed relation assignment R-tilde with the Gumbel-Softmax trick (differentiable over the
  discrete choice of which relations merge), temperature tau.
- Form smoothed relation embeddings E-tilde = R-tilde E.
- Run a Relational GNN (RGNN) over the subgraph using E-tilde, then mean-pool node states through a
  ReLU to the branch representation h_sem.
- A KL trade-off term (coefficient lambda) pulls E-tilde back toward E to prevent over-smoothing from
  collapsing genuinely distinct relations.

The RGNN node update (layer l) aggregates over smoothed relations r in R-tilde and neighbours, with a
sigmoid attention weight alpha_{i,r} per node-relation pair.

## 5. Structure Refining branch (denoise unreliable edges)

Purpose: prune noisy or task-irrelevant edges in the subgraph so reasoning runs on a reliable
structure.

Mechanism:
- Treat every node pair (i, j) in the subgraph as an independent Bernoulli edge with reliability
  pi_{i,j} = sigmoid(Z(i) Z(j)^T), where Z = MLP(node features). A smaller pi means the edge is more
  likely noise.
- Optimise pi jointly with the task via the concrete-relaxation (reparameterization) trick, since a
  hard Bernoulli is not differentiable.
- After relaxation the subgraph is a weighted fully connected graph, which the paper notes is
  computationally intensive; edges with pi below 0.5 are dropped, yielding the refined subgraph
  g-tilde.
- Run an L-layer GCN over g-tilde with the same structural node features, mean-pool through a sigmoid
  to the branch representation h_str.

## 6. Scoring and training

- Score: p(u,r,v) = sigmoid(MLP([h_sem concat h_str])). The two branch representations are
  concatenated and passed through a classifier.
- Loss: cross-entropy on the link label, plus the KL smoothing trade-off term D(E-tilde || E) scaled
  by lambda, plus L2 regularisation on the parameters.
- Training is by sampled negatives (num_neg_samples_per_link default 1); evaluation ranks the gold
  tail against a candidate set using GraIL's 50-negative ranking protocol, reporting filtered MRR,
  Hits@1, Hits@10.

## 7. Hyperparameters (as reproduced)

| Dataset | lr | emb_dim | batch | hop | epochs | source |
|---|---:|---:|---:|---:|---:|---|
| WN18RR | 0.01 | 32 | 16 | 3 | 100 | code defaults (official README runs no flags) |
| NELL-995 | 0.01 | 32 | 16 | 3 | 100 | code defaults (official README) |
| FB15k-237 | 0.0005 | 64 | 32 | 3 | 100 | paper appendix (differs from defaults; the released code hardcoded lr=0.01 over the CLI, a trap we hit) |

## 8. What ablation tells us about the two branches (from the paper's own tables)

Removing either branch costs only a few Hits@10 points, and the two matter differently per dataset:
- WN18RR average Hits@10: full 81.23, without Semantic Smoothing 78.49, without Structure Refining
  76.31 (so Structure Refining matters slightly more here).
- FB15k-237 average Hits@10: full 81.25, without SS 79.68, without SR 78.97.
Neither module is dominant; S2DN is an incremental refinement of the GraIL subgraph-GNN line, with its
distinctive claim being robustness to noise (tested against synthetic noise only).

## 9. One-line summary

S2DN reasons about an unseen entity purely through the structure of the local subgraph between the two
endpoints, denoising that subgraph two ways (smoothing similar relations, pruning unreliable edges),
and scores the link as a binary classification. It is structural, English-only in practice, and
text-blind by design.
