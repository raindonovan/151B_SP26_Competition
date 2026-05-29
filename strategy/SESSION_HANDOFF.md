# SESSION_HANDOFF.md — claude_strategy session state

> Read this FIRST when resuming a claude_strategy chat. Detailed findings live in their canonical homes; this is the index.

**Last updated**: 2026-05-28 (end of Day 6 — handing off to fresh chat after tool-set degradation)

## TL;DR — Where we are

- **Score: 0.706** is current best (slot4_undercount_expand). New high.
- **Picks must be changed**: Kaggle currently has 0.438 / 0.420 selected. Update to 0.706.
- **F7 (postprocessing/FINDINGS.md) PROVEN**: tier-1 items are graded wrong on format. Fraction-fix submission gained +2/283 with pure decimal→fraction change. Post-processing is the major lever.
- **MCQ override bug**: appending `\boxed{LETTER}` is a NO-OP — grader extracts FIRST `\boxed{LETTER}`. All past MCQ overrides were silently ignored. Fix is prepend / full-replace.
- **Search-gold bulk overlay = harmful (-2.1pp)** but root cause was format application errors (added labels, collapsed multi-answers), not bad content. Normalized search-gold is untested.

## Tomorrow's north star

The **inference-run scan**: for every T1 item, scan all runs (SC8/SC16/SC32/nothinking) using a Hendrycks-normalized format-blind comparison. Classify each T1 item as:
- **Bucket A** — some run got the math right → format-fix and submit, NO adapter needed
- **Bucket B** — no run ever got the math right → adapter training set

This is the operational unlock. See `strategy/HOW_WE_KNOW_CORRECTNESS.md` for the full framework.

## Pending tasks (in priority order)

1. **Push a0cb626 if unpushed** — contains SECURITY.md, CLAUDE.md (CREDENTIALS+GOLD rules), strategy/HOW_WE_KNOW_CORRECTNESS.md, data/ANSWER_SHEET_SCHEMA.md. Check `git log origin/main..HEAD`.
2. **Spawn claude_wolf_01** — bootstrap wolfram/ directory + run batch 01 (25 items per batch). Spawn prompt drafted in chat history. Wolfram only 66/943 verified (~7%); ~700 are computable. Wide-open lever.
3. **Compute qwen_cross_config_agree column** — free T1 expander, runs locally. Spec in `data/ANSWER_SHEET_SCHEMA.md`. Could expand T1 from ~90 to ~250+ overnight.
4. **Run the T1 inference scan** — Bucket A / Bucket B classification.
5. **Build the 2-3 confirmed-lever submissions** (using daily slots):
   - `undercount_plus_frac` (built; expected ~0.713) — Pick A material
   - `mcq_prepend_fix` (built; +~1pp expected on 16 INVALID MCQ items)
   - `search_gold_NORMALIZED` (untested; tests corrected hypothesis)

## Submission budget

~17 slots remaining before 5/31 deadline. Allocation:
- ~12 for format-rule probes (each tests a specific NORMALIZATION_RULES.md tier-3 rule)
- ~3 for score-locks (latest confirmed levers stacked, ensures Pick A is highest)
- ~2 reserve (adapter validation, emergency)

## Locked findings (canonical homes — do not duplicate, just reference)

| Finding | Home |
|---|---|
| Tier-1 items graded wrong on format (F7) | `postprocessing/FINDINGS.md` |
| 4 active concerns: MCQ bug, EV calc, proxy evidence, slice assumptions | `submission/AMBER_ALERT.md` |
| Kaggle scores on ~283 LB slice, not 943; final ranking is 943 | `submission/RED_ALERT_LB_SUBSET.md` |
| Normalization rules tiered (T1/T2/T3/T4) — trailing-zero strip is NEUTRAL | `postprocessing/NORMALIZATION_RULES.md` |
| Math-vs-format mental model, two-bucket SFT framework | `strategy/HOW_WE_KNOW_CORRECTNESS.md` |
| Upgraded answer-sheet schema + tier formula | `data/ANSWER_SHEET_SCHEMA.md` |
| Search-gold raw harmful, normalized untested (correction) | `submission/SCRATCH.md` (2026-05-28 correction) |

## Locked SOPs

| SOP | What it says | Where |
|---|---|---|
| CREDENTIALS RULE | Never embed PAT in prompts. Lives in `~/.git-credentials` per runtime. Fine-grained ≤7-day. | `CLAUDE.md` + `SECURITY.md` |
| GOLD-RULE | File findings in canonical home same session. Folder map in CLAUDE.md. | `CLAUDE.md` |
| Agent lifecycle | Role&Relevance in spawn prompt; mandatory SCRATCH.md signoff before ending. | `CLAUDE.md` |
| Terminology | "test set" = ~283 slice; "FINAL test set" = 943. | `CLAUDE.md` |
| VSCODE COMMIT BLOCK | When claude_strategy in chat can't write directly, emit paste-ready block for claude_vscode. | `strategy/CLAUDE.md` |

## Tool-set notes for next claude_strategy

Opus 4.7 chat UI has a **"Code" chip** at the bottom of the message input. When enabled, claude_strategy gets `bash_tool / create_file / view / str_replace` and can clone-edit-push directly (the "singing" workflow). When disabled or in older toggle states, falls back to GitHub MCP (read-only writes 403) + VSCODE COMMIT BLOCK relay.

**Verify on first message**: run an `ls` or any innocuous bash command. If bash_tool isn't available, tell Rain to check the Code chip.

## Recent session signoff

### Day 6 (2026-05-28, claude_strategy)
- Documented F7 (tier-1 graded wrong on format) with the fraction-fix smoking gun
- Wrote HOW_WE_KNOW_CORRECTNESS.md (the keystone mental model)
- Locked NORMALIZATION_RULES.md tiered structure
- Investigated search-gold harm — corrected to "format-application error, not bad content"
- Identified MCQ append-bug (AMBER #3)
- Designed wolfram/ directory + CLAUDE_WOLF.md schema + 25-per-batch workflow
- Handled SECURITY incident: classic PAT exposed in spawn prompts → rotated → policy locked
- GitHub MCP integration write scope confirmed broken (Anthropic-side OAuth bug, issues #38091 / #61189)
- Established VSCODE COMMIT BLOCK pattern as write bridge
- Mid-session tool-set degraded (bash_tool dropped); transitioning to fresh chat with Code enabled

### What's left for next claude_strategy
- Verify tools, read this doc + CLAUDE.md + SECURITY.md + HOW_WE_KNOW_CORRECTNESS.md + AMBER_ALERT.md + F7 in postprocessing/FINDINGS.md
- Confirm a0cb626 pushed (or push it)
- Pick up the wolf-agent spawn and the inference-run scan
