#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <wn18rr|fb237|nell> <1|2|3|4>" >&2
  exit 2
fi

FAMILY="$1"
SPLIT="$2"

case "$FAMILY" in
  wn18rr)
    DATASET="WN18RR_v${SPLIT}"
    EXPERIMENT="sdn_wn_v${SPLIT}_gpu"
    LOG_PREFIX="wn18rr_v${SPLIT}"
    ;;
  fb237)
    DATASET="fb237_v${SPLIT}"
    EXPERIMENT="sdn_fb_v${SPLIT}_gpu"
    LOG_PREFIX="fb237_v${SPLIT}"
    ;;
  nell)
    DATASET="nell_v${SPLIT}"
    EXPERIMENT="sdn_nell_v${SPLIT}_gpu"
    LOG_PREFIX="nell_v${SPLIT}"
    ;;
  *)
    echo "Unknown family: ${FAMILY}" >&2
    exit 2
    ;;
esac

IND_DATASET="${DATASET}_ind"
LOG_DIR="/home/admin_wsl/research_kg/logs/s2dn_reproduction"
CACHE="/home/admin_wsl/research_kg/S2DN/grail/data/${DATASET}/subgraphs_en_True_neg_1_hop_3"

source /home/admin_wsl/research_kg/S2DN/venv_s2dn_gpu_latest/bin/activate
cd /home/admin_wsl/research_kg/S2DN/SDN
mkdir -p "$LOG_DIR"

echo "Removing any existing ${DATASET} subgraph cache so this run uses the full dataset."
rm -rf "$CACHE"

python train.py \
  -d "$DATASET" \
  -e "$EXPERIMENT" \
  --gpu 0 \
  --num_workers 4 \
  2>&1 | tee "${LOG_DIR}/${LOG_PREFIX}_train_gpu.log"

python test_ranking.py \
  -d "$IND_DATASET" \
  -e "$EXPERIMENT" \
  2>&1 | tee "${LOG_DIR}/${LOG_PREFIX}_test_gpu.log"
