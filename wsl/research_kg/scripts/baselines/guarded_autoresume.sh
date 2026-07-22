#!/bin/bash
# Guarded auto-resume for screening runs. Watches an ALREADY-RUNNING training job and,
# on crash, resumes it under a strict policy — never a blind retry loop.
#
# Policy (all enforced below; numbers are the requirement they satisfy):
#   1. Resume only from a last_checkpoint.pt that carries optimizer+scheduler+epoch state.
#   2. Require HEAD == launch commit, tracked-clean tree, matching protocol args, exclusive GPU.
#   3. Each resume runs under a NEW continuation run id linked to the failed segment.
#   4. At most MAX_RESUMES resumes, with backoff.
#   5. Auto-resume ONLY verified-transient failures (SIGILL / cudaErrorUnknown).
#   6. Never auto-resume OOM/SIGABRT unless a foreign GPU compute-app proves external collision.
#   7. Stop if the SAME failure repeats at the SAME checkpoint epoch.
#   8. Record every segment's wall seconds; aggregate is the SUM of segments, never
#      one segment's wall divided by the epoch count.
#
# Required env:
#   RUN_SCRIPT     run script that honors RESUME_CKPT (e.g. run_e1_infonce_fold0.sh)
#   CKPT_DIR       dir holding last_checkpoint.pt
#   LAUNCH_COMMIT  40-char sha the run was launched at
#   RUN_ID_BASE    audit id of the first segment (e.g. E1-INFONCE-fold0)
#   WATCH_PID      pid of the currently-running training process to watch
#   LOGF           training log file (appended to on resume)
#   EXPECT_PROTO   python dict-literal of required args, e.g. "{'use_crr':0,'hard_neg_k':7}"
# Optional: TARGET_EPOCHS (default 30), MAX_RESUMES (default 2), REPO, SETTLE (default 8)
set -u
cd "$HOME/research_kg"
source RAA-KGC/SimKGC/venv/bin/activate

: "${RUN_SCRIPT:?}"; : "${CKPT_DIR:?}"; : "${LAUNCH_COMMIT:?}"; : "${RUN_ID_BASE:?}"
: "${WATCH_PID:?}"; : "${LOGF:?}"; : "${EXPECT_PROTO:?}"
REPO="${REPO:-/mnt/c/developer/research_ai/research_kg/mkgc-multilingual-inductive}"
TARGET_EPOCHS="${TARGET_EPOCHS:-30}"; MAX_RESUMES="${MAX_RESUMES:-2}"; SETTLE="${SETTLE:-8}"
AUDIT="DBP5L/ind_v2/audits/training"
SEG="$AUDIT/$RUN_ID_BASE/segments.tsv"
CKPT="$CKPT_DIR/last_checkpoint.pt"
# Orchestration scripts live (partly) OUTSIDE the git repo, so they are pinned by SHA-256,
# not by the commit. The launcher (RUN_SCRIPT) is WSL-only; the wrapper is untracked-in-repo.
WRAPPER_FILE="${WRAPPER_FILE:-$HOME/research_kg/scripts/baselines/guarded_autoresume.sh}"
LAUNCHER_FILE="$HOME/research_kg/$RUN_SCRIPT"
ORCH="$AUDIT/$RUN_ID_BASE/orchestration_manifest.tsv"

log(){ echo "[guard $(date -u +%H:%M:%SZ)] $*"; }
sha(){ sha256sum "$1" 2>/dev/null | awk '{print $1}'; }

record_orchestration(){
  mkdir -p "$(dirname "$ORCH")"
  { printf 'role\tpath\tsha256\n'
    printf 'wrapper\t%s\t%s\n'  "$WRAPPER_FILE"  "$(sha "$WRAPPER_FILE")"
    printf 'launcher\t%s\t%s\n' "$LAUNCHER_FILE" "$(sha "$LAUNCHER_FILE")"
    printf '#recorded_utc\t%s\tlaunch_commit=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$LAUNCH_COMMIT"
  } > "$ORCH"
  log "orchestration hashes pinned -> $ORCH"
  grep -E '^(wrapper|launcher)' "$ORCH" | while IFS=$'\t' read -r r p h; do log "  $r ${h:0:12} $p"; done
}
orch_line(){ grep -E "^$1"$'\t' "$ORCH" | head -1; }  # for embedding in continuation records

verify_orchestration(){  # reverify pinned hashes immediately before a resume
  local ok=1 role path want got
  while IFS=$'\t' read -r role path want; do
    case "$role" in wrapper|launcher) ;; *) continue ;; esac
    got="$(sha "$path")"
    [ "$got" = "$want" ] || { log "REFUSE: $role SHA drift ($path): want ${want:0:12} got ${got:0:12}"; ok=0; }
  done < "$ORCH"
  [ "$ok" -eq 1 ]
}

