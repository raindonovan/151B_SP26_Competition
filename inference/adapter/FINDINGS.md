# inference/adapter/FINDINGS.md — Cross-run findings for adapter inference

> **Scope**: patterns and discoveries that cut across multiple adapter-inference runs (`R{NN}_adapter_*` and `R{NN}_sft_eval_*`).
> Single-run findings live in the per-run `findings.md`. Promote here when a finding holds across runs.
> Top-level cross-cutting (e.g. things that hold for adapter AND base model) → `inference/FINDINGS.md`.

## Seeded from `inference/RESEARCH.md` (pre-Day-7 carryover, to be validated/expanded as we catalog each run)

### SFT v5 break-even
- Near break-even with base model (~0.646).
- Regression of ~7 semantic items vs base — NOT format-driven, real math regressions.
- 87% T1-easy training composition is a likely structural cause.
- Memorization ≠ generalization: the 20/20 in-set memorization test was measuring the wrong thing (items were in the training set).
- **Discipline correction (locked)**: held-out validation set required before any future SFT is declared viable.

### Repetition collapse
- Greedy + default sampling on the v5 adapter exhibited repetition collapse.
- Traced to decoding config, NOT weight-space collapse.
- `repetition_penalty=1.1` partially recovers, but the official Qwen guidance prefers `presence_penalty` over `repetition_penalty`.

### WiSE-FT (untried, candidate)
- For LoRA: scale `lora_alpha` by δ (δ=0.5 prior, no retraining).
- Could recover v5 adapter quality without burning more training compute.
- Untried as of Day 7.

## To-add (will populate as we catalog each adapter run)

_Empty._
