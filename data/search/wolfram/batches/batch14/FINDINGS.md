# Batch14 Findings — 2026-05-29

**Items**: 0054-0427 (first full P2 batch — teacher-split items)
**Subject mix**: number_theory (9), algebra (5), calculus (4), trigonometry (2), geometry (2), linear_algebra (1), statistics (2)

## Confidence distribution
- HIGH: 12/25 (48%) — Wolfram independently confirmed
- MED: 13/25 (52%) — teacher+best consensus, not independently Wolfram-verifiable (competition/OEIS)
- INCONCLUSIVE: 0/25

## Key structural difference from P1 batches
**ALL 25 items had teacher == best already agreeing.** This is the defining feature of the P2 bucket: these are items where teachers split (2/3 majority) but the best_answer and the teacher consensus still landed on the same value. There are NO discrepancies in this batch — the value is already correct in the sheet.

P2's role is therefore **verification anchoring**, not finding discrepancies:
- HIGH items: Wolfram provides independent 3rd confirmation → near-certain gold
- MED items: teacher+best agree but Wolfram can't verify (competition) → strong but not independent

## Wolfram-confirmed values (HIGH)
| ID | Confirmed value |
|----|----------------|
| 0069 | ∫₀^π x sin²x/(1+sinx) dx = π(4-π)/2 ≈ 1.3484 |
| 0075 | x > 21250 (Plan A vs B commission) |
| 0108 | A=72, B=12x (double-angle) |
| 0111 | 8x³ (radical simplification) |
| 0176 | w=(p-6k-m)/8 |
| 0211 | least odd prime of q₂₅₅ = 181 (same recurrence family as 0017, 0606) |
| 0238 | partial fractions: f=-61, g=61, h=62 |
| 0299 | wedding mean=18805.7, CI conclusion=no |
| 0306 | lim = 1 |
| 0362 | (6x-5y)(6x+5y) |
| 0367 | 60.3°, 46.3°, 53.3° (inverse trig) |
| 0389 | (x²+5x+5)²-1 (perfect-square form) |

## MED items (teacher+best agree, competition/OEIS — not Wolfram-verifiable)
0054, 0088, 0110, 0152, 0164, 0248, 0253, 0274, 0285, 0308, 0339, 0383, 0427

## New findings

### Finding B14-1 — P2 bucket has ZERO discrepancies
Confirms Finding 17: P2 (teacher-split) items where best already matches teacher consensus need no correction. The split was resolved correctly in sheet construction. P2 is pure verification value.

### Finding B14-2 — Recurrence family a_n=4a_{n-1}-a_{n-2} appears 3× with answer 181
Items 0017 (a₂₀₁₅), 0606 (y₂₅), 0211 (q₂₅₅) all use this recurrence and all have least-odd-prime-factor = 181. The Pisano-like period of this recurrence mod 181 must divide a common factor of indices 2015, 25, 255. Worth checking if MORE items use this exact recurrence (likely a dataset template).

### Finding B14-3 — MED confidence convention for competition consensus
For competition/OEIS items where teacher+best agree but Wolfram cannot independently compute, recording as MED (consensus-backed, not independently verified) rather than INCONCLUSIVE. This distinguishes "Wolfram failed but we have other evidence" from "no evidence at all."
