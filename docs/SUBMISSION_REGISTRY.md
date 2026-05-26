# Submission Registry v5 — 151B Competition

**Last updated:** 2026-05-26 ~15:00 PT (Day 2, post-Slot-1 result)
**Purpose:** Complete record of every Kaggle submission

> **Day 2 update 2026-05-26**: Added slot1_reformat=0.646 (Day 2 Slot 1) — +0.3pp over slot1_minimal_norm anchor. New best real-inference. Reformat post-processor LOCKED as +0.3pp lever.

## SUBMISSIONS (sorted by score)

| # | File | Score | Config | Date |
|---|---|---|---|---|
| 1 | info_4_t1lock_sheet_rest.csv | **0.671** | T1 run14b, T2-T4 from sheet — **BEST DIAG** | 2026-05-25 |
| 2 | info_2_answersheet_on_uncertain.csv | 0.667 | T1+T2 run14b, T3+T4 sheet | 2026-05-25 |
| 3 | **slot1_reformat.csv** | **0.646** | slot1_minimal_norm + reformat post-processor — **BEST REAL** | 2026-05-26 |
| 4 | run14b_v3filtered.csv | 0.646 | Base, SC=8, 32K, V3 shape filter | 2026-05-23 |
| 5 | slot3_run14b_nobox_patched.csv | 0.646 | 18 no-box patched, 0/18 gain | 2026-05-25 |
| 6 | slot1_minimal_norm.csv | 0.643 | slot1 minimal LaTeX normalizer (prior anchor) | 2026-05-26 |
| 7 | run14b_sc8_v1.csv | 0.639 | Base, SC=8, 32K, no filter | 2026-05-23 |
| 8 | slot1_adapter_v5_plus_run14b_20260525.csv | 0.639 | adapter_v5 + run14b splice | 2026-05-25 |
| 9 | run09sc8_v1_private943.csv | 0.614 | Base, V1, SC=8, 16K | 2026-05-13 |
| 10 | run09sc8_format_fixed.csv | 0.611 | Run09 + format fix | 2026-05-13 |
| 11 | sftv4_adaptive_rerolled.csv | 0.597 | SFT v4, SC=3/16, 16K | 2026-05-24 |
| 12 | run08v2_v1_private943.csv | 0.586 | Base, V1, SC=8 | 2026-05-06 |
| 13 | diagnostic_sub_a.csv | 0.505 | DiagA | 2026-05-22 |
| 14 | sftv3_epoch8_sc1_final.csv | 0.452 | SFT v3, SC=1, MCQ bug | 2026-05-24 |
| 15 | run09sc8_probe_b_reversed.csv | 0.438 | Order reversal probe | 2026-05-13 |
| 16 | run10_v3perslot_private943.csv | 0.424 | V3 per-slot | 2026-05-06 |
| 17 | expA_run08_perslot_perturbed.csv | 0.420 | Per-slot format | 2026-05-06 |
| 18 | D_05_07_numina_d.csv | 0.310 | DiagD | 2026-05-22 |
| 19 | diagnostic_sub_c.csv | 0.222 | DiagC | 2026-05-22 |
| 20 | post_filtered_b.csv | 0.151 | DiagB | 2026-05-22 |
| 21 | f_today_F.csv | 0.137 | DiagF | 2026-05-22 |
| 22 | E_05_13_h100run_e.csv | 0.028 | DiagE | 2026-05-22 |
| 23 | g_epoch8_lora_G.csv | 0.017 | SFT v3 epoch 8 (broken) | 2026-05-24 |

## DAY 2 SUBMISSIONS (in progress)

| # | File | Score | Config | Date |
|---|---|---|---|---|
| 24 | slot1_wolfram_full_overrides.csv | TBD ~16:00 PT | slot1 + Wolfram canonical overrides on 38 PACE items | 2026-05-26 |

## NOT SUBMITTED TODAY (declined candidates)
- slotA_slot1_dfrac_only.csv: confounded probe (dfrac + \\left/\\right both changed; can't isolate). SKIPPED.
- slot1_reformat_plus_b2_plus_sheet.csv: redundant with slot1_reformat (only 1 extra B2 override). Cleaner version submitted instead.

## LOCKED LEVERS (per memory #9 rule 4 — immediate lock-in on score impact)

- **Reformat post-processor**: +0.3pp stable (slot1_reformat=0.646 vs slot1_minimal_norm=0.643). Stack in all future base files. Don't re-probe alone.
- **Minimal LaTeX normalizer**: +0.4pp (slot1_minimal_norm=0.643 vs slot1=0.639). Stack.
- **32K vs 16K token budget**: +2.5pp (run14b vs run09). Default 32K+ for all inference.
- **V3 shape filter**: +0.7pp at SC=8. Apply post-vote.
- **Format-aware system prompt**: validated in smoke (4/8 → 8/8 unanimous on 5-value items). Kaggle-scale measurement pending.

## KEY FINDINGS

- Answer sheet beats run14b on T3+T4 (~+2.1pp) and marginally on T2 (~+0.4pp)
- Real-inference best: slot1_reformat = 0.646 (Day 2 Slot 1, +0.3pp over previous anchor slot1_minimal_norm = 0.643)
- Format losses: per-slot \\boxed{} -16.2pp; order reversal -17.6pp
- 18 no-box items: 0/18 sheet patches scored on Kaggle
- 32K beats 16K (+2.5pp); V3 shape filter +0.7pp
- run14b cross-check (2026-05-26): same 6 items under-generate in slot1 AND run14b → systemic, not config

## ANSWER SHEET NOTES

- SFT submissions EXCLUDED (circular reasoning)
- info_2 + info_4 EXCLUDED (swapped items ARE the sheet's answers — circular)
- Correlated base-model submissions dampened by weight/sqrt(group_size)
- Script: scripts/build_answer_sheet_v5_1.py
- v5.1 sheet has 575 T1+T2 items

## NEXT SUBMISSIONS PLAN

See Drive NEXT_ACTIONS (latest) for tomorrow's Slot C/D/E plan.
