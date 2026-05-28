# OPERATION TIME MACHINE — Lost-Data Mining Backlog

**Purpose:** methodical one-shot sweep of early docs + run artifacts for un-consolidated gold.
Work top-down; each pass EXTRACTS to its phase-home (see `/PIPELINE.md`) and updates status.
**Doctrine:** 4 days left, ONE shot per item — mine it right the first time.
**Status:** `[ ]` unmined · `[~]` partially mined · `[x]` mined + homed
**Chronology note:** git-add dates are confounded (Day-5 reorg reset them; LFS pointers committed 5/27),
so ranking is by *content richness × unmined × current relevance*, NOT git date.

---

## TIER 1 — richest, mostly unmined — START HERE
1. `[ ]` **archive/research/prompt_engineering_research.md** — 70KB / 896L — UNMINED. Prompt-lever research; the V0–V4 prompts trace back here. → INFERENCE prompt levers + STRATEGY.
2. `[~]` **archive/design/experiments.md** — 85KB / 928L — the **Experiment Log**, run-by-run incl. failures. Only judger/public + Insights 6–7 pulled so far. → RUN_REGISTRY + knowledge layer.
3. `[ ]` **archive/session_logs/SESSION_LOG.md** — 14KB / 224L — UNMINED. Chronological log opening on the v1 3-arm SFT FAILURE. Dense failure postmortems — the "capture failed runs" ask. → RUN_REGISTRY / adapters.
4. `[~]` **archive/design/DESIGN.md** — 68KB / 1304L — design rationale, Piazza rulings, SFT paths, data-filtering. Only §4.4/§5.1 grepped. → RULES + INFERENCE + STRATEGY.

## TIER 2 — high, unmined research / specs
5. `[ ]` **archive/research/INFERENCE_OPTIMISATION_RESEARCH.md** — 19KB — "prophetic" doc (oracle@N, GenSelect, hard-item SC recommended early). → STRATEGY/LEVERS.
6. `[ ]` **research/prompts/2026-05-09_dive_v1.md** — 19KB — multi-agent research dive, production prompts. → prompt levers.
7. `[ ]` **archive/research/variants_and_prompts.md** — 10KB — implementation spec for the V-variants. → ties V0–V4.
8. `[ ]` **archive/research/papers.md** — 9KB — papers/tooling findings (SC, test-time verification, SFT lit). → STRATEGY/RESEARCH.

## TIER 3 — RUN ARTIFACTS (per-item gold; INCLUDES failed runs)
9. `[ ]` **V0–V4 fixed_50 runs** (V0/V1/V2/V3 ~6MB each + V4 partial+final) + 4 summaries — per-item SC on known-gold slice + variant deltas. → RUN_ANSWER_MATRIX / RUN_REGISTRY.
10. `[ ]` **Private-943 SC runs**: run08, **run09 (LFS)**, run10, **run14b ×3 (LFS)** — full-set per-item answers = oracle-harvest core. ⚠️ LFS → unlock via download_url, never partial-read.
11. `[ ]` **hybrid/**: nothinking_full_943 (44MB, **NEVER scored standalone** = free Kaggle diagnostic), sc16 weak128 / hardest30, targeted_rescue ×2, adapter_v5_run. → RUN_REGISTRY.
12. `[ ]` **Failed / diagnostic runs**: run03/04 (engine parity), run05/06/07 (fixed_50 SC), run11 + run13 (v2openr1 collapse → rp1.1 fix), **v2_numina_concise_50 (category-error FAIL)**, expA_perslot, sft_v4_adaptive/samples, no_box_rescue, slot1_wolfram_raw. → capture deltas/postmortems.

## TIER 4 — medium / partially mined
13. `[~]` **archive/handoffs/HANDOFF_v2.3.md** — 31KB — Sub A/B/C analysis, W-tier teacher advantage (+26.4%).
14. `[~]` **milestone_report.tex** — 16KB — formal vetted findings (3 SFT failure modes invisible to eval loss).
15. `[ ]` **archive/docs/CLAUDE_STRATEGY_RULES.md** — 4.3KB — UNMINED "Immutable Project Rules". → RULES.
16. `[~]` STRATEGY_DAY4_LOCKED / STRATEGY_0_85 / PLAN / wolfram-FINDINGS / data-FINDINGS — largely mined (see strategy/FINDINGS F8 index).
17. `[ ]` archive/docs/{PROJECT_STATE, WORKER_PROMPTS, ANSWER_SHEET, NEXT_ACTIONS, RESEARCH, RESEARCH_FINDINGS} — small state/process snapshots.

## TIER 5 — low (process / stubs / superseded) — skim or skip
COMPETITION.md (rules ref) · README_SUBMISSION · CLAUDE_HANDOFF_INSTRUCTIONS · SUBMIT_NOW · PIVOT · TODO_old · playbook_README (mined) · RESEARCH_PROMPTS_DAY3 · candidates_*_breakdown.md · UNTRACKED_*.md stubs.

## Logs — mine ON DEMAND when a specific run is investigated
infrastructure/logs/{V0–V4, run14b, genselect, overnight_queue}.log · inference/adapters/{sft_v1_postmortem, sft_v3, sft_v4, sft_v5}/logs/.
