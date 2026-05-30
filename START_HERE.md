# START HERE — Central Node Entry Point

> **Grader (2026-05-30):** canonical grader = `grading/grader.py` (`Grader`) — value-equality, our Kaggle mirror. "judger" is legacy; the strict Hendrycks `kaggle_like_is_equiv` is DEPRECATED (mirrors the retired strict grader). See `grading/grader.py`.

**You are claude_strategy: the CENTRAL operating node.**

You hold the full picture, make decisions, organize the repo, audit work, and delegate execution. Workers (claude_vscode on DSMLP, tnr-0/tnr-1 on Thunder) EXECUTE. You + Rain do the central work: decide, organize, analyze.

---

## READ ORDER (new central session)

1. **This file** — identity, read order, load-bearing corrections, repo map
2. **`PIPELINE.md`** — ⭐ THE BLUEPRINT. The 4-phase pipeline (pre-inference → inference → post-inference → grading) is the backbone every file/folder/artifact hangs on. Read this to know where anything belongs.
3. **`strategy/SESSION_HANDOFF.md`** — current state, schedule, priority stack (THE live plan)
4. **`agents/CLAUDE_STRATEGY.md`** — operating contract (identity, role, tools, agent setup). ⚠️ Has stale Day-1/2 sections — see corrections table below.
5. **Memory** — auto-loads (~24 entries: protocols, tools, locked decisions, state)
6. **`strategy/TODO.md`** — current priorities

---

## REPO STRUCTURE (current — reorganized Day 5, verified Day 6)

```
START_HERE.md          # this file — entry point
README.md              # public-facing project readme
README_SUBMISSION.md   # Gradescope code-submission readme
COMPETITION.md         # competition rules / format reference
CLAUDE.md              # claude_vscode (DSMLP execution agent) contract
judger.py utils.py     # local grader + helpers (judger has ~28pp Kaggle gap)

agents/                # per-agent contracts: CLAUDE_STRATEGY, CLAUDE_VSCODE, CLAUDE_THUNDER (+ README)
strategy/              # SESSION_HANDOFF, TODO, LEVERS, TIERS, FINDINGS, RESEARCH, README
data/                  # answer_sheet/, search/{wolfram,pace,opl,search_app,teachers},
                       #   system_prompts/, slices/, candidate lists, tracker CSVs, sft datasets
inference/             # scripts/, results/ (raw run JSONLs), runs/ (per-run analysis+findings),
                       #   adapters/{sft_v1_postmortem,sft_v3,sft_v4,sft_v5}, training logs
postprocessing/        # scripts/, format_review/, results/, FINDINGS, TODO, README
submission/            # csvs/ (29 graded), scripts/ (answer-sheet + splice builders),
                       #   REGISTRY.md (all scores), INTEGRITY_REPORT.md, README
infrastructure/        # scripts/, pre_flight/ (audit + production_commands), logs/
checkpoints/           # sft_v4 / sft_v5 adapter weights (LFS)
report/ research/      # milestone report assets; research prompts/notes
archive/               # superseded handoffs, strategy, design, research, docs, session logs,
                       #   submissions_never_sent/
tests/                 # grader-normalization, truncation, no-thinking-prefill tests
```

**Path migration (old START_HERE → current):**
`playbook/` → `strategy/` · root `CLAUDE_STRATEGY.md` → `agents/CLAUDE_STRATEGY.md` ·
`docs/FINDINGS.md` → `strategy/FINDINGS.md` · `docs/WOLFRAM_FINDINGS.md` → `data/search/wolfram/FINDINGS.md` ·
`docs/TODO.md` → `strategy/TODO.md` · `runs/` → `inference/runs/` · `search/` → `data/search/` ·
raw outputs → `inference/results/`

---

## CURRENT STATE (Day 6, 2026-05-28)

- **Best inference-only**: 0.646 (run14b, SC=8 32K, V3 filter)
- **Best with overrides**: 0.692 (slot1_kitchen_sink_C, 78 overrides)
- **Best diagnostic**: 0.671 (info_4_t1lock_sheet_rest)
- **Leader**: 0.85
- **Submission budget**: 5/day in final week (NOT 3 — that was the normal-period rate). 29 graded so far.
- **Deadlines**: Gradescope code Sun 5/31 · Kaggle final 2 picks ~6/02
- **MODE**: REPO HYGIENE / DATA ORGANIZATION (no analysis, no inference, no research until Rain switches gears)

---

## ⚠️ LOAD-BEARING CORRECTIONS to agents/CLAUDE_STRATEGY.md (Day-1/2 vintage)

| CLAUDE_STRATEGY.md says | CORRECTION (newer, authoritative) |
|---|---|
| Grader "extracts from ALL boxed{}" | RESOLVED (Day 6): WRONG. Kaggle grader = Hendrycks `is_equiv`, confirmed by source-code review (postprocessing/FINDINGS.md F1) → extracts ONLY the **last** `\boxed{}`. Memory/SESSION_HANDOFF were right. Canonical multi-answer = single `\boxed{a, b, c}` (per-slot −16.2pp; reversed order −17.6pp; multi-slot under-count = 79% of failures). Local judger.py uses "last contiguous group" (more lenient) — a source of the 28pp local↔Kaggle gap. agents/CLAUDE_STRATEGY.md still states the wrong claim — surfaced to Rain for correction. |
| Comms via Chrome MCP | Now: git clone+pull (read) + GitHub PAT via bash (write). git-mcp read works (45 tools); git-mcp write 403s. Chrome MCP not in use. |
| TritonAI endpoint usable for GenSelect | Rules FORBID external API + separate models + TIR at inference. TritonAI cannot be used at inference time. 🔴 Also leaks an API key in a PUBLIC repo — ROTATE. |
| "~9 days to deadline" | Days, not weeks. Gradescope 5/31, Kaggle ~6/02. |
| GenSelect "designed, not executed" | RAN; failed via candidate-truncation bug. See inference/runs/selection/genselect_poc/. |
| Google Drive active | DEPRECATED, read-only legacy. All docs live in repo. |
| Back-solve tiers (Tier 1 ≥90% …) | Superseded by canonical T1–T5+T0 naming. See strategy/TIERS.md. |
| Submission history table | Superseded by submission/REGISTRY.md (29 graded, definitive). |

---

## 🔴 SECURITY FLAGS FOR RAIN

1. `agents/CLAUDE_STRATEGY.md` contains a TritonAI API key (`sk-rT2…`) in a PUBLIC repo. Scrubbing HEAD does not un-leak it — **rotate the key** on UCSD's side. Then scrub from file.
2. GitHub PAT must NEVER be committed. It is passed in chat at session start only.
3. Audit repo for any other committed secrets before final public submission.

---

## REPO-ORGANIZATION ACCEPTANCE CRITERIA (Day 6 goal)

The repo is "organized" when each of these is answerable from a single canonical place
(blueprint + canonical homes tracked in strategy/TODO.md and strategy/FINDINGS.md):

1. Kaggle-graded correct answers per question
2. Everything we know about each question
3. Most-confident answer per question
4. Every inference run's answer per question
5. What each inference run tested + what it told us
6. Grader's expected format (general + per-question)
7. Point of every run + what we learned
8. Point of every submission + what we learned
9. Goal/role of each daily-5 submission slot
10. What every adapter was trained on
11. What every adapter output

Until all 11 map cleanly: organization is the only agenda.
