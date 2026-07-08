# Implementation Plan: S2DN Ladder (2026-07-08)

This is the execution plan for the mentor's bottom-up ladder: reproduce S2DN, beat it on English
inductive KGC with a rule-guided modification, extend to multilingual, then add self-healing text
repair. It is the actionable companion to the research note in
[mentor_plan_research_2026-07-08.md](mentor_plan_research_2026-07-08.md), which holds the paper
summaries, the verified S2DN target numbers, and the topic analysis.

Work happens in the WSL workspace at `/home/admin_wsl/research_kg`. The existing DBP-5L pipeline
stays untouched and remains the source of truth for the multilingual text baselines. S2DN gets its
own isolated workspace and environment.

Check boxes off as tasks complete. Training runs longer than one hour are handed to the user to run,
per the standing workflow.

---

## Results and Inference

This section is the running result ledger for this implementation plan. It should be updated after
each completed split, reproduction run, ablation, or architectural modification.

### Reproduction Results

| Date | Dataset | Run | Status | MRR | Hits@1 | Hits@5 | Hits@10 |
|---|---|---|---|---:|---:|---:|---:|
| 2026-07-08 | WN18RR_v1_ind | `sdn_wn_v1_gpu` | Complete | 79.95 | 74.73 | 84.84 | 87.23 |
| 2026-07-08 | WN18RR_v2_ind | `sdn_wn_v2_gpu` | Complete | 80.83 | 77.32 | 83.11 | 85.26 |
| 2026-07-08 | WN18RR_v3_ind | `sdn_wn_v3_gpu` | Complete | 57.02 | 49.83 | 62.98 | 68.84 |
| 2026-07-08 | WN18RR_v4_ind | `sdn_wn_v4_gpu` | Complete | 77.28 | 74.60 | 78.52 | 80.93 |
| 2026-07-08 | WN18RR completed average | v1-v4 | Complete | 73.77 | 69.12 | 77.36 | 80.57 |

### Paper Metrics

The S2DN paper reports filtered `Hits@1`, `Hits@10`, and `MRR` for the per-version rows. It does
not report `Hits@5` in this table.

| Dataset | Split | MRR | Hits@1 | Hits@10 |
|---|---|---:|---:|---:|
| WN18RR | V1 | 79.89 | 74.73 | 87.64 |
| WN18RR | V2 | 81.16 | 78.23 | 85.60 |
| WN18RR | V3 | 58.10 | 52.89 | 69.52 |
| WN18RR | V4 | 78.04 | 75.33 | 82.15 |
| WN18RR | Avg v1-v4 | - | - | 81.23 |
| FB15k-237 | V1 | 52.10 | 43.68 | 67.34 |
| FB15k-237 | V2 | 64.80 | 55.45 | 82.38 |
| FB15k-237 | V3 | 65.07 | 56.31 | 83.97 |
| FB15k-237 | V4 | 68.44 | 60.96 | 91.31 |
| FB15k-237 | Avg v1-v4 | - | - | 81.25 |

| Dataset | Target / Reference | Inference |
|---|---|---|
| WN18RR_v1_ind | Paper: MRR 79.89, Hits@1 74.73, Hits@10 87.64 | Reproduction is successful. MRR is slightly above paper, Hits@1 matches exactly, and Hits@10 is only 0.41 points below. Continue v2-v4. |
| WN18RR_v2_ind | Paper WN18RR average Hits@10: 81.23 | v2 completed cleanly. Hits@10 is 85.26, and the v1-v2 completed average is already 86.25, which is comfortably above the paper's reported WN18RR average target. Finish v3-v4 before making the final claim. |
| WN18RR_v3_ind | Paper: MRR 58.10, Hits@1 52.89, Hits@10 69.52 | v3 completed cleanly and lands close to the paper's hard-split target. Hits@10 is 0.68 points below paper; MRR is 1.08 points below. This is acceptable reproduction drift for the hardest WN18RR split. |
| WN18RR_v4_ind | Paper: MRR 78.04, Hits@1 75.33, Hits@10 82.15 | v4 completed cleanly. MRR is 0.76 points below paper, Hits@1 is 0.73 points below, and Hits@10 is 1.22 points below. |
| WN18RR average | Paper average Hits@10: 81.23 | Full v1-v4 reproduced average Hits@10 is 80.57, only 0.66 points below paper. This is close enough to treat the S2DN reproduction as successful and move to RuleTrust-S2DN. |

