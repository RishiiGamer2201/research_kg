import csv
import re
import sys
from pathlib import Path


LOG_DIR = Path("/home/admin_wsl/research_kg/logs/s2dn_reproduction")
PATTERN = re.compile(r"MRR \| Hits@1 \| Hits@5 \| Hits@10 : ([0-9.]+) \| ([0-9.]+) \| ([0-9.]+) \| ([0-9.]+)")


def family_parts(family):
    if family == "wn18rr":
        return "WN18RR", "wn18rr", "results_wn18rr.csv", []
    if family == "fb237":
        return "fb237", "fb237", "results_fb237.csv", []
    if family == "fb237_paper":
        return "fb237", "fb237", "results_fb237_paper.csv", ["_paper"]
    if family == "nell":
        return "nell", "nell", "results_nell.csv", []
    raise ValueError(f"unknown family: {family}")


def extract_metrics(log_path):
    if not log_path.exists():
        return None
    text = log_path.read_text(errors="ignore")
    matches = PATTERN.findall(text)
    if not matches:
        return None
    mrr, h1, h5, h10 = matches[-1]
    return {
        "mrr": float(mrr),
        "hits@1": float(h1),
        "hits@5": float(h5),
        "hits@10": float(h10),
    }


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"wn18rr", "fb237", "fb237_paper", "nell"}:
        print("Usage: python scripts/collect_reproduction_results.py <wn18rr|fb237|fb237_paper|nell>", file=sys.stderr)
        raise SystemExit(2)

    family = sys.argv[1]
    dataset_prefix, log_prefix, out_name, suffixes = family_parts(family)
    rows = []
    for split in range(1, 5):
        metrics = None
        for suffix in suffixes + [""]:
            for stem in ("test_gpu", "test_retry", "detached"):
                metrics = extract_metrics(LOG_DIR / f"{log_prefix}_v{split}{suffix}_{stem}.log")
                if metrics is not None:
                    break
            if metrics is not None:
                break
        if metrics is None:
            continue
        row = {"dataset": f"{dataset_prefix}_v{split}"}
        row.update(metrics)
        rows.append(row)

    if rows:
        avg = {"dataset": f"{dataset_prefix}_average_completed"}
        for key in ("mrr", "hits@1", "hits@5", "hits@10"):
            avg[key] = sum(row[key] for row in rows) / len(rows)
        rows.append(avg)

    out_path = LOG_DIR / out_name
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset", "mrr", "hits@1", "hits@5", "hits@10"])
        writer.writeheader()
        writer.writerows(rows)

    print(out_path)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
