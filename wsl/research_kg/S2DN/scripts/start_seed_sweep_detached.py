"""Launch the paired-seed fb237_v1 sweep, detached.

Uses Popen(start_new_session=True), the only launch method that survives here. Runs baseline and
RuleTrust at each seed sequentially; expect roughly 4 to 5 hours per run, so about a day for the
default 3 seeds (6 runs).

Usage: python scripts/start_seed_sweep_detached.py [seeds...]   default seeds: 1 2 3
"""
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path("/home/admin_wsl/research_kg/S2DN")
LOG_DIR = Path("/home/admin_wsl/research_kg/logs/s2dn_reproduction")


def main() -> None:
    seeds = sys.argv[1:] or ["1", "2", "3"]
    for s in seeds:
        if not s.isdigit():
            print(f"seeds must be non-negative integers; got {s!r}", file=sys.stderr)
            raise SystemExit(2)

    script = ROOT / "scripts" / "run_seed_sweep_fb237_v1.sh"
    if not script.exists():
        print(f"missing launcher: {script}", file=sys.stderr)
        raise SystemExit(1)

    log = LOG_DIR / "fb237_v1_seed_sweep_detached.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = log.open("ab", buffering=0)
    proc = subprocess.Popen(
        [str(script), *seeds],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=out,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=os.environ.copy(),
    )
    print(proc.pid)
    print(log)


if __name__ == "__main__":
    main()
