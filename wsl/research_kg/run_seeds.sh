#!/bin/bash
# W1 — 3-seed chain of the locked paper-model config.
# ML is passed as arg 1 (128 if Run B wins G0, 160 if Run E wins). Default 128.
set -e
ML="${1:-128}"
source /home/admin_wsl/research_kg/RAA-KGC/SimKGC/venv/bin/activate
cd /home/admin_wsl/research_kg
echo "=== 3-seed chain @ max_length=$ML | started $(date) ==="
for seed in 42 123 777; do
  echo "### SEED $seed | $(date)"
  CUDA_VISIBLE_DEVICES=0 python3 train_dbp5l_lora.py \
    --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4 \
    --use-crr 1 --crr-rho 0.1 \
    --hard-neg-k 7 --hard-neg-start-epoch 5 \
    --max-length "$ML" --lora-rank 16 --seed "$seed" \
    2>&1 | tee "/home/admin_wsl/research_kg/logs/run_B_seed${seed}_ml${ML}.log"
done
echo "=== ALL 3 SEEDS DONE | $(date) ==="
