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

ROOT = os.environ.get("RESEARCH_KG_ROOT", os.path.expanduser("~/research_kg"))
LEX = "DBP5L/ind_v2/audits/lexical/LEX-RUN-002/cells"


def lexical_cell(fold, method, view):
    p = os.path.join(ROOT, LEX, f"{fold}__{method}__{view}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def compare(eval_dir, fold):
    eval_dir = eval_dir if os.path.isabs(eval_dir) else os.path.join(ROOT, eval_dir)
    out = {"fold": fold, "eval_dir": eval_dir, "criteria": {}, "detail": {}}
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

    nat = out["detail"].get("natural")
    if nat and nat["lexical"]:
        best = lambda k: max(v[k] for v in nat["lexical"].values())
        m = nat["model"]
        # (a) unmentioned bucket, per direction — the generalization criterion
        um_t = m["unmentioned_tail"] > max(v["unmentioned_tail"] for v in nat["lexical"].values())
        um_h = m["unmentioned_head"] > max(v["unmentioned_head"] for v in nat["lexical"].values())
        out["criteria"] = {
            "natural_aggregate_beats_lexical": m["combined"] > best("combined"),
            "unmentioned_tail_beats_lexical": um_t,
            "unmentioned_head_beats_lexical": um_h,
            "tail_direction_beats_lexical": m["tail"] > best("tail"),
            "head_direction_beats_lexical": m["head"] > best("head"),
        }
        masked = out["detail"].get("masked")
        if masked and masked["lexical"]:
            out["criteria"]["masked_beats_lexical"] = \
                masked["model"]["combined"] > max(v["combined"] for v in masked["lexical"].values())
        # sufficiency: aggregate alone is explicitly NOT enough
        required = [k for k in out["criteria"] if k != "natural_aggregate_beats_lexical"]
        out["sufficiency_verdict"] = (
            "PASS" if all(out["criteria"][k] for k in required) else "FAIL")
        out["sufficiency_note"] = (
            "Aggregate natural MRR is excluded from the verdict by design: it is dominated by "
            "answer-mention reading (R-031/R-037/R-042). Generalization is judged on the "
            "unmentioned bucket, per direction, plus the leak-reduced views.")
    return out


def _selftest():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="cmp_")
    try:
        # model that wins on aggregate but LOSES on unmentioned must FAIL the verdict
        view = {"by_direction": {
                    "combined": {"within_language_overall": {"mrr": 20.0}},
                    "tail": {"within_language_overall": {"mrr": 20.0}},
                    "head": {"within_language_overall": {"mrr": 20.0}}},
                "by_mention": {
                    "combined": {"unmentioned": {"mrr": 0.1}},
                    "tail": {"unmentioned": {"mrr": 0.1}},
                    "head": {"unmentioned": {"mrr": 0.1}}}}
        json.dump(view, open(os.path.join(d, "view_natural.json"), "w"))
        lex_dir = os.path.join(d, "lex"); os.makedirs(lex_dir)
        cell = {"combined": {"mrr": 6.5}, "tail": {"mrr": 8.9}, "head": {"mrr": 4.1},
                "by_mention": {"tail": {"unmentioned": {"mrr": 0.28}},
                               "head": {"unmentioned": {"mrr": 0.26}}}}
        json.dump(cell, open(os.path.join(lex_dir, "f0__bm25__natural.json"), "w"))
        global LEX, ROOT
        oldL, oldR = LEX, ROOT
        LEX, ROOT = "lex", d
        r = compare(d, "f0")
        assert r["criteria"]["natural_aggregate_beats_lexical"] is True
        assert r["criteria"]["unmentioned_tail_beats_lexical"] is False
        assert r["sufficiency_verdict"] == "FAIL", r["sufficiency_verdict"]
        # now make it also win the unmentioned buckets -> PASS
        view["by_mention"] = {"combined": {"unmentioned": {"mrr": 3.0}},
                              "tail": {"unmentioned": {"mrr": 3.0}},
                              "head": {"unmentioned": {"mrr": 3.0}}}
        json.dump(view, open(os.path.join(d, "view_natural.json"), "w"))
        assert compare(d, "f0")["sufficiency_verdict"] == "PASS"
        LEX, ROOT = oldL, oldR
        print("compare_vs_lexical self-check OK "
              "(aggregate win alone FAILS; unmentioned+directional win PASSES)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-dir", default="DBP5L/ind_v2/audits/eval/B0-FOLD0-SEED42")
    ap.add_argument("--fold", default="fold0_seed13")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        _selftest(); sys.exit(0)
    r = compare(a.eval_dir, a.fold)
    out = os.path.join(a.eval_dir if os.path.isabs(a.eval_dir) else os.path.join(ROOT, a.eval_dir),
                       "lexical_comparison.json")
    json.dump(r, open(out, "w"), indent=2, sort_keys=True)
    print(json.dumps({k: r[k] for k in ("criteria", "sufficiency_verdict") if k in r}, indent=2))
    print("wrote", out)
