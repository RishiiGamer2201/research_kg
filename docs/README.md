# Documentation Index

Everything about this project, in reading order. Start at the top.

## Read these first (the whole story)

| File | What it is | Read it to |
|---|---|---|
| [PROJECT_STORY_AND_PLAN.md](PROJECT_STORY_AND_PLAN.md) | The narrative, from fundamentals to the pivot | Learn and present the project |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Deep technical: every component and why, with two Mermaid diagrams | Answer any "why did you use X" question |
| [RESULTS_AND_INFERENCE.md](RESULTS_AND_INFERENCE.md) | Every experimental result and inference for the substrate | Cite exact numbers |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Execution plan, deadlines, reproducibility checklist | Know what is done and what is next |

## The pivot (the new research direction)

Folder: [pivot/](pivot/)

| File | What it is |
|---|---|
| [pivot/novel_directions_2026-07-05.md](pivot/novel_directions_2026-07-05.md) | The four candidate directions and the novelty check; the recommended self-healing idea |
| [pivot/multilingual_factuality_novelty_research_2026-07-05.md](pivot/multilingual_factuality_novelty_research_2026-07-05.md) | The alternative completion-before-RAG proposal (Direction B) and its literature |
| [pivot/trackB_pivot_brief.md](pivot/trackB_pivot_brief.md) | The earlier multilingual KG-RAG brief |
| [pivot/self_healing_detector_result_2026-07-07.md](pivot/self_healing_detector_result_2026-07-07.md) | First experiment of the pivot: the contamination detector (ROC-AUC 0.995) |
| [pivot/related_work.md](pivot/related_work.md) | CANONICAL literature map (SIGIR, KDD, WSDM, neighbours, 2024 to 2026): gap map, competitor matrix, venue positioning |
| [pivot/mentor_plan_research_2026-07-08.md](pivot/mentor_plan_research_2026-07-08.md) | Mentor ladder plan: S2DN/GOLD/LLM_sim paper summaries, verified S2DN targets, topic analysis |
| [pivot/IMPLEMENTATION_PLAN_S2DN_LADDER.md](pivot/IMPLEMENTATION_PLAN_S2DN_LADDER.md) | Execution plan with checkboxes: reproduce S2DN, RuleTrust-S2DN, multilingual, self-healing |
| pivot/archive/ | The two source drafts that were merged into related_work.md |

## Design decisions of the original project

Folder: [design/](design/)

| File | What it decides |
|---|---|
| [design/dataset_choice.md](design/dataset_choice.md) | Why DBP-5L |
| [design/skeleton.md](design/skeleton.md) | The overall architecture skeleton |
| [design/RAA_encoder_modernization.md](design/RAA_encoder_modernization.md) | Why BGE-M3 as the encoder |
| [design/ablation_plan.md](design/ablation_plan.md) | The planned ablation tables |
| [design/research_assessment_2026-07-03.md](design/research_assessment_2026-07-03.md) | Honest publishability assessment of the substrate paper |

## Supporting material

| Path | What it is |
|---|---|
| [paper/paper_draft.md](paper/paper_draft.md) | Working draft of the substrate paper |
| [figures/dbp5l-ind-architecture.html](figures/dbp5l-ind-architecture.html) | Interactive one-page architecture figure (substrate + self-healing panel) |
| [paper_recreations/](paper_recreations/) | Recreations of key related papers (KL-GMoE) |

## Where the code and data live

Code, data, and trained models are in WSL at `~/research_kg/` (Ubuntu), not in this Windows
documentation folder. Key scripts: `train_dbp5l_lora.py` (trainer, with resume support),
`eval_dbp5l.py` (evaluation), `detector_experiment.py` (contamination detector),
`build_clean_desc.py` (clean descriptions). Run logs are in `~/research_kg/logs/`.
