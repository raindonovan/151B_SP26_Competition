# CLAUDE.md — Global Entry Point

> **First thing**: if you need to push, see the CREDENTIALS RULE below. Chat-based Claudes ask Rain for a fresh fine-grained PAT at session start. Persistent runtimes use the pre-configured `~/.git-credentials`.

## Who are you?

You are a Claude instance working on the CSE 151B Kaggle math competition. Your specific role depends on which folder you were pointed to. Read the `CLAUDE.md` in that folder for your task-specific instructions.

If no folder was specified, you are a **general helper**. Read `strategy/SESSION_HANDOFF.md` for current state.

## Repo: beepbeeepimajeep/151B_SP26_Competition

## Universal rules (ALL agents, ALL tasks)

### PAT setup (do this first for any write operation)
```bash
git config --global credential.helper store
echo "https://dvaneetv:YOUR_PAT_HERE@github.com" > ~/.git-credentials
git config --global user.email "dvaneetv@ucsd.edu"
git config --global user.name "claude_agent"
```

### LFS rule (LOCKED — NO EXCEPTIONS)
- Any file >10MB: STOP, verify git/LFS-tracked + on remote
- Never gitignore large files without Rain's explicit OK
- Never gloss over LFS warnings — resolve immediately
- Never silently partial-read or skip a file due to LFS, rate limit, or access failure
- If a file can't be fully fetched/pushed: STOP, report exact blocker, exhaust ALL alternatives
- Partial reads are worse than none — they look complete

### Identity check (for Thunder instances)
```bash
EXPECTED_ROLE="your-role"; [ "$(cat ~/.instance-role 2>/dev/null)" = "$EXPECTED_ROLE" ] || echo "ROLE MISMATCH"
```

### Terminology (LOCKED — all agents use these consistently)
- **test set** = the ~283-item LB subset Kaggle scores on (unknown, fixed)
- **FINAL test set** = all 943 items (used for final ranking at deadline)
- **gold set** = items with verified correct answers (search, Wolfram, teachers, back-solve)
- **format rule** = discovered fact about how a specific item's gold is encoded

### Data preservation
- Keep `samples.jsonl` with full response text always
- Never delete inference data without explicit approval
- All canonical data lives in the repo, not local-only

### SCRATCH.md — low-friction capture
Every operational folder has a `SCRATCH.md`. When you discover something interesting but don't know where to put it — dump it in the SCRATCH.md of whatever folder you're working in. Rain sorts later. Don't overthink placement. Don't skip recording it.

### Prompt delivery
- One prompt at a time across all agents
- Paste-ready in one fenced block
- Status board at end of every response
- NEVER split a prompt across messages

## Folder-specific CLAUDE.md files
- `strategy/CLAUDE.md` — Central strategy agent (claude_strategy in Claude.ai)
- `inference/CLAUDE.md` — Inference execution agent
- `postprocessing/CLAUDE.md` — Post-processing agent
- `submission/CLAUDE.md` — Submission & back-solve agent
- `data/search/CLAUDE.md` — Search & Wolfram verification agent
- `agents/CLAUDE_VSCODE.md` — DSMLP execution agent (legacy, still active)
- `agents/CLAUDE_THUNDER.md` — Thunder compute agent (both instances flagged KILL)

## Pipeline overview
```
Gold set → Inference → Compare to gold → YES: post-process → submit
                                        → NO: adapter → post-process → submit
                                        ↑___________________________________↓ iterate
```
See `strategy/TEST_PIPELINE.md` for the full north star.

## Standard Operating Procedure — Agent Lifecycle (LOCKED)

