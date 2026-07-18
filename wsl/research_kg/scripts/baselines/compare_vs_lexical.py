"""Phase 2 — compare a trained model against the R-042 lexical floor.

Enforces the sufficiency rule from docs/PHASE2_BASELINE_MATRIX.md §4b: beating the lexical
baselines on natural aggregate MRR is NOT sufficient. A neural model must also beat them

  (a) on the UNMENTIONED bucket — the relational-generalization indicator,
  (b) in BOTH directions separately, and
  (c) on the leak-reduced views (alias-masked is a stress diagnostic, missing-text a floor).

Emits a verdict per criterion plus an overall PASS/FAIL, so "beats BM25 on natural MRR" can
never be reported as generalization on its own.

Usage: python3 compare_vs_lexical.py --eval-dir <audits/eval/ID> [--fold fold0_seed13]
Self-check: `python3 compare_vs_lexical.py --selftest`
"""
import os
import sys
import json
import argparse

import numpy as np

ROOT = os.environ.get("RESEARCH_KG_ROOT", os.path.expanduser("~/research_kg"))
LEX_RUN = "DBP5L/ind_v2/audits/lexical/LEX-RUN-003"
LEX = LEX_RUN + "/cells"
N_BOOT = 2000
BOOT_SEED = 20260718
PRACTICAL_MARGIN = 0.0      # predeclared margin (MRR points) the lower bound must exceed


def _key(row):
    """Alignment key: query id x direction. Both sides must agree exactly."""
    return (int(row["h"]), int(row["r"]), int(row["t"]), row["direction"])


def paired_bootstrap(model_rows, lex_rows, margin=PRACTICAL_MARGIN, n_boot=N_BOOT,
                     seed=BOOT_SEED):
    """Paired bootstrap over per-query reciprocal-rank differences (model - lexical).

    Asserts exact query-ID x direction alignment before pairing: a silent mismatch would
    compare different queries and invent a difference.
    """
    m = {_key(r): float(r["rr"]) for r in model_rows}
    l = {_key(r): float(r["rr"]) for r in lex_rows}
    only_m, only_l = set(m) - set(l), set(l) - set(m)
    if only_m or only_l:
        raise AssertionError(
            f"rank-dump misalignment: {len(only_m)} query/direction keys only in the model dump, "
            f"{len(only_l)} only in the lexical dump (e.g. {list(only_m)[:2] or list(only_l)[:2]}). "
            f"Paired comparison requires identical query sets.")
    keys = sorted(m)
    if not keys:
        return None
    d = np.array([m[k] - l[k] for k in keys], dtype=np.float64) * 100.0   # MRR points
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    boots = d[idx].mean(axis=1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n_paired": len(keys), "mean_diff_mrr_points": round(float(d.mean()), 4),
            "ci95_low": round(float(lo), 4), "ci95_high": round(float(hi), 4),
            "margin": margin, "n_boot": n_boot,
            "significant": bool(lo > margin)}


