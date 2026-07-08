# AAAI 2027 — Research Task Tracker
**Paper:** Multilingual + Inductive KGC with CRR Loss, Hard Negative Mining & Rich Descriptions on DBP-5L-Ind
**Deadline:** Abstract ~Jul 20 | Full Paper ~Jul 27 | **Today:** Jul 2 | **Days left:** 18 (abstract) / 25 (paper)

---

## ⚠️ PUBLISHABILITY ASSESSMENT (added 2026-07-02)

**Honest current estimate: ~15-25% acceptance chance at AAAI main track as currently documented** —
below the historical base rate (~20-24%). This is not a reason to panic; it's a reason to spend the
next 5-6 days on the four items below before anything else. Full reasoning kept here so we don't
lose the "why," not just the "what."

### What's genuinely strong (keep, protect, don't dilute)
- **DBP-5L-Ind benchmark construction** — real, citable, first entity-disjoint inductive split over DBP-5L.
- **Negative result on cross-lingual anchors** (15.59% → 3.17%) — rare and scientifically interesting;
  most papers only report what worked.
- **CRR + Hard Negative synergy** — genuine, non-obvious interaction effect (+15% relative over CRR alone).
- **Real ablation table** — incremental per-component contribution is documented.

### What will sink the paper if left unaddressed
1. **Zero external baselines run.** ablation_plan.md names RAA-KGC-BERT, SimKGC, ALIGNKGC, MKGC/KL-GMoE
   as the comparison set — none appear in results yet. Every number is internal-only (vs. our own
   zero-shot). Reviewers cannot tell if 15.59% MRR is good or bad. Missing baselines is close to an
   automatic weakness flag at AAAI.
2. **Absolute MRR (15.59%) has no external anchor.** Could look excellent or weak depending on what
   ALIGNKGC/SS-AGA score on a comparable setting — currently unknowable.
3. **Single run per config, no seeds.** Can't defend whether a 0.6% MRR delta (e.g. Run A vs Run B) is
   real or noise if a reviewer challenges it.
4. **"Kitchen sink" risk.** Benchmark + model + 4 findings + 1 negative result in one 7-8 page paper.
   Needs ONE headline claim with everything else organized in support of it, or it reads like a lab
   notebook rather than a paper thesis.
5. **No Related Work section yet.** Can't verify our gap claim is actually still open without it.

### The single highest-leverage action
Run **ALIGNKGC** as an external baseline on DBP-5L-Ind. Their code is public, it targets the exact
same "alignment seeds break when inductive" gap we exploit, and it's the one number that lets a
reviewer calibrate everything else in the paper.

---

## 🔴 PHASE A — Must-Do Before Writing Continues (NEW, do this first, ~5-6 days)

Ordered by priority. Do not start deep writing on Sections 1-4 until #4 (framing) is locked, since it
determines how everything else gets written.

- [ ] **A1. Run ALIGNKGC as external baseline** on DBP-5L-Ind (2-3 days — code is public)
- [ ] **A2. Run 3 seeds on Run B (best config)**, report mean ± std for every Table 1/2 cell (1 day)
- [ ] **A3. Paired bootstrap significance test** between Run B and the next-best ablation row, once
      seeds exist from A2 (0.5 days)
- [ ] **A4. Lock the single headline claim** — decide: is this a *benchmark* paper, a *negative-result*
      paper, or a *synergy* paper? Everything else gets reframed around this one choice. (0 days —
      pure writing/framing decision, do this in parallel with A1/A2)
- [ ] **A5. Write Section 2 (Related Work)** — needed to verify the gap claim is still real (1-2 days)

### Should-do (do if A1-A5 land with time to spare)
- [ ] **B1. Add Wikidata5M-Ind monolingual results** — original plan had this; gives a monolingual
      anchor point and directly supports "multilingual is harder" framing (1-2 days, pipeline from
      Week 1 already works)
- [ ] **B2. Run SimKGC (English-only) as a second baseline** — isolates whether multilingual text
      helps even on English-only test entities (1 day — code already working from Week 1)
- [ ] **B3. Error analysis on JA** (weakest language, 7.68% MRR) — is it description coverage, script
      tokenization, or something else? Turns an unexplained weak number into a defensible one (1 day)
- [ ] **B4. Manual quality spot-check on Llama 3.2-generated descriptions** (1,042 entities) — pre-empts
      "how do we know these aren't hallucinated garbage" (0.5 days)

