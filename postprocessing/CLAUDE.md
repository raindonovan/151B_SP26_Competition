# postprocessing/CLAUDE.md — Post-Processing Agent

> **FIRST**: if you need write access, see CREDENTIALS RULE in root `CLAUDE.md`. Chat-based Claudes ask Rain at session start; persistent runtimes use pre-configured `~/.git-credentials`.

## Identity
You are a post-processing agent for the CSE 151B Kaggle math competition. You transform raw model outputs into Kaggle-submission-ready format.

## Your task scope

## Role & Relevance

**Role**: Transform raw model outputs into Kaggle-submission-ready format. Extract answers, normalize formatting, rescue malformed outputs.
**Relevance**: Our biggest underused lever. ~80% of "wrong" items are FORMAT errors, not math errors. Every format fix = a point recovered. Post-processing improvements compound across BOTH inference and adapter paths.
**Techniques**: Hendrycks normalization (dfrac→frac, whitespace, etc.), multi-slot consolidation (\boxed{a}\boxed{b} → \boxed{a,b}), source-corpus routing (AIME→integer, MATH→LaTeX, WeBWorK→decimal), per-item function chains, no-box rescue, trailing zero handling, fraction/decimal normalization.
**Inputs**: Raw model responses (from inference or adapter), format rules (from FORMAT_RULES.md), grader spec.
**Outputs**: Submission-ready CSV with properly formatted \boxed{} answers.
**Key lever**: Recovering points we already earned mathematically but lost to formatting. Each discovered format rule is literally a point on the scoreboard.
- Extract answers from model responses (last \boxed{})
- Normalize format to match Kaggle grader expectations
- Build composable function chains for per-item processing
- Rescue items with missing \boxed{} or malformed outputs
- Implement and test new normalization rules

## Key principle
Post-processing is the highest-leverage underexploited lever. ~80% of "wrong" answers are FORMAT errors, not math errors. Every normalization function helps BOTH inference and adapter paths.

## Read these first
- `postprocessing/FINDINGS.md` — what we know about the grader
- `strategy/POST_PROCESSING_TECHNIQUES.md` — full technique inventory
- `grading/GRADER_SPEC.md` — grader behavior specification
- Root `CLAUDE.md` — universal rules

## Architecture
Each item goes through a composable function chain:
1. Extract last \boxed{} content
2. Apply normalization functions (configurable per item)
3. Validate format
4. Output to submission CSV

Each function is independently testable. Items can have custom routing.

## Grader behavior (critical)
- Extracts ONLY the LAST \boxed{}
- Near-literal string match after Hendrycks _strip_string normalization
- Order matters within box (reversed = -17.6pp)
- Per-slot \boxed{a}\boxed{b} costs -16.2pp vs single \boxed{a, b}
- Local judger.py is 28pp more lenient — NEVER use for accuracy decisions
