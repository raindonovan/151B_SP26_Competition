# Phase D — v7 Adapter Plan (v3, post-3-LLM-followup-and-verification)

**Status**: Supersedes v2 (commit 49e8da6, archived). v1 also archived. v3 incorporates the follow-up answers from Opus 4.8, ChatGPT (browsed), and Gemini, plus my own independent web verification of Qwen3-4B dense architecture, Numina + imagination-research practitioner patterns, Thinking Machines LoRA Without Regret, and vLLM multi-LoRA capabilities at 6-slot parallel serving.
**Optimization target**: **maximum probability of beating 0.745**. Risk minimization > peak performance.

---

## 1. What changed in v3 vs v2 (and why)

| Change | Driver | Impact |
|---|---|---|
| Dual-variant pilot (80/20 vs 95/5 in parallel) | ChatGPT explicit endorsement + Gemini confirming VRAM cost ≈ 0 | 2× shots on goal at no marginal cost |
| Pilot reframed as **plumbing + A/B selection, NOT accuracy gate** | Opus's strongest reframe | Pilot can't predict full-train accuracy at different item count; final gate is per-item route-sim on full train |
| Pilot size dropped 50 → 30 | Opus literature check (no <50-item pilot validates to full train) | Saves ~20 min, frees buffer |
| **Phase 4 collapsed via 6-LoRA simultaneous serving** | Gemini's confirmation `max_loras=6 max_lora_rank=64` costs only 1.54 GB on A100 80GB | ~30 min saved, eliminates cold-start variance |
| **Offline DeepConf added to Phase 5** | Gemini pivot from V1 patches to offline post-processing | ~20 min for +confidence-weighted voting, near-zero risk |
| GPU utilization tightened — both GPUs busy in every phase | Rain's "don't ignore 2× A100" directive | Total wall time ~4h50m vs 5h15m in v2 |
| vLLM version pinned: **0.10.2 or 0.11.1** | Gemini's regression survey | Avoids 0.6.4 async slot lockout + 4 other known bugs |
| Operational flags locked: `--enforce-eager`, `--max-loras` = pool size | Gemini's gotcha list | Prevents CUDA graph hangs + LRU eviction bugs |
| MoE concern resolved: Qwen3-4B verified dense | Independent web verification (official Qwen blog) | FlashInfer assertion bug doesn't apply |

What did NOT change vs v2:
- LoRA hyperparameters (r=64/α=128/drop=0, LR=2e-4, batch=4, all 7 linear layers) — v5 already TM-optimal
- Composition lever: Qwen-wrong residual targeting
- Strategy: Option C (pilot → gate)
- Per-item route-sim as the production gate

---

## 2. Verified citations (sources I personally fetched or directly read in repo)

| # | Source | Status | What it gives |
|---|---|---|---|
| 1 | docs.vllm.ai/en/latest/api/vllm/lora/peft_helper/ | ✅ Personally fetched | DoRA validator blocks `use_dora` |
| 2 | github.com/vllm-project/vllm/pull/11003 | ✅ Personally fetched | DoRA explicitly listed as unsupported feature in PEFTHelper |
| 3 | github.com/vllm-project/vllm/pull/14389 | ✅ Personally fetched | DoRA PR "wants to merge", NOT merged |
| 4 | github.com/vllm-project/vllm/issues/10849 | ✅ Personally fetched | Open with "keep-open" label, no PR linked |
| 5 | huggingface.co/blog/winning-aimo-progress-prize | ✅ Personally fetched | Numina used 4 validation sets (AMC, AIME, MATH-L4, MATH-L5); did NOT use LoRA |
| 6 | github.com/imagination-research/aimo2 | ✅ Personally fetched | AIMO2 2nd place; validation = AIME 2025 (30) + ref (10) = 40 items; sample+aggregate accuracy; NO LoRA per ChatGPT's independent check |
| 7 | thinkingmachines.ai/blog/lora | ✅ Personally fetched | All-layer LoRA + LR ≈10× FullFT + small batch |
| 8 | qwenlm.github.io/blog/qwen3 | ✅ Personally fetched | Qwen3-4B is DENSE (not MoE — Qwen3 MoE is only 30B-A3B and 235B-A22B) |
| 9 | docs.vllm.ai/en/v0.9.2/examples/offline_inference/multilora_inference.html | ✅ Personally fetched | Multi-LoRA offline inference supported |
| 10 | **Internal: v5 adapter_config.json** | ✅ Read in repo | v5 already uses all 7 linear layers |
| 11 | Gemini follow-up (multi-LoRA VRAM math) | ✅ Receipt this session | 6 × 64 × 28 × 7 × 2 × 2560 × 2 bytes = 1.54 GB pre-allocated |
| 12 | Gemini follow-up (DeepConf formulas) | ✅ Receipt this session | Token c_i, trajectory C_t, LGC score S_t, weighted aggregation R(a) |
| 13 | ChatGPT follow-up (imagination-research no-LoRA) | ✅ Receipt this session | Their --finetuning_type full confirms no adapter precedent |
| 14 | Opus follow-up (data repetition on Qwen3-4B) | ✅ Receipt this session | arXiv:2602.11149 tested on Qwen3-4B specifically; negative trajectories don't degrade |

