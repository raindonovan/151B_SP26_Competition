# CLAUDE_STRATEGY_RULES — Immutable Project Rules

Updated: 2026-05-27 (migrated to repo; PAT enables direct updates)

---

## My role (claude_strategy)

- Plan, audit, teach. Don't execute on remote machines.
- Spec changes; execution agents (vscode, tnr-0, tnr-1) write code.
- Verify by reading committed output from the repo, not by trusting agent reports.
- After agents push, audit from repo BEFORE authorizing the next launch.

## Project at a glance

- CSE 151B Spring 2026 Kaggle math competition
- 943 private items, Qwen3-4B-Thinking-2507
- Deadline ~2026-06-02 (~5 days from 2026-05-27)
- 2 final submissions required at end (Pick A + Pick B)
- Kaggle cap: 3 submissions/day — SCARCE (15 remaining as of Day 3)
- Gradescope code deadline: 2026-05-31 (4 days away)

## Multi-agent windows

| Window | Role | Identity guard |
|---|---|---|
| claude_strategy (this chat) | plan / audit / teach | n/a |
| claude_vscode (DSMLP) | execution on raindonovan tunnel | auto-loads CLAUDE.md |
| claude_thunder tnr-0 | production GPU runs | `~/.instance-role` = "tnr-0" |
| claude_thunder tnr-1 | production GPU runs | `~/.instance-role` = "tnr-1" |

Cross-agent prompts: `[FROM CLAUDE_STRATEGY → TO <window>]`, single message, hostname guard at top.

## State of truth

Primary: `docs/` in this repo. Editable via GitHub PAT (see Drive SECRETS doc).
Legacy: Drive handoff folder `1lkRmVmCUOEfTnwGLRr3kI4SBYuFAe6kv` — read-only reference.

## Discipline (locked)

- **No maybe-code**: don't draft scripts/prompts I'm not committed to.
- **Pre-flight every GPU run** (memory #25): prompt format, data paths, resume capability, output paths, model paths, 5-item smoke. NO EXCEPTIONS.
- **One prompt at a time for ALL agents**: deliver when predecessor reports; never pre-queue.
- **Status board at END OF EVERY response** (no exceptions, even short replies).
- **Update PROJECT_STATE at every major checkpoint** via GitHub API.
- **Submissions are scarce** (15 remaining): every slot tests a deliberate hypothesis. No throwaway burns.
- **ADHD redirect rule**: when Rain drifts to a tangent, acknowledge briefly, offer to log, redirect back.

## Locked facts

- Kaggle canonical format: `\dfrac` + comma+space + single `\boxed{a, b, c}` (sample submission)
- Grader extracts LAST `\boxed{}`, string-matches with dialect tolerance
- 18 no-box items: unsolvable by LLM consensus (16/18 unique 4th answer vs all teachers)
- Adapter v5: ~3 semantic items regression vs base, NEAR break-even (NOT format-broken)
- Minimal normalizer (strip `\left/\right/\,`) is non-destructive AND rescues ~4 items (+0.4pp confirmed)
- TP=2 works on 2× A100-80GB with Qwen3-4B-Thinking-2507
- Multi-answer shape fix lever: REALIZED at +0.3pp (slot1_reformat Day 2)
- NoThinking prefill: append `Okay, I think I have finished thinking.\n</think>\n\n` after chat template

## Infrastructure state

- git-mcp READ: works (45 tools)
- git-mcp WRITE: via GitHub PAT + bash_tool curl to api.github.com (PAT in Drive SECRETS doc)
- Google Drive: read + create only (no delete/edit). Wolfram batches, web search checkpoints here.
- tnr-0: `instance-x528wsl9-main`, Thunder ID 0
- tnr-1: `instance-q6b81cqp-main`, Thunder ID 1
- OPL embeddings: tnr-0 local ONLY — LFS migration needed before deletion
