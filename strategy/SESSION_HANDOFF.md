# SESSION_HANDOFF.md — post-Cursor-ACCEPT execution handover

**Status**: Research phase COMPLETE. Cursor independent re-audit returned **ACCEPT @ bc932f8**. v7 execution authorized. Prior claude_strategy session closed; next session picks up at Phase 0 kickoff via the continuation brief.

**Time to deadline**: ~T-8h (Sunday May 31 23:59 PT). Buffer protected.

---

## Goal

Ship Pick B FINAL to Kaggle by deadline via v7 LoRA adapter training. Optimize max P(beats 0.745 floor), NOT peak score. Pick A locked at 0.745 is the floor — every gate breach ships Pick A unchanged.

## Current state

- v7 plan locked: v3.1 canonical structure (d84de5b) + v3.2 patches (27e7a5f) = 14 patches integrated
- Cursor ACCEPT @ bc932f8 (after initial REPLAN @ 9208123 resolved by committing missing artifacts @ 27e7a5f)
- B2 empirical decomposition (308310e): v5 adapter showed +7 net on hard items (T3/T4/T5) — direct support for v7's wrong-residual targeting; caveats include memorization confound + is_equiv grader leniency
- Execution path: 6 phases, ~5h45m wall time, ~2h buffer to deadline
- Execution agents standby: claude_vscode + tnr-0 + tnr-1 ready

## Decisions and why (locked)

- **Wrong-residual targeting + ≥30% T1+T2 hedge** (B4): v5's 87.72% T1+T2 was structural error; invert toward harder items but hedge against unknown scored-slice composition
- **Tier-aware gold provenance** (C3, BINDING): T4/T5 route only on Wolfram-verified — label precision matters most where teacher consensus is weakest
- **SPLICE rule for Pick B FINAL** (C1, BINDING): Pick A frozen + adapter overrides on routed IDs ONLY; NEVER regenerate non-routed rows. Prevents ±2.6pp two-sided noise on ~211 non-routed scored items from swamping one-sided routed gain
- **Dual pilot 80/20 vs 95/5** on 2× A100, deterministic default-to-A tie-break (A2)
- **Phase 4 multi-LoRA** all 6 ckpts simultaneously (~1.54 GB VRAM) with 2 xhigh stress items in pre-flight (C2, BINDING)
- **Plain SC@8 majority is production default** (A1); DeepConf side-channel only, promotes only on zero-regression net-positive
- **Single Sonnet teacher** for trace generation (B3): eliminates teacher-heterogeneity confound
- **Pilot = plumbing + A/B selection**, NOT accuracy gate (Opus reframe); full-train route-sim is the real gate
- **Honest probability**: 50-65% beats 0.745, conditioned on p_label ≥0.85 + SPLICE enforced + 0/4 base rate adjustment

## Open questions (non-blocking)

- **Splice script edge case** (Cursor REAUDIT note 2): if route_to_adapter=True AND adapter answer equals Pick A answer byte-for-byte, the assertion `diff_count == overrides_applied` false-fails. Safe abort (no bad CSV ships) but blocks fire. **Fix before Phase 6 via claude_vscode**: change invariant to `diff_count <= overrides_applied` OR count only actual changes as overrides. ~5 min.
- **Stale header comment** in splice script (Cursor REAUDIT note 1): docstring references `len(routed_ids)`; cosmetic only.
- **Pick A CSV pre-fire integrity check**: 5 min, do during Phase 0
- **PAT rotation status**: memory says rotating today; confirm not breaking mid-execution
- **Class writeup deliverable**: confirm from syllabus whether exists
- **Thunder compute budget**: verify ≥8h on each of tnr-0 and tnr-1
- **Group members on Kaggle entry**: confirm team setup

## Immediate next action (X for new claude_strategy session)

Read the 6 scoped artifacts below, then draft the Phase 0 manifest build prompt for claude_vscode. Post draft to Rain for fire authorization.

Phase 0 has 3 parallel tasks; fire one prompt at a time (vscode first, then tnr-0, then tnr-1):

1. **claude_vscode**: build `data/v7_wrong_residual.csv` with C3 tier-aware provenance (HIGH-W/HIGH-T/MED/LOW) + B4 tier-mix-aware sampling (≥30% T1+T2 within wrong-residual). Pass: ≥100 route-eligible items, else fall back to Pick A only.
2. **tnr-0**: base SC@16 items 0-471 at deploy temp (0.6/0.95/16). vLLM 0.10.2/0.11.1, `--enforce-eager --enable-lora --max-loras=2 --max-lora-rank=64`, logprobs=True top_logprobs=20.
3. **tnr-1**: same spec as tnr-0 but items 472-942.

