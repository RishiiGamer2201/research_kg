#!/usr/bin/env bash
# Paired-seed sweep on fb237_v1: baseline and RuleTrust (mode=score) at the SAME seed, so the
# only difference between each pair is the rule term. This turns the high-variance single-seed
# comparison into a paired one and gives an error bar.
#
# Sequential (one run at a time; the GPU holds one S2DN run). Each run writes its own logs, so a
# crash mid-sweep keeps the completed runs. Reuses the subgraph cache and the rule cache; deletes
# neither. Paper hyperparameters throughout (lr 0.0005, dim 64, batch 32, hop 3).
#
# Usage: run_seed_sweep_fb237_v1.sh [seeds...]   default seeds: 1 2 3
set -euo pipefail

SEEDS=("$@")
if [[ ${#SEEDS[@]} -eq 0 ]]; then
  SEEDS=(1 2 3)
fi
for s in "${SEEDS[@]}"; do
  if ! [[ "$s" =~ ^[0-9]+$ ]]; then
    echo "seeds must be non-negative integers; got '$s'" >&2
    exit 2
  fi
done

DATASET="fb237_v1"
IND="fb237_v1_ind"
LOG_DIR="/home/admin_wsl/research_kg/logs/s2dn_reproduction"
source /home/admin_wsl/research_kg/S2DN/venv_s2dn_gpu_latest/bin/activate
cd /home/admin_wsl/research_kg/S2DN/SDN
mkdir -p "$LOG_DIR"

run_one() {
  # args: experiment_name log_prefix <extra train flags...>
  local exp="$1"; local prefix="$2"; shift 2
  echo "=== $(date) | START $exp ==="
  python train.py -d "$DATASET" -e "$exp" --gpu 0 --num_workers 4 \
    --batch_size 32 --lr 0.0005 --emb_dim 64 --rel_emb_dim 64 \
    --attn_rel_emb_dim 64 --hidden_size 64 --hop 3 "$@" \
    2>&1 | tee "${LOG_DIR}/${prefix}_train_gpu.log"
  python test_ranking.py -d "$IND" -e "$exp" \
    2>&1 | tee "${LOG_DIR}/${prefix}_test_gpu.log"
  echo "=== $(date) | DONE $exp ==="
}

for s in "${SEEDS[@]}"; do
  echo "######## SEED $s ########"
  run_one "sdn_fb_v1_paper_seed${s}_gpu" "fb237_v1_paper_seed${s}" \
    --seed "$s"
  run_one "sdn_fb_v1_ruletrust_seed${s}_gpu" "fb237_v1_ruletrust_seed${s}" \
    --seed "$s" --use-rule-trust --rule-trust-mode score \
    --rule-conf-threshold 0.1 --rule-min-support 2
done

echo "######## SWEEP COMPLETE $(date) ########"
