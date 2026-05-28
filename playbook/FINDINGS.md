# PLAYBOOK FINDINGS

**Updated**: 2026-05-28 Day 4 EOD
**Note**: Findings specific to the 0.85 push. Competition-wide findings remain in `docs/FINDINGS.md`. Per-run findings live in `playbook/runs/<run_name>/findings.md`.

## F1 — Inference-only base is ~0.646. Combined gains from format/post-processing/overrides reached 0.692 (Day 3). The +4.9pp gross gain includes Wolfram overrides — NOT inference-only.

Corrected from earlier F1: the 0.692 figure conflates inference improvements with override-applied submissions. Inference-only (slot1_reformat) is 0.646.

| Type | Score | Δ from base inference |
|---|---|---|
| Real inference, no normalization | ~0.643 (slot1_minimal_norm) | baseline |
| Real inference + multi-answer reformat | 0.646 (slot1_reformat) | +0.3pp |
| Real inference + reformat + Wolfram overrides | 0.653 (slot1_wolfram_full_overrides) | +0.7pp |
| Real inference + Day 3 kitchen sink (71 overrides + Hendrycks transforms) | 0.692 (slot1/slot2) | +4.9pp **with overrides** |

**Inference-only honest read: we're at 0.646. Overrides add another +4.6pp on top.** The leader at 0.85 sits +15.8pp above slot1_reformat and +20.4pp above raw base. Format tricks alone won't close this.

## F2 — OPL is answer-sheet gold for ~30-40 items, not training gold

See `playbook/runs/opl_run/findings.md` for full analysis. Headline:
- 39 OK-status items with clean concrete OPL answers, all disagree with Qwen
- Realistic projection +3.6pp (lower) to +10-12pp (upper, with layering)
- Earlier "+5-12pp" projection was inherited speculation
- NOT training gold (no CoT traces)

## F3 — The "memorization 20/20" SFT v5 test was measuring the wrong thing

See `playbook/runs/sft_v5_run/findings.md`. Headline:
- The 20 test items were IN the v5 training set → memorization, not generalization
- Real test-set performance was near break-even with base
- **Discipline correction**: held-out validation set required before any future SFT is declared viable

## F4 — Wolfram says 79% of "wrong" items are format/multi-slot issues, not arithmetic errors

From `docs/WOLFRAM_FINDINGS.md`:
- 79% of B1-7 items are multi-slot under-count (Qwen emits last 1-2 slots of N-slot answer)
- 56% of B8 items: Qwen math correct, format wrong
- 700-750 of 943 items are HIGH-computable
- **Multi-slot expansion lever (Lever 5) attacks the dominant failure mode**

## F5 — RAIN'S INSIGHT: Targeted Memorization SFT (NEW LEVER 6)

If memorization on training items is reliable, that capability IS useful — for specific items we KNOW Qwen gets wrong.

**The play**: train SFT adapter on 200-300 verified-wrong items. Use selectively at inference (only for items the adapter was trained on, or with confidence routing).

**Differs from v1/v4/v5**: scope is narrower (memorize specific items), success metric is clearer (does it produce the verified answer for THOSE items), generalization is not claimed.

**Rules check**: SFT is explicitly permitted. Selective routing at inference is single-model technique. ALLOWED.

See `playbook/LEVERS.md` Lever 6 + `playbook/runs/sft_v5_run/findings.md` for full reasoning.

## F6 — Rules constraints (locked 2026-05-28)

Re-read of competition description revealed:
- **TIR / code interpreters / tool-augmented generation EXPLICITLY EXCLUDED at inference time**
- **External model calls EXCLUDED** (including separate PRM model)
- SFT, RL, prompt engineering, self-consistency all permitted

**Implications**:
- Lever 1 (TIR) is KILLED
- PRM-half of Lever 3 is KILLED
- Levers 2, 3 (GenSelect), 4, 5, 6 all rules-permitted

**Hardcoded overrides are gray zone** — technically allowed by strict read, probably violate spirit. Off-table until Day 7 per Rain.

## F7 — Submission scarcity

5 days × 3/day = ~12 submissions remaining. Each must test a deliberate hypothesis. At deadline: 2 final picks.
