# 30_05 — Slot 1-4 Kaggle Scores (Day 8, deadline eve)

**Date:** 2026-05-30
**Base:** submission/csvs/undercount_plus_frac.csv (0.713)
**Build report:** submission/30_05/SLOTS_1_4_REPORT.md

## Actuals

| Slot | CSV | Overrides | Predicted Δ | Actual | Δ vs slot 1 | Status |
|------|-----|-----------|-------------|--------|-------------|--------|
| 1 control | 30_05_slot1_control.csv | 0 | 0.713 (base) | **0.713** | 0 | ✅ control valid |
| 2 +anchor | 30_05_slot2_anchor.csv | +316 anchor | +8 to +15pp | **0.738** | +0.025 | ✅ positive, below pred |
| 3 +bloc | 30_05_slot3_bloc.csv | +385 4/4 bloc | +0.5 to +1.5pp | _TBD_ | _TBD_ | pending upload |
| 4 +aggr | 30_05_slot4_aggressive.csv | +23 3/4+xhigh MCQ | +0 to +0.5pp | _TBD_ | _TBD_ | pending upload |

## Calibration

| Slot | Predicted | Actual | Match? |
|------|-----------|--------|--------|
| 1 | 0.713 (= base) | 0.713 | 🎯 EXACT |
| 2 | 0.78-0.85 (+8 to +15pp band) | 0.738 (+2.5pp) | ❌ off by ~5pp low |

## Why slot 2 underperformed prediction

Predicted delta assumed Kaggle's grader uses pure value-equality on anchor
overrides. Actual indicates Kaggle is format-strict on at least some anchor items.

Slice math:
- ~283-item Kaggle slice × 33.5% (anchor in slice) = ~95 anchor items in slice
- Model already correct on 66.5% of anchor → ~63 silent items
- Effective effect candidates: ~32 items
- Net +7 slice items (2.5pp × 283) → ~22% net positive yield

The missing ~78% of effect candidates are either silent (anchor = model) or
NEGATIVE (anchor's format didn't pass grader). Aligns with CHATGPT_AUDIT's finding
that ~25 of 78 anchor-vs-Opus "contradictions" are format/precision artifacts.

## Implications

1. Slot 3 (4/4 bloc) — teacher consensus format tends to be more Kaggle-friendly
   than anchor's audit-corrected format. Expect +0.5 to +2pp on top of slot 2.
2. Slot 4 (with 3 Opus flips on 0120/0248/0308) — value-correct overrides on items
   where anchor was wrong; small but positive.
3. Format normalization is a primary lever for answer sheet v7. Audit-aesthetic
   formats should be revised toward Kaggle-friendly formats when known.
4. 12hr A100 priority — if format is the bottleneck, more inference may have low
   ROI; format-normalization work over the answer sheet may dominate. Decision
   deferred until slot 3+4 land.

## Final-pick safety floor
Lock `30_05_slot2_anchor.csv` (0.738) as Pick A — never be exposed to the old
0.438/0.420 picks at the deadline. Pick B = best of slots 3-4 once scored (fall
back to slot 1 / 0.713 if neither beats slot 2).
