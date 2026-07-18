#!/bin/bash
# Self-test for launch_run.sh. Added after B0-RUN-001 died in 1s because $LOG was referenced
# inside the detached shell but never exported (the redirect got an empty filename). The
# checker was tested; the launcher was not. This closes that gap.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
T=/tmp/launchrun_test; rm -rf $T; mkdir -p $T
fails=0
ck() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1 (got '$2' want '$3')"; fails=$((fails+1)); fi; }

# 1. successful run: log captured, exit recorded, lock + heartbeat + pid present
HEARTBEAT_SECONDS=1 bash "$HERE/launch_run.sh" T-OK $T bash -c 'echo hello-from-job; sleep 3' > $T/launch1.txt 2>&1
sleep 6
ck "log captured"        "$(grep -c hello-from-job $T/T-OK/run.log 2>/dev/null)" "1"
ck "exit recorded"       "$(grep -c 'exit_code=0' $T/T-OK/run_exit.txt 2>/dev/null)" "1"
ck "pid recorded"        "$(grep -c '^pid=[0-9]' $T/T-OK/run_start.txt 2>/dev/null)" "1"
ck "lock written"        "$(grep -c 'T-OK' $T/T-OK/run.lock 2>/dev/null)" "1"
ck "heartbeat written"   "$([ -s $T/T-OK/heartbeat.txt ] && echo 1 || echo 0)" "1"
ck "done marker"         "$([ -f $T/T-OK/.DONE ] && echo 1 || echo 0)" "1"

# 2. failing job: non-zero exit is recorded (not swallowed)
bash "$HERE/launch_run.sh" T-FAIL $T bash -c 'exit 7' > /dev/null 2>&1
sleep 3
ck "failure exit code"   "$(grep -c 'exit_code=7' $T/T-FAIL/run_exit.txt 2>/dev/null)" "1"

# 3. signalled job: signal is decoded
bash "$HERE/launch_run.sh" T-SIG $T bash -c 'kill -TERM $$' > /dev/null 2>&1
sleep 3
ck "signal decoded"      "$(grep -c 'signal=15' $T/T-SIG/run_exit.txt 2>/dev/null)" "1"

# 4. run directories are never reused
bash "$HERE/launch_run.sh" T-OK $T bash -c 'true' > $T/launch2.txt 2>&1
ck "refuses reuse"       "$(grep -c REFUSING $T/launch2.txt)" "1"

# 5. health check agrees with the launcher on a live run
HEARTBEAT_SECONDS=1 bash "$HERE/launch_run.sh" T-LIVE $T bash -c 'sleep 20' > /dev/null 2>&1
sleep 3
bash "$HERE/check_run.sh" $T/T-LIVE > $T/chk.txt 2>&1
ck "live run healthy"    "$(grep -c HEALTHY $T/chk.txt)" "1"
pkill -f 'sleep 20' 2>/dev/null

rm -rf $T
[ $fails -eq 0 ] && echo "launch_run self-test OK" || { echo "launch_run self-test FAILED ($fails)"; exit 1; }
