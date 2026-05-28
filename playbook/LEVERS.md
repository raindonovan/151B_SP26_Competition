# THE 5 LEVERS — Feasibility, ENG Time, Risk

**Updated**: 2026-05-28 (Day 4 start)
**Scoring**: Feasibility 1-10 (10 = high confidence we can ship). ENG time = engineering days, not wall time.

## Lever 1 — TIR (Tool-Integrated Reasoning) — Python execution during inference

| Aspect | Value |
|---|---|
| Expected gain | +5-10pp (literature: +23pp on AIME pattern-aware TIR) |
| Feasibility score | **5/10** (vLLM is the unknown; needs research) |
| ENG time | 1.5-3 days |
| Risk | vLLM doesn't natively support mid-generation pause. Wrapper required. Continuation finicky. |
| Prerequisite | R1 research must conclude vLLM is not a blocker |
| Status | **GATED on R1** |

**Why win**: Numina AIMO-1 winning technique. Addresses arithmetic errors AND produces clean numerical output. Statistics-heavy dataset (80% of B1-7) is exactly where Python excels.

**Why might fail**: vLLM mid-generation pause may not be supported. If we have to chunked-generate, throughput drops 5-10x — could blow Gradescope time budget.

## Lever 2 — Knowledge Distillation SFT v7

| Aspect | Value |
|---|---|
| Expected gain | +2-5pp |
| Feasibility score | **7/10** (we've done SFT before, infrastructure exists) |
| ENG time | 2-3 days (data gen Day 4 + train Day 5 + inference Day 6) |
| Risk | **Same failure mode as SFT v4/v5: trained adapter shows memorization on training items but break-even on test items.** |
| Status | **VIABLE pending postmortem** |

**Why win**: dataApp pipeline is built. SFT scripts are working. v5 checkpoint-1176 selection methodology is established. Better data curation (multi-teacher consensus on items Qwen actually gets wrong) is the differentiator from v4/v5.

**Why might fail**: Qwen3-4B may not benefit from teacher-trace distillation in the way the literature suggests for bigger models. v5 was near-break-even — v7 needs to show why this round is different.

**See**: POSTMORTEMS.md for v4/v5 adapter trial documentation.

## Lever 3 — GenSelect + PRM-guided Best-of-N

| Aspect | Value |
|---|---|
| Expected gain | +3-6pp |
| Feasibility score | **6/10** (GenSelect implemented but broke; PRM needs research) |
| ENG time | 0.5 days for GenSelect smoke + fix; +1 day for PRM if needed |
| Risk | **Qwen may be poor at self-verification (we already observed this).** Truncation issue in our PoC might be confounding — fix that first before concluding Qwen-as-judge is broken. |
| Status | **POSSIBLE — needs smoke test with fixed candidate input** |

**Why win**: NVIDIA AIMO-2 winning technique. We HAVE the implementation. Truncation issue is fixable.

**Why might fail**: If Qwen genuinely can't judge its own traces, GenSelect ceiling is low. PRM requires external model (Qwen2.5-Math-PRM-7B from HF) — fitting it alongside Qwen3-4B on A100 80GB requires R2 confirmation.

## Lever 4 — Hard-item SC amplification + Multi-mode ensemble

| Aspect | Value |
|---|---|
| Expected gain | +1-3pp |
| Feasibility score | **8/10** (existing infrastructure, free analysis on existing data) |
| ENG time | 0.5 days analysis + 1 day SC=16 bottom-200 run |
| Risk | Diminishing returns past SC=16. NoThinking 943 has 5.3% truncation. |
| Status | **READY** |

**Why win**: We already have hardest-30 SC=16 results unanalyzed AND NoThinking SC=8 full-943 unanalyzed. Pure free data.

## Lever 5 — Multi-slot expansion as generic post-processing

| Aspect | Value |
|---|---|
| Expected gain | +2-5pp |
| Feasibility score | **9/10** (no new infrastructure, fold into run_inference.py) |
| ENG time | 1 day |
| Risk | Multi-slot detection must be accurate — false expansion could regress single-answer items. |
| Status | **READY** (after Lever 1 or 2 ships) |

**Why win**: Wolfram findings — 79% of B1-7 items are pure multi-slot under-count. Generic expander applied universally in run_inference() is methodologically clean (not item-specific overrides).

---

## Composite ranking

| Rank | Lever | EV | Feas | ENG | Net score |
|---|---|---|---|---|---|
| 1 | Lever 5 (Multi-slot expansion) | +2-5pp | 9/10 | 1d | **Highest immediate win** |
| 2 | Lever 4 (Hard-item SC + multi-mode) | +1-3pp | 8/10 | 0.5d analysis | **Free data ready** |
| 3 | Lever 2 (SFT v7) | +2-5pp | 7/10 | 2-3d | Real gain pending postmortem |
| 4 | Lever 3 (GenSelect/PRM) | +3-6pp | 6/10 | 0.5-1.5d | Smoke test first |
| 5 | Lever 1 (TIR) | +5-10pp | 5/10 | 1.5-3d | HIGHEST EV but gated on R1 |

**Strategic note**: composite ranking sorts Lever 5 to #1 because feasibility is so high — but Lever 1 has the highest EV. The right play is parallel: ship Lever 5 in 1 day (free baseline boost), do Lever 4 free analysis (Day 4 AM), then commit to Lever 1 or 2 for the Day 5-6 big swing.
