# inference/adapter/ — Inference runs that loaded an SFT adapter

> **Scope**: runs of the locked base model (`Qwen3-4B-Thinking-2507`) WITH an SFT/LoRA adapter loaded via PEFT.
> **NOT in scope here**: SFT training itself (lives in `inference/adapters/`, which holds training configs/scripts/logs — separate concern, different folder by historical accident).

## Naming convention (applies to all run subfolders here)

```
R{NN}_{purpose}_{variant}_{decoding}_{items}_{tokens}/
```

Where:
- `R{NN}` = sequential run number, chronological from day 1 (00 = first run we have artifacts for; suffix letters for re-runs/variants of the same R-number, e.g. `R14b`).
- `purpose` ∈ `{baseline, eval, smoke, poc, sft_eval, adapter_eval}` — short tag for what the run was for.
- `variant` = model + post-processing combo (e.g. `sft_v5_ep12`, `sft_v4_ckpt588`).
- `decoding` ∈ `{greedy, sc8, sc16, sc32, nothink}`.
- `items` = item set identifier (e.g. `f50` for fixed-50 dev set, `p943` for the full private test set).
- `tokens` = token budget (e.g. `t16k`, `t32k`).

Example: `R20_adapter_eval_sft_v5_ep12_sc8_p943_t16k/`

## Per-run folder contents

Each `R{NN}_.../` subfolder contains EVERYTHING for that run:

- `README.md` — what it was, when, exact config, who ran it (which agent on which runtime)
- `findings.md` — what we learned. If the run was mundane, this is short. If it surfaced a cross-cutting finding, it gets escalated to `inference/FINDINGS.md` with a back-link.
- `samples.jsonl` (or LFS pointer) — raw per-sample outputs with full response text
- `summary.json` — derived metrics, voted answers, etc.
- `scripts/` — the exact run script(s) used (copy, so the run is reproducible even if the canonical script changes)
- `decision.md` — only if a decision came out of this run (e.g. "switch to sc8 as default")

## Cross-folder docs

- `FINDINGS.md` — adapter-specific cross-run patterns (e.g. "sft_v5 break-even with base, ~7-item regression at greedy")
- `SCRATCH.md` — unsorted observations, append-only
- `inference/runs/CATALOG.md` — master rename + status index (covers BOTH adapter and base_model runs in one table)
- `inference/FINDINGS.md` — top-level cross-cutting (e.g. "SC plateaus at N≈16 regardless of decoding")
