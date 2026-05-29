# CLAUDE_WOLF.md — Wolfram Verification Agent Operating Manual

**Agent**: claude_wolf (claude_vscode runtime)
**Role**: Wolfram Alpha MCP verification — the ONLY independent (non-LLM) source we have.
**Status**: Phase 2 active — batch09 is next.

## Quick state
- Total dataset: 943 items
- Legacy verified (B1-B8 + WEBSEARCH): 65 DONE, 1 DISPUTED (0141)
- Unverified: 877 items (876 non-skip, 1 skip: 0570 still flagged)
- Known bugs to skip: 0011, 0317, 0570, 0585, 0622, 0858, 0894

## Files
- `MASTER_QUESTIONS.csv` — 943-row tracking table (id, subject, type, n_ans_slots, wolfram_status, wolfram_answer, confidence, batch, computable, notes, question_preview)
- `WOLF_LIST.md` — one-line digest of every DONE item
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
8. Update `MASTER_QUESTIONS.csv` row: wolfram_status=DONE, wolfram_answer, confidence, batch

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
2. Update MASTER_QUESTIONS.csv (mark 25 as DONE)
3. Append 25 to WOLF_LIST.md
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
