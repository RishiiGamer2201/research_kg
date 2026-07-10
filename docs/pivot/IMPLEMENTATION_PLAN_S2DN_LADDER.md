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
| 2026-07-09 | fb237_v1_ind | `sdn_fb_v1_gpu` | Complete, default params | 47.29 | 37.07 | 57.80 | 65.12 |
| 2026-07-10 | fb237_v1_ind | `sdn_fb_v1_paper_gpu` | Complete, paper params | 53.13 | 44.63 | 61.22 | 67.80 |
| 2026-07-09 | fb237_v2_ind | `sdn_fb_v2_gpu` | Stopped, default params | - | - | - | - |
| 2026-07-10 | fb237_v2_ind | `sdn_fb_v2_paper_gpu` | Crashed, CUDA OOM at batch 32 | - | - | - | - |
| 2026-07-10 | fb237_v2_ind | `sdn_fb_v2_paper_bs16_gpu` | Ready to launch, paper params except batch 16 | - | - | - | - |

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
| WN18RR average | Paper average Hits@10: 81.23 | Full v1-v4 reproduced average Hits@10 is 80.57, only 0.66 points below paper. This completes the first reproduction block. Continue the paper ladder with FB15k-237 v1-v4 and NELL before serious RuleTrust claims. |
| fb237_v1_ind default-param run | Paper: MRR 52.10, Hits@1 43.68, Hits@10 67.34 | The first FB15k-237 v1 run used released-code defaults and the hardcoded `lr=0.01`, so it is not the valid paper-parameter reproduction. Keep it only as an engineering record. |
| fb237_v1_ind paper-param run | Paper: MRR 52.10, Hits@1 43.68, Hits@10 67.34 | Corrected v1 completed with `lr=0.0005`, `dim=64`, `batch_size=32`, `hop=3`, and original S2DN architecture. It beats paper v1 by +1.03 MRR, +0.95 Hits@1, and +0.46 Hits@10. |

### Engineering Results

