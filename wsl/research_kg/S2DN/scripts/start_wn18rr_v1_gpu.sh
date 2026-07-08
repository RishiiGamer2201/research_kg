#!/usr/bin/env bash
set -euo pipefail

cd /home/admin_wsl/research_kg/S2DN
mkdir -p /home/admin_wsl/research_kg/logs/s2dn_reproduction

nohup ./scripts/run_wn18rr_v1_gpu.sh \
  > /home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v1_gpu_nohup.log \
  2>&1 &

echo "$!"
