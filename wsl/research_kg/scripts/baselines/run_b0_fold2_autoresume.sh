#!/bin/bash
# Auto-resume wrapper for fold2. Survives intermittent WSL2 cudaErrorUnknown transients by
# relaunching, but ONLY while the checkpoint keeps advancing — a stall (same epoch twice)
# means a real fault, so we stop. Operational only: no training-code/hash/protocol change.
set -u
cd "$HOME/research_kg"
source RAA-KGC/SimKGC/venv/bin/activate          # so epoch_of has torch
CKPT="$HOME/research_kg/DBP5L/checkpoints/bgem3_lora_dbp5l_20260720_0915_crr_hn7_r16/last_checkpoint.pt"
epoch_of(){ python3 -c "import torch;print(torch.load('$CKPT',map_location='cpu').get('epoch',0))" 2>/dev/null || echo -1; }
MAX=12; prev=-1
for i in $(seq 1 $MAX); do
  cur=$(epoch_of)
  echo "[autoresume] attempt $i/$MAX — checkpoint at epoch $cur"
  if [ "$cur" -ge 30 ]; then echo "[autoresume] reached 30 epochs, done"; exit 0; fi
  if [ "$i" -gt 1 ] && [ "$cur" -le "$prev" ]; then
    echo "[autoresume] checkpoint did NOT advance ($prev -> $cur): real fault, not transient. Stopping." >&2
    exit 3
  fi
  prev=$cur
  bash "$HOME/research_kg/run_b0_fold2_resume.sh" && { echo "[autoresume] training exited 0"; exit 0; }
  echo "[autoresume] crash (exit $?); relaunching after 20s"; sleep 20
done
echo "[autoresume] exhausted $MAX attempts" >&2; exit 4
