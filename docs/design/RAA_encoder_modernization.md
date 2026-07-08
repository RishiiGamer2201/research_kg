# Task 2; RAA-KGC Encoder Modernization (Decision)

**Status:** decided 2026-06-23.
**Decision:** replace RAA-KGC's `bert-base-uncased` encoders with **BGE-M3** as the primary;
keep a tiered set of alternatives for ablation.

---

## 1. Why this task is load-bearing (not cosmetic)

RAA-KGC (19-June notes / 10-June flowchart) is a **two-unshared-encoder + InfoNCE + in-batch
negatives** bi-encoder; i.e. the **SimKGC lineage** of text-based KGC. Two consequences:

1. **It is natively inductive.** An entity is represented by *encoding its description*, not by a
   memorized embedding row, so unseen entities are handled by construction. SimKGC reaches
   **MRR 71.4 on Wikidata5M-Ind**; impossible for TransE-style transductive models. This makes
   RAA-KGC a second inductive backbone (alongside CBLiP) and the natural carrier of cross-lingual
   signal for the multilingual half of the project.
2. **`bert-base-uncased` is English-only.** A multilingual + inductive system cannot run on it.
   So the swap is *required*, and the encoder we pick also decides whether **Idea 3**
   (cross-lingual anchors; favor high-resource-language neighbors for low-resource queries) is
   even expressible: anchors and candidates in different languages must live in one space.

Continuity bonus: **BGE-M3 is built on XLM-RoBERTa**, the multilingual sibling of BERT; a clean
lineage upgrade from `bert-base-uncased`.

---

## 2. The decision

| Role | Model | Size | Rationale |
|------|-------|------|-----------|
| **Primary (main model)** | **BGE-M3** | ~568M | 100+ langs, retrieval-trained, strong cross-lingual alignment, 8K ctx, fine-tunes on 16 GB with a usable batch. Best balance of multilingual + cross-lingual + trainable. |
| Light baseline | multilingual-E5-base | 278M | Smaller -> bigger batch -> **more in-batch negatives** (matters a lot for contrastive KGC). Speed/accuracy floor. |
| Modern contender | Qwen3-Embedding-0.6B | 600M | Newest LLM-based, instruction-aware; benchmarks the BGE-M3 choice against the 2025/26 SOTA family. |
| ~~Scale ablation~~ OUT OF SCOPE | Qwen3-Embedding-8B / Llama-Embed-Nemotron-8B | 8B | Dropped: project is 16 GB-permanent (no A100/cloud). 8B embedders do not fit and are not part of the experimental plan. |
| Cross-lingual probe | LaBSE | 471M | Weaker general retrieval but trained explicitly on translation-pair alignment; the cleanest tool for the **Idea 3** cross-lingual-anchor study. |

**MTEB context (June 2026):** Qwen3-Embedding-8B leads multilingual (~70.6), Qwen3-0.6B ~64.3,
NVIDIA Nemotron-8B tops multilingual among open-weight; BGE-M3 is the open production standard
for 100+ languages.

---

## 3. Where each encoder slots into RAA-KGC

RAA-KGC uses two towers (per the flowchart):
- **g1 (query / anchor encoder):** encodes the Classic Query `[CLS] head : desc [SEP] relation [SEP]`
  AND the Anchor-Enhanced Queries (classic query + up to 5 anchor entities + their descriptions).
- **g2 (candidate encoder):** encodes Candidate Entity Query `[CLS] candidate : desc [SEP]`.

Everything downstream is unchanged by the swap: InfoNCE training with SN + IBN + IBRN negatives,
`Total Loss = alpha * Anchor Loss + beta * Classic Loss`, and inference
`Combined Score = max(anchor sim) + max(classic sim)`. **Only the encoder backbone changes.**

### Two design knobs the swap forces (each an ablation)
1. **Shared vs unshared towers.** SimKGC/RAA use *unshared* g1, g2. With a ~568M multilingual
   model that doubles memory on 16 GB. **On 16 GB, SHARED is mandatory** (one BGE-M3 for both
   towers); unshared is a deferred ablation for when more VRAM is available.
2. **Encoder size vs in-batch negatives.** Bigger encoder -> smaller batch -> fewer negatives ->
   weaker contrastive signal. This is the main reason BGE-M3/mE5 beat an 8B for the *primary*.

### Per-model input conventions (don't mix these up)
- **BGE-M3:** no special instruction prefix for dense retrieval; use the dense output (can add
  sparse/multivector later as an enhancement).
- **mE5:** requires `query: ` on the g1 side and `passage: ` on the g2 side.
- **Qwen3-Embedding:** instruction-aware; an explicit task instruction can be prepended to the
  query (g1) side; candidate side left plain.

---

## 4. Compute notes (16 GB is the binding constraint)

Current compute = a single **RTX 5070 Ti 16 GB**; **no A100/cloud right now** (Kaggle/Colab free
tiers are also 16 GB-class). Everything in the "now" plan must fit 16 GB:

- **BGE-M3 (primary):** full fine-tune with **gradient checkpointing + bf16 + gradient
  accumulation** (accumulate to recover the large *effective* batch contrastive KGC needs, since
  the real batch is VRAM-capped). If memory-tight, **LoRA on the encoder** instead of full FT.
- **Shared tower is mandatory** here (two unshared ~568M towers + a big batch will not fit).
- **mE5-base (278M)** is the fallback if BGE-M3 batches end up too small for good negatives.
- **8B models are out of scope now** (deferred to future A100/cloud).
- Cross-lingual sharing (Idea-3 lever) = pulling anchor / neighbor descriptions from a
  high-resource language when the query language is low-resource; data-side, costs no extra VRAM.

---

## 5. Open items
- Confirm BGE-M3 dense-only vs dense+sparse hybrid for the candidate retrieval / scoring stage.
- Decide anchor-language policy for Idea 3 (always high-resource? mixed? learned?).
- Batch size achievable per encoder on 16 GB vs A100 (sets the negative count); measure early.

Related: [[../paper_recreations/MKGC_KL-GMoE_architecture.md]] (IER reranking composes on top of
this; KL-GMoE's cross-lingual *parameter* sharing is a separate, optional lever). Feeds task 3
(skeleton).