### Engineering Results

| Date | Component | Result |
|---|---|---|
| 2026-07-08 | WSL GPU access | Fixed after WSL restart |
| 2026-07-08 | S2DN GPU env | Working experimental GPU stack |
| 2026-07-08 | S2DN validation patch | Fixed tuple-output validation crash |
| 2026-07-08 | S2DN ranking patch | Ranking now completes on saved checkpoints |
| 2026-07-08 | Result collection | WN18RR CSV collector added and v1-v4 average computed |

Engineering evidence and inference:

- WSL GPU access: `nvidia-smi` lists RTX 5070 Ti and PyTorch CUDA is available. The original issue
  was transient WSL/NVML state, not a broken driver setup.
- S2DN GPU env: `venv_s2dn_gpu_latest` uses PyTorch 2.11.0+cu128 and DGL 2.4.0+cu121. S2DN smoke
  reached `Device: cuda:0`, so the stack is usable despite the DGL dependency override.
- Validation patch: `managers/evaluator.py` unwraps `(score, kl_loss)` before metrics. This mirrors
  how training already handled the model output.
- Ranking patch: `test_ranking.py` unwraps tuple outputs, uses `weights_only=False`, and normalizes
  the loaded model device. This fixed PyTorch 2.6+ checkpoint loading and CPU/GPU graph mismatch.
- Result collection: `results_wn18rr.csv` summarizes v1-v4 metrics consistently after each split.

### Current Inference

| Question | Current Answer | Confidence | Next Evidence Needed |
|---|---|---:|---|
| Can we reproduce S2DN on English inductive KGC? | Yes. WN18RR v1-v4 completed with average Hits@10 `80.57` against paper `81.23`. | High | Start RuleTrust-S2DN on top of the reproduced baseline. |
| Is the GPU setup usable? | Yes; v1-v4 completed in the GPU env. S2DN remains subgraph-heavy and not fully GPU-saturated. | High | Reuse the same env for RuleTrust-S2DN ablations. |
| Are we ready to implement RuleTrust-S2DN? | Yes. The English WN18RR S2DN baseline is reproduced closely enough to become the comparison point. | High | Implement rule mining and rule-prior injection into Structure Refining. |
| Is multilingual/self-healing next? | No. It remains downstream after English reproduction and one principled S2DN improvement. | High | RuleTrust-S2DN result on WN18RR and preferably FB15k-237. |

---

## 0. Current Blockers and Reality Checks

Read this before starting. Two things gate everything.

### 0.1 WSL GPU access

Initially, `nvidia-smi` inside WSL failed with `Failed to initialize NVML: N/A`, and
`torch.cuda.is_available()` returned False. This was a transient WSL NVML issue, fixed by restarting
WSL from Windows.

- [x] Restart WSL from Windows PowerShell: `wsl --shutdown`, then reopen a WSL shell.
- [x] Confirm `nvidia-smi` lists the RTX 5070 Ti.
- [x] Confirm in the training venv: `python3 -c "import torch; print(torch.cuda.is_available())"`
      prints `True`.
- [ ] If it breaks again after restart, check the Windows NVIDIA driver and the WSL kernel
      (`wsl --update`) before any training.

### 0.2 DGL on Blackwell is the real reproduction risk

The working torch here is 2.11.0+cu128. The S2DN README pins `dgl==1.1.2` (CUDA 11 era) and the
repo `requirements.txt` pins `dgl==0.4.2` (CUDA 10 era, GraIL-old). Neither matches torch 2.x on
CUDA 12.8, and neither is expected to support Blackwell sm_120. This is the single most likely place
the reproduction stalls. Plan for it up front rather than discovering it mid-run.

- [x] Treat "get DGL to import and see the GPU" as the first hard gate, ahead of any S2DN training.
- [x] Fallback ladder if the pinned DGL will not build against Blackwell:
  - [x] Try a DGL 2.x wheel built for torch 2.x and a recent CUDA, then patch S2DN's DGL API calls
        forward (the DGL API changed between 1.1 and 2.x, so expect some code edits).
  - [x] If GPU DGL is not workable quickly, run WN18RR_v1 on CPU first purely as a correctness
        sanity check. V1 is tiny, so CPU is viable for one split even though it is slow.
  - [x] Record whichever stack works in the environment report so results are reproducible.

