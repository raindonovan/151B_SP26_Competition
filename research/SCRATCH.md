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

## SIGNOFF: claude_grader_research (2026-05-28)

### What I tried:
- Cloned repo, read ALL specified files (REGISTRY.md, AMBER_ALERT.md, RED_ALERT.md, GLOBAL_STRATEGY.md, SCRATCH.md, 25_08/, GRADER_SPEC.md, JUDGER_AND_PUBLIC_SET.md, FINDINGS.md, FORMAT_RULES.md, data/FINDINGS.md, FORMAT_CONVENTIONS.md, POST_PROCESSING_TECHNIQUES.md)
- Fetched and analyzed the COMPLETE Hendrycks `math_equivalence.py` source code (SHA b5c066f) from `hendrycks/math` repo via git-mcp
- Read EleutherAI `lm-evaluation-harness` hendrycks_math implementation
- Rebuilt the entire `_strip_string` and `is_equiv` locally and ran 40+ edge case tests
- Searched for CSE 151B SP26 competition page (not found — may be private/InClass Kaggle)
- Searched for AIMO Progress Prize 1 & 2 winner writeups (Numina, NemoSkills)
- Searched for HuggingFace Math-Verify source code and changelog
- Read starter notebook cells 11 (prompt) and 22 (scoring) in full
- Searched for Piazza posts about format/grader (found references to Anthony Tong confirmation)

### What I did:
- Produced `grading/GRADER_RESEARCH.md` — comprehensive 9-section analysis with edge case tables
- Appended 13 NEW format rules to `postprocessing/SCRATCH.md` with priority-ordered pipeline
- Verified every claim with actual code execution (not speculation)

### What worked:
- git-mcp:get_file_contents successfully fetched the Hendrycks source code (better than web_fetch which hit rate limits)
- Local reproduction of `_strip_string` allowed empirical testing of 40+ edge cases
- Cross-referencing source code with our submission data confirmed all prior findings AND revealed 13 new ones

### What didn't:
- Could not find the exact Kaggle competition page for CSE 151B SP26 math (likely InClass/private)
- Could not find the server-side Kaggle grader code directly (it's likely a variant of Hendrycks bundled in the competition setup)
- web_fetch on github.com returned 429 (rate limited) — used git-mcp instead

### What's left for next agent:
1. **Build the actual post-processing script** implementing the priority-ordered pipeline (13 rules)
2. **Test negative fraction sign placement** on our dataset — scan for items where our answer has `\frac{-a}{b}` and test whether gold uses `-\frac{a}{b}` instead
3. **Audit for bare `%`, `\mathrm{}`, `\mathbf{}`, `\text{A}`** in our current best submission
4. **Audit for `*` vs `\cdot` and bare `ln` vs `\ln`** in current answers
5. **Check multi-answer items for slash fractions** that need explicit `\frac{}{}` conversion (standalone auto-convert doesn't work in multi-answer)
6. **The MCQ override mechanism**: build proper prepend/replace override for MCQ items (not append)

### Key discoveries:
1. **Negative fraction sign placement is a NEW lever**: `-\frac{2}{3}` ≠ `\frac{-2}{3}` — MATH convention is sign-outside
2. **`0.5` and `a/b` auto-conversion are STANDALONE ONLY**: They don't fire inside multi-answer comma-separated strings. Must use explicit `\frac{}{}` in multi-answer.
3. **Bare `%` survives normalization**: Only `\%` is stripped. If model emits bare `%`, it persists.
4. **`\text{A}` without space is PRESERVED**: Only `\text{ unit}` (with space) triggers unit stripping. `\text{A}` stays as-is.
5. **Multiple `\text{ ` occurrences crash normalization**: Causes assert failure → falls back to raw string comparison, bypassing ALL normalization.
6. **`\cdot` ≠ `*` and `\ln` ≠ `ln`**: LaTeX operators/functions are NOT interchangeable with plain text equivalents.
7. **The complete `_strip_string` processing order is documented** — 17 steps in exact sequence, with specific conditions for each.
