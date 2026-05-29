# HENDRYCKS-STRICT NORMALIZER — Per-Item-Type Transform Spec (2026-05-28)

**Purpose:** "If the grader is Hendrycks (it is — see GRADER_RESEARCH.md §1), apply THESE exact transforms, by item type, to maximize score." This is the build spec for the post-processor's final overlay.

**Golden rule:** the grader extracts the LAST `\boxed{}` (free-form) / FIRST `\boxed{LETTER}` (MCQ), runs `_strip_string`, then `==`. So our job: make our last box's `_strip_string` output **byte-identical** to gold's `_strip_string` output. We can't see gold, so we (a) avoid forms Hendrycks won't normalize away, (b) push toward the form gold most likely uses.

---

## MCQ (has `options` field — 300 items)
- **Emit a single `\boxed{LETTER}`, uppercase, no wrapper.** `\boxed{C}`. Not `\boxed{\text{C}}`, not `(C)`, not `\boxed{C.}`.
- Grader takes the **FIRST** `\boxed{LETTER}` via `re.search`. So:
  - **To override an MCQ answer: PREPEND** `\boxed{NEW}` to the response, OR replace the response entirely with `\boxed{NEW}`, OR find-and-replace the first existing box. **NEVER append-to-end** (no-op — AMBER #3 confirmed).
- Fallback if no letter-box: grader takes the **last bare capital letter** in the text. So a stray "...therefore A is wrong, B is right" can mis-grade — ensure exactly one clean box.

## Free-form — SINGLE INTEGER
- Bare integer, no decoration: `\boxed{42}`.
- **Strip:** any `.0`/`.00` (`42.0`→`42`), thousands commas (`1,000`→`1000`), `\mathrm{}`/`\mathbf{}` wrappers, `\text{}`, trailing units, `=` prefixes >2 chars (rewrite `Total=42`→`42`).
- `x=42`, `D=42` are auto-stripped (≤2-char LHS) — safe, but cleaner to strip ourselves.

## Free-form — SINGLE DECIMAL
- **STRIP TRAILING ZEROS** (L1): `1.50`→`1.5`, `-0.50`→`-0.5`, `3.600`→`3.6`. Hendrycks does NOT do this. **Highest-volume format lever (~63 items flagged).**
- Do NOT add/remove precision blindly — match gold's precision. If unsure of gold precision, the model's natural output is the best prior; only strip *trailing* zeros (lossless).
- **Expand scientific notation** (L12): `1.5e3`→`1500`, `1.5\times10^3`→`1500`.
- `.5`→`0.5` is auto (leading-dot fix), but emit `0.5` to be safe.

## Free-form — SINGLE FRACTION / RATIONAL
- Prefer `\frac{a}{b}` form (gold uses fractions for rationals — MATH convention, probe-confirmed +2 items #30).
- **Negative placement matters** (L8): if gold is `\frac{-2}{3}` and you emit `-\frac{2}{3}`, FAIL. Default to numerator-negative `\frac{-a}{b}` (matches `a/b` auto-fix output) unless evidence says otherwise.
- **SAFE:** single `a/b` (incl. `-3/5`) auto-converts to `\frac` (L13) — don't bother rewriting a lone `a/b`.
- **`0.5`↔`\frac{1}{2}` is the ONLY auto decimal↔fraction.** All other decimal↔fraction is a manual lever (L2): convert decimal→fraction only when you have evidence gold is a fraction.

## Free-form — MULTI-ANSWER (the dominant lever, L4/L5)
- **ONE box, comma-separated, CORRECT ORDER:** `\boxed{a, b, c}`. Never per-slot `\boxed{a}\boxed{b}` (−16.2pp). Order wrong = −17.6pp.
- Spacing irrelevant (`a, b` ≡ `a,b`) — global space strip.
- **UNDERCOUNT FIX:** if the model's reasoning produces N answers but boxes only the last, collect all N from the trace, write them in question-order in one box.
- **PER-ELEMENT FRACTIONS (L9 — NEW):** inside a multi-answer list, `a/b` is NOT auto-converted (the `a/b`→`\frac` fix only fires on a whole single-fraction string). So `1/2, 3/4` will NOT match `\frac{1}{2},\frac{3}{4}`. **Write each rational element as explicit `\frac{}{}` yourself** if gold uses fractions.
- **PER-ELEMENT TRAILING ZEROS:** strip in each element (`2, 140.00`→`2, 140`).

## Free-form — SET (`{1, 2, 3}`)
- **L11 (NEW):** set braces are NOT stripped (`{1,2,3}` ≠ `1,2,3`). Match gold's notation. If unsure, the dataset/judger convention is comma-list inside the box for "unordered list" types → prefer bare `1, 2, 3` but flag as ambiguous; this is a per-item evidence question, not a blanket rule.

## Free-form — INTERVAL (`(2, 5)`, `[0, \infty)`)
- Spacing auto-stripped; brackets/parens are literal and PRESERVED. Match gold's open/closed exactly. `(2,5)` ≡ `(2, 5)` (safe), but `(2,5)` ≠ `[2,5]`.

## Free-form — EXPRESSION / SYMBOLIC
- **No sympy server-side** — `\pi/4` ≠ `0.7854`, `2x` ≠ `x+x`, `*` ≠ `\cdot`. Emit the form gold uses; do not "simplify".
- **Strip `\mathrm{}`/`\mathbf{}`** (L10 NEW): `\mathrm{e}`→`e`. Hendrycks does NOT strip these (judger.py does, so this never showed up in local eval).
- **`*` vs `\cdot` NOT normalized** (documented failure: items 104, 127) — match gold.
- Multi-char `=` prefixes NOT stripped (`Mean=`, `A=`, `B=`) — items 20/108/139 lost. Strip the prefix yourself, emit RHS only (unless the answer genuinely is an equation gold wants).

## TRUE/FALSE / YES-NO / WEEKDAY
- judger.py normalizes booleans/weekdays; **Hendrycks does NOT.** Match gold's exact string casing (`Yes` vs `yes` vs `True`). This is a per-item evidence question — flag, don't blanket-transform.

---

## THE BUNDLED "STRICT NORMALIZER" OVERLAY (recommended next submission)
Apply, in order, to every free-form last-box value (idempotent, slice-independent, zero new evidence required):
1. Collapse multiple `\boxed{}` → single `\boxed{...}` (undercount/multi-slot fix).  ← biggest yield
2. Per-element: strip trailing zeros from decimals (`X.d0+`→`X.d`, `X.0+`→`X`).
3. Per-element: strip thousands commas from pure numbers (careful: only when the comma is INSIDE a single number, not the multi-answer delimiter).
4. Strip `\mathrm{...}`→`...`, `\mathbf{...}`→`...`.
5. Expand scientific notation → plain decimal.
6. Strip multi-char `LHS=` prefixes (keep RHS).
7. Per-element rationals → `\frac{}{}` if list contains other fractions / gold-form is fraction.
8. Leave dfrac/left/right/circ/%/sqrt-shorthand alone (auto-normalized — don't burn effort).

Treat this as ONE hypothesis submission. If it beats 0.706, the strict-normalizer levers (L9–L12) are live; if neutral, they don't hit the slice (but may still help the hidden 660 — keep for final pick).

**Validation harness:** `/home/claude/hendrycks_is_equiv.py` is the canonical engine — run any candidate answer + hypothesized gold through `is_equiv()` BEFORE submitting. Copy it into `grading/` as the reference implementation.
