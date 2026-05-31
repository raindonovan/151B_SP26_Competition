# R20_eval_v1_sc8_p943_t32k_pp1 — findings (deep audit)

**Run:** `run14b_sc8_v1_private943_tok32k_pp1` · SC@8 · **32K tokens** · v1-baseline · 2026-05-22
**THE 0.646 best-inference baseline** — the floor the locked 0.745 Pick A was built on (via teacher/anchor/Opus overrides). **Kaggle: 0.646** (REGISTRY #4 cohort; analyzer run WITH `--kaggle-score 0.646`).
**Isolates TOKEN-BUDGET effect:** R09's structural sibling (both SC@8, v1) with 32K vs 16K tokens.
**Analyzer:** v3-final-final (761f903). Numbers match the lock-session pressure-test exactly (analyzer is deterministic).
Sampling: T=0.6, top_p=0.95, top_k=20, presence_penalty=1.0, repetition_penalty=1.0, n_samples=8, max_new_tokens=32768.

## a. Headline
- **Bucket:** A=426 · A_lucky_sample=14 · B=58 · unknown=445
- **Scored set** (n=498): math_correct=426, **acc=0.8554** — HIGHEST of the four (R08 0.8173, R09 0.8474, R10 0.7952).

## b. hard_independent_CLEAN — best of cohort
- **n=16, correct=13, acc=0.8125.** Per-source: wolfram_HIGH 6/7, search_GOLD 7/9.
- Trend across the 4-way: R08 0.625 → R09 0.6875 → R10 0.75 → **R20 0.8125**. Both SC and tokens help the hard-independent set.
- (c-info) DIRTY (T4/T5): 0.1923 — the structural-normalizer gap, stable across all 4 runs (~0.18–0.22).

## c. unanimous_teachers — best of cohort
- **n=403, correct=398, acc=0.9876** (R08 0.9454, R09 0.9851, R10 0.9107). SC+32K recovers consensus agreement fully.

## d. A_lucky_sample (n=14) — DeepConf territory GREW at 32K
- Distribution by n_correct/8: {1:3, 2:2, 3:4, 4:2, 5:1, 6:1, 7:1}.
- **DeepConf gold (≥5/8 lost vote): 3 items — 296 (5/8), 839 (6/8), 302 (7/8)** — vs R09's **1**. Doubling tokens roughly tripled the DeepConf-territory pool. (Caveat: 302/839 have voted==gold by value but the canonical/extraction differed — likely format-adjacent; 296 is a clean 5/8 multi-slot order case.)
- SC@32 candidates (1–4/8): 11.
- So at 32K, **DeepConf logprob-weighting becomes a slightly stronger morning lever than it looked at R09** (3 vs 1 high-confidence-but-lost items), though the pool is still small; SC@32 (11 items) remains the broader lever.

## e. B items (n=58) — format-recoverability
| Category | Count |
|---|---|
| multi-slot | 29 |
| true miss | 12 |
| MCQ-letter | 10 |
| fraction-form | 4 |
| undercount | 3 |

**~46/58 (79%) format-recoverable.** Top B: id=26 `232`→`I`, id=12 `2c+4p=70,11`→`11` (undercount), id=41 `2112`→**`4048`** (now converges to a wrong number — genuine miss, no longer the rambling non-answer it was at 16K), id=61 piecewise (true miss). Full list: `analysis/analysis.csv` filter `bucket_b_review_needed=True`.

## f. Truncation — the token-effect headline
- **R20 truncated = 17** (R08 119, R09 93). **32K rescued 72 of the 89 always-truncated-at-16K items.**
- **Only 17 still truncate at 32K** → the genuine >32K candidates (want 65536/81920): **93, 112, 161, 204, 229, 275, 308, 312, 376, 383, 445, 498, 586, 652, 724, 799, 809**.
- Prediction check (from R10): id=**117 WAS rescued at 32K** (now A, math-correct) ✓; id=**127 was NOT** rescued (still B) — so 127 is a true miss, not merely truncation.

## g. Cross-run vs R09 — TOKEN effect at fixed SC/v1 (16K→32K)
| R09 → R20 | count |
|---|---|
| A → A | 417 |
| A → A_lucky_sample | 4 |
| A → B | **1** |
| A_lucky → A | 4 |
| A_lucky → A_lucky | 8 |
| A_lucky → B | 6 |
| B → A | **5** |
| B → A_lucky | 2 |
| B → B | 51 |
- **Token dividend = 5 (B→A) + 2 (B→A_lucky) = 7**, with 1 regression.
- **Lever ranking at fixed v1 prompt:** SC (R08→R09) bought **+33**; tokens (R09→R20) bought **+7**; prompt-variant (R08→R10) was **net −11**. **SC ≫ tokens ≫ prompt-variant.** The 6 A_lucky→B regressions are vote-shuffle noise on already-fragile items (the canonical sample changed with the longer responses).

## h. 4-way intersection (R08 ∩ R09 ∩ R10 ∩ R20) — completes the cohort core
- **h1. A∩A∩A∩A = 371 strict** (373 incl. A_lucky) — rock-solid across single/SC × v1/v3perslot × 16K/32K. ~75% of the scored set. NOT adapter/normalizer candidates.
- **h2. B∩B∩B∩B = 48** (down from R10's 53-item triple core — 117 rescued at 32K + a few shifted to A_lucky): 5,25,26,33,41,61,67,68,72,89,100,103,104,106,127,134,167,182,192,218,231,233,247,263,264,282,306,317,345,353,389,395,413,440,474,506,548,578,587,591,638,657,710,713,723,748,793,868
- **h3. Of the 10 R8∩R9∩R10 true-miss seed, 9 survive R20** [41, 61, 103, 104, 127, 231, 264, 282, 868]; **id=117 rescued at 32K** (now A, correct — exactly the predicted truncation rescue).
- **h4. Recoverability of B∩B∩B∩B:** 37 format-recoverable (multi-slot 21, MCQ-letter 10, fraction 4, undercount 2 → **normalizer territory**); **11 true-miss → FINAL ADAPTER TARGET SEED: [41, 61, 103, 104, 127, 167, 231, 264, 282, 345, 591]**.
  - Heuristic caveat: classification is automated (gold-vs-extracted + box-count). 41 already T3-confirmed true-B; recommend T3 confirms the full 11 before adapter training (esp. 167/345/591 which the heuristic newly added vs the R10 seed — verify they're math-misses not format).
  - **Adapter-exclusion (R08-T3):** id=9 is a gold-split artifact, correctly NOT in B∩B∩B∩B (it's undercount/A_lucky across runs). Keep off exemplars.

## Notes / surprises about the 0.646 baseline
- **Tokens are a real but second-order lever:** 16K→32K bought only +7 scored items, vs SC's +33. The 0.646's edge over R09's 0.614 is mostly the 72 truncation rescues converting to correct answers on the *full* set (many in `unknown`/T4-T5, off the hard-gate set) — i.e., 32K helps the long-derivation items that 16K cut off, which is why it's the best baseline despite a small *scored-set* token dividend.
- **The 0.745 Pick A is built on a baseline whose own scored accuracy is 0.8554** on independent gold — the overlay stack (anchor/Opus) then adds the teacher-corroborated items on top. R20 is a strong, clean floor.
- **DeepConf got more attractive at 32K** (3 vs 1 high-conf-lost items) — worth noting for the morning DeepConf-vs-SC@32 decision, though both pools are small.
- Final adapter seed is just ~11 items — the "consistently wrong on math across every lever" set is tiny; the bulk of apparent failures are format (structural-normalizer) or token (high-budget re-run), not model capability.
