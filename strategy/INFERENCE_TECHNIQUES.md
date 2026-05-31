# Inference Techniques Inventory

**Updated**: 2026-05-28 Day 6

## Tried

| Technique | Runs | Result | Notes |
|-----------|------|--------|-------|
| SC@8 (base model, T=0.6) | run10, run14b | 0.646 (best inference-only) | Our primary inference method. Plateau at N=8 |
| SC@8 NoThinking | nothinking_sc8 | UNANALYZED | Prefill-based (enable_thinking is no-op on this model). Results exist, never scored or analyzed |
| SFT v3 adapter | sftv3_epoch8 | 0.452 | Broken — collapsed to repetition |
| SFT v4 adaptive | sftv4_adaptive | 0.597 | Below base — regression |
| SFT v5 (QLoRA, ckpt-1176) | adapter_v5_plus_run14b | 0.639 | Near break-even with base. 87% T1-easy training was structural issue |
| WiSE-FT (lora_alpha scaling) | Not run standalone | — | Discussed for v5 recovery; δ=0.5 recommended prior |
| Hardest-30 SC=16 | results/hybrid/tnr-A/ | UNANALYZED | Extended SC on 30 hardest items. Data exists. |
| GenSelect PoC | selection/ | UNANALYZED | Qwen judges its own candidates. PoC data exists, needs re-analysis |
| Multi-temperature voting | Not run | — | Sun et al. showed +7.3pp on Qwen3-4B. Never tried |

## Untried (candidates for remaining days)

| Technique | Expected impact | GPU cost | Priority | Notes |
|-----------|----------------|----------|----------|-------|
| **DeepConf@SC32/64** | +1-3pp (noisy at small N) | HIGH (32-64 samples × 943 items × ~50K tokens) | HIGH | Logprob-weighted SC voting. Needs `logprobs=N` on vLLM `SamplingParams` (NOT plumbed in `run_vllm_sc.py` — confirmed Day 9 audit). Fu et al. 2508.15260. See "Day-9 audit-derived recommendations" below for the targeted contested-slice variant. |
| **GenSelect (full re-run)** | +1-3pp | MEDIUM (2× base inference) | MEDIUM | Model ranks its own candidates. Prior PoC had truncation issues |
| **Multi-temperature voting** | +3-5pp (Sun et al.) | MEDIUM | MEDIUM | Vary T across SC samples. Direct empirical support on Qwen3-4B |
| **Diverse-prompt ensemble** | +2-4pp | MEDIUM | LOW | Dipper-style. Different prompt variants, vote across |
| **Targeted memo SFT v7** | Unknown | LOW (QLoRA training <1hr) | CONDITIONAL | Only after Core Q4 answered. Train on verified-wrong items only |
| **Universal-SC** | +1-2pp | LOW | LOW | Final cheap call picks most consistent among K candidates |

## Unanalyzed data (MUST DO)

These inference results exist but haven't been analyzed:
1. **NoThinking SC=8 full-943** — data exists at inference/results/. Never scored on Kaggle, never analyzed per-item.
2. **Hardest-30 SC=16** — at results/hybrid/tnr-A/. Check if any new correct answers.
3. **GenSelect PoC** — at inference/runs/selection/. Count items where correct was in pool but selector picked wrong.
4. **Oracle@8 on run14b** — for each item, does ANY of 8 SC samples match gold proxy? Ceiling for selection techniques.

## Key research references

- **DeepConf**: Fu et al., arxiv 2508.15260. Lowest Group Confidence filtering. 99.9% at 512 traces on AIME 2025.
- **Multi-temp voting**: Sun et al. on Qwen3-4B family. +7.3pp from temperature diversification.
- **Self-consistency**: Wang et al. 2023. Plateau at N=16-32 for AIME-level.
- **WiSE-FT for LoRA**: Dang/Baek COLM 2025. Scale lora_alpha by δ (δ=0.5 prior). No retraining.

## Day-9 audit-derived recommendations (filed for post-deadline / future iterations)

**Context**: Day-9 Phase-0 audit found that true log-likelihood SC re-voting on saved Qwen runs is not executable — `inference/scripts/run_vllm_sc.py` builds `SamplingParams` without `logprobs=N`, so per-sample dicts (`response`, `extracted_answer`, `gen_tokens`, `hit_token_cap`, `shape_rejected`, `temperature`) carry no token-level confidence signal. Confirmed against run14b_sc8 (32k) and matches `inference/base_model/FINDINGS.md` DeepConf entry.

**Recommendation R1 — Targeted-slice DeepConf re-run (high ROI, low cost):**
- Plumb `logprobs=20` into `SamplingParams` in `run_vllm_sc.py` (one-line change).
- Identify the **contested slice**: items where run14b SC8 margin ≤ 5/8, OR any of {hit_token_cap, shape_rejected, agreement_rate < 1.0}. Expected ~150–250 items.
- Re-run only the contested slice at SC@16 with logprobs on. Cost: ~30–60 min on A30 (vs. 6–8 hr for full 943 SC@32).
- Aggregate via DeepConf lowest-group-confidence weighting (Fu 2508.15260) — true logprob-weighted vote.
- Pick-B eligible (Qwen-only, no teacher overlay).

**Recommendation R2 — Save logprobs by default going forward:**
- Any future SC run should ship with `logprobs=N` enabled (N=10–20 sufficient). Storage overhead is small relative to response text.
- Unblocks DeepConf, perplexity-based filtering, and self-RAG-style verification across runs without re-inference.

**Recommendation R3 — Proxy-confidence SC re-vote (interim, no GPU):**
- For runs already saved without logprobs, a proxy vote can use `gen_tokens` (shorter = often more confident), `hit_token_cap` (penalize truncated), `shape_rejected` (mask), and agreement margin. Weaker than true DeepConf but executable on existing artifacts. Use only as tie-breaker, not standalone selector.
