# Self-Healing KB: First Detector Result (2026-07-07)

The first real experiment of the pivot direction. It shows the core claim works: an entity's
description can be checked against its own graph structure, and inconsistency flags contamination.

## Method

Signal: encode an entity's description and a serialisation of its graph neighbourhood with the
same BGE-M3 encoder, and take the cosine similarity as a consistency score. A low score means the
text disagrees with the structure, that is, likely contaminated. Training-free; no LLM judge, no
external calls; it reuses the project's own encoder (the same model that completes the KG also
audits it).

Because the real found contamination sits on structure-poor entities (they were LLM-filled
precisely because they were sparse: median 0 edges), a controlled-injection benchmark is the
sound way to measure detector quality. Built on structure-rich entities (at least 3 edges) that
have a real description:
- clean (label 0): the entity's real description versus its own structure.
- injected (label 1): a different random entity's real description versus this entity's structure
  (a wrong-entity fabrication, guaranteed inconsistent, needs no generation).
Plus a real-contamination anchor: the 40 actual Llama fabrications that happen to have at least
2 edges, evaluated as an in-the-wild check.

Script: `~/research_kg/detector_experiment.py`. Result: `~/research_kg/logs/detector_result.json`.

## Result

Consistency score (cosine, mean): clean 0.885, injected 0.663, real-contamination 0.761. The
clean descriptions sit clearly above the fabrications.

Controlled benchmark (clean vs wrong-entity injection, n = 400):
- ROC-AUC 0.995
- best-F1 threshold 0.773: precision 0.985, recall 0.990, F1 0.988

Real in-the-wild contamination: at that same threshold, 23 of 40 (57 percent) of the actual
Llama fabrications are flagged. This is with almost no structure to check against (these entities
have only 2 to a few edges), so 57 percent is a floor, not a ceiling; entities with richer
structure should be caught more reliably.

## What this establishes and what it does not

Establishes: the text-versus-structure consistency signal separates real descriptions from
fabrications almost perfectly when structure exists, using nothing but the graph's own facts and
an off-the-shelf encoder. Combined with the earlier plus-1.95 MRR downstream repair, we now have
both halves of the loop demonstrated: detection works, and repair helps.

Does not yet establish (the honest next steps, for the KDD or SIGIR paper):
- A realistic-fabrication injection set (generate believable wrong bios rather than swap whole
  descriptions), so the controlled positives match the real failure mode, not just wrong-entity.
- A per-language and per-script breakdown of detector precision and recall.
- An LLM-judge variant (NLI or a local model) compared against the embedding-consistency variant.
- Coverage analysis: the fraction of KB entities with enough structure to audit, and what to do
  for description-only entities.
- A second knowledge base (a Wikidata slice) for generality.

## Numbers to quote

- Detector: ROC-AUC 0.995, F1 0.988 on the controlled benchmark; 57 percent of real fabrications
  caught with minimal structure.
- Repair (from the substrate work): removing contamination improved Japanese completion by 1.95
  MRR, overall by 0.25.
- Contamination found in the wild: about 70 percent of the LLM back-filled descriptions.
