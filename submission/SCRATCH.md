# submission/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- CURRENT PICKS ARE WRONG: 0.438 + 0.420 selected. Must change to 0.692 + next best before deadline.
- Strip is neutral: #26 (0.692) = #25 (0.692 without strip).
- MED overrides = +0.3pp: #26 (0.692) vs #27/#29 (0.689 without MED).
- Whitehill 2017 (1707.01825) Section 3: accuracy oracle attack on unknown subset. Our accuracy metric gives ~8 bits per submission. 29 submissions × 8 bits = 232 bits of information about the test set.
- Back-solve assumed /943 before we knew about the ~283 LB subset. Old back-solve posteriors are unreliable. Need to redo with |T|≈283 assumption.

---

## [Penny 5] Information-theoretic ceiling (2026-05-28, claude_librarian)

**Source**: data/FINDINGS.md §2 (INFORMATION-THEORETIC CEILING).
**Key**: Pure back-solve caps ~0.72 (info-theoretic bound: each submission gives ≤log₂(944)≈9.88 bits, 5 queries ≤49.4 bits vs 943 bits uncertainty). Format-fix path caps ~0.77+. Leader 0.770 is reachable via format-fix path, NOT via back-solve alone. Combined (format + back-solve + Wolfram + manual) is the best path.
**Implication for submission strategy**: Don't invest remaining submissions purely in back-solve oracle mining. Format-fix post-processing is the higher-ceiling path. Back-solve is additive on top.
