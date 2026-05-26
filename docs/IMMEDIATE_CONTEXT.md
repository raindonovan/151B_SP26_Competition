# IMMEDIATE CONTEXT -- current state (2026-05-27 ~01:30 local / ~09:30 UTC)

## Where we are RIGHT NOW

**Last major event**: tnr-0 25th-snapshot restore complete after SIGKILL phantom-memory recovery (took ~90 min). Identity guardrail (`~/.instance-role`) now established on both Thunder instances. Batched runner code (commit 5442405) on tnr-0's branch. chunk=4 smoke just launched.

## Active state

- **tnr-0** (NEW instance, 2x A100-80GB, `instance-x528wsl9-main`): Running chunk=4 batched smoke (8 items, SC=16, max_tokens=49152). ETA 10-20 min. GO/NO-GO gate for tnr-1 restart decision.
- **tnr-1** (original instance, 2x A100-80GB): Still running B2 NoThinking full 943 at serial pace. 43+ items at last check. Plan: kill and restart with batched + `--max-tokens 8192` IF tnr-0 smoke validates.
- **vscode** (DSMLP): standing down
- **claude_strategy**: Drive -> repo doc migration in progress

## Kaggle slots state

- 2 of 3 slots remaining today (only slot1_minimal_norm = 0.643 used)
- HOLDING for tomorrow morning's Thunder-derived submissions

## Best scores snapshot

- **Best real inference**: 0.643 (slot1_minimal_norm)
- Best diagnostic: 0.671 (info_4)
- run14b real: 0.646 (v3 filter)
- Adapter v5 vs base: ~3 semantic items regression (near break-even, NOT format-broken)

## Pending decision: restart tnr-1?

After tnr-0 smoke result:
- **>=2x speedup, clean preemption** -> restart tnr-1 with batched + `--max-tokens 8192` for B2 v2 (saves ~5-8h B2 wallclock)
- **<1.5x speedup** -> leave tnr-1 alone, accept ~50-66% B2 coverage by morning
- **Smoke fails** -> debug, possibly lower chunk size to 2

## What I'm waiting on

1. tnr-0 smoke result (~10-20 min ETA)
2. Then: tnr-1 restart decision
3. Then: A1 production launch on tnr-0 (~2.5-3.5h)
4. Then: B2 v2 production launch on tnr-1 (conditional) (~4-5h)

## Doc migration status (5/27)

- [x] `docs/HANDOFF.md` migrated (replaces stale v4.1)
- [x] `docs/IMMEDIATE_CONTEXT.md` (this doc) -- migrated NOW
- [x] `docs/MASTER_TODO.md` -- migrated NOW
- [x] `docs/STRATEGY_IDEAS.md` -- migrated NOW
- [x] `docs/SUBMISSION_REGISTRY.md` -- migrated NOW
- [x] `docs/DAY_2_SUBMISSION_QUEUE.md` -- migrated NOW

## If chat dies / context lost

- Read this doc + `docs/HANDOFF.md` + `docs/MASTER_TODO.md`
- Check `inference/tnr-0-*` and `inference/tnr-1-*` branches via git-mcp
- Memory entries: #3, #17, #26, #28, #30
