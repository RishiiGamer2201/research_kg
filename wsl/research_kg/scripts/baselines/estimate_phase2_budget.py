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
# THREE encoded evaluation views. mentioned/unmentioned is a zero-cost partition of the
# natural-view ranks (same forward passes, just bucketed), so it is NOT a fourth encode.
N_VIEWS = 3
ENCODED_VIEWS = ["natural", "masked", "missing"]
FAIL_ALLOWANCE = 0.20       # 20% for crashes/OOM/restarts
CONFIRM_FRACTION = 0.25     # re-run 25% of runs for confirmation/paired checks

# Per-encoder relative cost vs the measured B0 (BGE-M3 + LoRA) reference.
# 'measured' entries come from a profiling run; 'assumed' entries are placeholders that MUST
# be replaced by measurement before they are used for a final budget decision.
ENCODER_COST_FACTORS = {
    "bge-m3-lora(B0)": {"factor": 1.00, "basis": "measured (this profile)"},
    # historical substrate: mBERT ~3.1 GPU-h/seed vs BGE ~9-10 -> ~0.33x
    "mbert":           {"factor": 0.33, "basis": "assumed from historical R-007 ratio"},
    # XLM-R base is ~ mBERT-scale but with a larger vocab/embedding table
    "xlm-r":           {"factor": 0.40, "basis": "assumed (xlm-r base, larger vocab)"},
}


def per_run_hours(epoch_min, encode_min, valid_min, eval_min,
                  epochs=EPOCHS, hn_start=HN_START_EPOCH, n_views=N_VIEWS, factor=1.0):
    """Cost of ONE run for one encoder. `factor` scales all GPU work for non-reference encoders."""
    train_h = epochs * epoch_min * factor / 60.0
    # HN cache refresh: one entity-encode per epoch from hn_start onwards
    hn_refreshes = max(epochs - hn_start + 1, 0)
    hn_h = hn_refreshes * encode_min * factor / 60.0
    valid_h = epochs * valid_min * factor / 60.0
    # evaluation: each ENCODED view needs its own entity encode + head&tail ranking pass.
    # mentioned/unmentioned adds nothing: it partitions the natural-view ranks.
    eval_h = n_views * (encode_min + eval_min) * factor / 60.0
    return {"train_h": round(train_h, 2), "hn_refresh_h": round(hn_h, 2),
            "valid_h": round(valid_h, 2), "eval_h_encoded_views": round(eval_h, 2),
            "encoded_views": n_views, "mention_partition_extra_h": 0.0,
            "total_h": round(train_h + hn_h + valid_h + eval_h, 2),
            "hn_refreshes": hn_refreshes, "cost_factor": factor}


def plan_cost(epoch_min, encode_min, valid_min, eval_min, runs_per_encoder,
              encoder_factors=None, fail=FAIL_ALLOWANCE, confirm=CONFIRM_FRACTION):
    """Per-encoder subtotals kept SEPARATE, then summed — encoders are not equal cost."""
    encoder_factors = encoder_factors or ENCODER_COST_FACTORS
    per_encoder = {}
    for name, meta in encoder_factors.items():
        pr = per_run_hours(epoch_min, encode_min, valid_min, eval_min, factor=meta["factor"])
        per_encoder[name] = {"cost_factor": meta["factor"], "basis": meta["basis"],
                             "per_run_h": pr["total_h"], "runs": runs_per_encoder,
                             "subtotal_h": round(pr["total_h"] * runs_per_encoder, 1),
                             "breakdown_per_run": pr}
    # base is the sum of the REPORTED subtotals so the published table is internally consistent
    base = round(sum(e["subtotal_h"] for e in per_encoder.values()), 1)
    return {"runs_per_encoder": runs_per_encoder,
            "per_encoder": per_encoder,
            "base_h": base,
            "failed_run_allowance_h": round(base * fail, 1),
            "confirmation_rerun_h": round(base * confirm, 1),
            "total_h": round(base * (1 + fail + confirm), 1),
            "total_days_at_20h": round(base * (1 + fail + confirm) / 20.0, 1)}


def report(epoch_min, encode_min, valid_min, eval_min):
    return {
        "measured_inputs_min": {"epoch": epoch_min, "encode_hn_refresh": encode_min,
                                "validation_per_epoch": valid_min, "eval_pass_per_view": eval_min},
        "accounting": {
            "encoded_evaluation_views": ENCODED_VIEWS,
            "mentioned_unmentioned": "zero-cost partition of the natural-view ranks (no extra encode)",
            "hn_refreshes_per_run": max(EPOCHS - HN_START_EPOCH + 1, 0),
            "failed_run_allowance": FAIL_ALLOWANCE,
            "confirmation_fraction": CONFIRM_FRACTION,
        },
        "reference_per_run_B0": per_run_hours(epoch_min, encode_min, valid_min, eval_min),
        "plans": {
            "fallback_3folds_plus_3seeds": plan_cost(epoch_min, encode_min, valid_min, eval_min, 5),
            "full_3x3": plan_cost(epoch_min, encode_min, valid_min, eval_min, 9),
        },
    }


def _selfcheck():
    pr = per_run_hours(epoch_min=30, encode_min=6, valid_min=2, eval_min=3)
    # 30 epochs * 30 min = 15h train
    assert abs(pr["train_h"] - 15.0) < 1e-6, pr
    # HN refreshes: epochs 5..30 inclusive = 26 encodes * 6 min = 2.6h
    assert pr["hn_refreshes"] == 26 and abs(pr["hn_refresh_h"] - 2.6) < 1e-6, pr
    # validation 30 * 2 min = 1h ; eval 3 views * (6+3) = 27 min = 0.45h
    assert abs(pr["valid_h"] - 1.0) < 1e-6 and abs(pr["eval_h_encoded_views"] - 0.45) < 1e-6, pr
    assert abs(pr["total_h"] - (15.0 + 2.6 + 1.0 + 0.45)) < 1e-6, pr
    # three encoded views; mentioned/unmentioned adds nothing
    assert pr["encoded_views"] == 3 and pr["mention_partition_extra_h"] == 0.0, pr
    assert abs(per_run_hours(30, 6, 2, 3, n_views=1)["eval_h_encoded_views"] - 0.15) < 1e-6

    # per-encoder costs stay SEPARATE and scale by factor (encoders are not equal cost)
    facs = {"big": {"factor": 1.0, "basis": "measured"},
            "small": {"factor": 0.5, "basis": "assumed"}}
    p = plan_cost(30, 6, 2, 3, 5, encoder_factors=facs, fail=0.2, confirm=0.25)
    big = p["per_encoder"]["big"]["subtotal_h"]; small = p["per_encoder"]["small"]["subtotal_h"]
    assert abs(small - big / 2) < 0.05, (big, small)          # halved cost -> halved subtotal
    assert abs(p["base_h"] - round(big + small, 1)) < 0.05, p  # subtotals sum to base
    assert abs(p["total_h"] - round((big + small) * 1.45, 1)) < 0.05, p
    # a naive equal-cost model would over-count: verify we are NOT doing that
    assert p["base_h"] < big * 2, "per-encoder factors not applied"
    print("estimate_phase2_budget self-check OK (3 encoded views; per-encoder costs separate)")


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
