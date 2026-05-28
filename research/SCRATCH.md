# research/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- Format conventions deep research (Day 6): full report stored in Claude.ai conversation artifact, summary at research/FORMAT_CONVENTIONS.md. Key finding: Hendrycks _strip_string is the most likely grader. Source-corpus routing is the highest-EV post-processing technique.
- 113 free-form items embed A./B./C. in question text but route as free-form (no options field). These might need MCQ-style letter extraction in post-processing.
- Dataset mix: 300 MCQ, 105 fake-MCQ (embedded letters), 538 genuine free-form.
- Source corpus signals: 15 AIME-like, 21 WeBWorK-like, 31 textbook-like, 149 olympiad-like (by keyword heuristic).

---

## [Penny 10] Day 3 research methodology SOP (2026-05-28, claude_librarian)

**Source**: archive/docs/RESEARCH.md
**Template**: Day 3 methodology (5 agents queried, triangulated across sources, empirically followed up) is the template for our research SOP. Pattern: (1) define question precisely, (2) query 5+ independent sources/agents, (3) triangulate findings, (4) empirically validate top claims, (5) commit verified findings to repo.
**Full log**: archive/docs/RESEARCH.md
**Reuse**: Any future research task should follow this pattern. It's how we got the Hendrycks grader finding.
