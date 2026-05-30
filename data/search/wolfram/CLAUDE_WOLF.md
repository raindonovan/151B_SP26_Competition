# CLAUDE_WOLF.md — Wolfram Verification Agent Operating Manual

**Agent**: claude_wolf (claude_vscode runtime)
**Role**: Wolfram Alpha MCP verification — the ONLY independent (non-LLM) source we have.
**Status**: Phase 2 active — batches B9-B18 done; batch19 next. (Last updated after B18.)

## Terminology (LOCKED — do not call findings "overrides")
This agent produces, per item, a **verified answer** + confidence. That answer is the answer; it has standing on its own. We then *observe* how it relates to the sheet's current `best_answer`:
- **match** — verified answer agrees with the sheet (confirmation; promotes the item toward gold). Matches are valuable, not "no-ops."
- **discrepancy** — verified answer differs from the sheet (the sheet's value is wrong there). We report it; we do NOT "override" anything.
- **inconclusive** — Wolfram couldn't solve it.

Why not "override": (1) it falsely frames the stale sheet value as the thing with standing and our solved answer as displacing it — backwards; (2) it overstates our authority — we are a verification *source*, and whether a discrepancy is acted on is the data/submission agent's call when aggregating all evidence.

**Note — the OTHER, legitimate sense of "override":** the inference pipeline (`inference/scripts/run_inference.py`, reading `wolfram_overrides.csv`, column `override_value`) literally *overrides* the model's last `\boxed{}` output with the verified value. There, "override" correctly names an *action on model output*. That file/schema is load-bearing and documented in the gradescope submission — do NOT rename it. Keep "override" for the pipeline action; use match/discrepancy for verification findings.

## Quick state (after B18)
- Total dataset: 943 items
- DONE (verified): 272 — confidence: 206 HIGH, 59 MED, 4 PARTIAL, 2 MEDIUM, 1 consensus-only
- INCONCLUSIVE (Wolfram couldn't solve): 43
- DISPUTED: 1 (0141)
- UNVERIFIED (not yet done): 627
- Batches done: B1-B8 + WEBSEARCH (legacy, 66) then B9-B18 (this work, 250)
- Known bugs to skip: 0011, 0317, 0570, 0585, 0622, 0858, 0894

## Files
- `WOLF_RESULTS.csv` — 943-row tracking table (id, subject, type, n_ans_slots, wolfram_status, wolfram_answer, confidence, batch, computable, notes, question_preview)
- `WOLF_RESULTS_READABLE.md` — one-line digest of every DONE item
- `TODO.md` — priority queue + next-batch IDs
- `FINDINGS.md` — cumulative cross-batch findings (append-only)
- `SCRATCH.md` — low-friction capture; dump anything surprising
- `batches/batchNN/` — per-batch: questions.csv, results.csv, FINDINGS.md

## Batch loop (25 items per batch)

### Picking items
Priority (highest first):
1. P1: Qwen disagrees with teacher consensus AND subject is computable → `disagree_teacher` in format_flags
2. P2: Teacher split (agree_count=2, not 3) AND computable
3. P3: Multi-answer computable (n_ans_slots ≥ 2)
4. P4: Single-answer computable
5. P5: 'other' subject / MAYBE computable
Skip: 0011, 0317, 0570, 0585, 0622, 0858, 0894

### Per-item workflow
1. Read the full question from private.jsonl (id lookup)
2. Formulate a natural-language Wolfram query
3. Call `mcp__claude_ai_Wolfram__WolframAlpha`
4. Reformulate ONCE if result is ambiguous or empty
5. Extract the answer (value only — discard verbose response)
6. Assign confidence: HIGH / MED / LOW / PARTIAL / INCONCLUSIVE
7. Append row to `batches/batchNN/results.csv` immediately
8. Update `WOLF_RESULTS.csv` row: wolfram_status=DONE, wolfram_answer, confidence, batch

### Confidence guide
- HIGH: unambiguous numeric/symbolic answer, Wolfram fully solved it
- MED: answer likely right but format or interpretation uncertainty
- LOW: Wolfram gave partial info or needed heavy reformulation
- PARTIAL: got some slots but not all (e.g., last slot is interpretation phrase)
- INCONCLUSIVE: Wolfram couldn't compute it (synthetic sequence, missing context, etc.)

### Context hygiene (CRITICAL)
- DISCARD full Wolfram response — extract only the answer value
- Append results.csv row-by-row as you go
- Never batch-write at end of batch
- Commit after every batch as safety boundary

### After each batch
1. Write `batches/batchNN/FINDINGS.md` with:
   - Confidence distribution (HIGH/MED/LOW/PARTIAL/INCONCLUSIVE counts)
   - Disagreements with current sheet answer
   - Format patterns noticed
   - Dataset bugs/quirks
   - Items needing query reformulation
   - Cross-cutting patterns worth promoting to root FINDINGS.md
2. Update WOLF_RESULTS.csv (mark 25 as DONE)
3. Append 25 to WOLF_RESULTS_READABLE.md
4. Update TODO.md (mark batch done, list next 25 IDs)
5. If observation is gold-tier, append to `FINDINGS.md` (root)
6. Commit + push before starting next batch

## Key prior findings (read before batch09)
- 79% of B1-7 wrong items = multi-slot under-count, not arithmetic errors
- B8: 56% had Qwen right mathematically but format-mismatched
- Wolfram HIGH + teacher consensus = near-certain ground truth
- Format (fraction vs decimal, labels, units) is post-processing's job — record the VALUE
- See FINDINGS.md for full taxonomy (7 failure modes)

## Wolfram query tips
- For statistics: include all given data, specify what to compute
- For calc/algebra: paste LaTeX expression, ask "evaluate" or "solve"
- For sequences: list first 5+ terms, ask "find pattern" or "closed form"
- For MCQ: solve the underlying math, then identify which option matches
- If Wolfram returns graph-only: rephrase as "compute [specific value]"
