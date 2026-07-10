import os
import subprocess
import sys
from pathlib import Path


ROOT = Path("/home/admin_wsl/research_kg/S2DN")
LOG_DIR = Path("/home/admin_wsl/research_kg/logs/s2dn_reproduction")


def main() -> None:
    argc = len(sys.argv)
    if argc not in (2, 3) or sys.argv[1] not in {"1", "2", "3", "4"}:
        print(
            "Usage: python scripts/start_fb237_paper_split_detached.py <1|2|3|4> [batch_size]",
            file=sys.stderr,
        )
        raise SystemExit(2)

    split = sys.argv[1]
    batch = sys.argv[2] if argc == 3 else "32"
    if not batch.isdigit():
        print("batch_size must be a positive integer", file=sys.stderr)
        raise SystemExit(2)

    script = ROOT / "scripts" / "run_fb237_paper_split_gpu.sh"
    suffix = "" if batch == "32" else f"_bs{batch}"
    log = LOG_DIR / f"fb237_v{split}_paper{suffix}_detached.log"

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = log.open("ab", buffering=0)
    proc = subprocess.Popen(
        [str(script), split, batch],
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
