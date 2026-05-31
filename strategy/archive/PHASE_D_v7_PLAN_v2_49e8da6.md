# Phase D — v7 Adapter Plan (v2, post-deep-verification)

**Status**: This supersedes v1 (commit 286aaf9, archived at `strategy/archive/PHASE_D_v7_PLAN_v1_286aaf9.md`).
**Why v2**: v1 underweighted ChatGPT's browsed evidence (treated as duplicate of Copilot, which was wrong) and was too generous toward academic citations. v2 prioritizes practitioner evidence I personally verified online this session, and incorporates the per-item route-sim gate which is the strongest single risk-reducer surfaced by any of the 5 LLM consultations.
**Optimization target**: **maximum probability of beating 0.745**, not peak performance. Risk minimization > theoretical max.

---

## 1. What I verified online (independent, this session)

All of these were either accessed personally by me (via web_search/web_fetch) or were quotes from Opus 4.8/Gemini that match the public record.

| Claim | Source | Status |
|---|---|---|
| vLLM rejects DoRA at adapter load via `_validate_features` | docs.vllm.ai peft_helper.py + PR #11003 | ✅ Verified — production validator literally checks `use_dora` and errors |
| vLLM Issue #10849 "add DoRA support" still OPEN, no PR linked | github.com/vllm-project/vllm/issues/10849 | ✅ Verified |
| vLLM PR #14389 "Add DoRA Support" by ChloeL19 — "wants to merge", NOT merged | github.com/vllm-project/vllm/pull/14389 | ✅ Verified, still open with merge conflicts |
| Numina (AIMO1 winner) used FOUR validation sets to avoid public LB overfit | HuggingFace blog "winning-aimo-progress-prize" | ✅ Verified — AMC, AIME, MATH-L4, MATH-L5 |
| Numina did NOT use LoRA (full FT on 8x H100) — they lacked confidence vs full FT | Same source | ✅ Verified — informational, not a v7 constraint |
| Imagination-research AIMO2 (2nd place) validation = AIME 2025 (30) + reference (10) = 40 items, measuring both sample-level and aggregated accuracy | github.com/imagination-research/aimo2 README | ✅ Verified |
| Thinking Machines "LoRA Without Regret": all-layers > attention-only, LR ≈ 10× FullFT, small batch | thinkingmachines.ai/blog/lora | ✅ Verified |
| **v5's own LoRA config**: target_modules = q,k,v,o,gate,up,down (ALL 7 LINEAR LAYERS), LR=2e-4, batch=4, r=64, α=128, dropout=0, 16 epochs linear | `checkpoints/sft_v5/checkpoint-1176/adapter_config.json` + `train_sft_v5.py` | ✅ Verified directly in repo |

**Key implication**: v5's hyperparameters are already aligned with Thinking Machines best practice. So **changing hyperparameters is NOT where v7's gain comes from**. The opportunity is entirely in (a) training data composition, (b) checkpoint selection, and (c) per-item routing.

---

## 2. The single insight that should drive v7

From ChatGPT (the browsed response) + practitioner evidence:

**"Train an adapter, then deploy it only on the specific items where it provably beats base under final-sampling conditions. Treat every other item as base."**

This is sharper than "dual-path routing" because the routing decision is per-item, made AFTER training, based on actual paired SC evaluation. It converts the adapter into per-item lottery tickets where we only cash in winners.

Formally, for each candidate route ID:
```
route_to_adapter[id] = True if:
    (adapter_SC@8(id) == gold) AND (
        base_SC@8(id) != gold                          # clear win
        OR adapter_vote_margin(id) >= base_vote_margin(id) + 1   # safe tie
    )
else False
```

Items where adapter and base both win equally → route to base (conservatism, no format risk).
Items where adapter loses → route to base (regression refused).
Items where both lose → route to base (no opportunity, avoid downside).

This is risk-minimization built into the deploy layer. It's the difference between trusting the adapter globally and only trusting it where we have evidence per item.

---

## 3. What changes vs v5

