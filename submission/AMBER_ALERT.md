# 🟡 AMBER ALERT — FOUR CONCERNS THAT AFFECT HOW WE INTERPRET SUBMISSIONS

**Raised:** 2026-05-28 (Day 6, during 25_08 submission build).
**Severity:** AMBER (below RED_ALERT_LB_SUBSET.md, above routine findings).
**Status:** UNRESOLVED. Read before interpreting any submission score or building any new override CSV.
**Read in conjunction with:** `submission/RED_ALERT_LB_SUBSET.md` (the 283-slice issue).

---

## TL;DR — four things we got wrong or don't know

1. **All our EV calculations assume uniform random slice sampling.** We multiply `items_changed × 0.30` to estimate slice items affected. This is the no-information prior. We have **no clean evidence** that the slice is uniform OR that it deviates in any specific direction. The math is "best guess in absence of signal", not "calibrated to known slice properties".

2. **The "slice oversamples hard items" claim that briefly circulated is NOT supported by clean evidence.** It was inferred from the back-solve sanity check (predicted-on-943 > actual-on-slice for high-scoring subs). But that signal is contaminated by RED_ALERT itself — the Bayesian back-solve treats each submission's score as a Binomial(943, p) likelihood when it's really Binomial(283, p), which inflates `predicted-on-943` for high scorers. The +0.12 gap (Run14b V3-filtered's predicted 0.766 vs actual 0.646) can be **fully explained by Bayesian contamination, requiring zero slice bias**. Do not use back-solve summary diffs as evidence of slice composition.

3. **The "append a final `\boxed{}` to override" mechanism is BROKEN for MCQ items.** Per `grading/GRADER_SPEC.md` §3, the MCQ grader extracts the **FIRST** `\boxed{LETTER}` via `re.search`, with fallback to last bare capital. Our standard override mechanism (used in `25_08/slot3_mcq_teacher_override.csv` and `25_08/slot5_combined_all.csv`) appends a new `\boxed{}` at the end of the response, which is the LAST box, not the first. For MCQ items, the original `\boxed{LETTER}` already in the response wins, and our override is silently ignored. Slot 3's 26 overrides and the 26 MCQ-portion of Slot 5's 186 overrides may be no-ops. **Check past submissions for this same bug** — if we ever used append-to-end on MCQ items in prior submissions, those overrides were also silently dropped, which means scores attributed to "Wolfram MED won 1 slice item" or similar may need re-examination.

4. **All override evidence sources are PROXIES, not ground truth.** Teacher consensus (closed-source LLMs sharing training biases), web-search GOLD labels (variable source quality: Putnam = strong; Gauthmath/homework.study = weak), Wolfram (mathematical but only for items it can compute), and back-solve posterior (contaminated per RED_ALERT). We treat "3+ teachers agree" or "search status=GOLD" as if it were verified gold. It isn't. Our high-scoring submissions (0.692) may be RIGHT on items where teachers DISAGREE with us — we have no way to verify that with the slice hidden.

---

## What this means for ongoing decisions

### When designing new override CSVs:
- Default to the uniform-random EV math unless someone produces clean slice-composition evidence (not back-solve summary diffs).
- For MCQ overrides, **do not use append-to-end mechanism**. Either prepend `\boxed{LETTER}` to the response, or rewrite the response entirely to just be `\boxed{LETTER}`.
- Treat each evidence source's "correct answer" as a probability, not a fact. Apply confidence priors: Wolfram HIGH > Wolfram MED ≈ Putnam-sourced search > teacher-3-of-4 > teacher-2-of-4 > Gauthmath search > computed-by-agent search > back-solve.

### When interpreting submission scores:
- The slice score is a noisy point estimate with ±~5pp noise.
- A delta of <0.005 between two submissions is within noise — do not draw strong conclusions.
- A delta of +0.005 to +0.020 may be real but cannot be attributed to specific items without further probes.
- A delta of >+0.020 from a known small change set is interpretable (e.g., adding 30 overrides and gaining 10pp means most overrides landed on slice items and were correct).

### When choosing final 2 picks:
- Prefer submissions where overrides are grounded in highest-quality evidence (Wolfram HIGH, Putnam sources, multi-method agreement).
- Avoid stacks that piled together weak proxies (the same logic as RED_ALERT's "shake-down risk on the 660-item private leaderboard").

---

## What we DO NOT know (and should not pretend to know)

- Whether the slice over- or under-samples MCQ vs free-form items.
- Whether the slice over- or under-samples hard vs easy items.
- Whether specific item IDs are in slice (probabilistic guesses only, with weak signal).
- Whether the order of slice composition was random-at-setup or stratified.

The right posture is: **uniform prior, accept that EV is wide-banded, prefer broadly-grounded submissions, run differential probes when slice info would be decision-critical.**

---

## What we DO know

- The slice is fixed at competition setup. Same 283 items grade every submission.
- The 283 ≠ leaderboard rank. Final ranking is on the full 943, with the slice being only the public-LB feedback channel.
- Our format-fix knowledge (Hendrycks `is_equiv` source-code level) is CLEAN. Not contaminated by slice issues.
- Our inference outputs (V0-V4, run09, run14b, SC samples) are CLEAN — real model outputs, not score-derived.

---

## Cross-refs

- `submission/RED_ALERT_LB_SUBSET.md` — the foundational 283-slice contamination of back-solve infrastructure
- `grading/GRADER_SPEC.md` — the MCQ-first-box vs free-form-last-box distinction (§3)
- `submission/25_08/README.md` — current submission round affected by concerns #1, #3, #4
- `data/backsolve_summary.txt` — source of the contaminated signal in concern #2

---

## Date / origin

Concerns surfaced 2026-05-28 in the 25_08 submission-build conversation between Rain and claude_submissions. Documented after Rain explicitly asked for amber-level visibility on the unresolved issues.
