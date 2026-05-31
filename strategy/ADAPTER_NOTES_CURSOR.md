# ADAPTER NOTES (CURSOR) — Phase A repo read

Date: 2026-05-31  
Mode: Co-investigator read (next-attempt oriented, not QA)

## Scope and evidence used

This note is based on a full read of adapter-related sources requested in Phase A:

- `inference/adapters/sft_v1_postmortem/` (`.py` scripts + dataset metadata)
- `inference/adapters/sft_v3/` (training log, config, scripts, checkpoint eval artifacts)
- `inference/adapters/sft_v4/` (training + checkpoint compare scripts, untracked notes)
- `inference/adapters/sft_v5/` (training script + run findings)
- `inference/runs/adapters/sft_v5/` (`README.md`, `findings.md`)
- `inference/RESEARCH.md`, `inference/TODO.md`, `inference/SCRATCH.md`, `inference/FINDINGS.md`
- `strategy/CLAUDE.md`
- `research/` (all files in this repo folder)
- `postprocessing/RESEARCH.md`, `postprocessing/FINDINGS.md`
- `inference/base_model/*/findings.md` with adapter-relevant signal (especially R08/R09/R10/R20/R20b)
- `inference/results/sft_v4_adaptive/` (`run_meta.json`, `samples.jsonl` summarized, `submission.csv` summarized)
- `inference/scripts/run_hybrid_inference.py`, `inference/scripts/eval_adapter.py`
- checkpoint metadata: `checkpoints/sft_v4/checkpoint-588/adapter_config.json`, `checkpoints/sft_v5/checkpoint-1176/adapter_config.json`

---

## Attempt-by-attempt extraction

## SFT v1 (3-arm postmortem era)

- Training dataset (source/size/composition)
  - Three primary arms: OpenR1 1k, Numina concise 1k, Frugal traces target 1k (actual file row count: 678 for Frugal output file in repo), plus later Numina concise v2 8k artifact.
  - Data generated from external corpora/teacher traces (`OpenR1-Math-220k`, `NuminaMath-1.5`, `Frugal-Thinking-4B` generation pipeline), not curated around known private-943 misses.
  - Early datasets were not consistently scaffolded to the same `<think>...</think> + final boxed` completion format as later v3+ datasets.
- Training hyperparams
  - Script supports QLoRA via Unsloth with defaults: rank 16, alpha 32, lr 2e-4, cosine schedule, batch 2, grad_accum 4, warmup 0.03, weight_decay 0.01, optimizer `adamw_8bit`, full-linear target modules, no LoRA dropout, gradient checkpointing enabled.
  - Run-history docs tie the catastrophic failure to effective max sequence truncation (`max_seq_length=4096` in that run context), even though script CLI supports larger values.
- Eval methodology
  - Smoke/eval runs on small slices (R11-R14 family) and qualitative no-box behavior checks.
  - No robust held-out-in-private scoring gate that isolates generalization to unseen items.
- Result (numerical)
  - Catastrophic behavior in early SFT-merged evaluations: severe no-box/rambling pathologies (R13: 0.14 on fixed50 before repetition-penalty rescue path).
  - Net adapter utility from this era considered failed; run history marks v1 as catastrophe.
- Root cause of failure/break-even
  - Primary: training-trace truncation mismatch (long reasoning traces cut during SFT) causing learned "ramble/no final box" behavior.
  - Secondary: objective/selection mismatch (data not targeted to stable private-set misses, and evaluation did not protect against pathologies early enough).
- One thing to change next attempt
  - Hard gate: pre-train token-length profiling + guaranteed no-truncation setting (p99+ headroom), with immediate abort on no-box pathology in held-out eval.

## SFT v3

- Training dataset (source/size/composition)
  - `sft_v3_dataset_final.jsonl`: 594 examples.
  - Tier mix: R1/R2 392, W2 154, W1 48.
  - Teacher distribution (from config): Sonnet 366, GPT-5.4 104, GPT-OSS 23.
  - Format compliance in final dataset: 594/594 with `</think>`, 594/594 with `\boxed{}`.
