# HISTORICAL_STACK.md — Reconstruction of the 0.713 stack

**Audit date:** 2026-05-30 · **Agent:** claude_vscode · **Branch/HEAD:** `main` @ `f8c17e9`
**Method:** git log per file + `submission/29_05/RUN_REPORT.md` + `submission/REGISTRY.md`. No code changed.

## Submission + score
- **`submission/29_05/csvs/undercount_plus_frac.csv` = 0.713** (REGISTRY #35, "Slot 4 + Slot 1 additive stack — NEW BEST").
- Built **2026-05-28**, commit **`84dcb08`** ("Build undercount_plus_frac.csv and mcq_prepend_fix.csv from 0.706 base").

## Source inference run
- `inference/results/run14b_sc8_v1_private943_tok32k_pp1.jsonl` (Qwen3-4B-Thinking-2507, SC=8, 32k tok). `_v3filtered` variant also present.

## Ordered stack at submission time (raw inference → submitted CSV)
1. **Inference** — run14b SC@8 → per-item voted answers.
2. **Fusion → `slot1_kitchen_sink_C.csv` (0.692)** — SC8 vote + Wolfram + answer-sheet + prior teacher overrides. Answer-sheet builder lineage: `submission/scripts/build_answer_sheet_v5_1.py` (`e07ef0e`). REGISTRY #26.
3. **Undercount expansion → `slot4_undercount_expand.csv` (0.706)** — 51 items expanded. Built 25_08, commit `5225c25`. REGISTRY #33. (The 51 ids are listed in `29_05/RUN_REPORT.md §2`.)
4. **Frac override append → `undercount_plus_frac.csv` (0.713)** — 8 items `{135,207,529,716,784,817,919,936}`, mechanism `response = slot4_response + "\n\n\\boxed{FRAC}"`. Disjoint from the 51 undercount items, so 0.706 is preserved verbatim on those and the 8 frac items get the last-box override.

## KEY FINDING
**`postprocessing/scripts/normalizer.py` was NOT in the 0.713 stack.** The 0.713 result was produced entirely by the **submission-build pipeline** (answer-sheet fusion + targeted per-item `\boxed{}` appends documented in `84dcb08`). The "0.713 normalization stack" phrasing in docs is a misnomer — there was no single normalizer runner; it was a documented multi-step build. `normalizer.py` has **never been scored on Kaggle** (its first end-to-end Kaggle run is slot 4 of `submission/30_05/SCORES.md`, still awaiting).

## Diff vs current state (script SHA deltas since 0.713 / 84dcb08)
| Script | At 0.713 era | Current SHA | Changed? |
|---|---|---|---|
| `postprocessing/scripts/normalizer.py` | n/a (added later, `c07e149`) | `5e10eb5` (05-30) | **YES — rewritten to single-mode; auto frac/format transforms removed** |
| `postprocessing/scripts/apply_grader_normalization.py` | `e07ef0e` | `e07ef0e` | no |
| `postprocessing/scripts/fix_submission_format.py` | `e07ef0e` | `e07ef0e` | no |
| `postprocessing/scripts/post_filter.py` | `e07ef0e` | `e07ef0e` | no |
| `submission/scripts/build_answer_sheet_v5_1.py` | `e07ef0e` | `e07ef0e` | no |

**No scripts deleted** since `84dcb08` (verified `git log --diff-filter=D 84dcb08..HEAD`).

## Source SHAs (A5)
- `private.jsonl` @ `fc507a7` (2026-05-13) — **unchanged**.
- `data/search/teachers/anchor_set_FINAL.csv` @ `d31b7dc` (2026-05-30) — **changed** (updated by the round-3/anchor work — the premise of this audit).