| Date | Component | Result |
|---|---|---|
| 2026-07-08 | WSL GPU access | Fixed after WSL restart |
| 2026-07-08 | S2DN GPU env | Working experimental GPU stack |
| 2026-07-08 | S2DN validation patch | Fixed tuple-output validation crash |
| 2026-07-08 | S2DN ranking patch | Ranking now completes on saved checkpoints |
| 2026-07-08 | Result collection | WN18RR CSV collector added and v1-v4 average computed |
| 2026-07-08 | RuleTrust-S2DN scaffold | Implemented rule miner, rule prior builder, CLI flags, and Structure Refining prior injection |
| 2026-07-08 | RuleTrust smoke test | WN18RR_v1 one-epoch GPU smoke run completed; 10 length-2 rules mined at support >= 2 and confidence >= 0.1 |
| 2026-07-08 | Generic reproduction launcher | Added reusable detached launcher for `wn18rr`, `fb237`, and `nell` splits |
| 2026-07-09 | Eval-only detached launcher | Added `start_eval_only_detached.py` so interrupted ranking can be resumed from a saved checkpoint without retraining |
| 2026-07-09 | FB15k-237 v1 retry evaluation | Original ranking stopped at 108/205 with no metrics; eval-only retry completed all 205 test triples and produced final ranking metrics |
| 2026-07-09 | FB15k-237 v2 default-param stop | Stopped `sdn_fb_v2_gpu` after discovering FB15k-237 paper uses `lr=0.0005` and `dim=64`, while released code forced `lr=0.01` |
| 2026-07-10 | FB15k-237 paper-param launcher | Added `run_fb237_paper_split_gpu.sh` and `start_fb237_paper_split_detached.py` for strict FB15k-237 reproduction |
| 2026-07-10 | S2DN CLI hyperparameter fix | Removed hardcoded `params.lr = 0.01` and `params.batch_size = 32` from `train.py` so paper hyperparameters are actually honored |
| 2026-07-10 | FB15k-237 v1 paper-param result | Corrected `sdn_fb_v1_paper_gpu` completed and beats paper v1 on MRR, Hits@1, and Hits@10 |
| 2026-07-10 | FB15k-237 v2 paper-param launch | Started `sdn_fb_v2_paper_gpu`; log confirms `lr=0.0005`, `dim=64`, `batch_size=32`, `hop=3`, and `use_rule_trust=False` |
| 2026-07-10 | FB15k-237 v2 paper-param crash | `sdn_fb_v2_paper_gpu` crashed in epoch 1 with `CUBLAS_STATUS_EXECUTION_FAILED` then `CUDA: out of memory`. Paper batch 32 with dim 64 and hop 3 does not fit v2 subgraphs on the 16 GB RTX 5070 Ti; the paper used RTX 2080 Ti / RTX 3090 hardware |
| 2026-07-10 | Batch-size fallback tooling | `run_fb237_paper_split_gpu.sh` and `start_fb237_paper_split_detached.py` now take an optional batch-size argument. Non-32 batch runs get distinct experiment and log names (`_bs16`) so paper-batch artifacts are never overwritten. `collect_reproduction_results.py` prefers `_paper` logs, then `_paper_bs16`, then `_paper_bs8`, and no longer falls back to invalid default-param logs |

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
| Can we reproduce S2DN on English inductive KGC? | WN18RR v1-v4 is reproduced; corrected FB15k-237 v1 now beats the paper v1 target. | High | Run corrected FB15k-237 v2-v4, then NELL. |
| Is the GPU setup usable? | Yes; WN18RR v1-v4 completed in the GPU env. S2DN remains subgraph-heavy and not fully GPU-saturated. | High | Reuse the same env for FB15k-237 and NELL. |
| Are we ready to implement RuleTrust-S2DN? | The scaffold is implemented and smoke-tested, but full RuleTrust ablations should wait until FB15k-237 and NELL baselines are reproduced. | High | Finish FB15k-237/NELL reproduction, then run RuleTrust ablations. |
| Is multilingual/self-healing next? | No. It remains downstream after English reproduction and one principled S2DN improvement. | High | Complete S2DN reproduction ladder and RuleTrust comparison first. |

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
- [~] Then FB15k-237 v1..v4 (paper average Hits@10 `81.25`).
  - [x] fb237_v1 default-param run completed on 2026-07-09 as `sdn_fb_v1_gpu`; not valid for paper comparison.
  - [x] fb237_v1 paper-param run completed on 2026-07-10 as `sdn_fb_v1_paper_gpu`.
  - [x] fb237_v2 paper-param run `sdn_fb_v2_paper_gpu` crashed with CUDA OOM at batch 32 on
        2026-07-10; batch 32 with dim 64 and hop 3 does not fit v2 on 16 GB.
  - [ ] fb237_v2 rerun at batch 16 as `sdn_fb_v2_paper_bs16_gpu`, all other paper settings
        unchanged. Document as: paper hyperparameters except reduced batch size due to 16 GB GPU
        memory. If batch 16 still OOMs, use batch 8.
  - [ ] fb237_v3.
  - [ ] fb237_v4.
  - [ ] Batch-size consistency decision: if v2..v4 need batch 16, decide whether to also rerun v1
        at batch 16 so the FB15k-237 average is computed over one batch size instead of mixing 32
        and 16. Cheap option: report v1 at both batch sizes and state the deviation in the paper.
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

