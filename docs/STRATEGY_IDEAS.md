# Strategy & Ideas v3 -- 151B Competition

# Last updated: 2026-05-25
# Purpose: Strategy lineage after SFT v4 regression diagnosis

> **MIGRATED FROM DRIVE 2026-05-27 -- HISTORICAL CONTEXT.** Captures strategy state on 5/25. For current state see `docs/IMMEDIATE_CONTEXT.md` and `docs/MASTER_TODO.md`. Preserved for the reasoning lineage that led to the current hybrid-inference approach.

## Current Status (as of 5/25)

- **Best Kaggle: 0.646** (run14b_v3filtered, base model)
- **SFT v4: 0.597** (REGRESSION -- diagnosed, fix plan -> led to SFT v5)
- **Days remaining: ~7**
- **17 submissions used**

## Root Cause Analysis (SFT v4 0.597)

Three confirmed causes:

1. **Catastrophic forgetting** on 552 untrained items (~1-3pp)
2. **MCQ prompt format mismatch** -- teacher traces reference letter labels but training used bare options (~1-2pp)
3. **16K vs 32K token budget** on untrained items (~2.5pp)

Confirmed by 3-LLM research exchange using papers:
- "SFT Memorizes, RL Generalizes" (arXiv:2501.17161)
- "RL Fine-Tuning Heals OOD Forgetting in SFT" (arXiv:2509.12235)
- "Entropy-Adaptive Fine-Tuning" (arXiv:2601.02151)

## The Fix: Hybrid Inference (Fix B + Fix C)

### Fix B: Retrain with letter labels
- Dataset: data/sft_v5_dataset.jsonl (202 MCQ relabelled)
- Config: r=64, alpha=128, max memorization
- -> **DONE 5/25; v5 epoch 12 = checkpoint-1176**

### Fix C: Adapter switching (two separate runs + splice)
- Run 1: Base model for untrained items (32K, SC=8 or reuse run14b)
- Run 2: SFT adapter for trained items ONLY (SC=3)
- Splice by item ID

### Key Insight: Reuse run14b
756 of 943 items had strong/medium SC=8 consensus in run14b -- no need to re-run.
Only re-run: 176 weak items at SC=16 + 391 adapter items at SC=3.

## Expected Outcome (5/25 projection -- see Submission Registry for actuals)

- Untrained items: ~0.67
- Trained items: ~95% accuracy via memorization
- Combined: ~0.75-0.78

**ACTUAL (post-test):** Adapter v5 + run14b splice = 0.639, near break-even with base. v5 NOT format-broken. Real regression ~3 semantic items.

## Research Findings

1. Adapter switching eliminates OOD forgetting entirely
2. r=64 is correct under adapter switching (memorization vault)
3. Max memorization epoch is correct
4. Two separate runs safer than dynamic LoRA switching
5. Route by empirical memorization, not training set membership
6. Byte-identical prompts between training and inference critical
7. pace_patch catches wrong labels before they're memorized

## Competition Constraints (locked)

- Model: Qwen/Qwen3-4B-Thinking-2507
- 3 submissions/day, 2 final selections
- Kaggle grader: last `\boxed{}`, string-match
- Training on private.jsonl: ALLOWED
- DSMLP A30 24GB (inference), Thunder 2x A100 80GB
