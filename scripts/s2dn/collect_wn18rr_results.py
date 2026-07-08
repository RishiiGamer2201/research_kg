import csv
import re
from pathlib import Path


LOG_DIR = Path("/home/admin_wsl/research_kg/logs/s2dn_reproduction")
OUT = LOG_DIR / "results_wn18rr.csv"
PATTERN = re.compile(
    r"MRR \| Hits@1 \| Hits@5 \| Hits@10 : "
    r"([0-9.]+) \| ([0-9.]+) \| ([0-9.]+) \| ([0-9.]+)"
)


def read_metrics(split: int):
    log_path = LOG_DIR / f"wn18rr_v{split}_test_gpu.log"
    if not log_path.exists():
        return None
    matches = PATTERN.findall(log_path.read_text(errors="replace"))
    if not matches:
        return None
    mrr, h1, h5, h10 = (float(x) for x in matches[-1])
    return {
        "dataset": f"WN18RR_v{split}",
        "mrr": mrr,
        "hits@1": h1,
        "hits@5": h5,
        "hits@10": h10,
    }


def main() -> None:
    rows = [row for split in range(1, 5) if (row := read_metrics(split))]
    if rows:
        avg = {
            "dataset": "WN18RR_average_completed",
            "mrr": sum(row["mrr"] for row in rows) / len(rows),
            "hits@1": sum(row["hits@1"] for row in rows) / len(rows),
            "hits@5": sum(row["hits@5"] for row in rows) / len(rows),
            "hits@10": sum(row["hits@10"] for row in rows) / len(rows),
        }
        rows.append(avg)

    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "mrr", "hits@1", "hits@5", "hits@10"])
        writer.writeheader()
        writer.writerows(rows)

    print(OUT)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
