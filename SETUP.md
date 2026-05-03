# CSE 151B SP26 — Environment & Infrastructure

## Overview

Two isolated compute environments are maintained on RunPod. Both share the same GitHub repo as the single source of truth. Only one pod runs at a time — pause the inactive pod to avoid double billing.

```
GitHub repo (source of truth)
    ├── Pod A — Transformers (current, stable)
    └── Pod B — vLLM (planned, for scaling)
```

---

## Pod A — Transformers (Current)

### Hardware

| Item | Value |
|------|-------|
| GPU | NVIDIA GeForce RTX 4090 |
| VRAM | 24 GB |
| Cost | $0.69 / hr |

### Software Stack

| Package | Version |
|---------|---------|
| Python | 3.11 |
| CUDA | 12.8 |
| PyTorch | 2.11.0+cu128 |
| Transformers | 5.7.0 |
| BitsAndBytes | INT4 (double quant, bf16 compute) |
| Kernel | Python (cse151b) |

### Model

```
Qwen/Qwen3-4B-Thinking-2507
```

Loaded with 4-bit BitsAndBytes quantization. Inference runs sequentially via Transformers + TextStreamer.

### Known Performance Characteristics

- Mean generation time: ~395 s/question (Run 03, 8192 token cap)
- At this pace, full 1126-question run ≈ 124 hrs ≈ $85
- 6/20 questions hit the 8192-token cap in Run 03 (5 of 6 are MCQ)
- Sequential generation is the bottleneck — Pod B (vLLM) is required for overnight/large runs

### Environment Path

```
/workspace/151B_SP26_Competition/.venv
```

Do not modify this environment. It is the stable fallback.

### Resuming Pod A

1. Start pod on RunPod dashboard
2. Open JupyterLab
3. `git pull` in `/workspace/151B_SP26_Competition`
4. Select kernel `Python (cse151b)`
5. Run notebook from top

---

## Pod B — vLLM (Working)

### Hardware

| Item | Value |
|------|-------|
| GPU | NVIDIA GeForce RTX 4090 |
| VRAM | 24 GB |

### Software Stack

| Package | Version |
|---------|---------|
| Python | 3.x (in `.venv`) |
| Torch | 2.6.0+cu124 |
| Transformers | 4.51.3 |
| vLLM | 0.8.5 |
| Engine | vLLM **V0** (V1 disabled) |
| dtype | bfloat16 (no quantization) |
| gpu_memory_utilization | 0.85 |

### Critical: VLLM_USE_V1=0

vLLM 0.8.5 on this pod **only works with the V0 engine**. The V1 engine fails to initialize.
Set the env var **before** importing vllm:

```python
import os
os.environ["VLLM_USE_V1"] = "0"
import vllm  # must come after
```

`scripts/run_vllm_experiment.py` already does this. Any new vLLM script must do the same.

### Environment Path

```
/workspace/151B_SP26_Competition/.venv
```

Despite the SETUP.md two-pod plan calling for environment isolation, vLLM was
installed into the same `.venv` as Pod A's Transformers stack on this pod
(single-pod setup). It works; treat the `.venv` as the canonical environment
for both engines on this machine. If a true two-pod split is later needed,
revisit this section.

### Smoke test (already verified)

The smoke test from the original Pod B plan was run with
`scripts/run_vllm_experiment.py --data-end 5 --max-new-tokens 2048`.
Pipeline ran end-to-end; cutoffs were expected at 2048 tokens for
Qwen3-Thinking. See `results/run_vllm_smoke_5_tok2048.jsonl`.

### Verifying vLLM still works

```bash
/workspace/151B_SP26_Competition/.venv/bin/python -c "
import os
os.environ['VLLM_USE_V1'] = '0'
import vllm, torch, transformers
print('vllm', vllm.__version__)
print('torch', torch.__version__)
print('transformers', transformers.__version__)
print('cuda', torch.version.cuda, '| device', torch.cuda.get_device_name(0))
"
```

Expected: `vllm 0.8.5 | torch 2.6.0+cu124 | transformers 4.51.3 | cuda 12.4 | RTX 4090`.

### Original Pod B Plan (kept for reference)

The original two-pod plan called for a clean isolated environment built from a
vLLM-pre-installed RunPod template. That plan is preserved below in case the
single-pod setup needs to be split later:

1. On RunPod dashboard: **Deploy Pod** → select GPU → choose vLLM-compatible template
2. Open terminal on new pod
3. Clone repo:
   ```bash
   git clone <repo-url> /workspace/151B_SP26_Competition
   cd /workspace/151B_SP26_Competition
   ```
