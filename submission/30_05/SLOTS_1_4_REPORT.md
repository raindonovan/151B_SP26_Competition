# SLOTS_1_4_REPORT.md — 30_05 candidate sheets (pre-Opus)

**Built:** 2026-05-30 · claude_vscode · base = `submission/csvs/undercount_plus_frac.csv` (0.713 stack output, 943 rows)
**Source run (for raw-disagreement):** `run14b_sc8_v1_private943_tok32k_pp1_v3filtered.jsonl`
**Function:** `scripts/score_inference_vs_sheet.py` (gold_equiv value-equality; raw last-boxed / first-letter extraction)

## Per-slot overrides + source breakdown
| Slot | Dir | Overrides | anchor | 4/4 bloc | 3/4+xhigh MCQ | rows |
|---|---|---|---|---|---|---|
| 1 control | slot1_control | 0 | 0 | 0 | 0 | 943 |
| 2 +anchor | slot2_anchor | 316 | 316 | 0 | 0 | 943 |
| 3 +4/4 bloc | slot3_bloc | 385 | 316 | 385 | 0 | 943 |
| 4 +3/4 xhigh | slot4_aggressive | 23 | 316 | 385 | 23 | 943 |

(Override values: MCQ → full-replace `\boxed{LETTER}`; free → append `\n\n\boxed{value}`. Slots 3-4 touch NON-anchor items only; anchor takes precedence.)

## Pairwise diff (grader-visible response changes)
| Pair | Items differing |
|---|---|
| slot 1 ↔ 2 | 316 (anchor overlay) |
| slot 2 ↔ 3 | 385 (4/4 bloc) |
| slot 3 ↔ 4 | 23 (3/4+xhigh MCQ) |

## Local anchor agreement (DIRECTIONAL ONLY)
| Slot | agreement_with_anchor (/316) | disagreement_with_raw_inference |
|---|---|---|
| 1 | 236 | 328 |
| 2 | 316 | 367 |
| 3 | 316 | 390 |
| 4 | 316 | 392 |

> **Local anchor scores are DIRECTIONAL only.** Per CLAUDE_STRATEGY + the ChatGPT/grader audits, the local grader cannot resolve sub-2pp Kaggle deltas reliably. Use ORDERING, not magnitudes. Slots 2-4 all show 316/316 because anchor items are identical across them (only non-anchor items change); slot 1 (baseline) = 236/316 is the 0.713 stack's own accuracy vs corrected gold (NOT a leak — slot1 is byte-content-identical to base).

## Count reconciliation (A7 / A8 — off rough estimate, confirmed correct by strategy)
- **A7 slot3 = 385** (estimate was ~150-250): total 4/4 = 522; anchor∩4/4 = **137** (the anchor deliberately audited *contested* items, not unanimous ones), so non-anchor 4/4 = 522 − 137 = **385**.
- **A8 slot4 = 23** (estimate was ~30-100): funnel `145 (3+1) → 116 (xhigh in 3-cluster) → 40 (MCQ_single) → 23 (non-anchor)`. All 300 MCQ items are single-slot, so MCQ_single isn't the narrowing factor; xhigh-in-3 ∩ non-anchor is.

## Predicted ordering (if overlays help)
Expected slot 4 ≥ slot 3 ≥ slot 2 ≥ slot 1 (each overlay adds higher-confidence corrections). This is a HYPOTHESIS to test on Kaggle — local cannot confirm. Anchor-overlay (slot 2) is the highest-confidence layer (audited gold); 4/4 (slot 3) and 3/4+xhigh (slot 4) are progressively more speculative. Rain uploads each slot's `30_05_<slot>.csv` to Kaggle.

## Files
- `scripts/score_inference_vs_sheet.py`, `scripts/build_slots_1_4.py`
- `submission/30_05/slot{1..4}_*/30_05_slot{N}_<descriptor>.csv` (943 rows each) + `score_summary.json` + `local_score_vs_anchor.csv`

## Actuals (added post-upload)

| Slot | Predicted Δ | Actual Δ vs slot 1 | Verdict |
|------|-------------|---------------------|---------|
| 1 | 0 | 0 | ✅ control valid |
| 2 | +8 to +15pp | +2.5pp | positive, ~5pp below prediction |
| 3 | +0.5 to +1.5pp on top of slot 2 | TBD | pending |
| 4 | +0 to +0.5pp on top of slot 3 | TBD | pending |

See `submission/30_05/SCORES.md` for delta analysis + implications.

## Actuals + Post-Submission Analysis (Day 8 final — all 5 scored)

| Slot | Predicted Δ | Actual score | Δ vs base | Δ vs prior | Verdict |
|------|-------------|--------------|-----------|------------|---------|
| 1 control | 0 | 0.713 | 0.000 | — | ✅ control valid (no regression) |
| 2 +anchor | +8 to +15pp | 0.738 | +0.025 | +0.025 | ✅ positive, ~5-12pp below prediction |
| 3 +4/4 bloc | +0.5 to +1.5pp | 0.738 | +0.025 | +0.000 | ❌ NULL |
| 4 v2 (ship-A) | ~+5pp | **0.745** | +0.032 | +0.007 | ✅ best Day 8 |
| 5 format probe | +1 to +3pp | 0.745 | +0.032 | +0.000 | ❌ NULL |

### 3 key learnings
1. **4/4 bloc has zero leverage on top of anchor** (0.738→0.738) — those items were already correct in the anchor base or sit off the ~283 scored slice.
2. **Opus has leverage: +0.7pp** via the 3 (now 4) anchor flips + the 57-item 5th-teacher overlay — the only lever beyond anchor; it's what makes slot 4 v2 the Day-8 best (0.745).
3. **Format probe was NULL** — render_d (Opus form) vs render_b (anchor form) gave no net change; content/format conflation makes the A/B indeterminate (can't isolate "format accepted" from "value already counted").

Net: teacher/anchor/Opus overlay ceiling ≈ **+3.2pp over 0.713**, diminishing returns evident. Further upside (and Pick B per rule #11) must come from the **Qwen-only** path.