| Element | v5 | v7 | Reason |
|---|---|---|---|
| LoRA target_modules | q,k,v,o,gate,up,down (all 7) | **same** | Already TM-optimal |
| r, α, dropout | 64, 128, 0 | **same** | Already TM-optimal |
| LR | 2e-4 | **same** (or 1e-4 if more conservative) | Within TM 1e-4 to 5e-4 range |
| Batch | per_device 4, accum 1 | **same** | Small batch already correct per TM |
| Epochs | 16 | **12 cap, checkpoint every 2** | Conservative; v5's epoch-12 pick was wrong, save room for earlier ckpts |
| LR scheduler | linear | **same** | No evidence to change |
| **Composition** | 87.72% T1+T2 Qwen-right | **≥80% Qwen-wrong residual + ≤20% anchors** | THE primary lever; v5 internal evidence |
| **Dataset size** | 391 items | **150-250 items** | Smaller, more curated, all verified |
| **Trace source** | Sonnet teacher | **same**, but only items where trace conclusion matches verified gold | Part 14.E refutation showed coherence works; still keep label-confidence gate |
| **Checkpoint selection** | 20/20 memo test | **Per-item route-sim score across 6 ckpts** | v5's failure mode |
| **Deploy gate** | Routing manifest assumes adapter wins on all trained items | **Per-item gate via paired base-vs-adapter SC@8** | New, ChatGPT's insight |

---

## 4. The plan (with explicit 2× A100 parallelism)

We have **two A100 80GB** instances (tnr-0, tnr-1) available. Total expected wall time **~5h** with parallelism, **~7-8h** without. We have ~10-11h to deadline. Plan fits with buffer.

### Phase 0 — Wrong-residual manifest build (30 min)
**A100 #1**: idle (or pre-warm vLLM)
**A100 #2**: idle
**claude_vscode (local)**: Join `R20_eval_v1_sc8_p943_t32k_pp1.jsonl` with `MASTER_ANSWERS.csv`. Identify items where:
- Base SC@8 majority ≠ `sheet_best_answer`, AND
- `sheet_confidence` is high (multi-teacher consensus or Wolfram verification), AND
- `sheet_best_answer` is not a placeholder
Output: `data/v7_wrong_residual.csv` with ~200-400 candidates.

**Pass criteria**: at least 100 high-confidence wrong-residual candidates exist (we know v5 had Kaggle score ~0.69 ≈ base accuracy on private 943 ≈ ~650 items right, so ~290 items potentially wrong; many of those are reliably labeled).

If fewer than 100 candidates → fallback to **B (skip v7)**. The lever doesn't exist.

### Phase 1 — Pilot training (60 min, parallel)
**A100 #1**: Train pilot adapter on 50 randomly sampled items from wrong-residual + 10 random anchors. 4 epochs total. Checkpoint every epoch. r=64/α=128, LR=2e-4, batch=4, linear scheduler.
**A100 #2**: Run base SC@8 on the **same 50 pilot items + 10 anchors** at deploy temp (0.6, top_p=0.95). This is the baseline for paired comparison.

This parallelism saves ~45 minutes. We're using one GPU to learn and the other to establish baseline simultaneously.

### Phase 2 — Pilot decision gate (30 min, sequential)
For each of 4 pilot checkpoints (epochs 1-4):
- Run adapter SC@8 on pilot items + anchors
- Compute per-item: adapter vote margin, correctness, base vote margin
- Aggregate: trained-item win rate, anchor regression rate, format compliance

**PILOT PASS CRITERIA** (binding — all three must be true on at least one checkpoint):
| Criterion | Threshold |
|---|---|
| Of pilot items where base was wrong, adapter is **right** (clear win) | ≥30% (so at least 12 of 40 wrong items flipped) |
| Anchor regression (base-correct items flipped wrong by adapter) | ≤1 of 10 |
| Format compliance (parseable `\boxed{}` on extracted last box) | ≥95% |

**If no checkpoint passes all three → ABORT v7. Fall back to Pick B intermediate.** This is the strongest protection against repeating v5's break-even outcome.

**If a checkpoint passes → Phase 3.**

### Phase 3 — Full v7 training (90 min, parallel)
**A100 #1**: Train full v7 on **150-250 items** = (≥80% wrong-residual + ≤20% anchors), 12 epochs, ckpt every 2 epochs (saves: ep2/4/6/8/10/12). Same hyperparameters as v5.
**A100 #2**: While training, run base SC@8 on the **full 943-item set** if not already done at deploy temp. This will be the per-item route-sim baseline.

### Phase 4 — Checkpoint selection (60 min, parallel)
For each of 6 checkpoints (ep2/4/6/8/10/12):
- Run adapter SC@8 on the trained items (~150-250 of them)
- Compute per-item paired score vs base

Best checkpoint = max(items_where_adapter_wins - 2 × items_where_adapter_regresses), subject to format_compliance ≥98%.

