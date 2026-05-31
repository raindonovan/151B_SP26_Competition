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

---

## Part 2 — Phase A redo, gap fills

### 1) v5 log reads (full) + extracted trajectory/anomalies

Files fully read:
- `inference/adapters/sft_v5/logs/adapter_v5_run.log`
- `inference/adapters/sft_v5/logs/memo_test.log`
- `inference/adapters/sft_v5/logs/preflight_smoke.log`

Supplemental for requested loss/grad trajectory (because the 3 requested logs are inference/preflight/memo logs, not trainer-step logs):
- `inference/adapters/sft_v5/training.log`

#### 1A. Training trajectory (loss/grad/lr) from `training.log`

- Parsed 313 trainer snapshots (`loss`, `grad_norm`, `learning_rate`, `entropy`, `epoch`) from the log stream.
- Overall trajectory:
  - `loss`: 0.9858 -> 0.000131 (min 0.000039)
  - `grad_norm`: 3.712 -> 0.001323 (min 0.000671)
  - `learning_rate`: 1.013e-05 -> 5.373e-07 late in run snapshots
  - `epoch` coverage in snapshots: 0.05 -> 15.97
- Anchor points:
  - epoch ~1.02: loss 0.2559, grad 0.3716
  - epoch ~4.03: loss 0.05217, grad 0.5337
  - epoch ~8.01: loss 0.007375, grad 0.09479
  - epoch ~12.04: loss 0.000698, grad 0.002431
  - epoch ~14.03: loss 0.000070, grad 0.002576
- Final trainer summary line:
  - `train_runtime=1736s`, `train_loss=0.0571`, `mean_token_accuracy=1`, `epoch=16`.

Interpretation:
- Optimization converged strongly (very low late-step losses, near-zero gradients).
- No evidence in trainer metrics of instability (no NaN/OOM/traceback), so the break-even outcome is not explained by failed optimization dynamics.

#### 1B. `preflight_smoke.log` findings

- Final gate summary: 7/7 PASS (`Prompt format`, `Model load`, `Generation smoke`, `Shape filter`, `Resume`, `Adapter consistency`, `Output format`).
- Smoke generation examples showed boxed outputs on all tested items (`5/5 produced \boxed{}`).
- Adapter-consistency mini-test: 5/5 items were `3/3` match.
- Notable operational signal: one very slow probe (`ID 10`, ~98s in adapter-consistency section), but still successful.
- Minor warnings only (vLLM env warning, NCCL teardown warning), no execution-blocking errors.

#### 1C. `memo_test.log` per-checkpoint/per-item outcomes

Test set in log:
- MCQ IDs: `[1, 3, 10, 13, 23, 34, 38, 47, 53, 69]`
- FREE IDs: `[14, 15, 31, 39, 42, 48, 52, 56, 59, 60]`

Per-checkpoint results:
- Epoch 8 (`checkpoint-784`): 19/20, failed `ID 13` (`label C`, got `['C','D','D']`)
- Epoch 12 (`checkpoint-1176`): 20/20
- Epoch 14 (`checkpoint-1372`): 19/20, failed `ID 10` (`label E`, got `['C','C','E']`)
- Epoch 16 (`checkpoint-1568`): 19/20, failed `ID 10` (`label E`, got `['C','E','E']`)
- Winner: epoch 12; log explicitly states: `No merge -- keep as LoRA adapter.`

This is meaningful as an in-training consistency test, but not sufficient as deployment selection (details in section 6).

#### 1D. `adapter_v5_run.log` trajectory/anomalies

- This file is full adapter inference run telemetry (391 adapter-routed IDs, SC=3), not trainer loss/grad logs.
- Completion summary: `Done. 391 items written`.
- Throughput/timing behavior:
  - average wall/item ~8.77s
  - p95 ~25.32s
  - max ~68.97s (`ID 336`)
- SC consistency:
  - vote distribution: 388 items with `3/3`, 3 items with `2/3` (`IDs 10, 147, 831`).
- Warnings observed are operational (vLLM env + NCCL cleanup), not quality-failure signals.

### 2) Full read of `inference/results/hybrid/`

Fully read files/subdirs:
- root files: `adapter_targets.txt`, `adapter_v5_run.jsonl`, `sc16_base_run.jsonl`, `sc16_priority.txt`, `sc16_targets.txt`
- subdirs: `dsmlp-A30/`, `slot1/`, `tnr-A/`, `tnr-B/`
- also read: `slot1/routing_manifest.csv`, `slot1/submission.csv`

