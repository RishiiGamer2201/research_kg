#!/usr/bin/env bash
# RuleTrust-S2DN, score-level neurosymbolic fusion, on FB15k-237.
#
# Paper hyperparameters (lr 0.0005, dim 64, hop 3) so the run is directly comparable to the
# reproduced baseline `sdn_fb_v${SPLIT}_paper_gpu`. The only difference is --use-rule-trust.
#
# Deliberately does NOT delete the subgraph cache: fb237_v1's cache is valid and rebuilding
# it costs about an hour. The rule cache (ruletrust_rules_v2.json) is mined on first use.
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: $0 <1|2|3|4> [batch_size] [mode: score|adjacency|both]" >&2
  exit 2
fi

SPLIT="$1"
if [[ "$SPLIT" != "1" && "$SPLIT" != "2" && "$SPLIT" != "3" && "$SPLIT" != "4" ]]; then
  echo "Split must be one of 1, 2, 3, 4" >&2
  exit 2
fi

BATCH="${2:-32}"
if ! [[ "$BATCH" =~ ^[0-9]+$ ]]; then
  echo "batch_size must be a positive integer" >&2
  exit 2
fi

MODE="${3:-score}"
if [[ "$MODE" != "score" && "$MODE" != "adjacency" && "$MODE" != "both" ]]; then
  echo "mode must be one of score, adjacency, both" >&2
  exit 2
fi

DATASET="fb237_v${SPLIT}"
IND_DATASET="${DATASET}_ind"
SUFFIX=""
[[ "$BATCH" != "32" ]] && SUFFIX="${SUFFIX}_bs${BATCH}"
[[ "$MODE" != "score" ]] && SUFFIX="${SUFFIX}_${MODE}"
EXPERIMENT="sdn_fb_v${SPLIT}_ruletrust${SUFFIX}_gpu"
LOG_PREFIX="fb237_v${SPLIT}_ruletrust${SUFFIX}"
LOG_DIR="/home/admin_wsl/research_kg/logs/s2dn_reproduction"

source /home/admin_wsl/research_kg/S2DN/venv_s2dn_gpu_latest/bin/activate
cd /home/admin_wsl/research_kg/S2DN/SDN
mkdir -p "$LOG_DIR"

echo "RuleTrust-S2DN on ${DATASET}: paper params (lr 0.0005, dim 64, hop 3), batch ${BATCH}, mode ${MODE}."
echo "Baseline for comparison: sdn_fb_v${SPLIT}_paper_gpu"
echo "Reusing existing subgraph cache (not deleting it)."

python train.py \
  -d "$DATASET" \
  -e "$EXPERIMENT" \
  --gpu 0 \
  --num_workers 4 \
  --batch_size "$BATCH" \
  --lr 0.0005 \
  --emb_dim 64 \
  --rel_emb_dim 64 \
  --attn_rel_emb_dim 64 \
  --hidden_size 64 \
  --hop 3 \
  --use-rule-trust \
  --rule-trust-mode "$MODE" \
  --rule-conf-threshold 0.1 \
  --rule-min-support 2 \
  2>&1 | tee "${LOG_DIR}/${LOG_PREFIX}_train_gpu.log"

python test_ranking.py \
  -d "$IND_DATASET" \
  -e "$EXPERIMENT" \
  2>&1 | tee "${LOG_DIR}/${LOG_PREFIX}_test_gpu.log"
