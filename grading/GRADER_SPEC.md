# GRADER_SPEC — The Grading Phase (canonical)

**Pipeline phase:** GRADING (final phase, AFTER post-processing). See `/PIPELINE.md`.
**Answers repo-organization question #6:** what format the grader expects, in general and per question type.
**Status:** RESOLVED 2026-05-28 (Day 6). This file is the single source of truth for grader behavior;
all other mentions (agents/CLAUDE_STRATEGY.md, postprocessing/FINDINGS.md F1-F3, memory) defer to this.

---

## 1. What the Kaggle grader IS

The Kaggle grader is the **Hendrycks MATH `is_equiv`** equivalence checker.
- **Confirmed via source-code review** (originally logged as postprocessing/FINDINGS.md F1).
- Corroborated by: the official starter notebook (`starter_code_cse151b_comp.ipynb`),
  the official system prompts, and our own submission probes.

## 2. Extraction rule (the resolved contradiction)

**The grader extracts ONLY the LAST `\boxed{}` in the response, then string-matches after normalization.**

- ❌ The claim in `agents/CLAUDE_STRATEGY.md` that it "extracts from ALL `\boxed{}` / is multi-box tolerant" is **WRONG**. That sentence actually describes our *local* `judger.py`, not the Kaggle grader. (Flagged for correction.)
- Within-box **order matters**: reversed values in `\boxed{a, b}` → `\boxed{b, a}` cost **−17.6pp** (probe_b_reversed vs Run 09).
- Per-slot format `\boxed{a} \boxed{b}` (separate boxes) cost **−16.2pp** vs single `\boxed{a, b}` — because only the LAST box survives, dropping the rest.

## 3. MCQ vs Free-form (two different code paths)

| Type | Path | Rule |
|---|---|---|
| **MCQ** | `score_mcq` / `extract_letter` | Takes the **first** `\boxed{LETTER}` (`re.search`), fallback = last bare capital letter. Exact match to gold letter. |
| **Free-form** | `Judger.auto_judge` (Hendrycks `is_equiv`) | Takes the **last** `\boxed{}`, normalizes, symbolic/numeric equivalence. |

## 4. What the grader auto-normalizes — DON'T waste levers "fixing" these (was F2)

`\dfrac`→`\frac` · `\left`/`\right` removed · whitespace stripped · `\sqrt`/`\frac` shorthand accepted · leading `x=` prefix stripped.

## 5. What the grader does NOT normalize — these ARE our levers (was F3)

- **Multi-slot under-count** (DOMINANT — 79% of failures): emit one box per sub-answer → only last survives → undercount.
- Fraction vs decimal mismatch.
- `\text{A}` vs `A`.

## 6. Per-question format the grader expects

- **MCQ:** single `\boxed{LETTER}`, e.g. `\boxed{C}`.
- **Free-form, single answer:** single `\boxed{value}`.
- **Free-form, multi-answer:** ONE box, comma-separated, **correct order**: `\boxed{a, b, c}`.
  Never per-slot `\boxed{a} \boxed{b}`. (Official starter prompt says exactly this.)

## 7. Local judger.py ≠ Kaggle grader (the 28pp gap)

`judger.py` is our LOCAL grader. It diverges from Kaggle in two known ways:
1. **Extraction:** `extract_all_boxed` keeps the *last contiguous GROUP* of boxes (merges adjacent boxes with ", "). More lenient than Kaggle's strict last-box-only.
2. **Gold source:** local uses pseudo-gold (teacher consensus), Kaggle uses true withheld gold.

Net: Run 09 scored 0.332 local vs 0.614 Kaggle. **Use judger.py ONLY for degenerate-output detection, never accuracy decisions.**

## 8. Source pointers

- Local grader code: `/judger.py` (`extract_all_boxed`, `extract_boxed_answer`, `auto_judge`)
- Official scoring + prompts: `/starter_code_cse151b_comp.ipynb` (cells 11, 22)
- Probe evidence: `/submission/REGISTRY.md` (#5 reversed −17.6pp; per-slot subs)
