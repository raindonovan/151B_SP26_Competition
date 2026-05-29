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

---
## Agent signoff — claude_grader_research — 2026-05-28
### What I tried
- Cloned repo, ingested all grader/submission/postproc/data docs (Phase 1).
- Fetched + ran the ACTUAL Hendrycks `is_equiv` + `last_boxed_only_string` source against 35+ edge-case probes (Phase 2).
- Researched Math-Verify (lenient counter-reference), AIMO 1/2/3 winner post-processing, lm-eval-harness known Hendrycks bugs, and searched for the CSE 151B SP26 Kaggle grader code (Phase 4).
### What I did
- Created grading/GRADER_RESEARCH.md (full findings by confidence).
- Created postprocessing/STRICT_NORMALIZER_SPEC.md (per-item-type build spec + bundled overlay recommendation).
- Saved VERIFIED reference impls: grading/hendrycks_is_equiv_reference.py + hendrycks_extraction_reference.py (use as pre-submission validation harness).
- Appended findings to postprocessing/SCRATCH.md and grading/SCRATCH.md.
### What worked
- Confirmed grader = Hendrycks at LINE level — all 20 prior documented claims verified against source. GRADER_SPEC.md is trustworthy.
- Found 5 NEW levers (L9–L13) not in existing docs: multi-answer per-element a/b NOT auto-fraction'd; \mathrm/\mathbf NOT stripped; set braces NOT stripped; sci-notation NOT normalized; single neg a/b IS safe.
### What didn't work
- No external grader code exists for SP26 math comp (private competition). No golden key. Our reconstruction is the ceiling of available knowledge.
### What's left for next agent
- BUILD the bundled "strict normalizer" overlay (STRICT_NORMALIZER_SPEC.md §"THE BUNDLED OVERLAY") and submit as ONE hypothesis (test L9–L12 on slice). Highest cheap EV.
- Wire grading/hendrycks_is_equiv_reference.py into the post-processor as a pre-submit check.
- Per-item evidence calls still needed for: set-brace items, Yes/yes casing, interval open/closed, fraction-vs-decimal direction (these are NOT blanket rules).
### Key discoveries
- judger.py strips \mathrm and handles per-element fractions → it MASKED levers L9/L10 in local eval. The judger↔Hendrycks delta IS the lever list, mechanically.
- AIMO winner independently confirms RED_ALERT: small public test → overfit risk → prefer robust picks for final 2.
- MCQ override must PREPEND/replace, never append (re-confirmed AMBER #3 via source: re.search = FIRST box).