FB15k-237 default-parameter reproduction initially started with `fb237_v1` as `sdn_fb_v1_gpu`.
That run completed but used released-code defaults, including a hardcoded `lr=0.01`, so it is not
the valid paper reproduction. After checking Appendix B of S2DN, FB15k-237 was restarted with paper
hyperparameters: `lr=0.0005`, `dim=64`, `batch_size=32`, and `hop=3`. The corrected
`sdn_fb_v1_paper_gpu` run completed all 100 epochs in about 4 hours 46 minutes, then ranked all 205
test triples. Final metrics are MRR `53.13`, Hits@1 `44.63`, Hits@5 `61.22`, and Hits@10 `67.80`.
This run used the original S2DN architecture, not RuleTrust. Current corrected logs:
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/fb237_v1_paper_detached.log`,
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/fb237_v1_paper_train_gpu.log`,
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/fb237_v1_paper_test_gpu.log`, and
`/home/admin_wsl/research_kg/logs/s2dn_reproduction/results_fb237_paper.csv`.

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

- [x] `rule_miner.py`: mine length-2 Horn-style relation rules from training triples, form
      `(x, r1, z) + (z, r2, y) -> (x, r, y)`. Keep rules above support and confidence thresholds.
- [x] `rule_features.py`: for each enclosing subgraph, compute a dense max-confidence rule prior
      supporting the current candidate relation through local length-2 typed paths.
- [x] CLI flags: `--use-rule-trust`, `--rule-weight`, `--rule-conf-threshold`,
      `--rule-min-support`, `--rule-cache`.
- [x] Edge reliability combination:
      `final_graphlearner_logit = neural_graphlearner_logit + rule_weight * (rule_prior - 0.5)`.

Implementation note: the original S2DN Structure Refining module learns a dense node-node
adjacency from node embeddings, not a direct per-original-edge reliability score. RuleTrust
therefore injects the symbolic prior into the dense GraphLearner logits before the existing
probabilistic/KNN graph construction step. With `--use-rule-trust` absent, this code path is
disabled and baseline behavior is preserved.

Status 2026-07-08: RuleTrust scaffold compiled and completed a one-epoch WN18RR_v1 GPU smoke run:

```bash
python train.py -d WN18RR_v1 -e smoke_ruletrust_wn_v1 --gpu 0 --num_epochs 1 \
  --eval_every 1 --num_workers 4 --use-rule-trust --rule-weight 0.5 \
  --rule-conf-threshold 0.1 --rule-min-support 2
