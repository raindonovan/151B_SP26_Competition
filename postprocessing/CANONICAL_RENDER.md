# CANONICAL_RENDER.md — canonical answer rendering (03_06 source campaign)

`postprocessing/canonical_render.py :: render_canonical(raw_value, n_slots, is_mcq)` →
a single `\boxed{...}` string. **VALUE NEVER CHANGES — render only.**

## Rules

1. **Pure arithmetic eval.** A slot that is *entirely* a numeric arithmetic expression
   (`^[\d\s+\-*/().]+$`, containing an operator, no `**`) is evaluated to an exact rational:
   `4+9` → `13`. Result rendered as integer or `\frac`. Symbolic/text slots are never evaluated.
2. **`8\div3` → `\frac{8}{3}`** (integer operands).
3. **`*` → `\cdot`** (single `*` only; `**` exponent untouched).
4. **integer `a/b` → `\frac{a}{b}`** (reduced; sign on numerator; `b==1` → integer).
5. **multi-slot**: top-level comma split (brace/paren/bracket aware so tuples/intervals/sets
   stay whole), each slot canonicalized, emitted as ONE `\boxed{a, b, c}` in source order.
   When `n_slots` (`n_ans_slots_q`) is known it is the expected slot count for cross-check; the
   render itself uses the source's own comma structure (it never *fabricates* a missing slot).
6. **MCQ** (`is_mcq=True`): `\boxed{LETTER}` (or `\boxed{L1, L2}` for multi-select).
7. **symbolic / everything else**: whitespace-normalized LaTeX, value preserved verbatim.

## Idempotence / value-safety

- Arithmetic eval is gated to exact rationals: `4+9`→`13` but `1/3`→`\frac{1}{3}`
  (value-equal, never `0.333…`). No rounding, no decimal↔fraction value change.
- Applied **identically** to all 15 campaign sheets so cross-sheet Kaggle deltas isolate the
  *source*, not the formatting.

## Usage in sheets

Each sheet = run14b (R20 SC8) base. For an id where the sheet's source has a non-empty
answer: response cell = `render_canonical(source_value, n_ans_slots_q, is_mcq)` (a clean
`\boxed{}` only). Otherwise: keep Qwen's original run14b response **verbatim** ("else keep
Qwen"). `s15` is the sole exception: v7 values with **raw** render (no canonicalization) to
expose the format gap vs `s10`.
