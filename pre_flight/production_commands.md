# Production phase commands

All 8 phases (Instance A: A1, A2; Instance B: B1, B2, B3, B4a, B4b, B5).
`<TIMESTAMP>` placeholder = `$(date +%Y%m%d_%H%M)` resolved at launch.

**Ordering:**
- Instance A: A1 and A2 share the SAME vLLM session (continuous batching) — but the runner spawns a fresh vLLM per invocation. To "share session" you must wrap both into one launch script OR accept the ~40s warmup cost per phase. Mark accordingly.
- Instance B: B1 → B2 → B3 → B4a → B4b → B5 sequential

**Conditional:**
- B2 conditional on B1 promising (Strategy decides after B1 completes)
- B3 conditional on a canonical genselect entry point (see B3 below — multiple genselect scripts exist; spec is incomplete)

---

## Phase A1 — SC=16 weak default (128 items)

Expected duration: **~2.5 hr**

```bash
python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --item-ids data/candidates_sc16_weak_default_128.txt \
  --output results/hybrid/sc16_weak_default_<TIMESTAMP>.jsonl \
  --sc 16 \
  --max-tokens 49152 \
  --thinking-budget 24576 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase A2 — SC=16 hardest 30 items

Expected duration: **~1.5 hr** (when continuous-batched with A1; standalone adds ~40s warmup)

```bash
python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --item-ids data/candidates_sc16_hardest30.txt \
  --output results/hybrid/sc16_weak_hard_<TIMESTAMP>.jsonl \
  --sc 16 \
  --max-tokens 81920 \
  --thinking-budget 65536 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase B1 — NoThinking probe 98

Expected duration: **~30–45 min**

```bash
python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --item-ids data/candidates_nothinking_98.txt \
  --output results/hybrid/nothinking_probe98_<TIMESTAMP>.jsonl \
  --no-thinking \
  --sc 8 \
  --max-tokens 5000 \
  --temperature 0.7 --top-p 0.8 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase B2 — NoThinking full 943 (CONDITIONAL on B1 promising)

Expected duration: **~30–90 min**

```bash
python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --item-ids data/private_all_943.txt \
  --output results/hybrid/nothinking_full943_<TIMESTAMP>.jsonl \
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
python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --item-ids data/candidates_pertier_t1to3.txt \
  --output results/hybrid/pertier_t1to3_<TIMESTAMP>.jsonl \
  --sc 8 \
  --max-tokens 49152 \
  --thinking-budget 24576 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase B4b — Per-tier control T4

Expected duration: **~30 min**

```bash
python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --item-ids data/candidates_pertier_t4.txt \
  --output results/hybrid/pertier_t4_<TIMESTAMP>.jsonl \
  --sc 8 \
  --max-tokens 81920 \
  --thinking-budget 65536 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --repetition-penalty 1.1
```

## Phase B5 — Greedy probe 158 weak

Expected duration: **~15–20 min**

```bash
python3 scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --item-ids data/candidates_sc16_weak_158.txt \
  --output results/hybrid/greedy_weak158_<TIMESTAMP>.jsonl \
  --sc 1 \
  --max-tokens 49152 \
  --thinking-budget 24576 \
  --temperature 0.0
```

(Greedy: temperature=0; top_p / top_k / rep_penalty omitted since they have no effect on greedy decoding.)

---

## Per-flag argparse verification

Confirmed via `python3 scripts/run_hybrid_inference.py --help` (after Task 3):

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
- `--no-thinking` ✓ (new)
- `--top-k` ✓ (new)
- `--min-p` ✓ (new)
- `--repetition-penalty` ✓ (new)
- `--presence-penalty` ✓ (new — not used in any of the 8 phases, exposed per Task 3)
