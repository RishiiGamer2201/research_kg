# Phase 2 — Frozen baseline matrix (P2.1)

Frozen **before** any expensive run. Changing anything here requires a new ledger row stating
what changed and why; results computed under a different protocol are not comparable.

## 1. Fold / seed design

| Axis | Decision |
|---|---|
| **Cross-fold generality** | Every baseline runs on **all three folds** (`fold0_seed13`, `fold1_seed42`, `fold2_seed79`) with **one common training seed = 42**. |
| **Seed variance** | **Three paired seeds {42, 123, 777}** on the **designated development/reporting fold = `fold0_seed13`**. |
| **Full 3×3** | Only if compute permits after the two blocks above; not assumed. |
| **Reporting** | Cross-fold = mean ± sd over folds (seed 42). Seed variance = mean ± sd over seeds (fold0). Never pool the two into one ± figure. |

`fold0_seed13` is the development/reporting fold: all screening decisions are made there.
Folds 1–2 (seed 42) exist to show the conclusion is not fold-specific.

## 2. Held-constant across every encoder / method
Any run that deviates is invalid for the comparison table.

| Component | Frozen value |
|---|---|
| Descriptions (primary track) | `ind_v2/tracks/descriptions_v2_primary.json` (`d1afcf20…`, 0 cross-lang) |
| Support exposure | **inverse-clean** ordered pools, `support_pool_inverse_clean.json` (prefix k∈{0,1,3,5}) |
| Eval targets | per fold `budgets/eval_targets_test.json` (fixed across budgets) |
| Candidate universes | `candidates_all.json` (`6a641485…`) + `candidates_within_{lang}.json` |
| Filter | single complete known-fact filter, one `filter_hash` for all budgets |
| Directions | head + tail with the `reverse of` reciprocal marker; head/tail/combined reported separately |
| Tie handling | average tied ranks |
| Negatives | identical scheme + count across encoders (CRR, hard-neg K=7 from epoch 5) |
| Evaluator | one `eval_dbp5l.py` build; `--v2-targets`, `--directions tail,head` |
| Manifests | every run writes `manifest.json` (git commit, input hashes, seed, model revision) |

## 3. Baselines (P2.1 suite)
Cheap first (CPU), then GPU:

| # | Baseline | Cost | Purpose |
|---|---|---|---|
| B-lex | BM25 / exact-name match | CPU | lexical floor; also exposes the answer-mention effect |
| B-str | degree + PPR (relation-free) | CPU | structural floor (already measured in R-034) |
| B-mbert | mBERT bi-encoder | GPU | encoder control |
| B-xlmr | XLM-R bi-encoder | GPU | encoder control |
| **B0** | **BGE-M3 + LoRA r16, CRR, HN K=7** | GPU | locked anchor baseline |
| B-struct-ind | one corrected structural inductive baseline | GPU | structural comparison on v2 folds |

## 4. Required reporting views (never collapsed into one number)
Every model reports **all four**, per direction (head / tail / combined):

1. **Natural text** (primary view) — headline retrieval number.
2. **Mentioned vs unmentioned** split (`by_mention`) — isolates the answer-mention effect.
3. **Alias-masked** (`descriptions_v2_masked.json`, 14.2% text removed) — leak-reduced view.
4. **Missing-text** (`descriptions_v2_missing_text.json`, name-only) — no-description floor.

Plus: per-language, per-evidence-budget (0/1/3/5), macro-language and worst-language.

## 5. Claim discipline (mandatory)
Natural-text MRR **must not** be described as relational generalization: on v2, unmentioned MRR
is ~1% versus 5–18% mentioned (R-037), so the natural-text number substantially reflects
answer-mention reading. Generalization claims must cite the **unmentioned** and **alias-masked**
results. Any abstract/table sentence violating this is a defect.

## 6. Order of work (cheap → expensive)
1. Wiring smoke tests: training reads v2 fold splits + inverse-clean support; tiny-config run.
2. Cheap CPU baselines (B-lex, B-str) on all three folds.
3. B0 on fold0 seed 42 → profile GPU-hours, then the fold/seed blocks in §1.
4. Encoder controls (mBERT, XLM-R), then the structural inductive baseline.
5. Only then screen extensions (P2.2+).
