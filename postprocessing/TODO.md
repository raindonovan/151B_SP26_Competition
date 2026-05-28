# Post-Processing TODO

## Active
- [ ] Multi-slot expander on 51 use_teacher items (undercount_candidates.csv)
- [ ] Generic multi-slot expander (read Qwen reasoning, detect under-counted answers)
- [ ] Fraction/decimal direction fix (7 items from Wolfram B8)
- [ ] Missing prefix/label fix (D=, Quadrant, degree — items 40, 72, 496, 167)

## Confirmed dead
- [x] ~~Trailing-zero strip~~ — PROVEN NEUTRAL (Day 3 Slots 1 vs 2)
- [x] ~~\dfrac vs \frac~~ — Hendrycks auto-normalizes
- [x] ~~\left/\right removal~~ — Hendrycks auto-normalizes
- [x] ~~Whitespace in comma lists~~ — Hendrycks strips all whitespace
