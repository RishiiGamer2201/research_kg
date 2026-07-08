import os
import subprocess
from pathlib import Path


ROOT = Path("/home/admin_wsl/research_kg/S2DN")
LOG_DIR = Path("/home/admin_wsl/research_kg/logs/s2dn_reproduction")
SCRIPT = ROOT / "scripts" / "run_wn18rr_v1_gpu.sh"
LOG = LOG_DIR / "wn18rr_v1_gpu_detached.log"


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG.open("ab", buffering=0)
    proc = subprocess.Popen(
        [str(SCRIPT)],
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
