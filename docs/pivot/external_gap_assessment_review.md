# External Gap Assessment: Capture and Critique

Written 2026-07-14. This memo captures the reusable content from the external document
`Claude KG.pdf` ("Research Gaps for an AAAI Knowledge-Graph Paper"), records an honest critique of
it, and points to the merged plan in [UNIFIED_PATHWAY.md](UNIFIED_PATHWAY.md).

Style note: no emojis, no shorthand dashes, so it stays clean if pasted elsewhere.

---

## 1. Provenance (read this before trusting any number in the PDF)

The PDF was produced by an external AI agent, not from this codebase directly. Its own Caveats
section states it:

- could not access a `project_knowledge_search` tool and reconstructed the research journal from the
  public GitHub repo (README, PROJECT_STORY_AND_PLAN.md, IMPLEMENTATION_PLAN.md);
- did not read the 37 AAAI PDFs; the theme map is built from public AAAI proceedings and aggregators;
- treats the repo state as "of 2026-07-07";
- did not independently reproduce any of our numbers (70 percent contamination, ROC-AUC 0.995, plus
  1.95 MRR, 26.51 MRR are all our own reported results).

Consequence: the PDF predates the mentor pivot entirely. It contains no mention of S2DN, the
reproduce-then-beat ladder, or RuleTrust, because all of that was created after 2026-07-08. It is a
"publish the assets you already have" strategy memo, useful as a cross-check, not as a plan of
record.

---

## 2. What is worth keeping (folded into the plan)

### 2.1 Competitor differentiators (verbatim-usable in related work)

The four nearest papers and the precise one-line differentiation for each:

- KG Error Detection with Contrastive Confidence Adaption (CCA), Xiangyu Liu, Yang Liu, Wei Hu
  (Nanjing University), AAAI 2024, Vol. 38(8), pp. 8824-8831, doi:10.1609/aaai.v38i8.28729.
  Closest on mechanism (text plus graph structure from triplet reconstruction), but its noise is
  synthetic (semantically similar and adversarial), it is monolingual English, detection only (no
  repair), and measures no downstream impact. This is the paper reviewers will most cite against us.
  Differentiation: CCA finds bad edges; we find AI-fabricated descriptions.
- Type-Information-Assisted Self-Supervised KG Denoising, AISTATS 2025, arXiv 2503.09916.
  Structure-based self-supervised noise detection, but uses no text descriptions (so no
  structure-vs-text disagreement), no multilingual angle, no repair, no downstream grounding.
- TruthfulRAG, AAAI 2026. Uses KGs to resolve factual conflicts at RAG inference time between
  sources, not contamination baked into a stored KB; no low-resource focus.
- Retrieval Collapses When AI Pollutes the Web, WWW 2026 (short paper). Proves AI pollution degrades
  retrieval (67 percent pool contamination leads to 80 percent-plus exposure contamination; accuracy
  stays deceptively stable while source diversity collapses) but proposes no detection, no KG signal,
  no repair. It motivates our direction rather than occupying it.

Adjacent but further: mRAKL (Findings of ACL 2025, constructs low-resource KGs via RAG, assumes
evidence is trustworthy), KG-TRICK (COLING 2025, fills missing text/links, does not audit
contamination), FactNet (2026, prevents contamination by deterministic construction rather than
detecting/repairing it).

### 2.2 The four-pillar novelty framing

The PDF's claim: no AAAI 2025/2026 paper, and no verified SIGIR/KDD/WSDM/WWW/ACL/EMNLP 2025-2026
paper, combines all four of: (1) detecting AI-fabricated contamination in a KB's own entity
descriptions, (2) using the KG's own structure (structure-vs-text disagreement) as the signal, (3)
concentrated in low-resource/non-Latin scripts, (4) with a measured downstream completion/grounding
effect plus repair. Each nearest prior work misses at least two pillars.

Use with care (see critique 3.4). This is a combination-novelty argument.

### 2.3 Venue timing (verified by the PDF, re-verify before submission)

