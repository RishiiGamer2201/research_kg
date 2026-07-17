#!/bin/bash
# Option (b): retrain the paper config (BGE-M3, ml160, r16, CRR, HN K=7) on the CLEAN
# descriptions (no unverifiable English back-fill for EL/JA), 3 seeds.
# Prereq: entity_descriptions_clean.json exists (built by scripts/data_prep/build_clean_desc.py).
# Each seed ~5h; ~15h total. Run when the GPU is free (after the mBERT baseline).
set -e
DESC=/home/admin_wsl/research_kg/DBP5L/processed/entity_descriptions_clean.json
[ -f "$DESC" ] || { echo "ERROR: $DESC not found. Run scripts/data_prep/build_clean_desc.py first."; exit 1; }
source /home/admin_wsl/research_kg/RAA-KGC/SimKGC/venv/bin/activate
cd /home/admin_wsl/research_kg
for seed in 42 123 777; do
  echo "=== CLEAN retrain seed $seed | $(date) ==="
  CUDA_VISIBLE_DEVICES=0 python3 train_dbp5l_lora.py \
    --desc-path "$DESC" \
    --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4 \
    --use-crr 1 --crr-rho 0.1 --hard-neg-k 7 --hard-neg-start-epoch 5 \
    --max-length 160 --lora-rank 16 --seed "$seed" \
    2>&1 | tee "logs/run_clean_seed${seed}_ml160.log"
done
echo "=== ALL 3 CLEAN SEEDS DONE | $(date); tell Claude to eval them ==="
