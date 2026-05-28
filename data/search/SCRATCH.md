# data/search/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- Batch 1 (web_search_100): 60 GOLD, 3 PARTIAL, 37 NOT_FOUND. 60% hit rate.
- Batch 2 (web_search_200): in progress.
- NOT_FOUND items are primarily: complex MCQ (OEIS sequences, advanced integrals, matrix operations), FREE items needing specific data/calculator precision (confidence intervals, regression).
- PAYWALLED items tell us the source corpus = textbook. Format conventions follow textbook norms.
- Competition math (AoPS-findable) has highest search success rate.

---

## [Penny 4] OPL direct-match items: 39 OK-status (2026-05-28, claude_librarian)

**Source**: data/search/opl/findings.md
**What**: 39 items with clean concrete OPL answers extracted (top_status=OK), ALL disagreeing with current Qwen submission.
**Ceiling**: +3.6pp (39 × 88% hit rate / 943).
**Location**: data/search/opl/candidates.csv (look for top_status=OK rows).
**Caveat**: Overrides were off-table until Day 7. These become actionable when/if Rain greenlights overrides.
**NOT**: Training data, a direct answer key, or +5-12pp. See opl/findings.md for full calibration.
