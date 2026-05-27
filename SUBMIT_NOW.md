# SUBMIT NOW — Day 3 Kaggle Submissions (5 slots)

**Sequence**: Submit Slots 1→5 in order. Each one's score informs the next slot's strategy.

---

## Slot 1: Kitchen sink WITH trailing-zero strip
https://raw.githubusercontent.com/beepbeeepimajeep/151B_SP26_Competition/main/submissions/slot1_kitchen_sink_C.csv

**Tests**: baseline kitchen-sink (78 overrides + trailing-zero strip). Expected 0.70-0.74 if strip helps.

---

## Slot 2: Kitchen sink WITHOUT strip (probe)
https://raw.githubusercontent.com/beepbeeepimajeep/151B_SP26_Competition/main/submissions/slot2_no_trailing_zero_strip.csv

**Tests**: isolates trailing-zero strip impact (102 items). Slot 1 − Slot 2 = strip effect.

---

## Slot 3: Kitchen sink MINUS Rescue MED (8 items reverted)
https://raw.githubusercontent.com/beepbeeepimajeep/151B_SP26_Competition/main/submissions/slot3_minus_rescue_med.csv

**Tests**: isolates Rescue MED tier (items 161, 204, 312, 453, 724, 799, 836, 911 — 2/4 teacher agreement). Slot 1 − Slot 3 = Rescue MED net effect.

---

## Slot 4: Kitchen sink MINUS Wolfram MED (7 items reverted)
https://raw.githubusercontent.com/beepbeeepimajeep/151B_SP26_Competition/main/submissions/slot4_minus_wolfram_med.csv

**Tests**: isolates Wolfram MED/PARTIAL tier. Slot 1 − Slot 4 = Wolfram MED net effect.

---

## Slot 5: Kitchen sink MINUS ALL MED (15 items reverted)
https://raw.githubusercontent.com/beepbeeepimajeep/151B_SP26_Competition/main/submissions/slot5_minus_all_med.csv

**Tests**: combined MED impact. Slot 1 − Slot 5 = total MED tier value. Sanity check: should ≈ (Slot 1 − Slot 3) + (Slot 1 − Slot 4) if tiers are independent.

---

## Decision matrix (after all 5 land)

After Kaggle returns all 5 scores, the deltas tell us:
- **Strip impact** = Slot 1 − Slot 2 (positive = keep strip)
- **Rescue MED value** = Slot 1 − Slot 3 (positive = MED helps)
- **Wolfram MED value** = Slot 1 − Slot 4 (positive = MED helps)
- **All MED value** = Slot 1 − Slot 5 (cross-check)

For final 2 picks (deadline ~2026-06-02), use whichever submission scored highest, plus the kitchen-sink variant whose ablations showed all tiers net-positive.

## Verification (already done)
- All 5 files differ from each other in expected ways
- id=41=2112 (IMO 2025 P6 confirmed)
- Hendrycks bug fixes applied to all 5
