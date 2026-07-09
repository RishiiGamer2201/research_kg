#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <1|2|3|4>" >&2
  exit 2
fi

SPLIT="$1"
if [[ "$SPLIT" != "1" && "$SPLIT" != "2" && "$SPLIT" != "3" && "$SPLIT" != "4" ]]; then
  echo "Split must be one of 1, 2, 3, 4" >&2
  exit 2
fi

DATASET="fb237_v${SPLIT}"
IND_DATASET="${DATASET}_ind"
EXPERIMENT="sdn_fb_v${SPLIT}_paper_gpu"
LOG_PREFIX="fb237_v${SPLIT}_paper"
LOG_DIR="/home/admin_wsl/research_kg/logs/s2dn_reproduction"
CACHE="/home/admin_wsl/research_kg/S2DN/grail/data/${DATASET}/subgraphs_en_True_neg_1_hop_3"

source /home/admin_wsl/research_kg/S2DN/venv_s2dn_gpu_latest/bin/activate
cd /home/admin_wsl/research_kg/S2DN/SDN
mkdir -p "$LOG_DIR"

echo "Running FB15k-237 v${SPLIT} with paper hyperparameters: dim=64, lr=0.0005, batch_size=32, hop=3."
echo "Removing any existing ${DATASET} subgraph cache so this run uses the full dataset."
rm -rf "$CACHE"

python train.py \
  -d "$DATASET" \
  -e "$EXPERIMENT" \
  --gpu 0 \
  --num_workers 4 \
  --batch_size 32 \
  --lr 0.0005 \
  --emb_dim 64 \
  --rel_emb_dim 64 \
  --attn_rel_emb_dim 64 \
  --hidden_size 64 \
  --hop 3 \
  2>&1 | tee "${LOG_DIR}/${LOG_PREFIX}_train_gpu.log"

python test_ranking.py \
  -d "$IND_DATASET" \
  -e "$EXPERIMENT" \
  2>&1 | tee "${LOG_DIR}/${LOG_PREFIX}_test_gpu.log"