---

## 3. The plan with 2× A100 utilization (per phase)

### Phase 0 — Wrong-residual manifest build (30 min) — **both GPUs busy**
- **claude_vscode**: Join `R20_eval_v1_sc8_p943_t32k_pp1.jsonl` with `MASTER_ANSWERS.csv`. Identify items where base SC@8 majority ≠ `sheet_best_answer` AND `sheet_confidence` is high (multi-teacher consensus or Wolfram). Output: `data/v7_wrong_residual.csv` with target ~200-400 candidates.
- **tnr-0**: Run base SC@16 on items 0-471 (first half of 943) at deploy temp 0.6 / top_p 0.95 / k=16. This upgrades our route-sim baseline from SC@8 to SC@16 for tighter vote-margin signal.
- **tnr-1**: Run base SC@16 on items 472-942 (second half) at same params. Sets up `--enforce-eager --enable-lora --max-loras=2` on vLLM 0.10.2+ (or 0.11.1).

**Phase 0 pass criteria**: ≥100 high-confidence wrong-residual candidates. If <100 → fall back to Option B (skip v7).

### Phase 1 — Dual pilot training (45 min) — **both GPUs busy**
- **tnr-0**: Pilot A — 30 items (24 wrong-residual + 6 anchors = 80/20), 4 epochs, ckpt every epoch. Hyperparameters identical to v5.
- **tnr-1**: Pilot B — 30 items (28 wrong-residual + 2 anchors = ~95/5), 4 epochs, ckpt every epoch.

### Phase 2 — Pilot eval + A/B select (30 min) — **both GPUs busy**
- **tnr-0**: Run paired base-vs-adapter SC@8 on Pilot A's 30 items + 10 anchors at deploy temp.
- **tnr-1**: Run paired base-vs-adapter SC@8 on Pilot B's 30 items + 10 anchors at deploy temp.

