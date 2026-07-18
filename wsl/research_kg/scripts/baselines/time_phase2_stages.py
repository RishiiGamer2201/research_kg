"""Phase 2 — DIRECT stage timing for the budget decision.

A short profiling run cannot measure the stages that dominate the real budget:
  * the hard-negative cache refresh happens once per epoch from --hard-neg-start-epoch, so a
    2-epoch run measures at most one (and possibly zero) refreshes;
  * evaluation is run once per description VIEW (natural / masked / missing), each an entity
    encode plus a head+tail ranking pass.

This times those stages directly, on a quiet GPU, so the estimator consumes measured stage
costs instead of extrapolated epoch time.

  stage 1: one forced hard-negative refresh over the TRAIN-ONLY negative universe
           (fold train entities, negpol-v2-train-only) at the training max_length.
  stage 2: one complete head+tail evaluation cycle per view (natural, masked, missing).

Output: DBP5L/ind_v2/audits/phase2_stage_timings.json
"""
import os
import sys
import json
import time
import argparse

ROOT = os.environ.get("RESEARCH_KG_ROOT", os.path.expanduser("~/research_kg"))
sys.path.insert(0, ROOT)


def time_hn_refresh(fold_dir, desc_path, max_length, model_name="BAAI/bge-m3"):
    import torch
    from transformers import AutoTokenizer
    import train_dbp5l_lora as T

    entity_texts = {int(k): v for k, v in json.load(open(desc_path)).items()}
    train_ents = set(json.load(open(os.path.join(fold_dir, "train_entities.json"))))
    universe = sorted(e for e in entity_texts if e in train_ents)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(model_name)
    model = T.BGE_M3_LoRA_KGC(model_name, lora_rank=16, lora_alpha=32).to(device).eval()

    torch.cuda.synchronize() if device.type == "cuda" else None
    t0 = time.time()
    cache, _ = T.build_entity_cache(model, tok, entity_texts, universe,
                                    max_length, device, batch_size=512)
    torch.cuda.synchronize() if device.type == "cuda" else None
    dt = time.time() - t0
    peak = (torch.cuda.max_memory_allocated() / 1e9) if device.type == "cuda" else 0.0
    del model, cache
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return {"negative_universe": len(universe), "max_length": max_length,
            "seconds": round(dt, 1), "minutes": round(dt / 60, 2),
            "peak_vram_gb": round(peak, 2)}


def time_eval_cycle(fold_dir, view_path, view_name):
    import eval_dbp5l as E
    E.DESC_PATH_OVERRIDE = view_path
    targets = os.path.join(fold_dir, "budgets", "eval_targets_test.json")
    t0 = time.time()
    r = E.evaluate(None, per_language=False, zero_shot=True,
                   directions=["tail", "head"], v2_targets_path=targets)
    dt = time.time() - t0
    return {"view": view_name, "seconds": round(dt, 1), "minutes": round(dt / 60, 2),
            "combined_mrr": round(r["by_direction"]["combined"]["within_language_overall"]["mrr"], 4)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", default=os.path.join(ROOT, "DBP5L/ind_v2/folds/fold0_seed13"))
    ap.add_argument("--max-length", type=int, default=160)
    ap.add_argument("--stages", default="hn,eval")
    a = ap.parse_args()

    views = {
        "natural": os.path.join(ROOT, "DBP5L/ind_v2/tracks/descriptions_v2_primary.json"),
        "masked": os.path.join(ROOT, "DBP5L/ind_v2/tracks/descriptions_v2_masked.json"),
        "missing": os.path.join(ROOT, "DBP5L/ind_v2/tracks/descriptions_v2_missing_text.json"),
    }
    out = {"fold": os.path.basename(a.fold), "max_length": a.max_length}

    if "hn" in a.stages:
        out["hard_negative_refresh"] = time_hn_refresh(a.fold, views["natural"], a.max_length)
        print("HN refresh:", json.dumps(out["hard_negative_refresh"]), flush=True)

    if "eval" in a.stages:
        out["eval_cycles"] = []
        for name, path in views.items():
            r = time_eval_cycle(a.fold, path, name)
            out["eval_cycles"].append(r)
            print("eval cycle:", json.dumps(r), flush=True)
        out["eval_total_minutes"] = round(sum(c["minutes"] for c in out["eval_cycles"]), 2)

    p = os.path.join(ROOT, "DBP5L/ind_v2/audits/phase2_stage_timings.json")
    json.dump(out, open(p, "w"), indent=2, sort_keys=True)
    print("wrote", p)
