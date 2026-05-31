# SESSION_HANDOFF.md — Day 9 final, execution handover

**Status**: Research phase COMPLETE. Execution phase begins immediately. claude_strategy session closing for context-management reasons; next agent (fresh claude_strategy session OR direct execution coordination) picks up at Phase 0 kickoff.

**Time to deadline**: ~T-9h (Sunday May 31 23:59 PT).

---

## What's locked

| Artifact | Path | Commit |
|---|---|---|
| v7 plan canonical structure | `strategy/PHASE_D_v7_PLAN.md` | d84de5b (v3.1) |
| v3.2 patch notes (4 new patches) | `strategy/V3_2_PATCH_NOTES.md` | this commit |
| Research phase flow protocol | `strategy/RESEARCH_PHASE_FLOW.md` | cd2161d |
| Cursor review of v3 plan | `strategy/REVIEW_OF_STRATEGY_V3.md` | 204380c |
| claude_strategy review of Cursor research | `strategy/REVIEW_OF_CURSOR_RESEARCH.md` | 536e4a4 |
| B2 v5 per-item decomposition | `data/v5_per_item_decomp.csv` + `data/v5_decomp_summary.md` | this commit |
| Pre-fire checklist | `submission/PICKB_FINAL_PREFIRE_CHECKLIST.md` | locked from prior session |
| Cursor combined audit of v3.2 + B2 | `strategy/REVIEW_OF_V3_2_AND_B2.md` | PENDING — gates execution kickoff |

## What the next agent does

**ON SESSION OPEN**: 
1. Read v3.1 plan (`strategy/PHASE_D_v7_PLAN.md` @ d84de5b)
2. Read v3.2 patch notes (`strategy/V3_2_PATCH_NOTES.md`)
3. Read B2 summary (`data/v5_decomp_summary.md`)
4. Read Cursor combined audit when committed (`strategy/REVIEW_OF_V3_2_AND_B2.md`)
5. Read this handoff doc

**FIRST DECISION**: Cursor audit ACCEPT / REPLAN / TIEBREAK on v3.2 + B2.
- If ACCEPT → fire Phase 0 prompts to claude_vscode + tnr-0 + tnr-1
- If REPLAN → tight v3.3 patch (max 30 min, must not delay Phase 0 entry beyond T-7h)
- If TIEBREAK → ONE more LLM query via dataapp on a sharp specific question

**DO NOT**:
- Re-litigate v3.1 or v3.2 plan content
- Add new LLM consultations beyond tiebreak
- Add new research questions
- Modify the SPLICE rule (C1) — it's binding
- Change tier-aware provenance gate (C3) thresholds
- Skip the 6-LoRA pre-flight stress test (C2)

## v3.2 critical patches summary (binding for execution)

- **C1 SPLICE rule**: Phase 6 Pick B FINAL CSV = Pick A frozen + adapter overrides on routed IDs ONLY. Diff count assertion is hard gate. Build script: `submission/scripts/build_pickb_final_splice.py`.
- **C2 stress items**: Phase 4 pre-flight = 5 normal + 2 xhigh-difficulty items across all 6 adapter IDs concurrently. No PagedAttention preemption / no OOM / xhigh slowdown <2× vs normal.
- **C3 tier-aware gold provenance**: T4/T5 route only on Wolfram-verified. T2/T3 on HIGH-W or HIGH-T (2+ teacher). T1 allows MED. T0 needs HIGH.
- **C4 probability honest range**: 50-65% conditioned on p_label ≥0.85, SPLICE enforced, 0/4 base rate adjustment.

## Open Phase 0 prompts to draft (immediate next steps)

1. **Phase 0 manifest build prompt** for claude_vscode:
   - Build `data/v7_wrong_residual.csv` with gold_provenance tagging (HIGH-W/HIGH-T/MED/LOW)
   - Include `route_eligible_tier_aware` column per C3 logic
   - Maintain ≥30% T1+T2 within wrong-residual (B4)
   - Output ≥100 route-eligible items or fall back to Pick A only (no v7)

2. **Phase 0 base SC@16 prompt** for tnr-0:
   - Run base SC@16 on items 0-471 at deploy temp (0.6/0.95/16)
   - vLLM 0.10.2 or 0.11.1, --enforce-eager --enable-lora --max-loras=2 --max-lora-rank=64
   - logprobs=True top_logprobs=20

3. **Phase 0 base SC@16 prompt** for tnr-1:
   - Same as tnr-0 but items 472-942

## Agents at handover

| Agent | State |
|---|---|
| claude_strategy | CLOSING this session post-handoff |
| Cursor | Standby for combined audit (prompt drafted by claude_strategy, awaiting fire) |
| claude_vscode | Idle post-commits, awaiting Phase 0 manifest build prompt |
| tnr-0 | Idle, ready for Phase 0 base SC@16 (items 0-471) |
| tnr-1 | Killed thinking-twin probe + salvaged 9 partial items; ready for Phase 0 base SC@16 (items 472-942) |

## Pressing non-execution items (from claude_strategy's last check-in)

These need attention BEFORE final fire but in parallel with execution:

- **Pick A CSV pre-fire integrity check** (5 min) — verify byte-identical to last validated state, 943 rows, no NaN
- **PAT rotation status** — confirm rotated or DELAYED until after fire
- **Class writeup deliverable** — confirm from syllabus whether exists; if so, separate deadline
- **Thunder compute budget** — verify ≥8h on each of tnr-0 and tnr-1
- **Group members on Kaggle entry** — confirm team setup

## Critical operational rules

- vLLM version: pin 0.10.2 or 0.11.1 on all GPU instances
- Launch flags: `--enforce-eager --enable-lora --max-loras=N --max-lora-rank=64` (N=phase-specific)
- Sampling: temperature=0.6, top_p=0.95, top_k=20 (Qwen3 official)
- Token budget: max_tokens=49152, thinking_budget=24576 default; T4/T5 use 81920/65536
- Always logprobs=True top_logprobs=20 for SC inference
- Single Sonnet teacher for trace generation (B3, no heterogeneity)

## What the human (Rain) owns

- Authorize Phase 0 kickoff post-Cursor-audit
- Courier LLM queries via dataapp (max one tiebreak before executive call)
- Final fire decision on Kaggle submission
- Gradescope submission (separate workflow, run_inference() entry point)

## Final reads before kickoff

1. v3.1 plan d84de5b
2. v3.2 patch notes (this commit)
3. B2 summary (this commit)
4. Cursor combined audit (pending)
5. This SESSION_HANDOFF
6. submission/PICKB_FINAL_PREFIRE_CHECKLIST.md

If session-resume context says anything inconsistent with these documents, the documents win. claude_strategy session is CLOSED post-this-commit; treat any prior chat as informational only.