**A100 #1**: ckpts 2, 6, 10
**A100 #2**: ckpts 4, 8, 12 (in parallel)

### Phase 5 — Per-item routing manifest + Pick B integration (45 min)
1. For each trained-item ID, decide route_to_adapter[id] using the gate in §2.
2. Build routing manifest: source=adapter only on items passing the gate.
3. Run adapter SC@8 on items in `route_to_adapter=True` set, generate final answers.
4. Layer into `submission/scripts/build_pickb.py` as a new override layer (Qwen-derived per the locked Day-8 final-pick rule — no teacher overrides in submission_answer).
5. Apply the PICKB_FINAL_PREFIRE_CHECKLIST byte-diff + manifest review.

### Phase 6 — Fire + Gradescope (20 min)
Submit Pick B FINAL to Kaggle. Submit code package to Gradescope. Done.

**TIME TOTAL (with 2× A100 parallelism)**: 30 + 60 + 30 + 90 + 60 + 45 + 20 = **5h 15min**.
**Buffer**: ~5h for diagnostics, re-runs, or full-replan if Phase 2 fails.

---

## 5. v7 PRE-DEPLOY GO/NO-GO (binding, expanded from v1)

| # | Criterion | Metric | Threshold | Fallback if fails |
|---|---|---|---|---|
| 1 | Adapter loads cleanly via vLLM LoRARequest | One smoke call, 5 probe items | 100% load, sane outputs | STOP — diagnose; do not submit |
| 2 | Pilot passes ALL three Phase-2 criteria | win rate ≥30%, anchors ≤1/10, format ≥95% | All true on ≥1 ckpt | ABORT v7, ship Pick B intermediate |
| 3 | Selected ckpt: per-item route-sim shows ≥10 items where adapter clearly beats base (paired SC@8) | items_won - 2×items_regressed | ≥10 | Pick lower-epoch ckpt or ABORT |
| 4 | Format compliance on routed items | extract rate of last `\boxed{}` | ≥98% | Pick later ckpt or ABORT |
| 5 | Anchor regression on full 10-anchor panel | adapter wrong on base-correct items | ≤1/10 | ABORT |
| 6 | Per-item routing manifest correctness | unit test on 943-row file | 100% — adapter only on `route_to_adapter=True` items | Fix and re-verify |
| 7 | Pick B FINAL byte-diff vs intermediate | only `route_to_adapter=True` items changed | exactly the routed item count | Fix and re-verify |
| 8 | Time budget remaining at Phase 5 entry | wall clock | ≥1h before deadline | Stop and ship Pick B intermediate |

**Single hardest gate**: #2 (pilot). If pilot fails, do not push to full train. The pilot exists specifically to catch the failure modes that ruined v5.

---

## 6. Probability estimates (revised, more honest)

| Path | P(beats 0.745) | Reasoning |
|---|---|---|
| A — Full train v7 now, skip pilot | **35-45%** | v5 failed similar attempt. No proof we've fixed the underlying issue. Submission slot wasted on regression risk. |
| B — Skip v7, ship Pick B intermediate | **50-55%** | Current best. No v7 layer. Bounded upside but no v7 downside. Floor. |
| C — Pilot → gate full train | **55-70%** | Conditional. **If pilot passes**: ~65-70%. **If pilot fails**: ~50-55% (same as B). Expected over unknown outcome: ~55-65%. |

**Why C dominates B in expectation**: option value. The pilot costs ~1h, and either it tells us v7 will work (and we get a higher expected score) or it tells us v7 won't (and we ship B anyway, having spent ~1h vs ~5h). C is strictly weakly better than B in expectation, assuming the pilot is honestly diagnostic (which we engineered it to be — the per-item gate, not aggregate metrics).

**Best-case ceiling for v7**: if we route ~30-50 items where adapter clearly wins and ~10-15 of those happen to be in the 283-item scored slice, that's ~4-5pp Kaggle gain. So upper-bound Pick B FINAL ~ 0.74-0.79.

**Floor for v7**: per-item routing ensures no regressions. Floor = current Pick B intermediate score.

---

## 7. Pre-mortem — most likely failure mode if we ship and lose

