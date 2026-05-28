# RESEARCH — Living Document

**Purpose**: Capture insights from LLM research agents, synthesize across prompts, drive submission decisions. Append-only. Each session gets a dated section.

This sits alongside:
- `docs/FINDINGS.md` — accumulated knowledge (what we KNOW empirically); the Hendrycks find is at the top
- `docs/SUBMISSIONS_TODO.md` — action items
- `docs/RESEARCH.md` (this file) — external research input + synthesis + decisions

---

## Day 3 — 2026-05-27 evening (5-slot Kaggle submission research)

### Context at time of research
- Time pressure: ~2 hours to Kaggle daily-slot reset at session start
- 5 slots remaining today; final 2 picks at deadline ~2026-06-02
- Current best: 0.653 real-inference / 0.671 diagnostic; leaderboard #1: 0.770
- Strategic shift mid-session: **research-before-commit**. CSVs in `submissions/` are floors, not commitments.
- Base CSVs ready: `track_A_day3_v1`, `track_A_day3_v2`, `track_B_day3_v1`, `track_C_day3_v1` (Slots 1-4); Slot 5 reserved.

### 5 Research agents queried

| Agent # | Lens | Key insight |
|---|---|---|
| 1 | String matching & format conventions | Track C base should move to Slot 1; alternative parallel-track plan |
| 2 | Test-time inference optimization | Arithmetic: 110-item gap > 71-item override queue. One slot must be format-thesis, not pure overrides |
| 3 | **Math/logic & creative aggregation** | **🚀 Reverse-engineered Hendrycks `is_equiv` source. The 28pp gap = Hendrycks(Kaggle) vs Minerva(local). \dfrac is non-issue; \text{A} preserved; trailing zeros NOT stripped** |
| 4 | Math problem format conventions | Multi-slot expansion + MCQ \text{} unwrap. Hit browsing limit. |
| 5 (Gemini, added) | LaTeX normalization + override execution | Same Hendrycks finding as Agent 3. **Dangerous recommendation: alphabetical sort (would break order, -17.6pp probe-verified)** |

### Empirical follow-up: format hypothesis spot-check

Ran spot-check on slot1_reformat (300 MCQ items + 643 free-form):
- `\text{X}` MCQ wrap: **0 items** — already stripped in our pipeline. DEAD.
- `\mathbf` wrap: 0 items. DEAD.
- Trailing period `A.`: 0 items. DEAD.
- Parenthetical `(A)`: 0 items. DEAD.
- **Trailing-zero decimals: 53 items** — `0.3750`, `70.00`, `4.000`, `1.160`, `10.50`, etc. **LIVE LEVER.**

### Synthesis — what 5 agents AGREE on

1. **Multi-slot expansion is the dominant fix** — Agents 1, 2, 3, 4, Gemini
2. **Don't burn a slot on pure format probe** — Agents 1, 2, 3, 4 agree; Gemini disagrees (probe-first)
3. **Track C base (0.653) should move to Slot 1, not Slot 4** — Agents 1, 2, 3 agree; Gemini puts probe at Slot 1
4. **Track A vs Track C base A/B is the highest-information single comparison** — Agents 2, 3
5. **Kaggle grader is Hendrycks-style** — Agents 3, 5 (Gemini) cite source code

### Synthesis — DISAGREEMENTS resolved

| Disagreement | Resolution | Winner |
|---|---|---|
| `\dfrac` standardization? | Hendrycks auto-strips dfrac→frac. **NOT a lever.** | Agent 3 (cited source) |
| Probe Slot 1 vs leverage Slot 1? | All other agents say leverage. Gemini's EV math is broken (claims 1054pp gain via slot-multiplication that ignores cap at 30pp format-error count). **Leverage.** | Agents 1, 2, 3, 4 |
| Alphabetical sort multi-answer? | **NO.** We have probe-verified -17.6pp order-reversal penalty. **DO NOT APPLY.** | Empirical evidence beats Gemini |
| Strip trailing units (`\text{ cm}`)? | Hendrycks already does this when there's trailing space. Don't double-strip aggressively. | Agent 3 |
| MED tier priority order? | Wolfram MED before Rescue MED (verifier-backed > 2/4 teacher) | Agent 2 |

### Slot strategy ideas (decisions table — fill at commit time)

| Slot | Candidate plan A (claude_strategy original) | Candidate plan B (research-informed) | Rationale for B |
|---|---|---|---|
| 1 | Track A v1 (slot1_reformat + Wolfram HIGH + rescue HIGH) | **Track C v1 + trailing-zero strip + multi-slot scan** (kitchen sink on 0.653 base) | Front-load best base + only live format lever. Agents 1/2/3 push Track C to Slot 1; spot-check confirms trailing-zeros is real with 53 affected items. |
| 2 | Track A v2 (+ rescue MED) | **Same kitchen-sink format on Track A** (slot1_reformat 0.646 + same overrides + trailing-zero strip) | Clean base A/B with format normalized. Single highest-info comparison per Agents 2/3. |
| 3 | Track B v1 (+ Wolfram MED/PARTIAL) | WAIT for Slots 1+2 scores; decide reactively | Don't pre-commit; let base A/B inform |
| 4 | Track C v1 | WAIT | Reactive |
| 5 | Reserve | Reserve | Unchanged |

### Open questions to send back to agents
- Agent 1: basis for `\dfrac` standardization claim? Source code or inference?
- Agent 2: Kaggle = Qwen-Math parser or Hendrycks-style? Resolve via 28pp gap interpretation
- Agent 3: design offline Hendrycks vs Minerva test; trailing-zero strip safe heuristic
- Agent 4: WeBWorK vs Putnam vs AIME identification from problem text patterns
- Gemini: alphabetical sort recommendation conflicts with our probe; EV math derivation

### Decisions taken (FILL AFTER agent replies + Rain go-ahead)

| Slot | Submitted file | Kaggle score | Notes |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

### Full agent responses

(Stored separately — pastes were ~8K words combined. See git history of this file or `docs/research/2026-05-27/` if we archive them. For now, key claims and synthesis above.)

---

## Day 4 — TBD

(placeholder)

---

## Past research / thinking — to be consolidated

(TODO from SUBMISSIONS_TODO.md — search repo + Drive for legacy research docs and consolidate or archive)
