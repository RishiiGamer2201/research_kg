"""DBP5L-Ind v2 / P1.6+P1.7 completion — missing-text track + train-only graph-text view.

Two artifacts requested to close the remaining Phase-1 partials:

1. MISSING-TEXT track (global, deterministic): every description reduced to the entity's
   normalized name only (description "removed"). Diagnostic track for the no-text condition.
   -> DBP5L/ind_v2/tracks/descriptions_v2_missing_text.json

2. TRAIN-ONLY graph-derived text (per fold): for TRAIN-concept entities, serialize their
   training-graph edges ("relation -> neighbour_name; ...") using TRAIN triples ONLY (both
   endpoints are train entities). No validation/test edges, so no §4.2 leak. Optional
   augmentation; unseen (valid/test) entities are left as name-only here.
   -> DBP5L/ind_v2/folds/<fold>/train_graphtext.json

Self-check: `python3 build_v2_extra_tracks.py --selftest`.
"""
import os
import sys
import json
import time
import hashlib
import unicodedata
import argparse
from collections import defaultdict

MAX_EDGES = 20      # cap serialized edges per train entity (determinism + length)


def _norm(s):
    return " ".join(unicodedata.normalize("NFC", (s or "")).lower().split())


def _dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _load(root):
    proc = os.path.join(root, "DBP5L/processed")
    with open(os.path.join(proc, "entities.json")) as f:
        ents = {int(g): e for g, e in json.load(f).items()}
    rn_path = os.path.join(proc, "relation_names.json")
    rel_names = json.load(open(rn_path)) if os.path.exists(rn_path) else {}
    triples = []
    for split in ("train", "valid", "test"):
        p = os.path.join(proc, f"{split}.json")
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    d = json.loads(line)
                    triples.append((d["h"], d["r"], d["t"]))
    return ents, rel_names, triples


def build_missing_text(root, ents):
    view = {str(g): _norm(ents[g].get("name") or "") for g in ents}
    out_dir = os.path.join(root, "DBP5L/ind_v2/tracks"); os.makedirs(out_dir, exist_ok=True)
    h = _dump(os.path.join(out_dir, "descriptions_v2_missing_text.json"), view)
    return {"n_entities": len(view), "hash": h}


def build_train_graphtext(root, ents, rel_names, triples):
    gid_name = {g: _norm(e.get("name") or "") for g, e in ents.items()}
    def rtext(r):
        return _norm(rel_names.get(str(r), rel_names.get(r, f"relation {r}")))

    folds_root = os.path.join(root, "DBP5L/ind_v2/folds")
    summary = {}
    for name in sorted(os.listdir(folds_root)):
        fdir = os.path.join(folds_root, name)
        te = os.path.join(fdir, "train_entities.json")
        if not os.path.isdir(fdir) or not os.path.exists(te):
            continue
        train_ents = set(json.load(open(te)))
        # edges internal to the train graph (both endpoints train) only
        out_edges = defaultdict(list)
        for (h, r, t) in triples:
            if h in train_ents and t in train_ents:
                out_edges[h].append((rtext(r), gid_name.get(t, "")))
                out_edges[t].append((f"reverse of {rtext(r)}", gid_name.get(h, "")))
        view = {}
        for g in sorted(train_ents):
            edges = sorted(set(out_edges.get(g, [])))[:MAX_EDGES]
            body = "; ".join(f"{rt} {nm}" for rt, nm in edges if nm)
            view[str(g)] = f"{gid_name.get(g, '')}. {body}".strip()
        h = _dump(os.path.join(fdir, "train_graphtext.json"), view)
        summary[name] = {"n_train_entities": len(view), "hash": h}
    return summary


def build(root):
    ents, rel_names, triples = _load(root)
    out = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "missing_text": build_missing_text(root, ents),
        "train_graphtext_per_fold": build_train_graphtext(root, ents, rel_names, triples),
    }
    out_dir = os.path.join(root, "DBP5L/ind_v2/tracks")
    with open(os.path.join(out_dir, "extra_tracks_stats.json"), "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    return out


def _selfcheck():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="extra_test_")
    try:
        proc = os.path.join(d, "DBP5L/processed"); os.makedirs(proc)
        fdir = os.path.join(d, "DBP5L/ind_v2/folds/fold0_seed13"); os.makedirs(fdir)
        ents = {"0": {"lang": "en", "name": "Alan Turing"}, "1": {"lang": "en", "name": "Cambridge"},
                "2": {"lang": "en", "name": "Unseen"}}
        json.dump(ents, open(os.path.join(proc, "entities.json"), "w"))
        json.dump({"9": "studied at"}, open(os.path.join(proc, "relation_names.json"), "w"))
        # train edge 0-1 (both train); edge 0-2 touches unseen 2 -> excluded from train graphtext
        with open(os.path.join(proc, "train.json"), "w") as f:
            f.write(json.dumps({"h": 0, "r": 9, "t": 1}) + "\n")
            f.write(json.dumps({"h": 0, "r": 9, "t": 2}) + "\n")
        json.dump([0, 1], open(os.path.join(fdir, "train_entities.json"), "w"))
        r = build(d)
        assert r["missing_text"]["n_entities"] == 3
        mt = json.load(open(os.path.join(d, "DBP5L/ind_v2/tracks/descriptions_v2_missing_text.json")))
        assert mt["0"] == "alan turing"                         # name-only
        gt = json.load(open(os.path.join(fdir, "train_graphtext.json")))
        assert "cambridge" in gt["0"] and "studied at" in gt["0"]   # train edge serialized
        assert "unseen" not in gt["0"]                          # valid/test-touching edge excluded
        assert "2" not in gt                                    # unseen entity not in train view
        print("build_v2_extra_tracks self-check OK (missing-text + train-only graphtext)")
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
    print(json.dumps(build(args.root), indent=2))
