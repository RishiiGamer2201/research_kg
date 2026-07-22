#!/bin/bash
# E3 screening: CRR WITHOUT hard negatives (--hard-neg-k 0), else IDENTICAL to B0 frozen protocol.
# fold0_seed13, seed 42. Isolates whether HN7 helps on v2. In-batch CRR only; NO HN cache path.
set -u
cd "$HOME/research_kg"
source RAA-KGC/SimKGC/venv/bin/activate
FOLD="$HOME/research_kg/DBP5L/ind_v2/folds/fold0_seed13"
VIEW="$HOME/research_kg/DBP5L/ind_v2/tracks/descriptions_v2_primary.json"
RESUME=""
if [ -n "${RESUME_CKPT:-}" ]; then
  [ -f "$RESUME_CKPT" ] || { echo "RESUME_CKPT not found: $RESUME_CKPT" >&2; exit 2; }
  RESUME="--resume $RESUME_CKPT"
fi
HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=0 python3 train_dbp5l_lora.py \
  $RESUME \
  --v2-fold "$FOLD" \
  --desc-path "$VIEW" \
  --reciprocal 1 \
  --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4 \
  --use-crr 1 --crr-rho 0.1 --hard-neg-k 0 \
  --max-length 160 --lora-rank 16 --seed 42
