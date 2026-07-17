#!/bin/bash
# Phase 0: make the git repo the single source of truth for active code.
# Replaces the active pipeline files in ~/research_kg with symlinks into this repo.
# Data, venvs, checkpoints, and token caches stay in ~/research_kg (gitignored, unchanged).
# Idempotent: safe to re-run. Backs up any real (non-symlink) originals once.
set -e
REPO="/mnt/c/developer/research_ai/research_kg/mkgc-multilingual-inductive/wsl/research_kg"
WSL="$HOME/research_kg"
FILES="train_dbp5l_lora.py eval_dbp5l.py eval_dbp5l_anchors.py detector_experiment.py bootstrap_sig.py run_clean_retrain.sh run_baselines.sh run_seeds.sh run_seed777.sh README.md"

BK="$WSL/archive/pre_symlink_$(date +%Y-%m-%d)"
mkdir -p "$BK"
for f in $FILES; do
  if [ -e "$WSL/$f" ] && [ ! -L "$WSL/$f" ]; then cp "$WSL/$f" "$BK/$f"; fi
  rm -f "$WSL/$f"
  ln -s "$REPO/$f" "$WSL/$f"
done
echo "Symlinked $(echo $FILES | wc -w) files from repo -> $WSL"
