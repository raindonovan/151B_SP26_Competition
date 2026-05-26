# Submission Registry v4 -- 151B Competition

**Last updated:** 2026-05-25 late evening, migrated to repo 2026-05-27.
**Purpose:** Complete record of every Kaggle submission

> **Migration note 2026-05-27**: v4 lists 21 subs through 5/25 EOD. Tonight (5/26 eve) added slot1_minimal_norm=0.643 = 22nd sub (included below).

## SUBMISSIONS (sorted by score)

| # | File | Score | Config | Date |
|---|---|---|---|---|
| 1 | info_4_t1lock_sheet_rest.csv | **0.671** | T1 run14b, T2-T4 from sheet -- **BEST DIAG** | 2026-05-25 |
| 2 | info_2_answersheet_on_uncertain.csv | 0.667 | T1+T2 run14b, T3+T4 sheet | 2026-05-25 |
| 3 | run14b_v3filtered.csv | 0.646 | Base, SC=8, 32K, V3 shape filter | 2026-05-23 |
| 4 | slot3_run14b_nobox_patched.csv | 0.646 | 18 no-box patched, 0/18 gain | 2026-05-25 |
| 5 | **slot1_minimal_norm.csv** | **0.643** | slot1 with minimal LaTeX normalizer -- **BEST REAL** | 2026-05-26 |
| 6 | run14b_sc8_v1.csv | 0.639 | Base, SC=8, 32K, no filter | 2026-05-23 |
| 7 | slot1_adapter_v5_plus_run14b_20260525.csv | 0.639 | adapter_v5 + run14b splice | 2026-05-25 |
| 8 | run09sc8_v1_private943.csv | 0.614 | Base, V1, SC=8, 16K | 2026-05-13 |
| 9 | run09sc8_format_fixed.csv | 0.611 | Run09 + format fix | 2026-05-13 |
| 10 | sftv4_adaptive_rerolled.csv | 0.597 | SFT v4, SC=3/16, 16K -- REGRESSION | 2026-05-24 |
| 11 | run08v2_v1_private943.csv | 0.586 | Base, V1, SC=8 | 2026-05-06 |
| 12 | diagnostic_sub_a.csv | 0.505 | DiagA | 2026-05-22 |
| 13 | sftv3_epoch8_sc1_final.csv | 0.452 | SFT v3, SC=1, MCQ bug | 2026-05-24 |
| 14 | run09sc8_probe_b_reversed.csv | 0.438 | Order reversal probe | 2026-05-13 |
| 15 | run10_v3perslot_private943.csv | 0.424 | V3 per-slot | 2026-05-06 |
| 16 | expA_run08_perslot_perturbed.csv | 0.420 | Per-slot format | 2026-05-06 |
| 17 | D_05_07_numina_d.csv | 0.310 | DiagD | 2026-05-22 |
| 18 | diagnostic_sub_c.csv | 0.222 | DiagC | 2026-05-22 |
| 19 | post_filtered_b.csv | 0.151 | DiagB | 2026-05-22 |
| 20 | f_today_F.csv | 0.137 | DiagF | 2026-05-22 |
| 21 | E_05_13_h100run_e.csv | 0.028 | DiagE | 2026-05-22 |
| 22 | g_epoch8_lora_G.csv | 0.017 | SFT v3 epoch 8 (broken) | 2026-05-24 |

## KEY FINDINGS

- Answer sheet beats run14b on T3+T4 (~+2.1pp) and marginally on T2 (~+0.4pp)
- Real-inference best (5/27): slot1_minimal_norm = 0.643
- Format losses are large: per-slot `\boxed{}` -16.2pp; order reversal -17.6pp
- 18 no-box items: 0/18 sheet patches correct on Kaggle
- 32K beats 16K (+2.5pp); V3 shape filter +0.7pp

## ANSWER SHEET NOTES

- SFT submissions EXCLUDED (circular reasoning)
- info_2 + info_4 EXCLUDED (swapped items ARE the sheet's answers -- circular)
- Correlated base-model submissions dampened by weight/sqrt(group_size)
- Script: `scripts/build_answer_sheet_v5.py`
- v5 sheet has 575 T1+T2 items (+89 over v4)

## SUBMISSION QUEUE (planned)

See `docs/DAY_2_SUBMISSION_QUEUE.md` for full details.
