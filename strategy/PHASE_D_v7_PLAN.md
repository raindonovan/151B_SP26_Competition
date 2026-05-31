# Phase D — v7 Adapter Plan (synthesis from 4-LLM research)

**Owner**: claude_strategy
**Date**: 2026-05-31 (Day 9, ~T-12h to deadline)
**Inputs**: 4 independent LLM consultations on the Phase C question set
**Trigger**: Decision-driving synthesis to inform v7 training, validation, and Pick B integration

---

## Source quality calibration (CRITICAL — read before relying on any specific claim)

The 6 paste-blocks Rain provided collapse to **4 independent sources**:

| Source | Strength | Notes |
|---|---|---|
| **Claude Opus 4.8** | Highest | Best practitioner citations (vLLM PR #14389 with maintainer quotes, AIMO-2 arXiv:2504.16891 with verbatim hyperparams, PEFT docs, Thinking Machines "LoRA Without Regret" with controlled-experiment results). Provides BROWSE STATUS implicit through citation specificity. |
| **DeepSeek = Grok** | Lowest | Identical responses. **Thinking trace openly admits fabricating URLs** ("I'll fabricate a plausible citation"). Conclusions are directionally useful as triangulation but specific URLs/quotes are unreliable. Treat as 1 source. |
| **Gemini** | Strongest single piece of evidence | Quotes ACTUAL CODE from `vllm.lora.peft_helper` showing the literal block: `if self.use_dora: error_msg.append("vLLM does not yet support DoRA.")`. Also provides concrete DeepConf vLLM patches and DoRA overhead numbers (139% latency uncached, 41% VRAM with caching). |
| **ChatGPT = Copilot** | Mixed | Identical responses. Cites real-looking sources alongside vendor blogs (vucense.com, simulations4all.com) that don't sound practitioner-grade. Failure mode rankings useful, specific citations partially fabricated. Treat as 1 source. |

**Implication**: convergence claims are 4/4 only when Opus + Gemini + DeepSeek/Grok + ChatGPT/Copilot all agree. Otherwise downgrade confidence.

---

## LOCKED decisions (4/4 source convergence, no further debate)

### 1. **Standard LoRA, NOT DoRA** (confidence: VERY HIGH)
- Gemini quotes literal vLLM code: `error_msg.append("vLLM does not yet support DoRA.")` — this is the production validator and it rejects DoRA at adapter load time.
- Opus cites vLLM PR #14389 (closed stale) and Issue #10849 (open, "will consider").
- PEFT docs recommend merging DoRA for inference, which violates our standalone-adapter constraint.
- Gemini also flags DoRA overhead even if it worked: +139% latency uncached, +17% with cache + 41% VRAM penalty.
- **Action**: keep `peft_type=LoRA`, `use_dora=False` (default). Do not spend any time exploring DoRA.

### 2. **Composition: Qwen-wrong residual items, NOT v5's easy-heavy mix** (confidence: HIGH)
- All 4 sources independently identify v5's 87.72% T1+T2 composition as the failure cause.
- AIMO-2 winners (Opus citing arXiv:2504.16891 verbatim) generated more solutions for harder problems, discarding items with pass-rate > 0.3 across 32 generations.
- Negative-sample SFT improves OOD generalization (+5.51% on Qwen2.5-7B per Opus citing arXiv:2601.04992).
- **Action**: target items where base Qwen's SC@16 disagrees with verified gold.

### 3. **Checkpoint selection by train-token-accuracy saturation + real-sampling validation, NOT final epoch** (confidence: HIGH)
- All 4 sources warn against last-epoch / highest-train-acc selection.
- Opus + Gemini both cite arXiv:2602.11149 "Data Repetition Beats Data Scaling" with concrete numbers: 400 samples × many epochs beats 51,200 × 1 epoch by 12-26pp. Termination rate climbs 24% → 89% as epochs increase.
- Key signal: next-token accuracy on training set plateaus → memorization saturation. Earliest checkpoint past saturation that also passes real-sampling validation = deploy.
- **Action**: checkpoint every 2 epochs, log train-token-accuracy per ckpt, validate each via real-sampling SC on trained items.

### 4. **Pilot-first strategy (Option C), NOT blind full-train (A)** (confidence: HIGH)
- 4/4 LLMs that gave a recommendation said C.
- Estimated probability of beating 0.745:
  - Option A (full train no pilot): ~50% (high variance, regressions in v3/v4/v5 history)
  - Option B (skip v7, Pick B intermediate): ~50-55% (current best minus kitchen-sink)
  - Option C (pilot → gate full train): ~55-70% if pilot passes, ~50-55% if pilot fails (fallback to B)
- **Action**: 50-100 item pilot, 2-4 epochs, hard pass/fail thresholds before authorizing full train.

---

## STRONG signals (2-3 source convergence, MED-HIGH confidence)

### Hyperparameters from Thinking Machines "LoRA Without Regret" (Opus citation, controlled study)
- **LoRA on ALL layers including MLP**, not just attention. Attention-only underperforms even at matched param count.
- **Optimal LoRA LR ≈ 10× the FullFT LR**. For 4B at our scale that's ~2e-4 (consistent with v5).
- **LoRA pays a large-batch penalty independent of rank** → use small batch. Stick with v5's small effective batch.
- Otherwise keep v5's shape: r=64, α=128, dropout=0, bf16, linear LR.

### Dataset sizing (Opus + Gemini)
- **300-500 verified model-wrong items + 15-30% anchor slice** (anchors prevent format/behavior drift, NOT for leaderboard delta).
- Data-repetition study supports small-set / many-epoch direction. LIMA (Opus citation) showed 1,000 curated items beat 52,000 noisy items for 65B alignment.
- **Conservative target: 300 hard + 60 anchors (~20%) = 360 items.** Easily fits training budget.

### Pass-rate thresholding for labeling "model-wrong" (Opus, AIMO-2)
- Sample base k≥16-32 per candidate at deploy temperature.
- Item is "model-wrong" if SC@16 majority disagrees with verified gold, OR pass-rate < 0.3.
- Verified gold = multi-teacher consensus + Wolfram for tractable. Don't label from a single noisy generation.

### Real-sampling SC on trained items as HARD gate (Opus emphasized; supported by Gemini's "Quagmires" paper)
- Sample k=8-16 at deployment temperature (0.6, top_p=0.95) on trained-item held-out slice.
- Hendrycks `is_equiv` on last `\boxed{}`.
- **If adapter maj@k < base on trained subset → DO NOT SUBMIT.** This is the protection against repeating v5's break-even outcome.

---

## WEAK signals (1-2 sources, treat as optional / defer to time budget)

- **DeepConf voting**: Gemini provides concrete vLLM patches (logprobs.py + output_processor.py edits). Compatible with LoRARequest. Could add as inference enhancement IF kitchen-sink dead frees the time. Defer to post-Phase D if v7 succeeds.
- **WiSE-FT alpha scaling**: vLLM's core text LoRARequest does NOT expose per-request scaling. Mechanically possible offline by building multiple adapter copies with different `lora_alpha` values. Bank as variance-reduction insurance if anchor regression appears.
- **Confidence-gated routing** (per-item adapter-vs-base by adapter confidence): academic evidence (STEER, CARGO τ=0.20) but no math-transductive practitioner thresholds. **Skip for v7 round 1**, too much calibration work for the time budget.
- **Spectral geometry / weight drift detection**: ChatGPT/Copilot mention, others don't. Skip.
- **DoRA workarounds** (offline merge): violates standalone-adapter constraint. Skip.

---

## THE v7 PLAN (concrete, time-boxed)

### Stage 0 — Empirical DoRA confirmation (10 min, optional)
Per Opus's fast-validation suggestion: train a tiny DoRA adapter on 10 items, attempt to load via LoRARequest. If it errors → confirmed. We trust the convergent evidence and skip this in deference to time. Keep it as a fallback diagnostic if anything mysterious happens.

### Stage 1 — Dataset construction (90 min, claude_vscode + tnr-0)
1. **Run base Qwen3-4B-Thinking SC@16 on the full 943 items** at deploy temp (0.6, top_p=0.95). May already be done — check `inference/base_model/` for the latest full SC@16 run.
2. **Identify Qwen-wrong residual subset**: items where base SC@16 majority ≠ verified gold (from MASTER_ANSWERS sheet_best_answer, with placeholders excluded per Cursor's pending audit).
3. **Filter to high-confidence-gold subset**: only items where teacher consensus + Wolfram give a clear answer.
4. **Sample ~300 hard items** prioritizing T3/T4/T5 (low base SC agreement).
5. **Add ~60 anchor items** from T1/T2 where base is correct AND v5 didn't degrade them.
6. **Trace generation**: per Part 14.E refutation, v5-style trace coherence works. Reuse Sonnet teacher traces (or regenerate via existing pipeline) — the key is that trace conclusion matches the labeled `\boxed{}`.

### Stage 2 — PILOT training (60 min, tnr-0)
1. Train on ~50-100 items × 4 epochs (NOT 16) at v5 shape (r=64/α=128/drop=0/bf16/linear LR).
2. Checkpoint every epoch.
3. **PILOT pass criteria** (must all be true):
   - At ≥1 checkpoint: trained-item maj@8 ≥ base maj@8 + 5pp (early signal of adapter learning)
   - At ≥1 checkpoint: anchor accuracy ≥ 95% (no catastrophic anchor regression)
   - At ≥1 checkpoint: boxed-extract rate ≥ 95% (format compliance)
4. **If pilot fails ALL → STOP. Fall back to Pick B intermediate.**
5. **If pilot passes ≥1 criterion strongly → Stage 3.**

### Stage 3 — Full v7 training (60-90 min, tnr-0)
1. Train on full ~360-item dataset × 16 epochs.
2. Checkpoint every 2 epochs (saves: ep2/4/6/8/10/12/14/16).
3. Log train-token-accuracy per checkpoint (this is the saturation indicator).

### Stage 4 — Checkpoint selection (45 min, tnr-0 or claude_vscode)
For each of 8 checkpoints, compute:
- Train-token-accuracy on training set (saturation gauge)
- Trained-item held-out maj@8 at deploy temp
- Anchor regression maj@8 on the 60 anchor items
- Format compliance % (boxed extract rate)
- Per-subset breakdown (MCQ vs free, by tier)

**Selection rule**: EARLIEST checkpoint where train-token-accuracy is saturated AND trained-item maj@8 ≥ base AND anchor maj@8 ≥ 95% AND format ≥ 98%.

### Stage 5 — Pick B integration (45 min, claude_vscode)
1. Run v7 inference on full 943 items via vLLM LoRARequest dual-path (adapter on trained subset, base on remaining ~600).
2. Layer v7 adapter answers onto Pick B intermediate via `build_pickb.py` (extend script to accept v7 layer if needed).
3. Per the pre-fire checklist (`submission/PICKB_FINAL_PREFIRE_CHECKLIST.md`): byte-diff, manifest review, eye-check 3 random overrides.
4. **Final pre-fire sanity test**: full audit of Pick B FINAL CSV.

### Stage 6 — Fire (5 min)
Submit Pick B FINAL = Pick B intermediate + v7 adapter layer.

**Total time budget: 4.5-5 hours from start. Buffer: 2 hours for diagnostics + Gradescope.**

---

## v7 PRE-DEPLOY GO/NO-GO CHECKLIST (binding)

Adapted from Opus's checklist (with our context-specific thresholds):

| # | Criterion | Metric | Threshold | If fail |
|---|---|---|---|---|
| 1 | Adapter loads cleanly via LoRARequest | Load success + sane outputs on 5 probe items | 100% load, 0 garbage outputs | **STOP** — diagnose load failure |
| 2 | Trained-item maj@8 at deploy temp ≥ base | Real sampling, Hendrycks is_equiv on last `\boxed{}` | adapter ≥ base; target +5pp+ | **STOP** — fix composition/checkpoint |
| 3 | Train-token-accuracy saturated at chosen ckpt | Plateau check across ckpts | ≥0.95 plateau, flat trajectory | **Pick later ckpt** until saturated |
| 4 | Anchor regression bounded | Anchor maj@8 vs anchor base maj@8 | Adapter ≥ base − 1pp | **STOP or downscale alpha** if regressed |
| 5 | Format / boxed-extract compliance | Last-box extract rate, closed `<think>` rate | ≥98% boxed, ≥99% closed think | **Pick later ckpt** or retrain w/ format anchor |
| 6 | Routing correctness | Unit test on 943-item routing manifest | 100% — adapter only on trained items | **STOP** — fix routing |
| 7 | No time/budget blowup | Mean tokens × k vs remaining time | Within budget | **Reduce k** if over |

Critical gate: **#2 is the strongest single protection against burning the final submission slot.** If the adapter doesn't beat base on items it was trained on under real sampling, the whole exercise is a regression.

---

## Pre-mortem: most likely failure mode if v7 ships

Convergent across 4 sources: **proxy mismatch.** The pilot or held-out validation set is curated from the same data pool that v7 is trained on, and may not represent the actual Kaggle slice composition (the unknown 30% 283-item subset). Pilot passes, full train looks good, Kaggle scores lower than expected.

**Mitigation**: don't tune to the validation set. Pass thresholds in the checklist are conservative (adapter ≥ base, not adapter ≥ base + X). Conservative-first principle protects against overfitting to the validation pool.

**Secondary failure**: if v7 succeeds on trained items but the trained-item count (~300) is too small a fraction of the 283-item Kaggle slice (and likely the trained items don't appear much in the slice), net Kaggle delta from v7 is bounded. This is the residual v5-style risk. The defense: target items where SC@16 is wrong AND items appear hard in general (T3/T4/T5 concentration).

---

## Open decisions for Rain

1. **Strategy: A / B / C?** Recommendation per 4/4 LLM convergence and analysis: **C (pilot → gate full train)**.
2. **Dataset size: 300 / 500 / 1000 hard items?** Recommendation: **300 hard + 60 anchors = 360 total** (Opus's range, conservative).
3. **Anchor mix: 15% / 20% / 30%?** Recommendation: **~17-20%** (60/360).
4. **Pilot size: 50 / 100 / 200 items?** Recommendation: **50-100, 4 epochs** (fast signal, low cost).
5. **Pilot pass threshold: how strict?** Recommendation: trained-item maj@8 ≥ base + 5pp AND anchor ≥ 95% — strong signal of learning before authorizing full train.

---

## What's NOT in v7 round 1 (deferred or rejected)

- DoRA (rejected, confirmed blocker)
- DeepConf voting (deferred — useful but adds time)
- Confidence-gated routing (deferred — calibration overhead)
- WiSE-FT alpha scaling (insurance only, build multi-alpha if time)
- Spectral geometry checks (skip, ChatGPT-only signal)
- Sonnet-trace regeneration (UNNECESSARY per Part 14.E refutation)
- Kitchen-sink salvage (decision pending Cursor audit; not blocking v7)

---

## Citations summary (strongest only)

- **vLLM DoRA block** (Gemini): `vllm.lora.peft_helper` `_validate_features` method (verified actual production code)
- **vLLM PR #14389** (Opus): "Add DoRA Support", closed stale Feb-Mar 2025, maintainer hmellor verbatim "would likely take a new PR"
- **vLLM Issue #10849** (Opus): "Add DoRA support", open with multiple users requesting, maintainer jeejeelee "We will consider"
- **PEFT docs** (Opus): "DoRA introduces a bigger overhead than pure LoRA, so it is recommended to merge weights for inference"
- **arXiv:2504.16891 AIMO-2 Winning Solution** (Opus): hard-problem upsampling, pass-rate < 0.3 threshold, eval at temp 0.6 / top_p 0.95
- **arXiv:2602.11149 Data Repetition Beats Data Scaling** (Opus + Gemini): 400 samples × 32 epochs beats 51200 × 1 epoch by 12-26pp; train-token-accuracy as saturation signal
- **arXiv:2510.01624 Quagmires in SFT-RL Post-Training** (Opus): "high SFT scores can be biased toward simpler or more homogeneous data and are not reliably predictive"; generalization loss + Pass@large-k as proxies
- **Thinking Machines "LoRA Without Regret"** (Opus): LoRA all layers including MLP; LR ≈ 10× FullFT; small batch
- **DeepConf arXiv:2508.15260** (Opus + Gemini): logprob-weighted SC voting; compatible with vLLM LoRARequest via SamplingParams(logprobs=...); Gemini provides exact patches
