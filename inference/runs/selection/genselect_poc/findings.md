# GenSelect PoC — Findings

## Headline

**The PoC failed because we scaled to 943 items without a smoke test. Bug: candidate inputs were truncated, selector couldn't judge.**

## The bug

Selector prompt assembled 8 candidates per item. Each candidate appears to have been truncated to a small window (~500 chars based on the response text). Selector got cut-off reasoning, picked blindly.

**Direct evidence (item 0184 from `genselect_poc_r2_results.json`):**
- 4 of 8 candidates were correct (correct_sample_idxs = [2, 3, 4, 7])
- Selector text literally says: *"Solution 0: [truncated] - It starts by trying to parse the problem but gets cut off. ... All solutions are truncated, so I don't have the full content to analyze."*
- Selector picked WRONG answer (A) when correct (J) was in the pool
- `picked_correct: false`

## What we learned

1. **Never scale to 943 without a 5-item smoke test** that confirms the output is sensible (not just non-empty). This is now a discipline rule.
2. **Truncation budgets in multi-step pipelines need explicit verification.** "It ran and produced output" ≠ "It produced sensible output."
3. **"Qwen is bad at self-verification" was an UNVALIDATED conclusion.** The PoC failure was an implementation bug (truncated input), not a model capability ceiling. The right test of "is Qwen good at self-verification?" requires re-running GenSelect with full-length candidate inputs first.

## What we DON'T know yet

- Rate at which correct answer was IN the pool of 8 candidates (= oracle@8 ceiling). This is the cap on what better selection can recover.
- Rate at which selector was confused by truncation specifically (= recoverable by fixing input format).
- Whether Qwen-as-judge has fundamental issues beyond truncation.

These three are answerable from existing data — needs a deeper pass on `genselect_poc_r2_results.json` + cross-reference with run14b SC samples.

## Pending analysis (P0 for next session)

1. Count items where correct answer was in the 8-candidate pool but selector picked wrong
2. Of those, count how many had "truncation"-mentioning selector text
3. Compute oracle@8 rate from raw run14b SC data (different question, but the upper bound)

## Rules constraint check

GenSelect uses Qwen judging its own outputs = single model self-consistency = **ALLOWED under rules.** Not affected by the TIR/PRM exclusions.
