# CSE 151B SP26 — Experiment Log

## Environment

- Compute: NVIDIA GeForce RTX 4090 (24 GB)
- Model: `Qwen/Qwen3-4B-Thinking-2507`
- Quantization: 4-bit BitsAndBytes (INT4, double quant, bf16 compute)
- Torch: 2.11.0+cu128 | CUDA: 12.8 | Transformers: 5.7.0
- Kernel: Python (cse151b)

---

## Results Summary

| Run | Date       | Status    |  N | Data slice  | Prompt | Method       | tok  | Cutoffs | MCQ          | Free         | Overall      | Runtime | Cost | Results file | Notes |
|-----|------------|-----------|---:|-------------|--------|--------------|-----:|--------:|:-------------|:-------------|:-------------|---------|------|--------------|-------|
| 01  | 2026-05-01 | completed |  5 | `data[:5]`  | v1     | Transformers | 2048 | ?       | 0/2 = 0.0%   | 2/3 = 66.7%  | 2/5 = 40.0%  | —       | —    | [starter_results.jsonl](results/starter_results.jsonl) | Smoke test; cutoffs not tracked |
| 02  | 2026-05-01 | completed | 20 | `data[:20]` | v1     | Transformers | 4096 | 9/20?   | 3/9 = 33.3%  | 6/11 = 54.5% | 9/20 = 45.0% | —       | —    | [run02_baseline_20_tok4096.jsonl](results/run02_baseline_20_tok4096.jsonl) | 9/20 missing \boxed{}; likely cutoffs |
| 03  | 2026-05-01 | completed | 20 | `data[:20]` | v1     | Transformers | 8192 | 6/20    | 3/9 = 33.3%  | 6/11 = 54.5% | 9/20 = 45.0% | 123.8 h est | —    | [run03_tok8192_20.jsonl](results/run03_tok8192_20.jsonl) | Cutoffs 9→6; score unchanged |

---

## Token Budget Notes

For thinking models, `max_new_tokens` is an accuracy variable, not only a runtime/cost variable. If generation is cut off before the final `\boxed{...}` appears, the scorer marks the response wrong even if the reasoning was correct.

**Cutoff** = generation hit `max_new_tokens` before a `\boxed{}` was found in the output.

When comparing token budgets, hold prompt, data slice, sampling params, and model fixed — change only `max_new_tokens`.

Decision rule after each run:
- Cutoffs > 0 → run same slice at 2× token budget before changing anything else
- Cutoffs = 0 → token budget is not the bottleneck; move to prompt or method experiments

> `avg_gen_tokens` column to be added once runs are scripted (useful for comparing e.g. 4096 cap / avg 1700 tokens / 0 cutoffs vs 2048 cap / avg 2020 tokens / 3 cutoffs).

---

## Run Details

### Run 01 — Smoke test

**Rationale:** First run ever. Goal was purely to verify the pipeline works end-to-end — model loads, prompt builds, generation runs, scorer doesn't crash. Used only 5 questions to keep it fast. Token cap of 2048 was a conservative placeholder; we knew it might be too short for a thinking model but didn't want to wait long on a smoke test.

- **Data:** `data[:5]` — 2 MCQ, 3 free-form
- **Method:** Transformers + TextStreamer

| param | value | note |
|-------|------:|------|
| max_new_tokens | 2048 | capped: `min(MAX_TOKENS=32768, 2048)` |
| max_length | 16384 | input truncation |
| temperature | 0.6 | |
| top_p | 0.95 | |
| top_k | 20 | |
| repetition_penalty | 1.0 | |
| do_sample | True | |
| enable_thinking | True | default (not explicitly set) |
- **Runtime:** —
- **Cost est.:** —
- **Results:** `results/starter_results.jsonl`

**Observations:**
- Pipeline works end-to-end.
- `max_new_tokens=2048` may cut off reasoning mid-thought — thinking is ON.
- Cutoffs not tracked (added to table as `?`).
- Sample too small to judge quality.

---

### Run 02 — Baseline 20 questions

**Rationale:** Pipeline confirmed working. Scaled to 20 questions and doubled the token cap to 4096 to get a more meaningful baseline score before touching the prompt. We suspected 2048 was cutting off the model's thinking chain, so 4096 was a first attempt to give it more room. Post-run we found 9/20 responses had no `\boxed{}` at all — strong signal the model is still hitting the cap before finishing its answer. This makes the 4096 baseline effectively a floor, not a real score.

- **Data:** `data[:20]`
- **Method:** Transformers + TextStreamer

| param | value | note |
|-------|------:|------|
| max_new_tokens | 4096 | |
| max_length | 16384 | input truncation |
| temperature | 0.6 | |
| top_p | 0.95 | |
| top_k | 20 | |
| repetition_penalty | 1.0 | |
| do_sample | True | |
| enable_thinking | True | default (not explicitly set) |
- **Runtime:** —
- **Cost est.:** —
- **Results:** [run02_baseline_20_tok4096.jsonl](results/run02_baseline_20_tok4096.jsonl)

**Observations:**
- MCQ 3/9 = 33.3% | Free 6/11 = 54.5% | Overall 9/20 = 45.0%
- 9/20 responses had no `\boxed{}` in output — all marked wrong
- Likely many cutoffs at 4096 tokens before model finished thinking and wrote final answer
- gen_tokens/gen_secs not tracked this run (added for Run 03+); cutoff count is estimated
- **Next:** Run 03 same slice at 8192 tokens to test if cutoffs are the bottleneck

---

### Run 03 — Token budget test

**Rationale:** Run 02 had 9/20 responses with no `\boxed{}`, and inspection of the raw tails confirmed every single one was cut off mid-sentence. The model never finished its thinking chain — it wasn't a prompt or reasoning failure, just running out of tokens. Per our decision rule (cutoffs > 0 → double budget before changing anything else), Run 03 doubles to 8192 tokens with everything else held fixed. If the missing-boxed count drops and accuracy jumps, the diagnosis is confirmed.

- **Data:** `data[:20]`
- **Method:** Transformers + TextStreamer

| param | value | note |
|-------|------:|------|
| max_new_tokens | 8192 | 2× Run 02 |
| max_length | 16384 | input truncation |
| temperature | 0.6 | |
| top_p | 0.95 | |
| top_k | 20 | |
| repetition_penalty | 1.0 | |
| do_sample | True | |
| enable_thinking | True | default (not explicitly set) |
- **Runtime:** —
- **Cost est.:** —
- **Results:** [run03_tok8192_20.jsonl](results/run03_tok8192_20.jsonl)

**Observations:**
- TBD

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
