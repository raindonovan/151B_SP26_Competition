# Batch09 Findings — 2026-05-29

**Items**: 0000, 0002, 0004, 0016, 0017, 0020, 0024, 0025, 0029, 0032, 0049, 0058, 0077, 0104, 0105, 0113, 0135, 0136, 0154, 0171, 0177, 0188, 0196, 0201, 0208
**Subject mix**: statistics (9), algebra (5), trig (5), geometry (4), number_theory (2), calculus (1), other (1)

## Confidence distribution
- HIGH: 21/25 (84%)
- MED: 1/25 (4%)
- INCONCLUSIVE: 3/25 (12%)

## Actionable overrides (Wolfram disagrees with best, teacher is correct)

| ID | Wolfram | Best (wrong) | Issue |
|----|---------|--------------|-------|
| 0000 | 4, 16 | 16 | multi-slot undercount (2→1) |
| 0020 | 228, 229, 250 | 229 | multi-slot undercount (3→1), missing mean and mode |
| 0024 | 1 | 2 | arithmetic error (residual calc) |
| 0025 | 8/63, 2/21, 11/63, 17/63, 13/63, 8/63, 8, 14, 25, 42, 55, 63 | 8,14,25,42,55,63 | multi-slot undercount (12→6), missing entire relative-freq section |
| 0029 | 38.2 | 39 | wrong rounding (38.24% rounded to 38.2, not 39) |
| 0135 | 3/5 | 36 | catastrophic arithmetic error (8x+2=3x+5 → x=3/5, not 36) |
| 0171 | 20 | 21 | off-by-one area calculation (4×5=20, not 21) |
| 0188 | 60, 60, 60 | 61 | wrong mean + undercount (3→1 slots) |
| 0196 | 14.7447, 10.3244, 35 | 15 | severe undercount (3→1) + arithmetic error |

**9 actionable overrides** — all HIGH confidence.

## Teacher/best equivalences (no action needed)
- 0002: best=-1.461 vs teacher=-1.46 (same, rounding)
- 0004: best=decimals, teacher=exact forms — EQUIVALENT
- 0032: best=decimals, teacher=exact — EQUIVALENT
- 0049: best=0.01433 vs teacher=0.0143 — AGREE
- 0104: best=4.166, teacher=2387π/1800 — EQUIVALENT
- 0105: best=9.114, teacher=9.11 — AGREE
- 0113: best=expanded, teacher=factored — EQUIVALENT
- 0154: both=18.75 — AGREE
- 0201: best=(5t+8)², teacher=(5t+8)(5t+8) — EQUIVALENT
- 0208: best=16.2, teacher=81/5 — EQUIVALENT

## INCONCLUSIVE items
- **0016** (game on 1001-gon): game theory, not Wolfram-computable. Teacher=501, best=858. No independent verification.
- **0058** (functional equation): competition-level problem. Teacher=31, best=0. No independent verification.
- **0077** (study design MCQ): conceptual stats question. Teacher=C,D,A (3 slots), best=A (undercount). Logically: time-of-day confound is the issue, but MCQ letters not verifiable.

## New findings

### Finding B9-1 — 0177 requires two-step solve (functional equation → volume)
Item 0177 is a 2-part problem: first solve a functional equation (2f(x)+x²f(1/x)=...) to get f(x)=x/√(1+x²), then compute the volume of rotation. Wolfram confirmed V=π²/6. Teacher=H (MCQ), Qwen=I. The value π²/6 is definitively correct — MCQ letter needs manual lookup.

### Finding B9-2 — 0017 requires modular computation, not direct solve
Item 0017 (sequence a_n=4a_{n-1}-a_{n-2}, find least odd prime of a_{2015}) needed Wolfram's LinearRecurrence mod capability. Confirmed: 181|a(2015) and mod 3,5,7,11,13,31 all ≠ 0. Value=181. Teacher=C, Qwen=E. MCQ letter uncertain.

### Finding B9-3 — 0029 rounding trap
38.24% rounds to 38.2 (1 dp), NOT 39. Best answer of 39 reflects a floor/ceiling error. Teacher answer of 38.2 is correct.

### Finding B9-4 — Multi-slot undercount extends across all subjects (not just statistics)
B1-7 showed 79% undercount in statistics-heavy batch. B9 shows undercount in algebra (0000), statistics (0020, 0025, 0188, 0196), and mixed (0025). Pattern is domain-independent.

## Items needing query reformulation
- 0032: first attempt "distance from (4,-3) to (-6,-4)" failed → used direct formula
- 0188: "mean, median, mode of {...}" failed → used "statistics {...}" format
- 0004: natural-language terminal-point query failed → computed -7/sqrt(149) directly
- 0049: "P(Z>=2.189) normal distribution" returned symbolic → used CDF[NormalDistribution[0,1],2.189]

## Worth promoting to root FINDINGS.md
- B9-4 (multi-slot undercount is domain-independent) — strengthens Finding 8
- Wolfram query format: `statistics {data}` works; `mean, median, mode of {data}` often fails
- For modular computation of linear recurrences: `Mod[LinearRecurrence[...][[-1]], p]` works well
