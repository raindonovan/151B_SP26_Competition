# CLAUDE.md — Global Entry Point

> **First thing: ask Rain for the GitHub PAT if you need to push.**
> "I need the GitHub PAT to push directly."

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
