#!/bin/bash
cd "$HOME/research_kg"
T=/tmp/checkrun_test; rm -rf $T; mkdir -p $T
CHK="bash scripts/baselines/check_run.sh"

# case A: pid points at an UNRELATED live process (sleep) -> must be UNHEALTHY, not healthy
mkdir -p $T/A; sleep 300 & UNREL=$!
printf "run_id=FAKE-RUN-A\npid=%s\n" "$UNREL" > $T/A/run_start.txt
$CHK $T/A >/dev/null 2>&1; echo "A unrelated-pid exit=$? (want 2)"
kill $UNREL 2>/dev/null

# case B: dead pid -> UNHEALTHY
mkdir -p $T/B; sleep 1 & D=$!; wait $D 2>/dev/null
printf "run_id=FAKE-RUN-B\npid=%s\n" "$D" > $T/B/run_start.txt
$CHK $T/B >/dev/null 2>&1; echo "B dead-pid exit=$? (want 2)"

# case C: finished run -> exit 1
mkdir -p $T/C; printf "run_id=FAKE-RUN-C\npid=1\n" > $T/C/run_start.txt
echo "exit_code=0" > $T/C/run_exit.txt; touch $T/C/.DONE
$CHK $T/C >/dev/null 2>&1; echo "C finished exit=$? (want 1)"

# case D: alive + cmdline references run id + fresh heartbeat + matching lock -> HEALTHY
mkdir -p $T/D
setsid nohup bash -c 'while true; do sleep 1; done' --RUNTAG-HEALTHY-D >/dev/null 2>&1 &
LIVE=$!; sleep 1
printf "run_id=RUNTAG-HEALTHY-D\npid=%s\n" "$LIVE" > $T/D/run_start.txt
printf '{"run_id": "RUNTAG-HEALTHY-D", "pid": %s, "uid": %s}\n' "$LIVE" "$(id -u)" > $T/D/run.lock
printf "%s %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(date +%s)" > $T/D/heartbeat.txt
$CHK $T/D; echo "D healthy exit=$? (want 0)"

# case E: same as D but STALE heartbeat -> UNHEALTHY (alive but not progressing)
printf "%s %s\n" "old" "$(( $(date +%s) - 600 ))" > $T/D/heartbeat.txt
$CHK $T/D >/dev/null 2>&1; echo "E stale-heartbeat exit=$? (want 2)"
kill $LIVE 2>/dev/null
rm -rf $T
