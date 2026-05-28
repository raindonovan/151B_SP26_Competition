# Submission Integrity Report — 2026-05-27

**Auditor:** submission_master
**Scope:** Line-by-line integrity check of all 34 submission CSVs in repo

## VERDICT: NO CORRUPTION FROM PARTIAL DOWNLOADS

All 34 CSVs pass integrity checks: 943 rows each, IDs 0-942 complete, no duplicates, no empty response cells, no EOF truncation. Rain's concern about submitting before download finished did NOT cause data corruption in any committed file.

## FLAGS (3 findings, 1 critical)

### 🔴 FLAG 1: track_C_day3_v1.csv is IDENTICAL to track_B_day3_v1.csv
- Same git SHA: `9ddedd04`
- Byte-for-byte identical content confirmed
- If both were submitted to Kaggle, a submission slot was wasted
- Both score the same → no information gained from the duplicate

### ⚠️ FLAG 2: id=405 has unbalanced braces in ALL submissions
- Every submission from base inference has { =103, } =108 (diff=-5) on item 405
- Present consistently → upstream in the model output, not a CSV issue
- The boxed extractor still works (extracts last balanced \boxed{})
- Low risk but worth noting for any future response-level debugging

### ⚠️ FLAG 3: 18 persistent no-box items across all slot1_* derivatives
- IDs: 93, 112, 161, 204, 229, 308, 312, 376, 383, 445, 453, 498, 652, 724, 799, 809, 836, 911
- These are the same 18 items that hit the token limit in run14b (32K tokens)
- trackA rescued 5 HIGH (229,308,383,498,445) → 13 remaining
- trackB rescued 8 more MEDIUM → 5 remaining (93,112,376,652,809)
- The 5 remaining are LOW confidence rescues — left unrescued by design

## NO-BOX COUNT EVOLUTION (shows pipeline working)

| Submission | No-box items | Notes |
|-----------|-------------|-------|
| run08v2 (first, SC=8 16K) | 113 | Token limit at 16K |
| run09 (SC=8, 16K) | 93 | SC voting helped some |
| run14b (SC=8, 32K) | 18-19 | 32K eliminated 75 no-box items |
| slot1_* derivatives | 18 | Same base inference |
| Track A (+ 5 HIGH rescue) | 13 | Rescue pipeline working |
| Track B (+ 8 MEDIUM rescue) | 5 | Only LOW confidence remain |

## PAIRWISE ANSWER AGREEMENT (key pairs)

| Pair | Agree | Differ | Notes |
|------|-------|--------|-------|
| slot1_reformat vs trackA_day4 | 925 | 0 | trackA_day4 = slot1_reformat + 5 rescues (identical where both have answers) |
| track_A_day3 vs track_B_day3 | 923 | 7 | Only 7 wolfram/web overrides differ between tracks |
| run14b_v3filtered vs slot1_reformat | 769 | 156 | 156 items changed by post-processing pipeline |
| track_A_day3 vs trackA_day4 | 748 | 46 | 46 items differ (different wolfram batch, different override decisions) |
| track_B_day3 vs trackB_day4 | 931 | 7 | Very close — same overrides, minor value differences |

## DAY 3 v1→v2 CHANGES

- Track A v1→v2: +8 MEDIUM rescue items added (161,204,312,453,724,799,836,911)
- Track B v1→v2: 1 formatting tweak (id=218: `\arcsin\!` → `\arcsin `)

## SCORE CONTEXT

| Submission | Boxed items | Score | ~Correct | Error rate on boxed |
|-----------|------------|-------|----------|-------------------|
| slot1_wolfram (best real) | 925 | 0.653 | ~615 | 33.5% |
| slot1_reformat | 925 | 0.646 | ~609 | 34.2% |
| run14b_v3filtered | 925 | 0.646 | ~609 | 34.2% |
| info_4 (best diag) | 943 | 0.671 | ~632 | 33.0% |

~310 items are wrong despite having a \boxed{} answer. The ceiling from fixing wrong answers (not just rescuing no-box items) is much larger than the no-box rescue path.

## DIAGNOSTIC SUBMISSIONS — VERIFIED

All diagnostic submissions have expected structure:
- E_05_13_h100run_e.csv: Every response is exactly 88 bytes (all-placeholder, scored 0.028 as expected)
- info_3_full_answersheet.csv: Short responses (avg 32 bytes, just answer values)
- diagnostic_sub_a/c: Variable length with teacher traces