- Training hyperparams
  - Base: `Qwen/Qwen3-4B-Thinking-2507`.
  - LoRA: r=64, alpha=128, dropout=0.05, target modules q/k/v/o + gate/up/down.
  - Train: 8 epochs, bs=2, grad_accum=8 (effective 16), lr=2e-4, cosine schedule, wd=0.01, bf16, max_length=4096, packing off, optimizer `adamw_torch`.
  - Custom assistant-only masking collator used due to TRL API changes/template limitations.
- Eval methodology
  - Dry run (2 steps), smoke tests on 10 random training items at selected checkpoints.
  - Memorization check against teacher answers on smoke items.
  - No true held-out private-943 validation gate before checkpoint selection/deployment.
- Result (numerical)
  - Training looked "successful" internally (loss near 0 by epoch 8, smoke formatting pass).
  - Competition outcome documented as poor: Kaggle ~0.452.
- Root cause of failure/break-even
  - Evaluation proxy mismatch: training/smoke/memorization metrics rewarded in-sample reproduction.
  - Dataset weighting/composition likely over-emphasized easy/reinforcement items and did not focus enough on persistent misses.
- One thing to change next attempt
  - Replace in-training memorization proxies with a locked held-out private-derived validation slice (never used in training) as the sole checkpoint-selection gate.

## SFT v4

- Training dataset (source/size/composition)
  - 391-item "clean" dataset (`data/sft_v4_dataset.jsonl`), with MCQ options and xhigh exclusions.
  - Repo-level summary indicates this run is still under-documented historically; this read resolves the concrete script-level config.
  - Dataset has high MCQ-like share (~206/391 by user-message "Options:" shape).
- Training hyperparams
  - Same base model and LoRA rank family as v3 (r=64, alpha=128, dropout=0.05).
  - 8 epochs, bs=1, grad_accum=4 (effective 4), lr=2e-4 cosine, wd=0, max_seq_length=5500.
  - Selective checkpoint saving at epochs 4/6/8.
- Eval methodology
  - Checkpoint compare scripts score on tiny in-training sample subsets (5 MCQ + 5 free) with greedy decoding.
  - Adaptive inference artifact (`inference/results/sft_v4_adaptive`) uses hybrid route:
    - trained IDs (`n=391`) sampled at n=3;
    - untrained IDs (`n=552`) sampled at two temperatures with n_per_temp=8 + shape filter.
  - This is better than pure train-only eval but still mixes evaluation logic with training-membership routing.
- Result (numerical)
  - Registry score around 0.597.
  - Better than v3, still materially below strong base inference stacks.
- Root cause of failure/break-even
  - Improved formatting/memorization did not translate into broad out-of-training correctness gains.
  - Checkpoint selection still anchored to in-training or tiny probes, not a robust held-out criterion.
  - Routing complexity (`trained` vs `untrained` strategy) risks overfitting policy logic to known IDs without proving net uplift.
- One thing to change next attempt
  - Ban training-ID-aware checkpoint selection and force one universal held-out metric; if routing is used, evaluate routing policy on disjoint held-out IDs only.

## SFT v5

- Training dataset (source/size/composition)
  - 391-item dataset (`data/sft_v5_dataset.jsonl`) derived from v4 lineage, with 14 trace fixes and lettered MCQ handling.
  - Composition remains similar to v4 footprint, still not primarily built from persistent hard-miss target set.
- Training hyperparams
  - LoRA same rank family: r=64, alpha=128, dropout=0.0.
  - 16 epochs, bs=4, grad_accum=1 (effective 4), lr=2e-4 linear schedule, wd=0.
  - Save every 196 steps (~2 epochs), auto-resume enabled.
  - Adapter config confirms inference-mode LoRA over same target modules as v4/v3.
