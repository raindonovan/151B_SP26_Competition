# HOW_WE_KNOW_CORRECTNESS.md — The Mental Model

> **The keystone doc. Read this before touching any inference scan, adapter, post-processor, or submission decision.**

## The one distinction that fixes everything

Every answer has **two independent properties**:

1. **Math correctness** — does the answer equal the true mathematical answer, ignoring how it's written?
2. **Format correctness** — is it written the exact string the Kaggle grader's string-match accepts?

These are independent. An answer can be math-right but format-wrong (proof: the fraction-fix submission #30, where changing only decimal→fraction flipped +2 slice items wrong→right — see `postprocessing/FINDINGS.md` F7).

## The four quadrants every item lives in

| | Format right | Format wrong |
|---|---|---|
| **Math right** | ✅ Scored correct (do nothing) | 🔧 **Format loss** → post-processor fixes, NO adapter needed |
| **Math wrong** | ❌ Needs better math → adapter or inference change | ❌ Doubly broken |

## The rule that resolves the "we don't know what's graded correct" trap

**Ground truth answers the math question. Submissions answer the format question. Never conflate them.**

- Want to know "did Qwen get the math right in run X for item Y?" → compare Qwen's answer to ground truth using a format-BLIND normalizer (Hendrycks `is_equiv`). This needs only the T1 list, never the grader.
- Want to know "is this exact string Kaggle-accepted?" → only submissions can answer this. Format rules accumulate in `postprocessing/NORMALIZATION_RULES.md` as they're confirmed by submission deltas.

## How this hands you the SFT set for free

For each T1 item (where we know the true math answer), scan all inference runs:

- **Bucket A** — some run produced the correct math (format-blind comparison). Not an adapter problem. Find the run, format it through the post-processor, submit.
- **Bucket B** — NO run ever produced the correct math. This is the SFT training set — true answers Qwen can't derive.

Because the comparison is format-blind, format is ruled out of the SFT set selection by construction.

## The adapter-format trap (and how to avoid it)

Past adapter attempts learned wrong formatting. The fix is one rule:

> **Training labels must be in the same canonical format the post-processor outputs.**

Mechanically: take the T1 ground-truth answer → run it through the post-processor → THAT exact string is the SFT training label. Training-time and inference-time formats are identical by construction. The post-processor becomes the single canonical-format definer for the whole pipeline.

**Consequence: the post-processor must be locked BEFORE the adapter is trained.** Order matters. Train on top of a flaky post-processor and you bake the flakiness into the weights.

## The T1 (ground truth) definition

The bar is **two INDEPENDENT evidence types agree** — LLM consensus alone is not enough (teachers are correlated).
T1 (≥99% confidence):
3/3 teachers agree
AND at least one independent non-LLM source agrees
(wolfram_HIGH OR search_GOLD OR qwen_cross_config_unanimous)
AND no structural violation (e.g. probability ∈ [0,1], matrix-symmetric, etc.)
T2 (~90% confidence):
3/3 teachers agree, no independent source yet
OR 2/3 teachers + 1 independent non-LLM source
AND no structural violation
T3 (~75% confidence):
majority teacher + Qwen agrees with majority, no contradicting source
T4-T5: everything else (lower confidence, requires probe to upgrade)

Cross-config Qwen agreement (SC8 ∧ SC16 ∧ nothinking all unanimous) counts as an independent source because the sampling regimes are genuinely different — but it's still the same model, so it's a weaker independence than Wolfram or web search. Use it as a tier booster, not a sole anchor.

## The two engines, working in parallel

| Engine | Question it answers | Oracle |
|---|---|---|
| **Content engine** (T1 list + inference scan) | What's true? Did Qwen get the math right? | Ground truth (T1) |
| **Format engine** (post-processor + submissions) | What string does Kaggle accept? | Kaggle submissions |

They're complementary. Every submission confirms or kills a format rule, which feeds `NORMALIZATION_RULES.md`, which makes the post-processor smarter, which makes Bucket-A submissions land cleanly.

## Canonical homes for the things this doc generates

- T1 list (the math truth) → `data/MASTER_ANSWERS.csv` + a derived `testing/tier1_ground_truth.csv`
- Format rules (what Kaggle accepts) → `postprocessing/NORMALIZATION_RULES.md` (tiered)
- Per-run math-correctness scan results → `inference/run_scan_results.csv`
- Bucket-A items (format-fix candidates) → `submission/csvs/` builds
- Bucket-B items (adapter targets) → adapter training set
- Gold findings of any kind → see the GOLD-RULE in root `CLAUDE.md`
