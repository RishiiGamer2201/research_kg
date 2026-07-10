"""Launch the RuleTrust-S2DN FB15k-237 run, detached.

Uses the same Popen(start_new_session=True) pattern as the other start_*_detached.py
scripts, which is the only launch method that has actually survived in this setup. A raw
`nohup ... &` inside `wsl -- bash -lc` dies with the wsl.exe session.

Usage:
  python scripts/start_ruletrust_fb237_detached.py <1|2|3|4> [batch_size] [score|adjacency|both]
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
            "Usage: python scripts/start_ruletrust_fb237_detached.py "
            "<1|2|3|4> [batch_size] [score|adjacency|both]",
            file=sys.stderr,
        )
        raise SystemExit(2)

    split = argv[0]
    batch = argv[1] if len(argv) > 1 else "32"
    mode = argv[2] if len(argv) > 2 else "score"

    if not batch.isdigit():
        print("batch_size must be a positive integer", file=sys.stderr)
        raise SystemExit(2)
    if mode not in {"score", "adjacency", "both"}:
        print("mode must be one of score, adjacency, both", file=sys.stderr)
        raise SystemExit(2)

    script = ROOT / "scripts" / "run_ruletrust_fb237_gpu.sh"
    if not script.exists():
        print(f"missing launcher: {script}", file=sys.stderr)
        raise SystemExit(1)

    suffix = ""
    if batch != "32":
        suffix += f"_bs{batch}"
    if mode != "score":
        suffix += f"_{mode}"
    log = LOG_DIR / f"fb237_v{split}_ruletrust{suffix}_detached.log"

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = log.open("ab", buffering=0)
    proc = subprocess.Popen(
        [str(script), split, batch, mode],
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
