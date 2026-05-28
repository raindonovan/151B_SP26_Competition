# SESSION HANDOFF — Day 5 Evening (2026-05-28)

## You are claude_strategy = CENTRAL NODE
Read `agents/CLAUDE_STRATEGY.md` for your full tools list and operating rules.

## Session Start Checklist
1. Clone repo: `git clone https://github.com/beepbeeepimajeep/151B_SP26_Competition.git /home/claude/repo`
2. Ask Rain for PAT: "I need the GitHub PAT to push directly."
3. Read this file + `agents/CLAUDE_STRATEGY.md` + memory
4. Check `strategy/TODO.md` for priorities

## Current State
- **Best inference-only**: 0.646 (slot1_reformat, run14b SC=8 32K)
- **Best with overrides**: 0.692 (kitchen_sink_C, 78 overrides)
- **Leader**: 0.85
- **Deadline**: Sun 5/31 (Gradescope code + Kaggle final picks)
- **Submissions used**: 29 of ~45 total (3/day). ~12 remaining.
- **CURRENT KAGGLE PICKS ARE WRONG**: 0.438 + 0.420 selected. CHANGE BEFORE DEADLINE.

## What was done Day 5
- Full repo reorganization into pipeline structure (agents/ strategy/ data/ inference/ postprocessing/ submission/ archive/ infrastructure/)
- Full data audits: DSMLP clean, Thunder tnr-0 clean, tnr-1 clean (kill both)
- 4 critical inference JSONLs LFS-tracked (586MB, f231f1a)
- 29/29 submission CSVs verified + definitive REGISTRY.md with all Kaggle scores
- Agent configs updated with tools, LFS rule, full read protocol
- Direct push via PAT + bash_tool established (breakthrough — no more vscode relay for writes)
- Checkpoint stubs committed for untracked weights (paper trail for report)
- Gold findings from repo read captured (see below)

## Repo Structure (post-reorg)
```
START_HERE.md          # Entry point (NEEDS UPDATE — still has old paths)
agents/                # CLAUDE_VSCODE.md, CLAUDE_STRATEGY.md, CLAUDE_THUNDER.md
strategy/              # SESSION_HANDOFF (this), TODO, LEVERS, TIERS, FINDINGS, RESEARCH
data/                  # answer_sheet/, search/{wolfram,pace,opl,search_app,teachers}, system_prompts/
inference/             # scripts/, results/, runs/, adapters/{sft_v1-v5}, training/
postprocessing/        # scripts/, format_review/, FINDINGS, TODO
submission/            # csvs/ (29 files), scripts/, REGISTRY.md, INTEGRITY_REPORT.md
archive/               # handoffs/, strategy/, design/, research/, docs/, session_logs/, submissions_never_sent/
infrastructure/        # scripts/, pre_flight/, logs/
```

## Gold Findings from Day 5 Repo Read
1. **Public dataset matching (NuminaMath 860K + MATH 12.5K)** = highest-EV play not yet started (from STRATEGY_0_85.md)
2. **~310 items wrong despite \boxed{}** — ceiling from fixing WRONG answers >> format fixes or no-box rescue
3. **Trailing-zero strip PROVEN NEUTRAL** — Day 3 Slots 1 vs 2 both 0.692
4. **MED tier = +0.3pp** — kitchen sink (0.692) vs minus-all-MED (0.689)
5. **format_aware_v1.txt** already implements V2 bookend addressing grader's last-\boxed{} behavior
6. **TIR is KILLED by rules** — STRATEGY_0_85 Day 6 TIR plan is dead
7. **Cross-Run Oracle Harvest UNLOCKED** — all inference JSONLs now on GitHub via LFS

## Priority Stack (next session)
1. **UPDATE START_HERE.md** with post-reorg paths (still points to old structure)
2. **Update strategy/TODO.md** with comprehensive priorities
3. **Cross-Run Oracle Harvest** — build oracle matrix from 12+ inference runs (which items did ANY run get right?)
4. **Post-processor buildout** — multi-slot expander on 51 undercount items
5. **Public dataset matching** — NuminaMath/MATH semantic search for verified answers
6. **Gradescope code submission** — single run_inference() entry point
7. **CHANGE KAGGLE FINAL PICKS** — currently 0.438 + 0.420, should be 0.692 + next best

## Key Files to Read
- `agents/CLAUDE_STRATEGY.md` — your operating contract (UPDATED Day 5 with tools)
- `strategy/LEVERS.md` — active levers
- `strategy/TIERS.md` — T1-T5 confidence tiers
- `submission/REGISTRY.md` — all 29 submissions with scores
- `postprocessing/TODO.md` — post-processing levers
- `infrastructure/pre_flight/production_commands.md` — exact inference configs

## Compute Status
- **DSMLP**: Active, A30 24GB, clean
- **Thunder tnr-0**: KILL (audited, clean)
- **Thunder tnr-1**: KILL (audited, stashes droppable)
