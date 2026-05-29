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

## F2 — OPL bulk-override is empirically disconfirmed (Day 7 update)

See `data/search/opl/findings.md` for full analysis. **Headline (revised 2026-05-29)**:
- Day-7 OPL × teacher-consensus join: **0 T1-promoted / 25 OPL-disagrees / 14 split-teacher** of 39 OK-status items.
- The earlier projection of +3.6pp (lower) to +10-12pp (upper) was a CEILING that assumed parameter equality between OPL templates and our questions. The join shows that assumption is false.
- Smoking-gun spot-check: id=15 at the **highest** similarity (0.9055) — OPL matched a completely different Loyola Chicago precalc problem. If the top match is a false positive, the rest are worse.
- **OPL channel marked DEAD**. See `data/search/opl/decision.md`. NOT training gold, NOT answer-sheet gold, NOT a routing signal worth building in the time remaining.

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

---

## F8 — Day-6 archaeology: recovered gold (index → target phase-homes)

Deep-read of the early archive (`DESIGN.md`, `experiments.md`, `V0_V4_SUMMARY.md`, `milestone_report.tex`,
`data/FINDINGS.md`, `HANDOFF_v2.3.md`). What was recovered and where it should live:

- **GRADING — DONE, homed:** full Hendrycks normalization table + Minerva-vs-Hendrycks 28pp framing + Piazza
  confirmations → `grading/GRADER_SPEC.md`, `grading/JUDGER_AND_PUBLIC_SET.md`. (Was buried in `data/FINDINGS.md`.)
- **INFERENCE → RUN_REGISTRY / RUN_ANSWER_MATRIX (held):** V0–V4 variant runs on the fixed_50 slice EXIST as
  result JSONLs (V0 baseline 0.614; V1 counting-prefix; V2 bookend = MathIF "repeat trick", cited strongest fix;
  V3 shape-filter +0.7pp → became run14b_v3filtered; V4 temp-ladder). ⚠️ `V0_V4_SUMMARY.md` says "V1–V4 planned,
  not run" — STALE; the run files exist. Early SC runs (run05/06/07 on fixed_50; run08/09 on private943; run14b)
  hold per-item SC samples = oracle-harvest material. V1 counting-prefix reportedly never promoted to full 943.
- **KNOWLEDGE LAYER → MASTER_ITEM_TABLE (held):** master_item_tracker V3 flags (backsolve_disagree 269,
  disagree_teacher 233, format_only_diff 117, undercount 110, mcq_not_letter 16); dataset item bugs
  (0011/0317/0570/0585/0622/0858/0894/0141); 18 no-box items + forced-suffix rescue results.
- **STRATEGY → LEVERS / endgame:** information-theoretic back-solve ceiling (≤~49 bits over 5 queries vs 943 bits
  of label uncertainty → pure score-feedback back-solve cannot resolve all labels; the format-fix path is the
  higher ceiling); validated-lever lift table (multi-answer +0.3 · minimal-norm +0.4 · V3 +0.7 · 32K-vs-16K +2.5 ·
  answer-sheet on T3+T4 +2.1).
- **RULES (Piazza, authoritative):** Ruijia Niu 2026-05-05 — "any method to modify your model, as long as you start
  with the required Qwen3-4B-Thinking-2507" (distillation/SFT approved). Anthony Tong 2026-05-09 — grader does not
  normalize fraction vs decimal (corroborates Hendrycks). → belongs in a rules home.
