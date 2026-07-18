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
- **Gate G0 close-out after both:** mark G0 boxes, record pushed SHA, `git push origin main` (12 commits pending). Then Phase 1.

### 2026-07-18 — Run E DONE, Gate G0 CLOSED
- Run E clean retrain finished 30/30 ep, exit 0, best acc@1 72.54% (ep23). Train manifest status=complete, ckpt c85f23de.
- **Clean eval: within-lang MRR 27.02** (H@1 18.5 H@3 30.2 H@10 43.0), cross-lingual 26.78. Per-lang FR37.7/ES37.6/JA19.8/EL17.1/EN16.1. Ledger R-023.
- **Finding (precise):** seed-42 clean 27.02 sits within provisional band 26.51±0.31 → NO evidence contamination inflated THIS run. NOT a definitive clean-vs-contaminated comparison — that needs the **3-seed clean baseline in Phase 2**. Do not overclaim causality from one seed.
- **Gate G0 CLOSED:** all boxes marked, R-016..R-023 in ledger. Pushed to main (SHA recorded in plan). Phase 0 DONE.
- **Phase 1 STARTED (ledger R-024):**
  - **P1.2 concept clusters DONE:** `scripts/data_prep/build_concept_clusters.py` (union-find over `processed/alignments.json` global-id pairs). 56,589 entities → **29,440 concepts** (9,762 multilingual size 2–5, 19,678 singletons, **0 ambiguous** = no same-lang collisions). Canonical concept_id = min gid. Output `DBP5L/ind_v2/concepts/` (concepts.json, entity2concept.json committed; union_provenance.jsonl gitignored/regenerable). Deterministic (hash-stable). Self-check `--selftest`.
  - **P1.7 concept-leakage audit DONE (partial):** `scripts/data_prep/concept_leakage_audit.py`. **v1 split leaks 72.3% of test concepts (4,964/6,866) into train** via cross-lingual aligned IDs → confirms §4.3, motivates v2. Provides reusable `assert_concept_disjoint(train,valid,test)` for the fold builder.
  - Data model: entities.json keyed by GLOBAL id {lang,local_id,global_id,name,uri,desc}; alignments.json = global-id pairs; align_index.json NOT transitively closed (don't use). v1 ind/ uses per-lang LOCAL ids → map via entities.json (lang,local_id)→global.
- **P1.3 folds DONE (ledger R-025):** `scripts/data_prep/build_v2_folds.py`. Official fold seeds **[13,42,79]** (FOLD_SEEDS const). 29,440 concepts → per fold train 22,082 / valid 2,943 / test 4,415 (75/10/15), stratified by concept size (language coverage) bucket, whole concepts only. Inductive valid (disjoint from train). All 5 langs in valid+test. `assert_concept_disjoint` passes all folds. Per fold published: {train,valid,test}_{concepts,entities}.json + stratification_stats.json + fold_manifest.json (seed/ratios/hashes/assert=passed); folds_summary.json. Deterministic. Committed to repo (1.8MB). Self-check `--selftest`.
- **RQ1 precise definition (locked):** a v1 test concept "leaks" iff its alignment-connected component (union-find concept) contains ≥1 entity in the v1 training set of ANY language → 72.3% (4,964/6,866). In R-024 + P1.7 note.
- **Also fixed:** P0.3 determinism checkbox now [x] (R-020 proved it, was stale). Confirmed head/tail reciprocal eval is a Phase-1 item (P1.6).
- **P1.1 DONE (ledger R-026):** `hash_source_data.py` → `source_manifest.json` (31 files, top_sha256 0eca75a5). `DBP5L_DATA_PROVENANCE.md` (KEnS/EMNLP-2020, CC BY-SA 3.0, ID chain URI→(lang,local)→global→concept). Exact upstream git commit NOT captured (content hash = anchor). [User flagged P1.1 was skipped — now done.]
- **P1.4 DONE (ledger R-027):** `build_v2_support_budgets.py`. **Comparability rule (user-mandated) enforced:** S^5 union selected FIRST, removed from eval targets for ALL budgets → targets + candidates fixed; ONE filter (all graph facts, single hash) for all budgets; only exposed evidence varies S^0⊂S^1⊂S^3⊂S^5. Order key `(other_seen?0:1, r, other_gid, dir)`. Per fold: ~10,399 unseen w/ support, avg pool 3.81, S^5 union ~39k, eval_targets_test ~37k. Invariants pass (caps, prefix nesting, target∩S^5=0, targets-fixed, single-filter). Committed (~10MB v2 data). Self-check.
- **P1.5 DONE (ledger R-028):** `build_v2_descriptions.py`. Priority native-wiki → cross-lang(concept) → name. 56,589: **48,496 native / 4,274 cross-lang / 3,819 name**, NO LLM. snapshot_rev=7ba0dd5f (wiki corpus hash; per-page rev ids NOT captured = recorded gap). Per-entity provenance: raw+norm hashes SEPARATE, source, url(uri), snapshot_rev/date, lang+entity_lang, licence CC BY-SA 3.0, retrieval, fallback_reason, cross_lang_source_gid+concept, translated=False. **Answer mentions PRESERVED (not stripped) — leakage quantified in P1.7 per user directive.** Graph-derived train text deliberately NOT used (avoids §4.2 leak). Big derived files (47MB) gitignored/regenerable; inputs (wiki.json, entity2concept, entities.json) all tracked. Self-check.
  - **P1.6 note:** alignment-free primary track must EXCLUDE `wikipedia_cross_lang` descriptions for test/valid (they inject aligned-language info); provenance flag enables this.
- **P1.6 Part A DONE (ledger R-029):** `build_v2_eval_tracks.py`. Primary alignment-free view `descriptions_v2_primary.json` (hash d1afcf20): cross-lang(4274)→native name, **0 cross-lang usage ASSERTED**. Oracle view = descriptions_v2.json (hash 2a19bb0b, labelled diagnostic). Candidate universes independent+hashed: all-lang 6a641485 (matches evaluator's persisted hash!), within-lang ×5. Track manifest declares head/tail/combined + budget-fixed targets/filter refs. Committed (primary corpus 16MB gitignored; candidates+manifest committed). Self-check.
- **P1.6 Part B PENDING (code + retrain):** reciprocal head+tail in BOTH trainer + evaluator.
  - Evaluator `eval_dbp5l.py`: currently tail-only (query `head[SEP]rel→tail`). Add head prediction via reciprocal query with a DIRECTION/inverse-relation TOKEN; report head / tail / combined SEPARATELY. Fixed candidate universe + single filter already present.
  - Trainer `train_dbp5l_lora.py`: add reciprocal training examples (each triple both directions with direction token) so head prediction is trained, not zero-shot.
  - Then RETRAIN single-seed reciprocal on primary view (d1afcf20) + eval head/tail/combined. GPU job ~5-10h; launch via `nohup setsid ... & disown`, resume-safe (see Run E recovery below).
- **NEXT: P1.6 Part B code**, then rest P1.7 (exact+semantic answer leakage [user directive], dup/inverse/answer-string/degree/PPR shortcut), P1.8 data card → Gate G1 (push).

### 2026-07-17 (cont) — Run E INTERRUPTED then RESUMED detached
- Tracked bg tasks got mass-killed at a session boundary (~8h job can't survive as a tool-tracked task). Run E had done **2/30 epochs** (valid acc@1 64.5→67.4) with best_model.pt + last_checkpoint.pt saved. Manifest stayed `running` (correct = incomplete).
- **RESUMED fully detached** (survives tool/session death): `~/research_kg/run_E_resume.sh` launched via `nohup setsid bash run_E_resume.sh & disown` from WSL. Confirmed running (PID, GPU ~10GB/32%). ~16.6 min/epoch → ~7.5h for remaining 28 epochs.
- **Sentinel:** on finish the script touches `DBP5L/checkpoints/bgem3_lora_dbp5l_20260717_1541_crr_hn7_r16/.RUN_E_DONE` and appends `RUN_E_EXIT=<code>` to `logs/run_clean_seed42_ml160.log`.
- **RECOVERY (if killed again):** re-run `wsl.exe -d Ubuntu -- bash -lc "cd ~/research_kg && nohup setsid bash run_E_resume.sh >> logs/run_E_launch.log 2>&1 & disown"`. Trainer `--resume last_checkpoint.pt` continues from last completed epoch (RNG/opt/sched restored). Idempotent.
- **WHEN `.RUN_E_DONE` appears:** eval `best_model.pt` → `HF_HUB_OFFLINE=1 python3 eval_dbp5l.py --checkpoint <RD>/best_model.pt --desc-path .../entity_descriptions_clean.json`. Compare within-lang MRR to historical R-005/006 (26.5, provisional: contaminated desc + best-case ties). Then finish_run auto-marks manifest complete on train exit; append ledger R-023; mark Gate G0; `git push origin main`.
- **Lesson:** long GPU jobs MUST launch via `nohup setsid ... & disown` (NOT tool run_in_background — that dies at session boundaries). Verify with `pgrep -af train_dbp5l` + nvidia-smi.
