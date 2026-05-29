# Wolfram Verification — Findings (migrated from Drive)

**Migrated**: 2026-05-27 ~17:50 PT from Drive doc `10lKzVdUUXhErH3C4y65rCikaGwkQuBCj`
**Original maintainer**: wolfmaster + claude_strategy
**Status**: Cumulative cross-batch findings. Append-only.

## Coverage snapshot
- Total dataset: 943 items
- Wolfram coverage: 63 items (~6.7%) across Batches 1-8
- B1-B7 (38 items): 33 HIGH overrides, 2 MED, 3 inconclusive (interpretation-MCQ truncation)
- B8 (25 items): 23 HIGH overrides (incl. 0181 by symmetry argument), 1 no-op, 1 inconclusive (0570 synthetic)
- W-tier remaining high-leverage: ~186 items (174 Qwen-vs-teacher disagreements + 67 teacher splits, with overlap)

## Finding 1 — Qwen's math is right far more often than its strings
**56% of Batch 8 items (14/25) had Qwen mathematically correct but format-mismatched** against Kaggle's string matcher. The dominant failure is encoding, not arithmetic.

**B1-7 audit reinforces this dramatically**: 79% (30/38) of B1-7 items are pure under-count where math reasoning was correct.

## Finding 2 — Qwen failure-mode taxonomy (7 modes)
1. **Multi-slot under-count** — collapses N-slot answer to last slot. Dominant in B1-7 (30/38). Severity up to 12→1 (item 0748).
  - 1a. Multi-select MCQ collapse — single letter when multi-letter required (0633, 0587, 0721)
2. **Decimal/fraction format mismatch** — math right, decimal form fails string-match (0089, 0100, 0106, 0118, 0218, 0395, 0454 all B8)
3. **Symbolic-constant substitution** — plugs numeric values for unspecified constants (0584)
4. **Missing prefix/label/unit** — no `D=`, no `Quadrant`, no `^\circ` (0040, 0072, 0496, 0167)
5. **Multi-option equivalence trap** — multiple options encode same math, Kaggle accepts only one (0317)
6. **Genuine arithmetic error** — small numeric mistake (0506, 0068)
  - 6a. "All of the above" sub-MCQ trap — Qwen picks one true statement instead of D (0721)
7. **LaTeX text-wrap** — model wraps single-letter MCQ as `\text{A}` or `\text{Yes}` (0413, 0622). Kaggle behavior with `\text{}` wrappers UNVERIFIED.

## Finding 3 — Dataset quality issues
- **0317**: dataset bug — options D and H are mathematically equivalent
- **0011**: truncated problem text in private.jsonl
- **0585, 0622, 0858**: trailing [ANS] for interpretation-MCQ with options MISSING from question text. Likely dataset prep dropped MCQ-option text for an entire problem class. 7.9% prevalence in B1-7.
- **0894**: question hint says "theoretically close to 9" but verified count = 10

## Finding 4 — Structural verification trick for MCQ matrix problems
For matrix-answer MCQs, distractor options often have structural violations:
- Similarity matrices MUST be symmetric (r_ij = r_ji)
- Distance matrices satisfy triangle inequality
- Correlation matrices are positive semi-definite

**Item 0181**: only option A is symmetric of 10 candidates. Symmetry-by-elimination resolves in seconds without computing the formula.

## Finding 5 — Wolfram capability boundaries
- **HIGH**: arithmetic, algebra, calculus, closed-form statistics, trig, geometry, classical math results (Putnam), number theory (OEIS), linear algebra
- **MED**: multi-canonical-form items (fraction vs decimal), truncated text, interpretation-MCQ trailing slots
- **LOW**: synthetic OEIS-style sequences not in OEIS (0570), Chinese-textbook non-standard formulas, source-text dependent

## Finding 6 — Computability estimate for full 943
- ~700-750 likely computable to HIGH confidence (~74-80% of dataset)
- ~80-100 synthetic/textbook/source-dependent → LOW solution but HIGH learning yield
- ~30-50 genuinely uncomputable

## Finding 8 — Multi-slot under-count is the DOMINANT failure
**30/38 (79%) of B1-7 items are pure multi-slot under-count.** Qwen's math is right; it emits only the last 1-2 slots of an N-slot answer.

**Implications**:
- Highest-leverage post-processing lever in the dataset is slot-counting / multi-slot reconstruction
- B1-7 is statistics-heavy (~80%); pattern may be domain-specific
- 0 items in B1-7 were AGREE-only — every covered item produced an actionable override

## Finding 9 — "Interpretation MCQ" dataset truncation class
0585, 0622, 0858: trailing [ANS] for interpretation-MCQ after Yes/No conclusion, but options absent. Hypothesis: dataset prep dropped MCQ-option text for an entire problem class.

