# 25_08 — Kaggle Scores (COMPLETE)

**Base:** `slot1_kitchen_sink_C.csv` = 0.692

| Slot | CSV | Items changed | Score | Δ vs 0.692 | Slice items net | Verdict |
|------|-----|---------------|-------|------------|-----------------|---------|
| 1 | slot1_frac_override.csv | 8 | **0.699** | **+0.007** | **+2** | ✅ WIN — fraction format confirmed |
| 2 | slot2_search_gold_overlay.csv | 116 | 0.671 | **−0.021** | **−6** | ❌ LOSS — search bulk harmful |
| 3 | slot3_mcq_teacher_override.csv | 26 | 0.692 | 0.000 | 0 (no-op) | 🟡 MCQ append-bug confirmed |
| 4 | slot4_undercount_expand.csv | 51 | **0.706** 🏆 | **+0.014** | **+4** | ✅✅ NEW BEST — undercount is the lever |
| 5 | slot5_combined_all.csv | 186 | 0.696 | +0.004 | +1 | ⚠️ Interference; search drag |

## Per-change yield analysis

| Slot | Changes | Slice items affected (est) | Net slice gain | Per-change yield |
|------|---------|----------------------------|----------------|-------------------|
| 1 frac | 8 | ~2.4 expected | +2 | **~83% conditional** (very high) |
| 2 search | 116 | ~35 expected | −6 | **−17% conditional** (actively wrong on net) |
| 4 undercount | 51 | ~15 expected | +4 | **~27% conditional** (solid) |
| 5 combined | 186 (160 effective) | ~48 expected | +1 | **2% conditional** (search drag) |

Yield numbers explain the result: search-gold's −17% conditional yield means about half its 35 slice items flipped WRONG → wrong direction, dragging combined.

## Confirmed AMBER alert items

- **AMBER #3 (MCQ append-bug)**: CONFIRMED empirically. Slot 3 = exactly 0.692, no change.
- **AMBER #4 (proxies, not ground truth)**: CONFIRMED for search-gold specifically. The "GOLD" label in `web_search_100/200` is unreliable as a ground-truth proxy.

## Implications for next round

- **NEW BASE: `slot4_undercount_expand.csv` = 0.706**
- Natural next submission: stack slot 1 + slot 4 (no search) → likely ~0.713 if additive
- Drop bulk search-gold from future stacks
- Rebuild MCQ override with full-replace mechanism if we want to test raw-teacher-vs-fusion (completed in 29_05 Build 2: fusion wins on disagreements; raw-teacher-vs-Qwen on MCQ remains untested)
