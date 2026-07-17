# Project Memory — SelfHeal-MKGC

Running log. Newest entries at top of each section. Absolute dates.

## Fixed context
- **Repo (git, canonical):** `C:\developer\research_ai\research_kg\mkgc-multilingual-inductive` — origin `github.com/RishiiGamer2201/research_kg`, branch `main`.
- **Live WSL tree (NOT git):** `\\wsl$\Ubuntu\home\admin_wsl\research_kg` — active trainers, data, checkpoints, venv. Docs live only on Windows.
- **Windows mirror of WSL:** `wsl/research_kg/` inside the repo (data `DBP5L/ind`+`processed/` and `scripts/` already tracked, 396 files).
- **Proposal:** `docs/FINAL_RESEARCH_PROPOSAL_2026-07-17.md`. **Plan of record:** `docs/FINAL_IMPLEMENTATION_PLAN_2026-07-17.md`.
- **Venv:** `~/research_kg/RAA-KGC/SimKGC/venv` (WSL). Best substrate: Run E (BGE-M3, ml160, LoRA r16, CRR, HN K=7), 3-seed mean MRR 26.51 — provisional (trained on contaminated descriptions).
- **Clean descriptions:** `DBP5L/processed/entity_descriptions_clean.json` (no LLM back-fill). Contaminated original: `entity_descriptions.json`.

## Key facts / decisions
- Phase order is benchmark-first: P0 repair repro → P1 DBP5L-Ind v2 → P2 baselines → P3 routing → P4 self-healing → P5 downstream. Only B0 + ≤4 survivors get multi-seed.
- Global auto-memory (separate system) at `~/.claude/projects/.../memory/MEMORY.md` records prior strategic decisions (SIGIR 2027 target, SimRMKGC anchor, reproduce 3 datasets in parallel).

## Progress log

### 2026-07-17 — Phase 0 START
- Mapped both trees. Confirmed §4.10/P0.1 gap: Windows repo missing active root code that lives only in WSL:
  `train_dbp5l_lora.py`, `eval_dbp5l.py`, `eval_dbp5l_anchors.py`, `detector_experiment.py`, `bootstrap_sig.py`,
  run wrappers `run_clean_retrain.sh`, `run_baselines.sh`, `run_seeds.sh`, `run_seed777.sh`, and WSL `README.md`.
- **P0.1 DONE (ledger R-016):**
  - Copied 5 root scripts + 4 run wrappers + README into `wsl/research_kg/`.
  - Added `RESEARCH_KG_ROOT` env override (default `~/research_kg`) to train/eval/eval_anchors/detector — no source edits needed to relocate data. All byte-compile.
  - Env captured: `wsl/research_kg/ENVIRONMENT.md` + `requirements.simkgc-venv.txt`. py3.10.20, torch2.11.0+cu128, CUDA12.8, transformers5.12.1, peft0.19.1. GPU: RTX 5070 Ti 16GB.
  - Gotchas: text venv has NO FlagEmbedding/dgl (BGE-M3 loads via transformers AutoModel — fine). 3 divergent S2DN venvs (`venv_s2dn{,_gpu,_gpu_latest}`) — canonical one to be frozen in P0.5.
- **WORKFLOW LOCKED (user decision):** repo is canonical; live WSL `~/research_kg` uses **symlinks** into `/mnt/c/.../wsl/research_kg/`. Edit repo → WSL runs it, no copy. Setup: `setup_wsl_symlinks.sh` (idempotent, backs up originals to `archive/pre_symlink_<date>/`). Verified imports work in venv. Data/venv/checkpoints stay in WSL (gitignored).
  - Gotcha: invoke WSL via **PowerShell tool**, not Bash tool — Git Bash MSYS mangles `/mnt/c` paths. Multi-line WSL scripts: write to scratchpad file, run `wsl.exe -d Ubuntu -- bash <file>` from PowerShell.
- **P0.2 DONE (ledger R-017):** `run_manifest.py` (stdlib-only, imports in any venv). `start_run`/`finish_run`, SHA-256 of inputs, atomic `os.replace`, refuse-overwrite, status running|complete|failed|invalidated, parent/invalidates ids, HF model_revision from cache. Wired into `train_dbp5l_lora.py` (fresh runs; resume keeps manifest) and `eval_dbp5l.py` (per-eval timestamped dir under `<ckpt>/evals/`). Self-check + live test on real data pass. Schema: `MANIFEST_SCHEMA.md`. Symlinked into WSL.
  - Deferred to P0.3: candidate-set hash + filter hash (need evaluator to persist ordered candidate list + explicit filter policy). Also `failed` status (crash currently stays `running`).
