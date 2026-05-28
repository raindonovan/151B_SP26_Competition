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
