# Phase 2 — Frozen baseline matrix (P2.1)

Frozen **before** any expensive run. Changing anything here requires a new ledger row stating
what changed and why; results computed under a different protocol are not comparable.

## 1. Fold / seed design

| Axis | Decision |
|---|---|
| **Cross-fold generality** | Every baseline runs on **all three folds** (`fold0_seed13`, `fold1_seed42`, `fold2_seed79`) with **one common training seed = 42**. |
| **Seed variance** | **Three paired seeds {42, 123, 777}** on the **designated development/reporting fold = `fold0_seed13`**. |
| **Full 3×3** | **NOT adopted** (decision R-043, 2026-07-18): measured cost 333.1 GPU-h ≈ 16.7 days vs 185.2 h ≈ 9.3 days for the fallback — +148 h buys only fold×seed interaction estimates that no planned claim requires, with Phases 3–5 still ahead on one GPU. |
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
| B-lex | BM25 / exact-name match | CPU | lexical floor; exposes the answer-mention effect; **retained as lexical experts** (below) |
| B-str | degree + PPR (relation-free) | CPU | structural floor (already measured in R-034) |
| B-mbert | mBERT bi-encoder | GPU | encoder control |
| B-xlmr | XLM-R bi-encoder | GPU | encoder control |
| **B0** | **BGE-M3 + LoRA r16, CRR, HN K=7** | GPU | locked anchor baseline |
| B-struct-ind | one corrected structural inductive baseline | GPU | structural comparison on v2 folds |

## 4. Required reporting views (never collapsed into one number)
Every model reports **all four**, per direction (head / tail / combined):

1. **Natural text** (primary view) — headline retrieval number.
2. **Mentioned vs unmentioned** split (`by_mention`) — isolates the answer-mention effect.
3. **Alias-masked** (`descriptions_v2_masked.json`, 14.2% text removed) — **stress diagnostic**, not a
   clean generalization measure: masking removes legitimate context along with answer names, so it
   under-states achievable performance. Report it as a robustness/stress number.
4. **Missing-text** (`descriptions_v2_missing_text.json`, name-only) — no-description floor.

Plus: per-language, per-evidence-budget (0/1/3/5), macro-language and worst-language.

**Lexical run provenance (recorded per result cell, R-042):** query batch size, scoring mode,
tokenizer, tie policy, BM25 k1/b, filter policy, view hash, targets hash, and per language the
candidate-order hash, vocabulary hash and BOTH `sparse_matrix_exact_hash` (raw canonical CSR
bytes: shape, dtypes, little-endian normalized indptr/indices/data) and
`sparse_matrix_tolerant_hash` with `sparse_matrix_tolerant_decimals` recorded. The exact hash
detects sub-epsilon scoring drift; the tolerant hash absorbs cross-platform float noise.

**Lexical results are reported by direction × mention bucket, never as aggregate MRR alone**
(answer exposure is strongly directional). Lexical baselines run on the **full** target set —
they are cheap once vectorized — so no sampling CI is needed; if any run is sub-sampled, its
95% CI on MRR must be reported alongside (`mrr_ci95`).

## 4b. Expert roles are SEPARATE (binding for P2.3 fusion and P3 TrustRouter)

| Component | Role | Allowed uses | Prohibited |
|---|---|---|---|
| **`name_match`** | **mention / leakage DETECTOR and router feature only** | leakage diagnostics; a router *feature* signalling "the answer is probably named in this text"; mentioned/unmentioned stratification | **never a retrieval expert; never a fallback; must NOT be routed missing-text or quarantined-text queries** — its non-mention signal is effectively zero |
| **BM25 / BGE learned-sparse** | genuine **lexical retrieval experts** | P2.3 sparse side of calibrated dense/sparse/multi-vector fusion; standalone expert; fallback when the dense expert is unavailable | — |
| **Dense (BGE-M3) / structure / name-only** | **missing- or quarantined-text fallbacks** | the fallback path when a description is absent, suspect, or quarantined | — |

Rationale: `name_match` scores essentially at floor once the answer is not named, so routing a
missing-text query to it would produce confident-looking noise. BM25 retains real non-mention
signal and is therefore a legitimate expert. Quantitative support comes from **R-042** (full
target set); the earlier R-040/R-041 numbers are invalidated for biased sampling.

**Sufficiency rule:** beating these baselines on natural aggregate MRR is NOT sufficient. A
neural model must also beat them on (a) the unmentioned bucket, (b) both directions separately,
and (c) at matched evidence budgets — otherwise it has only learned the mention shortcut.

## 5. Claim discipline (mandatory)
Natural-text MRR **must not** be described as relational generalization: on v2, unmentioned MRR
is ~1% versus 5–18% mentioned (R-037), so the natural-text number substantially reflects
answer-mention reading.

**The primary relational-generalization indicator is the `unmentioned` query bucket** — it keeps
the text intact and simply selects the queries whose description does not name the answer. The
alias-masked view is a *stress* diagnostic (it also deletes legitimate context) and must not be
presented as the clean generalization measure. Any abstract/table sentence violating this is a
defect.

**Negative-sampling policy (R-038):** every v2 result must be trained under
`negpol-v2-train-only` (negatives drawn from the fold's training entities only). Runs trained
with the old all-entity negative pool are not strictly concept-inductive and cannot be cited as
v2 baselines.

## 6. Order of work (cheap → expensive)
1. Wiring smoke tests: training reads v2 fold splits + inverse-clean support; tiny-config run.
2. Cheap CPU baselines (B-lex, B-str) on all three folds.
3. B0 on fold0 seed 42 → profile GPU-hours, then the fold/seed blocks in §1.
4. Encoder controls (mBERT, XLM-R), then the structural inductive baseline.
5. Only then screen extensions (P2.2+).
