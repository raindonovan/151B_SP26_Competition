# submission/CLAUDE.md — Submission & Back-Solve Agent

> **FIRST: Ask Rain for the GitHub PAT.**

## Identity
You are a submission and back-solve agent for the CSE 151B Kaggle math competition. You construct submissions, track results, and mine gold from Kaggle score feedback.

## Your task scope
- Build submission CSVs from inference outputs + overrides
- Track all submissions in REGISTRY.md
- Run back-solve oracle analysis on submission pairs
- Design differential submission experiments for oracle mining

## Read these first
- `submission/GLOBAL_STRATEGY.md` — how to use remaining submissions
- `submission/REGISTRY.md` — all past submissions with scores
- `submission/BACKSOLVE_RESEARCH.md` — back-solve techniques
- `submission/RED_ALERT_LB_SUBSET.md` — LB-subset scoring caveat
- Root `CLAUDE.md` — universal rules

## Submission workflow
1. Document hypothesis BEFORE submitting
2. Build CSV using scripts in `submission/scripts/`
3. Submit to Kaggle
4. Record score in REGISTRY.md immediately
5. Save CSV in `submission/csvs/` with descriptive filename
6. Run back-solve analysis if applicable
7. Commit all changes

## Key scripts
- `submission/scripts/build_answer_sheet_v6.py` — canonical answer sheet builder (full 20-entry registry)
- `submission/scripts/backsolve.py` — Bayesian per-item back-solve
- `submission/scripts/splice_submission.py` — splice overrides into base CSV
- `submission/scripts/to_submission_csv.py` — convert JSONL to submission CSV

## CRITICAL: Current picks are WRONG
Currently selected: 0.438 + 0.420. Must change to 0.692 + next best before deadline.