**Hypothesis A — Proxy mismatch (highest probability)**: The wrong-residual set we trained on doesn't overlap heavily with the 283-item scored slice. Route-sim shows adapter wins on training items, but those wins don't appear on Kaggle. Result: 0-1pp net gain, no harm.
- **Mitigation**: maximize training set spread across the 943; deliberately include all difficulty tiers (T3/T4/T5 weighted heavier since they're likely overrepresented in scored slices); the per-item route gate prevents regressions even if proxy mismatch is severe.

**Hypothesis B — Trace coherence regression unique to harder items (medium probability)**: We refuted Part 8's trace-coherence hypothesis on the at-risk subset (Part 14.E), but the at-risk subset was 20 of 391 v5 items. v7's harder composition might surface trace incoherence we haven't tested.
- **Mitigation**: Phase 2 format compliance check (≥95% boxed). If format breaks, abort.

**Hypothesis C — Time overrun**: Pilot reveals adapter learns slowly and Phase 3 needs 16 epochs not 12, blowing the budget.
- **Mitigation**: Phase 5 #8 (≥1h budget remaining at integration entry). Hard abort if we breach.

**Hypothesis D — vLLM unmerged-LoRA serving issue at scale**: Hot-loading adapter for partial routing might have an edge case we haven't seen.
- **Mitigation**: Phase 0 includes a vLLM LoRARequest smoke call. v5 deployment worked in routing mode, so this is unlikely to be new.

---

## 8. What I am consciously NOT doing in v7 round 1

- **DoRA** (rejected, blocker confirmed)
- **WiSE-FT alpha scaling** (vLLM core text LoRARequest doesn't expose per-request scaling; offline copies = time we don't have)
- **DeepConf logprob voting** (Gemini provided concrete patches but ~2h integration time; defer)
- **Confidence-gated routing via logits** (calibration overhead with no math-transductive practitioner evidence)
- **Trace regeneration via teachers** (Part 14.E refuted Part 8's hypothesis; sticking with v5-style Sonnet traces)
- **Kitchen-sink salvage** (quicklook showed all 6 completed items <60% SC — weak; killed)
- **Spectral geometry weight checks** (ChatGPT/Copilot single-source signal, no practitioner validation)
- **Multi-validation-set Numina-style validation** (we have 943 items in one population; we sample within it, can't add external)

---

## 9. Verified citations (only sources I personally fetched or that match what I see in repo/web today)

| # | Source | URL | What it gives us |
|---|---|---|---|
| 1 | vLLM peft_helper.py | docs.vllm.ai/en/latest/api/vllm/lora/peft_helper/ | DoRA validation blocker (production code) |
| 2 | vLLM Issue #10849 | github.com/vllm-project/vllm/issues/10849 | DoRA feature request still OPEN |
| 3 | vLLM PR #14389 | github.com/vllm-project/vllm/pull/14389 | DoRA PR exists but NOT MERGED |
| 4 | HuggingFace blog: winning-aimo-progress-prize | huggingface.co/blog/winning-aimo-progress-prize | Numina's 4-validation-set discipline |
| 5 | imagination-research/aimo2 | github.com/imagination-research/aimo2 | AIMO2 2nd place validation pattern (40 items, sample+aggregate accuracy) |
| 6 | Thinking Machines LoRA Without Regret | thinkingmachines.ai/blog/lora | All-layers LoRA, LR 10× FullFT, small batch |
| 7 | HuggingFace TRL: lora_without_regret | huggingface.co/docs/trl/lora_without_regret | Reproduced TM findings, all-layer LoRA reduces memory while matching FullFT |
| 8 | Tinker LoRA Primer | tinker-docs.thinkingmachines.ai/lora-primer | Confirms LR 20-100× full FT for some models |
| 9 | **Internal: v5 adapter_config.json** | `checkpoints/sft_v5/checkpoint-1176/adapter_config.json` | Confirms v5 already used all-layer LoRA |
| 10 | **Internal: v5 train_sft_v5.py** | `inference/adapters/sft_v5/scripts/train_sft_v5.py` | Confirms v5 hyperparameters TM-aligned |

---

## 10. Decisions still required from Rain (none should block; defaults below are conservative)

1. **Strategy: A / B / C?** Default: **C (pilot → gate)**. 4/4 external LLMs agree; my analysis agrees.
2. **Pilot composition**: 50 wrong-residual + 10 anchors? Default yes.
3. **Full v7 composition**: 150 + 30 anchors? 200 + 40 anchors? Default: **180 wrong-residual + 35 anchors = 215 total** (in ChatGPT's range, slight bias to the larger end since labels are clean).
4. **Pilot win-rate threshold**: 30% of base-wrong items flipped? Default yes.
5. **Anchor regression cap**: ≤1/10 in pilot, ≤2/35 in full? Default yes.
