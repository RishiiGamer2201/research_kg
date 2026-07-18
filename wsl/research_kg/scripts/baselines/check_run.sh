#!/bin/bash
# Health check for a launched run. Replaces `pgrep`, which can match the checker shell or an
# unrelated process (that false positive made a dead run look alive in LEX-RUN-002).
#
# Four independent verifications, all against the RECORDED pid:
#   1. kill -0 <pid>                    process exists and is signalable by us
#   2. /proc/<pid>/cmdline contains RUN_ID (or environ has RUN_ID=)   right process, not a shell
#   3. run.lock pid/uid match the live process owner                  owns this run directory
#   4. heartbeat.txt is fresh                                         actually progressing
#
# Usage: bash check_run.sh <run_dir> [max_heartbeat_age_seconds]
# Exit:  0 healthy · 1 finished · 2 unhealthy/stale · 3 malformed run dir
set -u
RUN_DIR="${1:?usage: check_run.sh <run_dir> [max_heartbeat_age_s]}"
MAX_AGE="${2:-90}"

[ -d "$RUN_DIR" ] || { echo "MALFORMED: no run dir $RUN_DIR"; exit 3; }
START="$RUN_DIR/run_start.txt"
[ -f "$START" ] || { echo "MALFORMED: missing run_start.txt"; exit 3; }

RUN_ID="$(sed -n 's/^run_id=//p' "$START" | head -1)"
PID="$(sed -n 's/^pid=//p' "$START" | head -1)"
[ -n "$RUN_ID" ] || { echo "MALFORMED: no run_id"; exit 3; }

if [ -f "$RUN_DIR/.DONE" ] || [ -f "$RUN_DIR/run_exit.txt" ]; then
  echo "FINISHED $RUN_ID: $(cat "$RUN_DIR/run_exit.txt" 2>/dev/null | tr '\n' ' ')"
  exit 1
fi
[ -n "$PID" ] || { echo "MALFORMED: no pid recorded for $RUN_ID"; exit 3; }

fail() { echo "UNHEALTHY $RUN_ID (pid $PID): $1"; exit 2; }

# 1. process exists
kill -0 "$PID" 2>/dev/null || fail "kill -0 failed (process gone)"

# 2. it is OUR process, not a shell that happens to match a name
CMDLINE="$(tr '\0' ' ' < "/proc/$PID/cmdline" 2>/dev/null || true)"
if ! printf '%s' "$CMDLINE" | grep -q -- "$RUN_ID"; then
  ENVIRON="$(tr '\0' '\n' < "/proc/$PID/environ" 2>/dev/null | grep -c "^RUN_ID=$RUN_ID$" || true)"
  [ "${ENVIRON:-0}" -ge 1 ] || fail "pid alive but cmdline/environ do not reference $RUN_ID (cmdline: ${CMDLINE:0:120})"
fi

# 3. run-directory ownership: lock pid + uid must match the live process
if [ -f "$RUN_DIR/run.lock" ]; then
  LPID="$(sed -n 's/.*"pid": *\([0-9]*\).*/\1/p' "$RUN_DIR/run.lock" | head -1)"
  LUID="$(sed -n 's/.*"uid": *\([0-9]*\).*/\1/p' "$RUN_DIR/run.lock" | head -1)"
  [ "$LPID" = "$PID" ] || fail "run.lock pid $LPID != recorded pid $PID"
  PUID="$(awk '/^Uid:/{print $2}' "/proc/$PID/status" 2>/dev/null)"
  [ -z "$LUID" ] || [ -z "$PUID" ] || [ "$LUID" = "$PUID" ] || fail "run.lock uid $LUID != process uid $PUID"
  LOCK_OK="lock ok"
else
  LOCK_OK="no run.lock (pre-lock launcher)"
fi

# 4. heartbeat freshness
if [ -f "$RUN_DIR/heartbeat.txt" ]; then
  HB_EPOCH="$(awk '{print $2}' "$RUN_DIR/heartbeat.txt" 2>/dev/null)"
  NOW="$(date +%s)"
  AGE=$(( NOW - ${HB_EPOCH:-0} ))
  [ "$AGE" -le "$MAX_AGE" ] || fail "heartbeat stale (${AGE}s > ${MAX_AGE}s) — process alive but not progressing"
  HB_OK="heartbeat ${AGE}s old"
else
  HB_OK="no heartbeat (pre-heartbeat launcher)"
fi

echo "HEALTHY $RUN_ID (pid $PID): $LOCK_OK, $HB_OK"
exit 0
