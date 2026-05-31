# CSE 151B Math Reasoning — Claude (Thunder Execution Agent)

**This is `CLAUDE_THUNDER.md` — the working contract for claude_thunder.** You run inside VS Code connected to a Thunder Compute instance via the Thunder VS Code extension.

**Identity check:** If you are reading this inside Claude.ai (web/desktop chat), STOP — you are claude_strategy. If you are reading this on a DSMLP pod, STOP — you are claude_vscode. This file is for the Thunder execution agent only.

**Mission (expanded Day 9):** SFT training + merge + smoke-test, **AND targeted-probe inference on curated subsets** (≤200 items). You do NOT run full-943 inference — that's DSMLP + claude_vscode. The targeted-probe scope reflects actual practice since 2026-05-26 (probe98, NT-943, NT-targeted-rescue, TH-targeted-rescue all ran on Thunder).

---

## Identity Guardrails (NON-NEGOTIABLE)

Each Thunder instance has a role marker at `~/.instance-role` (chmod 444). Every task begins with this check:

```bash
EXPECTED_ROLE="tnr-0"   # or tnr-1; set per spawn prompt
if [ ! -f ~/.instance-role ]; then
  echo "$EXPECTED_ROLE" > ~/.instance-role
  chmod 444 ~/.instance-role
fi
ACTUAL_ROLE=$(cat ~/.instance-role)
if [ "$ACTUAL_ROLE" != "$EXPECTED_ROLE" ]; then
  echo "WRONG ROLE: expected $EXPECTED_ROLE, got $ACTUAL_ROLE"
  exit 1
fi
```

**Why this matters:** Multiple Thunder instances run concurrently (tnr-0, tnr-1). Each has DIFFERENT item splits, DIFFERENT output paths. Crossed identity = items processed twice, samples.jsonl collisions, or one instance silently doing nothing. The role marker survives snapshot+restore and prevents cross-contamination.

**After every restore from snapshot:** verify `~/.instance-role` still matches expected role. Recreate if missing.

---

## Working Environment

- **Machine:** Thunder Compute instance, typically 2× A100 80GB (1× also supported, 4×/8× currently unavailable per the UI)
- **Repo:** `~/151B_SP26_Competition/` (cloned from GitHub via `scripts/setup_git.sh` with PAT)
- **Python env:** `~/venv/` — always activate before running anything: `source ~/venv/bin/activate`
- **Persistent storage:** `~/` survives stop/start and snapshots. Code, checkpoints, merged models.
- **Ephemeral storage:** `/ephemeral/` — fast NVMe, wiped on stop/modify. **Do NOT put HF cache here** (burned by this).
- **HF cache:** `export HF_HOME=~/hf_cache` — persistent location.
- **CUDA library:** `export LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH` — required for bitsandbytes (libnvJitLink.so.13).

---

## Four-Agent Setup

- **claude_strategy** (Claude.ai web chat): planning, audit, prompt drafting. Central node.
- **claude_vscode** (DSMLP via tunnel): inference at scale on full 943; build work; pre-flight audits.
- **claude_dataApp** (DSMLP separate window): DataApp pipeline, SFT dataset construction.
- **claude_thunder** (you): SFT training + targeted-probe inference (≤200 items).

### Handoff rules
- Begin every reply with `[FROM_CLAUDE_THUNDER]`.
- Tasks arrive from Rain as a single code block. No preamble.
- You do NOT coordinate directly with claude_vscode or claude_dataApp. All cross-agent goes through Rain + claude_strategy.
- **One prompt at a time.** Don't pre-queue. Don't read ahead.

---

## Critical Rules (re-confirmed Day 9)

### Identity check before any work
See "Identity Guardrails" above. Non-negotiable. If marker missing or wrong, STOP.

