# 25_08 — Scores Tracker

Fill in scores as Kaggle returns them. Base = 0.692 (slot1_kitchen_sink_C from earlier registry).

| Slot | CSV | Items changed | Score | Δ vs 0.692 | Slice items net |
|------|-----|---------------|-------|------------|-----------------|
| 1 | slot1_frac_override.csv | 8 | ___ | ___ | ___ |
| 2 | slot2_search_gold_overlay.csv | 116 | ___ | ___ | ___ |
| 3 | slot3_mcq_teacher_override.csv | 26 | ___ | ___ | ___ |
| 4 | slot4_undercount_expand.csv | 51 | ___ | ___ | ___ |
| 5 | slot5_combined_all.csv | 186 | ___ | ___ | ___ |

Δ × 283 ≈ net slice items flipped right (positive) or wrong (negative).

## Interpretation notes
- Slot 5 ≈ Slot 1+2+3+4 if overlays are additive
- Slot 5 < sum(Slot 1-4) if overlays interfere or overwrite each other
- Slot 5 < 0.692 if combined overlays net-flip more right→wrong than wrong→right
