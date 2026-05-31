# R20b_eval_v1_sc8_p943_t32k_v3filt — findings (deep audit; FINAL of 5)

**Run:** `run14b_sc8_v1_private943_tok32k_pp1_v3filtered` · SC@8 · 32K · v1-baseline · **v3 shape-filter applied to samples before voting** · derivative of R20 (same 8 samples per item).
**Isolates SAMPLE-FILTER effect** at fixed inference. Not a fresh GPU run — a post-processing layer (`shape_rejected` per sample, `v3_samples_kept`/`v3_samples_rejected`) that changes which votes win.
**Analyzer:** v3-final-final (761f903), SC path (raw-SC-compatible schema — no prep step needed). **Kaggle: 0.646** (REGISTRY #14 = `run14b_v3filtered.csv`) — identical to R20's 0.646.

## What the filter actually does
Rejected ≥1 sample on **142 items**; changed the `voted_answer` vs R20 on **55 items**. So it is a genuine A/B, not a no-op. `shape_filter_fallback=True` on 0 items (no item lost all samples).

## a. Headline
- **Bucket:** A=430 · A_lucky_sample=10 · B=58 · unknown=445
- **Scored set** (n=498): math_correct=430, **acc=0.8635** — highest local of the cohort (R20 0.8554), +4 A vs R20.

## b. hard_independent_CLEAN (across all 5)
- **n=16, correct=13, acc=0.8125** — IDENTICAL to R20 (wolfram 6/7, search 7/9). The filter did not touch the hard-independent set.
- Trend: R08 0.625 → R09 0.6875 → R10 0.75 → R20 0.8125 → **R20b 0.8125** (plateau).
- (c-info) DIRTY: 0.2051 (stable).

## c. unanimous_teachers (across all 5)
- **n=403, correct=401, acc=0.9950** — highest of cohort (R08 0.945, R09 0.985, R10 0.911, R20 0.988). The filter's local gain is concentrated here: it cleaned 4 vote-fragile consensus items into clean wins.

## d. A_lucky_sample (n=10) — filter REDUCED it (R20 had 14)
- The filter converted 4 of R20's A_lucky_sample items into clean A (vote no longer fragile after rejecting off-shape samples). It created 0 new A_lucky. So the filter's entire visible effect is **A_lucky→A cleanup** — see §g.
- Remaining 10 A_lucky: the items where even shape-filtering didn't make the correct minority sample win the vote.

## e. B items (n=58) — format-recoverability
Identical B set to R20 (the filter moved nothing in/out of B). ~79% format-recoverable (multi-slot, MCQ-letter, fraction-form). id=41 `2112`→`4048` (true miss), etc. Full list: `analysis/analysis.csv` filter `bucket_b_review_needed=True`.

## f. Truncated — n=16 (R20 was 17) — FLAGGED
- **16 vs R20's 17.** One item's canonical sample changed under the filter: for that item the filter rejected the truncated sample that R20's vote had landed on, and a non-truncated sample won instead. Trivial (filter operates on votes; it incidentally swapped one item's canonical-sample truncation flag). Not a concern.

## g. Cross-run vs R20 — FILTER effect (LOAD-BEARING)
| R20 → R20b | count |
|---|---|
| A → A | 426 |
| **A_lucky_sample → A** | **4** |
| A_lucky_sample → A_lucky_sample | 10 |
| B → B | 58 |
| (B→A, B→A_lucky, A→B, A_lucky→B) | **0 each** |

- **Filter dividend = (B→A 0 + B→A_lucky 0) − (A→B 0 + A_lucky→B 0) = 0.**
- The filter's only effect on the gold-scored set is **A_lucky→A (4 items)** — it makes 4 already-mathematically-correct items win their vote cleanly, but moves **nothing from wrong→right or right→wrong**.
- **VERDICT: the v3 shape-filter is NOT a Pick-B improvement. DROP from morning planning.** Local scored-acc rose +0.8pp (0.8554→0.8635) purely from vote-cleanup on already-correct items; **Kaggle is flat (0.646 == R20 0.646)** — the cleanup didn't touch any item on the ~283 slice that wasn't already counted. A free post-processing layer that doesn't change correctness is not a lever.

## h. 5-way intersection (R08∩R09∩R10∩R20∩R20b) — COHORT COMPLETE
- **h1. A∩∩∩∩∩ = 371 strict** (373 incl. A_lucky) — definitive rock-solid set across single/SC × v1/v3perslot × 16K/32K × raw/filtered. NOT adapter/normalizer candidates.
- **h2. B∩∩∩∩∩ = 48** — identical to R20's 4-way B∩ (the filter changed nothing in the wrong set). Definitive "wrong across every lever" set: 5,25,26,33,41,61,67,68,72,89,100,103,104,106,127,134,167,182,192,218,231,233,247,263,264,282,306,317,345,353,389,395,413,440,474,506,548,578,587,591,638,657,710,713,723,748,793,868
- **h3. All 11 R20 true-miss seed survive R20b** — including the 3 heuristic-newcomers **167, 345, 591** (all still B∩∩∩∩∩). The filter rescued none of the seed.
- **h4. LOCKED FINAL ADAPTER TARGET SEED (true-miss in B∩∩∩∩∩): [41, 61, 103, 104, 127, 167, 231, 264, 282, 345, 591]** — 11 items wrong on the math across ALL FIVE levers. The other 37 of the 48 are format-recoverable (structural-normalizer territory, NOT adapter).
  - **Recommend T3 confirm the 11** before adapter training. Already T3-validated: id=41 (R08-T3), id=282 (R10-T3, extra-root error). id=117 was correctly removed at R20 (32K truncation rescue). Newcomers 167/345/591 are heuristic-classified — verify they're math-misses not subtle format.
  - id=9 (gold-split, R08-T3) correctly absent from B∩∩∩∩∩ — stays off exemplars.

## Notes / surprises about the filter
- **The filter is a pure vote-cleanup, not a correctness lever.** It touched 55 voted answers but every gold-scored change was A_lucky→A (already correct, now cleanly so). Zero wrong→right. This is the cleanest possible "this lever is dead for Pick B" signal: it can't help Kaggle because it doesn't change any item's correctness, only its vote-margin.
- **The 5-run cohort accuracy plateaued** at hard_clean 0.8125 (R20=R20b) and B∩=48. The adapter seed (11) and the rock-solid set (371) are now LOCKED — no further p943 lever in this cohort moves them.
- Lever ranking (final, at fixed v1): **SC +33 ≫ tokens +7 ≫ filter 0 ≫ prompt-variant −11.** SC is the dominant lever; tokens second; the shape-filter and the v3-perslot prompt are both non-levers (0 and negative).
