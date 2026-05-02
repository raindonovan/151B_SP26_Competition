# CSE 151B SP26 — Experiment Log

## See Also

- [`DESIGN.md`](DESIGN.md) — strategic phases, prompt-engineering plan, promotion criteria
- [`SETUP.md`](SETUP.md) — Pod A/Pod B environments, inference speed levers
- [`COMPETITION.md`](COMPETITION.md) — rules, submission format, allowed methods
- [`CLAUDE.md`](CLAUDE.md) — agent operating instructions (mirrored in `AGENTS.md` for Codex)

This doc owns the **operational** record (what was run, with what params, what came out). Strategic decisions (which prompt policies to test, what gates to use, what phase comes next) live in `DESIGN.md`.

---

## Environment

- Compute: NVIDIA GeForce RTX 4090 (24 GB)
- Model: `Qwen/Qwen3-4B-Thinking-2507`
- Quantization: 4-bit BitsAndBytes (INT4, double quant, bf16 compute)
- Torch: 2.11.0+cu128 | CUDA: 12.8 | Transformers: 5.7.0
- Kernel: Python (cse151b)

---

## Locked Defaults

Apply to every run unless explicitly overridden. Per-run param tables write **"default"** for any field below; only deviations get listed.

| Param | Value | Source |
|---|---|---|
| temperature | 0.6 | Qwen3-Thinking-2507 model card |
| top_p | 0.95 | Qwen3-Thinking-2507 model card |
| top_k | 20 | Qwen3-Thinking-2507 model card |
| min_p | 0.0 | Qwen3-Thinking-2507 model card |
| repetition_penalty | 1.0 | Qwen3-Thinking-2507 model card |
| do_sample | True | required for sampling decoding |
| enable_thinking | True | thinking-variant model |
| max_length (input truncation) | 16384 | Pod A |
| Engine | Transformers + BnB-INT4 | Pod A primary; Pod B = vLLM/INT8 (planned, see SETUP.md) |

If a run deviates from any default, the deviation must appear in **both** that run's params table **and** the Sampling/Notes column of the Results Summary, so the diff is visible at a glance.

---

## Results Summary

| Run | Date | N | Slice | Prompt | Engine | tok | avg_tok | s/q | Cutoffs | MCQ | Free | Overall | Sampling | Results |
|-----|------------|---:|-------------|--------|--------------|-----:|--------:|------:|--------:|:-------------|:-------------|:--------------|----------|----------|
| 01  | 2026-05-01 |  5 | `data[:5]`  | v1     | Transformers | 2048 | —       | —     | ?       | 0/2 = 0.0%   | 2/3 = 66.7%  | 2/5 = 40.0%  | default  | [starter_results.jsonl](results/starter_results.jsonl) |
| 02  | 2026-05-01 | 20 | `data[:20]` | v1     | Transformers | 4096 | —       | —     | 9 (est.) | 3/9 = 33.3%  | 6/11 = 54.5% | 9/20 = 45.0% | default  | [run02_baseline_20_tok4096.jsonl](results/run02_baseline_20_tok4096.jsonl) |
| 03  | 2026-05-01 | 20 | `data[:20]` | v1     | Transformers | 8192 | 5466    | 395.7 | 6       | 4/9 = 44.4%  | 6/11 = 54.5% | 10/20 = 50.0% | default | [run03_tok8192_20.jsonl](results/run03_tok8192_20.jsonl) |

Runtime + cost: Run 03 = 131.9 min ≈ $1.52. Earlier runs untracked.

---

## Insights

Cross-run lessons. Each cites the run(s) it came from. New insights belong here, not buried in a single run's Observations.

1. **Token budget is the dominant accuracy variable below 16k.** Runs 02→03 (4096 → 8192, all else fixed): no-`\boxed{}` cutoffs dropped from ~9 to 6 on n=20, and one previously-cutoff MCQ flipped to correct. Overall +5pp on n=20 is within sampling noise on its own — the **cutoff-rate drop is the load-bearing evidence**. Until cutoffs reach zero, token cap dominates any prompt effect.

