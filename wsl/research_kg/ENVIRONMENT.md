# Environment report (Phase 0 / P0.1)

Captured 2026-07-17 from the live WSL tree. This repo (`wsl/research_kg/`) is the
committed mirror of `\\wsl$\Ubuntu\home\admin_wsl\research_kg` (not itself a git repo).

## Data/checkpoint root resolution
Root code no longer hardcodes `~/research_kg`. It reads env var **`RESEARCH_KG_ROOT`**,
defaulting to `~/research_kg` (old behavior). To run from a clone with data elsewhere:

```bash
export RESEARCH_KG_ROOT=/path/to/research_kg   # dir containing DBP5L/, logs/
```

Applies to: `train_dbp5l_lora.py`, `eval_dbp5l.py`, `eval_dbp5l_anchors.py`, `detector_experiment.py`.

## Text branch (BGE-M3 / LoRA / mBERT / XLM-R)
- venv: `~/research_kg/RAA-KGC/SimKGC/venv`
- Python 3.10.20
- torch 2.11.0+cu128, CUDA 12.8, transformers 5.12.1, peft 0.19.1
- numpy 2.2.6, scipy 1.15.3, scikit-learn 1.7.2, torch-geometric 2.8.0
- Full freeze: `requirements.simkgc-venv.txt` (91 pkgs)
- NOTE: `FlagEmbedding` and `dgl` are NOT installed here. BGE-M3 loads via transformers
  `AutoModel` (XLM-R backbone), so FlagEmbedding is not needed for the LoRA trainer.

## Structural branch (S2DN)
- Separate, divergent venvs (§4.10 "multiple divergent environments"):
  `S2DN/venv_s2dn`, `S2DN/venv_s2dn_gpu`, `S2DN/venv_s2dn_gpu_latest`. `dgl` lives here.
- `CBLiP/IEP/venv` is a third baseline env.
- TODO(P0.5): freeze the canonical S2DN venv and record which of the three is authoritative.

## Hardware
- GPU: NVIDIA GeForce RTX 5070 Ti, 16 GB, driver 610.74.
- (96 GB GPU expected later per proposal §3.5 for structural experiments.)
