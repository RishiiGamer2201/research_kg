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
| 2026-07-12 | `sdn_fb_v1_ruletrust_gpu` | fb237_v1 | paper params, mode=score | 53.19 | 44.15 | 61.95 | 71.22 | 3.90 | Completed. Hits@10 +3.42 over baseline; MRR flat (+0.06); Hits@1 -0.49. rule_scale learned 3.90 from init 0, so the model actively uses the rule signal. Single seed, 205 test triples. Not yet validated: shuffled-rule control pending. |
| 2026-07-12 | `sdn_fb_v1_ruletrust_shuffle0_gpu` | fb237_v1 | paper params, mode=score, --rule-shuffle (control) | 51.03 | 41.22 | 59.76 | 70.00 | 0.12 | Control run; rule bodies deranged onto wrong head relations. rule_scale collapsed from 3.90 to 0.12 (32x drop), so the model ignores shuffled rules: mechanism check passes. But metrics swung 2+ points from baseline in incoherent directions (MRR -2.10, Hits@10 +2.20), so single-seed variance exceeds the effect and no metric claim is supported. Best val AUC 0.8317. |

Paper reference for fb237_v1: MRR 52.10, Hits@1 43.68, Hits@10 67.34.

## 3. Ablation Matrix

Every entry states the flags and what the outcome would mean. An ablation whose result cannot
falsify anything is not worth GPU time.

- [x] **Baseline.** No rule flags. `sdn_fb_v1_paper_gpu`. Establishes the number to beat.

- [x] **Main run, mode=score.** `--use-rule-trust --rule-trust-mode score`
      Supports the hypothesis if MRR or Hits@10 improves over baseline beyond seed noise, and
      `rule_scale` converges clearly positive. Falsifies it if metrics are flat and `rule_scale`
      converges to about 0.
      Result: Hits@10 rose 3.42 points, MRR flat, rule_scale learned 3.90.

- [ ] **Negative control, mode=adjacency.** `--use-rule-trust --rule-trust-mode adjacency`
      Predicted to equal the baseline, because the adjacency prior is measured inert: rule-supported
      pairs are 0.02 percent of node pairs and the max logit change is about 1.1e-4 against a
      nondeterminism floor of 1e-6. If this run somehow improves on baseline, our measurement is
      wrong and everything here needs re-checking.

- [x] **Rules-shuffled control.** `--use-rule-trust --rule-trust-mode score --rule-shuffle`
      `sdn_fb_v1_ruletrust_shuffle0_gpu`, 2026-07-12. Reassigned mined rules to wrong head relations,
      count and confidence distribution held identical.
      Result (split verdict): mechanism passes but metrics inconclusive. rule_scale collapsed from
      3.90 (real) to 0.12 (shuffled), a 32x drop, so the model distinguishes genuine from shuffled
      rules and nearly ignores the fakes. But a should-be-baseline run swung MRR -2.10 and Hits@10
      +2.20 from baseline in incoherent directions, so run-to-run variance exceeds the effect and the
      +3.42 Hits@10 cannot be attributed to the rules from single seeds.

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

- [ ] **Seeds.** DEFERRED to the end (decision 2026-07-17), then required. Rationale: the RuleTrust
      mechanism is not yet locked, so spending about 27 hours of GPU on a 3-seed paired sweep now would
      validate a design that may still change. Plan: keep exploring modifications; once the
      architecture is locked, run 3 to 5 paired seeds (baseline and RuleTrust at the same seed) on the
      final model(s) to get the error bar before any metric claim. A paired-seed launcher already
      exists (`scripts/run_seed_sweep_fb237_v1.sh`, `start_seed_sweep_detached.py`); one attempt on
      2026-07-17 was started and killed at epoch 20, nothing usable. Still gating for any published
      number: the 2026-07-12 shuffle control showed a should-be-baseline run moving metrics by more
      than the observed +3.42 Hits@10, so the effect is inside single-seed variance. No metric claim
      until the paired seeds run on the locked model.

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

### Observed on fb237_v1 (2026-07-12)

rule_scale converged to 3.90 from an initialisation of 0, which is the "converges clearly positive"
case. This means the rule evidence carries information the GNN did not already encode on this split.
The gain is concentrated in Hits@10 (+3.42) rather than Hits@1 (-0.49) or MRR (+0.06), which is
consistent with a high-precision low-recall signal that pulls true tails into the top 10 but does
not sharpen rank 1.

A positive rule_scale is necessary but NOT sufficient evidence. A shuffled-rule control must show
the gain disappears, otherwise the effect could be noise regularisation from one extra learnable
parameter rather than symbolic evidence.

### Shuffle control outcome (2026-07-12)

The make-or-break control ran to completion. `sdn_fb_v1_ruletrust_shuffle0_gpu` used the same paper
hyperparameters and mode=score as the real run, but with `--rule-shuffle` (rule bodies deranged onto
wrong head relations). It ran all 100 epochs and ranked all 205 inductive test triples cleanly. The
control gives a split result.

1. Mechanism passes. rule_scale collapsed from 3.90 (real) to 0.12 (shuffled), a 32x drop, so the
   model strongly distinguishes genuine rules from shuffled ones and nearly ignores the fakes. Best
   validation AUC also orders correctly: real 0.8586 > baseline 0.8527 > shuffle 0.8317. These are
   the least noisy evidence available (a learned parameter and the larger validation set).

2. Metric claim NOT supported. The shuffle run should sit near baseline (rule_scale 0.12, shuffled
   rules cover about 0 percent of cases), yet it swung to MRR 51.03 (2.1 below baseline) and Hits@10
   70.0 (2.2 above baseline) in incoherent directions, and reached a worse validation optimum. A
   should-be-baseline run moved the metrics by more than the real run's apparent +3.42 Hits@10. So
   run-to-run variance on this 205-triple split exceeds the effect size, and the +3.42 cannot be
   attributed to the rules from single seeds.

Three-way comparison:

| Run | rule_scale | best val AUC | MRR | Hits@10 |
|---|---:|---:|---:|---:|
| Baseline `sdn_fb_v1_paper_gpu` | n/a | 0.8527 | 53.13 | 67.80 |
| Real RuleTrust `sdn_fb_v1_ruletrust_gpu` | 3.90 | 0.8586 | 53.19 | 71.22 |
| Shuffle control `sdn_fb_v1_ruletrust_shuffle0_gpu` | 0.12 | 0.8317 | 51.03 | 70.00 |

Overall: the rules carry a real signal the model chooses to use (rule_scale and validation AUC both
order correctly), but no ranking-metric improvement above noise has been demonstrated. Multiple
seeds are now required, not optional.

## 5. Threats to Validity

- [x] **Single seed.** The current runs are one seed each. Seed-to-seed variation on these splits was
      not measured up front. Treat any gain below roughly 1 MRR point as not yet meaningful, and do
      not report a headline improvement from one seed. Demonstrated on 2026-07-12: a should-be-baseline
      control run (shuffle, rule_scale 0.12) differed from baseline by -2.1 MRR and +2.2 Hits@10,
      empirically confirming variance exceeds the effect size at one seed.
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
