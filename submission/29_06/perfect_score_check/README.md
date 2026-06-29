# 29_06 — perfect-score sanity check

> ✅ **RESULT: scored 1.0 on Kaggle (CONFIRMED).** The official solutions, boxed back
> into a submission, score a perfect 1.0 — proving our value-equality grader mirror
> (`grading.grader.Grader`) and our response format agree with Kaggle's grader
> **exactly** on all 943 private items. The "believed-accurate, pending confirmation"
> caveat on the grader is now resolved. The grader ships in `summer_research/grading/`
> (`verify_grader.py` reproduces the local 943/943).

**Hypothesis (confirmed).** Box the *official* Kaggle solutions back into a submission CSV and it
should score **1.0** on Kaggle. This is a **validation harness**, not a leaderboard
play: it tests whether our grader mirror (`grading.grader.Grader`) and our response
format actually agree with Kaggle's grader. A 1.0 confirms both; anything less localizes
a format/grader gap. (The competition is over — this is post-comp grader forensics.)

## What it is

- **Source of truth:** `data/raw/_original/solution.csv` — the official post-competition
  grading sheet (943 rows; `id, answer, options, Usage, is_matharena`).
- **Build:** `submission/scripts/build_perfect_score_check.py` (self-verifying).
- **Output:** `29_06_perfect_score_check.csv` — `id,response`, 943 rows, ids zero-padded
  to 4 digits (`0000`) to match the 0.745 winning reference.

## Response format (Strategy A — hybrid)

- **Canonical `\boxed{<value>}`** for every answer. Multi-value (JSON-list) golds are
  comma-joined inside one box (`\boxed{4, 16}`); single values, intervals, and MCQ
  letters go in verbatim (`\boxed{A}`, `\boxed{148.022}`).
- **Exception — the 4 percent answers** (ids 96/169/237/563, golds `158% 400% 50% 20%`):
  a boxed percent does **not** score. `%` is a LaTeX comment character, so the grader's
  boxed extractor truncates at it (`\boxed{158%}` → `158`), and `\%` is normalized away
  (`\boxed{158\%}` → `158`). The grader **keeps** the `%` in the gold, so no boxed form
  can ever match. These four instead use the plain final-answer sentence
  **`The answer is 158%.`**, which the grader's free-text extractor reads as `158%` and
  scores. (Filed as a grader rule in `postprocessing/FINDINGS.md`.)

## Local verification (the confidence signal)

All **943/943 score locally** under the exact grader mirror from
`inference/scripts/analyze_run.py` — `auto_judge` over comma-split gold slots with
per-slot options. Rebuild + re-verify:

```bash
python3 submission/scripts/build_perfect_score_check.py
# -> LOCAL GRADE (grader mirror): 943/943 pass (100.00%)
```

The script exits non-zero if any item fails to grade, so a clean run *is* the
submission-ready gate.

## Expectation on Kaggle

If Kaggle's grader is our value-equality mirror (which the competition campaign found it
to be), this scores **1.0**. Any shortfall is informative: it would name the exact items
where Kaggle's grader/extractor diverges from our mirror — the percent items above are
the known edge case we already had to route around, so they are the most likely to be
where a residual gap (if any) shows up.

*Rain submits to Kaggle; this folder is the locally-verified artifact + provenance.*
