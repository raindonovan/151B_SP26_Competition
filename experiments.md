# CSE 151B SP26 — Experiment Log

## See Also

- [`DESIGN.md`](DESIGN.md) — strategic phases, prompt-engineering plan, promotion criteria
- [`SETUP.md`](SETUP.md) — Pod A/Pod B environments, inference speed levers
- [`COMPETITION.md`](COMPETITION.md) — rules, submission format, allowed methods
- [`CLAUDE.md`](CLAUDE.md) — agent operating instructions (mirrored in `AGENTS.md` for Codex)

This doc owns the **operational** record (what was run, with what params, what came out). Strategic decisions (which prompt policies to test, what gates to use, what phase comes next) live in `DESIGN.md`.

---

## Environment

Two pods, same model, different inference stacks. See [`SETUP.md`](SETUP.md) for setup details and the rationale for the split. Per-run rows in the Results Summary identify which pod produced them via the Engine column.

**Shared**
- Model: `Qwen/Qwen3-4B-Thinking-2507`
- Compute: NVIDIA GeForce RTX 4090 (24 GB)

**Pod A — Transformers (current primary)**
- Engine: Transformers + BitsAndBytes
- Quantization: 4-bit BitsAndBytes (INT4, double quant, bf16 compute)
- Torch: 2.11.0+cu128 | CUDA: 12.8 | Transformers: 5.7.0
- Kernel: Python (cse151b)
- Used by: Runs 01–03

**Pod B — vLLM (working as of 2026-05-03)**
- Engine: vLLM 0.8.5 (V0 engine; `VLLM_USE_V1=0` required — see Known Issues)
- Quantization: none
- dtype: bfloat16
- gpu_memory_utilization: 0.85
- Torch: 2.6.0+cu124 | CUDA: 12.4 | Transformers: 4.51.3
- Runner: `scripts/run_vllm_experiment.py`
- Used by: `run_vllm_smoke_5_tok8192`, planned Run 04 onward

---

## Locked Defaults

Sampling defaults are **shared** across both pods and apply to every run unless explicitly overridden. Engine defaults are **per-pod** (Pod A = Transformers + BnB-INT4; Pod B = vLLM + BF16) — engine choice is recorded explicitly in each run, not as a deviation.

Per-run param tables write **"default"** for any sampling field below; only deviations get listed.

**Sampling (shared, both pods)**

| Param | Value | Source |
|---|---|---|
| temperature | 0.6 | Qwen3-Thinking-2507 model card |
| top_p | 0.95 | Qwen3-Thinking-2507 model card |
| top_k | 20 | Qwen3-Thinking-2507 model card |
| min_p | 0.0 | Qwen3-Thinking-2507 model card |
| repetition_penalty | 1.0 | Qwen3-Thinking-2507 model card |
| do_sample | True | required for sampling decoding (Pod A only — vLLM samples whenever `temperature > 0`) |
| enable_thinking | True | thinking-variant model |
| max_length (input truncation) | 16384 | Pod A |

**Engine (per-pod, recorded explicitly)**

| Pod | Engine | Quantization | dtype |
|---|---|---|---|
| Pod A | Transformers | BnB-INT4 (double quant) | bf16 compute |
| Pod B | vLLM 0.8.5 (V0) | none | bfloat16 |

**Token-budget semantics differ between pods — read this before setting `max_new_tokens` on Pod B.**

| Pod | How the budget works |
|---|---|
| Pod A (Transformers) | `max_length=16384` truncates the **prompt only**. `max_new_tokens` is an **independent** generation cap. Effective generation budget = `max_new_tokens` regardless of prompt length. |
| Pod B (vLLM) | `max_model_len` caps **prompt + generation combined**. Effective generation budget = `max_model_len − prompt_len`. To match Pod A's full 8192-token gen budget on the standard slice, use `max_model_len ≥ 16384` (script default is 16384). For an explicit 16k generation budget, set `max_model_len ≥ ~24576` (16384 + prompt headroom). |

When comparing a Pod A run to a Pod B run, confirm both effectively allowed the same generation budget, not just that they share the same `max_new_tokens` number.

