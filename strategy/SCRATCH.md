# strategy/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- The test pipeline diagram is missing an "iterate" feedback arrow showing the 4-step loop (expand gold → new inference → grow adapter → improve post-proc). Currently only labeled, not visually connected.
- DeepConf@SC32/64 is our last big inference run candidate. Heavy GPU, can run 2 days on Thunder autonomously. Needs output_scores=True plumbed through sampler. ~50 lines of code on top of existing SC pipeline.
- NoThinking SC=8 results exist but were NEVER analyzed or scored on Kaggle. This is free data sitting on disk.
- GenSelect PoC had truncation issues — check if full-length candidates change the outcome.
- We should answer: for each item, does ANY of 8 SC samples match gold? (oracle@8 ceiling analysis)

---

## [Penny 7] Lever rankings cross-reference (2026-05-28, claude_librarian)

**Source**: strategy/LEVERS.md (comprehensive lever analysis, updated Day 4 EOD).
**Composite ranking**:
1. Lever 5 (Multi-slot expansion) — 9/10 feasibility, +2-5pp, 1d ENG. Ship first.
2. Lever 4 (Hard-item SC analysis) — 8/10 feasibility, +1-3pp, 0.5d. Free data ready.
3. Lever 6 (Targeted memo SFT) — 7/10 feasibility, +3-8pp, 2d. Highest EV among allowed.
4. Lever 3 (GenSelect re-run) — 6/10, +2-5pp. After smoke test.
5. Lever 2 (SFT v7 general) — 6/10, +2-5pp. Risky; v4/v5 already failed pattern.

**Killed**: Lever 1 (TIR) — rules. PRM-half of Lever 3 — rules.
**Key insight**: Lever 5 (post-processing) is highest-feasibility quick win. Lever 6 (targeted memo SFT) is highest-EV among rules-permitted techniques.

---

## SIGNOFF — claude_librarian (2026-05-28)

**What I tried**: All 10 pennies from the repo organization task.

**What I did**:
- Penny 1: Extracted 63 trailing-zero items from master_item_tracker.csv (FINDINGS said 53; regex found 63 — likely a slightly broader match). Added full table to postprocessing/FORMAT_RULES.md.
- Penny 2: Extracted 119 format_only_diff_teacher items (FINDINGS said 117; actual flag count 119). Created postprocessing/format_candidates_117.csv. Noted in postprocessing/SCRATCH.md.
- Penny 3: Verified undercount_candidates.csv exists (82 rows vs 110 flagged — gap of 28). Added undercount category to FORMAT_RULES.md + SCRATCH.md.
- Penny 4: Added OPL 39 OK-status summary to data/search/SCRATCH.md.
- Penny 5: Added info-theoretic ceiling to submission/SCRATCH.md.
- Penny 6: Added TIME_MACHINE_BACKLOG Tier 1 items to strategy/TODO.md.
- Penny 7: Added lever rankings cross-ref to strategy/SCRATCH.md.
- Penny 8: Added 5 no-box rescue items (4 HIGH + 1 MEDIUM) to FORMAT_RULES.md.
- Penny 9: Added prompt dive summary to inference/RESEARCH.md.
- Penny 10: Added Day 3 research SOP to research/SCRATCH.md.

**What worked**: All 10 pennies completed and committed in 2 commits. Data extraction via Python was clean.

**What didn't**: Minor count discrepancies — FINDINGS says 53 trailing-zero but regex finds 63; FINDINGS says 117 format-only-diff but flag count is 119; undercount CSV has 82 of 110 flagged items. These gaps should be investigated but don't block the routing.

**What's left for next agent**:
- The 28-item gap in undercount (110 flagged vs 82 in CSV) needs resolution.
- The 63 vs 53 trailing-zero count should be reconciled (may be different filter criteria).
- TIME_MACHINE_BACKLOG Tier 1 docs (prompt_engineering_research.md 70KB, experiments.md 85KB) are flagged but UNMINED — someone needs to actually mine them.
- FORMAT_RULES.md "Discovered rules" table is still empty (the trailing-zero items are in a new section, not the original table — that table needs specific per-item verified format rules).

**Key discoveries**:
- The format_candidates_117.csv is the single highest-value post-processing input — 119 items where math is right but format is wrong. Pure mechanical wins.
- master_item_tracker.csv has 1039 rows but private.jsonl has 943 items — the 96-item surplus is still unreconciled (noted in TODO.md already).
