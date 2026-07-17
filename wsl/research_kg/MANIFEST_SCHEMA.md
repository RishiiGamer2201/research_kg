# Run manifest schema (Phase 0 / P0.2)

Written by `run_manifest.py` as `<run_dir>/manifest.json`. One manifest per run.
Validator = `python3 run_manifest.py` (self-check: one-byte input change flips the hash;
overwrite of a running/complete manifest is refused).

## Fields
| Field | Meaning |
|---|---|
| `run_id` | `YYYYMMDD_HHMMSS_<8hex>` (UTC) — unique, generated before work starts |
| `kind` | `train` \| `eval` \| `detector` \| ... |
| `status` | `running` \| `complete` \| `failed` \| `invalidated`. A crash leaves `running` (= incomplete). |
| `parent_run_id` | run this derives from (e.g. resumed/continued), else null |
| `invalidates_run_id` | run this supersedes; the old row is never deleted, only linked |
| `start_utc` / `end_utc` | ISO-8601 UTC |
| `env.git_commit` / `env.git_dirty` | repo commit + dirty-tree flag of the canonical repo |
| `env.command` | exact argv |
| `env.hostname` / `env.gpu` / `env.platform` | machine + accelerator |
| `env.python` / `env.torch` / `env.cuda` / `env.transformers` / `env.peft` | versions |
| `env.seed` | random seed |
| `env.model_name` / `env.model_revision` / `env.tokenizer_revision` | HF model + resolved cache commit |
| `input_hashes.*` | SHA-256 of every pinned artifact: train/valid split, descriptions, relation_names, anchors, candidates, filter, checkpoint. Missing file → null. |
| `input_paths.*` | the paths those hashes were taken from |
| `metrics` | headline metrics attached at finish |
| `extra` | run-specific (args, run_name, max_length, results_path, ...) |

**P0.3 will add** `candidates` and `filter` to `input_hashes` once the evaluator persists an
ordered candidate list and an explicit filter policy (currently constructed in-code).

## Sample (train, abbreviated)
```json
{
  "run_id": "20260717_150245_d76cc27d",
  "kind": "train",
  "status": "complete",
  "start_utc": "2026-07-17T15:02:45Z",
  "end_utc": "2026-07-17T15:02:46Z",
  "env": {
    "python": "3.10.20", "torch": "2.11.0+cu128", "cuda": "12.8",
    "transformers": "5.12.1", "peft": "0.19.1",
    "gpu": "NVIDIA GeForce RTX 5070 Ti", "seed": 42,
    "git_commit": "bd241f3d...", "git_dirty": false,
    "model_name": "BAAI/bge-m3",
    "model_revision": "9a0624b896d81da7492a910ffa53731274b6cf3d"
  },
  "input_hashes": {
    "train_split": "c28fe545140a...", "valid_split": "e071f40d9906...",
    "descriptions": "462e6127a919...", "relation_names": "bc1251ff63e1..."
  },
  "metrics": {"best_valid_acc1": 40.1, "epochs_run": 10}
}
```