If a run deviates from any sampling default, the deviation must appear in **both** that run's params table **and** the Sampling/Notes column of the Results Summary, so the diff is visible at a glance.

---

## Results Summary

| Run | Date | N | Slice | Prompt | Engine | tok | avg_tok | s/q | Cutoffs | MCQ | Free | Overall | Sampling | Results |
|-----|------------|---:|-------------|--------|--------------|-----:|--------:|------:|--------:|:-------------|:-------------|:--------------|----------|----------|
| 01  | 2026-05-01 |  5 | `data[:5]`  | v1     | Transformers | 2048 | —       | —     | ?       | 0/2 = 0.0%   | 2/3 = 66.7%  | 2/5 = 40.0%  | default  | [starter_results.jsonl](results/starter_results.jsonl) |
| 02  | 2026-05-01 | 20 | `data[:20]` | v1     | Transformers | 4096 | —       | —     | 9 (est.) | 3/9 = 33.3%  | 6/11 = 54.5% | 9/20 = 45.0% | default  | [run02_baseline_20_tok4096.jsonl](results/run02_baseline_20_tok4096.jsonl) |
| 03  | 2026-05-01 | 20 | `data[:20]` | v1     | Transformers | 8192 | 5466    | 395.7 | 6       | 4/9 = 44.4%  | 6/11 = 54.5% | 10/20 = 50.0% | default | [run03_tok8192_20.jsonl](results/run03_tok8192_20.jsonl) |
| smoke‑vLLM | 2026-05-03 | 5 | `data[:5]` | v1 | vLLM BF16 | 8192 | 4332 | 20.7 | 0 | 1/2 = 50.0% | 2/3 = 66.7% | 3/5 = 60.0% | default | [run_vllm_smoke_5_tok8192.jsonl](results/run_vllm_smoke_5_tok8192.jsonl) |

Runtime + cost: Run 03 = 131.9 min ≈ $1.52. Earlier Pod A runs untracked. vLLM smoke = 103.3 s wall-clock for generation (negligible cost).

**`smoke‑vLLM` is an infrastructure-validation run, not a comparable experiment.** N=5 is too small for accuracy claims; its purpose was to confirm Pod B (vLLM 0.8.5, V0 engine) generates end-to-end with `\boxed{}` extraction working. It is excluded from cross-run accuracy comparisons. The first comparable Pod B run is planned Run 04.

---

## Insights

Cross-run lessons. Each cites the run(s) it came from. New insights belong here, not buried in a single run's Observations.

1. **Token budget was the dominant accuracy variable on Pod A at 4k vs 8k.** Runs 02→03 on Pod A/Transformers/BnB-INT4 (4096 → 8192, all else fixed): no-`\boxed{}` cutoffs dropped from ~9 to 6 on n=20, and one previously-cutoff MCQ flipped to correct. Overall +5pp on n=20 is within sampling noise on its own — the **cutoff-rate drop is the load-bearing evidence**. *Scope caveat:* this conclusion is from two Pod A runs only. Whether the same cap-vs-accuracy pattern (and the same cutoff rate at 8k) holds under Pod B/vLLM/BF16 is open until Run 04 parity completes; engine + numerics + quantization all changed simultaneously.

2. **MCQ cutoffs dominate at 8k on Pod A.** 5 of 6 cutoffs in Run 03 were MCQ. The MCQ prompt does not force commitment once the model is confident — it produces full derivations like a free-form question. This is the single most actionable open finding; it implies an MCQ-commitment prompt should be a high-priority experiment regardless of where the token cap lands. *Scope caveat:* observed under Pod A/Transformers/BnB-INT4 only. The vLLM smoke run (n=5, 8k tok) had 0 cutoffs, but n=5 is too small to claim anything; Run 04 (n=20 vLLM parity) is the first signal whether the MCQ cutoff pattern persists under vLLM/BF16 or whether the engine change shifts the failure mode.

