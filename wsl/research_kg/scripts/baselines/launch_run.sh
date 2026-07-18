#!/bin/bash
# Detached launcher that records the PID, command, a run lock and a live heartbeat.
#
# Fixes two gaps found in practice:
#   LEX-RUN-001 — killed by SIGTERM, PID never captured (launcher matched on process name).
#   LEX-RUN-002 — a `pgrep` health check returned a false positive (it matched the checker
#                 shell), so a dead run looked alive. Health is now verified against the
#                 recorded PID + cmdline + lock ownership + heartbeat (see check_run.sh).
#
# Usage: bash launch_run.sh <RUN_ID> <output_root> <command...>
set -u
RUN_ID="$1"; shift
OUT_ROOT="$1"; shift
RUN_DIR="$OUT_ROOT/$RUN_ID"
HEARTBEAT_SECONDS="${HEARTBEAT_SECONDS:-15}"

if [ -e "$RUN_DIR" ]; then
  echo "REFUSING: $RUN_DIR already exists (run directories are never reused)" >&2
  exit 2
fi

# Mandatory preflight: never launch on scripts that cannot report status (CRLF once made
# resume_guard.sh print REFUSED while exiting 0). Set SKIP_PREFLIGHT=1 only to debug.
if [ "${SKIP_PREFLIGHT:-0}" != "1" ]; then
  PREFLIGHT="$(cd "$(dirname "$0")" && pwd)/preflight.sh"
  if [ -f "$PREFLIGHT" ]; then
    bash "$PREFLIGHT" > /tmp/preflight_$$.log 2>&1 || {
      echo "REFUSING: preflight failed — not launching $RUN_ID" >&2
      cat /tmp/preflight_$$.log >&2; rm -f /tmp/preflight_$$.log; exit 2; }
    rm -f /tmp/preflight_$$.log
  fi
fi
mkdir -p "$RUN_DIR"
LOG="$RUN_DIR/run.log"

REPO_DIR="${REPO_DIR:-/mnt/c/developer/research_ai/research_kg/mkgc-multilingual-inductive}"
{
  echo "run_id=$RUN_ID"
  echo "started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "host=$(hostname)"
  echo "command=$*"
  # launch commit is recorded so resume_guard.sh can refuse resuming under different code
  echo "launch_commit=$(git -C "$REPO_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "launch_tree_dirty=$(git -C "$REPO_DIR" status --porcelain 2>/dev/null | wc -l)"
} > "$RUN_DIR/run_start.txt"

RUN_ID="$RUN_ID" RUN_DIR="$RUN_DIR" LOG="$LOG" HEARTBEAT_SECONDS="$HEARTBEAT_SECONDS" \
setsid nohup bash -c '
  set -u                      # an unset var (e.g. LOG) must fail loudly, not redirect to ""
  echo "pid=$$" >> "$RUN_DIR/run_start.txt"
  # run lock: binds this run directory to this PID/owner, for ownership verification
  cat > "$RUN_DIR/run.lock" <<LOCK
{"run_id": "$RUN_ID", "pid": $$, "uid": $(id -u), "user": "$(id -un)",
 "host": "$(hostname)", "started_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
LOCK
  # heartbeat: updated while the job runs, so a stalled/dead job is detectable
  (
    while kill -0 $$ 2>/dev/null; do
      printf "%s %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(date +%s)" > "$RUN_DIR/heartbeat.txt"
      sleep "$HEARTBEAT_SECONDS"
    done
  ) &
  HB=$!
  "$@" >> "$LOG" 2>&1
  code=$?
  kill "$HB" 2>/dev/null
  {
    echo "exit_code=$code"
    echo "ended_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if [ $code -gt 128 ]; then echo "signal=$((code-128)) (terminated by signal)"; fi
  } >> "$RUN_DIR/run_exit.txt"
  touch "$RUN_DIR/.DONE"
' _ "$@" > /dev/null 2>&1 < /dev/null &
disown

sleep 1
echo "launched $RUN_ID -> $RUN_DIR"
cat "$RUN_DIR/run_start.txt"
