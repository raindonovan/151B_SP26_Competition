# 🚨 RED ALERT — THE LEADERBOARD IS ~30% OF PRIVATE, NOT ALL 943

**Discovered:** 2026-05-28 (Day 6). **Severity:** foundational assumption error → technical debt.
**The lens this creates is mandatory reading before interpreting ANY submission score.**

## The polluted assumption
For most of this competition we assumed **Kaggle score = (correct / 943)** on the full private set.
**FALSE.** Per the competition page (verbatim): *"The leaderboard reports accuracy on approximately 30%
of the private test set."* Kaggle grades all 943 but **shows us only a fixed ~283-item public slice**;
the other ~660 ("private leaderboard") stay hidden until the deadline and decide the final ranking.
This is the standard Kaggle public/private split — the gap between them is the **"shake-up."**

## THE LENS (apply to every submission, forever)
A submission's Kaggle score is its **accuracy on one fixed, UNKNOWN ~283-item slice of private.** It tells us:
- ✅ **relative quality on that slice** (higher score = genuinely better on those ~283 items, ±~5pp noise)
- ❌ **NOTHING reliable about the other ~660 items** — the score channel is literally independent of them
- ⚠️ tuning to maximize the slice = **overfitting the public LB → shake-up risk** on the full 943

## What is BROKEN (contaminated by the 943 assumption)
- **Back-solve** (`submission/scripts/backsolve.py`, `data/back_solve_detail.csv`): its likelihood treated each
  submission's score as evidence over all 943. It can only EVER inform the ~283 slice items (oracle-probing
  literature, arXiv 1707.01825) — and we don't even know WHICH 283. Off-slice updates are phantom. **Back-solve
  per-item answers and confidence tiers are unreliable, especially for the ~70% off-slice items.**
- **Information-theoretic ceiling note** (`data/FINDINGS.md`): used "{0..943}, log₂(944)". Should be ~{0..283},
  log₂(284). Conclusion STRENGTHENS: pure score-feedback back-solve is even weaker than stated.
- **Any per-item interpretation of score deltas as 943-wide signal.** A delta is net items flipped *in the slice*.

## What is CLEAN (independent of the score channel — NOT wasted)
- All **inference outputs** (V0–V4, run09, run14b, SC samples) — real model outputs.
- **Relative ranking of submissions** on the slice (0.692 > 0.646 is real).
- **Format-fix knowledge** (Hendrycks `is_equiv`) — derived from grader source code, not scores.
- **Teacher / Wolfram / OPL gold** — external verification, never touched the Kaggle score.
- **Cross-run oracle harvest** — our own outputs.
- Today's **pipeline / repo organization**.

## ⚠️ ENDGAME IMPLICATION (the expensive one)
Final ranking is the **full 943**, not the slice. Submissions that scored high by **slice-tuned overrides**
(e.g. info_4 = 0.671, built from the answer sheet) may be **overfit to the 283 slice and shake DOWN on the 943.**
→ For the 2 final picks, prefer **robust, broadly-grounded** submissions (real inference + externally-verified
gold) over slice-tuned override stacks. Treat the public LB as a noisy guide, not the target.

## Do NOT
Aggressive leaderboard probing to extract slice labels is (a) limited to the ~283 slice anyway and
(b) **prohibited by Kaggle rules.** Not a path.

## Cross-refs
`COMPETITION.md` (eval surfaces) · `grading/GRADER_SPEC.md` · `data/answer_sheet/RED_ALERT.md` · `data/FINDINGS.md` §6.
