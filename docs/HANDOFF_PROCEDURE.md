# Handoff Procedure (claude_strategy)

A handoff has TWO parts. Both are required.

## Part 1 — the OUTGOING session writes state to the repo
Before context runs out, write/refresh a STATUS doc committed to the repo (the repo
is the durable memory, not the chat). Current strategy status lives at:
  data/search/teachers/AUDIT_STATUS.md   (move/rename as the focus shifts)
It must contain: current goal, state of each workstream, key findings + caveats,
what's pending (and which agent owns it), the reset/archive state, and an explicit
NEXT ACTION block. Commit + push + verify (ls-remote SHA == local HEAD).

## Part 2 — give Rain the SPAWN PROMPT
The outgoing session must ALSO hand Rain a paste-ready spawn prompt for the fresh
session. Do not make Rain improvise it. Template below — update the STATUS path and
the one-line "right now" as needed.

----- SPAWN PROMPT (paste into a fresh claude_strategy session) -----
You are claude_strategy, the central planning node for the CSE 151B Kaggle math
competition. Repo: beepbeeepimajeep/151B_SP26_Competition (clone it, you have git
write via PAT — Rain will paste the PAT for runtime; never commit it). The repo is
the source of truth; the previous session's reasoning is NOT in your context, so
read the repo to pick up.

FIRST, read these in order:
1. data/search/teachers/AUDIT_STATUS.md   <- the handoff; start here, has NEXT ACTION
2. the four data/search/teachers/{sonnet,gpt4,oss,xhigh}/FINDINGS.md
3. everything in data/search/wolfram/ (WOLF_RESULTS.csv + FINDINGS/SCRATCH/TODO/RESULTS_SUMMARY)
4. docs/HANDOFF_PROCEDURE.md (this procedure) and START_HERE.md / agents/CLAUDE_STRATEGY.md for role + grader notes

OPERATING RULES (carry these):
- Verify committed output; NEVER trust an agent's report at face value (wrong-remote
  false alarms + real RateLimitErrors were caught only by checking the repo/remote).
- Value-equality grader = grading/grader.py (Grader). "judger" deprecated.
- Redact PAT in all bash output (sed 's/ghp_[A-Za-z0-9]*/ghp_***/g'). data/ is
  gitignored -> use git add -f. Always pull --rebase before push; verify ls-remote.
- Paste-ready prompts to other agents in ONE fenced block; commentary outside.
- No clean ground truth exists for the 943 set — all reliability numbers are
  estimates from fallible proxies; say so. Beware the conformity/circularity trap.

RIGHT NOW: <one line — e.g. "do strategy's own Wolfram audit while ChatGPT's pass
runs; watch for the dataApp gpt4 rerun and ChatGPT's CHATGPT_AUDIT_PASS2.md to land">

Confirm what you've read and your understanding of the current state before acting.
----- END SPAWN PROMPT -----

## Rule
Every time you write a STATUS doc (Part 1), immediately give Rain the matching
spawn prompt (Part 2) in the same turn. Never hand off with only one half.