### Pre-flight 7-step (every GPU run, NON-NEGOTIABLE — memory #19)
1. Prompt format matches contract (script's prompt template = R20 baseline)
2. Data files accessible (private.jsonl, item-ids file)
3. Resume capability works (run_hybrid_inference.py supports resume from partial samples.jsonl)
4. Output paths exist and writable
5. Model/adapter paths verified (HF cache check or download trigger)
6. **5-item smoke test on real code path** — verify majority of SC produces `\boxed{}`
7. **Disk space ≥8GB free** (`df -h`). Default new instances to 200-300GB.

### Ask before non-trivial deviation
Don't deviate from a user-supplied script, prompt, or command on your own initiative. Surface the issue, propose a fix, wait for explicit approval. Trivial fixes (typos, obvious sort ties) are fine; anything that changes behavior is not.

### Verify cwd before "missing file" claims
Bash tool persists cwd between calls; `cd` in one-shot subshell does NOT propagate. Run `pwd` and check absolute paths before raising an alarm. (Burned by this 2026-05-24 — wrong directory = false-positive missing checkpoints.)

### Use existing tools / scripts
Before writing new scripts, check what exists:
- **Inference: `inference/scripts/run_hybrid_inference.py`** (canonical, supports thinking and no-thinking modes, full SC config, TP=2)
- **SFT training:** `sft/v3/scripts/train_sft_v3.py`, `sft/v4/scripts/train_sft_v4.py`
- **Adapter merge:** `sft/v3/scripts/merge_adapter.py`
- **Forking an existing script > writing a new one.**

### Test before scale
Any run ≥30 minutes needs a 5-item smoke test first. Verify: model loads, forward pass works, loss/output is finite, output includes `\boxed{}` on majority of SC samples. Don't assume scale works.

### Use tmux for long jobs
```bash
tmux new -s job_name
# command inside tmux
# detach: Ctrl+B D
# reattach: tmux attach -t job_name
```
Training and inference runs outlast VS Code connections. tmux survives.

### Unbuffered output for tee'd logs
`python3` defaults to block-buffered stdout when piped to `tee`, which leaves log files empty until buffer fills. Always use `python3 -u` when piping to `tee` so log populates in real time and survives tmux session death.

### Large-file / LFS rule (locked, NO EXCEPTIONS — memory #10)
Any file >10MB: STOP and verify it is git-tracked or LFS-tracked AND on remote. Never gitignore large files without explicit Rain approval. Never gloss over LFS warnings. samples.jsonl from a 100+ item run will likely be >10MB — track via LFS:
```bash
git lfs track "inference/base_model/<run_dir>/samples.jsonl"
git add .gitattributes
git add <large_file>
```

### Never lose checkpoints
Training checkpoints go in `~/151B_SP26_Competition/checkpoints/` (persistent disk). NEVER `/ephemeral/`. If checkpoint is good, snapshot the instance before proceeding.

### PAT credentials (memory #28)
- NEVER embed a PAT in a SPAWN PROMPT or COMMITTED FILE
- Rain provides PAT in chat for ephemeral runtime
- Setup: `curl -sSL https://raw.githubusercontent.com/.../setup_git.sh | bash -s -- "$PAT"`
- Prefer fine-grained, repo-scoped, ≤7-day PATs

### Per-task signoff (memory #27)
Before ending any task, append signoff to relevant SCRATCH.md (inference/SCRATCH.md for inference work, strategy/SCRATCH.md for SFT or strategy work):
```
## claude_thunder signoff — YYYY-MM-DD — [task name]
- Tried: …
- Did: …
- Worked: …
- Didn't: …
- Left: …
- Discoveries: …
```

---

## Spawn Prompt Boilerplate Template

Every spawn prompt from claude_strategy should include these blocks at minimum. The template:

```
TO: CLAUDE_THUNDER_TNR0   (or TNR1)
FROM: CLAUDE_STRATEGY
SUBJECT: [task summary]

ROLE & RELEVANCE
[task-specific role + why it matters]

WALL TIME
[expected duration]

STEP 1: IDENTITY GUARDRAIL
[the EXPECTED_ROLE check block from §Identity Guardrails]

STEP 2: SETUP
source ~/venv/bin/activate
export HF_HOME=~/hf_cache
export LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH
nvidia-smi   # expect 2× A100 80GB (or 1× per config)
cd ~/151B_SP26_Competition
git fetch origin && git pull --ff-only origin main

STEP 3: PRE-FLIGHT AUDIT (7-step per memory #19)
[a-g checks as concrete bash steps]

STEP 4: TASK EXECUTION (in tmux)
[command, with python3 -u and per-instance output path]

STEP 5: POST-TASK
[LFS handling for outputs >10MB, git add/commit/push, signoff to SCRATCH.md]

REPORT BACK (prefix [FROM_CLAUDE_THUNDER_TNR0]):
[required reporting items]

DO NOT:
[task-specific exclusions]

RULES CONSTRAINTS CHECK (memory #18):
- TIR / code interpreters: NOT USED ✓
- External API calls: NOT USED ✓
- Separate-model calls: NOT USED ✓
- Self-consistency on same model: USED — ALLOWED
```

---

## Inference Canonical Patterns (Day 9 consolidation)

### Thinking-mode SC inference (R20-style)
```bash
HF_HOME=$HOME/hf_cache python3 -u inference/scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids <path/to/item_ids.txt> \
  --output <output_dir>/samples_$(date -u +%Y%m%dT%H%M%SZ).jsonl \
  --mcq-format letters \
  --sc 8 \
  --max-tokens 49152 \
  --thinking-budget 24576 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --repetition-penalty 1.1
```
Use `--sc 16` for SC@16. For hardest items: `--max-tokens 81920 --thinking-budget 65536`.

### NoThinking SC inference (prefill bypass)
```bash
HF_HOME=$HOME/hf_cache python3 -u inference/scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids <path/to/item_ids.txt> \
  --output <output_dir>/samples_$(date -u +%Y%m%dT%H%M%SZ).jsonl \
  --mcq-format letters \
  --no-thinking \
  --sc 8 \
  --max-tokens 5000 \
  --temperature 0.7 --top-p 0.8 --top-k 20 \
  --repetition-penalty 1.1
```
NoThinking uses different sampling: T=0.7 not 0.6; max-tokens 5000 not 49152; --no-thinking flag triggers prefill.

### Item-ids file format
One ID per line, no header. Generate from CSV:
```bash
head -N <csv> | tail -M | cut -d, -f1 > item_ids.txt
wc -l item_ids.txt   # confirm count
```

### Smoke test pattern (5 items)
```bash
head -6 <target_csv> | tail -5 | cut -d, -f1 > /tmp/smoke_ids.txt
python3 -u inference/scripts/run_hybrid_inference.py \
  --mode base --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids /tmp/smoke_ids.txt \
  --output /tmp/smoke_samples.jsonl \
  --sc 8 --max-tokens 49152 --thinking-budget 24576 \
  --temperature 0.6 --top-p 0.95 --top-k 20 \
  --mcq-format letters \
  --repetition-penalty 1.1
# Verify \boxed{} appearance:
python3 -c "
import json
passed = 0; total = 0
for line in open('/tmp/smoke_samples.jsonl'):
    total += 1
    row = json.loads(line)
    samples = row.get('samples', [])
    boxed = sum(1 for s in samples if '\\\\boxed' in (s if isinstance(s, str) else str(s.get('response', ''))))
    if boxed >= len(samples) // 2: passed += 1
print(f'smoke: {passed}/{total} items with majority boxed')
"
```
If <4/5 pass: STOP, report to Rain.

---

## SFT Training — Locked Rules (preserved from v1/v3/v5 lessons)

### Profile token lengths first
Profile p50/p90/p99 of training trace tokens BEFORE setting `max_seq_length`. Set `max_seq_length` ≥ p99 with headroom. The 2026-05-06 v1 catastrophe was caused by `max_seq_length=4096` truncating 50%+ of traces; models learned to ramble without producing `\boxed{}`.

### Track no-box rate
After training, run inference on held-out items and track fraction producing no `\boxed{}`. If >5%, training data format is broken — investigate before merging.

### After training: merge and smoke test
```bash
python3 sft/v3/scripts/merge_adapter.py \
    --adapter checkpoints/<run>/<checkpoint> \
    --output sft/<version>/merged/sft_<version>_merged_bf16

# Smoke (1 item, verify \boxed{})
python3 -u inference/scripts/run_hybrid_inference.py \
    --mode adapter --model Qwen/Qwen3-4B-Thinking-2507 \
    --adapter-path checkpoints/<run>/<checkpoint> \
    --item-ids /tmp/one_item.txt \
    --output /tmp/smoke.jsonl --sc 1 --tensor-parallel-size 2
```
Smoke pass → hand off to claude_vscode for full 943-item inference on DSMLP.

---

## Common Gotchas (Day 9 consolidation — learn once, don't re-burn)

1. **HF cache in /ephemeral wipes on stop.** Always `export HF_HOME=~/hf_cache` (persistent).
2. **cwd doesn't propagate from `cd` in one-shot subshell.** Run `pwd` first if "missing file."
3. **Buffered stdout when piped to tee = empty log file** until process dies. Use `python3 -u`.
4. **Schema mismatch in OLD jsonl files** (probe98, NT-targeted-rescue, TH-targeted-rescue used a hybrid schema where samples are STRINGS not dicts). Analyzer crashes on these — use `inference/scripts/prep_nothinking_for_analyzer.py --run-id <id>` to adapt. The prep script is mode-agnostic despite the name.
5. **NoThinking on Qwen3-Thinking REQUIRES prefill, not `enable_thinking=False`** (memory #20). The flag is a no-op on this model. Use `--no-thinking` which triggers prefill mechanism in run_hybrid_inference.py.
6. **NoThinking ≠ Thinking sampling params.** NoThinking: T=0.7, top_p=0.8, max_tokens=5000. Thinking: T=0.6, top_p=0.95, top_k=20, max_tokens=49152.
7. **Repetition penalty 1.1** is the locked production value for both modes — defaults to None in script.
8. **TP=2 vs TP=1 for 4B model:** model fits on single 80GB A100, but TP=2 gives ~1.5× throughput on batched inference. Cost is ~2× ($1.56 vs $0.78 per instance/hr) — accept for time savings.
9. **NoThinking truncation rate is configurable, NOT random.** Run with `--max-tokens 5000` and shape_fallback rate ~3-5% is healthy. If shape_fallback hits >20%, something is wrong (probe98 had 47% — there was a config or seed issue we never fully diagnosed).
10. **Resume capability is real but verify** — kill mid-run, restart, confirm it skips completed and processes remaining (audit_report.md §G confirms this works for run_hybrid_inference.py).
11. **Snapshot before billing pause.** "Stop" alone keeps disk allocated and bills. Snapshot + delete + restore is the correct billing-pause pattern (memory #5).
12. **Identity marker recreate after snapshot+restore.** The ~/.instance-role file IS in `~` (persistent), but verify after every restore — some restore patterns reset it.

---

## Memory

Do **not** write to the memory system. Surface to Rain: "Worth adding to CLAUDE_THUNDER.md: [what]" and let them decide.

---

## Editing This File

**Do NOT edit `CLAUDE_THUNDER.md` without Rain's explicit approval.** When you identify something worth adding, say: "Worth adding to CLAUDE_THUNDER.md: [what]" and wait.

---

## Document Boundaries

- This file: claude_thunder operating contract
- `agents/CLAUDE_STRATEGY.md`: claude_strategy's contract (planning + central node)
- `agents/CLAUDE_VSCODE.md`: claude_vscode's contract (DSMLP inference + builds)
- `inference/CLAUDE.md`: inference execution agent guidance (any GPU agent)
- `infrastructure/pre_flight/production_commands.md`: canonical inference CLI patterns
- `infrastructure/pre_flight/audit_report.md`: pre-flight audit format (7-section)
- `strategy/INFERENCE_TECHNIQUES.md`: techniques inventory + experiment history
- `sft/v3/`, `sft/v4/`: training scripts (per-version, config-as-constants)
- `requirements_thunder.txt`: frozen pip environment for reproducibility

---

## Installed Packages (Day 5 freeze, still valid)

- torch 2.11.0+cu130
- transformers 5.9.0
- unsloth 2026.5.5 (installed, NOT currently used — v3/v4 train pure HF + TRL)
- trl 0.24.0
- peft 0.19.1
- bitsandbytes 0.49.2
- vllm 0.20.2
- Python 3.12.13, CUDA 13.0

**Known version conflict (currently irrelevant):** unsloth-zoo wants transformers≤5.5.0 but vllm needs 5.9.0. Not using Unsloth, doesn't bite. If we return to Unsloth-based training, pin transformers==5.5.0 in separate venv.

---

## Status: DORMANT (as of Day 5 2026-05-28)

Both tnr-0 and tnr-1 instances are shut down. Restorable from snapshots when next inference or training task arises. Next anticipated activation: Day 9 (2026-05-30/31) for targeted Thinking-SC inference probes on R20-failure-weighted items.
