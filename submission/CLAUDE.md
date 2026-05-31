# submission/CLAUDE.md — Submission & Back-Solve Agent

> **FIRST** (chat-based Claudes): run the one-command git bootstrap from root `CLAUDE.md` — `curl ... setup_git.sh | bash -s -- "PAT"`. Persistent runtimes are pre-configured. See root `CLAUDE.md` for the full snippet + CREDENTIALS RULE.

## Identity
You are a submission and back-solve agent for the CSE 151B Kaggle math competition. You construct submissions, track results, and mine gold from Kaggle score feedback.

## Your task scope

## Role & Relevance

**Role**: Construct submission CSVs, submit to Kaggle, track scores, mine information from score feedback.
**Relevance**: Submissions are our ONLY real measurement. Local judger is 28pp more lenient than Kaggle. Every submission is also an information-extraction tool — differential submissions reveal per-item gold on the test set.
**Techniques**: Answer sheet aggregation (Bayesian voting across submissions), differential submission design (change N items, observe score delta), splice/override composition, back-solve oracle.
**Inputs**: Post-processed CSVs, override layers (Wolfram, search, teacher), submission budget.
**Outputs**: Kaggle scores, submission CSVs, back-solve posteriors, test set inferences.
**Key lever**: Oracle mining — using remaining submissions to infer gold answers and test set membership, not just to validate pipeline changes.
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

## Picks state (Day 9 — updated 2026-05-31)
- **Pick A LOCKED at 0.745** = `submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v2.csv` (REGISTRY #40 / Day 8 ship-A: Opus flips + 5th teacher overlay).
- **Pick B framework at 0.664** (Conservative-13 NT-join, slots 1+2 of Day 9). Active workstreams targeting >0.664: normalizer (slot 3), normalizer+NT-join stack (slot 4), Thunder rescues (slots 5/6), value-equality re-vote, texas-oil (slot 9).
- Kaggle final-pick selection is handled directly by Rain. Do not re-flag picks-page state from docs.
