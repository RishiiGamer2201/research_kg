#!/bin/bash
# Create a CONTINUATION run: resumes a parent run's checkpoint under a NEW run identity,
# recording exactly what changed. The parent's manifest and run records are never touched.
#
# Usage: continue_run.sh <parent_run_dir> <NEW_RUN_ID> <parent_checkpoint> [repo_dir]
set -u
PARENT_DIR="${1:?usage: continue_run.sh <parent_run_dir> <NEW_RUN_ID> <parent_checkpoint> [repo]}"
NEW_ID="${2:?missing new run id}"
PARENT_CKPT="${3:?missing parent checkpoint path}"
REPO="${4:-/mnt/c/developer/research_ai/research_kg/mkgc-multilingual-inductive}"

[ -d "$PARENT_DIR" ] || { echo "no parent run dir $PARENT_DIR" >&2; exit 2; }
[ -f "$PARENT_CKPT" ] || { echo "no parent checkpoint $PARENT_CKPT" >&2; exit 2; }

OUT_ROOT="$(dirname "$PARENT_DIR")"
NEW_DIR="$OUT_ROOT/$NEW_ID"
[ -e "$NEW_DIR" ] && { echo "REFUSING: $NEW_DIR exists (run dirs are never reused)" >&2; exit 2; }
mkdir -p "$NEW_DIR"

PARENT_ID="$(sed -n 's/^run_id=//p' "$PARENT_DIR/run_start.txt" | head -1)"
OLD_COMMIT="$(sed -n 's/^launch_commit=//p' "$PARENT_DIR/run_start.txt" | head -1)"
NEW_COMMIT="$(git -C "$REPO" rev-parse HEAD)"
CKPT_SHA="$(sha256sum "$PARENT_CKPT" | cut -d' ' -f1)"

# parent cache key, as recorded in the parent's training manifest (if reachable)
OLD_KEY="$(grep -oE '"cache_key": *"[^"]+"' "$PARENT_DIR"/../../../checkpoints/*/manifest.json 2>/dev/null \
           | head -1 | sed 's/.*: *"//;s/"//')"

cat > "$NEW_DIR/continuation.json" <<JSON
{
  "run_id": "$NEW_ID",
  "resumes_run_id": "${PARENT_ID:-unknown}",
  "parent_run_dir": "$PARENT_DIR",
  "parent_checkpoint": "$PARENT_CKPT",
  "parent_checkpoint_sha256": "$CKPT_SHA",
  "launch_commit_old": "${OLD_COMMIT:-unrecorded}",
  "launch_commit_new": "$NEW_COMMIT",
  "cache_key_old": "${OLD_KEY:-unrecorded}",
  "cache_key_new": "resolved at run start (see this run's training manifest)",
  "cache_key_delta_reason": "token_cache_key now also pins model_revision/tokenizer_revision",
  "parent_manifest_modified": false,
  "created_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON
echo "continuation record -> $NEW_DIR/continuation.json"
cat "$NEW_DIR/continuation.json"
echo
echo "Now launch the continuation with:"
echo "  bash scripts/baselines/launch_run.sh $NEW_ID $OUT_ROOT <command> --resume $PARENT_CKPT"
echo "(the parent run directory and its manifest are left untouched)"
