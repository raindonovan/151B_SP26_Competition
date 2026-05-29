# Batch10 Findings — 2026-05-29

**Items**: 0214-0437 (25 P1 items)
**Subject mix**: statistics (8), algebra (7), trigonometry (5), geometry (2), number_theory (2), other (1)

## Confidence distribution
- HIGH: 22/25 (88%)
- INCONCLUSIVE: 3/25 (12%)

## Actionable overrides (Wolfram confirms teacher, best wrong)

| ID | Wolfram answer | Best (wrong) | Issue |
|----|---------------|--------------|-------|
| 0214 | 11, F, 10, T | 11,F,7,T | slot3: floor(√107)=10 not highest-prime=7 |
| 0243 | 0.8925, 0.2150 | 1 | catastrophic — 2-slot p-value answer collapsed to "1" |
| 0269 | 1.789, 0.3198, B | 1.717,0.3198,B | t_crit wrong (1.717 vs Wolfram 1.789 at α=0.04, df=47) |
| 0271 | -4, 0, 4 | 4 | severe undercount — missing -4 and 0 solutions |
| 0287 | 212, 136 | 136 | undercount — missing part-a n=212 |
| 0301 | 0.878, 57.2 | 0.877, 57.2 | slot1 rounding: 0.87761→0.878 (3 sf), not 0.877 |
| 0313 | -2*sqrt(14)/15 | -21414 | digit-concat error: Qwen output "2√14" as "2,1,4" = "214" |
| 0372 | 0.51 | 1 | wrong — 1.96*20.58/√6377=0.505≈0.51, not 1 |
| 0411 | 392*pi/45 | 39246 | completely wrong — 27.37 units, not 39246 |
| 0437 | 76.37, 79.63 | 79.63 | undercount — only upper bound given |

**10 actionable overrides** — all HIGH confidence.

## Teacher/best equivalences (no action needed)
- 0240: teacher/best agree (same values, best adds units)
- 0296, 0319, 0322, 0345, 0369, 0382, 0397, 0404, 0421: all teacher/best equivalent forms

## INCONCLUSIVE items
- **0255**: OEIS tiling sequence (4×2n L-tetrominoes) for n=15..24. Not Wolfram-computable.
- **0347**: 9×9 tiling with 1×3 tiles, N mod 1000. Hard combinatorics.
- **0386**: Geometric/combinatorics problem. teacher=3, best=5.

## New findings

### Finding B10-1 — 0313 digit-concat error pattern
Qwen output "-2√14/15" but tokenized as "-21414" (treating "2", "1", "4", "1", "4" as digits). This is a tokenization/display artifact, not arithmetic error. Flag: any item where best_answer looks like a number with spurious digits matching LaTeX output of teacher.

### Finding B10-2 — 0411 similar wrong-magnitude error
Arc length 392π/45 ≈ 27.37 but best=39246. May be unit conversion error (inches?): 27.37 ft * 12 * 12? Or misread: "39.246..." with decimal lost? Either way, completely wrong.

### Finding B10-3 — α=0.04 critical t distinct from common tables
Item 0269: t_crit(df=47, α=0.04) = 1.789, not 1.717. Best used a common α=0.05 value (~1.684) or a different df. Wolfram InverseCDF confirmed 1.78937.