4. Install only missing project dependencies (do not install Transformers/BNB into this env)
5. Verify vLLM import:
   ```python
   import os; os.environ["VLLM_USE_V1"] = "0"
   import vllm; print(vllm.__version__)
   ```
6. Run smoke test (see below)

### vLLM Smoke Test (Run vLLM-smoke-01)

Before any real runs, verify the full pipeline:

| Parameter | Value |
|-----------|-------|
| Data | `data[:5]` |
| Prompt | v1-baseline (same as Run 01) |
| max_new_tokens | 4096 |
| Goal | Pipeline runs end-to-end, `\boxed{}` appears in output |

Success criteria:
- `import vllm` succeeds
- `Qwen/Qwen3-4B-Thinking-2507` loads
- All 5 questions generate output
- At least 4/5 outputs contain `\boxed{}`
- Scorer runs without error

### vLLM Parity Check (Run vLLM-parity-20)

After smoke test passes, run the same 20 questions as Run 03 and compare:

| Parameter | Value |
|-----------|-------|
| Data | `data[:20]` |
| Prompt | v1-baseline |
| max_new_tokens | 8192 |
| Goal | Accuracy within ~5pp of Run 03 (50%), `\boxed{}` extraction rate matches |

This confirms vLLM produces equivalent outputs before it becomes the primary inference path.

### Qwen3-Thinking Specifics for vLLM

- Verify thinking mode is active (check for `<think>` blocks in output)
- Match sampling params to Pod A: `temperature=0.6`, `top_p=0.95`, `top_k=20`, `repetition_penalty=1.0`
- `thinking_budget` parameter can cap `<think>` block length — useful for MCQ speed

### Running an experiment

Use `scripts/run_vllm_experiment.py`. It owns the v1-baseline prompts, MCQ
detection by non-empty `options`, chat-template construction, vLLM batched
generation, and Judger-based scoring. Each run writes a JSONL of per-question
rows and a sidecar `*.summary.json` with run-level metrics.

Example:

```bash
/workspace/151B_SP26_Competition/.venv/bin/python scripts/run_vllm_experiment.py \
  --run-id run04_vllm_parity_20_tok8192 \
  --data-start 0 \
  --data-end 20 \
  --max-new-tokens 8192 \
  --max-model-len 16384 \
  --output results/run04_vllm_parity_20_tok8192.jsonl
```

CLI args: `--run-id`, `--data-start`, `--data-end`, `--max-new-tokens`,
`--output`, `--max-model-len` (default 16384), `--data-path` (default
`data/public.jsonl`).

**`max_model_len` matters.** vLLM caps **prompt + generation combined**
at this value. Setting `max_model_len == max_new_tokens` silently shrinks
the effective generation budget on any non-empty prompt (effective gen
budget = `max_model_len − prompt_len`). For full 8k generation regardless
of prompt length, keep the 16384 default. For a 16k generation budget,
override to ~24576 (16384 + headroom for prompts).

---

## Git Sync Workflow

**Rule: commit and push before switching pods.**

```bash
# Before pausing a pod
git add experiments.md results/ starter_code_cse151b_comp.ipynb
git commit -m "Run XX: <description>"
git push

# After starting the other pod
git pull
```

Never leave results, notebook state, or `experiments.md` updates only on a pod's local disk. If a pod is terminated (not paused), uncommitted work is lost.

### Pause vs Terminate

| Action | Disk | Cost | When to use |
|--------|------|------|-------------|
| **Pause** | Preserved | ~$0/hr (tiny storage fee) | Normal switching between pods |
| **Terminate** | Deleted | $0 | Only if pod is permanently abandoned |

Always **pause**, never terminate, unless you are certain the environment is no longer needed.

---

## Inference Speed Levers (within Transformers)

While vLLM is being set up, these can be applied to Pod A:

1. **Early stopping on `\boxed{}`** — stop generation as soon as the answer appears; saves the remaining token budget for every question that answers before the cap
2. **Per-type token caps** — MCQ only needs one letter; use a lower `max_new_tokens` for MCQ than for free-form
3. **`thinking_budget`** — Qwen3-Thinking supports capping the `<think>` block length directly

---

## Overnight / Large Run Plan (vLLM)

Once parity is confirmed on Pod B, large runs move there:

| Run type | Questions | Method | Est. runtime |
|----------|-----------|--------|-------------|
| Prompt sweep (5 policies) | 50 each | vLLM | TBD after parity |
| Validation | 100–200 | vLLM | TBD |
| Self-consistency k=3 | 50 | vLLM | TBD |
| Full competition run | 1126 | vLLM | TBD |

Update this table once vLLM benchmarks are available from the parity run.
