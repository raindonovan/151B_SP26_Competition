# 30_05 — Submission Batch (Day 8, deadline eve)

**Date:** 2026-05-30 · **Status:** ⏳ AWAITING KAGGLE SCORES — fill actuals below
**Daily limit:** 5 submissions. **Hard deadline:** Sun 2026-05-31.

## Why this batch
The 29_05_rejudge experiments were planned but **never submitted**. They are the
highest-EV use of today's slots: they (a) measure the judge-update lift on our
proven best and (b) decode which post-processing levers still matter under the
(locally-verified, not-yet-Kaggle-confirmed) value-equality judge. Slot 4 then
measures the now-finalized **single-mode normalizer** end-to-end, which has never
been scored against Kaggle. Slot 5 is reserved for a data-driven call after 1–4.

## What we believe about the judge (verified locally; Kaggle confirmation = this batch)
`judge_single_numerical_value` does numeric value-equality at ~1e-8: `4.000==4`,
`0.6==3/5` PASS; rounded-but-wrong values FAIL. **If confirmed**, surface form
(decimal/fraction/trailing-zero) is dead as a lever; live levers are
precision/rounding, parseability, and structural (MCQ first-box, multi-answer
single-box-ordered, undercount). The single-mode normalizer is built to that belief.

## The submissions

| # | CSV | Prior | vs ref | Items changed | Hypothesis | Prediction | **Actual** | Verdict |
|---|-----|-------|--------|---------------|------------|------------|------------|---------|
| 1 | `29_05/csvs/PICK_01_control_undercount_plus_frac.csv` | 0.713 (old judge) | — (ref) | — | Judge update lifts our best for free | rises vs 0.713 | _TBD_ | _TBD_ |
| 2 | `28_05/csvs/slot4_undercount_expand.csv` | 0.706 (old judge) | frac items only: `135,207,529,716,784,817,919,936` | Is the frac/numeric layer redundant now? | ties #1 if exact decimals accepted | _TBD_ | _TBD_ |
| 3 | `29_05/csvs/undercount_frac_mcq.csv` (build via `29_05/scripts/build_undercount_frac_mcq.py`) | ~0.710 (never scored) | +16 MCQ overrides: `18,117,403,443,457,501,518,589,670,675,682,695,720,727,786,935` | Do MCQ teacher-overrides help under new judge? | ≈ or slightly below #1 | _TBD_ | _TBD_ |
| 4 | normalizer-e2e on R14 (`run14b_sc8_v1_private943` raw → single-mode normalizer → CSV) | R14 raw = 0.646 | structural normalization of a real run | Does the single-mode normalizer lift a raw inference run? | rises vs 0.646; vs #1 unknown | _TBD_ | _TBD_ |
| 5 | RESERVED | — | — | data-driven after 1–4 (F22 variance probe, or a refined pick) | — | _TBD_ | _TBD_ |

## Decode logic — what each result tells us
- **#1 − 0.713** = free lift from the judge update. Large positive ⇒ much historical format-fixing was already absorbed by the judge.
- **#1 vs #2** isolates the frac/numeric lever:
  - `#2 == #1` ⇒ numeric-surface layer is **dead** → single-mode normalizer (which drops it) is correct; keep frac only as explicit per-item overrides.
  - `#2 < #1` by ~0.007 ⇒ frac still lives on rounded-decimal items → re-add as per-item overrides, NOT as a mode.
- **#3 vs #1** isolates MCQ teacher-overrides: `#3 > #1` ⇒ wire MCQ override into the pipeline; `#3 ≤ #1` ⇒ drop.
- **#4 vs #1** = the single-mode normalizer's standalone value on a real run vs the answer-sheet pipeline.

## Safety floor (decide before submitting)
The currently-selected Kaggle final picks are still the wrong ones (0.438/0.420).
**Lock `PICK_01_control_undercount_plus_frac` (0.713) as Pick A now** so we are never
exposed to the 0.438 at the deadline, regardless of how 1–5 land. Pick B chosen from
the best of this batch once scored.

## Follow-ups once actuals are in (do not skip)
1. Fill **Actual** + **Verdict** columns.
2. Append rows to `submission/REGISTRY.md` (master cross-round log).
3. Update `strategy/SESSION_HANDOFF.md` TL;DR with the new best.
4. Resolve the format-lever docs in `postprocessing/` per the #1-vs-#2 result
   (delete/keep the FORMAT_RULES / STRICT_NORMALIZER_SPEC family with confidence).
5. Set final Kaggle picks (A = floor, B = best of batch).

## Notes
- Slots 1–3 use existing/buildable CSVs (ready now). Slot 4 needs a CSV produced by
  running the single-mode normalizer over R14's raw output (vscode task).
- All CSVs must validate before submit: 943 rows, header `id,response`, no dup IDs.
