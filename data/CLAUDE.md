# data/CLAUDE.md — Data & Answer Sheet Agent

> **FIRST** (chat-based Claudes): run the one-command git bootstrap from root `CLAUDE.md` — `curl ... setup_git.sh | bash -s -- "PAT"`. Persistent runtimes are pre-configured. See root `CLAUDE.md` for the full snippet + CREDENTIALS RULE.

## Identity
You are a data agent for the CSE 151B Kaggle math competition. You build and maintain the unified answer sheet — the single source of truth for "what is our best answer for each of the 943 items?"

## Your task scope

## Role & Relevance

**Role**: Aggregate all evidence sources into unified data artifacts. Build and maintain the master answer sheet and the gold test set.
**Relevance**: Every other phase depends on clean, unified data. Without a single source of truth for "what is our best answer per item," agents make conflicting decisions.
**Techniques**: Multi-source aggregation (inference votes + teachers + Wolfram + search + back-solve), Bayesian answer sheet construction, anti-bias rules (exclude SFT-trained subs, dampen correlated submissions), MASTER_ANSWERS.csv maintenance.
**Inputs**: Inference results, teacher answers, Wolfram overrides, search gold, back-solve posteriors.
**Outputs**: MASTER_ANSWERS.csv (943×19 all-source matrix), unified_answer_sheet_v6.csv, gold_test_set.csv.
**Key lever**: A clean master table lets us answer the core questions (what's correct, what needs format fixing, what's adapter material) without re-deriving from scratch.
- Build the unified answer sheet (best answer + confidence per item)
- Aggregate evidence from all sources (inference, teachers, Wolfram, back-solve, search)
- Filter to 90%+ confidence items → gold test set for testing/
- Maintain the master item tracker

## Key files in this folder
- `answer_sheet/` — answer sheet outputs (unified_answer_sheet_v6.csv TO BUILD)
- `master_item_tracker.csv` — 943-row tracker with all per-item metadata
- `teacher_answers_compact.json` — 5 teacher model answers per item
- `wolfram_overrides.csv` — 63 Wolfram HIGH-confidence overrides
- `back_solve_detail.csv` — Bayesian per-item back-solve results
- `search/` — web search and Wolfram verification results
- `system_prompts/` — prompt templates used in inference
- `FINDINGS.md` — data-layer findings

## Build script
`submission/scripts/build_answer_sheet_v6.py` — canonical builder with full 20-entry submission registry.
Input: submission CSVs from `submission/csvs/` + submission scores from `submission/REGISTRY.md`.
Output: `data/answer_sheet/unified_answer_sheet_v6.csv`.

## Evidence sources (ranked by confidence)
1. **Web search verified** (5 items): IMO 2025 P6, Putnam 2021 A5, etc.
2. **Wolfram HIGH** (51 items): computational verification
3. **Multi-teacher unanimous**: all 5 teachers agree
4. **Qwen SC≥7/8**: strong self-consistency agreement
5. **Back-solve oracle**: Bayesian posterior from 24+ Kaggle submissions
6. **Single teacher**: one teacher only

## Output: Gold Test Set
Filter unified answer sheet to items with ≥90% confidence.
Output to: `testing/gold_test_set.csv`
This becomes the validation set for the test pipeline (Stage 1).

## Anti-bias rules (LOCKED)
1. Exclude SFT-trained submissions from sheet OR cap weight at 0.05
2. Dampen correlated same-model submissions via weight/√group_size
3. Leave-one-out cross-validation for per-submission accuracy

## Read these first
- `data/FINDINGS.md` — existing data findings
- `submission/REGISTRY.md` — all 29 submissions with Kaggle scores
- `strategy/TEST_PIPELINE.md` — how the gold test set feeds into the pipeline
- Root `CLAUDE.md` — universal rules (LFS, etc.)
