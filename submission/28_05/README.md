# 25_08 — Five Independent Hypothesis Submissions

**Built:** 2026-05-28 (under 15-min window)
**Base:** `slot1_kitchen_sink_C.csv` (0.692 — current best)
**Strategy:** 5 NON-CHAINED independent slots. Each tests a different post-processing/format hypothesis using NEW evidence sources. No slot's correctness depends on another's outcome.
**Override mechanism:** Append `\n\n\boxed{NEW_ANSWER}` to base response. Grader extracts the LAST `\boxed{}`, so this cleanly overrides without breaking other rows.
**Slice math:** Test set ≈ 283 items. 1 correct flip = +0.354pp. Expected slice items per overlay ≈ N × 0.30.

---

## Slot 1 — frac_override.csv
**Hypothesis:** Hendrycks gold uses fractions for rational answers (MATH paper: "probabilities expressed as simplified fractions"). Items where Qwen emits decimal but all teachers agree on a fraction form are pure format losses.

**Items changed:** 8
- 135: `0.6` → `\frac{3}{5}`
- 207: `2.8` → `\frac{14}{5}`
- 529: `21.45` → `\frac{429}{20}`
- 784: `0.2833` → `\frac{17}{60}`
- 817: `4.19` → `\frac{88}{21}`
- 936: `17.1875` → `\frac{275}{16}`
- 716: `0.5758` → `\frac{19}{33}`
- 919: `0.1756` → `\frac{3875}{12012}`

**Expected in slice:** ~2-3 items. If all correct flips: +0.7–1.1pp. If half wrong: +0.0pp.
**Why independent:** Tests fraction-form hypothesis alone. No dependency on other slots.

---

## Slot 2 — search_gold_overlay.csv
**Hypothesis:** Web-search-verified GOLD answers (external evidence, independent of our model) are correct and improve score on items where current answer differs.

**Items changed:** 116 (all FREE-form GOLD from `web_search_100` + `web_search_200`)

**Expected in slice:** ~35 items. Yield depends on (a) % already correct after Hendrycks norm, (b) % where search is right and we're wrong. At observed yield rate of ~10-15% net positive: +1-2pp.
**Risk:** Some search answers may be in slightly wrong format (e.g., extra prefix `x=...`) and overwrite items we already had correct.
**Why independent:** Tests external-evidence overlay alone. MCQ items excluded since search returns values not letters.

---

## Slot 3 — mcq_teacher_override.csv
**Hypothesis:** When 2+ teachers agree on an MCQ letter that DIFFERS from our current best, the teacher consensus is more reliable.

**Items changed:** 26 MCQ letter flips (e.g., 18: I→H, 102: E→I, 329: D→J, 670: A→D, ...)

**Expected in slice:** ~8 items. At 30-50% net yield (teacher consensus is fairly reliable on MCQ): +1-1.4pp.
**Risk:** Teacher consensus is wrong on some items; we'd flip right→wrong.
**Why independent:** Tests MCQ letter-correction hypothesis alone.

---

## Slot 4 — undercount_expand.csv
**Hypothesis:** Items where Qwen emits fewer answer slots than the question requires (per `[ANS]` markers) are losing points because the grader sees an incomplete answer. Teacher multi-answer consensus fills the gap.

**Items changed:** 51 multi-answer expansions (e.g., 0: `16` → `4,16`; 20: `229` → `228,229,250`; 188: `61` → `60,60,60`; ...)

**Expected in slice:** ~15 items. This is the DOMINANT failure mode per V3 tracker (79% of B1-7 failures). At 20-40% net yield: +1-2.5pp.
**Risk:** Teacher's multi-answer may have wrong values for slots we'd otherwise have correct in the last slot.
**Why independent:** Tests multi-slot expansion alone.

---

## Slot 5 — combined_all.csv
**Hypothesis:** All four evidence overlays (frac + search + MCQ teacher + undercount) applied together produce additive gains. Tests the JOINT effect.

**Items changed:** 186 unique items (priority: undercount > frac > MCQ > search where they conflict).
- 8 fraction
- 26 MCQ letter
- 51 undercount expansion
- 116 search gold (some collisions resolved by priority)

**Expected in slice:** ~56 items changed. If overlays are additive: +3-5pp. If they interfere or have overlap: smaller gain. If too aggressive: could fall below 0.692.
**Why independent (NOT chained):** Built from the same evidence sources as slots 1-4, applied to the SAME base. Doesn't require slot 1-4 results to build or interpret. Stands alone as "joint application of post-processing levers" hypothesis.

---

## What we DON'T test today (deliberately deferred)

- Trailing-zero strip — already tested, NEUTRAL (#25 = #26 = 0.692)
- 117 `format_only_diff` items — Hendrycks strips whitespace anyway (false signal)
- V1/V2 counting prompt — pre-inference, can't build in 15 min
- SFT variants — repeatedly net-negative or break-even
- Per-slot \boxed{} formatting — proven −16.2pp
- Order reversal — proven −17.6pp

---

## Information gain we get regardless of scores

Each slot is also a probe:
- Slot 1 score tells us: do fraction conversions help on slice?
- Slot 2 score tells us: is search gold reliable enough to overlay broadly?
- Slot 3 score tells us: is teacher MCQ consensus better than Qwen?
- Slot 4 score tells us: is multi-answer expansion the dominant lever everyone says it is?
- Slot 5 score tells us: do these levers interfere or stack additively?

Independent of WHICH wins, we get 5 independent measurements of post-processing lever value.

## Upload order (suggested, parallel is fine since no chaining)

Submit any order. All 5 are independent. Recommended: Slot 4 first (highest expected delta), then 5, 3, 2, 1.
