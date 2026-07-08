import os
import subprocess
import sys
from pathlib import Path


ROOT = Path("/home/admin_wsl/research_kg/S2DN")
LOG_DIR = Path("/home/admin_wsl/research_kg/logs/s2dn_reproduction")


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in {"wn18rr", "fb237", "nell"} or sys.argv[2] not in {"1", "2", "3", "4"}:
        print("Usage: python scripts/start_inductive_split_detached.py <wn18rr|fb237|nell> <1|2|3|4>", file=sys.stderr)
        raise SystemExit(2)

    family = sys.argv[1]
    split = sys.argv[2]
    script = ROOT / "scripts" / "run_inductive_split_gpu.sh"
    log = LOG_DIR / f"{family}_v{split}_detached.log"

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = log.open("ab", buffering=0)
    proc = subprocess.Popen(
        [str(script), family, split],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=out,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=os.environ.copy(),
    )
    print(proc.pid)


if __name__ == "__main__":
    main()
