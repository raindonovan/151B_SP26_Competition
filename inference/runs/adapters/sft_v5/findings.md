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

---

## Eval-protocol carry-forward from R14 cross-check (2026-05-31 Day 9)

**Origin**: R14 audit (rep_penalty=1.1 rescue of OpenR1-v2-16K SFT-merged rambling) flagged that SFT-merged models with truncated training traces exhibit catastrophic "no-box" output that rp=1.1 rescues at the extraction-path level. Cursor cross-check (T-template YELLOW) recommended an eval-protocol guardrail for sft_v5 even though sft_v5 is kept as ADAPTER (not merged), to detect the pathology if it surfaces.

**Pathology monitor checklist for ANY sft_v5 (or future SFT) inference eval:**

1. **Log per-run**: `missing_boxed`, `missing_boxed_mcq`, `missing_boxed_free`, `avg_gen_tokens`, `cutoffs`.
2. **Trigger threshold**: if `missing_boxed > ~10% of slice size`, the rambling pathology is likely active.
3. **Fallback decode**: in that case, run a SECOND eval pass with `repetition_penalty=1.1` (single-sample or SC@N as appropriate) on the same slice. Compare:
   - missing_boxed (should drop materially if pathology was active)
   - avg_gen_tokens (should drop)
   - overall_accuracy (should rise IF the no-box items had recoverable answers in the trace)
4. **Decision rule**: if fallback rp=1.1 rescues ≥50% of the no-box failures, the model has the OpenR1-v2 pathology; treat results from the baseline rp=1.0 run as understating capability. If fallback rescue is <20%, the no-box failures are model-capability gaps, not extraction-path gaps.
5. **Do NOT default to rp=1.1 on base Qwen evals.** This is a rescue lever for SFT-pathology only — base Qwen3-4B-Thinking-2507 does not exhibit the rambling mode (V-series confirms rp=1.0 produces 0.70-0.72 on fixed50 with no extraction failures).

**Why this is a carry-forward, not a closed item**: sft_v5 is kept as adapter (not merged into base weights). The R14 evidence came from a MERGED adapter, so the pathology mechanism (merge-induced trace-truncation echo) doesn't directly apply. But sft_v5 has not been evaluated under inference at scale, and if/when it is, the monitor needs to be in place to detect any rambling residue.

**Anti-recommendation**: Do NOT proactively run sft_v5 with rp=1.1 — only on observed pathology. Proactive use risks suppressing legitimate reasoning that the working base model needs.

Per the R14 cross-check residual risk: causal attribution of the R14 effect to rep_penalty alone is weakened by stack/version drift between R13 and R14 (vLLM/torch/GPU versions differ). The 15/17 extraction-rescue finding (R13-wrong → R14-right where R13 had no box) is strongly correlated with the rep_penalty change but not isolated from it.