#### 2A. ID-set/routing structure

- `adapter_targets.txt`: 391 IDs (min 1, max 942)
- `sc16_priority.txt`: 153 IDs
- `sc16_targets.txt`: 176 IDs
- Set relations:
  - `sc16_priority` is subset of `sc16_targets` (153/153)
  - `sc16_targets` and `adapter_targets` are disjoint (0 overlap)
- `slot1/routing_manifest.csv`: 943 rows -> `adapter=391`, `base=552` (exact dual-path partition).

#### 2B. `adapter_v5_run.jsonl` characterization (391 items, dual-path adapter branch artifact)

- Mode is uniformly `adapter`.
- Voting quality:
  - avg votes 2.992 / avg n_voting 3.000
  - `no_voted_answer=0`
  - distribution: 388 items `3/3`; 3 items `2/3`
- Trace/format presence:
  - For sampled items (IDs `1,3,10,13,14,15,23,31,34,38`), all 3 samples/item contained reasoning tags and `\boxed{}`.
  - `voted_answer` present for all sampled items.

Sampled 10-item spot check (requested 5-10):
- ID 1: `3/3`, voted `A`, trace+boxed present in all 3 samples.
- ID 3: `3/3`, voted `B`, trace+boxed present in all 3.
- ID 10: `2/3`, voted `E`, trace+boxed present in all 3 (one dissent sample).
- ID 13: `3/3`, voted `C`, trace+boxed present in all 3.
- ID 14: `3/3`, voted `\frac{\log 35}{\log 3}`, trace+boxed present in all 3.
- ID 15: `3/3`, voted `8,NONE`, trace+boxed present in all 3.
- ID 23: `3/3`, voted `H`, trace+boxed present in all 3.
- ID 31: `3/3`, voted `-3,42`, trace+boxed present in all 3.
- ID 34: `3/3`, voted `J`, trace+boxed present in all 3.
- ID 38: `3/3`, voted `B`, trace+boxed present in all 3.

#### 2C. Other hybrid artifacts

- `sc16_base_run.jsonl`: 43 rows, avg votes 8.651, avg n_voting 12.349, no empty voted answers.
- `tnr-A/a1_serial_sc16_weak128_*.jsonl`: 127 parseable rows + 1 malformed line (confirmed), avg votes 10.425 / n_voting 14.717.
- `tnr-A/a2_serial_sc16_hardest30_*.jsonl`: 30 rows, avg votes 9.233 / n_voting 15.5.
- `tnr-B/nothinking_probe98_*.jsonl`: 98 rows, 17 rows with empty voted answer.
- `dsmlp-A30/adapter_rescue_61_*.jsonl`: 61 rows, avg votes 6.82 / n_voting 16.
- `dsmlp-A30/adapter_smoke_*.jsonl`: 1 row, 16/16 vote.

### 3) v5 dataset tier verification (391 items)

Verified by joining:
- `data/sft_v5_dataset.jsonl` (`item_id`)
- `data/MASTER_ANSWERS.csv` (`item_id`, `sheet_tier`)

Counts (all 391 mapped; missing=0):
- T1: 2 (0.51%)
- T2: 341 (87.21%)
- T3: 31 (7.93%)
- T4: 7 (1.79%)
- T5: 10 (2.56%)

Claim check:
- "87% T1-easy" is imprecise if interpreted as T1 only (actual T1 is 0.51%).
- The observed distribution strongly supports "easy-heavy" if interpreted as `T1+T2`: 343/391 = **87.72%**.

### 4) MERGE-vs-ADAPTER per-version table (v1/v3/v4/v5)

