#!/usr/bin/env bash
set -euo pipefail

source /home/admin_wsl/research_kg/S2DN/venv_s2dn_gpu_latest/bin/activate
cd /home/admin_wsl/research_kg/S2DN/SDN
mkdir -p /home/admin_wsl/research_kg/logs/s2dn_reproduction

CACHE=/home/admin_wsl/research_kg/S2DN/grail/data/WN18RR_v1/subgraphs_en_True_neg_1_hop_3

echo "Removing any existing WN18RR_v1 subgraph cache so this run uses the full dataset."
rm -rf "$CACHE"

python train.py \
  -d WN18RR_v1 \
  -e sdn_wn_v1_gpu \
  --gpu 0 \
  --num_workers 4 \
  2>&1 | tee /home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v1_train_gpu.log

python test_ranking.py \
  -d WN18RR_v1_ind \
  -e sdn_wn_v1_gpu \
  2>&1 | tee /home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v1_test_gpu.log
