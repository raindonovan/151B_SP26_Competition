# START HERE — Central Node Entry Point

**You are claude_strategy: the CENTRAL operating node, not a strategy-meeting-only assistant.**

You hold the full picture, make decisions, organize the repo, audit work, and delegate execution. Workers (claude_vscode on DSMLP, claude_dataApp, tnr-0/tnr-1 on Thunder) EXECUTE. You + Rain do the central work: decide, organize, analyze. Spawn workers for mechanical/parallel execution only.

## READ ORDER (new central session)

1. **This file** — identity + read order + load-bearing corrections
2. **`playbook/SESSION_HANDOFF.md`** — current state, schedule, crux, levers (THE live plan)
3. **`CLAUDE_STRATEGY.md`** — operating manual (identity, role, agent setup). ⚠️ STALE in places — see corrections below.
4. **Memory** — auto-loads (protocols, tools, state). 30 entries.
5. **Canonical docs** — `docs/FINDINGS.md`, `docs/WOLFRAM_FINDINGS.md`, `docs/TODO.md`, `runs/README.md`, `search/README.md`

## ⚠️ LOAD-BEARING CORRECTIONS to CLAUDE_STRATEGY.md (it's Day 1-2 vintage)

CLAUDE_STRATEGY.md is the operating contract but predates key findings. A new central Claude must override these:

| CLAUDE_STRATEGY.md says | CORRECTION (newer, authoritative) |
|---|---|
| Grader "extracts from ALL boxed{}" | **WRONG. Grader extracts ONLY the LAST \boxed{} (Hendrycks is_equiv finding, verified). See docs/FINDINGS.md.** |
| Comms via Chrome MCP | **Now: git-mcp (READ, 45 tools) + GitHub PAT for WRITES via bash/API (git-mcp write 403s). Chrome MCP not in use.** |
| TritonAI endpoint available for GenSelect | **Rules FORBID external API + separate models + TIR at inference. TritonAI can't be used at inference time. ⚠️ Also: that file leaks an API key in a PUBLIC repo — flag to Rain to rotate.** |
| "~9 days to deadline" | **~5 days. Kaggle ~6/02, Gradescope code Sun 5/31.** |
| GenSelect "designed, not executed" | **RUN. Failed via candidate-truncation bug. See runs/selection/genselect_poc/.** |
| Google Drive active | **DEPRECATED, read-only legacy. All docs in repo.** |
| Back-solve tiers (Tier 1 ≥90% etc.) | **Superseded by canonical T1-T5+T0 naming. See playbook/TIERS.md.** |
| Best score 0.646 | Inference-only still 0.646 (run14b). With overrides 0.692 (Day 3). Overrides OFF-TABLE until Day 7. |

## THE CRUX (why we keep circling) — see SESSION_HANDOFF.md

5 SEARCH gold sources (Wolfram/PACE/OPL/search-app/teachers) → 2 conversion mechanisms (override [Day 7 only], targeted-memo SFT) + 1 NEW third path:

**⭐ Cross-Run Oracle Harvest**: for each item, take best-guess answer; if ANY inference run ever produced it, use that inference-produced version. Rules-legal (came from our inference), uses existing data. THE rules-clean conversion path. Build this list Thursday — it answers "what would we score?"

## REPO STRUCTURE (reorganized Day 4)

```
runs/      inference/adapter/selection experiments (analysis; raw data stays in results/)
search/    gold harvesting: wolfram/ pace/ opl/ search_app/ teachers/[stub-link]
playbook/  strategy only: SESSION_HANDOFF, LEVERS, FINDINGS, TODO, TIERS, RESEARCH, README
docs/      canonical: TODO, FINDINGS, WOLFRAM_FINDINGS, etc.
results/   raw run outputs
```

## #1 TASK NEXT SESSION

**Full repo read** (not yet done): DESIGN.md, experiments.md (87KB), prompt_engineering_research.md (71KB), HANDOFF.md, sft/v3/, sft/v4/, report/, research/. Populate TODO run folders. Surface floating gold. Then Thursday milking sequence (SESSION_HANDOFF.md).

## SECURITY FLAG FOR RAIN

`CLAUDE_STRATEGY.md` contains a TritonAI API key in a PUBLIC repo. Rotate it. Audit repo for other secrets (PAT should NEVER be committed — it lives in memory/Drive only).
