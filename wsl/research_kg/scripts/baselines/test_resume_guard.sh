#!/bin/bash
cd "$HOME/research_kg"
REPO=/mnt/c/developer/research_ai/research_kg/mkgc-multilingual-inductive
G=scripts/baselines/resume_guard.sh
RD=DBP5L/ind_v2/audits/training/B0-RUN-002
LAUNCH=d51630bc3ecf3c9c31b2ed64972e1b99821157f2
fails=0
ck(){ [ "$2" = "$3" ] && echo "PASS $1" || { echo "FAIL $1 (got $2 want $3)"; fails=$((fails+1)); }; }

bash $G "$RD" "$LAUNCH" >/dev/null 2>&1; ck "refuse under newer code" "$?" "1"
HEAD_NOW=$(git -C $REPO rev-parse HEAD)
bash $G "$RD" "$HEAD_NOW" >/dev/null 2>&1; R=$?
# tree may be dirty -> also refused; accept 1 (dirty) or 0 (clean)
[ "$R" = "0" ] || [ "$R" = "1" ] && echo "PASS matching-commit path returns $R (0 clean / 1 dirty)" || { echo "FAIL matching"; fails=$((fails+1)); }
bash $G /nonexistent "$LAUNCH" >/dev/null 2>&1; ck "malformed run dir" "$?" "2"

# run script must refuse to resume when guard fails
RESUME_CKPT="$HOME/research_kg/DBP5L/checkpoints/bgem3_lora_dbp5l_20260718_0840_crr_hn7_r16/last_checkpoint.pt"
if [ -f "$RESUME_CKPT" ]; then
  RESUME_CKPT="$RESUME_CKPT" RESUME_RUN_DIR="$RD" bash run_b0_fold0_seed42.sh >/dev/null 2>&1
  ck "run script refuses guarded resume" "$?" "3"
else
  echo "SKIP run-script test (no checkpoint yet)"
fi
[ $fails -eq 0 ] && echo "resume guard self-test OK" || echo "resume guard self-test FAILED ($fails)"