3. **Pod A throughput is infeasible for full-set runs.** Run 03 measured ~14 tok/s through Transformers + BnB-INT4 → ~395 s/q → ~124 hr / ~$85 for the full 1126 questions. Anything past a 50–100 q validation slice needs Pod B (vLLM batching).

4. **The model self-terminates near `\boxed{}` already.** Simulated early-stopping on Run 03 saved ~1% of decoded chars on average — the model emits EOS shortly after the boxed answer in the success cases. Early-stop (now wired into the notebook) is a cheap safety net but **not** a meaningful speed lever for this model on this data. Real speed wins come from Pod B and from prompt changes that prevent runaway thinking.

5. **Pod B/vLLM is operational and dramatically faster on small batches (n=5 smoke).** The vLLM 8k smoke run (`run_vllm_smoke_5_tok8192`, batched on n=5) finished in 103.3 s = **20.7 s/q** vs Pod A Run 03's 395.7 s/q at the same 8k cap — roughly **19× faster** at this batch size. avg_gen_tokens was 4332 (vs Run 03's 5466), with **0 cutoffs and 0 missing `\boxed{}` on 5 questions**. *Scope caveat:* per-question wall time on a single n=5 batch is dominated by the slowest item under vLLM batching, so the speed multiplier is not stable across batch sizes; the lower avg_gen_tokens may reflect BF16 numerics producing shorter `<think>` blocks than INT4, or just sample noise on n=5. The 19× number is a floor on the speed win, not a published throughput. *Budget caveat:* the smoke run was at `max_model_len=8192` (the old script default), which under vLLM caps prompt+generation combined — see Locked Defaults. avg_gen_tokens=4332 with max well below 8192 suggests no question actually came near the cap, so the throughput number is unaffected in practice, but technically a long-prompt item could have been silently truncated. Run 04 onward uses `max_model_len=16384`, which removes this footgun and makes timing comparisons against Pod A apples-to-apples. Run 04 (n=20 vLLM parity) is needed to confirm both the speedup and the no-cutoff pattern at a meaningful sample size.

---

## Experiment Queue

What's planned. The "on deck" row is the single source of truth for what runs next; everything below it is provisional and will be re-evaluated after each completed run.

> **Rows here describe *planned* runs, not measured results.** "Hypothesis" and "Expected outcome" are predictions written *before* the run. Measured results live in the **Results Summary** table and the per-run subsection under **Run Details**. When a queued run completes, it moves out of this table.

| # | On deck? | Hypothesis | Variable changed | Held fixed | Expected outcome | Decision rule |
|---|---|---|---|---|---|---|
| 04 | **yes** | Pod B (vLLM/BF16) reproduces Run 03 accuracy within ±5pp at ≥5× speed on the same slice. First apples-to-apples Pod A↔B comparison. | Engine Transformers/INT4 → vLLM/BF16 | `data[:20]`, prompt v1, tok 8192, sampling defaults | Accuracy within ±5pp of Run 03's 50%; cutoffs ≤ Run 03's 6/20; throughput ≥5× Run 03's 395.7 s/q. | Parity passes (accuracy + cutoffs in expected range) → adopt vLLM as default engine for all runs ≥50 q. Accuracy gap >5pp → diagnose (BF16 vs INT4 numerics? sampling mismatch? prompt template mismatch?) before scaling. Throughput <5× → re-time after the 50-q run; small batches under-utilize batching. |
| 05 |     | A vLLM/BF16 baseline on a 50-q slice (`fixed_50_v1` if defined per DESIGN.md §1.6, else `data[:50]`) at tok 8192 anchors the prompt sweep. | `data[:20]` → 50-q slice | engine vLLM, tok 8192, prompt v1, sampling defaults | Per-type accuracy stable; cutoffs reasonable. | Lock as the prompt-sweep anchor; do not rerun unless tok cap or engine changes. |
| 06 |     | An MCQ-commitment prompt cuts MCQ cutoffs without hurting free-form accuracy. | prompt v1 → v2-mcq-commit | 50-q slice from Run 05, vLLM, tok 8192, sampling defaults | MCQ accuracy ↑ ≥ 4 q (DESIGN.md §1.11 promotion bar); free-form within ±2 q. | Promote per DESIGN.md §1.11 if gain ≥ 4 q. Otherwise iterate prompt or split MCQ-only branch. |
| 07 | optional | If cutoffs remain meaningful at 8k under vLLM/BF16 (Run 04 or Run 05), test 16k token budget. | `max_new_tokens` 8192 → 16384 | engine vLLM, prompt v1, slice from triggering run, sampling defaults | Cutoffs ≤ 1; overall ≥ Run 04 + 5pp. | Cutoffs > 1 at 16k → reasoning ceiling, not budget; pivot to prompt work. Cutoffs ≤ 1 → 16k becomes the new comparison cap; rerun the prompt sweep against it. **Skip this run entirely if Run 04 or Run 05 shows cutoffs at 8k are already negligible under vLLM.** |

