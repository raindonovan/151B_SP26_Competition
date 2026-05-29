# inference/base_model/ — Inference runs with vanilla base model (no adapter)

> **Scope**: runs of the locked base model (`Qwen3-4B-Thinking-2507`) WITHOUT any adapter loaded. This is the bulk of our inference work.

## Naming convention (same as adapter folder)

```
R{NN}_{purpose}_{variant}_{decoding}_{items}_{tokens}/
```

Where:
- `R{NN}` = sequential run number, chronological from day 1.
- `purpose` ∈ `{baseline, eval, smoke, poc, ablation}`.
- `variant` = post-processing combo applied at inference (e.g. `v1base`, `v1pp1`). For pure base-model with no inference-time tweaks, `v1base`.
- `decoding` ∈ `{greedy, sc8, sc16, sc32, nothink}`.
- `items` = item set (e.g. `f50`, `p943`).
- `tokens` = token budget (e.g. `t16k`, `t32k`).

Example: `R09_eval_v1base_sc8_p943_t16k/`

## Per-run folder contents

Each `R{NN}_.../` subfolder contains EVERYTHING for that run:

- `README.md` — what it was, when, exact config, who ran it
- `findings.md` — what we learned (short by default; escalate to `inference/FINDINGS.md` for cross-cutting)
- `samples.jsonl` (or LFS pointer) — raw per-sample outputs
- `summary.json` — derived metrics, voted answers
- `scripts/` — the exact run script(s) used
- `decision.md` — only if a decision came out of this run

## Cross-folder docs

- `FINDINGS.md` — base-model cross-run patterns (e.g. "SC8 plateaus at 0.646 regardless of token budget beyond 16K")
- `SCRATCH.md` — unsorted observations, append-only
- `inference/runs/CATALOG.md` — master rename + status index
- `inference/FINDINGS.md` — top-level cross-cutting findings