- AAAI-27: abstracts due July 21, 2026; full papers July 28, 2026; conference February 16-23, 2027,
  Montreal. Limit 7 pages main content, max 9 total. No CJK package, so Greek and Japanese examples
  need romanization or figure-embedded text.
- WSDM 2027: Hong Kong, February 15-19, 2027 (20th ACM WSDM). Our docs cite full paper about
  Aug 24, 2026, with a Findings safety net. Stated pivot target.
- KDD 2027 Cycle 2 (about Feb 2027) and SIGIR 2027 are fallbacks; both fit KG data-quality work.

### 2.4 Landscape scale (motivation context)

AAAI 2026 accepted 4,167 of 23,680 submissions (17.6 percent, lowest in three years; up from 12,957
submissions and 23.4 percent at AAAI 2025). The competitive center of gravity is LLM+KG / GraphRAG
(crowded and risky). KG quality/denoising is the thinnest cluster, which is where our evidence lives.

### 2.5 The honest soft spot (the PDF gets this right)

The detector currently flags only about 57 percent of real fabrications, because the low-resource
entities that are most contaminated have almost no structure to check against. ROC-AUC 0.995 is on a
controlled injection benchmark, not on the real fabrications. The PDF's advice: if detector recall on
structure-poor entities stays near 57 percent, foreground the honest coverage limit and lead with the
downstream-grounding result as the headline instead of raw detection.

---

## 3. Critique (where the PDF is stale or oversells)

1. Unaware of the mentor pivot. The document reconstructs the repo as of 2026-07-07 and therefore
   never mentions S2DN, the reproduce-then-beat ladder, or RuleTrust. Its sequencing advice is a
   different philosophy (publish existing assets) from the mentor's bottom-up ladder (earn the
   self-healing result through a reproduced and beaten English inductive baseline with a
   neuro-symbolic method). We are keeping the mentor ladder as the backbone.

2. Its Gap 2 partly contradicts the senior. "Release DBP-5L-Ind as an AAAI Datasets and Benchmarks
   paper because it is done" is exactly the benchmark-swap framing the senior called not novel. The
   PDF flags this as a risk yet still ranks it as the safe AAAI play. Viable as a separable lower-risk
   product, but not a substitute for the novel contribution the senior asked for.

3. Ignores the RuleTrust reality. As of 2026-07-12 the RuleTrust Hits@10 gain is inside single-seed
   noise: the shuffle control moved metrics more than the real effect (see
   [RULETRUST_EXPERIMENT_LEDGER.md](RULETRUST_EXPERIMENT_LEDGER.md)). "Beat S2DN" is not yet achieved.
   The PDF's "about 80 percent of experiments already exist" optimism does not touch the part of the
   project that is actually unfinished and at risk.

4. The four-pillar novelty claim is fragile. "Nobody has combined pillars 1+2+3+4" is a
   combination argument, the same shape as the senior's original critique ("you just combined existing
   things"). PROJECT_STORY_AND_PLAN.md is more honest: claim a defensible gap, not absolute first. Do
   not let the PDF's confident "independently confirmed white space" language pull us into
   over-claiming.

5. The 0.995 versus 57 percent gap is a reviewer trap the PDF under-weights. ROC-AUC 0.995 is on
   controlled synthetic injections, the same synthetic-noise weakness the PDF criticizes CCA for. On
   real fabrications we flag 57 percent. A reviewer will notice we beat a baseline on exactly the axis
   where our own headline number is softest. The fix (lead with downstream repair, report both
   numbers, and treat structure-poor auditing as its own contribution) must be designed in, not bolted
   on. This is why Gap 3 is promoted in the unified pathway.

---

## 4. The reconciliation in one line

The mentor ladder and the PDF share the same endgame (self-healing multilingual KBs). They differ
only on the path. The unified pathway keeps the mentor ladder as the backbone, uses the PDF's
competitor map and two-paper split as the packaging, and promotes the PDF's Gap 3 (auditing
structure-poor entities) because the mentor's own RuleTrust signal is entity-independent and
therefore is the tool that attacks the 57 percent soft spot. See
[UNIFIED_PATHWAY.md](UNIFIED_PATHWAY.md).
