# RuleTrust-S2DN Experiment Ledger

Running record for the RuleTrust ablation study. Companion to
[IMPLEMENTATION_PLAN_S2DN_LADDER.md](IMPLEMENTATION_PLAN_S2DN_LADDER.md), which holds the reasoning
and the measurements that led here. This file tracks runs, controls, and what each result would
mean.

## 1. Hypothesis

Stated so it can be falsified:

> Entity-independent symbolic rule evidence adds predictive signal to a neural subgraph model on
> inductive link prediction, because unseen entities blunt the GNN while relation-level rules
> transfer unchanged.

Supporting measurement, on fb237_v1 with the target edge removed from the subgraph so there is no
leakage:

| Quantity | Train subgraphs | Inductive test (unseen entities) |
|---|---:|---:|
| Positives with rule support | 38.8% | 36.1% |
| Negatives with rule support | 0.8% | 0.1% |
| Rule-only AUC | 0.690 | 0.680 |

The rule signal does not degrade on unseen entities. It is high precision and low recall: it fires
on roughly 36 percent of cases and is almost never wrong when it fires.

Design: `output = fc_layer(g_rep) + rule_scale * rule_target_score`, where `rule_scale` is a
learnable scalar initialised to 0. Training therefore starts bit-identical to the baseline and the
model must learn to trust the rules. Parameter count goes from 122896 to 122897, exactly one extra
parameter.

## 2. Results Ledger

| Date | Experiment | Dataset | Config | MRR | Hits@1 | Hits@5 | Hits@10 | rule_scale | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 2026-07-10 | `sdn_fb_v1_paper_gpu` | fb237_v1 | paper params, no rules | 53.13 | 44.63 | 61.22 | 67.80 | n/a | Reproduction baseline. Beats paper v1 (52.10 / 43.68 / 67.34). |
| 2026-07-10 | `sdn_fb_v1_ruletrust_gpu` | fb237_v1 | paper params, mode=score | pending | pending | pending | pending | pending | Running. Only difference from baseline is `--use-rule-trust`. |

Paper reference for fb237_v1: MRR 52.10, Hits@1 43.68, Hits@10 67.34.

## 3. Ablation Matrix

Every entry states the flags and what the outcome would mean. An ablation whose result cannot
falsify anything is not worth GPU time.

- [x] **Baseline.** No rule flags. `sdn_fb_v1_paper_gpu`. Establishes the number to beat.

- [~] **Main run, mode=score.** `--use-rule-trust --rule-trust-mode score`
      Supports the hypothesis if MRR or Hits@10 improves over baseline beyond seed noise, and
      `rule_scale` converges clearly positive. Falsifies it if metrics are flat and `rule_scale`
      converges to about 0.

- [ ] **Negative control, mode=adjacency.** `--use-rule-trust --rule-trust-mode adjacency`
      Predicted to equal the baseline, because the adjacency prior is measured inert: rule-supported
      pairs are 0.02 percent of node pairs and the max logit change is about 1.1e-4 against a
      nondeterminism floor of 1e-6. If this run somehow improves on baseline, our measurement is
      wrong and everything here needs re-checking.

- [ ] **Rules-shuffled control.** Reassign mined rules to wrong head relations, keep count and
      confidence distribution identical. Any gain must DISAPPEAR. If a shuffled rule set still
      helps, the gain is not coming from symbolic evidence (it would be acting as noise
      regularisation) and the headline result is invalid. This is the single most important control
      in the study.

