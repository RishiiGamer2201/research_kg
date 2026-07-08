# Ablation Plan

**Status:** draft 2026-06-23. Tied to `skeleton.md`. Cells are placeholders until runs exist.
**Settings:** Mono-Ind = monolingual inductive (Wikidata5M-Ind); Multi-Ind = multilingual
inductive (constructed entity-disjoint splits over DBP-5L / MKGC-Wikidata5M-multilingual).
**Metrics (every cell):** MRR, Hits@1, Hits@3, Hits@10 (filtered). Chat/summary views show a
subset for width; the full table carries all four.

> The main *results* table (full system vs external baselines: RAA-KGC-BERT, SimKGC, CBLiP-only,
> ALIGNKGC, MKGC/KL-GMoE) is separate from these; these tables isolate OUR components.

---

## Table 1; Main component ablation (additive build-up)

Each row adds exactly one component to the row above, so the marginal MRR delta is the component's
contribution. This is the headline ablation.

| # | Configuration | Adds | Mono-Ind MRR | Mono-Ind H@10 | Multi-Ind MRR | Multi-Ind H@10 | Isolates / claim |
|---|---------------|------|:---:|:---:|:---:|:---:|---|
| 0 | RAA-KGC original (BERT, InfoNCE) | reference | - | - | n/a* | n/a* | task-2 motivation (BERT is English-only) |
| 1 | Base bi-encoder (BGE-M3, InfoNCE) | multilingual encoder | - | - | - | - | the inductive+multilingual backbone (Idea 1 enabler) |
| 2 | + RAA anchors (same-language) | relation-aware anchors | - | - | - | - | value of anchors |
| 3 | + CRR loss (replaces InfoNCE) | CRR | - | - | - | - | **Idea 2** (CRR, 1st time multilingual+inductive) |
| 4 | + IER reranking | iterative rerank | - | - | - | - | borrowed MKGC trick |
| 5 | + cross-lingual anchors | high-resource anchors | = row 4** | = row 4** | - | - | **Idea 3** (cross-lingual anchors) |
| 6 | + KL-GMoE adapters (stretch) | cross-lingual params | - | - | - | - | borrowed MKGC idea (param-level sharing) |
| 7 | + CBLiP fusion (stretch) = **Full** | structural signal | - | - | - | - | does structure beat text-only? |

\* Row 0 cannot run Multi-Ind (English-only encoder); that *is* the motivation for task 2.
\** Row 5 = row 4 in the monolingual setting (no other languages to source anchors from).

Read it as: rows 1->5 are the v1 story ("modern multilingual base + the two transductive tricks +
IER + cross-lingual anchors"); rows 6-7 are stretch. Reviewers read the **per-row MRR delta**.

---

## Table 2; Loss ablation (isolates Idea 2: CRR)

Architecture fixed at the full v1 stack; only the training loss changes.

| Loss | Mono-Ind MRR | Multi-Ind MRR | Notes |
|------|:---:|:---:|---|
| InfoNCE (SimKGC default) | - | - | baseline objective |
| Margin / ranking loss | - | - | classic KGC ranking loss |
| **CRR** | - | - | our port of KGCRR's loss |
| InfoNCE + CRR | - | - | does combining help? |

Claim to support: CRR (only ever tested English + transductive on FB15k-237/WN18RR) still improves
ranking in the inductive + multilingual regime.

---

## Table 3; Anchor ablation (isolates Idea 3: cross-lingual anchors)

The cross-lingual story needs a **per-language** breakdown; the thesis is that gains concentrate
on the **low-resource** languages.

| Anchor config | EN | FR | ES | JA | EL | Avg MRR |
|---------------|:--:|:--:|:--:|:--:|:--:|:--:|
| no anchors | - | - | - | - | - | - |
| same-language anchors | - | - | - | - | - | - |
| **cross-lingual anchors (high-resource source)** | - | - | - | - | - | - |
| relation-level fallback (for brand-new heads) | - | - | - | - | - | - |

Languages are DBP-5L's (EN/FR/ES/JA/**EL**); **EL (Greek) is the low-resource column to watch**,
JA second. Plus an anchor-count sweep k ∈ {0, 1, 3, 5, 10}. Expected shape: cross-lingual anchors
lift EL (then JA) most, ~flat on EN.

---

## Table 4; Encoder ablation (isolates task-2 modernization)

Architecture fixed; swap the backbone. Justifies the BGE-M3 choice empirically.

| Encoder | Params | Mono-Ind MRR | Multi-Ind MRR | Notes |
|---------|:---:|:---:|:---:|---|
| bert-base-uncased (original RAA) | 110M | - | n/a | English-only |
| XLM-R base | 270M | - | - | multilingual BERT sibling |
| mE5-base | 278M | - | - | light, big-batch |
| **BGE-M3** | 568M | - | - | **chosen primary** |
| Qwen3-Embedding-0.6B | 600M | - | - | modern LLM-based contender |

---

## Table 5; Structural fusion ablation (CBLiP, stretch)

| Config | Mono-Ind MRR | Multi-Ind MRR | Notes |
|--------|:---:|:---:|---|
| text-only (no CBLiP) | - | - | our core |
| + CBLiP late fusion (best λ) | - | - | does structure add over text? |
| λ sweep {0, 0.25, 0.5, 0.75, 1} | - | - | 1.0 = text-only, 0.0 = structure-only |

---

## What each table is FOR (so we don't run experiments we won't use)
- T1 proves the system is more than the sum of borrowed parts (per-component deltas).
- T2 = Idea 2 evidence. T3 = Idea 3 evidence (the per-language shape is the actual result).
- T4 retro-justifies task 2. T5 decides whether CBLiP earns a place at all.

**Build order:** T1 rows 1->4 come free as the v1 core is assembled; T2 and T4 are cheap swaps on
the finished pipeline; T3 needs the constructed multilingual benchmark first; T5 + T1 rows 6-7 are
last (stretch).

Related: [[skeleton.md]], [[RAA_encoder_modernization.md]], [[../paper_recreations/MKGC_KL-GMoE_architecture.md]].