---

## Data Slices

A slice is the **deterministic** question set a run uses. Slices are first-class identifiers — comparing runs means comparing the same slice (or accepting cross-slice noise explicitly).

| Slice ID | N | Definition | Used by |
|---|---:|---|---|
| `data[:5]`     |  5 | First 5 rows of `data/public.jsonl`. | Run 01 |
| `data[:20]`    | 20 | First 20 rows. | Runs 02, 03, planned 04 |
| `fixed_50_v1`  | 50 | TBD per DESIGN.md §1.6: ~15–20 MCQ + 30–35 free, stratified to roughly match the 33%/67% competition split. ID list to be saved at `data/slices/fixed_50_v1.json` once chosen. | Planned Runs 05+ (prompt sweep) |
| `private_test` | TBD | Released on submission day. | Submission runs only. |

### Slice rules

- A slice's id list is locked once any run uses it. Edits = a new slice with a new ID (e.g. `fixed_50_v2`).
- All slice ID lists live under `data/slices/<id>.json` as an explicit list of question IDs (not Python ranges).
- Stratified slices store the seed alongside the id list so the draw is reproducible.
- Cross-slice comparisons need an uncertainty band, not an equality claim.

---

## Known Issues

Tracked here so they don't surface mid-run at the worst possible time. Address opportunistically before any run >50 q.

### Pod A — Notebook

- **Dead `MAX_TOKENS = 32768` knob in cell 7.** Generation actually uses `DEBUG_MAX_NEW_TOKENS` defined locally in cell 20 (currently 8192). Risk: someone changes `MAX_TOKENS` expecting it to take effect. Either delete the unused config or wire it through.
- **`tokenizer.padding_side = 'left'` not set.** Single-sequence inference is unaffected, but any future batched generation on Pod A will silently produce wrong outputs without left padding. (Pod B/vLLM handles padding internally — this is a Pod A-only concern.) Set this before the first Pod A batched run, not after.
- **No per-item incremental save.** Cell 26 writes results only after the full loop completes. A crash at question 800/1126 loses all 800 prior generations. Convert to per-item append-mode write before scaling past ~50 q on Pod A.
- **No CSV submission generator.** `COMPETITION.md` §Submission requires `id,response` CSV with proper double-quoting; current pipeline only writes JSONL. Needed before the first private-set run.
- **Stale display in cell 26 output** (`Saved … run02_baseline_20_tok4096.jsonl`) — `OUTPUT_PATH` in cell 7 is now `run03_tok8192_20.jsonl`; the saved file matches the new path, only the printed text is stale. Self-resolves on the next full run.

### Pod B — vLLM script

- **`VLLM_USE_V1=0` is required.** vLLM 0.8.5 on this pod fails to initialize under the V1 engine. `scripts/run_vllm_experiment.py` sets this env var before importing `vllm`; any new vLLM script must do the same. If this becomes a problem in a future vLLM upgrade, see [`SETUP.md`](SETUP.md) Pod B section.
- **No per-item incremental save.** `scripts/run_vllm_experiment.py` writes the full JSONL only after the entire batch completes (same shape as the Pod A notebook issue). vLLM's batched scheduling makes per-item streaming awkward, but a "stream completed requests as they finish" path is feasible via `LLM.generate(..., use_tqdm=False)` + the `RequestOutput.finished` flag. Implement before any vLLM run ≥100 q so a mid-batch crash doesn't lose hours of generation.
- **No CSV submission generator on Pod B path either.** Same gap as Pod A — currently no `id,response` CSV writer matching `COMPETITION.md` §Submission. Should land in one place that both pods can call.

