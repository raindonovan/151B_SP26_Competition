# RESEARCH — Living Document

**Purpose**: Capture insights from LLM research agents, synthesize across prompts, drive submission decisions. Append-only. Each session gets a dated section.

This sits alongside:
- `docs/FINDINGS.md` — accumulated knowledge (what we KNOW empirically)
- `docs/SUBMISSIONS_TODO.md` — action items
- `docs/RESEARCH.md` (this file) — external research input + synthesis + decisions

---

## Day 3 — 2026-05-27 evening (5-slot Kaggle submission research)

### Context at time of research
- Time pressure: ~2 hours to Kaggle daily-slot reset at session start
- 5 slots remaining today; final 2 picks at deadline ~2026-06-02
- Current best: 0.653 real-inference / 0.671 diagnostic; leaderboard #1: 0.770
- Strategic shift: **research-before-commit**. CSVs in `submissions/` are floors, not commitments.
- Base CSVs ready: `track_A_day3_v1`, `track_A_day3_v2`, `track_B_day3_v1`, `track_C_day3_v1` (Slots 1-4); Slot 5 reserved.

### Prompts sent (4 angles, all with same core context, same final ask, same steelman section)

#### Prompt 1 — String Matching & Format Conventions
**Lens**: Kaggle-style automated math graders, LaTeX dialect equivalence (\dfrac vs \frac, \text{} wrapping), normalization conventions across MATH/GSM8K/AIME/Putnam
**Academic sources for**: evaluation methodology in math QA datasets, LaTeX rendering ambiguity, published normalization pipelines
**Status**: SENT — awaiting reply

[PASTE LLM RESPONSE HERE]

#### Prompt 2 — Test-Time Inference Optimization
**Lens**: test-time compute optimization for ≤7B reasoning models, SC variants, AIMO-2/Numina techniques, GenSelect, format-aware decoding
**Academic sources for**: inference-time optimization on small reasoning models 2024-2026, published SC variants
**Status**: SENT — awaiting reply

[PASTE LLM RESPONSE HERE]

#### Prompt 3 — Math/Logic & Creative Aggregation (the math one)
**Lens**: BEYOND-Bayesian creative algorithmic angles — information-theoretic submission design, differential probing math, ILP/MaxSAT formulation, adversarial back-solve from leaderboard, per-item entropy
**Academic sources for**: Bayesian experimental design, MaxSAT for combinatorial inference, ILP for binary classification with sparse linear constraints, rank-based inference from aggregate signals
**Status**: SENT — awaiting reply

[PASTE LLM RESPONSE HERE]

#### Prompt 4 — Math Problem Format Conventions
**Lens**: source-corpus identification (WeBWorK vs Putnam vs AIME vs Olympiad), corpus-specific format rules, identifying problem provenance from text
**Academic sources for**: WeBWorK answer format specifications, Putnam/AIME answer encoding conventions, LaTeX rendering norms
**Status**: SENT — awaiting reply

[PASTE LLM RESPONSE HERE]

### Synthesis across prompts (fill after all replies in)

**Common recommendations across LLMs:**
- 

**Conflicting recommendations:**
- 

**New ideas not in our current plan:**
- 

**Format probes worth running:**
- 

**Information-gain submissions worth running:**
- 

### Decisions taken on 5 slots

| Slot | File / variant | Rationale | Source (prompt #) |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

### Results (fill after Kaggle scores land)

| Slot | Submitted file | Kaggle score | Surprise/expected | Inference for next slot |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

### What we learned (post-session)
- 

### Carryover to Day 4
- 

---

## Day 4 — TBD

(placeholder)

---

## Day 5 — TBD

(placeholder)

---

## Past research / thinking — to be consolidated

**TODO**: search repo + Drive for older research/thinking docs (answer sheet methodology, back-solve framework, OPL design, SFT v5/v7 analysis, etc.) and either:
- Append summaries here (one section per topic), OR
- Move full docs to `docs/archive/` with index entries here

Candidates to search for:
- Back-solve methodology (was in Drive as "Back-Solve Mathematical Framework" id 1Cs14P3H2eHKpe1Z0myqG1XikKMoqqIUxfRTbWQ5LDfM — captured in FINDINGS.md)
- Earlier research session summaries (any "research" or "thinking" titled docs in Drive or repo)
- W-tier analysis (in `results/w_tier_confidence_analysis.csv`)
- OPL design docs
- SFT postmortems
