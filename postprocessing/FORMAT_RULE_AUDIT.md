# Format Rule Audit

This file is the organizational bridge between scattered formatting evidence and the actual post-inference processor.

## Why this exists

Format-rule knowledge in this repo is not fully centralized yet.

The intended canonical home is `postprocessing/`, but actual evidence is distributed across:

- `grading/` for source-level grader behavior
- `submission/` for empirical leaderboard probes and failure analyses
- `COMPETITION.md` for official/staff competition guidance
- `research/` for source-corpus and evaluator comparisons
- `data/` for undercount and rescue candidate artifacts
- tests and helper code for implementation-level assumptions

The goal of this file is to keep that sprawl from turning into lost context.

## Recommended canonical structure

### 1. Master rule table

`postprocessing/FORMAT_RULE_REGISTRY.csv`

Use this as the structured source of truth for each rule candidate.

Each row should track:

- what the rule is
- where it applies
- whether it is confirmed, stale-risk, believed, disproved, or open
- why we suspect it
- all sources of evidence
- whether it is implemented and in which mode

### 2. Canonical grader behavior doc

`grading/GRADER_SPEC.md`

Use this for the old and source-derived grader model. It is still the strongest repo-local specification of extraction behavior and old normalization boundaries.

### 3. Tiered decision framework

`postprocessing/NORMALIZATION_RULES.md`

Use this to decide which rules belong in conservative/default/aggressive processing.

### 4. Processor design and implementation notes

`postprocessing/NORMALIZER_SPEC.md`

Use this for code-path design, mode semantics, CLI, fixtures, and implementation status.

### 5. Empirical submission evidence

`submission/REGISTRY.md` and `submission/AMBER_ALERT.md`

Use these for observed leaderboard effects and caveats in interpreting them.

## Where the post-inference processor should live

The processor code should stay in:

- `postprocessing/scripts/normalizer.py`
- `postprocessing/scripts/hendrycks_local.py`
- `postprocessing/scripts/evaluate_normalizer.py`

That is the right home because the processor belongs to the post-inference phase, not submission management or grading research.

## Where design notes from the last prompt should live

They should not live in chat history only.

They should be recorded in:

- `postprocessing/NORMALIZER_SPEC.md` for design and mode behavior
- `postprocessing/FORMAT_RULE_REGISTRY.csv` for rule-level evidence
- `postprocessing/FORMAT_RULE_AUDIT.md` for repo-wide organization and inconsistency tracking

This session's work should be treated as part of that canonical set.

## Ranked current canonical docs

1. `grading/GRADER_SPEC.md`
2. `grading/GRADER_RESEARCH.md`
3. `postprocessing/NORMALIZATION_RULES.md`
4. `postprocessing/STRICT_NORMALIZER_SPEC.md`
5. `postprocessing/FORMAT_RULES.md`
6. `submission/REGISTRY.md`

## Where rule knowledge is currently scattered

### Strong but scattered sources

- `submission/AMBER_ALERT.md`
- `submission/SUBMISSION_FORENSICS.md`
- `submission/SCRATCH.md`
- `postprocessing/FINDINGS.md`
- `research/FORMAT_CONVENTIONS.md`
- `COMPETITION.md`
- `judger.py`
- `grading/JUDGER_AND_PUBLIC_SET.md`
- `utils.py`

### Why this matters

Some of the most valuable facts are currently split by evidence type instead of by decision use:

- source-code truth in `grading/`
- empirical score movement in `submission/`
- rule candidates in `postprocessing/`
- evaluator drift and source routing in `research/`

That is workable for archaeology but bad for endgame iteration.

## Current inconsistencies and stale-risk items

### Old grader model vs new judge update

The biggest unresolved inconsistency is this:

- older repo docs assume Kaggle grader is effectively strict Hendrycks string matching
- the user-provided competition announcement says the judge was updated two days ago to fix fraction/decimal mismatches and similar false negatives
- the current `judger.py` is clearly more adaptive and sympy-backed than the old Hendrycks-only model

Practical conclusion:

- structural rules remain high confidence
- some numeric surface rules must be downgraded from "confirmed lever" to "stale-risk until revalidated"

Affected rules include at minimum:

- decimal vs fraction preference
- trailing-zero significance
- wrapper stripping
- possibly some label and expression-surface mismatches

### Structural rules remain robust

These are still the cleanest high-confidence rules even under the judge-update uncertainty:

- MCQ first-box extraction
- free-form last-box extraction
- single-box multi-answer formatting
- preserving multi-answer order
- multi-slot undercount recovery

### Known stale or scattered claims

- Some older docs outside `grading/GRADER_SPEC.md` still phrase the grader as if it reads all boxes or is multi-box tolerant.
- Several files still discuss fraction-vs-decimal as a hard old-grader fact without flagging the possible May 2026 judge update.
- `postprocessing/FORMAT_RULES.md` mixes per-item leads with still-open assumptions and needs the registry as its structured companion.

## Recommended working policy for the last 3 days

### Safe default

Focus on structural fixes first.

### Medium-confidence handling

Keep numeric surface rewrites behind explicit mode gates or per-item evidence.

### Documentation discipline

Any new claimed rule should be added to `postprocessing/FORMAT_RULE_REGISTRY.csv` before it is treated as real.

### Submission discipline

Do not spend remaining submissions on generic format fishing if a rule is only old-doc-confirmed and now stale-risk under the new judge update.

## Highest-EV TA question

If you ask exactly one question, I would ask this:

"After the recent Kaggle judge update, which answer-surface mismatches are still not normalized at grading time? In particular: decimal vs fraction, trailing zeros, large-number commas, labeled prefixes like Mean=228, and multi-answer delimiter/order issues."

Why this is highest EV:

- it collapses the biggest uncertainty introduced by the update
- it directly tells us which old rules are still worth spending submission budget on
- it distinguishes structural failures from now-fixed numeric-surface failures

## Maintenance rule

Going forward:

1. Put every new rule candidate in `postprocessing/FORMAT_RULE_REGISTRY.csv`.
2. Put implementation or mode changes in `postprocessing/NORMALIZER_SPEC.md`.
3. If a claim contradicts current grader behavior, note it here in the audit before changing canonical specs.