### Instrumentation provenance

When comparing across runs, only Run 03+ numbers are *measured*. Earlier rows are estimates or floors.

| Run | cutoffs | gen_tokens | gen_secs | per-item save | Reliability |
|---|:-:|:-:|:-:|:-:|---|
| 01 | ✗ (not tracked) | ✗ | ✗ | ✗ | Smoke-test only; cutoff column is `?`. |
| 02 | est. (post-hoc by counting missing `\boxed{}`) | ✗ | ✗ | ✗ | Cutoff count is an estimate, not a measurement. |
| 03 | ✓ | ✓ | ✓ | ✗ | First run with reliable per-item stats. Lacks crash-safe save. |

---

## Submissions

Track every leaderboard submission here. Kaggle limits: 3/day, 2 final selections.

| # | Date | Run ID | Slice | Local accuracy | Leaderboard accuracy | Gap | Notes |
|---|------|--------|-------|----------------|----------------------|----:|-------|

(No submissions yet.)

When the gap between local and leaderboard accuracy exceeds ~5pp, treat it as a **calibration problem first** (slice mismatch, scoring mismatch, parser mismatch, prompt-divergence between dev and submission run) — not a model problem. Investigate before spending another submission.

---

## Calibration vs Published Baselines

Run 03 = 50% overall on n=20 at 8k tokens. **Not directly comparable** to published Qwen3-4B-Thinking benchmarks:

- Different problem distribution (CSE 151B mix of high-school → graduate vs AIME25 / MATH / etc.)
- Different token budget (8k here vs typical 16k–32k in papers)
- Different sampling (matched to model card defaults, but per-paper choices vary)

The *Frugal Reasoning* paper (Table 5) reports base Qwen3-4B at 8k on AIME25 ≈ 13%. The CSE 151B mix is easier than AIME25, so 50% on 8k is unsurprising — but the same paper shows accuracy climbing substantially as the token cap rises through 16k–32k. **A jump in Run 04 (16k) should be expected from "unclamping a known ceiling" alone**, not attributed to other factors. Note this so a 16k overall accuracy jump doesn't get falsely credited to whatever else is changed alongside.

---

## Token Budget Notes

For thinking models, `max_new_tokens` is an **accuracy variable**, not only a runtime/cost variable. If generation is cut off before the final `\boxed{...}` appears, the scorer marks the response wrong even when the reasoning was correct.

**Cutoff** = generation hit `max_new_tokens` before a `\boxed{}` was found in the output.

When comparing token budgets, hold prompt, data slice, sampling params, and model fixed — change only `max_new_tokens`.

Decision rule after each run:
- Cutoffs > 0 → run same slice at 2× token budget before changing anything else
- Cutoffs = 0 → token budget is not the bottleneck; move to prompt or method experiments

---

## Run Details

### Run 01 — Smoke test

**Rationale:** First run ever. Goal was to verify the pipeline works end-to-end — model loads, prompt builds, generation runs, scorer doesn't crash. Used only 5 questions to keep it fast. Token cap of 2048 was a conservative placeholder; we knew it might be too short for a thinking model but didn't want to wait long on a smoke test.

- **Slice:** `data[:5]` — 2 MCQ, 3 free-form
- **Engine:** Transformers + TextStreamer

| param | value | note |
|-------|------:|------|
| max_new_tokens | 2048 | capped: `min(MAX_TOKENS=32768, 2048)` |
| sampling | default | per Locked Defaults |
- **Runtime / cost:** untracked
- **Results:** [starter_results.jsonl](results/starter_results.jsonl)