### Explicitly cut for this submission cycle (do not attempt before deadline)
- IER reranking, KL-GMoE adapters, CBLiP structural fusion — see Additions Table below for why.

---

## 📋 ADDITIONS TABLE — Everything We Could Implement, Ranked

| # | Addition | Effort | Expected impact on acceptance odds | Priority |
|---|---|---|---|---|
| 1 | Run ALIGNKGC as external baseline on DBP-5L-Ind | 2-3 days | **High** — the single biggest gap; without it reviewers can't calibrate any result | **Must-do (A1)** |
| 2 | Run 3 seeds on Run B, report mean ± std | 1 day | **High** — turns every ablation number from "maybe noise" into a defensible claim | **Must-do (A2)** |
| 3 | Add Wikidata5M-Ind monolingual results | 1-2 days | Medium-high — monolingual anchor point, supports core framing | Should-do (B1) |
| 4 | Lock single headline claim / paper framing | 0 days | **High**, free | **Must-do (A4)**, do first |
| 5 | Run SimKGC (English-only) as second baseline | 1 day | Medium — cheap, code already exists | Should-do (B2) |
| 6 | IER reranking (from MKGC/KL-GMoE paper) | 2-3 days, inference-only wrapper | Medium — free MRR bump if it works, not core to novelty claim | Nice-to-have, cut this cycle |
| 7 | KL-GMoE-style adapters | 5-7 days, nontrivial grouped-LoRA routing engineering | Low-medium given remaining time — high risk of not finishing | Cut this cycle |
| 8 | CBLiP structural fusion | 4-5 days | Low — already flagged stretch/optional in skeleton.md | Cut this cycle |
| 9 | Paired bootstrap significance test | 0.5 days (needs seeds from #2 first) | Medium — makes Table 1 deltas credible | Should-do (A3) |
| 10 | Manual quality check on LLM-generated descriptions | 0.5 days | Low-medium — pre-empts a hallucination-quality reviewer question | Nice-to-have (B4) |
| 11 | Write Related Work section | 1-2 days | **High**, but writing not experiments | **Must-do (A5)** |
| 12 | Error analysis on JA (weakest language) | 1 day | Medium — explains rather than hides the weak number | Should-do (B3) |

**Rule of thumb applied:** items 6-8 are all explicitly marked "stretch/optional" in skeleton.md's
original design. Adding them now risks leaving items 1/2/4/11 (the ones that actually determine
acceptance odds) unfinished. Skip them for this cycle; they're legitimate future-work material.

---

## CURRENT STATUS
- **Best model:** Run B — CRR + HN K=7 + max_length 128 + LoRA rank 16 → **MRR 15.59%**
- **GPU:** Run F training (40 epochs, lr 3e-4, ~9h) ← running now
- **Next:** Phase A (baselines + seeds + framing) takes priority over Run G and further tuning
- **Paper:** Do NOT start Section 5 prose until A4 (framing) is locked — numbers are ready but the
  narrative wrapper around them isn't decided yet

---

## Phase 0 — Environment & Baseline ✅
- [x] WSL2 + Ubuntu 26.04 | Python 3.10 | PyTorch 2.11 cu128 | RTX 5070 Ti
- [x] CBLiP baselines: WN18RR_v1 MRR=0.880 | FB15k-237_v1 MRR=0.617 | NELL_v1 MRR=0.720
- [x] SimKGC on WN18RR: MRR=0.656 | LaBSE sanity check PASSED | BGE-M3 memory test GREEN

---

## Phase 1 — CRR Loss Implementation ✅
- [x] Implement crr_loss.py + rho sweep (WN18RR / FB15k-237 / NELL)
- KEY FINDING: rho must be tuned per dataset — NELL benefits (rho=0.3 +12%), FB15k-237 hurts

---

## Phase 2 — Architecture & Data Preparation ✅

### Model (train_dbp5l_lora.py) ✅
- [x] BGE-M3 + LoRA trainer (rank 8 base, rank 16 best)
- [x] Fix AMP/GradScaler WSL2 Blackwell crash (bfloat16)
- [x] Fix CRR NaN loss (exp overflow → clamped to [-80, 80])
- [x] Hard negative mining: entity cache + GPU top-K retrieval + non-square logit matrix
- [x] Global negative loss (--global-neg flag, SimKGC-style, 56K candidates)
- [x] Curriculum learning (--curriculum flag, ramps hard_neg_k from 1 → target)
- [x] --max-length, --lora-rank parameters added

### DBP-5L-Ind Benchmark ✅ — PAPER CONTRIBUTION #1
- [x] Entity-disjoint inductive train/valid/test splits (build_dbp5l_ind.py)

| Lang | Train entities | Unseen test | Train triples | Test triples |
|------|---------------|-------------|---------------|--------------|
| EN   | 10,506        | 2,626       | 44,801        | 18,409       |
| FR   | 8,060         | 2,014       | 25,968        | 11,154       |
| ES   | 8,087         | 2,021       | 26,902        | 15,094       |
| JA   | 5,979         | 1,494       | 13,531        | 7,237        |
| EL   | 3,216         | 804         | 7,054         | 2,579        |
| **TOTAL** | **35,848** | **8,959** | **118,256** | **54,473** |

### Entity Description Enrichment ✅
- [x] KG-neighbor descriptions: all 56,589 entities
- [x] Wikipedia/DBpedia abstracts (original fetch): 33,637 entities (59.4%)
- [x] Phase 3c extra Wikipedia REST API fetch: +7,436 abstracts (78% hit on 9,535 name-only)
- [x] Llama 3.2:3b via Windows Ollama (172.17.0.1:11434): +1,042 LLM-generated descriptions
- **Final: ~42,115 entities (74.4%) have rich text descriptions**
- [ ] **B4 (new): manual quality spot-check on the 1,042 LLM-generated descriptions**

---

## Phase 3 — Core Training Runs ✅

| Run | Config | MRR | Note |
|-----|--------|-----|------|
| v1 | Name-only, InfoNCE | 0.41% | No semantic signal in descriptions |
| v2 | KG-neighbor, InfoNCE | ~1.1% | Train/eval query format mismatch |
| Row 1 | KG+relation, InfoNCE | 3.10% | First correct run |
| Row 3 | KG+rel, CRR rho=0.1 | 3.33% | CRR marginal gain without Wikipedia |
| Row 5-naive | KG, CRR+naive XL anchors | 1.53% | Wrong anchor source — not cross-lingual pairs |
| Row 1-wiki | Wikipedia, InfoNCE | **10.02%** | +10x from abstracts — CRITICAL finding |
| Row 3-wiki | Wikipedia, CRR | **9.86%** | CRR helps JA (+2.9%) but hurts EN/EL |
| Row 5-wiki | Wikipedia, CRR+XL | **3.17%** | NEGATIVE: XL anchors fight BGE-M3 alignment |

---

## Phase 3b — Hard Negative Mining ✅

- [x] Row 1-HN: InfoNCE + Wikipedia + HN K=7 → **MRR=9.49%**
  - HN hurt FR/ES (already separated), helped JA/EL (confused entities)
- [x] Row 3-HN: CRR + Wikipedia + HN K=7 → **MRR=11.36%** ← prev best before Phase 3c
  - FR: 16.88% | ES: 17.89% | JA: 8.17% | EN: 5.11% | EL: 2.93%

---

## Phase 3c — Performance Push (Enriched Descriptions) ✅

| Run | Config | MRR | H@1 | H@10 | vs 3-HN |
|-----|--------|-----|-----|------|---------|
| **A** | CRR + HN K=7 + ml=128 + enriched desc | **14.95%** | 9.04% | 26.42% | +31% |
| **B** | + LoRA rank 16 | **15.59%** | 9.78% | 26.57% | +37% ← **BEST** |
| C | + Global Neg (stale cache) | 13.20% | 6.93% | 25.06% | -15% ❌ |

**Run A insight:** max_length 128 + 7,436 new Wikipedia abstracts → EN +123%, EL +301%
**Run B insight:** LoRA r16 adds +0.64% MRR consistently across all langs
**Run C insight:** Global neg (stale epoch cache) = label noise → 95% train acc, -15% MRR

### Per-Language — Best (Run B)
| Lang | Zero-shot | Row 1 | 3-HN | **Run B** | Gain (0→B) |
|------|-----------|-------|------|-----------|------------|
| FR   | 1.33%     | 15.53% | 16.88% | **20.04%** | +15.1x |
| ES   | 1.40%     | 15.52% | 17.89% | **20.85%** | +14.9x |
| EN   | 1.22%     | 5.19%  | 5.11%  | **12.21%** | +10.0x |
| EL   | 0.98%     | 2.95%  | 2.93%  | **11.82%** | +12.1x |
| JA   | 1.08%     | 4.87%  | 8.17%  | **7.68%**  | +7.1x  |

- [ ] **B3 (new): error analysis on JA** — weakest absolute language despite strong relative gain

---

## Phase 3d — Extended Runs ← GPU BUSY, LOWER PRIORITY THAN PHASE A

| Run | Config | Status | MRR | Note |
|-----|--------|--------|-----|------|
| E | CRR + HN K=7 + **ml=160** + LoRA r16 | ✅ Done | **14.89%** | Worse than B — ml=128 is optimal |
| **F** | CRR + HN K=7 + ml=128 + LoRA r16 + **40ep lr=3e-4** | 🟢 **RUNNING** | TBD | Run B + more convergence |
| G | CRR + HN **K=15** + ml=128 + LoRA r16 | ⏸ **DEPRIORITIZED** | TBD | Behind Phase A now — only run if A1-A5 land early |

**ml=128 confirmed optimal** (Run E ml=160 slower +38% and slightly worse MRR)

> Note (2026-07-02): Run G is explicitly deprioritized behind Phase A. A 1-2% MRR bump from more
> hard negatives does not move the acceptance-odds needle the way a baseline comparison does. Only
> queue Run G if A1/A2/A5 finish with days to spare.

### Run F Command (running):
```bash
python3 train_dbp5l_lora.py --epochs 40 --batch-size 32 --grad-accum 8 --lr 3e-4
    --use-crr 1 --crr-rho 0.1 --hard-neg-k 7 --hard-neg-start-epoch 5
    --max-length 128 --lora-rank 16
    2>&1 | tee logs/run_rowF_40ep_ml128.log
```
Expected: +1-2% MRR if Run B was not fully converged at ep 30

### Run G Command (queued, deprioritized):
```bash
python3 train_dbp5l_lora.py --epochs 30 --batch-size 32 --grad-accum 8 --lr 5e-4
    --use-crr 1 --crr-rho 0.1 --hard-neg-k 15 --hard-neg-start-epoch 5
    --max-length 128 --lora-rank 16
    2>&1 | tee logs/run_rowG_hn15.log
```
Expected: +1-2% MRR for JA/EL from denser hard negative pressure

---

## Phase 4 — Paper Results (LIVE TABLES)

### Table 1 — Ablation Study (Within-Language MRR)
| Row | Model Configuration | MRR | H@1 | H@3 | H@10 |
|-----|---------------------|-----|-----|-----|------|
| 0   | BGE-M3 zero-shot (no fine-tuning) | 1.26% | 0.07% | 1.38% | 3.26% |
| 1   | + LoRA fine-tuning, InfoNCE, Wikipedia (ml=96) | 10.02% | 4.87% | 11.70% | 19.41% |
| 2   | + CRR loss (rho=0.1) | 9.86% | 3.95% | 11.98% | 20.80% |
| 3   | + Hard Negative Mining (K=7) | 11.36% | 6.00% | 13.09% | 21.28% |
| 4   | + max_length 128 + rich descriptions | 14.95% | 9.04% | 16.96% | 26.42% |
| **5** | **+ LoRA rank 16 (Full Model)** | **15.59%** | **9.78%** | **17.69%** | **26.57%** |
| 6 (abl) | + XL cross-lingual anchors | 3.17% | 0.43% | 3.75% | 8.09% |
| F   | + 40 epochs (Run F) | TBD | — | — | — |
| G   | + HN K=15 (Run G, deprioritized) | TBD | — | — | — |
| **A1 (new)** | **ALIGNKGC (external baseline)** | **TBD** | — | — | — |
| **B1 (new)** | **Wikidata5M-Ind (monolingual anchor)** | **TBD** | — | — | — |
| **B2 (new)** | **SimKGC English-only (2nd baseline)** | **TBD** | — | — | — |

> ⚠️ All rows above the "(new)" additions are internal-only comparisons. Table 1 is NOT reviewer-ready
> until at least A1 is filled in.

### Table 2 — Per-Language (Full Model, Run B)
| Lang | MRR | H@1 | H@3 | H@10 |
|------|-----|-----|-----|------|
| FR   | 20.04% | 14.25% | 22.17% | 31.43% |
| ES   | 20.85% | 15.30% | 23.37% | 30.93% |
| EN   | 12.21% | 5.54%  | 14.16% | 25.06% |
| EL   | 11.82% | 4.42%  | 14.97% | 26.41% |
| JA   | 7.68%  | 4.08%  | 8.88%  | 13.90% |

> **Report mean ± std once A2 (3 seeds) is done.** Currently single-run numbers only.

### Key Findings for Paper (All Experimentally Confirmed)
1. **12x MRR boost** over zero-shot (1.26% → 15.59%) — Wikipedia abstracts are the key driver
2. **Text length matters**: max_length 128 + rich descriptions → +31% relative vs shorter/sparse text
3. **EN/EL description coverage transforms results**: EN 5.11%→12.21% (+139%), EL 2.93%→11.82% (+303%)
4. **CRR + Hard Negatives synergistic**: +15% relative over CRR alone
5. **Global neg with stale cache HURTS**: achieves 95% train acc but -15% MRR — memorization trap
6. **XL anchor supervision degrades all languages (-68%)**: BGE-M3 pre-training already encodes cross-lingual alignment; explicit supervision is counterproductive
7. **rho-sensitivity**: CRR benefit is dataset-dependent (benefits NELL, hurts FB15k-237)
8. **ml=160 does NOT help** over ml=128: BGE-M3 captures sufficient context in 128 tokens

- [ ] Generate figures: per-language bar chart, ablation progression chart, loss curves
- [ ] **Do not finalize Table 1/2 for submission until A1 (baseline) and A2 (seeds) are in**

---

## Phase 5 — Paper Writing

> ⚠️ Revised guidance (2026-07-02): numbers from Run B are stable enough to draft FROM, but do not
> lock final prose/claims until A4 (headline framing) is decided — it changes which findings are
> foregrounded vs. relegated to a supporting-evidence subsection.

- [ ] **A4 — Lock headline claim FIRST** (benchmark paper vs. negative-result paper vs. synergy paper)
- [ ] **Section 5 (Experiments)** — draft now, but leave Table 1/2 headers marked "pending A1/A2"
  - Table 1: ablation progression
  - Table 2: per-language breakdown
  - Analysis: Wikipedia abstracts critical | CRR+HN synergy | XL anchor negative | ml=128 sweet spot
- [ ] **Section 4 (Methodology)**
  - 4.1: BGE-M3 + LoRA architecture
  - 4.2: CRR contrastive loss formulation
  - 4.3: Hard negative mining with entity cache
  - 4.4: Entity description enrichment pipeline
- [ ] **Section 3 (Problem Formulation)**
  - Formal definition: multilingual inductive KGC
  - DBP-5L-Ind benchmark construction
- [ ] **Section 2 (Related Work)** — A5, must-do, needed to confirm the gap claim is still real
  - Multilingual KGC | Inductive KGC | CRR loss | SimKGC | DBpedia | ALIGNKGC (once A1 run, cite +
    compare directly)
- [ ] **Section 1 (Introduction)**
  - Hook: gap in multilingual + inductive KGC
  - Contributions: benchmark + model + findings + negative result — **count and order these to match
    whatever A4 decides is the headline claim**
- [ ] **Section 6 (Conclusion)**
- [ ] **Abstract** (write LAST after all numbers confirmed, including A1/A2)
- [ ] Register on AAAI CMT system
- [ ] **ABSTRACT DEADLINE: ~July 20 ← 18 days**

---

## Phase 6 — Polish & Submission

- [ ] LaTeX formatting to AAAI 2027 template (8 pages + references)
- [ ] Double-blind anonymization (remove names, institution refs, repo links)
- [ ] Proofread all tables and figures
- [ ] **PAPER DEADLINE: ~July 27 ← 25 days**

---

## Suggested Day-by-Day for Phase A (next 5-6 days)

| Day | Focus |
|---|---|
| 1 | A4 (lock framing — do this first, costs nothing) + start A1 (clone/setup ALIGNKGC) |
| 2-3 | A1 continued (run ALIGNKGC on DBP-5L-Ind) + start A2 (kick off 3-seed reruns in parallel on GPU when free) |
| 4 | A2 finishes, A3 (bootstrap significance test) | start A5 (Related Work draft) |
| 5-6 | A5 finishes | Begin Section 5 draft with real baseline numbers now in hand |

If A1 (ALIGNKGC) turns out to be harder to get running than expected, fall back to B2 (SimKGC
English-only) as a partial substitute baseline — weaker than a true multilingual baseline, but still
better than zero external comparisons.
