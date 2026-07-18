"""DBP5L-Ind v2 / P1.7 — answer-mention leakage audit (snapshot text kept verbatim).

P1.5 deliberately preserved snapshot text instead of stripping answer mentions; this
quantifies the leakage so it is explicit, not hidden. For each eval-target triple (h,r,t):
  * tail direction: the model reads desc(h); the answer is t  -> leak if desc(h) mentions t.
  * head direction: the model reads desc(t); the answer is h  -> leak if desc(t) mentions h.

Two signals (both on NFC-normalized, lowercased text):
  exact        : the answer's full name appears as a substring of the query description.
  token_subset : every token of the answer name appears in the query description (a looser,
                 "semantic-ish" mention that survives reordering / extra words).

Broken down by direction, language (of the query entity whose text is read), and description
source (native / cross_lang / name). Run on BOTH the primary alignment-free view and the
oracle view. Very short answer names (<= 2 chars / purely numeric) are counted separately as
`trivial_name` because they cause spurious substring hits.

Self-check: `python3 audit_v2_answer_leakage.py --selftest`.
"""
import os
import sys
import json
import time
import hashlib
import unicodedata
import argparse
from collections import defaultdict


def _norm(s):
    return " ".join(unicodedata.normalize("NFC", (s or "")).lower().split())


def _toks(s):
    return set(_norm(s).split())


def _load(root):
    proc = os.path.join(root, "DBP5L/processed")
    with open(os.path.join(proc, "entities.json")) as f:
        ents = {int(g): e for g, e in json.load(f).items()}
    gid_lang = {g: e["lang"] for g, e in ents.items()}
    gid_name = {g: _norm(e.get("name") or "") for g, e in ents.items()}
    with open(os.path.join(root, "DBP5L/ind_v2/descriptions/descriptions_v2_provenance.json")) as f:
        source = {int(g): p["source"] for g, p in json.load(f).items()}
    views = {}
    with open(os.path.join(root, "DBP5L/ind_v2/descriptions/descriptions_v2.json")) as f:
        views["oracle"] = {int(g): _norm(v) for g, v in json.load(f).items()}
    with open(os.path.join(root, "DBP5L/ind_v2/tracks/descriptions_v2_primary.json")) as f:
        views["primary"] = {int(g): _norm(v) for g, v in json.load(f).items()}
    return ents, gid_lang, gid_name, source, views


def _leak(desc, ans_name, ans_toks):
    if not ans_name:
        return False, False
    exact = ans_name in desc
    subset = bool(ans_toks) and ans_toks.issubset(set(desc.split()))
    return exact, subset


def audit_fold(targets, gid_lang, gid_name, source, view_desc):
    # strata[(direction, lang, src)] = counters
    strata = defaultdict(lambda: {"n": 0, "exact": 0, "subset": 0, "trivial": 0})
    tot = {"n": 0, "exact": 0, "subset": 0, "trivial": 0}
    for h, r, t in targets:
        for direction, q, ans in (("tail", h, t), ("head", t, h)):
            desc = view_desc.get(q, "")
            ans_name = gid_name.get(ans, "")
            trivial = len(ans_name) <= 2 or ans_name.isdigit()
            exact, subset = _leak(desc, ans_name, _toks(ans_name))
            key = (direction, gid_lang.get(q, "?"), source.get(q, "?"))
            for bucket in (strata[key], tot):
                bucket["n"] += 1
                if trivial:
                    bucket["trivial"] += 1
                else:
                    bucket["exact"] += int(exact)
                    bucket["subset"] += int(subset)
    return strata, tot


def _rate(c):
    denom = max(c["n"] - c["trivial"], 1)
    return {"n": c["n"], "trivial": c["trivial"],
            "exact_rate": round(c["exact"] / denom, 4),
            "subset_rate": round(c["subset"] / denom, 4)}


def build(root):
    ents, gid_lang, gid_name, source, views = _load(root)
    folds_root = os.path.join(root, "DBP5L/ind_v2/folds")
    out = {"built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "folds": {}}
    for name in sorted(os.listdir(folds_root)):
        tgt_path = os.path.join(folds_root, name, "budgets", "eval_targets_test.json")
        if not os.path.exists(tgt_path):
            continue
        targets = json.load(open(tgt_path))
        fold_out = {}
        for view in ("primary", "oracle"):
            strata, tot = audit_fold(targets, gid_lang, gid_name, source, views[view])
            fold_out[view] = {
                "overall": _rate(tot),
                "by_direction": {d: _rate(_merge(strata, lambda k: k[0] == d))
                                 for d in ("tail", "head")},
                "by_language": {l: _rate(_merge(strata, lambda k: k[1] == l))
                                for l in ("en", "fr", "es", "ja", "el")},
                "by_source": {s: _rate(_merge(strata, lambda k: k[2] == s))
                              for s in ("wikipedia_native", "wikipedia_cross_lang", "entity_name")},
            }
        out["folds"][name] = fold_out
    out_dir = os.path.join(root, "DBP5L/ind_v2/audits")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "answer_leakage.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    out["hash"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    with open(p, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    return out


def _merge(strata, pred):
    acc = {"n": 0, "exact": 0, "subset": 0, "trivial": 0}
    for k, c in strata.items():
        if pred(k):
            for f in acc:
                acc[f] += c[f]
    return acc


def _selfcheck():
    gid_lang = {1: "en", 2: "fr", 3: "en"}
    gid_name = {1: "alan turing", 2: "cambridge", 3: "x"}
    source = {1: "wikipedia_native", 2: "wikipedia_native", 3: "entity_name"}
    view = {1: "alan turing studied at cambridge university", 2: "une ville", 3: "x"}
    # target (1, r, 2): tail reads desc(1) -> mentions "cambridge" (exact+subset). head reads
    # desc(2) -> does not mention "alan turing".
    strata, tot = audit_fold([[1, 0, 2]], gid_lang, gid_name, source, view)
    tail = _rate(_merge(strata, lambda k: k[0] == "tail"))
    head = _rate(_merge(strata, lambda k: k[0] == "head"))
    assert tail["exact_rate"] == 1.0 and tail["subset_rate"] == 1.0, tail
    assert head["exact_rate"] == 0.0, head
    # trivial name (entity 3 "x") excluded from denom
    strata2, _ = audit_fold([[1, 0, 3]], gid_lang, gid_name, source, view)
    tailt = _rate(_merge(strata2, lambda k: k[0] == "tail"))
    assert tailt["trivial"] == 1 and tailt["exact_rate"] == 0.0, tailt
    print("audit_v2_answer_leakage self-check OK (exact+subset, direction split, trivial guard)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("RESEARCH_KG_ROOT",
                                                     os.path.expanduser("~/research_kg")))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selfcheck()
        sys.exit(0)
    r = build(args.root)
    # compact console summary (primary view, fold0)
    f0 = sorted(r["folds"])[0]
    print(f"answer leakage (primary, {f0}):")
    print(json.dumps(r["folds"][f0]["primary"], indent=2))
    print("hash", r["hash"][:16])
