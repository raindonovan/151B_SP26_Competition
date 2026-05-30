# Strategy — Screen-then-Normalize on the Wolfram rows (2026-05-30)

**Method (per Rain's spec):** screen RAW first, normalize only the survivors, analyze
the delta. This deliberately does NOT normalize-then-analyze, which would launder
structurally-bad rows into something that looks clean. Two separate signals come out:
**structural validity** and **surface equivalence after normalization.**

Reproducible: `structural_screen.py` (stage 1) + `normalize_delta.py` (stage 2),
both in this folder. Normalizer = `scripts/gold_equiv.py` (wraps the canonical
value-equality `Grader`/`Judger`). Reference signal for stage 2 = the 4 independent
teachers. No clean ground truth exists — all numbers are proxy estimates.

> **Correction to STRATEGY_WOLF_AUDIT.md §4.** That doc called the 58 discrepancies
> "100% directly actionable." Wrong. Screen-first shows **44 clean, 5 structurally
> invalid (0027, 0082, 0468, 0753, 0923 — contain literal `?`/`...` or ambiguous slot
> boundaries), 9 convention-sensitive** (rounding/variance, gate on the F22 probe).

---

## SIGNAL 1 — Structural validity (RAW, before any normalization)
Of 477 DONE rows:

| Bucket | Count | Meaning |
|--------|-------|---------|
| **Structurally INVALID** | **141 (30%)** | do NOT normalize — data-quality problem |
| Convention-sensitive | 46 (10%) | normalize for inspection only, no auto-promote |
| Structurally valid | 290 (61%) | normalizer's job |

Invalid breakdown:
- **`mcq_stores_value` — 110.** type=MCQ but the row stores the derived *value*, not the
  option *letter* the grader wants. Not promotable as MCQ gold without a value→letter
  map — and per Finding 9 the option text is sometimes missing from the dataset, so the
  map isn't always possible. (This is the class my first audit mis-framed as a "feature.")
- **`slot_count_mismatch` — 27.** free_multi answer's slot count ≠ declared `n_ans_slots`.
  Root cause is mixed: incomplete answers (`0490` "23, …"), prose (`0409`), mis-typed
  MCQ-as-free_multi (`0560`, `0567`, `0587`, `0595`), convention-packed (`0542` stores
  both `[7457 pop / 8388 sample]`). All need structural resolution, not normalization.
- **`ellipsis_or_qmark` — 9.** Answer contains a literal `?` or `...` placeholder
  (`0082` `'1.309,1.677,?,No'`, `0753` `'...,16.56'`). The Wolfram answer is itself
  incomplete; promoting it injects `?`/`...` into the sheet.
- **`prose_or_nonanswer` — 1** (caught by screen v1; see false-negatives below — there
  are more).

## SIGNAL 2 — Surface equivalence (normalize ONLY the 290 valid rows)
Compared each valid Wolfram answer vs the 4 teachers; per row, best teacher outcome:

| Outcome | Count | % of 290 |
|---------|-------|----------|
| raw exact-match to ≥1 teacher | 109 | 38% |
| **match ONLY after normalization (DELTA)** | **101** | **35%** |
| no teacher match even after normalize | 80 | 28% |

**The 35% delta is the normalizer earning its keep** — pure formatting noise it
correctly collapses: latex↔ascii (`\dfrac{7}{2}`↔`-7/2`), frac↔decimal, `\,` spacing,
slot order (`15.84,18.96`↔`18.96,15.84`), `\sqrt{101}`↔`sqrt(101)`. Answer to "how much
of the mess is just formatting": **about a third of the structurally-clean rows.**

### The 80 "unresolved" decompose — and are mostly NOT genuine errors
| Sub-class | Count | Note |
|-----------|-------|------|
| **normalizer coverage GAP** | **~40** | FIXABLE in gold_equiv (see below) |
| rounding / decimal-place convention | ~21 | e.g. `0269` 0.3198 vs 0.320 — convention, not error |
| prose/annotation (screen false-neg) | ~9 | belongs in bucket 1, not here |
| word/synonym | ~2 | `0035` "down" vs "downward" — normalizer can't help |
| **genuine value disagreement** | **~1–3** | `0041` (2112 vs 3542/3986, teachers also disagree); `0418`,`0619` borderline slot-level |

So Wolfram-vs-teacher genuine math disagreement, on structurally-valid rows, is a
*tiny handful* — reassuring, and only visible because we screened first.

## Actionable output A — normalizer coverage gaps (fixable, ~40 rows recoverable)
`gold_equiv._latex_to_ascii` handles `\frac \sqrt \pi \cdot \times \div` but MISSES:
- `\le` `\ge` `<=` `>=` (`0447` `x<=4` vs `x \le 4` — identical, scored disagree)
- `\,` `\;` `\!` thin-spaces inside numbers/lists (`0487`)
- `\approx` (regression-line items `0021`)
- `^\circ` degree marker (`0401`)
- trig/log `\cos \sin \tan \ln` when backslashed (`0273`, `0841` — identical, scored disagree)
- expression term-order commutativity (`0157` `50sin-7cos` vs `-7cos+50sin`)
- label-prefix stripping is partial (`0055` `5x^4` vs `y=5x^4`)
Fixing these converts ~40 false-disagreements into matches and tightens the gold build.

## Actionable output B — structural_screen.py v2 (false negatives found)
v1 let prose/annotation rows into the "valid" bucket. Add detectors for:
- parenthetical annotation on an otherwise-clean answer: `0048` `'C (-2 ~ ln(0.135))'`,
  `0477` `'A, C (leading + open-ended ...)'`, `0859` `'1,2,2,4 (quadrants)'`
- prose stored in a free_single/free_multi row: `0252` `'normal populations + equal var'`,
  `0365` `'x in [-36,36], y in [0,6]'`, `0758`, `0759` (these are MCQ-concept items whose
  letter lives in the teacher column — really a type-mislabel + mcq_stores_value).
Net: true structural-defect count is **~150, not 141.**

## Bottom line for the gold build
1. Promote directly: only structurally-valid + raw/normalized-match rows.
2. Fix the 7 normalizer gaps above → recover ~40 rows cheaply.
3. Route the 110 MCQ-value rows to a value→letter mapping step (blocked where option
   text is missing — Finding 9).
4. Hold the 46 convention-sensitive rows for the F22 Kaggle probe; do NOT auto-promote.
5. The ~1–3 genuine Wolfram-vs-teacher disagreements (esp. `0041`) need a human/3rd source.
