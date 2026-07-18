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
mkdir -p "$RUN_DIR"
LOG="$RUN_DIR/run.log"

{
  echo "run_id=$RUN_ID"
  echo "started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "host=$(hostname)"
  echo "command=$*"
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
