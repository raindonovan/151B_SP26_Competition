# HANDOFF — Session bootstrap

**Last updated:** 2026-05-26 ~14:00 PT (mid-Day 2 of 6)

If you're starting a new claude_strategy session, read this first.

## Bootstrap sequence
1. Read this doc
2. Read Drive PROJECT_STATE (latest timestamp) — folder "151B Competition" id 14ntQe56m_ufIPyDk_Cs-sPjSESQ1NRZ8
3. Read Drive NEXT_ACTIONS (latest timestamp)
4. Read docs/STRATEGY_IDEAS.md for context on what's been tried
5. Read docs/IMMEDIATE_CONTEXT.md for right-now snapshot
6. Check Drive CLAUDE_STRATEGY_RULES (stable, don't replace) for working protocols

## Current state (2026-05-26 14:00 PT)
- **Day 2 of 6**
- **Best Kaggle**: 0.643 (slot1_minimal_norm, real-inference) / 0.671 (info_4, diagnostic)
- **In flight today**: tnr-0 A1+A2, tnr-1 rescue+NoThinking, A30 adapter v5, claude_wolfram PACE batches
- **Today's Kaggle submissions**: Slot 1 = slot1_reformat.csv (just uploaded), Slot 2 = slot1_wolfram_full_overrides.csv (~14:45 PT after Wolfram completes)
- **Tomorrow's headline**: Slot C real-inference splice using confidence map across all sources

## Multi-agent setup
- **claude_strategy** (this chat): planning + Drive read/write + repo read via git-mcp + Wolfram (sibling chat coordination)
- **claude_vscode**: code execution on DSMLP, repo commits, A30 inference, repo doc updates
- **tnr-0**: Thunder instance 0, A1+A2 chain
- **tnr-1**: Thunder instance 1, rescue + NoThinking chain
- **claude_wolfram**: sibling chat with Wolfram MCP, PACE verification, writes to Drive

## Workflow protocols
- **Drive is PRIMARY** for handoff docs (PROJECT_STATE, NEXT_ACTIONS). Repo docs/ is fallback.
- Drive create-only: NEW doc per update, Rain deletes superseded
- git-mcp write is BROKEN (403); repo writes go via vscode or tnr instances
- Watchdogs on tnr-0/tnr-1 push every 5 min — don't disturb
- Format-aware system prompt LOCKED for all inference

## Key invariants
- Kaggle reset is 17:11 PT daily — 3 slots/day
- Best real-inference score: 0.643 (anchor); never submit below this without strong reason
- Never strip per-sample data from inference runs (feeds future analysis)
- Pre-flight audit before EVERY GPU run (no exceptions)
- Format fix scripts must preserve raw \boxed{} content (don't over-normalize)

## Locked findings (don't re-test)
- Multi-answer order swap: not a lever (0 items recovered)
- Per-slot \boxed{}: -16.2pp
- xhigh on no-box items: worse than cheap teachers
- slot1/run14b under-generation: systemic, not config-specific

## Open work for next session pickup
- Build confidence_map.csv tonight from all sources
- Build Slot C splice tonight
- Tomorrow: Trace POC (Opus 4.7 judge), Slot C submit, Slot D design

See docs/STRATEGY_IDEAS.md for detailed pattern catalog and Trace project plan.
See docs/MASTER_TODO.md for current todos with timestamps.
