# Research Direction Assessment (2026-07-03)

**Verdict up front: the direction is correct and the gap claim is real and verified open.
But two experimental-validity bugs must be fixed before any number is final, and the
calibration data changes what the strongest framing is.**

Sources: SS-AGA, ALIGNKGC, KL-GMoE verified from the PDFs in `Research/Multilingual aspect/`
(primary sources, read directly). JMAC verified via arXiv fetch. Wikidata5M-Ind numbers from
the SimKGC/BLP/StATIK papers (single-fetch confidence, but well-known figures).

---

## 1. Scooping check; GAP CLAIM VERIFIED OPEN [done]

Checked every relevant line of work through EMNLP 2025:

| Paper | Venue | Setting | Unseen entities? |
|---|---|---|---|
| KEnS | EMNLP-F 2020 | DBP-5L, transductive (random triple split) | No |
| ALIGNKGC | AKBC/arXiv 2021 | DBP-5L, transductive; "unseen test" = unseen **facts**, entities still share IDs across languages | No |
| SS-AGA | NAACL 2022 | DBP-5L, transductive 60/30/10 triple split (verified from paper §4.1) | No |
| JMAC | EMNLP-F 2022 | DBP-5L, transductive, adds surface (text) info | No |
| GC-PLM | arXiv 2024 | Prix-LM DBpedia 7-lang, transductive | No |
| KL-GMoE | EMNLP-F 2025 | Custom Wikidata5M 5-lang (EN/FR/IT/JA/ZH, **no Greek, no DBP-5L**); "unseen" = unseen **languages** (verified: 0 hits for "inductive"/"Greek" in the paper) | No |

No entity-disjoint inductive split of DBP-5L exists, and no multilingual-KGC paper
evaluates on unseen entities. **DBP-5L-Ind is genuinely first.** Related-work section
should make the three-way distinction explicit: unseen *facts* (ALIGNKGC) vs unseen
*languages* (KL-GMoE) vs unseen *entities* (ours; hardest, breaks all alignment-seed
and entity-embedding methods by construction).

## 2. Calibration; what the verified numbers say

**Transductive DBP-5L (all entities seen), per-language MRR:**

| Method | Type | EL | JA | ES | FR | EN |
|---|---|---|---|---|---|---|
| TransE | struct | 24.3 | 25.3 | 24.4 | 27.6 | 16.9 |
| KG-BERT | text | 27.3 | 38.7 | 34.0 | 35.4 | 21.0 |
| AlignKGC | struct+align | 33.8 | 41.6 | 35.1 | 37.4 | 22.3 |
| SS-AGA | struct+align | 35.3 | 42.9 | 36.6 | 38.4 | 23.1 |
| JMAC w/ SI | struct+text | **71.7** | **66.8** | n/r | n/r | n/r |
| **Ours (inductive!)** | text | 11.8 | 7.7 | 20.9 | 20.0 | 12.2 |

**Monolingual English inductive (Wikidata5M-Ind), MRR:** DKRL 23.1 · KEPLER 40.2 ·
BLP-SimplE 49.3 · SimKGC 71.4 · StATIK 77.0.

Implications:
- A careless reviewer sees 15.59 overall vs 35-72 transductive and 49-77 English-inductive.
  **The paper must own this framing**: entity-disjoint + multilingual + low-resource is a
  strictly harder regime, and ours are the FIRST numbers on it. That argument only lands if
  baselines are run **on our split**; no published number is comparable (cuts both ways).
- FR/ES (~20) vs their transductive ceiling (~37-38) is a defensible inductive gap (~45%).
  JA is the anomaly: 7.7 vs 42.9 transductive (-82%). The JA error analysis (B3) is not
  optional; it's the most exposed number in Table 2.
- JMAC (71.7 EL transductive with text) is the number most likely to be quoted against us.
  Cite it proactively; note it memorizes entity embeddings + uses alignment seeds, both
  impossible for unseen entities.

## 3. Code audit; two validity bugs, several protocol gaps

