#!/bin/bash
# Resume guard: a run may only keep its identity if the code is IDENTICAL to its launch commit.
#
# Rationale: resuming under newer code silently mixes two code versions (and, here, two parent
# cache keys) inside one run identity, while the original manifest still claims the launch
# commit. Either pin the code, or continue under a NEW run id that records the delta.
#
# Usage:
#   resume_guard.sh <run_dir> <launch_commit> [repo_dir]
#
# DETERMINISTIC EXIT SEMANTICS (asserted by preflight.sh — do not change):
#   0 = ALLOWED   HEAD == launch commit AND working tree clean
#   1 = REFUSED   code/tree differs -> continue under a new run id (continue_run.sh)
#   2 = MALFORMED bad arguments, missing run dir, or git unreadable
# Note: CRLF line endings corrupt these codes; preflight.sh fails the launch if any tracked
# *.sh contains a CR byte (this bug once made the guard print REFUSED but exit 0).
set -u
RUN_DIR="${1:?usage: resume_guard.sh <run_dir> <launch_commit> [repo_dir]}"
LAUNCH_COMMIT="${2:?missing launch commit}"
REPO="${3:-/mnt/c/developer/research_ai/research_kg/mkgc-multilingual-inductive}"

[ -d "$RUN_DIR" ] || { echo "MALFORMED: no run dir $RUN_DIR" >&2; exit 2; }
HEAD_SHA="$(git -C "$REPO" rev-parse HEAD 2>/dev/null)" || {
  echo "MALFORMED: cannot read git HEAD in $REPO" >&2; exit 2; }
DIRTY="$(git -C "$REPO" status --porcelain 2>/dev/null | wc -l)"

short() { printf '%s' "${1:0:7}"; }

if [ "${HEAD_SHA:0:7}" = "${LAUNCH_COMMIT:0:7}" ] && [ "$DIRTY" -eq 0 ]; then
  echo "RESUME-OK: HEAD $(short "$HEAD_SHA") == launch commit $(short "$LAUNCH_COMMIT"), tree clean"
  exit 0
fi

reason=""
[ "${HEAD_SHA:0:7}" != "${LAUNCH_COMMIT:0:7}" ] && \
  reason="HEAD $(short "$HEAD_SHA") != launch commit $(short "$LAUNCH_COMMIT")"
[ "$DIRTY" -ne 0 ] && reason="${reason:+$reason; }working tree dirty ($DIRTY file(s))"

cat >&2 <<MSG
RESUME-REFUSED: $reason

This run may NOT be resumed under its current identity. Choose one:

  (a) pin the code and resume with the same identity:
      git -C "$REPO" worktree add /tmp/pin-$(short "$LAUNCH_COMMIT") $LAUNCH_COMMIT
      # then run from /tmp/pin-$(short "$LAUNCH_COMMIT")

  (b) continue under a NEW run id that records the delta:
      bash scripts/baselines/continue_run.sh <parent_run_dir> <NEW_RUN_ID> <parent_checkpoint>

The parent run's manifest and run records are never overwritten.
MSG
exit 1