**Pilot evaluation rubric** (per ChatGPT's calibration):

| Pilot metric | Plumbing check | Directional gate |
|---|---|---|
| Loss descends across 4 epochs | Required | — |
| Adapter loads cleanly via LoRARequest | Required | — |
| Format compliance (parseable last `\boxed{}`) | ≥95% | ≥98% for green |
| Base-wrong residual flips correct under SC@8 | — | **≥30% = ship-worthy direction; 20-30% gray zone (only ship with zero anchor regression); <20% = abort** |
| Anchor regression (base-correct → adapter-wrong) | ≤2/10 | ≤1/10 for green |
| Net residual gain (flips − regressions) | — | ≥+20% of pilot |

**A/B winner selection rule** (from ChatGPT):
```
if (pilot_B.flip_rate >= pilot_A.flip_rate + 5pp
    AND pilot_B.anchor_regressions <= pilot_A.anchor_regressions + 1
    AND pilot_B.format_failure_rate <= 1%
    AND pilot_B.avg_length <= pilot_A.avg_length * 1.20):
    winner = "B (95/5, aggressive)"
else:
    winner = "A (80/20, conservative)"

if both fail plumbing OR both <20% flip rate:
    ABORT v7, ship Pick B intermediate
```

### Phase 3 — Full v7 train of winner (90 min) — **both GPUs busy**
- **tnr-0**: Train full v7 on **180-200 items** (≥80% wrong-residual + ≤20% anchors per winning composition). 12 epochs, checkpoint every 2 epochs (saves: ep2/4/6/8/10/12). Same hyperparameters as v5. Log train-token-accuracy per checkpoint.
- **tnr-1**: 
  - First 60 min: write + smoke-test the offline DeepConf script (LGC over 512-token windows, R(a) = |T_a| × μ(S_t) weighted aggregation, per Gemini's formulas).
  - Last 30 min: run additional base sampling on hardest residual items (T4/T5) at SC@32 or SC@16 with higher k for tighter route-sim baseline on most-leveraged items.

### Phase 4 — Multi-LoRA simultaneous checkpoint eval (30 min) — **both GPUs busy**
**THE BIG COLLAPSE** — per Gemini's confirmation, all 6 checkpoints fit in one vLLM instance:
- **tnr-0**: `vllm serve <base> --enforce-eager --enable-lora --max-loras=6 --max-lora-rank=64`. Load all 6 v7 checkpoints (ep2/4/6/8/10/12) as separate `lora_int_id`s (1-6). For each item in trained set, dispatch 6 parallel SC@8 requests (one per checkpoint). SGMV kernel batches these into single fused forward passes.
  - Compute per-checkpoint per-item: `adapter_correct`, `adapter_vote_margin`, `format_compliant`, `train_token_acc`.
- **tnr-1**: Same multi-LoRA eval on **held-out validation slice** — items from the wrong-residual set that were NOT in the trained set (~10-15 items). This is our cross-check that the adapter generalizes to similar problems, not just memorizes trained ones.

**Checkpoint selection rule**:
```
best_ckpt = argmax over ckpts of (
    items_where_adapter_wins - 2 × items_where_adapter_regresses
), subject to:
    format_compliance >= 98%
    train_token_accuracy plateaued (delta vs prev ckpt < 1pp)
```

**Capacity overflow trigger** (Opus's check): if train-token-accuracy NEVER plateaus across all 6 checkpoints, that's evidence we need TWO adapters. In that case, train a second variant on the disjoint half of items in a hot patch (~45 min budget) — if time permits. Otherwise, ship the best of the six anyway.

### Phase 5 — Per-item routing + offline DeepConf integration (45 min) — **both GPUs busy**
- **tnr-0**: For each item in `route_to_adapter=True` set per the per-item gate, run adapter SC@8 at deploy temp. Save all 8 trajectories with `logprobs=True, top_logprobs=20`.
- **tnr-1**: Apply offline DeepConf voting (per Gemini's formulas):
  ```
  For each item with 8 trajectories:
    For each trajectory:
      c_i = -mean(log P of top-20 vocab) at each generation position
      C_t = mean(c_i) over all generated tokens (including <think>)
      S_t = LGC = min over sliding windows of size 512 tokens
    Group by parsed final \boxed{} answer
    R(a) = |T_a|^1.0 × mean(S_t over T_a)
    final_answer = argmax(R(a))
  ```
  Replace raw SC@8 majority with DeepConf weighted majority on adapter outputs.

**Per-item routing rule** (the deploy gate):
```python
def route_to_adapter(item_id, paired_eval):
    a_correct = paired_eval[item_id]["adapter_majority"] == gold
    b_correct = paired_eval[item_id]["base_majority"] == gold
    a_margin = paired_eval[item_id]["adapter_vote_margin"]
    b_margin = paired_eval[item_id]["base_vote_margin"]
    if a_correct and not b_correct:
        return True   # clear win
    if a_correct and b_correct and a_margin >= b_margin + 1:
        return True   # safe tie with margin
    return False     # base wins, both wrong, or tied without margin
```

Layer adapter answers (only on `route_to_adapter=True` items) into `submission/scripts/build_pickb.py` as a Qwen-derived override layer (per Day-8 final-pick rule).

### Phase 6 — Fire + Gradescope (20 min)
Apply `PICKB_FINAL_PREFIRE_CHECKLIST`. Submit Pick B FINAL to Kaggle. Submit code to Gradescope.

**Total wall time**: 30 + 45 + 30 + 90 + 30 + 45 + 20 = **290 min (~4h50m)**.
**Buffer to deadline**: ~5h. Generous for diagnostics + unexpected debugging.

---

## 4. v7 PRE-DEPLOY GO/NO-GO checklist (binding, expanded)

| # | Criterion | Threshold | Fallback if fails |
|---|---|---|---|
| 1 | Phase 0: ≥100 high-confidence wrong-residual candidates | hard | ABORT v7, ship Pick B intermediate |
| 2 | Phase 1: at least one pilot loads and trains without error | hard | ABORT, ship Pick B intermediate |
| 3 | Phase 2: at least one pilot has flip rate ≥20% AND anchor regression ≤2/10 AND format ≥95% | hard | ABORT, ship Pick B intermediate |
| 4 | Phase 3: full train completes 12 epochs, all 6 ckpts saved | hard | Use whatever ckpts saved; pick best per route-sim |
| 5 | Phase 4: per selected ckpt, items_won - 2 × items_regressed ≥ 10 | hard | Lower threshold to ≥5 OR ABORT |
| 6 | Phase 4: format compliance ≥98% on selected ckpt | hard | Pick later/earlier ckpt |
| 7 | Phase 4: held-out cross-check on tnr-1 — adapter wins on ≥30% of held-out items | soft (warning, not abort) | Reduce confidence in routing aggressiveness |
| 8 | Phase 5: routing manifest contains correct route_to_adapter=True/False per item | hard | Fix and re-verify |
| 9 | Phase 5: DeepConf weighted majority computed for each routed item | hard | Fall back to plain SC@8 majority |
| 10 | Phase 6: ≥1h budget remaining at Phase 5 entry | hard | Stop and ship Pick B intermediate |

---

## 5. Probability estimates (revised honestly)

| Path | P(beats 0.745) | Notes |
|---|---|---|
| A — Full train v7 now, skip pilot | 35-45% | v5 failed similar attempt |
| B — Skip v7, ship Pick B intermediate | 50-55% | Floor (no v7 downside, no v7 upside) |
| **C — Dual pilot → A/B select → single full train → multi-LoRA ckpt eval → per-item route + offline DeepConf** | **60-70%** | The current plan. C strictly weakly dominates B in expectation. |

If pilot passes: ~65-70%. If pilot fails: ~50-55% (= B). Expected over unknown outcome: 60-65%.

Best-case ceiling: if route gates ~30-50 items where adapter wins clearly, and ~10-15 happen to land in scored 283 slice, ~4-5pp Kaggle gain → ~0.74-0.79.
Floor: per-item routing + ChatGPT's conservative gate prevents regressions → floor ≈ Pick B intermediate.

---

## 6. Pre-mortem (most-likely failure modes)

**A — Proxy mismatch** (highest): training items don't overlap heavily with the 283-item scored slice. Adapter wins on trained items but those wins don't appear on Kaggle. **Mitigation**: per-item routing means no regressions either; floor ≈ Pick B. Bias trained items toward T3/T4/T5 (more likely overrepresented in scored slice).

**B — Trace incoherence on harder items**: Part 14.E refuted Part 8's hypothesis on at-risk subset (20 of 391 v5 items). v7's harder composition may surface trace incoherence we haven't tested. **Mitigation**: Phase 4 format compliance ≥98%. If breaks, abort.

**C — Time overrun**: pilot reveals slow learning; Phase 3 needs more epochs. **Mitigation**: hard ≥1h buffer check at Phase 5 entry. Abort if breached.

**D — vLLM multi-LoRA edge case at 6-slot serving**: Gemini's 6-slot math is theoretical. Could hit unknown serving bug. **Mitigation**: fall back to sequential ckpt eval (Phase 4 takes 90 min instead of 30; still fits budget).

**E — DeepConf offline post-processing bug**: Gemini's formulas could be subtly wrong (β=1.0, α=1.0, W=512 are educated defaults). **Mitigation**: keep plain SC@8 majority as fallback; DeepConf is a nice-to-have, not core.

---

## 7. Explicit NOT in v7 round 1

- DoRA (rejected, blocker confirmed)
- vLLM source patching for online DeepConf (3-4h risk per Gemini; offline pivot used instead)
- WiSE-FT alpha scaling (vLLM core doesn't expose per-request scaling)
- Confidence-gated routing via logits (no math-transductive practitioner threshold)
- Weight-merging adapters / TIES / DARE (Pattern B in Opus's framework — interference risk + violates merge lockout)
- Two full-train adapters by default (only if capacity overflow trigger fires per Opus)
- Kitchen-sink salvage (d6ea23e quicklook shows weak signal; killed)
- Spectral geometry weight checks (ChatGPT/Copilot single-source, no practitioner validation)
- Multi-validation-set Numina-style external benchmarks (we have one 943-item population)
- Trace regeneration (Part 14.E refuted Part 8)

---

## 8. Operational notes for execution agents

**vLLM launch flags (every inference run)**:
```
vllm serve Qwen/Qwen3-4B-Thinking-2507 \
  --enforce-eager \
  --enable-lora \
  --max-loras={pool_size_for_this_phase} \
  --max-lora-rank=64
```
- Phase 4: `--max-loras=6` (6 v7 checkpoints)
- Phase 5: `--max-loras=1` (winning checkpoint only)
- Pilot Phase 1-2: `--max-loras=1` per process (separate processes on tnr-0 and tnr-1)

**vLLM version**: 0.10.2 or 0.11.1 (per Gemini).

**Logprobs**: enable on all SC inference runs in Phase 4 and Phase 5 (`logprobs=True, top_logprobs=20`) so offline DeepConf has the data it needs.

**Sampling**: temperature=0.6, top_p=0.95, top_k=20 (Qwen3 official). All SC runs at k=8 unless specified.

---

## 9. Decisions still required from Rain (defaults sound)

1. **Authorize C (this plan)?** Default: YES.
2. **Pilot composition exact numbers**: 30 items each, 24+6 vs 28+2. Default: as-spec.
3. **Full train item count**: 180-200. Default: 200 (more is safer if labels are clean).
4. **Held-out cross-check size on tnr-1**: 10-15 items. Default: 12.
5. **Capacity overflow trigger threshold**: train-token-acc delta vs prev ckpt < 1pp on all 6 = no plateau. Default: yes.

(Operational decisions like vLLM version are locked above.)
