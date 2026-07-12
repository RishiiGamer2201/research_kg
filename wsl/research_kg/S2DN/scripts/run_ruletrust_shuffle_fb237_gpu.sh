#!/usr/bin/env bash
# Rules-shuffled control for RuleTrust-S2DN on FB15k-237.
#
# Identical to run_ruletrust_fb237_gpu.sh (paper params, mode=score) except it adds
# --rule-shuffle, which deranges mined rule bodies onto WRONG head relations. Verified
# offline (diag_rule_inductive.py --shuffle): this drives target-pair rule support from
# 36.1 percent to 0 percent and rule-only AUC from 0.68 to 0.50. If the real run's Hits@10
# gain survives here, it was noise regularisation, not symbolic evidence.
#
# Reuses the subgraph cache (does not delete it).
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: $0 <1|2|3|4> [batch_size] [shuffle_seed]" >&2
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

SEED="${3:-0}"
if ! [[ "$SEED" =~ ^[0-9]+$ ]]; then
  echo "shuffle_seed must be a non-negative integer" >&2
  exit 2
fi

DATASET="fb237_v${SPLIT}"
IND_DATASET="${DATASET}_ind"
SUFFIX=""
[[ "$BATCH" != "32" ]] && SUFFIX="${SUFFIX}_bs${BATCH}"
EXPERIMENT="sdn_fb_v${SPLIT}_ruletrust_shuffle${SEED}${SUFFIX}_gpu"
LOG_PREFIX="fb237_v${SPLIT}_ruletrust_shuffle${SEED}${SUFFIX}"
LOG_DIR="/home/admin_wsl/research_kg/logs/s2dn_reproduction"

source /home/admin_wsl/research_kg/S2DN/venv_s2dn_gpu_latest/bin/activate
cd /home/admin_wsl/research_kg/S2DN/SDN
mkdir -p "$LOG_DIR"

echo "SHUFFLE CONTROL on ${DATASET}: paper params, mode=score, --rule-shuffle seed ${SEED}, batch ${BATCH}."
echo "Compare against real run sdn_fb_v${SPLIT}_ruletrust_gpu and baseline sdn_fb_v${SPLIT}_paper_gpu."
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
  --rule-trust-mode score \
  --rule-conf-threshold 0.1 \
  --rule-min-support 2 \
  --rule-shuffle \
  --rule-shuffle-seed "$SEED" \
  2>&1 | tee "${LOG_DIR}/${LOG_PREFIX}_train_gpu.log"

python test_ranking.py \
  -d "$IND_DATASET" \
  -e "$EXPERIMENT" \
  2>&1 | tee "${LOG_DIR}/${LOG_PREFIX}_test_gpu.log"
