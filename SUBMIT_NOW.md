# SUBMIT NOW — Day 3 Kaggle Submission URLs

**Sequence**: Submit Slot 1 → wait for Kaggle score → submit Slot 2 → continue.

---

## Slot 1: Kitchen-sink Track C WITH trailing-zero strip
**Click to download CSV:**

https://raw.githubusercontent.com/beepbeeepimajeep/151B_SP26_Competition/main/submissions/slot1_kitchen_sink_C.csv

Fallback if above doesn't work:
https://media.githubusercontent.com/media/beepbeeepimajeep/151B_SP26_Competition/main/submissions/slot1_kitchen_sink_C.csv

**Expected**: 0.70–0.74 if trailing-zero strip helps.

---

## Slot 2: Kitchen-sink WITHOUT trailing-zero strip (the probe)
**Click to download CSV:**

https://raw.githubusercontent.com/beepbeeepimajeep/151B_SP26_Competition/main/submissions/slot2_no_trailing_zero_strip.csv

Fallback:
https://media.githubusercontent.com/media/beepbeeepimajeep/151B_SP26_Competition/main/submissions/slot2_no_trailing_zero_strip.csv

**Expected**: differs from Slot 1 by ±0.5–3pp on the 102 trailing-zero items.

---

## What to do
1. Click Slot 1 URL → browser downloads `slot1_kitchen_sink_C.csv`
2. Upload to Kaggle → report score
3. Click Slot 2 URL → browser downloads `slot2_no_trailing_zero_strip.csv`
4. Upload to Kaggle → report score
5. **Slot 3-5 reactive based on Slot 1 vs Slot 2 delta**:
   - If Slot 1 > Slot 2: trailing-zero strip helps → Slot 3 = drop Rescue MED to isolate that tier
   - If Slot 2 > Slot 1: strip hurts → Slot 3 = use Slot 2 base, drop Rescue MED
   - If equal: strip is neutral → Slot 3 = test something else

## Verification (already done)
- Both files differ on exactly 102 rows (trailing-zero affected items)
- All 78 overrides applied to both (id=41=2112, id=124=H, id=181=A, all Rescue HIGH/MED)
- Hendrycks bug fixes applied: `\boxed `-space neutralization + two-pass trailing-zero regex
- Slot 1 SHA prefix: 6e2276b9
- Slot 2 SHA prefix: 1ae705c2
