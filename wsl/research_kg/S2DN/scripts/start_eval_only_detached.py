import os
import subprocess
import sys
from pathlib import Path


ROOT = Path("/home/admin_wsl/research_kg/S2DN")
LOG_DIR = Path("/home/admin_wsl/research_kg/logs/s2dn_reproduction")
PYTHON = ROOT / "venv_s2dn_gpu_latest" / "bin" / "python"


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in {"wn18rr", "fb237", "nell"} or sys.argv[2] not in {"1", "2", "3", "4"}:
        print("Usage: python scripts/start_eval_only_detached.py <wn18rr|fb237|nell> <1|2|3|4>", file=sys.stderr)
        raise SystemExit(2)

    family = sys.argv[1]
    split = sys.argv[2]
    if family == "wn18rr":
        dataset = f"WN18RR_v{split}_ind"
        experiment = f"sdn_wn_v{split}_gpu"
    elif family == "fb237":
        dataset = f"fb237_v{split}_ind"
        experiment = f"sdn_fb_v{split}_gpu"
    else:
        dataset = f"nell_v{split}_ind"
        experiment = f"sdn_nell_v{split}_gpu"

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / f"{family}_v{split}_test_retry.log"
    out = log.open("ab", buffering=0)
    proc = subprocess.Popen(
        [str(PYTHON), "test_ranking.py", "-d", dataset, "-e", experiment],
        cwd=str(ROOT / "SDN"),
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