- [ ] **Weaker miner.** `--rule-no-inverse` (forward-only length-2, the v1 miner: 142 rules over 62
      of 180 head relations, versus v2's 462 over 93).
      Tests whether rule coverage drives the effect. Expect a smaller gain. If the gain is identical,
      coverage is not the mechanism and the story needs revisiting.

- [ ] **Confidence threshold sweep.** `--rule-conf-threshold` in {0.01, 0.1, 0.3, 0.5}.
      Trades coverage against rule precision. Note that 0.5 admits only 168 of 462 rules on fb237_v1.

- [ ] **Support threshold sweep.** `--rule-min-support` in {1, 2}.
      At min_support 1 and conf 0.01 the miner yields 257 forward-only rules over 75 of 180 head
      relations; measure whether the extra low-support rules help or add noise.

- [ ] **Rule body length.** `--rule-max-len 1` versus 2. Isolates how much comes from direct
      relation implications versus two-hop composition.

- [ ] **Seeds.** At least 3 seeds for baseline and for mode=score before any claim is made. See
      threats to validity.

- [ ] **Generalisation across splits.** fb237_v2, v3, v4.
      Note: v2 previously crashed with CUDA OOM at batch 32 on the 16 GB RTX 5070 Ti. Use batch 16
      and rerun the baseline at batch 16 too, so the comparison holds batch size fixed.

- [ ] **WN18RR.** Deliberately excluded as a testbed. It yields only 5 rules, none above 0.5
      confidence, so there is no symbolic signal to inject. Report this as a finding, not a gap.

## 4. Interpreting the Learned rule_scale

`rule_scale` is initialised to 0 and is the model's own statement about how much the symbolic
evidence is worth. It is more informative than the headline metric.

- Converges clearly positive: the rule evidence carries information the GNN does not already encode.
  This is the contribution, and the size of the weight is reportable.
- Converges near 0: the GNN already contains the rule signal on this split. This matches the naive
  combination test, where adding the rule score to the trained GNN's logit moved train AUC only from
  0.8814 to 0.8825. This is a finding and not a failure. It would direct the work toward settings
  where entity-independent signal is worth more: sparser graphs, harder splits, fewer training
  triples, and the multilingual case where some language graphs are structurally impoverished.
- Converges negative: something is wrong. Rule support is a high-precision positive indicator, so a
  negative weight would indicate a sign error or a data alignment bug. Stop and re-verify the
  relation2id alignment between the mined rules and `graph.edata['type']`.

## 5. Threats to Validity

- [ ] **Single seed.** The current runs are one seed each. Seed-to-seed variation on these splits has
      not been measured. Until multiple seeds exist, treat any gain below roughly 1 MRR point as not
      yet meaningful. Do not report a headline improvement from one seed.
- [ ] **Small test set.** fb237_v1's inductive test set has 205 triples. One triple is worth roughly
      0.5 percentage points of Hits@k, so metric noise is substantial and confidence intervals are
      wide.
- [ ] **Batch-size deviation.** If v2 to v4 require batch 16 for memory, the baseline must be rerun
      at batch 16 as well. Otherwise the FB15k-237 average mixes batch 32 (v1) with batch 16
      (v2 to v4) and the comparison is not clean.
- [ ] **Rule mining uses the training graph only.** Confirm no rule is mined from validation or test
      triples. The subgraph also has the target edge removed, so the target itself cannot support its
      own rule. Both properties are relied on and should be asserted in code, not assumed.
- [ ] **Redundancy with the GNN.** Rule paths are graph paths the GNN can also see. The inductive
      transfer result is the reason to expect a gain anyway, but the shuffled control is what proves
      it.

## 6. Do Not Repeat

Traps already hit in this project. Each cost hours.

- Paper hyperparameters live in the appendix, and the released S2DN code had a hardcoded
  `params.lr = 0.01` that silently overrode the CLI `--lr`. A 4h46m run was invalidated. Always grep
  the training script for assignments to `params.*` after argument parsing.
- A smoke test proves the code executes. It does not prove the change has any effect. The original
  RuleTrust prior passed a one-epoch smoke run while being provably inert. Always add an assertion
  or diff print showing the change alters the output.
- Always verify the logged hyperparameters, not the command line, before letting a long run proceed.
- `nohup ... &` inside `wsl -- bash -lc` does not survive the wsl.exe session. Launch detached runs
  with `scripts/start_*_detached.py`, which uses `Popen(start_new_session=True)`.
- Writing shell scripts into WSL through a `wsl bash -lc` heredoc silently strips `$1` and `${VAR}`.
  Write via the UNC path instead, then verify the bytes with `cat -A`.