Status 2026-07-08: WSL GPU/NVML works after restart. Two S2DN envs now exist:

- `venv_s2dn`: CPU fallback. Python 3.10, PyTorch 2.1.0+cu121, DGL 2.1.0 CPU wheel, LMDB 2.2.1,
  NetworkX 3.4.2, NumPy 1.26.4. PyTorch can see CUDA, but this torch build does not support RTX
  5070 Ti `sm_120`, and DGL has no CUDA device API. CPU smoke training completed for `WN18RR_v1`
  with `--max_links 20 --num_epochs 1`.
- `venv_s2dn_gpu_latest`: active GPU path. Python 3.10, PyTorch 2.11.0+cu128, DGL 2.4.0+cu121
  installed with dependency override, LMDB 2.2.1, NetworkX 3.4.2. Verification passed:
  PyTorch runs CUDA tensors on the RTX 5070 Ti, DGL moves a graph to CUDA, and S2DN smoke training
  runs with `Device: cuda:0`.

Environment report: `/home/admin_wsl/research_kg/logs/s2dn_reproduction/environment_report.md`.

---

## 1. Phase 0: S2DN Reproduction Workspace

Goal: a clean, isolated environment and the data in place, without touching the DBP-5L pipeline.

- [x] Create the workspace at `/home/admin_wsl/research_kg/S2DN/`.
- [x] Clone official S2DN code (github.com/xiaomingaaa/SDN) into it.
- [x] Obtain the GraIL inductive data (github.com/kkteru/grail), which carries `WN18RR_v1..v4`,
      `fb237_v1..v4`, `nell_v1..v4` and their `_ind` test folders.
- [x] Create an isolated env `venv_s2dn`. Do not reuse `RAA-KGC/SimKGC/venv`; it has no dgl or lmdb,
      and installing them there could break the DBP-5L pipeline.
- [x] Install S2DN dependencies in `venv_s2dn`. Start from the README set adapted to Blackwell
      (torch 2.x + cu128, a matching DGL 2.x, lmdb, networkx), not the CUDA-10 requirements.txt set.
- [x] Point S2DN's `data/` at the GraIL inductive folders (symlink `external/grail/data` in, or copy).
- [x] First dataset in place: `WN18RR_v1` and `WN18RR_v1_ind`.

Cross-check asset already on disk:

- [ ] Note that CBLiP and a Phase-0 WN18RR setup already exist in
      `~/research_kg/CBLiP/` and `~/research_kg/WN18RR/`. Keep them as an independent data path and a
      second inductive baseline if the S2DN loader misbehaves.

Environment tests:

- [x] `import torch`, `import dgl`, `import lmdb`, `import networkx` all succeed in `venv_s2dn`.
- [x] `dgl` sees the GPU (or the documented CPU fallback is in effect).

Runner scripts now exist in `/home/admin_wsl/research_kg/S2DN/scripts/`:
`check_env.sh`, `check_gpu_env.py`, `run_smoke_cpu.sh`, `run_wn18rr_v1_cpu.sh`,
`run_smoke_gpu.sh`, `run_wn18rr_v1_gpu.sh`, `run_wn18rr_split_gpu.sh`,
`start_wn18rr_split_detached.py`, and `collect_wn18rr_results.py`.

Important cache guardrail added 2026-07-08: S2DN's LMDB cache path does not encode `--max_links`.
The tiny smoke run and the full WN18RR_v1 run both use
`data/WN18RR_v1/subgraphs_en_True_neg_1_hop_3`. Therefore the smoke script now deletes its partial
cache before and after running, and the full WN18RR_v1 CPU script deletes any existing cache before
starting. If an earlier full run was started immediately after smoke, stop it and restart with the
patched script, otherwise it may train on the 20-link smoke cache.

---

## 2. Phase 1: Reproduce S2DN (English Inductive)

Goal: run the official code end to end and land close to the paper's WN18RR-V1 ranking numbers.

- [x] Run WN18RR_v1 first:
  - [x] `python train.py -d WN18RR_v1 -e sdn_wn_v1_gpu`
  - [x] `python test_ranking.py -d WN18RR_v1_ind -e sdn_wn_v1_gpu`
