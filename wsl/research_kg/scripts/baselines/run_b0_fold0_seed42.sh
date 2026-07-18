#!/bin/bash
# B0 — locked anchor baseline, DBP5L-Ind v2, frozen protocol (docs/PHASE2_BASELINE_MATRIX.md)
# fold0_seed13 (development/reporting fold), training seed 42.
cd "$HOME/research_kg"
source RAA-KGC/SimKGC/venv/bin/activate
FOLD="$HOME/research_kg/DBP5L/ind_v2/folds/fold0_seed13"
VIEW="$HOME/research_kg/DBP5L/ind_v2/tracks/descriptions_v2_primary.json"
RD="$HOME/research_kg/DBP5L/checkpoints/B0_v2_fold0_seed42"

# resume in place if a previous attempt left a checkpoint (idempotent restart)
RESUME=""
[ -f "$RD/last_checkpoint.pt" ] && RESUME="--resume $RD/last_checkpoint.pt"

HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=0 python3 train_dbp5l_lora.py \
  $RESUME \
  --v2-fold "$FOLD" \
  --desc-path "$VIEW" \
  --reciprocal 1 \
  --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4 \
  --use-crr 1 --crr-rho 0.1 --hard-neg-k 7 --hard-neg-start-epoch 5 \
  --max-length 160 --lora-rank 16 --seed 42
