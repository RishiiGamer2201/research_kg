"""Launch the rules-shuffled RuleTrust control, detached.

Uses Popen(start_new_session=True), the only launch method that has survived in this setup.

Usage:
  python scripts/start_ruletrust_shuffle_detached.py <1|2|3|4> [batch_size] [shuffle_seed]
"""
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path("/home/admin_wsl/research_kg/S2DN")
LOG_DIR = Path("/home/admin_wsl/research_kg/logs/s2dn_reproduction")


def main() -> None:
    argv = sys.argv[1:]
    if not 1 <= len(argv) <= 3 or argv[0] not in {"1", "2", "3", "4"}:
        print(
            "Usage: python scripts/start_ruletrust_shuffle_detached.py "
            "<1|2|3|4> [batch_size] [shuffle_seed]",
            file=sys.stderr,
        )
        raise SystemExit(2)

    split = argv[0]
    batch = argv[1] if len(argv) > 1 else "32"
    seed = argv[2] if len(argv) > 2 else "0"

    if not batch.isdigit():
        print("batch_size must be a positive integer", file=sys.stderr)
        raise SystemExit(2)
    if not seed.isdigit():
        print("shuffle_seed must be a non-negative integer", file=sys.stderr)
        raise SystemExit(2)

    script = ROOT / "scripts" / "run_ruletrust_shuffle_fb237_gpu.sh"
    if not script.exists():
        print(f"missing launcher: {script}", file=sys.stderr)
        raise SystemExit(1)

    suffix = "" if batch == "32" else f"_bs{batch}"
    log = LOG_DIR / f"fb237_v{split}_ruletrust_shuffle{seed}{suffix}_detached.log"

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = log.open("ab", buffering=0)
    proc = subprocess.Popen(
        [str(script), split, batch, seed],
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
