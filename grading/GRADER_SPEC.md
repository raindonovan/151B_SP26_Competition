# GRADER_SPEC — The Grading Phase (canonical)

**Pipeline phase:** GRADING (final phase, AFTER post-processing). See `/PIPELINE.md`.
**Answers org-question #6** (grader format, general + per question) and the new grading-phase question
*"how does the Kaggle grader grade?"*
**Status:** Consolidated 2026-05-28 from a Day-3 source-code reverse-engineering (was buried in
`data/FINDINGS.md`) + Piazza staff confirmations (was in `archive/design/`). This file is the single
source of truth; older mentions (agents/CLAUDE_STRATEGY.md, postprocessing/FINDINGS.md, data/FINDINGS.md)
defer to this.

---

## 1. What the Kaggle grader IS

**Kaggle grader ≈ Hendrycks MATH `is_equiv`** — pure post-normalization **string match**, NO server-side
symbolic/sympy equivalence.
- Confirmed three independent ways: (a) Day-3 source-code reverse-engineering; (b) Piazza — **Anthony Tong,
  2026-05-09: the grader does NOT normalize fraction vs decimal forms (no sympy on the server)**;
  (c) our submission probes.
- Source: `github.com/hendrycks/math/blob/main/modeling/math_equivalence.py`

## 2. Extraction rule

**Extracts ONLY the LAST `\boxed{}`, then normalizes, then string-matches the hidden gold.**
- The claim in `agents/CLAUDE_STRATEGY.md` that it reads ALL boxes / is "multi-box tolerant" is **WRONG** —
  that describes our *local* judger, not Kaggle. (Flagged for correction.)
- Within-box **order matters**: reversed `\boxed{a,b}`→`\boxed{b,a}` = **−17.6pp** (probe-verified).
- Per-slot `\boxed{a} \boxed{b}` (separate boxes) = **−16.2pp** vs single `\boxed{a, b}` — only the last box survives.

## 3. MCQ vs Free-form (two code paths)

| Type | Rule |
|---|---|
| **MCQ** | First `\boxed{LETTER}` (`re.search`), fallback last bare capital. Exact letter match. |
| **Free-form** | Last `\boxed{}`, Hendrycks normalize, string match. |

## 4. What Hendrycks AUTO-NORMALIZES — DO NOT waste a submission "fixing" these

| Transform | Effect |
|---|---|
| `dfrac`→`frac`, `tfrac`→`frac` | `\dfrac ≡ \frac` — **the \dfrac debate is RESOLVED, don't burn a slot** |
| `\left`→``, `\right`→`` | bracket scalers stripped |
| `^\circ`, `^{\circ}` → `` | degree symbols stripped |
| **ALL whitespace stripped (global)** | **`"a, b" ≡ "a,b"` — multi-answer comma SPACING does not matter** |
| `\!`, escaped `\$`, escaped `\%` → `` | stripped |
| `_remove_right_units` | strips `\text{ unit}` **only with a trailing space** → `\text{A}` (no space) is PRESERVED |
| `_fix_sqrt` | `\sqrt3 ≡ \sqrt{3}` |
| `_fix_fracs` | `\frac12 ≡ \frac{1}{2}` |
| `_fix_a_slash_b` | `3/5 ≡ \frac{3}{5}` (pure integers only) |
| `x=` strip iff `len(LHS) ≤ 2` | `D=8 → 8`, `x=5 → 5` |

## 5. What Hendrycks does NOT normalize — THESE ARE OUR LEVERS

| Failure mode | Status |
|---|---|
| **Multi-slot under-count** (Qwen boxes last slot only) | DOMINANT — 79% of B1-7 failures. Primary lever. |
| **Trailing zeros** `1.50 ≠ 1.5`, `70.00 ≠ 70` | LIVE — ~53 items in slot1_reformat affected |
| **Fraction vs decimal** `3/5 ≠ 0.6` | Never normalized (Piazza-confirmed). Affects "4 sig-fig" prompt. |
| `\mathbf{2}` vs `2`, `100,000` vs `100000` | minor / mostly dead in current subs |
| `\text{A}` vs `A` (MCQ wrap) | dead — our subs already letterized |

## 6. Per-question format the grader expects

- **MCQ:** single `\boxed{LETTER}`, e.g. `\boxed{C}`.
- **Free-form, single:** single `\boxed{value}` in probable gold form (watch fraction-vs-decimal).
- **Free-form, multi:** ONE box, comma-separated, **correct ORDER** (spacing irrelevant): `\boxed{a, b, c}`.
  Never per-slot. (The official starter prompt says exactly this.)

## 7. The local judger.py is NOT the Kaggle grader (28pp gap — see grading/JUDGER_AND_PUBLIC_SET.md)

`judger.py` ≈ Minerva `normalize_final_answer` (sympy-based, **more lenient** than Hendrycks) AND its MCQ
parser breaks on SC majority-vote output. Both make it untrustworthy for accuracy. **Use only for
degenerate-output detection.** Full analysis in the sibling doc.

## 8. Sources / provenance

- Hendrycks `is_equiv`: `github.com/hendrycks/math/.../math_equivalence.py`
- Minerva `normalize_final_answer`: `lm-evaluation-harness/lm_eval/tasks/minerva_math/utils.py`
- Piazza: Anthony Tong 2026-05-09 (no fraction/decimal normalization); Ruijia Niu 2026-05-05 (modeling rules).
- Probes: `submission/REGISTRY.md` (#5 reversed −17.6pp; per-slot subs −16.2pp).
- Local code: `/judger.py`; official scoring: `/starter_code_cse151b_comp.ipynb` (cells 11, 22).

## 9. Submission format (cross-phase — see also COMPETITION.md pre-inference)
The submission CSV is the boundary object the post-processor emits and the grader consumes, so its format is
documented in BOTH pre-inference (`COMPETITION.md`) and here (grading). Canonical exemplar:
`data/sample_submission.csv` (5 rows, header `id,response`, each a full raw Qwen trace ending in `\boxed{}`).
- Row = `id,response`; `response` = COMPLETE raw model output (all CoT/thinking), CSV-escaped (inner quotes `""`).
- Every `private.jsonl` id needs a row. Final answer is extracted from the trace by the grader (§2 above).
- The exemplar mixes `\frac` and `\dfrac` → reconfirms `\dfrac` is normalized away (§4).
