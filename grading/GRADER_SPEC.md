# GRADER_SPEC — The Grading Phase (canonical)

> **⚠️ UPDATE (2026-05-30): canonical grader = `grading/grader.py` (`Grader`).** The Kaggle
> grader switched to **value-equality** (~1e-8: `4.000==4`, `0.6==3/5`) around 05-27. So the
> value-equality engine (`Grader`) is now our Kaggle mirror — NOT the strict Hendrycks
> `kaggle_like_is_equiv`, which mirrors the RETIRED strict grader and is DEPRECATED. Any text
> below describing "Kaggle ≈ Hendrycks string-match, NO sympy" is the PRE-update state; the
> "judger untrustworthy / 28pp gap" framing was that pre-update gap and is now believed closed.
> Final Kaggle confirmation pending (submission/30_05 #1-vs-#2). Use `from grading.grader import Grader`.


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
- **Empirically re-confirmed by 25_08 Slot 4 (2026-05-28)**: 21 real content changes (mostly adding missing slots to multi-answer items) yielded +4 slice items net. The grader does NOT look at reasoning trace for missing slots — only the last box matters.

## 3. MCQ vs Free-form (two code paths)

| Type | Rule |
|---|---|
| **MCQ** | First `\boxed{LETTER}` (`re.search`), fallback last bare capital. Exact letter match. |
| **Free-form** | Last `\boxed{}`, Hendrycks normalize, string match. |

**⚠️ MCQ OVERRIDE MECHANISM CAVEAT (empirically confirmed 25_08 Slot 3, 2026-05-28):**
For MCQ items, **appending `\boxed{NEW_LETTER}` at the END of the response does NOT override** the original letter from the model's reasoning trace. The grader's `re.search` finds the FIRST box, which is the original. 25_08 Slot 3 used append-to-end on 26 MCQ items and scored exactly 0.692 = base = no change. To override MCQ, you must either:
- **Prepend** `\boxed{NEW_LETTER}` to the response, OR
- **Replace** the entire response with just `\boxed{NEW_LETTER}`, OR
- **Find-and-replace** the original first `\boxed{}` in the trace.

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
| **Multi-slot under-count** (Qwen boxes last slot only) | DOMINANT — 79% of B1-7 failures. Primary lever. **EMPIRICALLY CONFIRMED 25_08 Slot 4: +4 slice items from 21 real content changes (highest per-slot yield this run).** |
| **Trailing zeros** `1.50 ≠ 1.5`, `70.00 ≠ 70` | LIVE — ~53 items in slot1_reformat affected. **Net-neutral on slice (#25 = #26 = 0.692) — strip wins ≈ strip losses.** |
| **Fraction vs decimal** `3/5 ≠ 0.6` | Never normalized (Piazza-confirmed). **EMPIRICALLY CONFIRMED 25_08 Slot 1: +2 slice items from 8 decimal→fraction overrides (~83% conditional yield).** |
| **Symbolic vs decimal** `\pi/4 ≠ 0.7854` | Never normalized. **Empirically confirmed via 25_08 Slot 4 item 834.** |
| **`*` for multiplication NOT converted to `\cdot`** | Never normalized. **Empirically confirmed by 25_08 Slot 2 failure: items 104 (`7.7*31*pi/180`) and 127 (`5*ln(17/2)`) caused losses.** |
| **Multi-char LHS prefixes** (`Mean=`, `A=`, `B=`) | `_strip_string` only handles LHS ≤ 2 chars. **Empirically confirmed by 25_08 Slot 2 failure: items 20 (`Mean=228...`), 108 (`A=72, B=12x`), 139 (`A=201, B=...`) caused losses.** |
| **Verbal/conditional notation** ("if c>150; ...") | Never normalized. **Empirically confirmed by 25_08 Slot 2 item 61 piecewise verbal form.** |
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

## Role & Relevance

**Role**: Document exactly how the Kaggle grader works — extraction rules, normalization, and known behaviors.
**Relevance**: The grader is the JUDGE. Every formatting decision, every post-processing function, every answer representation choice is made relative to what the grader accepts. Misunderstanding the grader wastes points.
**Techniques**: Source-code reverse engineering (starter notebook), behavioral probes (differential submissions), instructor Piazza confirmations.
**Inputs**: Starter notebook code, probe submission results, Piazza posts.
**Outputs**: GRADER_SPEC.md (canonical grader behavior), JUDGER_AND_PUBLIC_SET.md (local judger comparison).
**Key lever**: Knowing exactly what the grader normalizes (safe to ignore) vs what it doesn't (must match exactly) is the foundation of all post-processing decisions.