### P0-A: eval ran at max_length 96 for models trained at 128/160
`eval_dbp5l.py --max-length` defaults to 96; the eval commands for Runs A/B/E/F (per
CHAT_HISTORY) never passed it. Every headline number was measured with queries/candidates
truncated to 96 tokens while trained at 128 (E: 160).
- Likely **understates** Run B; re-eval could be a free MRR gain.
- Invalidates the "ml=160 doesn't help" conclusion (E was also evaled at 96).
- **Action (30 min/run, GPU is idle):** re-eval A, B, E, F with matching `--max-length`.

### P0-B: the XL-anchor negative result is confounded by a train/eval mismatch
The XL runs train with anchor-averaged queries `normalize((q+a)/2)`, but `eval_dbp5l.py`
has **no anchor code path**; it evaluates with the bare query `q`. The model was scored
out of its training distribution. This is the same bug class as run v2 ("train/eval query
format mismatch"), which alone explained a ~3x MRR difference.
- The "-68%, XL anchors fight BGE-M3 alignment" claim is currently **not defensible**;
  part (possibly most) of the drop may be the mismatch, not the anchors.
- **Action:** add anchor-aware eval (encode anchors from support/train graph, RAA-style
  combined score) and re-eval the saved `crr_xl` checkpoints. Then the negative result is
  either rescued (real, now clean) or dies (report honestly / drop). Do NOT write Section 5
  around it before this.

### P1: protocol gaps to fix or disclose
1. **Tail-only evaluation**; no head prediction / inverse relations, in training or eval.
   Legitimate, but must be stated; any baseline must use the identical protocol.
2. **Support triples absent from the filter map**; support.txt facts are true facts; not
   filtering them slightly deflates metrics. Also support edges are currently **unused by
   the model entirely**; the benchmark provides them; the paper must say the model is
   text-only and doesn't consume them (or use them for the anchor fallback).
3. **Hard negatives don't mask other true tails of (h,r)**; only the exact target is
   masked in `get_hard_negatives`; other valid tails become false negatives (label noise).
   SimKGC masks these. Cheap fix; fold into the 3-seed retrain.
4. **In-batch duplicate tails** not masked (same false-negative issue, minor).
5. **Valid set is transductive** (both entities seen) while test is inductive; model
   selection happens off-distribution. Disclose in the benchmark protocol; v2 could hold
   out a small inductive valid entity set.
6. Ties broken optimistically in ranking (`>` not `>=`); standard-ish, minor.

## 4. Baseline reality check (A1 revision)

- **ALIGNKGC / SS-AGA / KEnS cannot run on DBP-5L-Ind at all**; they learn per-entity
  embeddings (shared IDs / alignment seeds); unseen entities have no representation.
  That is the paper's motivation, not a baseline row. Put them in Table 1 as
  "n/a; requires seen entities" with a sentence, and cite their transductive numbers as
  the ceiling. Don't burn 2-3 days making alignkgc-master run just to prove ~0.
- **The real, runnable external baseline is SimKGC with a multilingual encoder (mBERT)**
  on DBP-5L-Ind; code already cloned and working from Week 1. This is B2 promoted to
  must-do; it isolates "modern encoder (BGE-M3) vs 2022 recipe" and gives reviewers the
  comparison row they need.
- Second cheap row: **LaBSE / mE5 zero-shot** (already have LaBSE working) → shows the
  fine-tuning contribution isn't encoder-specific.
- Run F is done and WORSE (14.37 vs 15.59) → 40-epoch overfitting confirmed; Run B stays
  headline. Run G stays cut.

## 5. Recommended framing (A4 decision)

**Benchmark-first paper:** "DBP-5L-Ind: multilingual KGC breaks when entities are unseen;
a benchmark and first baselines." Everything else slots under it:
- The 12x-over-zero-shot recipe = "first strong baseline" (not a SOTA claim; nothing to
  beat, which is the safe position).
- CRR+HN synergy = analysis finding.
- XL-anchor negative result = finding **only if it survives P0-B**; the JMAC contrast
  (alignment supervision helps structural models +15 MRR, hurts/does nothing for
  pre-aligned text encoders) is the interesting story if it does.
- Transductive-SOTA table (Section 2) supplies the "how hard is this" calibration.

A method/synergy framing is weaker: the method is a composition of known parts, and with
no comparable published numbers a "our method wins" story has nothing to beat. A pure
negative-result framing can't carry an AAAI main-track paper alone.

## 6. Reviewer expectations & venue norms (recovered from research, 2026-07-03)

**Hard gates (AAAI reproducibility checklist; weighed in decisions):**
- Report the **number of runs** behind each result; single-seed point metrics without
  variance fall short. Precedent: StATIK (NAACL 2022) averaged 5 runs (2 for Wikidata5M).
  → A2 (3 seeds) + A3 (significance) are checklist items, not nice-to-haves. Significance
  testing applies to the degradation claim (15.59→3.17) as much as to improvements.
- Novel dataset (DBP-5L-Ind) must be **publicly released with a research-permissive
  license** and a data appendix at submission; split statistics (entity/triple counts per
  language) must be documented explicitly. License must be compatible with DBpedia/DBP-5L
  upstream.
- **LLM-generated description fills (1,042 Llama-3.2 entities) must be disclosed** as data
  provenance (Responsible-NLP-checklist norm; checklist violations can trigger desk reject
  at *ACL and the culture is spreading).

**Working in our favor:**
- ARR explicitly instructs reviewers that *lacking SOTA results is not a valid rejection
  reason*; 15.59% doesn't need to beat transductive numbers if claims are scoped.
- Baseline demands are bounded: *a paper needs evidence sufficient for its own claims*;
  supports skipping the ALIGNKGC inductive adaptation.
- Precedent: KL-GMoE (EMNLP-F 2025) runs TransE/RotatE/HAKE/GC-PLM/DIFT as baselines;
  **no** KEnS/AlignKGC/SS-AGA. Recent mKGC reviewers accept embedding+PLM baseline suites.
- Negative results are endorsed as contributions; but the negative-results community's
  own norm is that they must come **with a mechanistic why**, not a bare failure. (Another
  reason P0-B must be resolved first: the current "why" may be an artifact.) Negative
  result as *headline* is acknowledged as structurally risky; keep it as a secondary
  finding. (The Insights-from-Negative-Results 2026 deadline has passed; a short spin-out
  paper there remains possible post-AAAI.)

**Useful template:** Wikidata5M-SI (arXiv 2310.11917); English-only, so no scoop; is a
published template for documenting an entity-disjoint split (degree-stratified unseen
entities, up to 10 context facts per entity ≈ our support edges, k-shot ladder). Cite it
for the benchmark-construction methodology section; BLP (WWW 2021, 80/10/10 entity-disjoint
holdout) is the second construction precedent.

**Feasibility notes:** SimKGC trains Wikidata5M-Ind in ~11h on 4×V100 → DBP-5L-scale
(20x smaller) is easily tractable on the 5070 Ti. BLP is MIT-licensed with runnable
scripts; viable second external baseline if time allows. RAA-KGC numbers should be taken
from arXiv 2504.06129 (repo README has none).

## 7. Revised priority queue (supersedes Phase A ordering in TASK.md)

| # | Item | Cost | Why now |
|---|---|---|---|
| 1 | Re-eval A/B/E/F at correct max_length | 2h total | every published number depends on it; GPU idle |
| 2 | Anchor-aware eval; re-eval crr_xl checkpoints | 0.5-1 day | rescues or kills a headline claim (P0-B) |
| 3 | Fix hard-neg true-tail masking + support-filtering, then launch 3-seed Run B chain (seeds 42/123/777, ~21h) | 1 day wall | seeds (A2) + bug fix in one retrain batch |
| 4 | SimKGC-mBERT on DBP-5L-Ind (replaces ALIGNKGC as A1) | 1-1.5 days | the external baseline reviewers can hold |
| 5 | Related Work (A5) with the verified table from §2 | 1-2 days | numbers already gathered above |
| 6 | JA error analysis (B3) | 1 day | most exposed number after calibration |
| 7 | Bootstrap significance (A3) after seeds | 0.5 day |; |

Items 1-2 gate everything: do not draft Section 5 prose until they're done.