- Eval methodology
  - Chosen by `memo_test_v5.py` using 20 training-set items (20/20 consistency).
  - Real competition check later showed this metric was non-predictive for objective performance.
  - Findings doc now explicitly locks "held-out required" discipline correction.
- Result (numerical)
  - Near break-even with base (~0.646 range).
  - Did not deliver meaningful general uplift despite strong memorization behavior.
- Root cause of failure/break-even
  - Core methodological bug: training-set memorization metric used as viability criterion.
  - Structural data mismatch: training mix overly easy/general rather than concentrated on known persistent failure set.
  - General-improvement framing remained too broad; adapter likely needs scoped deployment to trained domains.
- One thing to change next attempt
  - Evaluate only on non-training held-out slice and reject any run that does not beat base on that gate, regardless of memorization score.

---

## Cross-cutting extraction (for next adapter attempt)

## Common failure modes across attempts

- Proxy-metric collapse: success declared on smoke/memorization/in-training checks that are weakly correlated with Kaggle delta.
- Objective mismatch: training for "overall improvement" on mixed/easy-heavy sets underdelivers against a tiny persistent hard-miss subset.
- Evaluation contamination risk: route/checkpoint logic repeatedly touches training membership and can leak optimism.
- Format-vs-math confusion: many misses are format-recoverable via normalizer; adapter effort was often spent where postprocessing had higher EV.

## Hardware and compute constraints discovered

- Training itself is not the bottleneck (reported ~30-36 min scale for v3/v5 on H100 class hardware).
- Operational fragility matters: environment/library compatibility (TRL API shifts, CUDA paths, cache location, LFS fetch) repeatedly consumed setup time.
- Inference-time adapter evaluation at full scale is the bottlenecked decision stage; cheap but misleading local metrics are abundant.

## Data quality issues that limited results

- Early v1 data had trace-length mismatch to train config, creating pathological behavior.
- v3-v5 datasets were not explicitly centered on stable, independently verified hard misses.
- Gold/source ambiguity in some items (notably formatting/option-map artifacts) can poison adapter target selection unless filtered.

## Evaluation methodology pitfalls

- "20/20 memorization" on training examples is tautological and should be treated as anti-signal for deployment readiness.
- Tiny checkpoint probes on train items (5-10 examples) are useful for smoke only, not for model selection.
- Local score constructs can diverge heavily from Kaggle slice behavior; held-out protocol must be designed to mimic decision objective, not convenience.
- Adapter-vs-base comparisons require same decoding stack and consistent extraction/normalization assumptions; stack drift muddies causal claims.

## What was learned about Qwen3-4B-Thinking-2507 for SFT

- The model is sensitive to trace-format/truncation mismatch: wrong sequence budget can induce no-box rambling failure modes.
- LoRA rank family used (r=64, alpha=128) is not the primary limiter; dataset targeting + evaluation discipline dominate outcomes.
- "General uplift" from broad SFT is weak at this scale; the plausible value proposition is targeted memorization/use-on-known-failures.
- Adapter should stay unmerged unless explicitly needed; merge-era pathologies from earlier runs caution against conflating merge effects with adapter quality.

## Open questions / unknowns to resolve before proposing v7

- Which exact item set should define "targeted memorization" scope (size, independence criteria, format-clean constraints)?
- What held-out protocol best predicts Kaggle improvement for this specific route (strict, value-equal, or both with decision thresholds)?
- Should deployment use explicit route-by-item (trained IDs only) vs confidence agreement between base/adapter?
- How much of prior adapter underperformance is data curation vs decoding/eval stack mismatch?
- Is teacher-source consistency (single-teacher vs mixed) materially causal here, or confounded with dataset quality/selection?

---

## Practical implications (Phase A only)

- The dominant lesson is methodological: next adapter attempt fails fast unless it beats base on non-training held-out items.
- The second lesson is scoping: adapter should be built and judged as a targeted-error lever, not a broad global-improvement lever.
- The third lesson is separation-of-concerns: keep format recovery in normalizer; reserve adapter capacity for genuine math misses.
