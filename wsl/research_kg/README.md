# research_kg (WSL): code, data, and models

This is the WSL working directory for the multilingual inductive KGC and self-healing KB project.
The documentation (story, architecture, results, plan, literature) lives in the Windows folder
`C:\developer\research_ai\research_kg\mkgc-multilingual-inductive\docs\`. This README covers only
the code and data here.

Environment: activate the virtualenv before running anything.
`source ~/research_kg/RAA-KGC/SimKGC/venv/bin/activate`

## Active pipeline (root)

Core scripts kept at root because the run wrappers call them by name and they import each other.

| File | What it does |
|---|---|
| `train_dbp5l_lora.py` | The trainer: BGE-M3 (or any encoder) + LoRA + CRR + hard negatives. Flags: `--desc-path`, `--resume`, `--seed`, `--model-name`, `--max-length`, `--lora-rank`. Saves `best_model.pt` and a full-state `last_checkpoint.pt` every epoch. |
| `eval_dbp5l.py` | Evaluation: filtered within-language and cross-lingual MRR / Hits@k. Auto-reads max_length from the checkpoint. Flags: `--checkpoint`, `--desc-path`, `--dump-ranks`, `--per-language`. |
| `eval_dbp5l_anchors.py` | Anchor-aware eval variant (imports `eval_dbp5l`); used for the cross-lingual anchor analysis. |
| `detector_experiment.py` | PIVOT: the contamination detector (text vs structure consistency with BGE-M3). ROC-AUC 0.995. |
| `bootstrap_sig.py` | Paired bootstrap + Wilcoxon significance test over `--dump-ranks` outputs. |

Run wrappers (each `cd`s here and activates the venv):

| Wrapper | Purpose |
|---|---|
| `run_clean_retrain.sh` | 3-seed retrain of the paper config on the clean descriptions. |
| `run_baselines.sh mbert-full\|mbert-simkgc\|xlmr-full` | Encoder baselines on the clean descriptions. |
| `run_seeds.sh [ml]` | 3-seed chain of the paper config. |
| `run_seed777.sh` | Just seed 777 (resume the interrupted chain). |

## scripts/

- `scripts/data_prep/` : build and fetch the data. `build_dbp5l_ind.py` (the split),
  `preprocess_dbp5l_ind.py`, `build_entity_descriptions.py`, `build_relation_names.py`,
  `fetch_wikipedia_abstracts.py`, `fetch_wikipedia_descriptions.py`,
  `generate_llm_descriptions.py`, `build_nollm_desc.py`, `build_clean_desc.py`. These use absolute
  paths, so run them from anywhere: `python3 scripts/data_prep/build_clean_desc.py`.
- `scripts/analysis/` : one-off analyses and checks. `ja_analysis.py` (token-length by language),
  `llm_spotcheck.py` (contamination audit sampling), `investigate_support.py`, `extract_final.py`,
  `extract_xl.py`, `check_*.py`, `multilingual_check.py`, `find_lora_targets.py`.

## Data, models, repos (do not move; paths are hardcoded)

| Path | What |
|---|---|
| `DBP5L/` | The dataset. `DBP5L/processed/` has train/valid/test json, `entity_descriptions*.json`, relation names. `DBP5L/ind/` the raw split. `DBP5L/checkpoints/` trained models. `DBP5L/token_cache/` cached tokenization (keyed by encoder and descriptions file). |
| `RAA-KGC/` | Contains the Python virtualenv at `RAA-KGC/SimKGC/venv`. Do not move. |
| `SimKGC_original/`, `CBLiP/`, `KEnS/`, `ALIGNKGC/`, `WN18RR/` | Cloned baselines and phase-0 datasets. |
| `logs/` | Run and eval logs. `logs/ranks/` per-triple rank dumps for significance. |
| `archive/` | Superseded scripts (old non-LoRA trainer, WN18RR phase-0, diagnostics) and completed one-off run scripts (Gate G1, final-eval passes). |

## Key facts

- Best substrate model: Run E config (BGE-M3, ml160, LoRA r16, CRR, HN K=7), 3-seed mean 26.51 MRR.
- Descriptions in use: `DBP5L/processed/entity_descriptions_clean.json` (no LLM back-fill).
  The contaminated original is `entity_descriptions.json`; the pre-back-fill state is
  `entity_descriptions_backup.json`.
- Detector result: `logs/detector_result.json` (ROC-AUC 0.995).
