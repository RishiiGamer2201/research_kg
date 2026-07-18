"""Phase 2 — total compute budget estimator (not training time alone).

Feeds on measured numbers from a profiling run's manifest (`metrics.profile`) and prices the
WHOLE Phase-2 plan:

  per run  = training epochs
           + hard-negative cache refreshes (one entity encode per epoch from --hard-neg-start-epoch)
           + evaluation over FOUR description views (natural, masked, missing [+ mentioned/
             unmentioned is a free split of natural]), each needing an entity-encode + a
             head-and-tail ranking pass
  plan     = per-run x runs, x encoders, + failed-run allowance + confirmation reruns

Plans:
  fallback : 3 folds @ seed 42, plus 3 paired seeds on fold0  -> 5 unique runs / encoder
  full3x3  : every fold x every seed                          -> 9 unique runs / encoder

Usage:
  python3 estimate_phase2_budget.py --manifest <run_dir>/manifest.json
  python3 estimate_phase2_budget.py --epoch-min 26 --encode-min 4 --valid-min 1.5   # manual

Self-check: `python3 estimate_phase2_budget.py --selftest`.
"""
import os
import sys
import json
import argparse

# plan constants (mirror docs/PHASE2_BASELINE_MATRIX.md)
EPOCHS = 30
HN_START_EPOCH = 5
N_VIEWS = 3                 # natural, masked, missing (mentioned/unmentioned splits natural)
ENCODERS = ["bge-m3-lora(B0)", "mbert", "xlm-r"]
FAIL_ALLOWANCE = 0.20       # 20% for crashes/OOM/restarts
CONFIRM_FRACTION = 0.25     # re-run 25% of runs for confirmation/paired checks


def per_run_hours(epoch_min, encode_min, valid_min, eval_min,
                  epochs=EPOCHS, hn_start=HN_START_EPOCH, n_views=N_VIEWS):
    train_h = epochs * epoch_min / 60.0
    # HN cache refresh: one entity-encode per epoch from hn_start onwards
    hn_refreshes = max(epochs - hn_start + 1, 0)
    hn_h = hn_refreshes * encode_min / 60.0
    valid_h = epochs * valid_min / 60.0
    # evaluation: each view needs its own entity encode + head&tail ranking pass
    eval_h = n_views * (encode_min + eval_min) / 60.0
    return {"train_h": train_h, "hn_refresh_h": hn_h, "valid_h": valid_h,
            "eval_four_view_h": eval_h,
            "total_h": train_h + hn_h + valid_h + eval_h,
            "hn_refreshes": hn_refreshes}


def plan_cost(pr, runs_per_encoder, encoders=ENCODERS,
              fail=FAIL_ALLOWANCE, confirm=CONFIRM_FRACTION):
    base = pr["total_h"] * runs_per_encoder * len(encoders)
    with_fail = base * (1 + fail)
    with_confirm = with_fail + base * confirm
    return {"runs_per_encoder": runs_per_encoder,
            "encoders": len(encoders),
            "base_h": round(base, 1),
            "failed_run_allowance_h": round(with_fail - base, 1),
            "confirmation_rerun_h": round(base * confirm, 1),
            "total_h": round(with_confirm, 1),
            "total_days_at_20h": round(with_confirm / 20.0, 1)}


def report(epoch_min, encode_min, valid_min, eval_min):
    pr = per_run_hours(epoch_min, encode_min, valid_min, eval_min)
    out = {
        "measured_inputs_min": {"epoch": epoch_min, "encode": encode_min,
                                "validation_per_epoch": valid_min, "eval_pass": eval_min},
        "per_run": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in pr.items()},
        "plans": {
            "fallback_3folds_plus_3seeds": plan_cost(pr, 5),
            "full_3x3": plan_cost(pr, 9),
        },
    }
    return out


def _selfcheck():
    pr = per_run_hours(epoch_min=30, encode_min=6, valid_min=2, eval_min=3)
    # 30 epochs * 30 min = 15h train
    assert abs(pr["train_h"] - 15.0) < 1e-6, pr
    # HN refreshes: epochs 5..30 inclusive = 26 encodes * 6 min = 2.6h
    assert pr["hn_refreshes"] == 26 and abs(pr["hn_refresh_h"] - 2.6) < 1e-6, pr
    # validation 30 * 2 min = 1h ; eval 3 views * (6+3) = 27 min = 0.45h
    assert abs(pr["valid_h"] - 1.0) < 1e-6 and abs(pr["eval_four_view_h"] - 0.45) < 1e-6, pr
    assert abs(pr["total_h"] - (15.0 + 2.6 + 1.0 + 0.45)) < 1e-6, pr
    # plan arithmetic: base = total * runs * encoders; extras added on top
    p = plan_cost(pr, 5, encoders=["a", "b"], fail=0.2, confirm=0.25)
    base = pr["total_h"] * 5 * 2
    assert abs(p["base_h"] - round(base, 1)) < 0.05, p
    assert abs(p["total_h"] - round(base * 1.45, 1)) < 0.05, p
    # eval cost must scale with the number of views
    assert per_run_hours(30, 6, 2, 3, n_views=1)["eval_four_view_h"] < pr["eval_four_view_h"]
    print("estimate_phase2_budget self-check OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=None, help="run manifest with metrics.profile")
    ap.add_argument("--epoch-min", type=float, default=None)
    ap.add_argument("--encode-min", type=float, default=None)
    ap.add_argument("--valid-min", type=float, default=None)
    ap.add_argument("--eval-min", type=float, default=12.0,
                    help="one head+tail ranking pass over a fold's targets (minutes)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        _selfcheck(); sys.exit(0)

    epoch_min, encode_min, valid_min = a.epoch_min, a.encode_min, a.valid_min
    if a.manifest:
        m = json.load(open(a.manifest))
        p = (m.get("metrics") or {}).get("profile") or {}
        n_ep = max(p.get("epochs_run", 1), 1)
        # train_seconds excludes encode+validation (see trainer profiling)
        epoch_min = epoch_min or round(p["train_seconds"] / n_ep / 60.0, 2)
        # encode_seconds covers the HN refreshes performed in this run
        n_enc = max(n_ep - HN_START_EPOCH + 1, 1) if n_ep >= HN_START_EPOCH else 1
        encode_min = encode_min or round(p.get("encode_seconds", 0) / n_enc / 60.0, 2)
        valid_min = valid_min or round(p["validation_seconds"] / n_ep / 60.0, 2)
        print(f"# from {a.manifest}: peak_vram={p.get('peak_vram_gb')}GB "
              f"wall={p.get('wall_hours')}h epochs={n_ep}")
    if None in (epoch_min, encode_min, valid_min):
        ap.error("provide --manifest or all of --epoch-min/--encode-min/--valid-min")
    print(json.dumps(report(epoch_min, encode_min, valid_min, a.eval_min), indent=2))
