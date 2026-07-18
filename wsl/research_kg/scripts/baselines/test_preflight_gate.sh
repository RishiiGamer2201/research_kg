#!/bin/bash
R=/mnt/c/developer/research_ai/research_kg/mkgc-multilingual-inductive
B=$R/wsl/research_kg/scripts/baselines
V=$R/wsl/research_kg/scripts/baselines/_crlf_canary.sh
T=/tmp/pfgate; rm -rf $T; mkdir -p $T
fails=0
ck(){ [ "$2" = "$3" ] && echo "PASS $1" || { echo "FAIL $1 (got $2 want $3)"; fails=$((fails+1)); }; }

# baseline: launcher works when preflight is clean
bash $B/launch_run.sh GATE-OK $T bash -c 'echo ok' >/dev/null 2>&1; ck "clean launch allowed" "$?" "0"

# fault injection: introduce a CRLF shell script that git tracks
printf 'echo hi\r\n' > "$V"; git -C $R add -f "$V" >/dev/null 2>&1
bash $B/preflight.sh >/dev/null 2>&1; ck "preflight detects injected CRLF" "$?" "1"
bash $B/launch_run.sh GATE-BLOCKED $T bash -c 'echo should-not-run' >/dev/null 2>&1
ck "launcher refuses on failed preflight" "$?" "2"
[ -d "$T/GATE-BLOCKED" ] && { echo "FAIL blocked run dir was created"; fails=$((fails+1)); } || echo "PASS no run dir created when blocked"

# cleanup injection
git -C $R rm -f --cached "$V" >/dev/null 2>&1; rm -f "$V"
bash $B/preflight.sh >/dev/null 2>&1; ck "preflight clean after cleanup" "$?" "0"
rm -rf $T
[ $fails -eq 0 ] && echo "preflight gate self-test OK" || echo "preflight gate self-test FAILED ($fails)"
