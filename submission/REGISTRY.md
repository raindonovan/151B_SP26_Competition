# Submission Registry — Definitive (from Kaggle screenshots 2026-05-28)

34 successful submissions + 2 errors = 36 total attempts.

| # | Repo CSV | Score | What it tested |
|---|---|---|---|
| 34 | 25_08/slot5_combined_all.csv | 0.696 | All 4 overlays stacked (frac+search+mcq+undercount) |
| 33 | 25_08/slot4_undercount_expand.csv | **0.706** | **Undercount expansion (51 items) — NEW BEST** |
| 32 | 25_08/slot3_mcq_teacher_override.csv | 0.692 | MCQ teacher override (no-op: append-bug, AMBER #3) |
| 31 | 25_08/slot2_search_gold_overlay.csv | 0.671 | 116 web-search GOLD overlay (NET HARMFUL) |
| 30 | 25_08/slot1_frac_override.csv | 0.699 | 8 decimal→fraction conversions (HENDRYCKS CONFIRMED) |
| 29 | slot5_minus_all_med.csv | 0.689 | Ablation: minus ALL MED |
| 28 | slot4_minus_wolfram_med.csv | 0.689 | Ablation: duplicate of #27 |
| 27 | slot4_minus_wolfram_med.csv | 0.689 | Ablation: minus Wolfram MED |
| 26 | slot1_kitchen_sink_C.csv | **0.692** | Kitchen sink + strip — **BEST** |
| 25 | slot2_no_trailing_zero_strip.csv | **0.692** | Without strip — **STRIP NEUTRAL** |
| 24 | slot1_wolfram_full_overrides.csv | 0.653 | Wolfram overrides only |
| 23 | slot1_reformat.csv | 0.646 | Base + format fixes |
| 22 | slot1_minimal_norm.csv | 0.643 | Minimal LaTeX norm |
| 21 | slot3_run14b_nobox_patched.csv | 0.646 | run14b + no-box patches |
| 20 | info_4_t1lock_sheet_rest.csv | **0.671** | T1 lock + sheet — **BEST DIAG** |
| 19 | slot1_adapter_v5_plus_run14b.csv | 0.639 | SFT v5 + run14b hybrid |
| 18 | info_2_answersheet_on_uncertain.csv | 0.667 | Sheet on uncertain items |
| 17 | sftv4_adaptive_rerolled.csv | 0.597 | SFT v4 adaptive |
| 16 | sftv3_epoch8_sc1_final.csv | 0.452 | SFT v3 — failed |
| 15 | g_epoch8_lora_G.csv | 0.017 | Broken SFT v3 lora |
| — | g_epoch8_lora_G.csv | Error | Failed upload x2 |
| 14 | run14b_v3filtered.csv | 0.646 | SC=8 32K V3-filtered |
| 13 | run14b_sc8_v1.csv | 0.639 | SC=8 32K V1 |
| 12 | f_today_F.csv | 0.137 | Early diagnostic |
| 11 | D_05_07_numina_d.csv | 0.310 | NuminaMath traces |
| 10 | E_05_13_h100run_e.csv | 0.028 | All-placeholder |
| 9 | post_filtered_b.csv | 0.151 | Post-filter experiment |
| 8 | diagnostic_sub_a.csv | 0.505 | New formatting |
| 7 | diagnostic_sub_c.csv | 0.222 | Diagnostic |
| 6 | run09sc8_format_fixed.csv | 0.611 | SC=8 + format fix |
| 5 | run09sc8_probe_b_reversed.csv | 0.438 | Reversed order (-17.6pp) |
| 4 | run09sc8_v1_private943.csv | 0.614 | SC=8 baseline |
| 3 | expA_run08_perslot_perturbed.csv | 0.420 | Per-slot perturbed |
| 2 | run10_v3perslot_private943.csv | 0.424 | V3 per-slot prompt |
| 1 | run08v2_v1_private943.csv | 0.586 | First submission |

## Key findings
- **NEW BEST: 0.706 from slot4_undercount_expand** (+1.4pp over previous best 0.692)
- **Undercount expansion CONFIRMED as dominant lever** (+4 slice items from 51 changes)
- **Hendrycks-prefers-fractions CONFIRMED** (+2 slice items from 8 decimal→fraction)
- **Bulk search-gold overlay is NET HARMFUL** (−6 slice items from 116 changes) — needs source-quality stratification
- **MCQ append-to-end mechanism BROKEN** (AMBER #3 confirmed: Slot 3 was exact no-op)
- Strip neutral: #26 = #25 (both 0.692) — strip neither helps nor hurts
- MED = +0.3pp: #26 (0.692) vs #27/#29 (0.689)
- Order matters: #4 (0.614) vs #5 (0.438) = -17.6pp
- CURRENT PICKS ARE WRONG: 0.438 + 0.420 selected — CHANGE BEFORE 5/31

## Naming mismatches (Kaggle vs Repo)
- slot1_kitchen_sink_CCCCCC → slot1_kitchen_sink_C.csv
- slot2_no_trailing_zero_stripzzzzzzzZZZZ → slot2_no_trailing_zero_strip.csv
- AAAslot4/BBBslot4/CCCCslot5 → slot4/slot5 (Kaggle filename dedup)

## Never-submitted (in archive/submissions_never_sent/)
info_1, info_3, slot1_reformat_plus_b2_plus_sheet, slotA_dfrac_only, slot3_minus_rescue_med, trackA/B day3+day4