2. **MCQ cutoffs dominate at 8k.** 5 of 6 cutoffs in Run 03 were MCQ (Run 03). The MCQ prompt does not force commitment once the model is confident — it produces full derivations like a free-form question. This is the single most actionable open finding; it implies an MCQ-commitment prompt should be a high-priority experiment regardless of where the token cap lands.

3. **Pod A throughput is infeasible for full-set runs.** Run 03 measured ~14 tok/s through Transformers + BnB-INT4 → ~395 s/q → ~124 hr / ~$85 for the full 1126 questions. Anything past a 50–100 q validation slice needs Pod B (vLLM batching) per `SETUP.md`.

4. **The model self-terminates near `\boxed{}` already.** Simulated early-stopping on Run 03 saved ~1% of decoded chars on average — the model emits EOS shortly after the boxed answer in the success cases. Early-stop (now wired into the notebook) is a cheap safety net but **not** a meaningful speed lever for this model on this data. Real speed wins come from Pod B and from prompt changes that prevent runaway thinking.

---

## Experiment Queue

What's planned. The "on deck" row is the single source of truth for what runs next; everything below it is provisional and will be re-evaluated after each completed run.

| # | On deck? | Hypothesis | Variable changed | Held fixed | Expected outcome | Decision rule |
|---|---|---|---|---|---|---|
| 04 | **yes** | At 16384 tok cap, MCQ cutoffs drop to ≤1/9 — remaining errors are reasoning, not budget. | `max_new_tokens` 8192 → 16384 | `data[:20]`, prompt v1, defaults | MCQ cutoffs ≤1; overall ≥ 55%. | Cutoffs > 1 → consider 24k or accept reasoning ceiling and pivot to MCQ-commitment prompt. Cutoffs ≤ 1 → lock 16k as the comparison cap for prompt sweep. |
| 05 |     | Define `fixed_50_v1` and establish baseline at chosen tok cap on it. | `data[:20]` → `fixed_50_v1` | tok cap from Run 04, prompt v1, defaults | Per-type accuracy stable; serves as comparator for prompt sweep. | Lock as the prompt-sweep anchor; do not rerun unless tok cap or engine changes. |
| 06 |     | An MCQ-commitment prompt cuts MCQ cutoffs without hurting free-form accuracy. | prompt v1 → v2-mcq-commit | `fixed_50_v1`, tok cap, defaults | MCQ accuracy ↑ ≥ 4 q (DESIGN.md §1.11 promotion bar); free-form within ±2 q. | Promote per DESIGN.md §1.11 if gain ≥ 4 q. Otherwise iterate prompt or split MCQ-only branch. |
| 07 |     | Pod B (vLLM) reproduces Run 03 within ±5pp at ≥5× speed. | Engine Transformers → vLLM | `data[:20]`, prompt v1, tok cap, defaults | Accuracy ±5pp; throughput ≥5× Run 03. | Parity passes → all runs ≥50 q migrate to Pod B per SETUP.md. |

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

### Notebook

- **Dead `MAX_TOKENS = 32768` knob in cell 7.** Generation actually uses `DEBUG_MAX_NEW_TOKENS` defined locally in cell 20 (currently 8192). Risk: someone changes `MAX_TOKENS` expecting it to take effect. Either delete the unused config or wire it through.
- **`tokenizer.padding_side = 'left'` not set.** Single-sequence inference is unaffected, but any future batched generation (especially the Pod B / vLLM transition or any Pod A batching) will silently produce wrong outputs without left padding. Set this before the first batched run, not after.
- **No per-item incremental save.** Cell 26 writes results only after the full loop completes. A crash at question 800/1126 loses all 800 prior generations. Convert to per-item append-mode write before scaling past ~50 q.
- **No CSV submission generator.** `COMPETITION.md` §Submission requires `id,response` CSV with proper double-quoting; current pipeline only writes JSONL. Needed before the first private-set run.
- **Stale display in cell 26 output** (`Saved … run02_baseline_20_tok4096.jsonl`) — `OUTPUT_PATH` in cell 7 is now `run03_tok8192_20.jsonl`; the saved file matches the new path, only the printed text is stale. Self-resolves on the next full run.

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
- **Decision applied:** cutoffs still > 0 → Run 04 will double again to 16384 before changing prompt.

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