**Observations:**
- Pipeline works end-to-end.
- `max_new_tokens=2048` may cut off reasoning mid-thought.
- Cutoffs not tracked (added to summary table as `?`).
- Sample too small to judge quality.

---

### Run 02 — Baseline 20 questions

**Rationale:** Pipeline confirmed working. Scaled to 20 questions and doubled the token cap to 4096 to get a more meaningful baseline before touching the prompt. Post-run, 9/20 responses had no `\boxed{}` at all — strong signal the model is hitting the cap before finishing. This makes the 4096 baseline effectively a floor, not a real score.

- **Slice:** `data[:20]`
- **Engine:** Transformers + TextStreamer

| param | value | note |
|-------|------:|------|
| max_new_tokens | 4096 | |
| sampling | default | per Locked Defaults |
- **Runtime / cost:** untracked
- **Results:** [run02_baseline_20_tok4096.jsonl](results/run02_baseline_20_tok4096.jsonl)

**Observations:**
- MCQ 3/9 = 33.3% | Free 6/11 = 54.5% | Overall 9/20 = 45.0%
- 9/20 responses had no `\boxed{}` — all marked wrong.
- Likely many cutoffs at 4096 tokens before model finished thinking and wrote final answer.
- gen_tokens / gen_secs not tracked this run; cutoff count is an estimate.
- **Decision applied:** cutoffs > 0 → double budget → Run 03.

---

### Run 03 — Token budget test

**Rationale:** Run 02 had 9/20 missing `\boxed{}`. Inspection of the raw tails confirmed every single one was cut off mid-sentence — not a prompt failure, just running out of tokens. Per the decision rule (cutoffs > 0 → double budget), Run 03 doubles to 8192 with everything else held fixed.

- **Slice:** `data[:20]`
- **Engine:** Transformers + TextStreamer

| param | value | note |
|-------|------:|------|
| max_new_tokens | 8192 | 2× Run 02 |
| sampling | default | per Locked Defaults |
- **Runtime:** ~131.9 min for 20 questions (mean 395.7 s/q).
- **Cost est.:** ~$1.52 on the 4090 at $0.69/hr.
- **Results:** [run03_tok8192_20.jsonl](results/run03_tok8192_20.jsonl)

**Observations:**
- Overall 10/20 = 50.0% (up from 45.0%; +1 question correct = within noise on n=20, see Insight 1).
- MCQ 4/9 = 44.4% (up from 33.3%); one previously-cutoff question (id=4) now completed and correct.
- Free-form 6/11 = 54.5% (unchanged); two newly-completed free-form items were still wrong (reasoning errors, not cutoffs).
- gen_tokens: mean=5466, p50=5895, p95=8192, max=8192.
- 6 responses hit the 8192-token cap with no `\boxed{}` — **5 of 6 are MCQ** (Insight 2).
- Critical: at 395.7 s/q, a full 1126-question run takes ~124 hrs and costs ~$85. Pod B (vLLM) batching is required before any run >50 q (Insight 3).
- **Decision applied:** original plan was to double again to 16k. Superseded by Pod B coming online — 16k token-budget test is now optional Run 07, deferred until vLLM cutoff behavior is known. Next run is the vLLM parity comparison (Run 04).

---

### `run_vllm_smoke_5_tok8192` — Pod B infrastructure validation

**Rationale:** First end-to-end vLLM run on Pod B after the V0-engine workaround (`VLLM_USE_V1=0`) was identified. Goal: confirm `scripts/run_vllm_experiment.py` loads the model under vLLM, batches the 5 prompts, and produces `\boxed{}`-bearing outputs that the existing `Judger` can score. **This is an infrastructure check, not an accuracy experiment** — n=5 is too small for any cross-run comparison and the result is excluded from the Insights numbers.

- **Slice:** `data[:5]` — 2 MCQ, 3 free-form
- **Engine:** vLLM 0.8.5 (V0), BF16, no quantization, gpu_memory_utilization=0.85

| param | value | note |
|-------|------:|------|
| max_new_tokens | 8192 | matches Run 03 cap for later comparison |
| sampling | default | per Locked Defaults |
| `VLLM_USE_V1` | `"0"` | required on this pod (see Known Issues) |

