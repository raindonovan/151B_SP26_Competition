# answer_sheet_v7_FINAL — Variant 1 master (Day 8)

**Built:** 2026-05-30 by claude_vscode (`scripts/build_answer_sheet_v7.py`). No Kaggle upload from the builder.
**Core idea:** separate **math truth** from **submission string**, and make **format risk visible per row**, after slot 2's anchor overlay scored only +2.5pp (vs +8-15pp predicted) — many anchor items were math-correct but Kaggle-format-incompatible.

## Files
- `data/answer_sheet_v7_FINAL.csv` — the master (943 rows, 11 cols). **LFS-tracked** (12 MB).
- `data/answer_sheet_v7_probe_overlay.csv` — the 69 `ship_class==B` items, with render variants (render_a/b/c/d), for the format-probe submission.

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
anchor_set_FINAL (316) + 4-of-4 teacher bloc (cluster_pattern=='4') + CHATGPT-curated 57 Opus 5th-teacher items + **4 Opus anchor-flips (0120/0248/0308 + 0836 from CHATGPT secondary review)** + 1 quarantine (0187) + 4 no-box rescue items + qwen-voted base (0.713 stack) for the remainder.

**Secondary-review patch (2026-05-30):** 0836 flipped to Opus value `15` (T1, `anchor_v2_opus_flip_secondary` — anchor refuted by counterexample). REVIEW_FUTURE notes added to 0383 (theorem-level disagreement unresolved) and 0570 (possibly-compromised synthetic prompt); 0405/0586 confirmed-anchor (notes only). No other rows changed.

**Key policy (DECISION 1, B-ship + A-flagging):** `submission_answer` **never regresses a proven string** — for the 57 value-equal anchor↔Opus contradictions we keep the 0.713 base string, but they are still tagged `format_suspect` / ship B so they enter the probe pool. Only the 21 differing contradictions (+3 flips, +untested overrides) get rebuilt submission strings. Math-truth changes can be aggressive; submission-string changes are conservative.

## Distribution stats (943 rows)
- **math_source_tier:** T1 308 · T2 410 · T3 39 · T4 182 · T5 4
  - (T3 = exact count of n_agree==3 among the 57 Opus items; the other 18 are n_agree==4 → T2.)
- **format_status:** submission_proven 773 · format_suspect 71 · untested 98 · known_bad 1
- **ship_class:** A 869 · B 69 · C 5  (C = 0187 quarantine + 4 no-box T5 rescue items)
- **anchor flips: 4** (0120, 0248, 0308, 0836)
- **probe pool (ship B): 69**  (after Fix 1: 0383/0570→A; Fix 2: 0405/0586→untested/A)

## How to use for slot 6+ builds
- **Conservative production sheet:** take `submission_answer` for all `ship_class∈{A}` (and the proven strings of B). This never regresses the 0.713 base and folds in T1/T2/T3 value upgrades.
- **Format probe submission:** use `answer_sheet_v7_probe_overlay.csv` (69 rows) — a clean A/B of `render_d` (Opus's form) vs `render_b` (anchor's form); only promote a render after it scores.
- **Math truth** (`math_answer`) is correct on all rows regardless of `submission_answer`; use it for adapter/training targets and downstream analysis.

## When to override `format_status`
- After slot 3 (4/4 bloc) Kaggle score lands: if the 4/4-bloc items prove Kaggle-accepted, re-tag those `submission_proven` and promote to ship A.
- After the format-probe submission lands: for each B item whose rebuilt render scored, set `format_status=submission_proven` and adopt that render as `submission_answer`.
- General rule: a row only moves toward A once its (math, format) pair has a Kaggle data point; until then keep it conservative.

## format_strategy column — what it actually means
`format_strategy` records the ACTION applied to derive `submission_answer` from `math_answer`, **not** the question type:
- `keep_raw` — math_answer was already the last `\boxed{}` in the 0.713 base; no derivation. Used across all qtypes whenever the base already contains the right answer.
- `append_last_box` — math_answer appended as a new `\boxed{}` at the end (after the existing Qwen response). Used when overriding the base answer.
- `replace_mcq_box` — MCQ full-replacement with `\boxed{LETTER}`.
- `single_box_multislot` — free_multi rendered as one `\boxed{a, b, c}`.
- `fraction_render` / `decimal_render` / `symbolic_render` — reserved for probe-overlay use (not used in v7_FINAL.csv).

To check the underlying qtype of a row, use `master_item_tracker.csv['is_mcq']` and comma presence in `math_answer`.

## Probe overlay (ship_class==B) — membership criteria (69 rows)
A row is in the format-probe overlay iff:
- `opus_verdict == 'contradict'` (anchor↔Opus disagreement), AND
- `anchor_source ∈ {wolfram_only, web_search_only}`, AND
- NOT in {0120, 0248, 0308, 0836} (Opus flips — math resolved), AND
- NOT in {0383, 0570} (CHATGPT secondary: content-uncertain → ship A), AND
- NOT in {0405, 0586} (CHATGPT secondary: anchor confirmed → untested/A), AND
- NOT 0187 (quarantined).

Result: 69 rows where math is reasonably trusted but anchor's format may not be Kaggle-friendly.

## Probe overlay render scheme (69 rows)
Pool composition: 55 multi-part (comma-separated) · 43 contain letters/text/variables · 27 fully numeric · 2 with `\frac`. Because the pool is dominated by multi-part symbolic/text answers (one sensible representation each), a forced fraction-vs-decimal-vs-symbolic triple doesn't exist for most rows. Render columns:
- `render_a_kaggle_friendly` — de-LaTeX'd version where LaTeX exists; else = `render_b` (differs on **3** rows here).
- `render_b_exact_symbolic` — current anchor form (= `math_answer`).
- `render_c_decimal` — decimal evaluation; populated only for fully-numeric items (**27** of 69).
- `render_d_opus_alternative` — Opus's contradiction value; **differs from `render_b` on all 69** by definition of the pool.
- `preferred_render_current` — = `render_b` (anchor format is what we currently ship).

This makes the probe a clean **A/B: `render_d` (Opus form) vs `render_b` (anchor form)** on all 69 items — submitting `render_d` on all 69 directly compares Opus's rendering of the same math against anchor's.
