# JUDGER & PUBLIC SET — Recovered Knowledge (canonical)

**Pipeline phase:** GRADING (local-eval side). See `/PIPELINE.md` and `grading/GRADER_SPEC.md`.
**Why this doc exists:** the local judger and the public set burned us early; what we learned was
scattered across `data/FINDINGS.md`, `archive/design/{DESIGN,experiments,V0_V4_SUMMARY}.md`,
`archive/handoffs/`, and the milestone report. Recovered + consolidated 2026-05-28 (Day 6 archaeology).
The judger problem and the public-set problem are linked — both are about our *local* eval surface.

---

## The three grading-phase questions, answered

### Q1. Did the judger course staff gave us behave like the Kaggle grader?
**NO.** They use different equivalence engines:
- **Kaggle grader ≈ Hendrycks `is_equiv`** — string match after normalization, NO sympy (see GRADER_SPEC).
- **Local `judger.py` ≈ Minerva `normalize_final_answer`** — sympy-based, **much more lenient** on math/format equivalence.
- Net **~28pp gap** (Run 09: 0.332 local vs 0.614 Kaggle). The gap has **two distinct causes**, don't conflate them:
  1. **Leniency mismatch** (free-form): Minerva accepts equivalent forms Hendrycks rejects → local would *over*-credit.
  2. **MCQ-parse anomaly**: judger's MCQ extractor parsed SC majority-vote output as **0/300 correct**, tanking
     Run 09 local to 0.332 even though Kaggle scored the same file 0.614. This anomaly dominated the *sign* of the
     Run-09 gap (milestone report, footnote *).
- **Bottom line:** judger.py is for **degenerate-output detection only**, never accuracy decisions.

### Q2. Can we learn anything by analysing the judger?
**Yes — three things:**
1. The judger's normalization is **Minerva**; the grader's is **Hendrycks**. The *delta between them* is exactly
   the set of mismatches that cost us on Kaggle (fraction/decimal, trailing zeros, equivalent forms). That delta is
   our format-lever list (see GRADER_SPEC §5).
2. `judger.py` has a **`strict_extract` flag**. Default `False` enables fallbacks (`"answer is X"`, `"C: explanation"`,
   last-number-in-text) — a reward function would learn to farm these, so any RL/eval reward MUST use
   `Judger(strict_extract=True)`.
3. The MCQ-parse anomaly on SC output means **local MCQ accuracy is meaningless on SC majority-vote files** — only
   trust local free-form, and only as a coarse signal.

### Q3. How does the Kaggle grader grade?
See `grading/GRADER_SPEC.md` (canonical). Short version: Hendrycks `is_equiv`, last `\boxed{}`, normalize, string-match,
order-sensitive, no sympy. Piazza-confirmed (Anthony Tong, 2026-05-09).

---

## The public set — what it is and why it's retired

- **`data/public.jsonl`: 1126 items WITH gold `answer` field** (375 MCQ + 751 free-form). Fields: question, answer, id.
- **It is LLM-synthesized.** TA-confirmed. Tell-tale: many gold answers are stored as **unevaluated stringified
  expressions**, e.g. id 0 → `"['325*(1+325)']"` (a formula, not the number 105950).
- **~10% gold errors, instructor-confirmed.** Specific TA-confirmed wrong items: **questions 1, 8, 12.3**.
- **Ambiguous gold** exists: e.g. fixed-slice id=48 — gold `I`=(4/3)ln3 and option `E`=(2/3)ln9 are mathematically
  identical (ln9 = 2ln3); two correct options, gold picks one, judger brittle on the other.
- **Consequence: public set RETIRED as an eval surface.** Combined noise floor on a 50-item slice is **~3–5 questions**
  (±2 sampling/engine + ~2–3 ambiguous/wrong gold). The `fixed_50_v1` slice (17 MCQ + 33 free, seeds 42/43) was built
  from it; treat its numbers as coarse only.
- **Kaggle (private) submission remains the ONLY valid accuracy measurement.**

## Known dataset item bugs (carry into the master item table)
0011 truncated text · 0317 options D/H mathematically equivalent · 0570 synthetic OEIS sequence not in OEIS ·
0585/0622/0858 lost MCQ options in dataset prep · 0894 hint says "≈9" but verified count = 10 · 0141 web-match
(Putnam 1989 A-1) gives 0 but 0 not in options.

## Sources
`data/FINDINGS.md` (grader reverse-engineering) · `archive/design/DESIGN.md` §4.4 (synthetic + confirmed errors) ·
`archive/design/experiments.md` Insights 6–7 (noise floor, ambiguous gold) · `milestone_report.tex` (28pp gap,
Run-09 MCQ-parse anomaly footnote) · `archive/handoffs/HANDOFF_v2.3.md` (retired-as-eval-surface).
