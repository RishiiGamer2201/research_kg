"""Phase 2 — three encoded-view evaluation of a trained checkpoint (post-training driver).

Runs the frozen reporting protocol on ONE checkpoint:
  views      : natural (primary alignment-free) | alias-masked | missing-text
  directions : head, tail, combined (reciprocal marker; reported separately)
  buckets    : mentioned / unmentioned (zero-cost partition of the natural-view ranks)
  extras     : per-triple rank dumps per view, for paired significance testing later

Each view is written atomically as it completes, with a resumable completion index (same
durability rule as the lexical audits: an end-of-run failure must not discard valid views).

The checkpoint is taken from the run's selection_record.json so the evaluated artifact is
exactly the one validation selected, and its SHA-256 is re-verified before evaluating.

Usage:
  python3 eval_three_views.py --train-run-dir <checkpoints/...> --out-dir <audits/eval/ID>
  python3 eval_three_views.py ... --resume
Self-check: `python3 eval_three_views.py --selftest`
"""
import os
import sys
import json
import time
import argparse
import hashlib

ROOT = os.environ.get("RESEARCH_KG_ROOT", os.path.expanduser("~/research_kg"))
sys.path.insert(0, ROOT)

VIEWS = {
    "natural": "DBP5L/ind_v2/tracks/descriptions_v2_primary.json",
    "masked": "DBP5L/ind_v2/tracks/descriptions_v2_masked.json",
    "missing": "DBP5L/ind_v2/tracks/descriptions_v2_missing_text.json",
}


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def load_selection(train_run_dir):
    """Checkpoint + selection metadata, with the SHA-256 re-verified."""
    sel_path = os.path.join(train_run_dir, "selection_record.json")
    if not os.path.exists(sel_path):
        raise FileNotFoundError(
            f"no selection_record.json in {train_run_dir} — training must complete first "
            f"(the record is written before any evaluation).")
    sel = json.load(open(sel_path))
    ckpt = sel["selected_checkpoint"]
    if not os.path.exists(ckpt):
        raise FileNotFoundError(f"selected checkpoint missing: {ckpt}")
    actual = _sha256(ckpt)
    if sel.get("selected_checkpoint_sha256") not in (None, actual):
        raise RuntimeError(
            f"checkpoint hash mismatch: selection_record says "
            f"{str(sel['selected_checkpoint_sha256'])[:12]} but the file is {actual[:12]}. "
            f"Refusing to evaluate a checkpoint that is not the one validation selected.")
    return sel, ckpt, actual


def run_view(ckpt, view_name, view_path, fold_dir, out_dir):
    import eval_dbp5l as E
    E.DESC_PATH_OVERRIDE = view_path
    targets = os.path.join(fold_dir, "budgets", "eval_targets_test.json")
    dump = os.path.join(out_dir, f"ranks_{view_name}.json")
    t0 = time.time()
    res = E.evaluate(ckpt, per_language=True, directions=["tail", "head"],
                     v2_targets_path=targets, dump_ranks=dump)
    res["view"] = view_name
    res["view_hash"] = _sha256(view_path)
    res["rank_dump"] = dump
    res["seconds"] = round(time.time() - t0, 1)
    return res


def main(a):
    sel, ckpt, ckpt_sha = load_selection(a.train_run_dir)
    out_dir = a.out_dir if os.path.isabs(a.out_dir) else os.path.join(ROOT, a.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    idx_path = os.path.join(out_dir, "completion_index.json")
    index = json.load(open(idx_path)) if (a.resume and os.path.exists(idx_path)) else {"views": {}}

    # pin what is being evaluated, before any GPU work
    _atomic_write(os.path.join(out_dir, "evaluated_checkpoint.json"), {
        "train_run_dir": a.train_run_dir,
        "selected_checkpoint": ckpt,
        "selected_checkpoint_sha256": ckpt_sha,
        "selection_metric": sel.get("selection_metric"),
        "selection_value": sel.get("selection_value"),
        "selection_epoch": sel.get("selection_epoch"),
        "fold": os.path.basename(a.fold.rstrip("/")),
        "directions": ["tail", "head", "combined"],
        "views": list(VIEWS),
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

    for name, rel in VIEWS.items():
        if a.resume and name in index["views"]:
            print(f"[{name}] skipped (already complete)", flush=True); continue
        r = run_view(ckpt, name, os.path.join(ROOT, rel), a.fold, out_dir)
        _atomic_write(os.path.join(out_dir, f"view_{name}.json"), r)
        bd, bm = r["by_direction"], r["by_mention"]
        index["views"][name] = {
            "combined_mrr": bd["combined"]["within_language_overall"]["mrr"],
            "tail_mrr": bd["tail"]["within_language_overall"]["mrr"],
            "head_mrr": bd["head"]["within_language_overall"]["mrr"],
            "unmentioned_combined_mrr": bm["combined"]["unmentioned"]["mrr"],
            "seconds": r["seconds"],
            "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        _atomic_write(idx_path, index)
        print(f"[{name}] combined {index['views'][name]['combined_mrr']:.3f} "
              f"(tail {index['views'][name]['tail_mrr']:.3f} / "
              f"head {index['views'][name]['head_mrr']:.3f}) "
              f"unmentioned {index['views'][name]['unmentioned_combined_mrr']:.3f} "
              f"[{r['seconds']:.0f}s]", flush=True)
    print("three-view evaluation complete ->", out_dir)


def _selftest():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="e3v_")
    try:
        # missing selection record -> clear, actionable error
        try:
            load_selection(d); raise SystemExit("expected FileNotFoundError")
        except FileNotFoundError as e:
            assert "selection_record.json" in str(e)
        # hash mismatch must be refused
        ck = os.path.join(d, "best_model.pt")
        open(ck, "wb").write(b"weights")
        json.dump({"selected_checkpoint": ck, "selected_checkpoint_sha256": "0" * 64},
                  open(os.path.join(d, "selection_record.json"), "w"))
        try:
            load_selection(d); raise SystemExit("expected hash mismatch RuntimeError")
        except RuntimeError as e:
            assert "hash mismatch" in str(e)
        # correct hash accepted
        json.dump({"selected_checkpoint": ck, "selected_checkpoint_sha256": _sha256(ck),
                   "selection_epoch": 7},
                  open(os.path.join(d, "selection_record.json"), "w"))
        sel, c, h = load_selection(d)
        assert sel["selection_epoch"] == 7 and h == _sha256(ck)
        print("eval_three_views self-check OK (selection record verified, hash mismatch refused)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-run-dir", help="checkpoint dir containing selection_record.json")
    ap.add_argument("--fold", default=os.path.join(ROOT, "DBP5L/ind_v2/folds/fold0_seed13"))
    ap.add_argument("--out-dir", default="DBP5L/ind_v2/audits/eval/B0-FOLD0-SEED42")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        _selftest(); sys.exit(0)
    if not a.train_run_dir:
        ap.error("--train-run-dir is required")
    main(a)
