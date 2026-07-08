# Dataset Choice (resolves skeleton open-decision #1)

**Status:** decided 2026-06-23.
**Multilingual-inductive dataset = DBP-5L** (augmented + inductive-split into "DBP-5L-Ind").
**Monolingual-inductive dataset = Wikidata5M-Ind.** **Optional 2nd = mOKB6** (cross-script only).

---

## Selection criteria (priority order)
1. Has a genuinely **low-resource language** (small per-language KG); needed for the Idea-3
   cross-lingual-anchor result (ablation Table 3).
2. Has / can get **entity descriptions**; non-negotiable for the BGE-M3 text bi-encoder.
3. **Separate per-language KGs + cross-lingual alignment links**; so "fact missing in language A,
   present in B" and cross-lingual anchors are literally expressible.
4. Allows **entity-disjoint inductive splits**, and fits 16 GB.

## Candidates

| Dataset | Structure | Langs | Low-resource? | Text? | Align links? | Scale | Framing |
|---|---|---|---|---|---|---|---|
| **DBP-5L** (chosen) | per-lang KGs + align | EN/FR/ES/JA/EL | **Yes (EL/Greek)** | augment (Wiki abstracts) | **Yes ~40%** | 225K triples | closed-world KGC |
| Wikidata5M-multi (MKGC) | 1 KG + multi text | EN/FR/IT/JA/ZH | No | built-in | n/a | 3.0M, heavy | closed-world KGC |
| mOKB6 | open KB (phrases) | EN/HI/TE/ES/PT/ZH | Yes (TE/HI + scripts) | thin | linked | 42K | Open KBC (off-track) |
| Wikidata5M-Ind | 1 KG, inductive | EN | n/a | yes | n/a | ok | closed-world inductive |

## DBP-5L statistics (the numbers that decided it)

Total: 56,590 entities, 1,392 relations, 225,831 triples; ~40% of each KG's entities align to others.

| Lang | Entities | Relations | Triples | Aligned |
|------|---:|---:|---:|---:|
| EN | 13,996 | 831 | 80,167 | 16,916 |
| FR | 13,176 | 178 | 49,015 | 16,877 |
| ES | 12,382 | 144 | 54,066 | 16,347 |
| JA | 11,805 | 128 | 28,774 | 16,263 |
| **EL (Greek)** | **5,231** | **111** | **13,839** | **9,042** |

EL is ~1/6 of EN -> the low-resource target. **JA is the mid/low second** (28.8K triples).

## Why DBP-5L over the others
- **Greek = real low-resource language.** The Idea-3 anchor result needs this column; Wikidata5M-
  multi has no low-resource language at all.
- **Separate KGs + ~40% pre-aligned entities** = the exact substrate cross-lingual anchors need
  (pull an EN anchor for an EL query via the alignment link).
- **Canonical multilingual-KGC benchmark** -> KEnS, ALIGNKGC, SSAGA, FedMKGC are directly
  comparable baselines. mOKB6 (Open KBC, surface-form entities, different metrics) would break that.
- **225K triples fits 16 GB easily**; Wikidata5M-multi (3.0M) does not fit the lightweight plan.

## Construction work = the benchmark contribution ("DBP-5L-Ind")
1. **Descriptions:** fetch multilingual Wikipedia/DBpedia abstracts per entity per language.
   Missing low-resource descriptions (common in EL) are a FEATURE; exactly the gap cross-lingual
   sharing fills (use the EN description when EL is absent).
2. **Inductive splits:** hold out a set of entities as unseen at train time; keep their
   descriptions + a few support edges in the inference graph. Document the protocol; release it.

## Settings, concretely
- **Monolingual inductive:** Wikidata5M-Ind (recognized; SimKGC MRR 71.4 reference). DBP-5L-EN
  inductive slice = controlled within-benchmark monolingual baseline.
- **Multilingual inductive:** DBP-5L-Ind (5 langs).
- **mOKB6:** optional appendix only, for cross-script (Telugu/Hindi) robustness.

## Knock-on change
Ablation Table 3 language columns: ~~EN/FR/IT/JA/ZH~~ -> **EN / FR / ES / JA / EL**, with **EL the
low-resource column to watch** (and JA second).

Related: [[skeleton.md]], [[ablation_plan.md]].
