#!/bin/bash
# Resume the interrupted 3-seed chain: seeds 42 and 123 are DONE, only 777 remains.
# Run this after PC restart. NOTE: no true resume exists, so 777 trains from epoch 0.
# (Do NOT use run_seeds.sh here; that would re-run 42 and 123 as well.)
source /home/admin_wsl/research_kg/RAA-KGC/SimKGC/venv/bin/activate
cd /home/admin_wsl/research_kg
echo "=== seed 777 (ml=160), started $(date) ==="
CUDA_VISIBLE_DEVICES=0 python3 train_dbp5l_lora.py \
  --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4 \
  --use-crr 1 --crr-rho 0.1 --hard-neg-k 7 --hard-neg-start-epoch 5 \
  --max-length 160 --lora-rank 16 --seed 777 \
  2>&1 | tee logs/run_B_seed777_ml160.log
echo "=== seed 777 done $(date); tell Claude to eval and finish the significance test ==="
