# Active Plan
Locked: 2026-05-21.
Authority: claude_strategy (Rain's planning agent in Claude.ai).
Status: Active. Supersedes PLAN.md previous version (2026-05-13).

This doc is the source of truth for what runs next. Phases and decision rules. Future agent sessions should read this before proposing changes.

## Terminology

- **public** = `data/public.jsonl`, 1126 items with embedded answer field. Retired as eval surface (~10% gold errors, instructor-confirmed).
- **private_kaggle** = scoring via CSV submission to Kaggle. Uses `private.jsonl` at repo root (943 items, no answer field). Returns single aggregate score.
- **private_local** = scoring against pseudo-gold from DataApp pipeline (3-teacher or 4-teacher consensus depending on xhigh coverage). Same inference run as input; different scoring path.

## Tier 1 (must-ship, ~11 days remaining as of 2026-05-20)

### Phase A — run14b inference on private (in progress)
- Config: V0_baseline, SC=8, 32k tokens, single temperature, locked sampling
- Output: `results/run14b_sc8_v1_private943_tok32k_pp1.jsonl`
- Status: ~88% complete as of 2026-05-21, multi-pod resume working
- When complete: convert to CSV, submit to Kaggle, record score in `experiments.md`
- Expected: 0.62-0.66 (Run 09 anchor is 0.614 at 16k tokens)

### Phase B — SFT v3 training (gated on DataApp completion)
- Training compute: Thunder Compute H100 PCIe (separate VS Code window from laptop, not DSMLP)
- Training data: produced by DataApp pipeline (4-teacher consensus, PRIORITY-labeled wrong items, Sonnet > GPT-5.4 > GPT-OSS trace preference)
- Base model: `Qwen/Qwen3-4B-Thinking-2507` (no checkpoints)
- Eval methodology: per DESIGN.md §1209-1262 (multi-signal eval, per-item logged metrics, checkpoint selection criterion, submission gate)
- Configs: overfitting-encouraged first (r=64, weight_decay=0, more epochs), then standard if time permits
- Lessons carry-forward from v1 catastrophe (2026-05-06): profile p99 trace lengths, smoke on 1 item, track no-box rate

### Tier 1 hard cutoffs
- Day 9 of remaining: hard cutoff for new experiments
- Day 11: SFT v3 outputs validated and submitted

## Tier 2 (conditional, after Tier 1 ships)

### Phase C — GRPO Phase 2
Conditions ALL required:
- SFT v3 trained + inferred successfully
- SFT v3 Kaggle score <0.65 (room to improve)
- DataApp produced clean pseudo-gold for RL rewards

If any condition not met: skip.

### Phase D — Order audit (post-DataApp consensus)
- Compare run14b multi-answer items' answer order vs consensus order
- Quantify free points from order-fixing alone
- Applies retroactively to run14b output (same input, same model behavior)

## NOT in this plan (deliberately deferred or excluded)

- run14c (V0-V4 lever bundling). Dropped from Tier 1.
- SC=16 experiments. Diminishing returns vs SFT upside.
- 64k token budget. Memory pressure on DSMLP, marginal gain.
- Confidence-aware abstention. Backlog.
- Repeated independent prompt-engineering ablations. V0-V4 confirmed ceiling at n=50.

## Hard constraints (carry-forward)

- **Token budget rule:** `max_model_len = max_new_tokens + 4096` (never set equal)
- **Locked sampling:** `temperature=0.6, top_p=0.95, top_k=20, min_p=0, rep_pen=1.0`
- **judger.py is NOT used for accuracy decisions.** Only Kaggle is truth (28pp gap, see CLAUDE.md).
- **Public set retired as eval surface** (~10% gold errors).
- **Submission slots are not scarce** (3/day, 3 days of available slots remaining).
- **DSMLP walltime is 6 hours per pod.** Incremental writes + resume mandatory.
- **`private.jsonl` lives at repo root, NOT `data/private.jsonl`.** Always pass `--data-path private.jsonl`.
- **Training base: only `Qwen/Qwen3-4B-Thinking-2507`** itself (not derived checkpoints).

## Document boundaries

- This file: phase sequencing + decision rules + Tier 1/Tier 2 split
- `CLAUDE.md`: claude_vscode operating contract (execution rules)
- `CLAUDE_STRATEGY.md`: claude_strategy operating contract (planning rules)
- `DESIGN.md`: historical design rationale + still-valid SFT eval methodology
- `COMPETITION.md`: competition rules + scoring + submission format
- `experiments.md`: run log + metadata
- `PIVOT.md`: SFT v1 → V0-V4 ablation pivot pointer
- `SESSION_LOG.md`: post-mortems (most recent: 2026-05-06 SFT v1 catastrophe)

## Revisions

- 2026-05-21: Rewritten by claude_strategy after audit. Tier 1/Tier 2 split locked. run14c dropped. dataClean renamed → DataApp (separate repo). DESIGN.md §1209-1262 eval methodology carried into Phase B.
- 2026-05-13: Original plan locked (now superseded).
