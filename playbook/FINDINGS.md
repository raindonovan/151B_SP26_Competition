# PLAYBOOK FINDINGS

**Updated**: 2026-05-28 (Day 4 start)
**Note**: Findings specific to the 0.85 push. Competition-wide findings remain in `docs/FINDINGS.md`.

## F1 — Total gain from all post-processing/normalization/overrides combined: +4.9pp

From base inference 0.643 (slot1_minimal_norm) to current best 0.692 (slot1/2 kitchen-sink, Day 3) = +4.9pp gross.

Breakdown:
- Minimal normalizer: +0.4pp
- Reformat (multi-answer): +0.3pp
- Wolfram full overrides (~38 items): +0.7pp
- Day 3 kitchen sink (~71 more overrides + Hendrycks transforms): +3.9pp
- TOTAL: +4.9pp over 3 days

**Implication**: incremental gains from format tricks are SMALL. We've extracted most of the easy juice. The leader at 0.85 has a structural advantage we haven't replicated. To close the gap, we need a single lever worth +10pp+, not five more format tweaks worth +0.3pp each.

## F2 — OPL is answer-sheet gold for ~30-40 items, NOT training gold

OPL match analysis (results/opl_match/candidates.csv, 2057 rows):
- 39 items have OK-status (clean concrete answer extracted from OPL .pg file)
- All 39 disagree with current Qwen submission
- 1 item has HIGH-bucket similarity match (id=15, sim=0.9055, OPL says "0")
- 844 items match parameterized templates — would require solving with our specific values (heavy lift)

**Conclusion**: OPL is best understood as a SOURCE OF ANSWER-SHEET CANDIDATES (T2-T3 tier), not as training data. The earlier "+5-12pp" projection was inherited speculation; actual realized value is **+3-4pp** if all 39 OK items are correctly overridden.

**Secondary value**: OPL provides a CLASSIFICATION signal (what kind of math is this question testing?) which CAN improve routing to Wolfram or to teacher LLMs. But that secondary value is not directly scorable.

## F3 — The "memorization 20/20" SFT v5 test was measuring the wrong thing

`scripts/memo_test_v5.py` tested whether v5 adapter could reproduce its TRAINING items. It got 20/20 on items that were IN the 391-item training set. This is MEMORIZATION, not generalization.

The v5 adapter on REAL inference (the 943-item private set, items the model has never seen) is essentially break-even with base inference. The 20/20 score told us nothing about test-set performance.

**Implication**: don't trust "memorization confirms training worked" as evidence of model improvement. Need to evaluate on held-out items.

## F4 — Genuine arithmetic errors vs format errors: roughly 21% vs 79% (B1-7 Wolfram audit)

From Wolfram findings: 79% of items Qwen gets "wrong" are format/multi-slot issues with correct math. 21% are genuine arithmetic errors.

**Implication**:
- Format-fix levers cap at +21-25pp (the 79% pool)
- We've extracted +5pp of that already
- Remaining ceiling: +15-20pp from format alone IF we crack multi-slot expansion
- TIR addresses the 21% genuine-arithmetic items (and produces cleaner format on the rest)

## F5 — Submissions are SCARCE now (updated Day 3)

Earlier framing of "non-scarce" is dead. 5 days × 3/day = 15 submissions remaining, each must test a deliberate hypothesis. At deadline: 2 final picks.
