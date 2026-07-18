#!/bin/bash
# B0 — locked anchor baseline, DBP5L-Ind v2, frozen protocol (docs/PHASE2_BASELINE_MATRIX.md)
# fold0_seed13 (development/reporting fold), training seed 42.
#
# NO IMPLICIT RESUME. The previous version pointed at a checkpoint path the trainer never
# creates, so a killed run would have silently restarted from scratch under a new directory.
# Resuming is now explicit and guarded:
#   RESUME_CKPT=<path>  must be set, and resume_guard.sh must pass (code == launch commit),
#   otherwise use continue_run.sh to continue under a NEW run id.
set -u
cd "$HOME/research_kg"
source RAA-KGC/SimKGC/venv/bin/activate
FOLD="$HOME/research_kg/DBP5L/ind_v2/folds/fold0_seed13"
VIEW="$HOME/research_kg/DBP5L/ind_v2/tracks/descriptions_v2_primary.json"
LAUNCH_COMMIT="${LAUNCH_COMMIT:-d51630bc3ecf3c9c31b2ed64972e1b99821157f2}"

RESUME=""
if [ -n "${RESUME_CKPT:-}" ]; then
  [ -f "$RESUME_CKPT" ] || { echo "RESUME_CKPT not found: $RESUME_CKPT" >&2; exit 2; }
  if [ -z "${RESUME_RUN_DIR:-}" ]; then
    echo "RESUME_RUN_DIR must be set (the run dir being resumed) so the guard can check it" >&2
    exit 2
  fi
  bash scripts/baselines/resume_guard.sh "$RESUME_RUN_DIR" "$LAUNCH_COMMIT" || {
    echo "Refusing to resume under a different code state. Use continue_run.sh." >&2; exit 3; }
  RESUME="--resume $RESUME_CKPT"
fi

HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=0 python3 train_dbp5l_lora.py \
  $RESUME \
  --v2-fold "$FOLD" \
  --desc-path "$VIEW" \
  --reciprocal 1 \
  --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4 \
  --use-crr 1 --crr-rho 0.1 --hard-neg-k 7 --hard-neg-start-epoch 5 \
  --max-length 160 --lora-rank 16 --seed 42
