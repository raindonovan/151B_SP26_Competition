# Post-Processing Research

## Grader behavior
See `grading/GRADER_SPEC.md` for full specification.
See `strategy/POST_PROCESSING_TECHNIQUES.md` for technique inventory.

## Key insight: 80% of errors are format, not math
Wolfram audit confirms. Dominant failure mode is multi-slot under-count.
Post-processing is the highest-leverage lever before adapter training.

## Architecture decision (LOCKED)
Post-processing is a composable function chain. Each item gets custom routing.
Adapter's job = correctness. Post-processing's job = format.
This separation compounds improvements across both inference and adapter paths.

## Source-corpus routing (HIGHEST PRIORITY — not yet implemented)
Route items by source corpus to determine expected gold format:
- AIME → bare integer in \boxed{}
- MATH → LaTeX with \frac, \sqrt, etc.
- WeBWorK → decimal with requested precision
- GSM8K → bare integer
- MCQ → just the letter

Identifying source corpus attacks the 80% format-loss directly.

## Format conventions research
See `research/FORMAT_CONVENTIONS.md` for detailed findings from the deep research session.
