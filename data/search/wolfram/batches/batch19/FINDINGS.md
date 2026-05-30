# Batch19 Findings — 2026-05-29

**Items**: first 25 of the "computable=YES" leftovers (unflagged, mostly MCQ math).
**Subject mix**: calculus (6), algebra (5), statistics (6), linear_algebra (2), trigonometry (2), number_theory (3), geometry (1)

## Outcome
- HIGH: 11 (clean verified value)
- MED: 7 (value computed but messy/parametric, or conceptual MCQ)
- INCONCLUSIVE: 7 (competition / can't verify)
- Of the HIGH/MED: 6 confirmed **matches** with the sheet; 0 clear discrepancies.

## Matches (sheet confirmed correct)
- 0014: t=ln35/ln3
- 0048: -2≈ln(0.135) (option C)
- 0074: paired-diff 94.6% CI (12.36, 25.04) ≈ sheet (12.32, 25.08)
- 0128: (y-3)/(y+3)
- 0130: r^42
- 0131: p-value 0.1084

## Values verified for MCQ items (computed the value; sheet stores a letter)
| ID | Verified value | Sheet letter |
|----|----------------|--------------|
| 0080 | √3/12 | G |
| 0094 | 4/3 (area) | C |
| 0109 | eigenvalues (a)4,2 (b)5,1,1 (c)3,-1,1 | B |
| 0123 | primitive x²cos y + y²cos x | G |
| 0147 | volume 25π/3 | I |
| 0013 | antiderivative (sec powers + ln\|tan\|) | C |
| 0114 | sin(2ⁿ⁺¹a)/(2ⁿ⁺¹ sin a) | D |

## Inconclusive (7)
0007 (snakes), 0053 (bird maze), 0073 (joint pdf transform), 0092 (parametric integral, no number), 0095 (triangle), 0098 (card-shuffle order), 0148 (compound Poisson).

## Notes
- This is the start of the verification-only phase (no flags). As expected: lots of matches, no discrepancies so far.
- **MCQ value-vs-letter gap:** for ~7 items I verified the exact VALUE but the sheet stores an MCQ letter. Confirming the letter needs reading the full option list per item — deferred. Per the operating manual, nailing the value is the priority; letter-mapping is a downstream step.
- Calculus integrals (0013, 0146) and approximation-theory (0150) are computable but produce messy closed forms that are tedious to match to an option letter.