- [x] Compare against the verified paper target (confirmed against Table 1 of the paper):

  | Metric | WN18RR_v1 target |
  |---|---:|
  | Hits@1 | 74.73 |
  | Hits@10 | 87.64 |
  | MRR | 79.89 |

- [x] Only after v1 is close, run WN18RR v2, v3, v4.
  - [x] WN18RR_v2. Completed on 2026-07-08.
  - [x] WN18RR_v3. Completed on 2026-07-08.
  - [x] WN18RR_v4. Completed on 2026-07-08.
- [x] Compute the WN18RR average Hits@10 and compare against the paper's `81.23`.
- [ ] Then FB15k-237 v1..v4 (paper average Hits@10 `81.25`).
- [ ] NELL last, only after WN18RR and FB15k-237 are stable.

Deliverables:

- [x] `logs/s2dn_reproduction/wn18rr_v1.log`
      Current files are `wn18rr_v1_gpu_detached.log`, `wn18rr_v1_train_gpu.log`, and
      `wn18rr_v1_test_gpu.log`.
- [x] `logs/s2dn_reproduction/results_wn18rr.csv` (per-version Hits@1, Hits@10, MRR, and average)
      Completed for WN18RR v1-v4.
- [x] Environment report: Python, CUDA, PyTorch, DGL versions and the S2DN and GraIL commit hashes.
- [x] If numbers do not match exactly, write the reason: dependency drift, seed differences,
      negative sampling, or data or code mismatch.

Success criterion:

- [x] Official S2DN code runs end to end and lands close to the paper's WN18RR-V1 numbers.

Status 2026-07-08: WN18RR_v1 reproduction completed on the GPU env. Training finished 100 epochs
in about 65 minutes. Best validation AUC reached `0.9198940992355347`. Ranking evaluation completed
in sample mode on `WN18RR_v1_ind` with:

| Metric | Reproduced | Paper target |
|---|---:|---:|
| MRR | 79.95 | 79.89 |
| Hits@1 | 74.73 | 74.73 |
| Hits@5 | 84.84 | - |
| Hits@10 | 87.23 | 87.64 |

