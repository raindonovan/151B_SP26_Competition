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
