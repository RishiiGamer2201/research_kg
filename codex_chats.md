# Codex Chat Log and Research Notes

This file records the important discussion, decisions, commands, results, and corrections from the
Codex collaboration on the multilingual inductive KGC / S2DN reproduction project.

Workspace:

- Windows project: `C:\developer\research_ai\research_kg\mkgc-multilingual-inductive`
- WSL project: `/home/admin_wsl/research_kg`
- S2DN workspace: `/home/admin_wsl/research_kg/S2DN`
- Active S2DN code: `/home/admin_wsl/research_kg/S2DN/SDN`
- Logs: `/home/admin_wsl/research_kg/logs/s2dn_reproduction`

Current date context during latest work: 2026-07-10, Asia/Calcutta.

---

## 1. Early Research Discussion

The project began as multilingual inductive knowledge graph completion using DBP-5L.

Initial research questions:

- What is the benefit of inductive multilingual KGC?
- Is multilinguality alone enough novelty?
- What real problem does it solve?
- Can the topic be reframed so multilinguality is central, not just a dataset change?
- Can knowledge graphs help solve multilingual failures of LLMs, especially for low-resource
  languages?

We discussed that the original framing, "inductive KGC plus multilingual data", may look too
incremental. The stronger framing became:

> Use knowledge graphs as a multilingual grounding and repair substrate for language models and
> multilingual retrieval systems, especially where low-resource language text is sparse,
> contaminated, misaligned, or hallucination-prone.

This led to several directions:

- Multilingual inductive KGC as a graph-grounded low-resource reasoning task.
- Cross-lingual graph-text consistency as a poisoning/contamination detector.
- Self-healing multilingual KGs, where poisoned or contaminated descriptions are detected,
  quarantined, and repaired.
- Rule-guided or neuro-symbolic structure refinement to strengthen inductive KGC.

The ideas and source links from this phase were saved into project markdown documents in `docs/`.

---

## 2. Mentor Feedback and Pivot

After a meeting with the senior/mentor, the plan changed.

Mentor questions:

- If the self-healing part finds poisoned text, how exactly is it found?
- If contaminated text is cleaned, how exactly is it repaired?
- Which method performs detection and repair?

Topics mentor asked to study:

- Fuzzy search
- Heuristic ontology alignment
- Rule mining
- Prediction / inference
- Neuro-symbolic AI
- Gephi
- B+ trees from Abdul Bari

Papers selected during mentor discussion:

- `C:\Users\admin\Downloads\03121-MaT.pdf`
- `C:\Users\admin\Downloads\2023.findings-emnlp.232.pdf`
- `C:\Users\admin\Downloads\2025.genaik-1.9.pdf`

Mentor asked to start with the AAAI 2025 paper `03121-MaT`, reproduce its score, then beat it in
English inductive KGC before moving to multilingual and self-healing.

The resulting ladder:

1. Reproduce S2DN / MaT-like English inductive KGC.
2. Beat the reproduced English baseline.
3. Extend the improved model to multilingual DBP-5L.
4. Add graph-text self-healing after multilingual graph runs are stable.

---

## 3. Implementation Plan

The main plan file is:

`docs/pivot/IMPLEMENTATION_PLAN_S2DN_LADDER.md`

Core plan:

- Create isolated S2DN reproduction workspace in WSL:
  `/home/admin_wsl/research_kg/S2DN`
- Use official S2DN code and GraIL inductive datasets.
- Do not modify the existing DBP-5L pipeline until English reproduction is stable.
- First reproduce WN18RR v1-v4.
- Then reproduce FB15k-237 v1-v4.
- Then reproduce NELL.
- Only after reproduction, run RuleTrust-S2DN ablations.

Important assumption:

> We should not claim RuleTrust improvement until baseline reproduction is stable on English
> inductive KGC.

---

## 4. Environment Setup

WSL had GPU trouble initially:

- `torch.cuda.is_available()` was false.
- `nvidia-smi` failed in WSL.

After WSL restart, GPU worked:

- GPU: NVIDIA GeForce RTX 5070 Ti
- VRAM: 16 GB
- Active environment: `/home/admin_wsl/research_kg/S2DN/venv_s2dn_gpu_latest`
- PyTorch: 2.11.0+cu128
- DGL: 2.4.0+cu121

Important compatibility patches were made:

- `subgraph_extraction/graph_sampler.py`
  - LMDB map size handling
  - writer env close
  - `num_workers=0` handling
- `subgraph_extraction/datasets.py`
  - LMDB env cache and `max_dbs=6`
- `managers/evaluator.py`
  - unwrap `(score, kl_loss)` tuple before metric calculation
- `test_ranking.py`
  - tuple-output handling
  - `torch.load(..., weights_only=False)`
  - normalize model params/device for CPU ranking

---

## 5. WN18RR Reproduction Results

