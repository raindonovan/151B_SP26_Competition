# CLAUDE HANDOFF INSTRUCTIONS

Read this FIRST when Rain bootstraps a fresh claude_strategy chat.

## Primary source of truth: this repo

All authoritative docs now live in `docs/` in the repo (`beepbeeepimajeep/151B_SP26_Competition`).
I can read them via git-mcp and write/update them directly via GitHub PAT.

**At session start, read in this order:**
1. `docs/CLAUDE_HANDOFF_INSTRUCTIONS.md` (this file)
2. `docs/CLAUDE_STRATEGY_RULES.md`
3. `docs/PROJECT_STATE.md`
4. `docs/NEXT_ACTIONS.md`
5. Drive SECRETS doc (id `1_9ynCvp2G5Z3yCkJ47pnM-bkfwwrhzv2`) for GitHub PAT — enables direct repo writes

Then output to Rain:
- One-line current state
- Next 3 actions
- Contradictions or stale info
- Confirmation of multi-agent setup

WAIT for Rain to confirm before doing anything.

## Writing to the repo (new capability)

GitHub PAT is in Drive SECRETS doc. Once loaded, writes via bash_tool:
```bash
python3 -c "
import base64, json, urllib.request
PAT = '<from SECRETS>'
REPO = 'beepbeeepimajeep/151B_SP26_Competition'
# ... write logic (see SECRETS doc for full template)
"
```

## Updating docs

To update any doc in `docs/`:
1. Read current content + SHA via git-mcp
2. Draft updated content
3. Write via GitHub API with the SHA
4. Commit message: `docs: refresh {DOCNAME} {YYYY-MM-DD}`

No more Drive create-new + flag-old dance. Edit in-place.

## Folder IDs (legacy Drive — read only, no longer primary)

- Handoff folder: `1lkRmVmCUOEfTnwGLRr3kI4SBYuFAe6kv`
- Wolfram batches: `1RaYGp8El80waS-_xSnvZrwPP7h_-IdkO`
- Parent folder: `14ntQe56m_ufIPyDk_Cs-sPjSESQ1NRZ8`
- SECRETS doc: `1_9ynCvp2G5Z3yCkJ47pnM-bkfwwrhzv2`

## Multi-agent windows

| Window | Role | Identity guard |
|---|---|---|
| claude_strategy (this chat) | plan / audit / teach | n/a |
| claude_vscode (DSMLP) | execution on raindonovan tunnel | auto-loads CLAUDE.md |
| claude_thunder tnr-0 | production GPU runs | `~/.instance-role` = "tnr-0" |
| claude_thunder tnr-1 | production GPU runs | `~/.instance-role` = "tnr-1" |

## What NOT to do

- Don't create new Drive doc versions for every state update — write directly to repo
- Don't paste recent chat exchanges into a new chat — the docs are the contract
- Don't pre-queue prompts for agents — one at a time, deliver when needed
- Always include STATUS BOARD at end of every response (no exceptions)