```

Smoke result: training reached `Device: cuda:0`, mined cache
`data/WN18RR_v1/ruletrust_rules.json`, found 10 rules, and completed epoch 1 with training AUC
`0.8491`.
- [ ] Deterministic, cached rule files so runs are reproducible.

Code review and measurement, 2026-07-10. The smoke run only proved the code executes, not that the
prior changes the output. Review plus three diagnostics found two bugs (now fixed) and one design
blocker (open). Diagnostics are `diag_attention_scale.py`, `diag_ruletrust_live.py`, and
`diag_ruletrust_report.py`, all read-only forward passes on trained checkpoints.

Bugs found and fixed:

- [x] Boost-only support, not centered. The old `(prior - 0.5)` penalized edges supported by rules
      with confidence below 0.5. Measured: **all 5 WN18RR_v1 rules have confidence below 0.5**
      (max 0.257), so the original code subtracted from every rule-supported edge on WN18RR. Now
      `rule_support = confidence` for supported pairs and `0` otherwise.
- [x] Inject in probability space, not into raw attention. Measured on WN18RR_v1 with the trained
      checkpoint: `attention` is an unbounded ReLU dot product (median 1.65, mean 7.75, max 1.8e4).
      `build_prob_neighbourhood` clamps to `[0.01, 0.99]`, so 60.93 percent of entries saturate at
      the ceiling and the remaining 39.06 percent receive a wildly out-of-scale shift. The boost is
      now applied after the clamp: `p = clamp(p + rule_weight * rule_support, 0.01, 0.99)`.
- [x] Vectorized `build_rule_boost`. The old version did triple-nested Python loops with
      per-element GPU scalar writes and `.tolist()` host syncs on every forward pass. Now composes
      per-relation dense adjacencies with matmul. This supersedes the "cache the prior" task:
      subgraph identity is not plumbed through the batched graph, so vectorizing is the practical
      fix.
- [x] Liveness instrumentation added (`RULETRUST_DEBUG=<n>`), reporting rule-supported pair count,
      headroom, and how many refined-adjacency probabilities actually change. This is the check
      that was missing and that let the inert version look healthy.
- [x] Baseline preserved: with `--use-rule-trust` absent the new code path is skipped entirely, and
      `rule_weight=0` reproduces baseline output to within GPU float nondeterminism (about 1e-6).

Open blocker: rule coverage is far too sparse for the prior to matter.

Measured on `fb237_v1` with the trained `sdn_fb_v1_paper_gpu` checkpoint, 40 real subgraphs:

| Quantity | WN18RR_v1 | fb237_v1 |
|---|---:|---:|
| Mined length-2 rules (min_support 2, conf 0.1) | 5 | 98 |
| Head relations covered | 3 of 9 | 44 of 180 |
| Rules with confidence at or above 0.5 | 0 | 39 |
| Attention in the graded band | 39.06% | 81.78% |
| Rule-supported node pairs | about 0% | 1698 of 13,036,128 (0.01%) |
| Supported pairs with headroom below the ceiling | 0 | 261 (15.37% of supported) |
| End-to-end max logit change | 0.000000 | 0.000144 (noise floor 1e-6) |

Conclusions:

- WN18RR is rule-barren and is the wrong testbed for a rule-based contribution. Its rules are few,
  low confidence, and support pairs the neural attention already keeps.
- On FB15k-237 the injection is now provably live, but it touches 0.01 percent of node pairs and
  only about 6 pairs per subgraph have headroom, so it cannot move MRR or Hits@10.
- Threshold tuning does not fix this. At the most permissive setting (min_support 1, confidence
  0.01) fb237_v1 yields 257 rules over 75 of 180 head relations, roughly 2.5 times more, which
  leaves coverage negligible. The rule language is the limit, not the thresholds.
- Rule support as currently defined is largely redundant with the neural attention: a typed
  length-2 path implies graph proximity, which a ReLU dot-product attention already scores highly.

- [ ] Do not run a RuleTrust ablation until coverage or leverage is fixed. It would report "rules
      do not help" for reasons that have nothing to do with the hypothesis.
- [ ] Decide the redesign direction (see Phase 2c below).
- [x] Note: `rule_miner.py` is a custom length-2 miner, not AnyBURL or AMIE as the mentor research
      note recommended. This is now believed to be a root cause of the coverage problem.

Ablations:

- [ ] S2DN reproduced baseline.
- [ ] RuleTrust-S2DN (full WN18RR_v1).
- [ ] RuleTrust-S2DN with `rule_weight=0` (must match baseline behavior).
- [ ] RuleTrust-S2DN with low-confidence rules removed.
- [ ] Optional: Semantic Smoothing only, Structure Refining only.

Success criterion:

- [ ] Beat reproduced S2DN on WN18RR average MRR or Hits@10.
- [ ] Then confirm the gain holds on FB15k-237.

---

## 3a. Phase 2c: Fixing RuleTrust Leverage (decision required)

The injection now works. The symbolic signal is too sparse to matter. Three ways forward, not
mutually exclusive. Each can be evaluated with `diag_ruletrust_report.py` in minutes, with no
training run, by checking whether rule-supported coverage and headroom rise to a level that could
plausibly shift metrics.

Option A: raise coverage with a real rule miner.

- [ ] Adopt AnyBURL, as the mentor research note originally recommended and as we skipped. It mines
      a much richer language: inverse relations, constants, and rules of length 1 to 3.
- [ ] Include inverse and transpose relations in mining, since S2DN's subgraphs carry them.
- [ ] Re-measure coverage and headroom with the diagnostic before any training run.

Option B: invert the leverage, penalize instead of boost.

- [ ] Boosting acts on 0.01 percent of pairs. Penalizing acts on the 81.78 percent graded mass.
      Use rules to down-weight edges that are contradicted or unsupported, rather than to boost the
      few that are supported.
- [ ] This is closer to what the mentor research note actually described: "detecting contradictions
      or unsupported edges" and "use contradictions or low-rule-support triples as candidates for
      removal or quarantine" (sections 3 and 6). It is also the GOLD and RUDIK framing.
- [ ] Needs care: penalizing every unsupported pair would delete most of the graph. The negative
      signal must be targeted, for example RUDIK-style mined negative rules.

Option C: move the symbolic signal from the adjacency to the score.

- [ ] Apply a relation-level rule prior to the final link-prediction logit, where it directly shifts
      predictions, instead of to the refined adjacency where it is diluted across N by N pairs.
- [ ] Cheapest to test and easiest to ablate, but less architecturally novel than A or B.

Recommendation on file: A plus B. Use AnyBURL to get a rule set with real coverage, then use it to
both support and contradict edges. Option C is the fallback if the adjacency remains too diluted.

---

## 3b. Phase 2b: Semantic Smoothing Modification (deferred second branch)

The mentor research note recommends a two-branch modification: rule confidence into Structure
Refining (Phase 2 above) and, in parallel, guiding Semantic Smoothing with relation, schema, or
text similarity (mentor_plan_research section 7, step 5: regularize Semantic Smoothing so
semantically or ontologically similar relations are easier to smooth together, while unrelated
relations stay apart). Phase 2 deliberately keeps Semantic Smoothing intact to isolate the
Structure Refining effect first. This section keeps the second branch on record so it is deferred,
not dropped.

- [ ] Decision needed: confirm with the mentor whether both branches are expected, or whether
      beating S2DN with the Structure Refining branch alone is sufficient for milestone 2.
- [ ] If pursued: initialize or regularize the Gumbel-Softmax relation-smoothing weights using a
      relation similarity matrix instead of learning all blur weights from scratch.
- [ ] Relation similarity sources to try: relation-name text embeddings (BGE-M3), co-occurrence
      statistics, and heuristic ontology or schema alignment across relations.
- [ ] Ablation: Structure Refining branch only, Semantic Smoothing branch only, both branches.
- [ ] Try this branch if Phase 2 alone does not beat S2DN, or stack it for additional gain.

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
- [ ] Detect bad triples with rule evidence: flag contradictions and low-rule-support edges as
      removal or quarantine candidates (GOLD-style, mentor_plan_research sections 3 and 6). This
      reuses the Phase 2 rule miner and covers structural noise, complementing the text detector.
- [ ] Quarantine flagged text.
- [ ] Repair with native-language Wikipedia when available. Use fuzzy search (n-gram index,
      BK-tree, or vector index) to match noisy entity names and aliases to canonical entity IDs and
      to locate candidate Wikipedia or Wikidata pages.
- [ ] Otherwise use an aligned high-resource description. Use ontology or entity alignment plus
      fuzzy search for cross-lingual lookup when spelling or script differs.
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

---

## 9. Mentor Topic Coverage Map

Every topic the mentor named, and where it lands in this plan. Kept explicit so no topic is silently
dropped and so each can be defended in the next meeting.

| Mentor topic | Relevance | Where it is implemented or studied |
|---|---|---|
| Rule mining, prediction, inference | Very high | Phase 2: `rule_miner.py` mines length-2 Horn rules; confidence becomes a Structure Refining prior. Also Phase 4 for contradiction-based triple quarantine. |
| Neurosymbolic AI | Very high | Phase 2 is the neurosymbolic layer: neural subgraph reasoning plus symbolic rule priors. Umbrella framing for the paper. |
| Heuristic ontology alignment | Medium now, high later | Phase 2b: schema and relation similarity to guide Semantic Smoothing. Phase 3: aligning relations and classes across the five languages. Phase 4: cross-lingual entity lookup for repair. |
| Fuzzy search | Medium | Phase 4: matching noisy names and aliases to canonical entity IDs, finding candidate Wikipedia or Wikidata pages, cross-lingual lookup across scripts. A tool, not the novelty. |
| Gephi | Low as method, useful for analysis | Analysis and figures, not a scored result. Use to visualize original GraIL subgraphs versus S2DN refined subgraphs, and contamination clusters, for the paper and for understanding model decisions. Schedule alongside Phase 2 ablations. |
| B+ trees (Abdul Bari) | Low for novelty, foundational | Fundamentals and scalability: efficient entity ID lookup, alias indexing, adjacency and relation indexes, scalable candidate retrieval. Note that for fuzzy and vector retrieval an n-gram index, BK-tree, or vector index is usually more directly useful than a plain B+ tree. Study item, not a paper contribution. |

Three papers from the mentor meeting and how each is used:

| Paper | Role in this plan |
|---|---|
| S2DN (03121-MaT, AAAI 2025) | The reproduce-and-beat target. Phases 1, 2, 2b. |
| GOLD (EMNLP Findings 2023) | Method source for rule plus structure denoising. Motivates the Phase 2 rule prior and the Phase 4 contradiction quarantine. Also the closest neighbour to differentiate against in the novelty scoping check. |
| LLM_sim (GenAIK 2025) | Repair baseline. Phase 4 optional constrained LLM repair, compared against re-sourcing. Deliberately not used for reproduction. |
