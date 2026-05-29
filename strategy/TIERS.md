# CANONICAL TIER NAMING — LOCKED 2026-05-28

**Replaces all prior W1/W2/T1/T2 terminology.** From this point forward, ALL docs use these tier names.

| Tier | Confidence | Use case |
|---|---|---|
| **Tier 1 (T1)** | 95%+ certainty | Override-safe, no manual review needed |
| **Tier 2 (T2)** | 85-94% | Override-with-spot-check |
| **Tier 3 (T3)** | 75-84% | Manual review before override |
| **Tier 4 (T4)** | 60-74% | Strong candidate, requires verification |
| **Tier 5 (T5)** | 25-59% | Uncertain, low-confidence signal |
| **Tier 0 (T0)** | < 25% / unknown | No signal, do not use |

## Calibration

- T1 = "I would bet $100 of my own money on this being correct"
- T2 = "I would bet $50"
- T3 = "I would bet $25, but want a second opinion"
- T4 = "Signal exists but coin-flip-ish — needs verification before acting"
- T5 = "Weak signal, not actionable without corroboration"
- T0 = "Not enough information to assign a tier"

## Application

- **Wolfram HIGH overrides** → T1 (mathematical proof, verified)
- **Wolfram MED overrides** → T2
- **Multi-teacher unanimous (3-of-3 / 4-of-4)** → T2
- **Multi-teacher majority (2-of-3 / 3-of-4)** → T3
- **Single-teacher answer** → T4
- **Back-solve majority from score-weighted submissions** → T3-T4 depending on submission diversity
- **OPL OK-status direct match** → ~~T2 if similarity ≥0.95, T3 otherwise~~ — **DEAD as of Day 7**, see `data/search/opl/findings.md`. Do NOT use as a tier source. 0/39 alignment with teacher consensus.
- **Qwen SC=8 with ≥7/8 agreement** → T2 on free-form, T1 on MCQ
- **Qwen SC=8 with 5-6/8 agreement** → T3
- **Qwen SC=8 with 3-4/8 agreement** → T4
- **Qwen SC=8 with split (≤2/8)** → T5

## Old → New mapping

| Old term | New term |
|---|---|
| W1 (full unanimous) | T1 |
| W2 (3-of-4 agreement) | T2 |
| W3 (2-of-4 agreement) | T3-T4 depending |
| W4 (1-of-4 / split) | T5 |
| answer sheet T1 | Renamed: T1+T2 source pool |
| answer sheet T4 | Renamed: T4+T5 uncertain pool |

**Action**: Any new doc must use new naming. Old docs to be migrated as touched (not eagerly).
