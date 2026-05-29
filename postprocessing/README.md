# postprocessing/ — Stage 3: Post-Inference Processing

Deterministic transforms applied AFTER model output, BEFORE submission. Rules-legal.

## Contents
- `scripts/` — format fix, multi-slot expansion, grader normalization
- `NORMALIZER_SPEC.md` — canonical normalizer design, mode split, CLI, testing system
- `FORMAT_RULE_REGISTRY.csv` — master structured list of formatting rules, status, evidence, and implementation state
- `FORMAT_RULE_AUDIT.md` — map of canonical docs, scattered sources, stale claims, and organizational policy
- `format_review/` — per-item format review data and candidates
- `TODO.md` — untried format levers
- `FINDINGS.md` — Hendrycks grader analysis, format failure taxonomy
- `DECISIONS.md` — locked post-processing decisions

## Key facts
- Grader: Hendrycks is_equiv (string match after normalization)
- Dominant failure: multi-slot under-count (79% of wrong items)
- Structural answer recovery matters more than prompt wording alone
- Trailing-zero stripping is common in raw outputs but not blanket-safe enough to treat as universal default
- Multi-slot expansion on 51 items: UNLOCKED (post-processing)
- ~310 items wrong despite \boxed{} — real ceiling is fixing wrong answers

## Current normalizer entry points
- `postprocessing/scripts/normalizer.py` — canonical CSV normalizer with `conservative`, `default`, and `aggressive` modes
- `postprocessing/scripts/hendrycks_local.py` — local Hendrycks-compatible extraction and equality helpers
- `postprocessing/scripts/evaluate_normalizer.py` — fixture harness for mode evaluation

## Minimal usage

```bash
python3 postprocessing/scripts/normalizer.py INPUT.csv OUTPUT.csv --mode default
python3 postprocessing/scripts/evaluate_normalizer.py --mode aggressive
```
