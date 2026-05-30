# answer_sheet_v7_FINAL — Variant 1 master (Day 8)

**Built:** 2026-05-30 by claude_vscode (`scripts/build_answer_sheet_v7.py`). No Kaggle upload from the builder.
**Core idea:** separate **math truth** from **submission string**, and make **format risk visible per row**, after slot 2's anchor overlay scored only +2.5pp (vs +8-15pp predicted) — many anchor items were math-correct but Kaggle-format-incompatible.

## Files
- `data/answer_sheet_v7_FINAL.csv` — the master (943 rows, 11 cols). **LFS-tracked** (12 MB).
- `data/answer_sheet_v7_probe_overlay.csv` — the 74 `ship_class==B` items, with render variants, for the format-probe submission.

## Schema (column definitions)
| col | meaning |
|---|---|
| `id` | 4-digit zero-padded item id |
| `math_answer` | mathematically correct value (canonical truth) |
| `submission_answer` | exact string for Kaggle (may differ from math_answer; **proven base string preserved when value-equal**) |
| `math_source_tier` | T1 (audited anchor / opus-flip) · T2 (4-of-4 bloc, anchor non-A, opus+4teacher) · T3 (opus+3-of-4) · T4 (qwen voted / 0.713 base) · T5 (rescue fallback) |
| `math_sources` | pipe-delimited origin (anchor\|wolfram, teacher_4of4, opus\|teacher_3of4, qwen_voted, rescue_fallback\|...) |
| `format_status` | submission_proven · format_suspect · untested · known_bad |
| `format_strategy` | keep_raw · replace_mcq_box · single_box_multislot · append_last_box |
| `provenance_answer` | 0.713_stack · anchor_audited · anchor_v2_opus_flip · teacher_4of4 · opus_5th_teacher_chatgpt_curated · qwen_voted_raw · rescue_fallback |
| `reason_for_override` | 1-line note (filled when worth surfacing) |
| `ship_class` | A (ship now) · B (needs format probe) · C (hold out) |
| `notes` | optional (e.g. DEEP-secondary markers) |

(Schema lists 11 named columns; the work-unit's "12" appears to be a miscount.)

## Source lineage
anchor_set_FINAL (316) + 4-of-4 teacher bloc (cluster_pattern=='4') + CHATGPT-curated 57 Opus 5th-teacher items + 3 Opus anchor-flips (0120/0248/0308) + 1 quarantine (0187) + 4 no-box rescue items + qwen-voted base (0.713 stack) for the remainder.

**Key policy (DECISION 1, B-ship + A-flagging):** `submission_answer` **never regresses a proven string** — for the 57 value-equal anchor↔Opus contradictions we keep the 0.713 base string, but they are still tagged `format_suspect` / ship B so they enter the probe pool. Only the 21 differing contradictions (+3 flips, +untested overrides) get rebuilt submission strings. Math-truth changes can be aggressive; submission-string changes are conservative.

## Distribution stats (943 rows)
- **math_source_tier:** T1 308 · T2 410 · T3 39 · T4 182 · T5 4
  - (T3 = exact count of n_agree==3 among the 57 Opus items; the other 18 are n_agree==4 → T2.)
- **format_status:** submission_proven 773 · format_suspect 74 · untested 95 · known_bad 1
- **ship_class:** A 864 · B 74 · C 5  (C = 0187 quarantine + 4 no-box T5 rescue items)

## How to use for slot 6+ builds
- **Conservative production sheet:** take `submission_answer` for all `ship_class∈{A}` (and the proven strings of B). This never regresses the 0.713 base and folds in T1/T2/T3 value upgrades.
- **Format probe submission:** use `answer_sheet_v7_probe_overlay.csv` — submit rebuilt renders for the 74 B items to learn which format Kaggle accepts; only promote a render after it scores.
- **Math truth** (`math_answer`) is correct on all rows regardless of `submission_answer`; use it for adapter/training targets and downstream analysis.

## When to override `format_status`
- After slot 3 (4/4 bloc) Kaggle score lands: if the 4/4-bloc items prove Kaggle-accepted, re-tag those `submission_proven` and promote to ship A.
- After the format-probe submission lands: for each B item whose rebuilt render scored, set `format_status=submission_proven` and adopt that render as `submission_answer`.
- General rule: a row only moves toward A once its (math, format) pair has a Kaggle data point; until then keep it conservative.
