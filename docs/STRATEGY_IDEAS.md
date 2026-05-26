# STRATEGY_IDEAS

**Last updated:** 2026-05-26 ~14:00 PT (mid-Day 2)

Running log of strategy ideas — validated, failed, queued.

## LOCKED / WORKING

### Format-aware system prompt with CORRECT/WRONG example
Drives 4/8 → 8/8 unanimous on multi-value items. Use for ALL inference. Locked in run_hybrid_inference.py via --system-prompt flag.

### Sample-level reformat post-processor
Extract all \boxed{}, top-level comma split, dedupe, take last N, rewrite as single canonical \boxed{a, b, c}. Captured in scripts/reformat_multi_answer.py. 54 multi-answer repairs on slot1.

### PACE (Wolfram MCP via Mathematica kernel)
Validated batch 1: 5/6 HIGH-confidence rescues + 1 MEDIUM. Symbolic verification beats teacher consensus on hard computable items.

### 4-source ensemble for hard items
base+format / NoThinking / adapter v5 / Wolfram canonical. Drives Slot C tonight.

### run14b cross-check pattern
Cheap (2 min) check whether failure is systemic vs config-specific. Skips unnecessary re-runs.

### Multi-agent + Drive-as-handoff
claude_strategy + vscode + tnr-0 + tnr-1 + claude_wolfram. Drive primary (create-only, new doc per update), repo as backup.

## QUEUED — TRACE PROJECT (tomorrow)

**Goal:** test if Opus 4.7 can reliably read Qwen reasoning + answer and judge correctness. If signal exists, override/tiebreak for Slot D.

**Why Opus 4.7 (not xhigh):**
xhigh failed 16/18 on no-box items with unique wrong answers + extraction errors. Same model = same blind spots as judge. Opus 4.7 is stronger, different training distribution, adds 5th independent signal regardless of judging outcome.

**PoC design:**
- 90 items (30 Qwen-correct, 30 Qwen-wrong, 30 uncertain) via teacher consensus + PACE ground truth
- Independent-solve + judge in single call (two-for-one: also gets 5th teacher answer)
- Standalone scripts/llm_judge.py using Anthropic SDK directly (no DataApp PAT dependency)
- Cost: $5-8. Time: ~3h total.

**Decision tree:**
- Regime A (accurate flag + accurate correct): oracle for Slot D, +5-10pp possible
- Regime B (accurate flag, moderate correct): flag-only, route to Wolfram/manual
- Regime C (unreliable): drop

## QUEUED — Wolfram pass 2 (after confidence map exists)
Targeted arbitration for confidence-map items where sources disagree 2-2 or 3-1. ~30-50 items, cheap.

## FAILED / FALSIFIED

- Multi-answer order swap: 0 items had right values wrong order. Not a lever.
- Per-slot \boxed{}: -16.2pp.
- \dfrac → \frac alone: confounded probe, not clean.
- xhigh on no-box items: worse than cheap teachers. LLM consensus doesn't help.
- slot1/run14b under-generation: SYSTEMIC. Adapter or Wolfram only paths.

## DEFERRED CREATIVE GAMBLES

- Multi-round SC (5×3 vs 1×16): EV 10-20%, samples already independent at T=0.6.
- Prompt-variation shootout: EV 30-40%.
- Self-critique loop: highest gamble, requires scaffolding.

## OPEN HYPOTHESES

- Does format-aware prompt help single-answer items? Untested.
- Rate of "right count, wrong values" failures? PACE only catches under-count.
- For MEDIUM-confidence Wolfram items: which string form does grader accept?