def lexical_cell(fold, method, view):
    p = os.path.join(ROOT, LEX, f"{fold}__{method}__{view}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def compare(eval_dir, fold, margin=PRACTICAL_MARGIN):
    eval_dir = eval_dir if os.path.isabs(eval_dir) else os.path.join(ROOT, eval_dir)
    out = {"fold": fold, "eval_dir": eval_dir, "criteria": {}, "detail": {},
           "practical_margin_mrr_points": margin}
    meta_p = os.path.join(eval_dir, "evaluated_checkpoint.json")
    if os.path.exists(meta_p):
        out["evaluated_checkpoint"] = json.load(open(meta_p))

    for view in ("natural", "masked", "missing"):
        vp = os.path.join(eval_dir, f"view_{view}.json")
        if not os.path.exists(vp):
            continue
        v = json.load(open(vp))
        bd, bm = v["by_direction"], v["by_mention"]
        row = {"model": {
            "combined": bd["combined"]["within_language_overall"]["mrr"],
            "tail": bd["tail"]["within_language_overall"]["mrr"],
            "head": bd["head"]["within_language_overall"]["mrr"],
            "unmentioned_combined": bm["combined"]["unmentioned"]["mrr"],
            "unmentioned_tail": bm["tail"]["unmentioned"]["mrr"],
            "unmentioned_head": bm["head"]["unmentioned"]["mrr"],
        }, "lexical": {}}
        for method in ("name_match", "bm25"):
            c = lexical_cell(fold, method, view)
            if not c:
                continue
            row["lexical"][method] = {
                "combined": c["combined"]["mrr"], "tail": c["tail"]["mrr"], "head": c["head"]["mrr"],
                "unmentioned_tail": c["by_mention"]["tail"]["unmentioned"]["mrr"],
                "unmentioned_head": c["by_mention"]["head"]["unmentioned"]["mrr"],
            }
        out["detail"][view] = row

    # ── paired bootstrap over per-query reciprocal-rank differences ──────────────
    # A point-estimate win does NOT authorize the remaining matrix: the lower confidence
    # bound must exceed the predeclared margin. Missing dumps -> INCONCLUSIVE, never PASS.
    tests, errors = {}, []
    for view in ("natural", "masked", "missing"):
        vp = os.path.join(eval_dir, f"view_{view}.json")
        if not os.path.exists(vp):
            continue
        v = json.load(open(vp))
        dump = v.get("rank_dump")
        if not dump or not os.path.exists(dump):
            errors.append(f"{view}: model rank dump missing"); continue
        model_rows = json.load(open(dump))
        for method in ("name_match", "bm25"):
            cell = lexical_cell(fold, method, view)
            if not cell or not cell.get("rank_dump"):
                errors.append(f"{view}/{method}: lexical rank dump missing"); continue
            lex_rows = json.load(open(os.path.join(ROOT, LEX_RUN, cell["rank_dump"])))
            for bucket, pred in (("unmentioned_tail", lambda r: r["direction"] == "tail" and not r["mentioned"]),
                                 ("unmentioned_head", lambda r: r["direction"] == "head" and not r["mentioned"]),
                                 ("all_tail", lambda r: r["direction"] == "tail"),
                                 ("all_head", lambda r: r["direction"] == "head")):
                try:
                    res = paired_bootstrap([r for r in model_rows if pred(r)],
                                           [r for r in lex_rows if pred(r)], margin)
                except AssertionError as e:
                    errors.append(f"{view}/{method}/{bucket}: {e}"); continue
                if res:
                    tests[f"{view}|{method}|{bucket}"] = res
    out["paired_tests"] = tests
    out["errors"] = errors

    # required: BOTH unmentioned directions on natural, and the leak-reduced views,
    # significant against EVERY lexical method.
    required = [k for k in tests
                if (k.split("|")[0] == "natural" and k.split("|")[2].startswith("unmentioned"))
                or (k.split("|")[0] in ("masked", "missing") and k.split("|")[2].startswith("all"))]
    out["required_tests"] = sorted(required)
    if errors or not required:
        out["sufficiency_verdict"] = "INCONCLUSIVE"
        out["verdict_reason"] = (errors or ["no required paired tests could be computed"])[:5]
    elif all(tests[k]["significant"] for k in required):
        out["sufficiency_verdict"] = "PASS"
        out["verdict_reason"] = ["all required lower CI bounds exceed the margin"]
    else:
        failed = [k for k in required if not tests[k]["significant"]]
        out["sufficiency_verdict"] = "FAIL"
        out["verdict_reason"] = [f"lower CI bound does not exceed margin: {k} "
                                 f"(lo={tests[k]['ci95_low']})" for k in failed[:5]]
    out["sufficiency_note"] = (
        "Verdict is PASS/FAIL/INCONCLUSIVE from PAIRED BOOTSTRAP lower confidence bounds, not "
        "point estimates. Natural aggregate MRR is excluded by design (dominated by "
        "answer-mention reading, R-031/R-037/R-042). Query-ID x direction alignment between "
        "the model and lexical rank dumps is asserted before pairing.")
    return out


def _selftest():
    # alignment assertion
    a = [{"h": 1, "r": 2, "t": 3, "direction": "tail", "rr": 0.5}]
    b = [{"h": 1, "r": 2, "t": 9, "direction": "tail", "rr": 0.1}]
    try:
        paired_bootstrap(a, b); raise SystemExit("expected misalignment AssertionError")
    except AssertionError as e:
        assert "misalignment" in str(e)
    print("PASS query-ID/direction misalignment is refused")

    # clear win -> significant
    rng = np.random.default_rng(0)
    keys = [{"h": i, "r": 0, "t": i + 1, "direction": "tail"} for i in range(400)]
    m = [{**k, "rr": float(v)} for k, v in zip(keys, rng.uniform(0.30, 0.50, 400))]
    l = [{**k, "rr": float(v)} for k, v in zip(keys, rng.uniform(0.00, 0.05, 400))]
    r = paired_bootstrap(m, l)
    assert r["significant"] and r["ci95_low"] > 0, r
    print(f"PASS clear win significant (mean {r['mean_diff_mrr_points']:.2f}, lo {r['ci95_low']:.2f})")

    # tiny/noisy win -> lower bound must NOT clear zero
    m2 = [{**k, "rr": float(v)} for k, v in zip(keys, rng.normal(0.20, 0.30, 400).clip(0, 1))]
    l2 = [{**k, "rr": float(v)} for k, v in zip(keys, rng.normal(0.199, 0.30, 400).clip(0, 1))]
    r2 = paired_bootstrap(m2, l2)
    assert not r2["significant"], r2
    print(f"PASS noisy point-estimate win NOT significant (mean {r2['mean_diff_mrr_points']:.3f}, "
          f"lo {r2['ci95_low']:.3f})")

    # predeclared practical margin can flip a statistically-significant but tiny win
    r3 = paired_bootstrap(m, l, margin=100.0)
    assert not r3["significant"], r3
    print("PASS practical margin enforced")

    # missing dumps -> INCONCLUSIVE, never PASS
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="cmp_")
    try:
        json.dump({"by_direction": {"combined": {"within_language_overall": {"mrr": 20.0}},
                                    "tail": {"within_language_overall": {"mrr": 20.0}},
                                    "head": {"within_language_overall": {"mrr": 20.0}}},
                   "by_mention": {"combined": {"unmentioned": {"mrr": 9.0}},
                                  "tail": {"unmentioned": {"mrr": 9.0}},
                                  "head": {"unmentioned": {"mrr": 9.0}}}},
                  open(os.path.join(d, "view_natural.json"), "w"))
        v = compare(d, "f0")
        assert v["sufficiency_verdict"] == "INCONCLUSIVE", v["sufficiency_verdict"]
        print("PASS missing rank dumps -> INCONCLUSIVE (a huge point win cannot authorize)")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("compare_vs_lexical self-check OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-dir", default="DBP5L/ind_v2/audits/eval/B0-FOLD0-SEED42")
    ap.add_argument("--fold", default="fold0_seed13")
    ap.add_argument("--margin", type=float, default=PRACTICAL_MARGIN,
                    help="predeclared practical margin in MRR points that the lower CI bound "
                         "must exceed (default 0.0 = strictly greater than zero)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        _selftest(); sys.exit(0)
    r = compare(a.eval_dir, a.fold, a.margin)
    out = os.path.join(a.eval_dir if os.path.isabs(a.eval_dir) else os.path.join(ROOT, a.eval_dir),
                       "lexical_comparison.json")
    json.dump(r, open(out, "w"), indent=2, sort_keys=True)
    print(json.dumps({"sufficiency_verdict": r.get("sufficiency_verdict"),
                      "verdict_reason": r.get("verdict_reason"),
                      "required_tests": r.get("required_tests")}, indent=2))
    print("wrote", out)
    # non-zero exit on anything but PASS, so a driver cannot proceed on FAIL/INCONCLUSIVE
    sys.exit(0 if r.get("sufficiency_verdict") == "PASS" else 1)
