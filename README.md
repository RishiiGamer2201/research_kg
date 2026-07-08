# Multilingual Inductive KGC and Self-Healing Knowledge Bases

Research project. Two connected parts:

- **Substrate (built and evaluated):** multilingual inductive knowledge graph completion. A
  BGE-M3 text bi-encoder, fine-tuned with LoRA, CRR loss, and hard negatives, completes facts
  about unseen entities across five languages (including low-resource Greek) on a single 16 GB
  GPU. Headline: 26.51 +/- 0.31 MRR (3 seeds), 18x over zero-shot; beats a 2019 mBERT baseline
  (24.08), most on Greek.
- **Self-healing knowledge bases (the new headline direction):** we found our own KB was ~70
  percent contaminated with confident AI-generated fabrications, concentrated in low-resource
  languages, and that the graph's own structure can detect and repair it. First detector result:
  ROC-AUC 0.995; repairing contamination improved Japanese completion by 1.95 MRR.

## Start here

- New to the project: read [docs/PROJECT_STORY_AND_PLAN.md](docs/PROJECT_STORY_AND_PLAN.md).
- Want the full doc map: [docs/README.md](docs/README.md).
- Want the technical depth: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Directory layout

```
README.md                     this file
TASK.md                       live task tracker for the substrate work
docs/                         all documentation (see docs/README.md)
  PROJECT_STORY_AND_PLAN.md   the narrative, for learning and presenting
  ARCHITECTURE.md             deep technical, with diagrams
  RESULTS_AND_INFERENCE.md    every result and inference
  IMPLEMENTATION_PLAN.md      execution plan and deadlines
  design/                     original-project design decisions
  pivot/                      the new-direction research and first result
  paper/                      substrate paper draft
  figures/                    interactive architecture figure
  paper_recreations/          recreations of related papers
Research/                     source papers, summaries, extracted figures
AuthorKit27/                  AAAI 2027 LaTeX kit (may be reused for KDD or SIGIR)
archive/                      historical logs (chat history, old journal, stale task copy)
```

Code, data, and models are in WSL at `~/research_kg/` (Ubuntu), not in this folder.

## Windows and WSL snapshots

This GitHub repo now keeps both sides of the work:

- The repository root is the Windows-side planning/documentation workspace.
- `wsl/` is a curated snapshot of the WSL training workspace at `/home/admin_wsl/research_kg`.

The WSL snapshot includes scripts, source files, compact results, S2DN reproduction logs, DBP-5L
artifacts, and legacy experiment code. It intentionally excludes virtual environments, checkpoints,
token caches, generated LMDB/subgraph caches, and large model binaries. See
[wsl/README.md](wsl/README.md) for details.

## Status and venue (as of 2026-07-07)

The substrate experiments are essentially complete. The direction is pivoting to the self-healing
knowledge base idea, targeting a better-fit A-star venue with more runway than AAAI-27: KDD 2027
Cycle 2 (historically around February 2027; KDD also has a Datasets and Benchmarks track) or
SIGIR 2027 (historically a late-January deadline; 2027 dates not yet posted). AAAI-27 Cycle-level
July deadlines are not the target for the pivot. See
[docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) and
[docs/pivot/](docs/pivot/) for details.