- **Runtime:** 103.3 s wall-clock for batch of 5 (20.7 s/q amortized).
- **Results:** [run_vllm_smoke_5_tok8192.jsonl](results/run_vllm_smoke_5_tok8192.jsonl) + sidecar `.summary.json`.

**Observations:**
- Pipeline runs end-to-end: vLLM loads → batched generate → `\boxed{}` extraction → `Judger.auto_judge` → JSONL + summary written.
- Overall 3/5 = 60.0% (1/2 MCQ, 2/3 free-form). **Not comparable to Run 03** at n=5.
- Cutoffs 0/5 and missing `\boxed{}` 0/5 at 8k. avg_gen_tokens=4332 (vs Run 03's 5466). Both findings are interesting but unreliable at n=5 — see Insight 5 caveats.
- Wall-clock 20.7 s/q vs Run 03's 395.7 s/q ≈ 19× faster on this batch size. This is a *floor* on the speedup for batched runs; per-question time under vLLM is dominated by the slowest item in the batch, so the multiplier is not stable across batch sizes.
- **Decision applied:** Pod B is operational. Promote Run 04 (vLLM parity on `data[:20]` at 8k) to "on deck".

---

### Run 04 — vLLM parity (planned, not yet run)

**Status:** queued, on deck. Scheduled to run as the next experiment.

**Rationale:** First apples-to-apples Pod A↔B comparison. Same slice, prompt, sampling, and token cap as Run 03 — only the inference backend (Transformers/INT4 → vLLM/BF16) and quantization change. Establishes whether vLLM is safe to adopt as the default engine for runs ≥50 q and whether the Run 03 MCQ-cutoff pattern (Insight 2) persists under vLLM/BF16.

- **Slice:** `data[:20]` (same 9 MCQ + 11 free-form as Runs 02–03)
- **Engine:** vLLM 0.8.5 (V0), BF16, no quantization, gpu_memory_utilization=0.85

| param | value | note |
|-------|------:|------|
| max_new_tokens | 8192 | matches Run 03 |
| max_model_len | 16384 | parity choice — see Locked Defaults / Token-budget semantics. With `max_model_len ≥ 16384`, the full 8192-token generation budget is available regardless of prompt length, matching Run 03's effective gen budget. The smoke run used 8192 (old default); Run 04 is the first apples-to-apples gen-budget comparison. |
| sampling | default | per Locked Defaults |
| `VLLM_USE_V1` | `"0"` | required on this pod |

- **Predicted runtime:** ≤ ~80 s wall-clock (Run 03 = 131.9 min; smoke run amortized to 20.7 s/q on n=5; n=20 batched should be substantially faster than 5×20.7s due to batching). Real number recorded on completion.
- **Pre-registered comparisons** (so post-run framing isn't biased):
  1. Overall accuracy vs Run 03's 50% — pass band: ±5pp (i.e. 45%–55%).
  2. MCQ accuracy vs Run 03's 44.4% (4/9) — same ±5pp band.
  3. Cutoffs vs Run 03's 6/20 — pass band: cutoffs ≤ 6. *Apples-to-apples now: both runs effectively allow 8192 generation tokens regardless of prompt length, since Run 04 uses `max_model_len=16384`.*
  4. Wall-clock per question vs Run 03's 395.7 s/q — pass band: ≥5× faster (≤79 s/q).
- **Decision rule:** see Run 04 row in Experiment Queue. On completion, this section gets the measured numbers, the row gets removed from the Queue, and a new row appears in Results Summary.

---

## Prompt Versions

### v1-baseline

**Free-form:**
```
You are an expert mathematician. Solve the problem step-by-step. Put your final answer inside \boxed{}. If the problem has multiple sub-answers, separate them by commas inside a single \boxed{}, e.g. \boxed{3, 7}.
```

**MCQ:**
```
You are an expert mathematician. Read the problem and the answer choices below, then select the single best answer. Output ONLY the letter of your chosen option inside \boxed{}, e.g. \boxed{C}.
```
