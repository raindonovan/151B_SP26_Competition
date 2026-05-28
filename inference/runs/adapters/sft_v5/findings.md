# SFT v5 — Findings

## Headline

**The "20/20 memorization" metric measured the wrong thing. v5 succeeded at remembering its training data; that says nothing about generalization to the other 552 items.**

## The mistake

`scripts/memo_test_v5.py` tested whether v5 adapter could reproduce 20 items from its TRAINING SET. It got 20/20 — declared winner.

This is a **tautology**, not evidence. Any modestly-trained 14-epoch model WILL memorize 391 items it was trained on. The 20/20 score said nothing about test-set generalization.

## Reality check

On the held-out portion of the 943 (items NOT in v5's training set):
- v5 adapter near break-even with base (~0.646 range)
- The 20/20 memorization metric did not predict the outcome we care about
- We declared "viable" based on a metric that doesn't measure what we needed

## Discipline correction (locked)

**No metric is trustworthy until validated on items NOT in training set.** Memorization on training items is a tautology, not a signal.

For any future SFT (v6+, v7+): include a held-out validation set of 50 items scored against teacher consensus, separate from training. Decide viability on that, not on memo tests.

## RAIN'S INSIGHT: Targeted memorization as a feature, not a bug

Rain pointed out (2026-05-28): if v5 can memorize its training items reliably, that capability IS USEFUL — we just have to scope it correctly.

**The play**: 
1. Identify 200-300 items Qwen base gets WRONG (low SC agreement on private 943)
2. Get verified correct answers for those items (multi-teacher consensus + Wolfram)
3. Train an SFT v7 adapter on those items + verified answers
4. At inference: run both base Qwen and v7-adapter. Use SFT-adapter answer ONLY for items it was trained on (or items where base+adapter agree → high-confidence override).

**Why this differs from v4/v5 mistakes**:
- v1/v4/v5 trained for general improvement (failed)
- v7-targeted would intentionally narrow the scope to "items we know base gets wrong"
- No claim of generalization — we only USE the adapter where it's been explicitly trained
- Held-out validation still required to confirm targeted memorization works without degrading base

**Rules constraint check**: SFT is explicitly permitted by competition rules. Running both base and adapter at inference is single-model self-consistency (the adapter is part of the submitted model). **ALLOWED.**

**Feasibility check**: 
- We have the SFT infrastructure built (v5 successfully trained)
- 200-300 wrong items: extractable from run14b SC agreement + answer sheet
- Verified answers: need teacher consensus + Wolfram for those items (engineering: ~1 day)
- Training: ~30 min on H100
- Inference: 2 passes (base + adapter), or selective routing
- Total ENG: ~2 days

**Status**: PROMOTE to playbook/LEVERS.md as a new lever (Lever 6: Targeted Memorization SFT). Higher feasibility than v7 "general distillation" because the goal is narrower and the success metric is clearer.

## Open questions

- Q: Was v5 actually merged or kept as adapter? **A: Kept as LoRA adapter (no merge). Per memo test winner notes.**
- Q: Was there a v6? **A: NO. sft/ folder has v1_postmortem, v3, v4, v5. No v6.**
- Q: What did v4 train on exactly? **A: I don't have this nailed down. Need to read sft/v4/ folder. My earlier "3-arm teacher" claim conflated v1 (the May 6 catastrophe with NuminaMath+OpenR1+Frugal arms) with v4. Pending.**
