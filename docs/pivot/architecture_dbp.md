# Architecture: DBP-5L Substrate (the textual multilingual inductive model)

Written 2026-07-17. Standalone description of our own model, the multilingual inductive KGC substrate
built on BGE-M3. This is the focused architecture view; the full component-by-component rationale with
every measured number is in [../ARCHITECTURE.md](../ARCHITECTURE.md) (Part A). Compared against S2DN in
[differentiate.md](differentiate.md); S2DN itself is in
[architecture_s2dn.md](architecture_s2dn.md).

Style note: no emojis, no shorthand dashes.

---

## 1. What task it solves

Multilingual inductive knowledge graph completion, framed as retrieval. For a query (head, relation,
?), rank all candidate tail entities by similarity to the query, where the correct tail may be an
entity unseen at training time, described in any of five languages (English, French, Spanish,
Japanese, and low-resource Greek).

Dataset: DBP-5L (five DBpedia language graphs, 56,589 entities, 1,392 relations, about 226k triples),
and on top of it DBP-5L-Ind, our entity-disjoint inductive split (20 percent of entities per language
held out entirely; evaluation triples must touch a held-out entity; up to 5 support edges per unseen
entity as context, filtered at evaluation).

## 2. The pipeline, end to end

```text
DBP-5L raw KGs (5 languages)
  -> entity-disjoint inductive split                                   [ARCHITECTURE.md Sec 1]
  -> per-entity description = name + neighbourhood serialisation
       (train and valid edges only, no leakage) + native Wikipedia     [Sec 2]
  -> shared bi-encoder:
       query text     = "head description [SEP] relation name"
       candidate text = "tail description"
       BGE-M3 (568M, frozen bf16) + LoRA r16 on attention q,v          [Sec 3-4]
       mean-pool -> L2 normalize -> cosine / learned temperature       [Sec 5]
  -> train: CRR ranking loss over 31 in-batch + 7 fresh mined
       hard negatives (entity cache re-encoded every epoch)            [Sec 6-7]
  -> infer: encode all 56,589 candidates once, cache; a new entity
       joins the index with one forward pass                           [Sec 5]
  -> eval: filtered ranking, within-language primary, cross-lingual
       robustness check; 3 seeds -> 26.51 +/- 0.31 MRR                 [Sec 8]
```

## 3. The inductive mechanism (text, not structure)

An entity is represented by encoding its text description, not by a learned per-entity vector. So an
entity unseen during training is usable the moment it has a description: one forward pass through the
frozen encoder places it in the same vector space as every trained entity. No retraining, no per-entity
parameters. This is what makes the model inductive, and it is a fundamentally different mechanism from
a structural subgraph model: the unseen entity needs text, not edges.

Measured dependence on text quality (the whole system rests on it): names only 0.41 MRR, plus
neighbourhood and relation text 3.1, plus Wikipedia abstracts 10.0, plus the full recipe 26.5. Text
quality is the single largest factor, larger than any architectural choice.

## 4. The multilingual mechanism (inherited, not built)

BGE-M3 is a multilingual retrieval encoder (built on XLM-RoBERTa, pretrained across 100+ languages).
Its pretraining already aligns the five languages and their scripts in one vector space, so
multilinguality is inherited rather than engineered. Evidence: ranking a query against all 56,589
entities in every language, instead of only same-language candidates, costs just 0.5 MRR, and explicit
cross-lingual anchor supervision adds nothing measurable on top. The encoder ablation (BGE-M3 26.51 vs
an mBERT rerun 24.08, and Greek 16.79 vs 10.63) shows the modern multilingual encoder is what carries
the low-resource languages.

## 5. Key components (one line each; full rationale in ARCHITECTURE.md)

- Encoder: BGE-M3, 568M, frozen in bfloat16, 1024-dim vectors.
- Adapter: manual LoRA rank 16 on the query and value attention projections of all 24 layers; about
  8M trainable parameters (1.4 percent); protects the pretrained cross-lingual alignment.
- Bi-encoder: one shared tower for query and candidate (not two, not a cross-encoder), so candidates
  cache once and a new entity is a single forward pass; scoring is cosine over a learned temperature.
- Loss: CRR, a differentiable reciprocal-rank surrogate; synergistic with hard negatives (CRR+HN
  about 13.8 vs about 10 for either alone).
- Negatives: 31 in-batch plus 7 mined hard negatives from a full-entity cache re-encoded every epoch
  (freshness is critical: a stale global pool hit 95 percent train accuracy but lost 3.6 MRR).
- Description text: name + neighbourhood serialisation (train/valid edges only) + native-language
  Wikipedia abstract, tokenized to 160 (Japanese needs the most tokens).
- Evaluation: filtered ranking, tail-only, within-language primary plus cross-lingual check, 3 seeds
  with bootstrap and Wilcoxon.

## 6. The self-healing layer that sits on top

Because the model consumes free-text descriptions, it is vulnerable to contaminated text. The audit
found about 70 percent of LLM-back-filled descriptions were fabrications, concentrated in Greek and
Japanese, and removing them improved Japanese by 1.95 MRR. The self-healing loop (Part B in
ARCHITECTURE.md) uses the graph's own structure to judge the text: serialise an entity's neighbourhood
and score its description's consistency against it, quarantine low-consistency descriptions, re-source
from native Wikipedia (recovered 45 percent) or fall back to the plain name, and measure the
downstream repair. This layer exists precisely because the model's evidence channel is text, and text
can be poisoned in a way structure is not.

## 7. One-line summary

The substrate represents an unseen entity by encoding its multilingual text description with a frozen
BGE-M3 plus small LoRA adapters, ranks candidates by cosine similarity, and is multilingual for free
through the encoder's pretrained cross-lingual geometry. It is textual, natively multilingual, and
structure-blind (it uses graph edges only after serialising them into text).
