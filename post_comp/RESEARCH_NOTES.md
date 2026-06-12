# RESEARCH_NOTES.md — Post-comp research angles

Canonical home for research notes promoted from scratch. **Narrative lock:** canonical win remains `30_05_slot4_aggressive_v2` (0.745/0.684); research notes explain mechanisms and field context, not a revised pick story.

---

## NoThinking vs competition axis

### [Rain] 2026-06-04 — Why NoThinking wasn't a leaderboard tactic

**GOLD:** NoThinking is a distinct research contribution (throughput/cost, structural fix for thinking-mode overrun), not a missed competition lever. The winning path correctly maximized accuracy under unlimited GPU.

There is a clean reason the field did not adopt our NoThinking version: 151B was a pure accuracy contest with GPU to burn. Trading ~5pp for ~80% fewer tokens is exactly what you do not do to win — you max the reasoning and rescue the overruns, which is what everyone else did. NoThinking's payoff is throughput and cost, which the leaderboard never rewarded.

That is why it is a distinct contribution rather than a competition tactic: it answers the field's dominant failure — thinking-mode rambling past the budget — structurally instead of reactively, on a different axis than the comp optimized for.

**Cross-ref:** External validation of truncation/thinking-length as core failure axes → `inference/FINDINGS.md` § `[Rain] 2026-06-04 — External validation (NoThinking / 151B paper line)`.
