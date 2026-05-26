# IMMEDIATE_CONTEXT

**Last updated:** 2026-05-26 ~14:00 PT

## Right now
- **Day 2 of 6** in CSE 151B Kaggle math competition
- **Best Kaggle real-inference:** 0.643 (slot1_minimal_norm)
- **Best Kaggle diagnostic:** 0.671 (info_4)
- **All 3 GPU instances active**: tnr-0 (A1+A2), tnr-1 (rescue+NoThinking), A30 DSMLP (adapter v5 smoking)
- **claude_wolfram** processing PACE batches 4-7 (~30 min remaining)

## What's blocking what
- Slot 2 submission → Wolfram batches 4-7 completing
- A30 adapter full launch → smoke confirmation
- Slot C build → all inference + Wolfram landing (~21:00 PT)
- Slot D tomorrow → Slot C scores + Trace POC results

## Quick facts
- 943 items on private set
- Format-aware system prompt (CRITICAL OUTPUT FORMAT + CORRECT/WRONG example) LOCKED
- 6 items systemically broken in base Qwen (slot1 + run14b both undercount); adapter or Wolfram only
- 38 PACE computable items have Wolfram canonical incoming
- 23 non-computable broken items: target for Trace POC tomorrow

## Where to find things
**Drive folder "151B Competition"** (id 14ntQe56m_ufIPyDk_Cs-sPjSESQ1NRZ8):
- PROJECT_STATE - 2026-05-26 14:00 PT (id 1NuesKNAdUKCqytmx5KWXpG4xudN8pevU)
- NEXT_ACTIONS - 2026-05-26 14:00 PT (id 1cjcmbIcs_L85lkjWN0ayB4suEl2MS8sj)
- CLAUDE_STRATEGY_RULES, HANDOFF_PROCEDURE (stable)
- WOLFRAM_BATCH_NN_RESULTS.md (PACE outputs)

**Repo (main branch):**
- submissions/slot1_minimal_norm.csv — 0.643 anchor baseline
- submissions/slot1_reformat.csv — today's Slot 1 (reformat post-processor test)
- data/candidates_targeted_rescue_61.txt — 61 broken multi-answer IDs
- results/pace/pace_today.csv — 61 items with PACE classification
- results/hybrid/tnr-A/ — tnr-0 A1+A2 outputs
- results/hybrid/tnr-B/ — tnr-1 rescue+NoThinking outputs
- results/hybrid/dsmlp-A30/ — A30 adapter outputs

**tnr-1 branch** (inference/tnr-1-20260526T065456Z): full tnr-1 history
**tnr-0 branch** (inference/tnr-0-20260526T065430Z): full tnr-0 history
