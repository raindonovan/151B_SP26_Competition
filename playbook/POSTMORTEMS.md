# POSTMORTEMS — What we tried and failed

**Created**: 2026-05-28 (Day 4 start)
**Purpose**: Document each failure honestly so we don't repeat. Each entry: what, when, cost, root cause, what we learned, would we try again differently.

---

## P1 — SFT v4 adaptive (REAL submission 0.597 vs base 0.646)

| Field | Value |
|---|---|
| Date | 2026-05-24 |
| What | SFT v4 trained on 3-arm teacher dataset, then adaptive SC sampling at inference (SC=3 confident items, SC=16 hard items) |
| Cost | Real Kaggle submission slot + ~2 days of compute |
| Result | **0.597 Kaggle — REGRESSION of -4.9pp vs base inference 0.646** |
| Root cause | Adapter caused base model degeneration. Training on 3-arm consensus introduced noise. Adaptive SC didn't recover. |
| What we learned | (a) Mixing teacher styles confuses Qwen. (b) Memorization on training items ≠ test-set performance. (c) Adaptive SC can't fix a bad adapter. |
| Would we try again? | Only with: (i) single-teacher style consistency, (ii) held-out test eval before scaling, (iii) smaller curated dataset (~300 items) |

---

## P2 — SFT v5 "20/20 memorization" misleading metric

| Field | Value |
|---|---|
| Date | 2026-05-25 |
| What | Trained v5 on 391-item dataset (14 fixed traces); memo test of 20 training items showed 20/20 consistent at checkpoint-1176 |
| Cost | ~28 min training on H100 + test infrastructure time |
| Result | **20/20 memorization — but on TRAINING items. Real Kaggle: v5 near-break-even with base (~0.646 region).** |
| Root cause | The memo test measured the wrong thing. It confirmed the model could reproduce ITS OWN TRAINING DATA, which any modestly-trained model will do. It said nothing about test-set generalization on the other 552 items. |
| What we learned | (a) Memorization on training items is a tautology, not a signal. (b) We declared v5 "viable" based on a metric that doesn't predict the outcome we care about. (c) Need held-out validation before trusting any SFT result. |
| Would we try again? | Yes BUT: evaluate on held-out items (e.g., 50 random items NOT in training set, scored against teacher consensus) before declaring success. |

---

## P3 — GenSelect PoC with truncated candidates

| Field | Value |
|---|---|
| Date | ~2026-05-26 |
| What | Implemented NVIDIA AIMO-2 GenSelect: feed 8 SC candidates to model as second pass, ask which is best. Tested on full 943. |
| Cost | One inference run (~hours) + analysis time |
| Result | **Selector frequently picked wrong candidate even when correct one was in the pool (e.g., item 0184: 4 of 8 candidates correct, GenSelect picked the wrong one, selector text literally said "all solutions truncated, I can't determine which is best")** |
| Root cause | We truncated each candidate to a tiny window (looked like ~500 chars) when assembling the selector prompt. Selector got cut-off reasoning, couldn't judge. **NOT a Qwen-as-judge failure — an implementation bug.** |
| What we learned | (a) NEVER scale to 943 without a smoke test on 5-10 items first. (b) Truncation budgets in multi-step pipelines need explicit verification. (c) "It ran and produced output" ≠ "It produced sensible output". |
| Would we try again? | Yes, with: (i) smoke test on 5 items showing selector reads full candidates, (ii) explicit token budget per candidate, (iii) verify selector text is reasoning about the math, not about formatting. |

---

## P4 — "OPL +5-12pp" inherited projection

| Field | Value |
|---|---|
| Date | Projection set ~2026-05-26, reality checked 2026-05-28 |
| What | Earlier hypothesis: OPL embedding matching could yield +5-12pp via direct answer overrides |
| Cost | OPL infrastructure built (embeddings, matcher, splice script) — ~1 day |
| Result | **Reality: 39 items with OK-status clean OPL answers (T2-T3 tier). Realistic gain +3-4pp from direct overrides. Layered with teacher consensus could reach +6-8pp but speculative.** |
| Root cause | Earlier projection assumed high parameterized-template solve rate, which didn't materialize. Most OPL matches are parameterized problems requiring our specific values. |
| What we learned | (a) Inherited projections rot — re-verify with actual data before committing strategy to them. (b) OPL is best framed as a CLASSIFICATION/ROUTING tool, not an answer engine. |
| Would we try again? | Yes, but with revised framing: OPL gives us "this question is testing X-type math" signal, which can route to Wolfram or teacher LLMs with better priors. Not a direct answer source for most items. |

---

## P5 — "Wolfram full overrides" projected +3-5pp, realized +0.7pp

| Field | Value |
|---|---|
| Date | 2026-05-26 (Day 2) |
| What | 38 Wolfram HIGH overrides applied to slot1_reformat |
| Cost | ~1 day of Wolfram queries + verification |
| Result | **slot1_wolfram_full_overrides = 0.653 vs slot1_reformat = 0.646. Net gain: +0.7pp.** |
| Root cause | Projection assumed each override = 1 correct flip. Reality: many Wolfram answers were format-equivalent to what Qwen already had (no flip), some flips were wrong (we got 88% hit rate which means 12% were regressions), and the base submission had some items correct that the override changed to wrong. |
| What we learned | (a) Override hit rate is real but not 100%. (b) Projections per-override need to account for: (i) hit rate, (ii) format-equivalence (no net change), (iii) base-already-correct (flip regresses). |
| Would we try again? | Yes — overrides are real Kaggle wins. But projections from now on use (correct flips - regressed items) / 943, not (overrides applied) / 943. |

---

## Patterns across postmortems

1. **We declare victory on metrics that don't predict the outcome we care about** (P2, P3)
2. **We scale to 943 without smoke-testing** (P3, partially P1)
3. **We inherit optimistic projections from earlier hypothesis-mode docs and never re-anchor to reality** (P4, P5)
4. **We don't always document failures in time to learn from them** (this is the first POSTMORTEMS.md file — that's the meta-failure)

## Discipline corrections (locked Day 4)

- **NO SCALE TO 943 WITHOUT 5-ITEM SMOKE TEST** that confirms the output is sensible (not just non-empty)
- **NO METRIC IS TRUSTWORTHY UNTIL VALIDATED ON HELD-OUT ITEMS** (training memorization doesn't count)
- **PROJECTIONS STATE LOWER BOUND FIRST** (e.g., "+3pp realistic, +8pp ambitious-but-stacked" not "+5-12pp")
- **POSTMORTEM WITHIN 24H OF FAILURE** — write to this file before moving on
