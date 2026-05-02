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

## Pod B — vLLM (Planned)

### Strategy

Pod B is a clean environment built for vLLM. It must be isolated from Pod A's `.venv` — no shared virtual environments.

Use a RunPod template with vLLM pre-installed (official vLLM template or a community image with matching CUDA/PyTorch). This avoids manually resolving CUDA wheel mismatches.

### Setup Steps (first time)

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
- Match sampling params to Pod A: `temperature=0.6`, `top_p=0.95`, `top_k=20`
- `thinking_budget` parameter can cap `<think>` block length — useful for MCQ speed

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
