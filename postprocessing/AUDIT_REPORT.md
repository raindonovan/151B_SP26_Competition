# AUDIT_REPORT.md — Normalization stack audit

**Date:** 2026-05-30 · **Agent:** claude_vscode · **Branch/HEAD:** `main` @ `f8c17e9` (4 uncommitted entries, untouched by this audit)
**Scope:** confirm what's in `postprocessing/`, what produced 0.713, and whether anything drifted. **No code changed.**
**Companion:** `postprocessing/HISTORICAL_STACK.md` (Phase B reconstruction).

---

## TL;DR (3 things)
1. **The 0.713 stack is NOT `normalizer.py`.** 0.713 came from the submission-build pipeline (answer-sheet fusion → undercount expand → 8 frac `\boxed{}` appends, commit `84dcb08`). `normalizer.py` has never been Kaggle-scored. See HISTORICAL_STACK.md.
2. **Current stack runs clean (0 exceptions)** on the locked base run — but **the current `normalizer.py` (5e10eb5) silently corrupts at least one correct multi-answer item** (item 15: `8, NONE` → `8, 8,NONE`). Confirmed defect, located. Does **not** affect 0.713; **does** affect the planned `30_05` slot-4 end-to-end normalizer run.
3. **No scripts deleted; no STOP-halt condition hit.** Source `private.jsonl` unchanged; `anchor_set_FINAL.csv` updated 05-30 (expected — the audit's premise).

---

## PHASE A — Inventory (`postprocessing/`)

| File | Lines | Last SHA | Date | One-line purpose |
|---|---|---|---|---|
| scripts/apply_grader_normalization.py | 253 | `e07ef0e` | 05-27 | Normalize content of last `\boxed{}` only; modes incl. `dfrac_only` (diagnostic) |
| scripts/fix_submission_format.py | 256 | `e07ef0e` | 05-27 | Consolidate multiple `\boxed{}` into one `\boxed{v1,v2,...}` for multi-answer items |
| scripts/post_filter.py | 198 | `e07ef0e` | 05-27 | Retroactive shape-filter on SC JSONL; re-vote on filtered samples |
| scripts/normalizer.py | 698 | `5e10eb5` | **05-30** | Canonical single-mode normalizer (extraction + Hendrycks-safe cleanup + structural MCQ/multi-slot fixes + per-item overrides). **Auto frac/format transforms removed.** |
| scripts/hendrycks_local.py | 169 | `c07e149` | 05-29 | Local extraction/equality helpers (strict-Hendrycks reference) |
| scripts/evaluate_normalizer.py | 76 | `c07e149` | 05-29 | Fixture harness for normalizer |
| per_item_overrides.csv | 0 | `c07e149` | 05-29 | Per-item override registry — **EMPTY (0 rows)** |
| FINDINGS / FORMAT_RULES / NORMALIZATION_RULES / NORMALIZER_SPEC / FORMAT_RULE_REGISTRY+AUDIT / STRICT_NORMALIZER_SPEC | — | mixed | — | Rule docs (mix of current + superseded) |

- **Canonical grader:** `grading/grader.py` = thin wrapper exposing the **value-equality** engine as `Grader` (imports cleanly, antlr present). Strict-Hendrycks `kaggle_like_is_equiv` is **DEPRECATED** per its own header.
- No `postprocessing/CATALOG.md`.

## PHASE B — Historical stack
Full reconstruction in `postprocessing/HISTORICAL_STACK.md`. Summary: `run14b SC8 → kitchen_sink_C (0.692) → slot4 undercount-expand (0.706) → +8 frac appends (0.713)`, commit `84dcb08`. `normalizer.py` not involved. Only `normalizer.py` changed since (rewritten single-mode); all `e07ef0e` scripts unchanged; none deleted.

## PHASE C — Current stack behavior
Ran current `normalizer.py` (`normalize_with_report`) on the **first 20 items of `run14b_sc8_v1_private943_tok32k_pp1.jsonl`** (sample[0] response), scored raw-extract vs normalized-candidate against `anchor_set_FINAL.csv` via `grading/grader.py`.

- **Exceptions: 0** (A2 ✅). Output non-empty.
- **10 of 20 items overlap the anchor.** Per-item break check (correct-in → wrong-out):
  - **Item 15 — CONFIRMED BREAK.** Raw final box `8, NONE` (correct, 2 slots) → normalizer candidate **`8, 8,NONE`** (3 values, `8` duplicated), gold `8, NONE`. **No flag raised** (silent). Cause: `multi_answer_normalize` (normalizer.py:192) consolidates **all** `\boxed{}` in the response (`extract_all_boxed`), pulling a stray intermediate `\boxed{8}` into the final list instead of trusting the final box that already had both slots.
  - **Item 12 — NOT a break** (false positive from my grader proxy). `2c + 4p = 70, 11` → `2c+4p=70, 11` is whitespace-only / value-identical.
  - **Item 5 — benign.** `OVERCOUNT_6_TO_5` flag but final candidate identical to raw.
- **A3 (score within 2pp of expected): NOT cleanly assessable.** The 10-item overlap is mostly multi-answer/equation/expression; the simple value-equality proxy I used (`judge_single_numerical_value` + string fallback) cannot score those item types correctly, so a subset-accuracy number would be misleading. The meaningful Phase-C signal is the per-item break check above. A faithful accuracy run needs the grader's full `auto_judge` with per-item answer types.

## KNOWN LEVERS — A4 (each mapped to current path + SHA)

| Lever | Status | Code home (path @ SHA) |
|---|---|---|
| Fraction fixes (additive) | Auto-transform **removed** from `normalizer.py@5e10eb5` (value-equality makes it moot). Mechanism survives as `force_fraction` override → `per_item_overrides.csv` (**empty**). Hendrycks-safe `\dfrac→\frac` shorthand only remains (value-neutral). | normalizer.py `5e10eb5`; per_item_overrides.csv `c07e149` (0 rows) |
| Undercount expansion (additive) | Present. **This is the path with the item-15 defect.** | normalizer.py `5e10eb5` (`multi_answer_normalize`) |
| Strip trailing zeros (neutral) | Present in answer-sheet builders; moot under value-equality (`4.000==4`). | build_answer_sheet_v5/v5_1/v6 `e07ef0e`; normalizer cleanup `5e10eb5` |
| Bulk search overlays (harmful) | No permanent script — was a one-off build (slot2, 25_08). Anti-pattern; correctly has no active code. | n/a |
| Last-boxed order-sensitive | Present (extraction). | normalizer.py `5e10eb5` (`extract_all_boxed`/last-box); grading/grader.py |
| Multi-slot single-box | Present. **See contradiction below.** | normalizer.py `5e10eb5`; fix_submission_format.py `e07ef0e` |

## STOP-RULE RESULTS (all checked)
- Normalization script deleted since 0.713? **No.**
- Stack runner locatable? **Yes** — `normalizer.py` has a CLI (`normalize_csv`); the 0.713 build was a documented multi-step pipeline (reconstructed in HISTORICAL_STACK.md), not a single script.
- Empty output / exceptions? **No** (0 exceptions, non-empty).
- Documented lever with no code? **No defect** — frac auto-transform is intentionally removed (override path exists but is unpopulated); search-overlay correctly has no code.

→ **No STOP-halt condition triggered.** One material defect surfaced (item 15) — reported, not fixed (work-unit forbids code changes absent trivial fix + strategy auth).

## FLAGS (factual; no fix applied)
1. **DEFECT — multi-answer consolidation corrupts correct items, silently.** `normalizer.py:192 multi_answer_normalize` over-collects intermediate boxes. Confirmed on item 15 (`8, NONE`→`8, 8,NONE`). Blast radius beyond the 20-item subset is **unmeasured**. Relevant to `30_05` slot-4 (first e2e normalizer scoring); irrelevant to 0.713.
2. **Naming drift** — docs/registry refer to a "0.713 normalization stack"; 0.713 was produced by the submission-build pipeline, not `postprocessing/normalizer.py` (which is unscored).
3. **Doc contradiction (unresolved)** — `agents/CLAUDE_VSCODE.md:156` says "Multi-box tolerant … Don't consolidate to single box," but `normalizer.py` and `fix_submission_format.py` **do** consolidate to a single box.
4. **`per_item_overrides.csv` is empty** — the per-item frac/override lever mechanism exists but carries 0 entries.
5. **A5** — `anchor_set_FINAL.csv` is **not** unchanged: updated `d31b7dc` (05-30) by the anchor work. `private.jsonl` unchanged (`fc507a7`).

## ACCEPTANCE
- A1 (report written): ✅ this file + HISTORICAL_STACK.md.
- A2 (runs end-to-end, no exceptions): ✅ 0 exceptions on 20 items.
- A3 (score within 2pp of expected): ⚠️ not cleanly assessable with a single-numeric proxy on a multi-answer subset; per-item break check done instead.
- A4 (every lever → path + SHA): ✅ table above.
- A5 (source SHAs unchanged): ⚠️ `private.jsonl` unchanged; `anchor_set_FINAL.csv` changed 05-30 (expected).