Training log:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v1_gpu_detached.log`.
Ranking log:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v1_test_gpu.log`.
Results CSV:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/results_wn18rr.csv`.

WN18RR_v2 reproduction completed on the GPU env. Training finished 100 epochs in about 3 hours
21 minutes. Best validation AUC reached `0.9219824075698853`. Ranking evaluation completed on
`WN18RR_v2_ind` with:

| Metric | Reproduced |
|---|---:|
| MRR | 80.83 |
| Hits@1 | 77.32 |
| Hits@5 | 83.11 |
| Hits@10 | 85.26 |

Training and ranking log:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v2_detached.log`.
Separate ranking log:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v2_test_gpu.log`.

WN18RR_v3 reproduction completed on the GPU env. Training finished 100 epochs in about 5 hours
41 minutes. Best validation AUC reached `0.9186472296714783`. Ranking evaluation completed on
`WN18RR_v3_ind` with:

| Metric | Reproduced | Paper target |
|---|---:|---:|
| MRR | 57.02 | 58.10 |
| Hits@1 | 49.83 | 52.89 |
| Hits@5 | 62.98 | - |
| Hits@10 | 68.84 | 69.52 |

Training and ranking log:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v3_detached.log`.
Separate ranking log:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v3_test_gpu.log`.

WN18RR_v4 reproduction completed on the same GPU env as `sdn_wn_v4_gpu`. Training finished 100
epochs in about 1 hour 39 minutes. Best validation AUC reached `0.9095140099525452`. Ranking
evaluation completed on `WN18RR_v4_ind` with:

| Metric | Reproduced | Paper target |
|---|---:|---:|
| MRR | 77.28 | 78.04 |
| Hits@1 | 74.60 | 75.33 |
| Hits@5 | 78.52 | - |
| Hits@10 | 80.93 | 82.15 |

Full WN18RR v1-v4 reproduced average:

| Metric | Reproduced average | Paper target |
|---|---:|---:|
| MRR | 73.77 | - |
| Hits@1 | 69.12 | - |
| Hits@5 | 77.36 | - |
| Hits@10 | 80.57 | 81.23 |

Training and ranking log:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v4_detached.log`.
Separate ranking log:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/wn18rr_v4_test_gpu.log`.

Compatibility patches needed for the modern env:

- `managers/evaluator.py`: unwrap `(score, kl_loss)` tuples before metric calculation.
- `test_ranking.py`: unwrap `(score, kl_loss)` tuples before ranking.
- `test_ranking.py`: load local full-model checkpoints with `weights_only=False` for PyTorch 2.6+
  compatibility.
- `test_ranking.py`: normalize loaded model `params.device` to the ranking device so CPU ranking
  does not mix CPU graph features with CUDA learned graphs.

Next command pattern for v2-v4:

```bash
cd /home/admin_wsl/research_kg/S2DN
source venv_s2dn_gpu_latest/bin/activate
python scripts/start_wn18rr_split_detached.py 2
```

---

## 3. Phase 2: RuleTrust-S2DN (the Modification)

Goal: beat reproduced S2DN by adding symbolic rule confidence into Structure Refining, keeping
Semantic Smoothing and the original scoring pipeline intact. This modifies the architecture the
mentor liked rather than replacing it.

Before building, a short scoping check so the contribution is defensibly novel:

- [ ] Confirm RuleTrust-S2DN is distinct from GOLD (rules + local structure for noise detection)
      applied to inductive KGC, and from NeuralLP and DRUM (differentiable rules, already S2DN
      baselines). The distinction to defend: we inject mined rule confidence as an edge-reliability
      prior inside S2DN's subgraph denoising, for inductive link prediction, not standalone noise
      scoring. Write one paragraph stating this before coding.
- [ ] Confirm with the mentor that a rule-guided modification is the intended direction (open
      question below) before investing in the full ablation matrix.

New components:

- [ ] `rule_miner.py`: mine length-2 Horn-style relation rules from training triples, form
      `(x, r1, z) + (z, r2, y) -> (x, r, y)`. Keep rules above support and confidence thresholds.
      Consider AnyBURL (arxiv.org/abs/2004.04412) rather than writing a miner from scratch.
- [ ] `rule_features.py`: for each edge in an enclosing subgraph, compute the max rule confidence
      supporting that edge relation.
- [ ] CLI flags: `--use-rule-trust`, `--rule-weight`, `--rule-conf-threshold`, `--rule-cache`.
- [ ] Edge reliability combination:
      `final_edge_logit = neural_edge_logit + rule_weight * (rule_prior - 0.5)`.
- [ ] Deterministic, cached rule files so runs are reproducible.

Ablations:

- [ ] S2DN reproduced baseline.
- [ ] RuleTrust-S2DN (full).
- [ ] RuleTrust-S2DN with `rule_weight=0` (must match baseline behavior).
- [ ] RuleTrust-S2DN with low-confidence rules removed.
- [ ] Optional: Semantic Smoothing only, Structure Refining only.

Success criterion:

- [ ] Beat reproduced S2DN on WN18RR average MRR or Hits@10.
- [ ] Then confirm the gain holds on FB15k-237.

---

## 4. Phase 3: Bridge to the DBP-5L Multilingual Pipeline

Do this only after English RuleTrust-S2DN beats or meaningfully matches S2DN.

- [ ] Write a converter from DBP-5L-Ind data to S2DN/GraIL folder format.
  - Input per language: `DBP5L/ind/{lang}/train.txt`, `valid.txt`, `test.txt`, `support.txt`.
  - Output: `data/dbp5l_{lang}_v1` and `data/dbp5l_{lang}_v1_ind` for en, fr, es, ja, el.
  - Mapping: base train graph from `train.txt`; validation from `valid.txt`; inductive test support
    from `support.txt`; inductive evaluation triples from `test.txt`.
- [ ] Verify the converter preserves the entity-disjoint inductive split (no train/test entity leak).
- [ ] Run graph-only RuleTrust-S2DN per language, English first, then all five.
- [ ] Compare against the existing BGE-M3 substrate (3-seed clean mean 26.51 MRR; best single run
      26.69 MRR) as the text-based reference point.
- [ ] Add text or BGE-M3 features only after graph-only multilingual runs work.

---

## 5. Phase 4: Self-Healing Text Layer

Do this only after the multilingual graph model works. Reuse existing WSL assets rather than
rebuilding.

Assets already present:

- Contaminated descriptions: `DBP5L/processed/entity_descriptions.json`.
- Clean descriptions: `DBP5L/processed/entity_descriptions_clean.json`.
- Backup and no-LLM: `entity_descriptions_backup.json`, `entity_descriptions_nollm.json`.
- Detector: `detector_experiment.py`; result `logs/detector_result.json` (ROC-AUC 0.995).

Pipeline:

- [ ] Detect contaminated descriptions with graph-text consistency (BGE-M3).
- [ ] Quarantine flagged text.
- [ ] Repair with native-language Wikipedia when available.
- [ ] Otherwise use an aligned high-resource description.
- [ ] Final fallback: entity name only, never hallucinated text.
- [ ] Optional later: constrained LLM repair (LLM_sim style), accepted only if graph-text
      consistency improves.

Evaluation:

- [ ] Detector ROC-AUC, precision, recall, F1.
- [ ] Before and after DBP-5L-Ind MRR.
- [ ] Per-language repair impact, with special focus on ja and el (low-resource).

---

## 6. Consolidated Test Plan

### Environment

- [ ] WSL path exists: `/home/admin_wsl/research_kg`.
- [ ] `nvidia-smi` works and `torch.cuda.is_available()` is True.
- [ ] `venv_s2dn` imports torch, dgl, lmdb, networkx.

### Reproduction

- [ ] WN18RR_v1 training completes.
- [ ] WN18RR_v1 ranking script completes.
- [ ] Result table contains Hits@1, Hits@10, MRR.
- [ ] WN18RR_v1 is close to the paper target.
- [ ] WN18RR v1..v4 average computed correctly.

### RuleTrust-S2DN

- [ ] Rule mining creates deterministic cached rule files.
- [ ] `--use-rule-trust false` matches baseline behavior exactly.
- [ ] RuleTrust-S2DN runs on WN18RR_v1.
- [ ] Metrics improve or at least do not collapse.
- [ ] Ablations show whether rule priors help.

### Multilingual

- [ ] Converter preserves the entity-disjoint inductive split.
- [ ] Per-language folders load without parser errors.
- [ ] Graph-only multilingual RuleTrust-S2DN runs for English first.
- [ ] All five languages run.
- [ ] Compared against the BGE-M3 substrate metrics.

### Self-Healing

- [ ] Existing detector result is reproducible.
- [ ] Controlled injection benchmark reports ROC-AUC.
- [ ] Real contamination subset reports flag rate.
- [ ] Cleaned descriptions improve or preserve multilingual KGC.
- [ ] Low-resource language impact reported separately.

---

## 7. Open Questions for the Mentor

These change the plan and should be confirmed before Phase 2 investment.

- [ ] When he says "beat S2DN," does he want a modification inside the S2DN architecture, or is any
      model allowed (including a text or LLM method)? His wording suggests modifying S2DN.
- [ ] Is WN18RR enough for the first reproduction checkpoint, or does he expect WN18RR, FB15k-237,
      and NELL all reproduced first?
- [ ] Does he agree the first modification should be neuro-symbolic rule-guided denoising
      (RuleTrust-S2DN)?
- [ ] For the late-August venue, does he mean WSDM 2027 rather than SIGIR? A late-August deadline
      matches WSDM, not SIGIR, so the paper calendar depends on the answer.

---

## 8. Assumptions, Defaults, and Deadline Reality

- First implementation target is S2DN inside WSL, not Windows.
- Use a separate `venv_s2dn` so the DBP-5L pipeline is never at risk.
- Fix WSL GPU access before any long training.
- First dataset is WN18RR_v1; first serious benchmark is the WN18RR v1..v4 average.
- First architectural novelty is rule-guided Structure Refining.
- Do not add multilinguality until English RuleTrust-S2DN beats or meaningfully matches S2DN.
- Do not add LLM repair until graph-text self-healing evaluation is stable.
- The existing DBP-5L code remains the source of truth for multilingual text baselines and
  contamination experiments.
- Deadline reality: the full ladder is not finishable by 18 July. A realistic first submittable unit
  is "reproduce S2DN and land one principled improvement (RuleTrust-S2DN) on English inductive KGC."
  The full multilingual plus self-healing version is a later-cycle target (WSDM or SIGIR, pending the
  venue question above). The mentor said there is no hurry, which fits.
