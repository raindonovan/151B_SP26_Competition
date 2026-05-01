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
| 02  | 2026-05-01 | running   | 20 | `data[:20]` | v1     | Transformers | 4096 | —       | —            | —            | —            | —       | —    | [run02_baseline_20_tok4096.jsonl](results/run02_baseline_20_tok4096.jsonl) | Baseline run |

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
