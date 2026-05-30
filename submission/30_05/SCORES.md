# 30_05 — Day 8 Kaggle Scores (5 submissions, deadline eve)

**Date:** 2026-05-30
**Base:** submission/csvs/undercount_plus_frac.csv (0.713)
**Build report:** submission/30_05/SLOTS_1_4_REPORT.md
**Best Day 8:** 0.745 (slot 4 v2 / format probe tied) · +3.2pp over base · gap to leader 0.85 = 10.5pp

## Day 8 Actuals

| Slot | CSV | Score | Δ vs base | Δ vs prior slot | Hypothesis | Result |
|------|-----|-------|-----------|------------------|------------|--------|
| 1 control | 30_05_slot1_control.csv | **0.713** | 0.000 | — | byte-equal 0.713 base; no Day5→8 regression | ✅ control valid |
| 2 +anchor | 30_05_slot2_anchor.csv | **0.738** | +0.025 | +0.025 | 316 audited anchor overrides lift score | ✅ positive, far below +8-15pp prediction |
| 3 +4/4 bloc | 30_05_slot3_bloc.csv | **0.738** | +0.025 | +0.000 | 4/4 teacher consensus on non-anchor helps | ❌ NULL — zero leverage on top of anchor |
| 4 v2 | 30_05_slot4_aggressive_v2.csv | **0.745** | +0.032 | +0.007 | full v7 ship-A (Opus flips + 5th teacher) | ✅ +0.7pp — best Day 8 |
| 5 probe | 30_05_slot5_format_probe.csv | **0.745** | +0.032 | +0.000 | render_d Opus-form beats anchor-form on 69 | ❌ NULL — indeterminate |

## Calibration check (predicted vs actual)

| Slot | Predicted | Actual | Verdict |
|------|-----------|--------|---------|
| 1 | 0.713 (= base) | 0.713 | 🎯 EXACT |
| 2 | +8 to +15pp | +2.5pp | ❌ big miss (~5-12pp low) — grader format-strict |
| 3 | +0.5 to +1.5pp on slot 2 | +0.0pp | ❌ NULL |
| 4 v2 | ~+5pp | +3.2pp (vs base) | ⚠️ underperformed |
| 5 probe | +1 to +3pp positive | +0.0pp | ❌ NULL result |

## Delta Analysis

- **4/4 bloc lever: NULL.** No movement on top of anchor — those items were already correct in the anchor base or fall outside the ~283 scored slice.
- **Opus lever (flips + 5th teacher): +0.7pp, ~2 slice items.** The only positive lever beyond anchor. This is what makes slot 4 v2 the Day-8 best.
- **Format probe: NULL.** render_d (Opus form) vs render_b (anchor form) produced no net change — content/format conflation makes the signal indeterminate (can't separate "format accepted" from "value already counted").
- **Teacher-overlay ceiling: ~+3.2pp over base, diminishing returns evident.** anchor (+2.5) then Opus (+0.7), then 4/4 and format probe both flat. The external-evidence overlay stack appears largely exhausted.

## Implications for tomorrow's Pick A / Pick B

- **Pick A = 0.745** (slot 4 v2) is the current best *overlay* sheet. (Note: per rule #11, Pick B must be Qwen-derived only; A is the safety/best-so-far.)
- **Safety floor:** never be exposed to the old 0.438/0.420 picks at the deadline — lock the best scored CSV (0.745) now.
- **Pick B path is Qwen-derived ONLY (rule #11):** primary mechanisms = inference-audit cross-run consensus + Phase 0 log-weighted SC + the 12hr A100 run. The teacher/anchor/Opus overlay path is NOT eligible for Pick B.
- **Real risk:** the overlay stack is near its ceiling (+3.2pp), and if no Qwen-only path clears 0.713→>0.745, Pick B has no upside path. Prioritize the Qwen-only inference work accordingly.