## Durable artifact pointers (scoped read on spawn)

| # | Path | Commit | Why |
|---|------|--------|-----|
| 1 | strategy/SESSION_HANDOFF.md | this commit | Durable handoff state (this doc) |
| 2 | strategy/PHASE_D_v7_PLAN.md | d84de5b | v3.1 canonical structure (257 lines) |
| 3 | strategy/V3_2_PATCH_NOTES.md | 27e7a5f | 4 patches (C1-C4) layered on v3.1 |
| 4 | data/v5_decomp_summary.md | 308310e | B2 empirical evidence (+7 net T3/T4/T5) |
| 5 | strategy/REVIEW_OF_V3_2_REAUDIT.md | bc932f8 | Cursor ACCEPT verdict + risk notes |
| 6 | submission/scripts/build_pickb_final_splice.py | 27e7a5f | Phase 6 splice (known edge case) |

Lazy-load only on need: REVIEW_OF_STRATEGY_V3.md (204380c), REVIEW_OF_CURSOR_RESEARCH.md (536e4a4), REVIEW_OF_V3_2_AND_B2.md (9208123, superseded), RESEARCH_PHASE_FLOW.md (cd2161d), PICKB_FINAL_PREFIRE_CHECKLIST.md, SCRATCH.md, archive/

DO NOT read on spawn: full repo, archived versions, inference/ code, large CSVs.

## Execution path (6 phases)

| Phase | Duration | Both GPUs | Key hard gate |
|-------|----------|-----------|---------------|
| 0 | 60 min | YES | ≥100 route-eligible items + both SC@16 splits done |
| 1 | 45 min | YES | At least one pilot loads/trains, format ≥95% |
| 2 | 40 min | YES | CI lower bound ≥20% flip + anchor regression ≤2/10 |
| 3 | 90 min | YES | Full train 12 epochs, all 6 ckpts saved |
| 4 | 50 min | YES | Pre-flight pass + items_won-2×regressed ≥10 |
| 5 | 45 min | YES | Tier-aware C3 route gate applied |
| 6 | 25 min | NO | SPLICE diff_count assertion (edge case patched first) |

## Critical operational rules (BINDING)

### Tools
- **NEVER use git-mcp:create_or_update_file or git-mcp:push_files** — they 403 with "Resource not accessible by integration." Use bash+PAT (preferred) or route ALL commits through claude_vscode.
- git-mcp:get_file_contents works fine for reads.

### Operations  
- One paste-ready prompt at a time for execution agents
- Identity-address at top: TO: CLAUDE_VSCODE / TO: CURSOR / TO: TNR0 / TO: TNR1
- Status board at end of every response
- Don't audit your own work — Cursor is the independent reviewer
- Don't re-litigate the plan (v3.1 + v3.2 LOCKED)

### vLLM specifics
- Version: 0.10.2 or 0.11.1
- Flags: `--enforce-eager --enable-lora --max-loras=N --max-lora-rank=64` (N=phase-specific)
- Sampling: temperature=0.6, top_p=0.95, top_k=20 (Qwen3 official)
- Token budget: 49152/24576 default; T4/T5 use 81920/65536
- Always logprobs=True top_logprobs=20

### Trace generation
- Single Sonnet teacher (B3)

## Agents at handover

| Agent | State |
|---|---|
| claude_strategy | Prior session CLOSED; fresh session via continuation brief |
| claude_vscode | Idle, ready for Phase 0 manifest build |
| tnr-0 | Idle, ready for Phase 0 base SC@16 (items 0-471) |
| tnr-1 | Killed thinking-twin probe (9 partial salvaged at inference/results/thinking_twin_probe/), ready for Phase 0 base SC@16 (items 472-942) |
| Cursor | Available for execution-time audits if needed |
| Rain (human) | Final authority, dataapp courier |

## What Rain owns

- Authorize Phase 0 kickoff (and subsequent phases)
- Courier LLM tiebreak queries via dataapp (max 2 total)
- Final fire decision on Kaggle submission
- Gradescope submission (separate workflow, run_inference() entry point)

## Authority

If session-resume context contradicts these documents, **the documents win**. Continuation brief is the cold-start primer; this SESSION_HANDOFF.md is the supporting durable state.