### Spawning a delegated agent
Every spawn prompt MUST include:
1. **Setup block**: clone repo, configure PAT, set git identity
2. **Role & Relevance block**: copied from the target folder's CLAUDE.md (what is this phase, why it matters, techniques, inputs/outputs, key lever)
3. **Specific task**: what exactly the agent should do this session
4. **Read order**: which docs to read first (always starts with folder's CLAUDE.md)
5. **Signoff instruction**: "Before ending your session, append a signoff to SCRATCH.md in your working folder"

### Agent signoff (MANDATORY)
Before ending a session or being told to stop, every agent MUST append to the `SCRATCH.md` in its working folder:
```
---
## Agent signoff — [agent_name] — [date]
### What I tried
- (list of approaches attempted)
### What I did
- (list of concrete actions taken, files created/modified)
### What worked
- (successes, key results)
### What didn't work
- (failures, dead ends, things that need different approach)
### What's left
- (unfinished tasks, next steps for whoever picks this up)
### Key discoveries
- (anything surprising, format rules, data issues, strategic insights)
```
This is the agent's legacy — the next agent or Rain reads this to avoid repeating work and to build on discoveries.

### Why this matters
Without signoffs, findings die with the session. Without Role & Relevance in the prompt, agents don't understand WHY their work matters. Both are non-negotiable.

## CREDENTIALS RULE (revised 2026-05-29 — supersedes 2026-05-28 lock)

The 2026-05-28 incident: a classic PAT got embedded in multiple agent spawn prompts, multiplying its exposure across runtimes and execution traces. That is the specific failure mode the policy guards against — NOT all chat-based credential transfer.

Active rules:
1. **NEVER embed a PAT, API key, password, or any credential in a spawn prompt, an agent-to-agent message, or any file committed to the repo.** This is the 2026-05-28 lesson — still locked. If a future Claude (including me, claude_strategy) starts to embed a PAT in a spawn prompt: STOP. Violation.
2. **Rain MAY provide a PAT directly to a Claude in chat for use in that Claude's runtime.** Requirements on the token:
   - Fine-grained, repo-scoped (never classic `ghp_` tokens, which over-scope)
   - ≤7-day expiry
   - Rotate within 24 hours of session end
3. **When a Claude receives a PAT via chat**, it writes to `~/.git-credentials`, uses it for the session, NEVER re-displays the token, and NEVER embeds it in subsequent outputs (spawn prompts, commits, log dumps, etc.).
4. **Any token disclosed in chat is burned at session end.** Rotate.
5. **Spawn prompts say**: "Credentials are pre-configured in ~/.git-credentials by Rain (or by the parent Claude's setup step). If git push fails with auth error, REPORT — do NOT request a PAT in chat from another agent."

### Per-session credential workflow (the practical recipe)

For **chat-based Claudes** (e.g. claude_strategy in claude.ai, ephemeral sandbox):
- At session start, if write access is needed, Rain provides a fresh fine-grained PAT directly in chat.
- Claude writes it to `~/.git-credentials`, uses it for the session.
- Sandbox resets at session end; token rotated by Rain within 24h.

For **persistent runtimes** (claude_vscode, claude_thunder):
- One-time manual setup by Rain. Same fine-grained token requirements.

### PAT setup (run this once per runtime that needs write access)
```bash
git config --global credential.helper store
echo "https://dvaneetv:THE_FINE_GRAINED_PAT@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
git config --global user.email "dvaneetv@ucsd.edu"
git config --global user.name "claude_agent"
```

## GOLD-RULE (LOCKED SOP)

Anything labeled GOLD — a confirmed lever, a discovered format rule, an empirical finding, a ground-truth signal — must be documented in its canonical home the same session it's discovered. Folder map:

- Format / grader rules → `postprocessing/FINDINGS.md` (also update `NORMALIZATION_RULES.md` tier)
- Verified Wolfram answers → `data/search/wolfram/WOLF_LIST.md` and `MASTER_QUESTIONS.csv`
- Inference-config wins (per-run, per-config) → `inference/FINDINGS.md`
- Confirmed submission levers (with score-delta evidence) → `submission/REGISTRY.md`
- Conceptual gold (mental models, principles) → `strategy/HOW_WE_KNOW_CORRECTNESS.md` or a new strategy doc
- Cross-cutting / "I don't know where this goes" → the relevant folder's `SCRATCH.md` (Rain sorts later)

Agents that discover gold but don't document it have failed their session. Every spawn prompt closes with: "if you find gold, file it per GOLD-RULE before signing off."
