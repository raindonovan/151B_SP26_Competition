# Pick B candidate slot 2 — 763-safe conservative join

**Built:** 2026-05-30 · claude_vscode · zero GPU. Deep audit (8-point verification, all pass). NOT Kaggle-submitted — Rain decides slot ordering.

## Why this CSV exists
**Slot-2 disambiguator** (per `submission/SLOT_PLAN.md`). Slot 1 is the Conservative-13 join (`picks_nothinking_join_conservative_v1.csv`), which contains one item (id=763) whose override is an **unevaluated expression** `4+9,8\div3`. If slot 1 scores below the expected range, slot 2 lets us tell apart two causes: **(A) the consensus-join framework failed** vs **(B) the Kaggle grader rejected the 763 expression form**. Without slot 2, a low slot-1 score would risk us wrongly underinvesting in tomorrow's 4-slot structural-normalizer block (slots 3/4/7/8 — the largest expected-delta Pick-B levers). Slot 2 protects that investment.

## Expression-form sweep (all 13 conservative items)
Audited every override value for: unicode arithmetic operators (÷ × −), unevaluated integer arithmetic, unsimplified fractions, mixed surface forms, `\div`/`\times`/`\cdot`. Full table: `expression_form_audit.csv`.
- **Result: only id=763 FLAGGED.** The other 12 are clean (decimals, integers, MCQ letters, simplest-form `\frac`, symbolic `7z,6w`, canonical `\dfrac{\pi}{3}`).
- **id=763 canonical form:** `4+9,8\div3` → **`13, \frac{8}{3}`** (constant-fold `4+9→13`, operator-to-fraction `8\div3→\frac{8}{3}`). sympy-verified value-equal to the current form; both `auto_judge==True` against gold `13, 8/3`.

## Apply mechanism
`postprocessing/scripts/apply_overrides.py` — **canonical full-replace** (`\boxed{value}`), the post-Day-8-bug-fix mechanism (per `strategy/POST_DEADLINE_AUDITS.md` A1 / memory #30; append merges grader box-groups and is broken for multi-slot). Source = raw R20 `run14b_sc8_v1.csv` (0.646). 13 overrides, 930 rows byte-identical to source.

## Rule #11 compliance
**Legal.** All 13 override values derive from Qwen output (NoThinking `voted_answer`) + **universal-tier normalization only** (id=763: constant-folding + operator-to-fraction of Qwen's own output). No teacher/sheet/Wolfram/anchor values in `response`. R20 and NoThinking are both `Qwen3-4B-Thinking-2507` (NoThinking = prefill-bypass inference mode of the same locked model).

## Expected Kaggle delta vs Conservative-13 (slot 1)
- **0pp** if Kaggle's grader already accepts the `4+9,8\div3` expression form (then slot 1 = slot 2, and a low slot-1 score implicates the join framework, not 763).
- **+0.3–0.7pp** if the Kaggle grader rejected the expression form on 763 (then slot 2 rescues that 1 item if on-slice).
Either way, the slot-1-vs-slot-2 delta is the diagnostic signal.
