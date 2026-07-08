#!/usr/bin/env bash
set -euo pipefail

source /home/admin_wsl/research_kg/S2DN/venv_s2dn/bin/activate
cd /home/admin_wsl/research_kg/S2DN/SDN
CACHE=/home/admin_wsl/research_kg/S2DN/grail/data/WN18RR_v1/subgraphs_en_True_neg_1_hop_3

rm -rf "$CACHE"

python train.py \
  -d WN18RR_v1 \
  -e smoke_cpu_wn_v1 \
  --disable_cuda \
  --num_epochs 1 \
  --max_links 20 \
  --num_workers 0 \
  --eval_every 1 \
  --eval_every_iter 999999

rm -rf "$CACHE"
