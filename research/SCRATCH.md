# research/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- Format conventions deep research (Day 6): full report stored in Claude.ai conversation artifact, summary at research/FORMAT_CONVENTIONS.md. Key finding: Hendrycks _strip_string is the most likely grader. Source-corpus routing is the highest-EV post-processing technique.
- 113 free-form items embed A./B./C. in question text but route as free-form (no options field). These might need MCQ-style letter extraction in post-processing.
- Dataset mix: 300 MCQ, 105 fake-MCQ (embedded letters), 538 genuine free-form.
- Source corpus signals: 15 AIME-like, 21 WeBWorK-like, 31 textbook-like, 149 olympiad-like (by keyword heuristic).
