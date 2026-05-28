# Production phase commands

7 active phases (B3 deferred to Day 2). Timestamps resolved at launch via `$(date -u +%Y%m%dT%H%M%SZ)`.

**Ordering:**
- Instance A: A1 → A2 (each spawns its own vLLM; ~40s warmup per phase is acceptable)
- Instance B: B1 → B2 → B4a → B4b → B5 sequential

**Conditional:**
- **B2** conditional on B1: run B2 ONLY IF B1's NoThinking on the 18 no-box items produces boxed answers on **≥3 of the 18** (vs base thinking 0/18). Otherwise skip B2.
- **B3** (GenSelect) deferred to Day 2.

**Common preamble for both instances:**
- The runner creates `os.path.dirname(args.output)` automatically (`scripts/run_hybrid_inference.py:282`), so no explicit `mkdir -p` needed.
- `HF_HOME=$HOME/hf_cache` set inline on each command to keep model downloads in a known location.
- All phases use `--tensor-parallel-size 2` for the 2× A100 nodes.

---

## Phase A1 — SC=16 weak default (128 items)

Expected duration: **~2.5 hr**

```bash
HF_HOME=$HOME/hf_cache python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids data/candidates_sc16_weak_default_128.txt \
  --output results/hybrid/tnr-A/sc16_weak_default_$(date -u +%Y%m%dT%H%M%SZ).jsonl \
  --mcq-format letters \
  --sc 16 \
  --max-tokens 49152 \
  --thinking-budget 24576 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase A2 — SC=16 hardest 30 items

Expected duration: **~1.5 hr**

```bash
HF_HOME=$HOME/hf_cache python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids data/candidates_sc16_hardest30.txt \
  --output results/hybrid/tnr-A/sc16_weak_hard_$(date -u +%Y%m%dT%H%M%SZ).jsonl \
  --mcq-format letters \
  --sc 16 \
  --max-tokens 81920 \
  --thinking-budget 65536 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase B1 — NoThinking probe 98

Expected duration: **~30–45 min**

```bash
HF_HOME=$HOME/hf_cache python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids data/candidates_nothinking_98.txt \
  --output results/hybrid/tnr-B/nothinking_probe98_$(date -u +%Y%m%dT%H%M%SZ).jsonl \
  --mcq-format letters \
  --no-thinking \
  --sc 8 \
  --max-tokens 5000 \
  --temperature 0.7 --top-p 0.8 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase B2 — NoThinking full 943 (CONDITIONAL)

**RUN B2 ONLY IF** B1's NoThinking on the 18 no-box items produces boxed answers on **≥3 of the 18** (vs base thinking 0/18). Otherwise skip and move to B4a.

Expected duration: **~30–90 min**

```bash
HF_HOME=$HOME/hf_cache python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids data/private_all_943.txt \
  --output results/hybrid/tnr-B/nothinking_full943_$(date -u +%Y%m%dT%H%M%SZ).jsonl \
  --mcq-format letters \
  --no-thinking \
  --sc 4 \
  --max-tokens 5000 \
  --temperature 0.7 --top-p 0.8 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase B3 — GenSelect — DEFERRED to Day 2

B3 (GenSelect) DEFERRED to Day 2. Repo has 6 `scripts/genselect_*` without a clear canonical production entry point. Will revisit once SC=16 + NoThinking results are in (gives us a basis for which GenSelect variant to use).

## Phase B4a — Per-tier control T1+T2+T3

Expected duration: **~20 min**

```bash
HF_HOME=$HOME/hf_cache python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids data/candidates_pertier_t1to3.txt \
  --output results/hybrid/tnr-B/pertier_t1to3_$(date -u +%Y%m%dT%H%M%SZ).jsonl \
  --mcq-format letters \
  --sc 8 \
  --max-tokens 49152 \
  --thinking-budget 24576 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase B4b — Per-tier control T4

Expected duration: **~30 min**

```bash
HF_HOME=$HOME/hf_cache python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids data/candidates_pertier_t4.txt \
  --output results/hybrid/tnr-B/pertier_t4_$(date -u +%Y%m%dT%H%M%SZ).jsonl \
  --mcq-format letters \
  --sc 8 \
  --max-tokens 81920 \
  --thinking-budget 65536 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase B5 — Greedy probe 158 weak

Expected duration: **~15–20 min**

```bash
HF_HOME=$HOME/hf_cache python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids data/candidates_sc16_weak_158.txt \
  --output results/hybrid/tnr-B/greedy_weak158_$(date -u +%Y%m%dT%H%M%SZ).jsonl \
  --mcq-format letters \
  --sc 1 \
  --max-tokens 49152 \
  --thinking-budget 24576 \
  --temperature 0.0
```

(Greedy: temperature=0; top_p / top_k / rep_penalty omitted since they have no effect on greedy decoding.)

---

## Per-flag argparse verification

Confirmed via `python3 scripts/run_hybrid_inference.py --help`:

- `--mode` ✓
- `--model` ✓
- `--item-ids` ✓
- `--output` ✓
- `--max-tokens` ✓
- `--sc` ✓
- `--temperature` ✓
- `--top-p` ✓
- `--gpu-util` ✓
- `--mcq-format` ✓
- `--thinking-budget` ✓
- `--no-thinking` ✓
- `--top-k` ✓
- `--min-p` ✓
- `--repetition-penalty` ✓
- `--presence-penalty` ✓ (exposed but not used in any current phase)
- `--tensor-parallel-size` ✓
