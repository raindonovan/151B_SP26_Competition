# PLAYBOOK — Drive to 0.85 in 5 Days

**Created**: 2026-05-28 (Day 4 start)
**Owner**: Rain (claude_strategy as scribe)
**Goal**: Hit 0.85 on Kaggle private leaderboard by 2026-06-02 using what we already have + 5 days of focused work.

## What this is

The PLAYBOOK is a focused work-track for the final 5-day push. It runs like any other sub-repo (wolfram/, submissions/, etc.) — has its own TODO, findings, research, runs, and decisions, separate from the canonical project state.

**Canonical project state** lives elsewhere:
- `docs/STRATEGY_DAY4_LOCKED.md` — handoff doc for session compaction
- `docs/SUBMISSIONS_TODO.md` — competition-wide TODO
- `docs/FINDINGS.md` — competition-wide knowledge base
- `docs/PROJECT_STATE.md` — global state snapshot

The PLAYBOOK is the **plan to hit 0.85**, not the project's full ledger. Things land here when they're part of the 0.85 push.

## Folder structure

```
playbook/
├── README.md           — this file
├── TIERS.md            — canonical tier naming (T1-T5 + T0)
├── TODO.md             — playbook todo (separate from canonical)
├── FINDINGS.md         — findings specific to playbook execution
├── RESEARCH.md         — research notes for playbook (TIR, PRM, distillation, etc.)
├── LEVERS.md           — the 5 levers with feasibility + ENG time + status
├── POSTMORTEMS.md      — what we tried and failed (and why)
└── runs/               — one folder per analyzed run (see runs/README.md)
    └── README.md
```

## Workflow

1. **New idea/lever** → add to LEVERS.md with feasibility score + ENG time + risk
2. **Need to verify feasibility** → write research question to RESEARCH.md, dispatch to research agent
3. **Want to execute a lever** → add specific task to TODO.md with owner + due date
4. **Run completes** → create `playbook/runs/<run_name>/` folder with output + analysis.md + decision.md
5. **Hypothesis confirmed/killed** → write to FINDINGS.md; update LEVERS.md status
6. **Lever fails or run wastes time** → POSTMORTEMS.md entry

## Discipline rules

- **No lever moves to "EXECUTING" status without a feasibility score ≥6/10 AND a smoke test plan**
- **No run gets locked as "complete" without an `analysis.md` written**
- **Every projection states LOWER BOUND first, then upper bound (no more inherited optimism)**
- **Postmortem within 24h of any failure (otherwise we move on without learning)**
