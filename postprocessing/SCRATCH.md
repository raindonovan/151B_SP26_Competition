# postprocessing/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- AMBER ALERT (Day 6): format-aware comparison is critical everywhere. Backsolve, answer sheet, post-processing all need to use the SAME normalization as the grader (Hendrycks _strip_string). Raw string comparison introduces noise.
- Post-processor should be a composable function chain with per-item routing. Each item gets a custom sequence of functions based on its format needs.
- Adapter format decision (LOCKED): adapter just needs to produce something resembling an answer. Post-processing handles format. This means post-processing is a PREREQUISITE for evaluating the adapter.
- Every discovered format rule (e.g., "item X needs trailing zeros") is literally a point on the scoreboard. Record in FORMAT_RULES.md.
- Source-corpus routing is the highest-EV post-processing improvement: route AIME→integer, MATH→LaTeX, WeBWorK→decimal. Attacks the 80% format-loss directly.
- Hendrycks _strip_string does NOT normalize: commas in numbers, decimals to fractions (except 0.5), trailing zeros, \mathrm{} wrappers. These are all levers.
- Minerva normalizer additionally strips unit words and commas in pure-digit numbers. If our grader uses Minerva, many format issues go away. Our 80% format-loss suggests it doesn't.
- Probe opportunity: submit \boxed{0.5} vs \boxed{\frac{1}{2}} on same item to fingerprint grader behavior.

---

## [Penny 2] 119 format-only-diff items extracted (2026-05-28, claude_librarian)

**Source**: data/FINDINGS.md §5, data/master_item_tracker.csv `format_only_diff_teacher` flag.
**Output**: `postprocessing/format_candidates_117.csv` (119 items — the "117" name is from the original count; actual extraction yielded 119).
**What these are**: Items where our current best_answer matches the teacher consensus AFTER normalization but differs in raw string form. These are PURE FORMAT ERRORS — the math is right, the encoding is wrong.
**Action**: Feed these into the post-processing pipeline. Each one is a recoverable point via format transform only (no math re-computation needed).
**Priority**: HIGH — these are the lowest-hanging fruit for post-processing.

---

## [Penny 3] Multi-slot undercount items (2026-05-28, claude_librarian)

**Source**: data/FINDINGS.md §5, data/master_item_tracker.csv `undercount` flag, data/undercount_candidates.csv (82 rows).
**What these are**: 110 items flagged as `undercount` in master tracker (items where current answer has fewer slots than the question's [ANS] markers). The undercount_candidates.csv has 82 of these pre-extracted.
**Gap**: 110 flagged vs 82 in CSV — 28 items may be missing from the CSV or were filtered.
**Why it matters**: Multi-slot undercount is the DOMINANT failure mode (79% of B1-7 audit items per data/FINDINGS.md §4). Qwen emits only the last \boxed{} for multi-answer items, losing all other slots.
**Action**: Post-processor needs multi-answer expansion — collect all \boxed{} from raw response, merge into single \boxed{a, b, c}.
