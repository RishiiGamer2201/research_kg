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


def _query_entity(row):
    """The entity whose DESCRIPTION the model reads for this query.
    tail prediction (h,r,?) reads desc(h); head prediction (?,r,t) reads desc(t)."""
    return int(row["h"]) if row["direction"] == "tail" else int(row["t"])


def load_entity2concept():
    p = os.path.join(ROOT, "DBP5L/ind_v2/concepts/entity2concept.json")
    if not os.path.exists(p):
        return None
    return {int(k): int(v) for k, v in json.load(open(p)).items()}


def cluster_bootstrap(model_rows, lex_rows, e2c, margin=PRACTICAL_MARGIN, n_boot=N_BOOT,
                      seed=BOOT_SEED):
    """PRIMARY test: bootstrap over CONCEPT CLUSTERS, not individual queries.

    Queries that share a source concept reuse the same description, so their reciprocal-rank
    differences are correlated; a per-query bootstrap understates the variance and produces
    over-narrow intervals. Here whole concepts are resampled with replacement, carrying ALL of
    their queries, which respects that correlation.

    Clustering follows the description the model actually reads:
      tail prediction -> cluster by the HEAD/query concept
      head prediction -> cluster by the TAIL/query concept
    """
    m = {_key(r): (float(r["rr"]), _query_entity(r)) for r in model_rows}
    l = {_key(r): float(r["rr"]) for r in lex_rows}
    only_m, only_l = set(m) - set(l), set(l) - set(m)
    if only_m or only_l:
        raise AssertionError(
            f"rank-dump misalignment: {len(only_m)} keys only in model, {len(only_l)} only in "
            f"lexical. Paired comparison requires identical query sets.")
    by_concept = {}
    unmapped = 0
    for k, (rr, qent) in m.items():
        c = e2c.get(qent)
        if c is None:
            unmapped += 1
            continue
        by_concept.setdefault(c, []).append((rr - l[k]) * 100.0)
    if not by_concept:
        return None
    concepts = sorted(by_concept)
    sums = np.array([sum(by_concept[c]) for c in concepts], dtype=np.float64)
    counts = np.array([len(by_concept[c]) for c in concepts], dtype=np.float64)
    # PRIMARY (matches the query-weighted MRR estimand): ratio estimator
    point = float(sums.sum() / counts.sum())
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(concepts), size=(n_boot, len(concepts)))
    boots = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
    lo, hi = np.percentile(boots, [2.5, 97.5])

    # SECONDARY robustness: concept-macro mean — every concept weighted equally, so a few
    # high-degree concepts cannot carry the result. Diverging from the ratio estimate signals
    # that the effect is concentrated in heavily-queried concepts.
    per_concept_mean = sums / counts
    macro_point = float(per_concept_mean.mean())
    macro_boots = per_concept_mean[idx].mean(axis=1)
    m_lo, m_hi = np.percentile(macro_boots, [2.5, 97.5])

    q = lambda p: float(np.percentile(counts, p))
    return {"unit": "concept cluster", "n_clusters": len(concepts),
            "n_unique_concepts": len(concepts),
            "n_queries": int(counts.sum()), "unmapped_queries": unmapped,
            "cluster_size_distribution": {
                "min": int(counts.min()), "p25": q(25), "median": q(50), "p75": q(75),
                "p95": q(95), "max": int(counts.max()),
                "mean": round(float(counts.mean()), 3)},
            "mean_diff_mrr_points": round(point, 4),
            "ci95_low": round(float(lo), 4), "ci95_high": round(float(hi), 4),
            "concept_macro_mean_diff_mrr_points": round(macro_point, 4),
            "concept_macro_ci95_low": round(float(m_lo), 4),
            "concept_macro_ci95_high": round(float(m_hi), 4),
            "concept_macro_significant": bool(m_lo > margin),
            "margin": margin, "n_boot": n_boot,
            "significant": bool(lo > margin),
            "evidence_against": bool(hi < margin)}


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
    tests, diag, errors = {}, {}, []
    e2c = load_entity2concept()
    if e2c is None:
        errors.append("entity2concept.json missing — the primary concept-cluster test cannot run")
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
                mrows = [r for r in model_rows if pred(r)]
                lrows = [r for r in lex_rows if pred(r)]
                name = f"{view}|{method}|{bucket}"
                try:
                    d = paired_bootstrap(mrows, lrows, margin)      # diagnostic (per query)
                    if d:
                        diag[name] = d
                    if e2c is not None:
                        c = cluster_bootstrap(mrows, lrows, e2c, margin)   # PRIMARY
                        if c:
                            tests[name] = c
                except AssertionError as e:
                    errors.append(f"{name}: {e}"); continue
    out["primary_tests_concept_clustered"] = tests
    out["diagnostic_tests_per_query"] = diag
    out["errors"] = errors

    # required: BOTH unmentioned directions on natural, and the leak-reduced views,
    # significant against EVERY lexical method.
    required = [k for k in tests
                if (k.split("|")[0] == "natural" and k.split("|")[2].startswith("unmentioned"))
                or (k.split("|")[0] in ("masked", "missing") and k.split("|")[2].startswith("all"))]
    out["required_tests"] = sorted(required)
    if errors or not required:
        out["sufficiency_verdict"] = "INCONCLUSIVE"
        out["verdict_reason"] = (errors or ["no required concept-clustered tests could be computed"])[:5]
    elif all(tests[k]["significant"] for k in required):
        out["sufficiency_verdict"] = "PASS"
        out["verdict_reason"] = ["all required concept-clustered lower CI bounds exceed the margin"]
    elif any(tests[k].get("evidence_against") for k in required):
        against = [k for k in required if tests[k].get("evidence_against")]
        out["sufficiency_verdict"] = "FAIL"
        out["verdict_reason"] = [f"upper CI bound below margin (model worse): {k} "
                                 f"(hi={tests[k]['ci95_high']})" for k in against[:5]]
    else:
        straddle = [k for k in required if not tests[k]["significant"]]
        out["sufficiency_verdict"] = "INCONCLUSIVE"
        out["verdict_reason"] = [f"clustered CI straddles the margin: {k} "
                                 f"(lo={tests[k]['ci95_low']}, hi={tests[k]['ci95_high']})"
                                 for k in straddle[:5]]
    out["sufficiency_note"] = (
        "PRIMARY test is a CONCEPT-CLUSTER bootstrap: queries sharing a source concept reuse "
        "the same description and are correlated, so whole concepts are resampled with all "
        "their queries (tail prediction clusters by head/query concept, head prediction by "
        "tail/query concept). The per-query bootstrap is retained as a DIAGNOSTIC only and "
        "never decides the verdict. PASS requires the clustered lower bound to exceed the "
        "predeclared margin; a CI straddling the margin is INCONCLUSIVE (insufficient "
        "evidence), and only an upper bound below the margin is FAIL (evidence against). "
        "Natural aggregate MRR is excluded by design (answer-mention reading, R-031/R-037/R-042).")
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

    # ── concept-cluster bootstrap ────────────────────────────────────────────
    # 40 concepts x 20 queries each. Within a concept every query shares the SAME difference
    # (perfectly correlated, the worst case): the per-query bootstrap sees 800 "independent"
    # points and reports a narrow CI, while the clustered bootstrap correctly sees only 40.
    rows_m, rows_l, e2c = [], [], {}
    conc = rng.normal(0.02, 0.30, 40)          # per-concept effect, mean small vs its spread
    for ci in range(40):
        for qi in range(20):
            ent = 1000 * ci + qi
            k = {"h": ent, "r": 0, "t": 999999 + ent, "direction": "tail", "mentioned": False}
            rows_m.append({**k, "rr": 0.30 + float(conc[ci])})
            rows_l.append({**k, "rr": 0.30})
            e2c[ent] = ci
    pq = paired_bootstrap(rows_m, rows_l)
    cl = cluster_bootstrap(rows_m, rows_l, e2c)
    assert cl["n_clusters"] == 40 and cl["n_queries"] == 800, cl
    width_pq = pq["ci95_high"] - pq["ci95_low"]
    width_cl = cl["ci95_high"] - cl["ci95_low"]
    assert width_cl > width_pq * 2, (width_pq, width_cl)
    print(f"PASS clustered CI is wider than per-query ({width_cl:.2f} vs {width_pq:.2f} pts) "
          "— correlation within concepts respected")
    assert pq["significant"] and not cl["significant"], (pq["significant"], cl["significant"])
    print("PASS per-query would authorize, clustered does NOT (verdict follows clustered)")
    # clustering key: head prediction must cluster by the TAIL entity
    hr = {"h": 5, "r": 1, "t": 7, "direction": "head", "mentioned": False, "rr": 0.5}
    assert _query_entity(hr) == 7 and _query_entity({**hr, "direction": "tail"}) == 5
    print("PASS cluster key follows the description actually read (tail->head ent, head->tail ent)")

    # cluster-size distribution is reported, and macro vs ratio DIVERGE when the effect is
    # concentrated in heavily-queried concepts (exactly the case macro is meant to expose).
    rm, rl, e2 = [], [], {}
    for ci in range(30):
        size = 50 if ci < 5 else 2            # 5 big concepts, 25 small ones
        eff = 0.40 if ci < 5 else 0.0         # the gain lives only in the big concepts
        for qi in range(size):
            ent = 10000 * ci + qi
            k = {"h": ent, "r": 0, "t": 500000 + ent, "direction": "tail", "mentioned": False}
            rm.append({**k, "rr": 0.20 + eff}); rl.append({**k, "rr": 0.20}); e2[ent] = ci
    cs = cluster_bootstrap(rm, rl, e2)
    d = cs["cluster_size_distribution"]
    assert cs["n_unique_concepts"] == 30 and d["max"] == 50 and d["min"] == 2, (cs["n_unique_concepts"], d)
    # ratio is query-weighted (big concepts dominate) -> high; macro weights concepts equally -> low
    assert cs["mean_diff_mrr_points"] > 3 * cs["concept_macro_mean_diff_mrr_points"], \
        (cs["mean_diff_mrr_points"], cs["concept_macro_mean_diff_mrr_points"])
    print(f"PASS size distribution reported (min {d['min']}, median {d['median']}, max {d['max']}); "
          f"ratio {cs['mean_diff_mrr_points']:.2f} vs concept-macro "
          f"{cs['concept_macro_mean_diff_mrr_points']:.2f} — concentration exposed")

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
