# POST_COMP_SCRATCH.md

> Ops (attribution, append rules, debrief procedure): **`post_comp/README.md`**

## Purpose

This is the shared scratchpad for all post-competition work.

Use this file for rough notes, partial thoughts, todo lists, debrief fragments, portfolio ideas, research directions, job-search angles, meeting notes, and anything else that belongs to the post-competition phase but does not yet have a polished home.

**Narrative lock:** When promoting material to portfolio, case study, or public docs, frame **we won** (winning path: `30_05_slot4_aggressive_v2`, 0.745/0.684 per `submission/REGISTRY.md`). Do not carry late-submission or Kaggle pick-selection narratives into polished post-comp output.

Do not overthink placement. If it is about what happens after the competition, put it here first. Later, promote useful material into more structured documents (win-forward).

## Attribution Rule

Every entry must say who wrote it.

Use one of these tags at the start of each entry:

- `[Rain]`
- `[Cursor]`
- `[Claude]`
- `[Other: name]`

When Cursor writes here, Cursor should label the entry `[Cursor]`.
When Claude writes here, Claude should label the entry `[Claude]`.

## How To Use

Append new notes under `Scratch Entries`.

Suggested format:

```text
---
## [Cursor] 2026-06-03 — short title
- note
- todo
- question
```

This file is intentionally informal. It is allowed to be messy.

## Things To Source From This Scratchpad Later

- Post-competition debrief agenda
- Portfolio case-study sections
- Blog post outline
- Research questions
- Resume bullets
- Website visuals
- System improvement plan
- Agent workflow lessons
- Future competition operating procedure
- Startup → **`POST_COMP_STARTUP_SCRATCH.md`** (see **`POST_COMP_STARTUP_README.md`**)

## Scratch Entries

---
## [Cursor] 2026-06-03 — Post-Competition Phase Kickoff

Rain wants the post-competition phase to turn the **win** into durable value:

- document the winning inference/postproc path and operating system
- explain agents, GPU boxes, red-team loops, submission discipline, and evidence cycles
- plan tooling upgrades for the next competition or product
- convert the experience into portfolio, job-search, research, and next-stage roadmap (see debrief Goal 7)

Key reminder: lock the "indication of effort" discussion into docs. Candidate artifacts include git activity heatmaps, commit timelines, score-over-time plots, subsystem effort maps, and final sprint timelines.

---
## [Rain] 2026-06-03 — Student competition strategy (canonical)

Full ranked next-competition plan logged in **`post_comp/COMPETITION_TARGETS.md`**.

- **Now:** Mega Agent-A-Thon (Jun 4–14) + ICML AI4Math Codabench track (~Jun 15)
- **Watch:** AIMO Progress Prize 4 (same game as 151B; multi-week sprint when it drops)
- **Paper lane:** INFORMS DMS Best Student Paper (submit Jun 30)
- **Optional:** USAII undergrad hackathon (Jun 21) if productized
- **Deprioritize:** ARC Prize, AIMO3-scale Kaggle, AIXDATA (past), human-only exams

---
## [Rain] 2026-06-04 — Career bridge (canonical)

See **`post_comp/CAREER_BRIDGE.md`**.

---
## [Rain] 2026-06-04 — NoThinking / 151B paper — external validation (GOLD)

**Quote (independent confirmation):** "The field independently confirmed truncation + thinking-length as the core failure axes, and that inference-time scaling beats SFT on this model — direct support for your token-budget findings."

**Repo tie-in (win-forward safe):** Canonical win remains `30_05_slot4_aggressive_v2` (0.745/0.684); this validates the *mechanism* narrative (inference OS, token budgets, SC) filed in `inference/FINDINGS.md` and R20 audits (`inference/SCRATCH.md` L338), not a revised pick story. SFT ceiling vs inference: `strategy/INFERENCE_TECHNIQUES.md` L9–L13; debrief inference-first: `post_comp/POST_COMP_DEBRIEF_MEETING.md` L57–L63. Paper draft artifact: `gradescope/milestone_report.tex` (SFT pathology + inference-time levers). INFORMS lane deadline Jun 30 per entries above.
