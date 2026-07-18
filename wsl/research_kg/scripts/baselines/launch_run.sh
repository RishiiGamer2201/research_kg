#!/bin/bash
# Detached launcher that records the PID, command and exit cause.
#
# Fixes the gap found in LEX-RUN-001 (killed by SIGTERM, PID never captured because the
# launcher matched on process name only). Every run gets a run-scoped directory that is
# never reused, plus a start/exit record.
#
# Usage: bash launch_run.sh <RUN_ID> <output_root> <command...>
set -u
RUN_ID="$1"; shift
OUT_ROOT="$1"; shift
RUN_DIR="$OUT_ROOT/$RUN_ID"

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

setsid nohup bash -c '
  echo "pid=$$" >> "'"$RUN_DIR"'/run_start.txt"
  "$@" >> "'"$LOG"'" 2>&1
  code=$?
  {
    echo "exit_code=$code"
    echo "ended_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if [ $code -gt 128 ]; then echo "signal=$((code-128)) (terminated by signal)"; fi
  } >> "'"$RUN_DIR"'/run_exit.txt"
  touch "'"$RUN_DIR"'/.DONE"
' _ "$@" > /dev/null 2>&1 < /dev/null &
disown

sleep 1
echo "launched $RUN_ID -> $RUN_DIR"
cat "$RUN_DIR/run_start.txt"