WN18RR v1-v4 was completed first.

| Dataset | Run | MRR | Hits@1 | Hits@5 | Hits@10 |
|---|---|---:|---:|---:|---:|
| WN18RR_v1_ind | `sdn_wn_v1_gpu` | 79.95 | 74.73 | 84.84 | 87.23 |
| WN18RR_v2_ind | `sdn_wn_v2_gpu` | 80.83 | 77.32 | 83.11 | 85.26 |
| WN18RR_v3_ind | `sdn_wn_v3_gpu` | 57.02 | 49.83 | 62.98 | 68.84 |
| WN18RR_v4_ind | `sdn_wn_v4_gpu` | 77.28 | 74.60 | 78.52 | 80.93 |
| WN18RR average | v1-v4 | 73.77 | 69.12 | 77.36 | 80.57 |

Paper WN18RR average Hits@10 target: `81.23`.

Inference:

- WN18RR reproduction is close to paper.
- Average Hits@10 is only 0.66 points below paper.
- This completed the first reproduction block.

Answer prepared for senior:

> We did not change the architecture for these runs. The remaining gap is likely from stochasticity
> and modern PyTorch/DGL/CUDA differences. WN18RR is reproduced closely enough to move to FB15k-237.

---

## 6. First FB15k-237 Attempt and Mistake

We launched FB15k-237 v1 with the generic launcher:

`sdn_fb_v1_gpu`

Initial result:

| Metric | Paper V1 | First Run | Gap |
|---|---:|---:|---:|
| MRR | 52.10 | 47.29 | -4.81 |
| Hits@1 | 43.68 | 37.07 | -6.61 |
| Hits@10 | 67.34 | 65.12 | -2.22 |

At first this was treated as a weak reproduction. Later we checked the paper appendix and found the
real issue:

- Paper FB15k-237 uses `dim=64`, `lr=0.0005`, `batch_size=32`, `hop=3`.
- Our generic run used code defaults:
  - `dim=32`
  - `lr=0.01`
  - `batch_size=32`
  - `hop=3`
- Worse, `train.py` had a hardcoded line:
  - `params.lr = 0.01`

This meant even passing `--lr 0.0005` would have been ignored.

This mistake cost time. The user explicitly asked not to repeat such mistakes. New reproduction
gate:

1. Check paper appendix hyperparameters before long runs.
2. Verify released code does not override CLI arguments.
3. Start a short dry run and verify actual logged parameters.
4. Only then launch long detached run.
5. Keep experiment names distinct.

---

## 7. Corrected FB15k-237 Paper-Parameter Reproduction

Patch made:

- Removed hardcoded `params.lr = 0.01`
- Removed hardcoded `params.batch_size = 32`
- Added paper-param launchers:
  - `wsl/research_kg/S2DN/scripts/run_fb237_paper_split_gpu.sh`
  - `wsl/research_kg/S2DN/scripts/start_fb237_paper_split_detached.py`
- Updated collector:
  - `collect_reproduction_results.py` now supports `fb237_paper`

Corrected FB15k v1 run:

`sdn_fb_v1_paper_gpu`

Verified hyperparameters:

```text
lr: 0.0005
emb_dim: 64
rel_emb_dim: 64
attn_rel_emb_dim: 64
hidden_size: 64
batch_size: 32
hop: 3
use_rule_trust: False
```

Corrected result:

| Metric | Paper V1 | Corrected Ours | Gap |
|---|---:|---:|---:|
| MRR | 52.10 | 53.13 | +1.03 |
| Hits@1 | 43.68 | 44.63 | +0.95 |
| Hits@5 | - | 61.22 | - |
| Hits@10 | 67.34 | 67.80 | +0.46 |

Inference:

> The weak first FB15k v1 result was caused by wrong/default hyperparameters. With paper
> hyperparameters, v1 beats the paper while keeping the original S2DN architecture.

---

## 8. FB15k-237 v2 Crash

Corrected v2 run was launched:

`sdn_fb_v2_paper_gpu`

Verified hyperparameters:

```text
lr: 0.0005
emb_dim: 64
rel_emb_dim: 64
attn_rel_emb_dim: 64
hidden_size: 64
batch_size: 32
hop: 3
use_rule_trust: False
```

Log check showed the run stopped/crashed before completing epoch 1.

Error:

```text
RuntimeError: CUDA error: CUBLAS_STATUS_EXECUTION_FAILED
CUDA: out of memory
```

Interpretation:

- This is a GPU memory issue.
- Correct paper params fit on v1 but not v2 on our 16 GB RTX 5070 Ti.
- The original paper used RTX 2080 Ti and RTX 3090.
- FB15k-237 v2 with `dim=64`, `batch_size=32`, and `hop=3` likely used RTX 3090 24 GB, or a more
  memory-efficient older CUDA/DGL stack.