epoch_of(){ python3 - "$CKPT" <<'PY' 2>/dev/null || echo -1
import torch,sys
print(torch.load(sys.argv[1],map_location='cpu').get('epoch',-1))
PY
}

record_seg(){ # run_id start_utc end_utc wall_s ep_start ep_end status
  mkdir -p "$(dirname "$SEG")"
  [ -f "$SEG" ] || printf 'run_id\tstart_utc\tend_utc\twall_s\tep_start\tep_end\tstatus\n' > "$SEG"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@" >> "$SEG"
  local total; total=$(awk -F'\t' 'NR>1{s+=$4} END{print s+0}' "$SEG")
  log "segment recorded ($7); aggregate wall so far = ${total}s across $(($(wc -l < "$SEG")-1)) segment(s)"
}

# rule 1 + protocol part of rule 2
verify_checkpoint(){
  python3 - "$CKPT" "$EXPECT_PROTO" <<'PY'
import torch,sys,ast
ck=torch.load(sys.argv[1],map_location='cpu')
need=['optimizer_state_dict','scheduler_state_dict','epoch','model_state_dict']
miss=[k for k in need if k not in ck]
assert not miss, f"checkpoint missing full-state keys: {miss}"
exp=ast.literal_eval(sys.argv[2]); args=ck.get('args',{}) or {}
bad={k:(args.get(k),v) for k,v in exp.items() if args.get(k)!=v}
assert not bad, f"protocol mismatch (ckpt vs expected): {bad}"
print("ckpt-verified epoch", ck['epoch'])
PY
}

# any GPU compute-app is foreign here (our training is already dead)
foreign_gpu(){ nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>/dev/null | grep -qE '[0-9]+'; }

# allowlisted untracked locations: run outputs, logs, caches, temp, checkpoints, audits.
# Anything code/config-like OUTSIDE these (and not a hash-pinned orchestration script) is refused.
ALLOW_UNTRACKED='^(logs/|tmp/|tools/|wsl/research_kg/logs/|DBP5L/checkpoints/|DBP5L/ind_v2/audits/|.*/__pycache__/)'
CODE_LIKE='\.(py|sh|ya?ml|toml|cfg|ini|conf|json)$'
PINNED='(^|/)guarded_autoresume\.sh$'  # provenance covered by SHA-256, not the commit

# rest of rule 2: frozen code (commit + allowlisted tree + pinned orchestration) + exclusive GPU
# NOTE: this guard runs in WSL against a Windows checkout made with core.autocrlf=true, so the
# working tree is CRLF while blobs are LF. WSL git (autocrlf unset) would flag every text file as
# modified — a false positive. Force the checkout's autocrlf so representations match; real content
# drift still shows. `git` alias below carries it to every status call.
GIT(){ git -C "$REPO" -c core.autocrlf=true "$@"; }
guard_env(){
  local head off
  head="$(GIT rev-parse HEAD 2>/dev/null)" || { log "REFUSE: git HEAD unreadable"; return 1; }
  [ "${head:0:12}" = "${LAUNCH_COMMIT:0:12}" ] || { log "REFUSE: HEAD ${head:0:7} != launch ${LAUNCH_COMMIT:0:7}"; return 1; }
  # (a) no TRACKED content modifications (line-ending-agnostic)
  [ "$(GIT status --porcelain -uno 2>/dev/null | wc -l)" -eq 0 ] || { log "REFUSE: tracked tree dirty"; GIT status --porcelain -uno 2>/dev/null | head | while read -r l; do log "    $l"; done; return 1; }
  # (b) no rogue UNTRACKED code/config outside the allowlist (pinned wrapper excepted)
  off="$(GIT status --porcelain --untracked-files=all 2>/dev/null | awk '/^\?\?/{print $2}' \
        | grep -vE "$ALLOW_UNTRACKED" | grep -E "$CODE_LIKE" | grep -vE "$PINNED")"
  [ -z "$off" ] || { log "REFUSE: untracked code/config outside allowlist:"; while read -r f; do log "    $f"; done <<<"$off"; return 1; }
  # (c) orchestration scripts unchanged since arm-time (SHA-256 reverify)
  verify_orchestration || { log "REFUSE: orchestration hash reverification failed"; return 1; }
  sleep "$SETTLE"  # let GPU memory free after the crash before judging exclusivity
  if foreign_gpu; then log "REFUSE: GPU not exclusive (foreign compute-app present)"; return 1; fi
  return 0
}

# rule 5/6 from log evidence + foreign-gpu flag: TRANSIENT | EXTERNAL_OOM | HARD
classify(){
  local t; t="$(tail -60 "$LOGF")"
  if grep -qE 'Illegal instruction|cudaErrorUnknown|CUDA error: unknown|an illegal instruction' <<<"$t"; then echo TRANSIENT; return; fi
  if grep -qiE 'out of memory|CUDA out of memory|Aborted \(core dumped\)|signal 6|SIGABRT' <<<"$t"; then
     [ "$1" = 1 ] && echo EXTERNAL_OOM || echo HARD; return; fi
  echo HARD
}
fail_sig(){ grep -oE 'Illegal instruction|cudaErrorUnknown|CUDA error: unknown|out of memory|Aborted \(core dumped\)' "$LOGF" | tail -1; }

