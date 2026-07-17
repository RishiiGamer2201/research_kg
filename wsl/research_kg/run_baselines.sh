#!/bin/bash
# W3 — external / encoder baselines on DBP-5L-Ind, using the SAME pipeline as the full model
# (identical data, split, negatives, eval protocol) so ONLY the encoder or loss changes.
# Run when the GPU is free (after the seed chain). Each run ~5-7h. Eval is separate (Claude runs it).
#
#   bash run_baselines.sh mbert-full    # mBERT + full method (CRR+HN+ml160) — isolates ENCODER vs BGE-M3
#   bash run_baselines.sh mbert-simkgc  # mBERT + InfoNCE, in-batch negs only — SimKGC-faithful recipe
#   bash run_baselines.sh xlmr-full     # XLM-R base + full method — 2nd encoder-ablation point (optional)
set -e
source /home/admin_wsl/research_kg/RAA-KGC/SimKGC/venv/bin/activate
cd /home/admin_wsl/research_kg
WHICH="${1:-mbert-full}"
# Baselines MUST use the same descriptions as the final model (clean, no LLM back-fill),
# else the comparison confounds encoder with description quality.
DESC=/home/admin_wsl/research_kg/DBP5L/processed/entity_descriptions_clean.json

case "$WHICH" in
  mbert-full)
    echo "=== mBERT + full method (encoder isolation vs BGE-M3) ==="
    CUDA_VISIBLE_DEVICES=0 python3 train_dbp5l_lora.py \
      --model-name bert-base-multilingual-cased \
      --desc-path "$DESC" \
      --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4 \
      --use-crr 1 --crr-rho 0.1 --hard-neg-k 7 --hard-neg-start-epoch 5 \
      --max-length 160 --lora-rank 16 --seed 42 \
      2>&1 | tee logs/baseline_mbert_full.log ;;
  mbert-simkgc)
    echo "=== mBERT + InfoNCE (SimKGC-faithful: in-batch negatives, no CRR, no hard-neg) ==="
    CUDA_VISIBLE_DEVICES=0 python3 train_dbp5l_lora.py \
      --model-name bert-base-multilingual-cased \
      --desc-path "$DESC" \
      --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4 \
      --use-crr 0 --hard-neg-k 0 \
      --max-length 160 --lora-rank 16 --seed 42 \
      2>&1 | tee logs/baseline_mbert_simkgc.log ;;
  xlmr-full)
    echo "=== XLM-R base + full method (encoder-ablation point) ==="
    CUDA_VISIBLE_DEVICES=0 python3 train_dbp5l_lora.py \
      --model-name xlm-roberta-base \
      --desc-path "$DESC" \
      --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4 \
      --use-crr 1 --crr-rho 0.1 --hard-neg-k 7 --hard-neg-start-epoch 5 \
      --max-length 160 --lora-rank 16 --seed 42 \
      2>&1 | tee logs/baseline_xlmr_full.log ;;
  *) echo "unknown: $WHICH"; exit 1 ;;
esac
echo "=== DONE $WHICH — tell Claude to eval the new checkpoint ==="