| Version | Deployment mode used in eval/inference | Evidence (training artifact) | Evidence (inference loading path) |
|---|---|---|---|
| v1 | **Merged** | `sft_v1_postmortem/logs/train_*` save `final_adapter`, then `logs/merge_*` run `merge_and_unload` and save `.../merged` | `sft_v1_postmortem/logs/smoke_openr1_v1_1k_5.log` initializes model at `training/checkpoints/openr1_v1_1k/merged` |
| v3 | **Merged** (intended/evaluated path) | `sft_v3/scripts/merge_adapter.py` explicit LoRA -> merged BF16 flow; `SFT_V3_TRAINING_LOG.md` says hand merged model for full inference | Merge script sanity checks no adapter files in output; v3 notes/logs describe merged deployment handoff |
| v4 | **Merged** | v4 flow produced merged model artifact used by adaptive run | `inference/results/sft_v4_adaptive/run_meta.json` has `"model": "sft_v4_epoch6_merged"` |
| v5 | **Adapter (unmerged)** | `memo_test.log` winner line: `No merge -- keep as LoRA adapter.` | `inference/scripts/run_hybrid_inference.py` in adapter mode uses `enable_lora=True` + `LoRARequest(..., args.adapter_path)` |

Important locked distinction:
- `sft_v4_adaptive` is merged-model routing.
- v5 hybrid path is live adapter loading (LoRARequest), not merged.

### 5) `run_hybrid_inference.py` content analysis (dual-path routing)

#### 5A. Base vs adapter mode behavior

- Shared core:
  - Reads items from `private.jsonl`, builds chat prompt with `SYSTEM_PROMPT`, runs SC sampling, writes one JSONL row per item.
- `--mode base`:
  - No LoRA request; plain base model generation.
  - Applies shape filter (`apply_shape_filter`) to reject no-box / invalid multi-box samples before voting.
- `--mode adapter`:
  - Requires `--adapter-path`.
  - Enables LoRA in vLLM (`enable_lora`, `max_lora_rank`) and passes `LoRARequest` at generation call.
  - Shape filter is disabled (`rejected = [False]*n`) in adapter branch.

#### 5B. Input contract

- Requires `private.jsonl` items keyed by `id` with at least:
  - `question`
  - optional `options` for MCQ formatting path
- Optional `--item-ids` file: one integer ID/line for targeted subsets.
- Optional decode-control params: `thinking_budget`, `top_k`, `min_p`, penalties, `--system-prompt`, `--no-thinking`, etc.

#### 5C. Output format

One JSONL row/item with fields:
- `id`, `mode`, `voted_answer`, `votes`, `n_voting`, `shape_fallback`
- `response` (picked full trace)
- `samples`, `sample_extracted`, `sample_n_output_tokens`
- `wall_seconds`, `timestamp`

#### 5D. Where combination happens

- There is **no base+adapter combination inside this script**.
- Script runs one mode at a time and emits per-item results.
- Combination/routing is external (e.g., `slot1/routing_manifest.csv` + assembled submission artifacts in `inference/results/hybrid/slot1/`).

### 6) `memo_test_v5.py` analysis + reconciliation with break-even

#### 6A. Is the test trivial?

Not fully trivial:
- It uses inference-like machinery, not teacher-forced decoding:
  - vLLM generation
  - SC sampling (`n=3`)
  - temperature/top-p/max_tokens controls
  - LoRARequest for each checkpoint
- It tests both MCQ and free-form items (10+10), and requires strict `3/3` per item.

So the test has operational meaning as "adapter can reliably regenerate training labels under inference sampling."

#### 6B. Why it still fails as deployment gate

Because it is still in-training-only:
- All 20 IDs are sampled from `data/sft_v5_dataset.jsonl` labels.
- Success criterion is label replication on seen examples, not unseen generalization.
- Checkpoint ranking is therefore dominated by memorization consistency, not Kaggle-relevant lift.

#### 6C. Reconciliation with v5 break-even

If memo test is meaningful for memorization but v5 is break-even globally, the consistent explanation is:

1) **Gate mismatch** (primary):
- The test measured exactly what v5 optimized for (seen-item recall), not the real objective (unseen/private improvement).

2) **Training-set composition mismatch** (structural):
- Verified distribution is 87.72% T1+T2 (easy-heavy), with only 12.28% in T3/T4/T5.
- This biases adaptation toward easy-pattern reinforcement rather than persistent hard-miss correction.

3) **Dual-path deployment context**:
- In production hybrid routing, adapter handles the 391 trained IDs while base handles 552 others.
- Global score lift requires either strong improvements on adapter-routed IDs or no regressions plus base gains elsewhere; in-practice v5 was near break-even.

Bottom line:
- `memo_test_v5.py` is a useful *sanity* instrument (adapter integrity + in-sample consistency under SC sampling), but is not a valid *selection* instrument for expected Kaggle uplift.

---

## Part 3 — Phase A third pass