# ── watch the initial (already-running) segment ──────────────────────────────
seg0_start="$(grep -m1 utc_start "$AUDIT/$RUN_ID_BASE/run_start.txt" 2>/dev/null | awk '{print $2}')"
seg0_start="${seg0_start:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"; seg0_ep0=$(epoch_of)
record_orchestration
log "armed; watching pid $WATCH_PID ($RUN_ID_BASE), ckpt=$CKPT_DIR, target ${TARGET_EPOCHS} epochs"
while kill -0 "$WATCH_PID" 2>/dev/null; do sleep 20; done
now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
w=$(( $(date -d "$now" +%s) - $(date -d "$seg0_start" +%s) ))
ep=$(epoch_of)
record_seg "$RUN_ID_BASE" "$seg0_start" "$now" "$w" "$seg0_ep0" "$ep" \
  "$([ "$ep" -ge "$TARGET_EPOCHS" ] && echo complete || echo crashed)"

prev_fail_ep=-999; prev_sig=""; attempt=0
while :; do
  ep=$(epoch_of)
  if [ "$ep" -ge "$TARGET_EPOCHS" ] || grep -q 'Done\. Best valid' "$LOGF"; then
    log "DONE: $RUN_ID_BASE reached epoch $ep"; exit 0; fi

  foreign=0; foreign_gpu && foreign=1
  cls=$(classify "$foreign"); sig=$(fail_sig)
  log "crash detected: ckpt_epoch=$ep class=$cls sig='${sig:-none}' foreign_gpu=$foreign"

  # rule 7: identical failure at identical epoch -> stop
  if [ "$ep" = "$prev_fail_ep" ] && [ "$sig" = "$prev_sig" ]; then
    log "STOP (rule 7): identical failure repeats at epoch $ep ('$sig')"; exit 3; fi
  # rule 5/6: eligibility
  case "$cls" in
    TRANSIENT)    log "eligible: verified-transient failure" ;;
    EXTERNAL_OOM) log "eligible: OOM/abort WITH foreign-GPU evidence -> external collision" ;;
    HARD)         log "STOP (rule 5/6): non-transient failure, no external-collision evidence — NOT auto-resuming"; exit 4 ;;
  esac
  # rule 4: retry budget
  attempt=$((attempt+1))
  [ "$attempt" -le "$MAX_RESUMES" ] || { log "STOP (rule 4): exhausted $MAX_RESUMES resumes"; exit 5; }
  # rule 1 + protocol: checkpoint verification
  vout=$(verify_checkpoint) || { log "STOP (rule 1): $vout"; exit 6; }
  log "$vout"
  # rule 2: frozen code + exclusive GPU
  guard_env || { log "STOP (rule 2): environment guard refused resume"; exit 7; }
  # rule 4: backoff
  back=$([ "$attempt" -eq 1 ] && echo 30 || echo 120)
  log "resume $attempt/$MAX_RESUMES after ${back}s backoff"; sleep "$back"
  # rule 3: continuation run id linked to the failed segment
  cid="${RUN_ID_BASE}-cont$(printf '%02d' "$attempt")"; mkdir -p "$AUDIT/$cid"
  cat > "$AUDIT/$cid/run_start.txt" <<EOF
continuation_of: $RUN_ID_BASE
parent_failed_ckpt_epoch: $ep
failure_class: $cls
failure_signature: ${sig:-none}
foreign_gpu_evidence: $foreign
utc_start: $(date -u +%Y-%m-%dT%H:%M:%SZ)
resume_ckpt: $CKPT
launch_commit: $LAUNCH_COMMIT
orchestration_wrapper_sha256: $(sha "$WRAPPER_FILE")
orchestration_launcher_sha256: $(sha "$LAUNCHER_FILE")
EOF
  prev_fail_ep="$ep"; prev_sig="$sig"
  s_start="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; s_ep0="$ep"
  RESUME_CKPT="$CKPT" setsid nohup bash "$RUN_SCRIPT" >> "$LOGF" 2>&1 </dev/null &
  sleep 30
  tpid=$(pgrep -f 'train_dbp5l_lora.py .*--resume' | head -1)
  log "resumed under $cid (pid ${tpid:-unknown})"
  while kill -0 "${tpid:-0}" 2>/dev/null; do sleep 20; done
  s_end="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; s_epE=$(epoch_of)
  sw=$(( $(date -d "$s_end" +%s) - $(date -d "$s_start" +%s) ))
  record_seg "$cid" "$s_start" "$s_end" "$sw" "$s_ep0" "$s_epE" \
    "$([ "$s_epE" -ge "$TARGET_EPOCHS" ] && echo complete || echo crashed)"
done
