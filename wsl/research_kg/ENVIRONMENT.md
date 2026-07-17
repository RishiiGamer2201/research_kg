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

## Code source-of-truth workflow (Phase 0)
The git repo is canonical. The live WSL runner uses **symlinks** into it, so editing a
repo file changes what actually runs — no copy step, no drift.
- One-time / idempotent setup: `bash setup_wsl_symlinks.sh` (from repo copy, run in WSL).
- Symlinks: `~/research_kg/{train_dbp5l_lora,eval_dbp5l,eval_dbp5l_anchors,detector_experiment,bootstrap_sig}.py`
  + run wrappers + README → `/mnt/c/.../wsl/research_kg/`.
- Data/venvs/checkpoints/token_cache stay in `~/research_kg` (gitignored).
- Verified: symlinked modules import in the venv and resolve data via default `RESEARCH_KG_ROOT`.

## Text branch (BGE-M3 / LoRA / mBERT / XLM-R)
- venv: `~/research_kg/RAA-KGC/SimKGC/venv`
- Python 3.10.20
- torch 2.11.0+cu128, CUDA 12.8, transformers 5.12.1, peft 0.19.1
- numpy 2.2.6, scipy 1.15.3, scikit-learn 1.7.2, torch-geometric 2.8.0
- Full freeze: `requirements.simkgc-venv.txt` (91 pkgs)
- NOTE: `FlagEmbedding` and `dgl` are NOT installed here. BGE-M3 loads via transformers
  `AutoModel` (XLM-R backbone), so FlagEmbedding is not needed for the LoRA trainer.

## Structural branch (S2DN)
- **Canonical venv: `S2DN/venv_s2dn_gpu_latest`** (frozen P0.5). torch 2.11.0+cu128,
  dgl 2.4.0+cu121, numpy 2.2.6, networkx 3.4.2, lmdb 2.2.1, torchmetrics 1.9.0.
  Full freeze: `requirements.s2dn-venv.txt` (66 pkgs).
- Superseded/divergent (do not use): `S2DN/venv_s2dn`, `S2DN/venv_s2dn_gpu`. `CBLiP/IEP/venv` is a separate baseline env.
- Smoke validated 2026-07-17 (R-022): `python train.py -d fb237_v1 -e smoke_gpu_fb237_v1 --gpu 0
  --num_epochs 1 --max_links 20 --hop 3 --emb_dim 64` → subgraph extraction + 1 epoch on cuda,
  effective hyperparams logged, S2DN_SMOKE_DONE. Full fb237_v1 repro is R-013 (MRR 53.13, ~4.8h).
- Run S2DN from `S2DN/SDN/` (`cd` there; the paper-split wrapper is `scripts/run_fb237_paper_split_gpu.sh`).

## Hardware
- GPU: NVIDIA GeForce RTX 5070 Ti, 16 GB, driver 610.74.
- (96 GB GPU expected later per proposal §3.5 for structural experiments.)
