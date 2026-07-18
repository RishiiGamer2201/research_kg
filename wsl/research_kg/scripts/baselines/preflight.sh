#!/bin/bash
# Permanent preflight — run BEFORE any launch, and in CI.
#
# Exists because CRLF in a working-tree shell script silently corrupted exit codes:
# resume_guard.sh printed REFUSED but exited 0, i.e. the guard would have permitted exactly
# what it exists to prevent. A launch must never proceed on scripts that cannot report status.
#
# Checks:
#   1. no tracked *.sh contains a CR byte
#   2. .gitattributes enforces `*.sh text eol=lf`
#   3. resume_guard.sh exit semantics are exactly 0=allowed / 1=refused / 2=malformed
#   4. every script in scripts/baselines/ is syntactically valid (bash -n)
#
# Exit: 0 all checks pass, 1 any check fails.
set -u
REPO="${1:-/mnt/c/developer/research_ai/research_kg/mkgc-multilingual-inductive}"
fails=0
ok()   { echo "  PASS $1"; }
bad()  { echo "  FAIL $1"; fails=$((fails+1)); }

echo "[1/5] tracked *.sh must not contain CR"
crlf_files=""
while IFS= read -r f; do
  [ -f "$REPO/$f" ] || continue
  if [ "$(tr -cd '\r' < "$REPO/$f" | wc -c)" -gt 0 ]; then crlf_files="$crlf_files $f"; fi
done < <(git -C "$REPO" ls-files '*.sh')
if [ -z "$crlf_files" ]; then ok "no CR in tracked shell scripts"
else bad "CR found in:$crlf_files"; fi

echo "[2/5] .gitattributes enforces LF for *.sh"
if grep -qE '^\*\.sh[[:space:]]+text[[:space:]]+eol=lf' "$REPO/.gitattributes" 2>/dev/null; then
  ok "*.sh text eol=lf present"
else bad ".gitattributes missing '*.sh text eol=lf'"; fi

echo "[3/5] resume_guard.sh exit semantics (0=allowed, 1=refused, 2=malformed)"
G="$REPO/wsl/research_kg/scripts/baselines/resume_guard.sh"
if [ -f "$G" ]; then
  TMP=$(mktemp -d); mkdir -p "$TMP/run"
  HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"
  DIRTY="$(git -C "$REPO" status --porcelain | wc -l)"
  bash "$G" "$TMP/run" "0000000deadbeef0000000000000000000000000" "$REPO" >/dev/null 2>&1
  [ $? -eq 1 ] && ok "refused -> 1" || bad "refused did not return 1"
  bash "$G" "/nonexistent-run-dir" "$HEAD_SHA" "$REPO" >/dev/null 2>&1
  [ $? -eq 2 ] && ok "malformed -> 2" || bad "malformed did not return 2"
  bash "$G" "$TMP/run" "$HEAD_SHA" "$REPO" >/dev/null 2>&1; rc=$?
  if [ "$DIRTY" -eq 0 ]; then
    [ $rc -eq 0 ] && ok "allowed -> 0 (clean tree)" || bad "allowed did not return 0 on clean tree"
  else
    [ $rc -eq 1 ] && ok "dirty tree -> 1 (refused, as designed)" || bad "dirty tree did not return 1"
  fi
  rm -rf "$TMP"
else bad "resume_guard.sh not found"; fi

echo "[4/5] vendored subtrees unchanged since the vendoring snapshot"
# Compare the VENDORED SUBTREES (external/grail, external/SDN), not external/ itself: our own
# metadata (VENDOR_INTEGRITY.json) lives alongside them and would otherwise trip the guard.
VI="$REPO/external/VENDOR_INTEGRITY.json"
if [ -f "$VI" ]; then
  SNAP_COMMIT=$(grep -o '"vendoring_snapshot_commit": *"[^"]*"' "$VI" | sed 's/.*"\([^"]*\)"$/\1/')
  vend_ok=1
  for d in grail SDN; do
    a=$(git -C "$REPO" rev-parse "$SNAP_COMMIT:external/$d" 2>/dev/null)
    b=$(git -C "$REPO" rev-parse "HEAD:external/$d" 2>/dev/null)
    if [ -n "$a" ] && [ "$a" = "$b" ]; then ok "external/$d unchanged ($b)"
    else bad "external/$d CHANGED: $a -> $b (vendored code must not be edited; record it if intentional)"; vend_ok=0; fi
  done
else bad "external/VENDOR_INTEGRITY.json missing"; fi

echo "[5/5] bash -n on scripts/baselines/*.sh"
syn=0
for f in "$REPO"/wsl/research_kg/scripts/baselines/*.sh; do
  bash -n "$f" 2>/dev/null || { echo "    syntax error: $(basename "$f")"; syn=1; }
done
[ $syn -eq 0 ] && ok "all scripts parse" || bad "syntax errors present"

echo
if [ $fails -eq 0 ]; then echo "PREFLIGHT OK"; exit 0
else echo "PREFLIGHT FAILED ($fails check(s)) — do not launch"; exit 1; fi