### Gap A) Quantization per-version table (Part 11 verification)

Method:
- Read full training scripts for v1/v3/v4/v5 and extracted model-loading + optimizer config from code.
- Sources:
  - `inference/adapters/sft_v1_postmortem/scripts/train_qwen3_qlora.py`
  - `inference/adapters/sft_v3/scripts/train_sft_v3.py`
  - `inference/adapters/sft_v4/scripts/train_sft_v4.py`
  - `inference/adapters/sft_v5/scripts/train_sft_v5.py`

| Version | Loading mechanism | Quantization config | torch dtype config | Optimizer |
|---|---|---|---|---|
| v1 | `Unsloth FastLanguageModel.from_pretrained(...)` | `load_in_4bit=True` (explicit) | `dtype=None` in loader, training with `bf16=True` in SFTConfig | `adamw_8bit` |
| v3 | `AutoModelForCausalLM.from_pretrained(...)` | No `load_in_4bit`, no `BitsAndBytesConfig` | `torch_dtype=torch.bfloat16` | `adamw_torch` |
| v4 | `AutoModelForCausalLM.from_pretrained(...)` | No `load_in_4bit`, no `BitsAndBytesConfig` | `torch_dtype=torch.bfloat16` | `adamw_torch` |
| v5 | `AutoModelForCausalLM.from_pretrained(...)` | No `load_in_4bit`, no `BitsAndBytesConfig` | `torch_dtype=torch.bfloat16` | `adamw_torch` |

Verification outcome for Part 11 claim:
- **Confirmed.**
  - v1 is QLoRA-style (4-bit load + Unsloth path + `adamw_8bit`).
  - v3/v4/v5 are full bf16 LoRA-style HF loads (no 4-bit quantization in training script + `adamw_torch`).

Notes:
- No `BitsAndBytesConfig` usage appears in v3/v4/v5 scripts.
- v1 docstring and loader explicitly call out 4-bit loading path.

### Gap B) Trace-answer coherence audit (Part 8 hypothesis validation sample)

Method:
- Stratified sample from `data/sft_v5_dataset.jsonl`, tiers via `data/MASTER_ANSWERS.csv`.
- Targeted ~5 each in T2/T3/T4 (available) + 2 from T5.
- Sample size: **17**
  - Tier breakdown: T2=5, T3=5, T4=5, T5=2
  - Type breakdown: MCQ=12, FREE=5

Sampled item_ids:
- T2: `1, 3, 13, 15, 23`
- T3: `69, 88, 111, 125, 127`
- T4: `10, 89, 164, 182, 317`
- T5: `14, 184`

Audit procedure per sampled item:
1. Parse reasoning trace between `<think> ... </think>` where present (or full assistant narrative when trace tags absent).
2. Identify the trace's reached conclusion.
3. Extract final `\boxed{...}` label.
4. Check coherence (trace conclusion aligns with boxed label semantics).

#### Coherence counts

- **MATCH (coherent): 17 / 17**
- **MISMATCH (incoherent): 0 / 17**

Interpretation for this sample:
- This sample does **not** surface direct trace-vs-box contradiction cases.
- It does not refute the broader hypothesis globally; it only says the sampled v5 rows are coherent by this criterion.

#### Mismatch characterization

- No hard mismatches in this sample, so no mismatch table by item_id.

#### Quality caveats observed (not counted as mismatch)

- Some traces are weak-confidence or retrieval-like, but still end on the same boxed target:
  - `ID 88` (T3, MCQ): trace uses sequence/lookup-style reasoning with low-derivation confidence language, but lands on option C and boxed C.
  - `ID 184` (T5, MCQ): no `<think>` tags; direct answer block states list matching option E and boxed E.
- Some traces branch before converging:
  - `ID 89` (T4, FREE): internal back-and-forth on integer months vs exact fraction, final boxed `326/7` matches final explicit algebraic result.

#### Concentration by tier/type

- Since mismatches were zero in this sample, there is no tier/type concentration pattern for incoherence.
- Coverage remains skewed toward MCQ (12/17), so this sample is better viewed as a targeted sanity check, not a full-population estimate.

Bottom line from third-pass coherence sample:
- In this stratified 17-item cut of v5, trace-to-label coherence is high (17/17).
- The structural coherence risk remains a valid hypothesis to test at larger scale, but it was **not** evidenced in this sample window.
