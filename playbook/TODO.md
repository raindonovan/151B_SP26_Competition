# PLAYBOOK TODO

**Updated**: 2026-05-28 Day 4 EOD
**Note**: PLAYBOOK-specific TODO for the 0.85 push. Canonical project TODO at `docs/TODO.md`.

## THIS SESSION (immediate)

Per Rain's 5-priority directive: organize docs + analyze unanalyzed + squeeze every 0.01pp from existing repo (NO new inferences, NO new builds).

- [x] Restructure playbook/runs/ to one-folder-per-run with findings.md inside
- [x] Move OPL findings into `playbook/runs/opl_run/`
- [x] Move GenSelect findings into `playbook/runs/genselect_poc_run/`
- [x] Move SFT v5 findings + Rain's targeted-memorization insight into `playbook/runs/sft_v5_run/`
- [x] Delete `playbook/POSTMORTEMS.md` (replaced by per-run findings)
- [x] Rename `docs/SUBMISSIONS_TODO.md` → `docs/TODO.md` (canonical)
- [x] Update LEVERS.md with rules constraints (TIR killed, PRM killed, Lever 6 added)
- [ ] Update memory with rules constraints
- [ ] Begin analysis of one unanalyzed run from the backlog (next session)

## P0 — Day 5 morning (cheap free-info on existing data, no new inference)

- [ ] **Oracle@8 analysis on run14b** — for each of 943 items, does ANY of the 8 SC samples match gold proxy? Tells us ceiling for Lever 3 (selection).
- [ ] **Score NoThinking SC=8 full-943 standalone** via Kaggle slot — free diagnostic anchor (45MB exists, never scored)
- [ ] **Analyze hardest-30 SC=16 results** (`results/hybrid/tnr-A/`) — check if any new correct answers we don't have
- [ ] **Re-analyze GenSelect PoC** — count items where correct was in pool but selector picked wrong + truncation correlation
- [ ] **Build multi-slot expander** from `results/undercount_candidates.csv` 51 use_teacher items — apply to existing submission for one Kaggle test

## P1 — Day 5-6 (squeeze remaining juice from existing data)

- [ ] Map answer sheet T-tier coverage across 943 items (using new T1-T5 naming)
- [ ] Identify items that have HIGH-T answers but Qwen is wrong — these are the override-target pool for Day 7
- [ ] Compute "what would Pick A score be" if we trust T1+T2 answer sheet on items where Qwen disagrees (without applying — diagnostic only)
- [ ] Confirm sft/v4 trace composition (currently unknown — read sft/v4/ folder)

## P2 — Day 6-7 (commit one big lever)

- [ ] Decide between Lever 6 (Targeted Memo SFT) vs Lever 3 (GenSelect re-run) based on P0/P1 findings
- [ ] Execute chosen lever
- [ ] Submit best result + Pick B with overrides

## P3 — Final submission

- [ ] Code submission to Gradescope by Sun 2026-05-31
- [ ] Final 2 Kaggle picks by ~2026-06-02

## RESEARCH QUEUE (held — Rain to approve dispatch)

- [x] ~~R1 (TIR feasibility)~~ — KILLED by rules
- [ ] R2 — REVISED: skip PRM (rules) → ask about "single-model judge prompt design for math BoN selection"
- [ ] R3 — Targeted Memorization SFT precedents: who has trained adapters on small held-out datasets and used them selectively at inference?
- [ ] R4 — GenSelect with full-length candidates: implementation patterns from NVIDIA NemoSkills AIMO-2 winner

## OPEN QUESTIONS FOR RAIN

1. Is multi-slot expansion using `undercount_candidates.csv` teacher consensus considered an "override" (off-table until Day 7) or "post-processing" (allowed)?
2. Approve Lever 6 (Targeted Memorization SFT) scoping work?
3. Approve dispatch of R3/R4 research prompts (R1 dead, R2 revised)?
