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
- **NEXT: P0.2** immutable run manifests (run_id, git_commit, hashes, atomic no-overwrite, status field). Then P0.3 deterministic eval, P0.4 relation identity, P0.5 reproduce one baseline. Gate G0.
