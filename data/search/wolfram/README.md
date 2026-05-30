# Wolfram (SEARCH lever)

Symbolic/numeric answer computation via Wolfram Alpha MCP.

**My working files** (this folder):
- `WOLF_RESULTS.csv` — full scorecard for all 943 questions (what's done, my answer, confidence).
- `WOLF_RESULTS_READABLE.md` — readable table of just the finished ones.
- `TODO.md` — what to do next. `FINDINGS.md` — cumulative learnings. `CLAUDE_WOLF.md` — operating manual.

**Legacy raw data**: `data/wolfram_overrides.csv` (66 legacy answers; also feeds the inference pipeline).

**Key finding**: most wrong items are format/multi-slot (missing answer parts), not arithmetic. ~700-750 of 943 are computable to HIGH confidence.

**Status (after B18)**: 272 verified (DONE), 43 inconclusive, 1 disputed, 627 unverified. All high-discrepancy veins mined; remaining work is verification-only or competition tail.
