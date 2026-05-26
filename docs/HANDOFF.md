# HANDOFF v11 — 2026-05-26 evening

## Purpose

Single document to fully resume Rain's CSE 151B Kaggle competition project in a fresh chat. Covers: state, best scores, infrastructure, active runs, 3-day plan, workflow protocols, key paths.

## Project at a glance

- **Competition**: CSE 151B Kaggle math (943 private items, Qwen3-4B-Thinking-2507)
- **Days remaining**: 6 (deadline approximately 2026-06-02)
- **Two final selections** required per competition rules

## Current scores

| Metric | Score | Notes |
|---|---|---|
| **Best real-inference** | **0.643** | slot1_minimal_norm (NEW 5/26 evening) |
| Best pure base | 0.646 | run14b_v3filtered (32K tokens, V3 shape filter) |
| Best diagnostic | 0.671 | info_4 (T1 base + T2-T4 sheet patches) |
| Adapter v5 alone | 0.639 | slot1 (391 adapter + 552 run14b splice) |
| Submissions used | 22+ | 2/3 slots remaining today |

## Live runs (as of doc creation)

- **tnr-0** (2x A100 80GB, TP=2): chunk=4 batched smoke in progress; A1 production pending smoke green-light.
- **tnr-1** (2x A100 80GB, TP=2): Phase B2 NoThinking full 943 running serial; will be killed and restarted with batched + max_tokens=8192 once tnr-0 validates.
- **vscode** (DSMLP raindonovan tunnel): standing down

Watchdog (push_watchdog.sh) on each Thunder pushes per-instance branches `inference/tnr-0-<TS>` and `inference/tnr-1-<TS>` every 5 min.

## Infrastructure validated tonight

- TP=2 on Qwen3-4B-Thinking-2507 works (NCCL custom_all_reduce, 2 workers, clean)
- thinking_token_budget enforced in vLLM 0.20.2
- NoThinking prefill recipe works under TP=2
- Minimal normalizer (`\left/\right` strip + thin-space strip) rescues ~4 items (+0.4pp on slot1)
- Batched dispatch in run_hybrid_inference.py (commit 5442405): `--batch-size N` flag

## Key contracts

### Inference

- Default: max_tokens=49152, thinking_budget=24576 for Qwen3-4B-Thinking
- Hardest items (T4 / low SC agreement): 81920/65536 per Qwen model card
- NoThinking: --no-thinking flag, max_tokens=**8192** (was 5000 -- bumped 5/27 after 17% truncation)
- Greedy: --sc 1 --temperature 0.0
- TP=2 on Thunder with 2x A100-80GB: model loads ~3 min, KV cache ~898K tokens

### Submission format

- Canonical Kaggle: `\dfrac` + comma+space + single `\boxed{a, b, c}`
- Grader extracts LAST `\boxed{}`, string-matches with dialect tolerance
- 3 submissions/day cap; 2 final selections required

### Adapter v5

- Path: checkpoints/sft_v5/checkpoint-1176/ (LFS, 505MB)
- Trained 16 epochs on Thunder, epoch 12 chosen
- v5 is NEAR BREAK-EVEN with base, NOT format-broken. ~3 semantic items regression
- Likely-wrong manual MCQ overrides: id=184=J not E, id=317=H not D

### 18 no-box items

- IDs: 93, 112, 161, 204, 229, 308, 312, 376, 383, 445, 453, 498, 652, 724, 799, 809, 836, 911
- Unsolvable by LLM consensus regardless of teacher strength
- Rescue path: base-model forced-answer prompting, NOT teacher escalation

## 3-day plan summary

**Day 1 (tonight 5/26)**: Thunder runs complete -> audit -> build candidates.

**Day 2 (5/27)**: Morning fires 3 Kaggle slots. Afternoon: v7 DECISION POINT. Extended PACE start.

**Day 3 (5/28)**: IF v7 GO -> train and infer. IF NO-GO -> GenSelect on Tier 5/no-box items.

**Days 4-5**: Buffer for final selection (2 picks).

See `docs/MASTER_TODO.md` for detailed breakdown.

## Multi-agent protocol

- **claude_strategy** (Claude.ai): plan/audit/teach. Has Drive MCP, Wolfram MCP, git-mcp (READ only)
- **claude_vscode** (DSMLP): repo execution, auto-loads CLAUDE.md
- **thunder-tnr-0**, **thunder-tnr-1**: production runs

### Discipline locked

- Cross-agent prompts prefixed `[FROM CLAUDE_STRATEGY -> TO <window>]` with identity guards
- Identity guard: `EXPECTED_ROLE="tnr-N"; [ "$(cat ~/.instance-role)" = "$EXPECTED_ROLE" ] || exit 1`
- `~/.instance-role` file (chmod 444) on each Thunder instance, set after every snapshot restore
- Single message with ALL outstanding prompts in clear table labeled by target window
- Per-instance output paths (results/hybrid/tnr-A/, tnr-B/)

### Rain context

- ADHD (memory #22) -- capture tangents in TODOs, redirect briskly
- Values understanding reasoning + trade-offs, not just outcomes

## Key paths and IDs

### Repo (github.com/beepbeeepimajeep/151B_SP26_Competition, PUBLIC)

- Inference results: results/hybrid/tnr-A/, results/hybrid/tnr-B/
- Adapter v5: checkpoints/sft_v5/checkpoint-1176/ (LFS, 505MB)
- Answer sheet v5.1: results/answer_sheet/unified_answer_sheet_v5_1.csv
- Submission slot1_minimal_norm: submissions/slot1_minimal_norm.csv (LFS, scored 0.643)
- Per-instance inference branches: `inference/tnr-0-<TS>`, `inference/tnr-1-<TS>`
- **Docs in repo (5/27 migration)**: this file + `docs/IMMEDIATE_CONTEXT.md`, `docs/MASTER_TODO.md`, `docs/STRATEGY_IDEAS.md`, `docs/SUBMISSION_REGISTRY.md`, `docs/DAY_2_SUBMISSION_QUEUE.md`

### Drive (folder "151B Competition", ID 14ntQe56m_ufIPyDk_Cs-sPjSESQ1NRZ8) -- REFERENCE ONLY POST-MIGRATION

- Back-Solve Ledger v3 -- 1bEfrvft7aMAJX6QrcQh1YxJxKTux1vNfKOkUXLobPcI
- Mathematical Framework -- 1Cs14P3H2eHKpe1Z0myqG1XikKMoqqIUxfRTbWQ5LDfM

## Cost discipline

- Cost numbers come ONLY from OpenAI Admin API or platform dashboard
- NEVER apply multipliers
- GPT-5.5 != GPT-5.5-xhigh -- always specify xhigh
- Thunder: NO `tnr stop` exists. Billing pause = snapshot+delete+restore via UI

## Anti-bias rules (locked, for Sheet v6)

1. SFT submissions trained on sheet labels = circular reasoning -- exclude OR cap weight 0.05 for untrained items only
2. Correlated submissions (same base model) -- dampen via weight/sqrt(N)
3. Leave-one-out cross-validation to estimate per-submission accuracy
4. Dialect-aware comparison: normalize both sides before agreement measurement

## Document maintenance rule (locked)

After every major decision, strategy move, results-in, gate pass/fail, or >30min elapsed:

1. STOP and update `docs/MASTER_TODO.md` + `docs/IMMEDIATE_CONTEXT.md` before continuing
2. Proactively add candidate TODOs unasked -- surface briefly "added to todo: X" and continue
3. ADHD-aware: every prompt-to-remember is friction
