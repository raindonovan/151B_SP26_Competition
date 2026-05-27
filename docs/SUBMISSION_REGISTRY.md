# SUBMISSION REGISTRY — Definitive (compiled 2026-05-27)

Source: Kaggle screenshots (Rain, 2026-05-27) + Drive Submission Registry v4 + repo docs/SUBMISSION_REGISTRY.md

## ALL KAGGLE SUBMISSIONS (sorted by score, from screenshots)

| # | File | Score | Type | Config | Date |
|---|------|-------|------|--------|------|
| 1 | info_4_t1lock_sheet_rest.csv | **0.671** | DIAGNOSTIC | T1 run14b, T2-T4 from sheet | 2026-05-25 |
| 2 | info_2_answersheet_on_uncertain.csv | 0.667 | DIAGNOSTIC | T1+T2 run14b, T3+T4 sheet | 2026-05-25 |
| 3 | **slot1_wolfram_full_overrides.csv** | **0.653** | REAL | slot1_reformat + 38 Wolfram last-box overrides | 2026-05-26 |
| 4 | slot1_reformat.csv | 0.646 | REAL | slot1_minimal_norm + reformat (54 multi-answer) | 2026-05-26 |
| 5 | run14b_v3filtered.csv | 0.646 | REAL | SC=8, 32K, V3 shape filter | 2026-05-23 |
| 6 | slot3_run14b_nobox_patched.csv | 0.646 | DIAGNOSTIC | 18 no-box patched → 0/18 gain | 2026-05-25 |
| 7 | slot1_minimal_norm.csv | 0.643 | REAL | minimal LaTeX normalizer | 2026-05-26 |
| 8 | run14b_sc8_v1.csv | 0.639 | REAL | SC=8, 32K, no filter | 2026-05-23 |
| 9 | slot1_adapter_v5_plus_run14b_20260525_1623.csv | 0.639 | REAL | adapter v5 + run14b splice | 2026-05-25 |
| 10 | run09sc8_v1_private943.csv | 0.614 | REAL | V1, SC=8, 16K | 2026-05-13 |
| 11 | run09sc8_format_fixed.csv | 0.611 | REAL | Run09 + format fix | 2026-05-13 |
| 12 | sftv4_adaptive_rerolled.csv | 0.597 | REAL | SFT v4, SC=3/16, 16K | 2026-05-24 |
| 13 | run08v2_v1_private943.csv | 0.586 | REAL | V1, SC=8 (first submission) | 2026-05-06 |
| 14 | diagnostic_sub_a.csv | 0.505 | DIAGNOSTIC | DiagA | 2026-05-22 |
| 15 | sftv3_epoch8_sc1_final.csv | 0.452 | REAL | SFT v3, SC=1 | 2026-05-24 |
| 16 | run09sc8_probe_b_reversed.csv | 0.438 | DIAGNOSTIC | order reversal probe | 2026-05-13 |
| 17 | run10_v3perslot_private943.csv | 0.424 | DIAGNOSTIC | V3 per-slot format | 2026-05-06 |
| 18 | expA_run08_perslot_perturbed.csv | 0.420 | DIAGNOSTIC | per-slot format | 2026-05-06 |
| 19 | D_05_07_numina_d.csv | 0.310 | DIAGNOSTIC | DiagD | 2026-05-22 |
| 20 | diagnostic_sub_c.csv | 0.222 | DIAGNOSTIC | DiagC | 2026-05-22 |
| 21 | post_filtered_b.csv | 0.151 | DIAGNOSTIC | DiagB | 2026-05-22 |
| 22 | f_today_F.csv | 0.137 | DIAGNOSTIC | DiagF | 2026-05-22 |
| 23 | E_05_13_h100run_e.csv | 0.028 | DIAGNOSTIC | DiagE | 2026-05-22 |
| 24 | g_epoch8_lora_G.csv | 0.017 | REAL (broken) | SFT v3 epoch 8 | 2026-05-24 |

Total submitted: 24 (+ 2 failed g_epoch8 uploads shown as Error in Kaggle)

## FILES IN REPO BUT NEVER SUBMITTED TO KAGGLE

These exist in `submissions/` but are NOT in the Kaggle screenshots:

| File | Status | Notes |
|------|--------|-------|
| info_1_teacher_on_uncertain.csv | Prepared, never submitted | Was queued but skipped |
| info_3_full_answersheet.csv | Prepared, never submitted | Full sheet submission, never sent |
| slot1_reformat_plus_b2_plus_sheet.csv | Prepared, skipped | Redundant with slot1_reformat |
| slotA_slot1_dfrac_only.csv | Prepared, skipped | Confounded probe |
| sftv4_adaptive_rerolled.csv | Submitted (0.597) but EXCLUDED from answer sheet | Circular: trained on sheet labels |

## FILES IN KAGGLE BUT NOT IN REPO

| File | Score | Action needed |
|------|-------|--------------|
| slot1_wolfram_full_overrides.csv | 0.653 | ✅ Rain provided CSV — ready to commit |
| g_epoch8_lora_G.csv | 0.017 | Low priority — broken submission |

## ANSWER SHEET SCRIPT

The answer sheet builder has gone through iterations. They're all in `scripts/`:
- `build_answer_sheet.py` — original (v1)
- `build_answer_sheet_v4.py` — score-weighted voting (current memory reference)
- `build_answer_sheet_v5.py` — adds numeric clustering (frac/decimal equivalence)
- `build_answer_sheet_v5_1.py` — adds xhigh recovery (**latest**)

**⚠️ ALL versions have the same stale 15-entry SUBMISSION_REGISTRY.** Missing 9 submissions with known scores.

The answer sheet output lives at `results/answer_sheet/unified_answer_sheet_v5_1.csv`.

## LOCKED LEVERS (Kaggle-validated deltas)

| Lever | Delta | Evidence |
|-------|-------|---------|
| 32K vs 16K token budget | +2.5pp | run14b vs run09 |
| V3 shape filter | +0.7pp | run14b_v3filtered vs run14b_sc8 |
| Minimal LaTeX normalizer | +0.4pp | slot1_minimal_norm vs run14b_sc8 |
| Reformat post-processor | +0.3pp | slot1_reformat vs slot1_minimal_norm |
| Wolfram canonical overrides | +0.7pp | slot1_wolfram vs slot1_reformat |
| Per-slot \boxed{} format | −16.2pp | run10 vs run08v2 |
| Answer order reversal | −17.6pp | probe_b vs run09 |
| Answer sheet on T3+T4 | +2.1pp | info_2 vs run14b |

## DRIVE DOCS TO MIGRATE (deprecated, content captured here)

- "Submission Registry v4" (id: 1wt74-l34t...) — most detailed, has per-submission postmortem
- "Submission Registry v3" (id: 1oQKGS03m...) — 18 submissions
- "Submission Registry v2" (id: 10bayVPnN...) — 17 submissions  
- "Submission Registry" (id: 1xIhTFy00...) — original 12, has decoy name explanations
- "Unified Answer Sheet" (id: 1MIa_921M...) — original methodology doc
- "Back-Solve Mathematical Framework" (id: 1Cs14P3H2...) — Bayesian formula
