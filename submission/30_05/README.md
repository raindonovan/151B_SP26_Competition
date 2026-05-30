# submission/30_05 — Day-8 candidate slots

## Filename convention (going forward)
Submission CSVs are named **`<date>_<slot>_<descriptor>.csv`** to keep filenames
unique across slots (avoids the confusing "every folder has `sheet.csv`" problem
during upload + diff). One CSV per slot folder, paired with `score_summary.json`
and `local_score_vs_anchor.csv`.

## Slots (built on the 0.713 base `submission/csvs/undercount_plus_frac.csv`)
| Slot | File | Overlay |
|---|---|---|
| 1 control | `slot1_control/30_05_slot1_control.csv` | none (0.713 stack output) |
| 2 +anchor | `slot2_anchor/30_05_slot2_anchor.csv` | + anchor_set_FINAL (316) |
| 3 +4/4 bloc | `slot3_bloc/30_05_slot3_bloc.csv` | + 4/4 teacher consensus (385, non-anchor) |
| 4 +3/4 xhigh | `slot4_aggressive/30_05_slot4_aggressive.csv` | + 3/4-with-xhigh MCQ (23, non-anchor) |

Each CSV is 943 rows, columns `[id, response]`. See `SLOTS_1_4_REPORT.md` for the
build details, pairwise diffs, and the (directional-only) local anchor scores.
Rain uploads each slot CSV to Kaggle.
