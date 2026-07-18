"""DBP5L-Ind v2 / P1.1 — freeze + hash the raw DBP-5L source.

SHA-256s every raw source file so the whole v2 benchmark is content-addressed back to an
immutable upstream snapshot. Any byte change upstream changes the manifest and invalidates
downstream comparisons.

Raw layout ($RESEARCH_KG_ROOT/DBP5L/raw), from KEnS (github.com/stasl0217/KEnS/tree/main/data):
  kg/{lang}-{train,val,test}.tsv   per-language triples (local ids)
  entity/{lang}.tsv                local id -> DBpedia URI  (the ORIGINAL identity, preserved)
  seed_alignlinks/{l1}-{l2}.tsv    cross-language alignment pairs (local ids)
  relations.txt                    original relation vocabulary

Output: DBP5L/ind_v2/source_manifest.json  {file: {sha256, bytes, lines}} + a top hash.

Self-check: `python3 hash_source_data.py --selftest`.
"""
import os
import sys
import json
import time
import hashlib
import argparse


def _hash(path):
    h = hashlib.sha256()
    n_lines = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n_lines += chunk.count(b"\n")
    return h.hexdigest(), os.path.getsize(path), n_lines


def build(root):
    raw = os.path.join(root, "DBP5L/raw")
    files = {}
    for dirpath, _, names in os.walk(raw):
        for name in names:
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, raw).replace(os.sep, "/")
            sha, size, lines = _hash(p)
            files[rel] = {"sha256": sha, "bytes": size, "lines": lines}
    # top hash = hash of the sorted per-file digests (order-independent, tamper-evident)
    top = hashlib.sha256(
        json.dumps({k: files[k]["sha256"] for k in sorted(files)},
                   sort_keys=True).encode()).hexdigest()
    manifest = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "upstream": "github.com/stasl0217/KEnS (data/), DBP-5L",
        "n_files": len(files),
        "total_bytes": sum(v["bytes"] for v in files.values()),
        "top_sha256": top,
        "files": files,
    }
    out = os.path.join(root, "DBP5L/ind_v2/source_manifest.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return manifest


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="src_hash_test_")
    try:
        raw = os.path.join(d, "DBP5L/raw/kg"); os.makedirs(raw)
        with open(os.path.join(raw, "en-train.tsv"), "w") as f:
            f.write("0\t1\t2\n3\t4\t5\n")
        m1 = build(d)
        assert m1["n_files"] == 1 and m1["files"]["kg/en-train.tsv"]["lines"] == 2, m1
        top1 = m1["top_sha256"]
        # one byte change -> top hash changes
        with open(os.path.join(raw, "en-train.tsv"), "a") as f:
            f.write("6\t7\t8\n")
        assert build(d)["top_sha256"] != top1, "top hash must change on content change"
        # unchanged rebuild -> identical
        with open(os.path.join(raw, "en-train.tsv"), "w") as f:
            f.write("0\t1\t2\n3\t4\t5\n")
        assert build(d)["top_sha256"] == top1, "hash must be stable for identical bytes"
        print("hash_source_data self-check OK")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("RESEARCH_KG_ROOT",
                                                     os.path.expanduser("~/research_kg")))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selfcheck()
        sys.exit(0)
    m = build(args.root)
    print(json.dumps({k: v for k, v in m.items() if k != "files"}, indent=2))
    print(f"per-file hashes: {m['n_files']} files in source_manifest.json")