User asked how original paper ran it.

Answer:

> The paper reports RTX 2080 Ti / RTX 3090. FB15k-237 v2 likely used RTX 3090 24 GB, while our RTX
> 5070 Ti has 16 GB. Also, our modern PyTorch/DGL stack may have different memory behavior. The
> architecture and dataset are unchanged, but we may need to reduce batch size to fit our hardware.

Recommended next step:

- Re-run FB15k-237 v2 with paper settings except `batch_size=16`.
- Document clearly:
  > Paper hyperparameters except reduced batch size due to 16 GB GPU memory.
- If batch 16 still OOMs, use batch 8.

---

## 9. RuleTrust-S2DN Scaffold

RuleTrust was implemented as a scaffold but not used for baseline reproduction.

Files added/modified:

- `wsl/research_kg/S2DN/SDN/utils/rule_miner.py`
- `wsl/research_kg/S2DN/SDN/utils/rule_features.py`
- `wsl/research_kg/S2DN/SDN/model/dgl/layers.py`
- `wsl/research_kg/S2DN/SDN/model/dgl/graph_classifier.py`
- `wsl/research_kg/S2DN/SDN/train.py`

Flags:

```text
--use-rule-trust
--rule-weight
--rule-conf-threshold
--rule-min-support
--rule-cache
```

RuleTrust idea:

- Mine length-2 Horn-style relation rules:
  `(x, r1, z) + (z, r2, y) -> (x, r, y)`
- Use max supporting rule confidence as a prior on subgraph edges.
- Combine neural edge reliability with rule prior:

```text
final_edge_logit = neural_edge_logit + rule_weight * (rule_prior - 0.5)
```

Smoke test:

- WN18RR_v1 one-epoch GPU smoke run completed.
- 10 length-2 rules mined at support >= 2 and confidence >= 0.1.

Important:

> RuleTrust is not active in current reproduction runs. Current baseline runs have
> `use_rule_trust: False`.

---

## 10. GitHub Pushes

Private repo:

`https://github.com/RishiiGamer2201/research_kg`

Relevant pushed commits:

- `17807b5 Initial research KG workspace snapshot`
- `b56549b Update WN18RR v3 reproduction results`
- `1388b04 Complete WN18RR reproduction results`
- `24d096e Add RuleTrust S2DN scaffold`
- `edea91e Add generic S2DN reproduction launchers`
- `c407e9c Update FB15k reproduction progress`
- `3e61d72 Correct FB15k paper-parameter reproduction`

Latest pushed state includes:

- Corrected FB15k v1 paper-param logs/results.
- FB15k paper-param launchers.
- CLI hyperparameter fix.
- Collector support for `fb237_paper`.
- Updated implementation plan.

---

## 11. Useful Commands

Monitor corrected FB15k v1 paper run:

```bash
wsl -- bash -lc 'tail -f /home/admin_wsl/research_kg/logs/s2dn_reproduction/fb237_v1_paper_detached.log'
```

Monitor corrected FB15k v2 paper run:

```bash
wsl -- bash -lc 'tail -f /home/admin_wsl/research_kg/logs/s2dn_reproduction/fb237_v2_paper_detached.log'
```

Start FB15k paper-param split:

```bash
wsl -- bash -lc 'cd /home/admin_wsl/research_kg/S2DN && python3 scripts/start_fb237_paper_split_detached.py 1'
```

Collect paper-param FB15k results:

```bash
wsl -- bash -lc 'cd /home/admin_wsl/research_kg/S2DN && source venv_s2dn_gpu_latest/bin/activate && python scripts/collect_reproduction_results.py fb237_paper && cat /home/admin_wsl/research_kg/logs/s2dn_reproduction/results_fb237_paper.csv'
```

Sync logs from WSL to Windows repo:

```bash
wsl -- bash -lc 'rsync -a /home/admin_wsl/research_kg/logs/s2dn_reproduction/ /mnt/c/developer/research_ai/research_kg/mkgc-multilingual-inductive/wsl/research_kg/logs/s2dn_reproduction/'
```

---

## 12. Current Status

As of the latest chat:

- WN18RR v1-v4 reproduction: complete and close to paper.
- FB15k-237 v1:
  - default-param run complete but not valid for paper comparison.
  - corrected paper-param run complete and beats paper v1.
- FB15k-237 v2:
  - paper-param run with batch size 32 crashed due to CUDA OOM.
  - recommended next run: `batch_size=16`, all other paper settings unchanged.
- NELL: not started yet.
- RuleTrust: scaffold implemented, not used for baseline reproduction.
- Multilingual DBP-5L bridge: not started yet.
- Self-healing text layer: not started yet.

Most important lesson:

> For strict reproduction, always verify the paper appendix and actual logged hyperparameters before
> starting long runs.

