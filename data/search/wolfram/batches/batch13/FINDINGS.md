# Batch13 Findings — 2026-05-29

**Items**: 0781-0936 (P1) + 0010-0045 (P2 start). 18 P1 + 7 P2.
**Subject mix**: algebra (7), statistics (5), trigonometry (3), geometry (3), linear_algebra (3), calculus (2), number_theory (1), other (1)

## Confidence distribution
- HIGH: 18/25 (72%)
- MED: 1/25 (4%)
- INCONCLUSIVE: 6/25 (24%)

## Actionable overrides (Wolfram confirms teacher, best wrong)

| ID | Wolfram answer | Best (wrong) | Issue |
|----|---------------|--------------|-------|
| 0790 | -20x²+45x-25=0 | INVALID | inference failure — standard form expansion |
| 0794 | 4.47, 4 | 5 | wrong — mean=4.47, median=4 (best=5 for both?) |
| 0834 | π/4, 3π/2, -19π/6 | 5 | severe undercount + wrong (3-slot radian conversion) |
| 0836 | 2025 | 15 | wrong — min chords = 2025 |
| 0872 | infinity, 0 | INVALID | inference failure — basic limits |
| 0936 | 275/16 | 27517 | digit-concat error (275/16 → "27517") |

**6 actionable overrides**.

## Teacher/best equivalences
- 0781, 0818, 0830, 0851, 0880, 0916: teacher/best agree (exact vs decimal)
- 0785, 0896, 0927: T/F questions — best uses 0/1 binary, teacher uses words; semantically agree
- 0030, 0042, 0044: teacher/best agree
- 0010, 0022, 0033, 0045: teacher AND best already agree (no disagreement to resolve)

## INCONCLUSIVE items (6)
- **0801**: projective space linear maps (competition)
- **0887**: fuzzy logic min/max equation
- **0904**: fuzzy relation matrix composition
- **0022, 0033, 0045**: teacher/best already agree but not Wolfram-verifiable (polyhedron, geometry, OEIS)

## New findings

### Finding B13-1 — Digit-concatenation error confirmed as recurring pattern (3rd instance)
- 0313: -2√14/15 → "-21414"
- 0411: 392π/45 → "39246"
- 0936: 275/16 → "27517"
All three: Qwen's correct fractional/radical answer rendered as concatenated digits. This is a SYSTEMATIC failure where the LaTeX/symbolic answer is being flattened into a digit string by stripping operators. **High-value post-processing target**: items where best_answer is a long integer that matches the digits of teacher's fraction/radical.

### Finding B13-2 — T/F multi-slot: binary vs word encoding
Items 0785, 0896, 0927: Qwen emits 0/1 (binary) where the expected format is False/True (words). The VALUES are correct (0=False, 1=True). Pure format mismatch — post-processing should map binary→words for these. This is distinct from undercount.

### Finding B13-3 — P2 items (teacher-split) have higher agreement rate
7 P2 items (0010,0022,0030,0033,0042,0044,0045): most have teacher AND best already agreeing. P2 bucket is genuinely lower-leverage than P1 for finding overrides, but higher-confidence for verification (fewer competition problems). Recommend continuing P2/P3 for verification anchoring rather than override-hunting.

### Finding B13-4 — "INVALID" best_answer = inference failure, not format
Items 0790, 0872: best="INVALID" means Qwen produced no parseable answer. These are NOT format issues — they're complete inference failures. Wolfram easily solved both (standard-form expansion, basic limits). Any item with best="INVALID" or best="answer" should be flagged for direct Wolfram/teacher override.
