# postprocessing/ — Stage 3: Post-Inference Processing

Deterministic transforms applied AFTER model output, BEFORE submission. Rules-legal.

## Contents
- `scripts/` — format fix, multi-slot expansion, grader normalization
- `format_review/` — per-item format review data and candidates
- `TODO.md` — untried format levers
- `FINDINGS.md` — Hendrycks grader analysis, format failure taxonomy
- `DECISIONS.md` — locked post-processing decisions

## Key facts
- Grader: Hendrycks is_equiv (string match after normalization)
- Dominant failure: multi-slot under-count (79% of wrong items)
- Trailing-zero strip: PROVEN NEUTRAL (Day 3 ablation)
- Multi-slot expansion on 51 items: UNLOCKED (post-processing)
- ~310 items wrong despite \boxed{} — real ceiling is fixing wrong answers
