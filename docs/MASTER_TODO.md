# MASTER_TODO

**Last updated:** 2026-05-26 ~14:00 PT

## Now
- [ ] Confirm slot1_reformat.csv uploaded to Kaggle (now on main)
- [ ] Wait Wolfram batches 4-7 (~30 min)
- [ ] A30 adapter v5 smoke (id=0, ~10 min) → green-light "full"
- [ ] When 8/8 Wolfram batches in Drive: build slot1_wolfram_full_overrides.csv

## Before Kaggle reset (~17:11 PT)
- [ ] Submit Slot 2 (slot1_wolfram_full_overrides.csv) by ~14:45 PT
- [ ] Interpret Slot 1 score (back ~15:00 PT)
- [ ] Interpret Slot 2 score (back ~15:30-16:00 PT)

## Mid-late afternoon
- [ ] tnr-1 rescue completes ~16:30-17:00 PT → NoThinking auto-chains
- [ ] tnr-0 A1 completes ~17:43 PT → A2 auto-chains
- [ ] A30 adapter completes ~17:30-19:30 PT

## Evening
- [ ] tnr-1 NoThinking done ~18:30-19:00 PT
- [ ] tnr-0 A2 done ~21:00 PT
- [ ] All inference sources landed

## Night (21:00-23:00 PT)
- [ ] Build scripts/build_confidence_map.py
- [ ] Run it → results/pace/confidence_map.csv
- [ ] Build submissions/slot_c_<descriptor>.csv from confidence map
- [ ] Strategic review with Rain

## Tomorrow morning (Day 3)
- [ ] Submit Slot C as Kaggle slot 1
- [ ] Launch Trace POC (Opus 4.7 judge on 90 test items)
- [ ] Build Slot D from confidence map + Wolfram + (if Trace passes) judge overrides
- [ ] Submit Slot D
- [ ] Plan Slot E based on scores

## Day 4-6
- [ ] Confidence map iteration with new signals
- [ ] Wolfram pass 2 targeted arbitration
- [ ] Slot E and Slot F decisions

## Deferred (this week, low priority)
- DataApp PAT rotation + repo cleanup (required before extending DataApp; bypass via standalone llm_judge.py for now)
- Shootout calibration on 50 known-answer items
- Multi-round SC pilot
- Prompt-variation shootout
