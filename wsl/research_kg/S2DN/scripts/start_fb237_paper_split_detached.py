import os
import subprocess
import sys
from pathlib import Path


ROOT = Path("/home/admin_wsl/research_kg/S2DN")
LOG_DIR = Path("/home/admin_wsl/research_kg/logs/s2dn_reproduction")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"1", "2", "3", "4"}:
        print("Usage: python scripts/start_fb237_paper_split_detached.py <1|2|3|4>", file=sys.stderr)
        raise SystemExit(2)

    split = sys.argv[1]
    script = ROOT / "scripts" / "run_fb237_paper_split_gpu.sh"
    log = LOG_DIR / f"fb237_v{split}_paper_detached.log"

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = log.open("ab", buffering=0)
    proc = subprocess.Popen(
        [str(script), split],
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