## Finding 10 — LaTeX text-wrap risk for MCQ letters
0413 emitted `\text{A}`; 0622 emitted `\text{Yes}`. Kaggle behavior with `\text{}` wrappers UNVERIFIED — worth empirical probe.

## Finding 11 — Multi-slot undercount is domain-independent (B9 confirmation)
B9 confirms multi-slot undercount across algebra, statistics, trig, and geometry — not just statistics as seen in B1-7. 9 of 22 HIGH items had actionable best-answer overrides, all undercount or arithmetic error. Wolfram query tip: `statistics {data}` works; `mean, median, mode of {data}` often fails.

## Finding 12 — Wolfram modular recurrence syntax confirmed
For linear recurrence mod p: `Mod[LinearRecurrence[{P,-Q},{a0,a1},N][[-1]], p]` works and returns exact result. Used to confirm 181|a(2015) for item 0017 (least odd prime of a_n sequence). Also verified mod 13, 31 ≠ 0.

## Finding 13 — Two-step problems require chained Wolfram queries
Item 0177: solve functional equation first (get f(x)=x/√(1+x²)), then compute volume of rotation. Wolfram confirmed V=π²/6 via `2*Pi * Integrate[y^2/Sqrt[1-y^2], {y, 1/2, Sqrt[3]/2}]`. Shell method along y-axis needed when rotation is around x-axis and region is y-parameterized.

## Finding 14 — Digit-concatenation error (SYSTEMATIC, high-value post-processing target)
Qwen sometimes flattens a correct fraction/radical answer into a concatenated digit string by stripping operators. Confirmed 3 instances:
- 0313: -2√14/15 → "-21414"
- 0411: 392π/45 → "39246"
- 0936: 275/16 → "27517"
**Post-processing lever**: items where best_answer is a long integer whose digits match the digits of a teacher fraction/radical are recoverable. Worth a sweep across all 943.

## Finding 15 — T/F binary-vs-word encoding mismatch
Qwen emits 0/1 (binary) where gold expects False/True (words). Confirmed: 0785, 0896, 0927 (also 0.000/1.000 float variant). Values correct (0=False, 1=True), pure format mismatch. Post-processing should map binary→words for T/F items.

## Finding 16 — best="INVALID"/"answer" = inference failure, not format
Items with best_answer literally "INVALID" or "answer" represent complete inference failures (no parseable output), NOT format issues. Wolfram easily solves these (e.g. 0790 standard-form, 0872 basic limits, 0679 silo radius, 0684 critical z, 0716 R²). Flag all such items for direct Wolfram/teacher override.

## Finding 17 — P-bucket leverage profile (from B9-B13)
- P1 (Qwen-vs-teacher disagree): ~33% INCONCLUSIVE (loaded with competition/OEIS problems where both guessed wrong), but high override yield (~32% actionable) when computable.
- P2 (teacher-split): higher teacher/best agreement, fewer competition problems → better for verification anchoring than override-hunting.
- OEIS algorithm MCQs ("given a(n) definition, compute y_list") are systematically INCONCLUSIVE — Wolfram cannot compute arbitrary OEIS sequences at given indices.

## Finding 18 — P3 bucket validated as the override-rich vein (B15)
P3 (multi-answer computable, ~108 items) yielded 10 actionable undercount overrides in 25 items (40%) vs 0 in P2/B14. Confirms Finding 17: multi-slot undercount is the dominant recoverable failure, and P3 is where it concentrates. **Recommend prioritizing P3 over remaining P2 for override-hunting.**

## Finding 19 — Undercount mode = "drop earlier sub-parts" (B15)
Multi-PART questions (a/b/c) where Qwen answers only the FINAL part: 0027 (eq2 only), 0262 (part c only), 0470 (99% CI only, 4 of 6 slots dropped). Same as Horner (0505) and division (0444) undercounts. Post-processing lever: count sub-part markers (a/b/c, multiple [ANS]) and verify equal answer count. Worst case so far: 0470 dropped 4 of 6 slots.

## Finding 20 — format_flags are noisy; Wolfram still needed
Even within the "undercount-flagged" P3 subset, ~24% (6/25 in B15: 0043,0157,0210,0273,0281,0325) had best ALREADY complete and correct. The undercount/backsolve_disagree flags over-trigger. Independent Wolfram verification is required to separate true undercounts from false flags before applying any automated multi-slot expansion.

## Open questions
- Exact Kaggle string-matching rules (whitespace, `\text{}` wrappers, trailing zeros, `^\circ` vs `°`)
- 0587 multi-select format: comma-sep vs concatenated vs sub-boxes
- 0894 borderline integer: submit both `9` and `10`
- 0715 list-inside-slot ordering: natural enumeration vs sorted
- Whether 0317-style duplicate-option bugs exist elsewhere
- Whether 0585/0622/0858-style interpretation-truncation exists elsewhere
