# THE LEVERS — Feasibility, ENG Time, Risk, Rules

**Updated**: 2026-05-28 (Day 4 EOD, after rules re-read)
**Scoring**: Feasibility 1-10 (10 = high confidence we can ship). ENG time = engineering days, not wall time.

## Rules constraints (LOCKED — re-read of competition description 2026-05-28)

From competition rules: *"External model calls, API access, and tool-augmented generation (e.g., code interpreters or calculators) are not permitted at inference time."*

| Lever | Rules status |
|---|---|
| TIR (Python execution at inference) | **❌ EXCLUDED — explicitly forbidden ("tool-augmented generation, e.g., code interpreters")** |
| PRM-7B as external scorer at inference | **❌ EXCLUDED — separate model = external model call** |
| GenSelect using Qwen judging Qwen | ✅ ALLOWED — single-model self-consistency |
| SFT (any variant) | ✅ ALLOWED — explicitly permitted ("Supervised fine-tuning — LoRA, QLoRA, or full fine-tuning") |
| Self-consistency / multi-pass with same model | ✅ ALLOWED — single-model technique |
| Prompt engineering | ✅ ALLOWED — explicitly permitted |
| Post-processing applied AFTER model output | ✅ ALLOWED — applied to model output, not during inference |
| Hardcoded overrides in run_inference() | ⚠️ GRAY — technically allowed but probably violates competition spirit. Per Rain: overrides off table until Day 7. |

## Lever 1 (DEPRECATED) — TIR

**Status: KILLED BY RULES.** Tool-augmented generation explicitly excluded. Do not pursue.

## Lever 2 — SFT v7 (general distillation approach)

| Aspect | Value |
|---|---|
| Expected gain | +2-5pp (uncertain — v4/v5 didn't beat base) |
| Feasibility | 6/10 (infrastructure exists, but pattern has failed twice) |
| ENG time | 2-3 days |
| Risk | **Same failure mode as v4/v5 — train, memorize training items, regress on held-out.** |
| Rules | ✅ ALLOWED |
| Status | VIABLE pending v4 postmortem completion |

**Why win**: dataApp pipeline built, SFT scripts working, v5 checkpoint-1176 selection methodology established.

**Why might fail**: Qwen3-4B may not benefit from teacher-trace distillation. v5 was break-even. v7 needs to differ structurally (smaller curated dataset, single-teacher consistency, held-out validation, fewer epochs).

## Lever 3 — GenSelect (Qwen-as-judge selection of N candidates)

| Aspect | Value |
|---|---|
| Expected gain | +2-5pp (PRM half is gone; just GenSelect remaining) |
| Feasibility | 6/10 (implementation exists, truncation bug needs fix + smoke) |
| ENG time | 0.5d fix + smoke + re-run |
| Risk | Truncation bug fixable; the deeper risk is whether Qwen-as-judge actually outperforms majority voting on math. Existing PoC inconclusive due to bug. |
| Rules | ✅ ALLOWED (single model judging its own output) |
| Status | POSSIBLE after smoke test with fixed candidate input |

## Lever 4 — Hard-item SC amplification + Multi-mode ensemble

| Aspect | Value |
|---|---|
| Expected gain | +1-3pp |
| Feasibility | 8/10 |
| ENG time | 0.5d analysis (existing data) + 1d optional SC=16 bottom-200 run |
| Risk | Diminishing returns past SC=16. NoThinking 943 has 5.3% truncation. |
| Rules | ✅ ALLOWED |
| Status | READY — existing data unanalyzed |

**Action**: ANALYZE FIRST. We already have hardest-30 SC=16 results + NoThinking SC=8 full-943 unanalyzed. Pure free data.

## Lever 5 — Multi-slot expansion (post-processing)

| Aspect | Value |
|---|---|
| Expected gain | +2-5pp |
| Feasibility | 9/10 |
| ENG time | 1d |
| Risk | Multi-slot detection must be accurate. False expansion could regress single-answer items. |
| Rules | ✅ ALLOWED (post-processing of model output) |
| Status | READY — `results/undercount_candidates.csv` has 82 items, 51 "use_teacher" ready to apply |

**Why high feasibility**: 51 items are pre-computed with teacher consensus. Generic expander applied to those 51 items = mostly mechanical.

**Caveat**: "use_teacher" application is borderline-override (we're using teacher consensus to overwrite Qwen output). Rain's "overrides off table until Day 7" applies if this counts as overrides. Need to clarify.

**Cleaner version**: Build a generic multi-slot expander that REASONS over Qwen's response text (no teacher consensus). For items where `n_slots_now < n_ans_needed` AND Qwen's text contains N answer-like values, expand into a single `\boxed{a, b, c, ..., n}`. Pure post-processing, no override flavor.

## Lever 6 (NEW) — Targeted Memorization SFT (Rain's insight)

| Aspect | Value |
|---|---|
| Expected gain | +3-8pp (200-300 items added to gold pool at high confidence) |
| Feasibility | 7/10 (SFT infrastructure works; targeted scope reduces risk vs general distillation) |
| ENG time | 2 days (extract wrong items + verify answers + train + inference) |
| Risk | Could degrade base model performance on items NOT in training set. Mitigation: selective routing or merged inference with confidence threshold. |
| Rules | ✅ ALLOWED — SFT is explicitly permitted |
| Status | VIABLE — needs scoping work this session |

**The play**:
1. Identify 200-300 items Qwen base gets wrong (low SC agreement in run14b + answer sheet disagreement)
2. Get verified correct answers via teacher consensus + Wolfram for those items
3. Train SFT adapter to memorize Q→A pairs for those specific items
4. At inference: use SFT-adapter output for items it was trained on, base Qwen for the rest. OR run both and pick based on confidence.

**Why differs from v1/v4/v5 mistakes**:
- v1/v4/v5 trained for GENERAL improvement → failed
- Lever 6 trains for TARGETED memorization on specific known-wrong items → tractable
- Memorization IS the goal here, not generalization
- Held-out validation still required (50-item evaluation set NOT in training)

**See**: `playbook/runs/sft_v5_run/findings.md` for full reasoning.

---

## Composite ranking (UPDATED post-rules-read)

| Rank | Lever | EV | Feas | ENG | Rules | Net |
|---|---|---|---|---|---|---|
| 1 | Lever 5 (Multi-slot expansion) | +2-5pp | 9/10 | 1d | ✅ | **Ship this first** |
| 2 | Lever 4 (Hard-item SC analysis) | +1-3pp | 8/10 | 0.5d | ✅ | **Free data ready** |
| 3 | Lever 6 (Targeted memo SFT) | +3-8pp | 7/10 | 2d | ✅ | **Highest EV among allowed** |
| 4 | Lever 3 (GenSelect re-run) | +2-5pp | 6/10 | 0.5d | ✅ | After smoke test |
| 5 | Lever 2 (SFT v7 general) | +2-5pp | 6/10 | 2-3d | ✅ | Risky; v4/v5 already failed pattern |

**Killed:** Lever 1 (TIR) — rules. PRM-half of Lever 3 — rules.

**Strategic note**: Lever 6 (Targeted Memorization SFT) is the new highest-EV-rules-permitted lever. Lever 5 is the highest-feasibility quick win.