- **P0.3 MOSTLY DONE (ledger R-018):**
  - Tie bug fixed at shared `compute_filtered_metrics`: was best-case (`>score`+1), now averaged `higher+(ties+1)/2`. Runnable check `eval_dbp5l.py --selftest` (passes in WSL). **This changes future metrics vs history** — small (float ties rare) but real; recorded as correction, history not overwritten.
  - Candidate universe persisted to `candidates.json` + hashed; eval manifest now pins candidates + all splits + support files (completes P0.2 candidate/filter-hash deferral).
  - Already-correct (verified): max_length auto-read from ckpt; filter map = train+valid+test+support.
  - DEFERRED: head-prediction eval → P1.6 (evaluator is tail-only `head[SEP]rel→tail`; needs reciprocal training). Repeat-determinism assertion → P0.5 (eval has no RNG, deterministic by construction).
- **P0.4 MOSTLY DONE (ledger R-019):**
  - GraIL converter: `rel_name(r)=R{r}__name` (injective) + collision report (**93 groups / 186 IDs** real, e.g. `composer`←[2,653]) + injectivity assertion. `grail_format/` regenerated un-merged. relation_names.json has 960 entries.
  - Rule cache: `rule_miner.rule_signature(...)` keys on dataset+train+params+relation2id+target_policy; `ensure_rule_cache` validates signature, re-mines stale. Removed redundant fixed-path pre-set in `train.py:238`. Self-check `python S2DN/SDN/utils/rule_miner.py`.
  - **Process fix:** `scripts/` was NOT symlinked → WSL ran stale converter. Now `setup_wsl_symlinks.sh` symlinks whole `scripts/` dir. Lesson: any code edited in repo must be symlinked into WSL to take effect.
  - DEFERRED: target-edge removal before mining/scoring → P2.6 (per-query RuleTrust scoring, needs dgl venv + §4.6 gradient audit); policy in cache signature already.
- **P0.5 IN PROGRESS (ledger R-020):**
  - Zero-shot full eval on clean desc, run TWICE → **byte-identical, DETERMINISTIC: True** (within-lang MRR 1.44016 both). Settles P0.3 repeat-determinism.
  - **Reproduces historical R-001 (zero-shot MRR 1.45) → got 1.44** (within 0.01; diff = tie-averaging + rounding). Rebuilt evaluator validated end-to-end on GPU.
  - Eval manifest fully populated on real run: candidate_hash, all splits + per-language support hashes, git commit, model rev 9a0624b8. P0.2 candidate/filter deferral CLOSED.
  - Eval throughput: ~56k entity encode ~55s; full 54,473-triple eval ~2 min (within+cross-lingual).
  - Smoke train DONE (R-021): 1-epoch bge ml64, ~7 min. Train manifest status=complete, ckpt hash d2c8dcde, metrics logged. Ckpt eval: max_length=64 auto-read from ckpt, eval manifest written. Full train→ckpt→load→eval→manifest chain validated.
  - Smoke MRR 0.40 < zero-shot 1.44 = EXPECTED (1 epoch, ml64, no CRR/HN, undertrained). NOT a regression. Real number needs Run E config.
  - REMAINING before Gate G0: (a) full trained Run E retrain ~10 GPU-h [big background job]; (b) S2DN structural smoke [needs dgl venv — one of S2DN/venv_s2dn*]. Both pure GPU-time, not code.
  - NOT pushed yet: holding Gate G0 push until structural baseline + full retrain done (or user says push text-side progress now). 10 commits local on main.
- **HF note:** eval hits HF Hub for BGE-M3 metadata each load (online). Set `HF_HUB_OFFLINE=1` to avoid network (used in smoke train). Model cached rev 5617a9f6.. / 9a0624b8.. .

### 2026-07-17 — Gate G0 GPU jobs RUNNING (user approved: single-seed Run E + newest S2DN venv smoke)
- **Run E retrain** (bg task bh72tja85): `train_dbp5l_lora.py` seed 42, clean desc, 30 epochs, ml160, r16, CRR ρ0.1, HN K=7 from ep5. Run dir `DBP5L/checkpoints/bgem3_lora_dbp5l_20260717_1541_crr_hn7_r16`. Manifest written, 118256 ex, 13860 steps, VRAM 1.14GB. Log `~/research_kg/logs/run_clean_seed42_ml160.log`. ETA ~5-10h. **After it finishes: eval the best_model.pt** (HF_HUB_OFFLINE=1) → compare to historical R-005/006 (26.5 provisional, was contaminated desc + best-case ties). This is the real clean number.
- **S2DN smoke** (bg task bok1mceqo): venv_s2dn_gpu_latest (torch2.11+cu128, dgl2.4.0+cu121), fb237_v1, 1 epoch, max_links 20, paper dims (emb64/hop3/lr5e-4). Log `scratchpad/s2dn_smoke.log`. Validates structural pipeline + logged hyperparams for G0. Not the full repro (that's R-013 MRR 53.13, ~4.8h).
- **Gate G0 close-out after both:** mark G0 boxes, record pushed SHA, `git push origin main` (11 commits pending). Then Phase 1.
