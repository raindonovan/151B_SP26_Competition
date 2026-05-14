# Active Plan: V4 → run14b → run14c → decision
Locked: 2026-05-13.
Authority: claude_strategy (Rain's planning agent).
Status: Active. Supersedes ad-hoc decisions in chat transcripts.
This doc is the source of truth for what runs next. Phase-by-phase. Future agent sessions should read this before proposing changes.

## Terminology

- **public** = `data/public.jsonl`, 1126 items with embedded answer field. Retired as eval surface (~10% gold errors, instructor-confirmed).
- **private_kaggle** = scoring via CSV submission to Kaggle. Uses `private.jsonl` at repo root (943 items, no answer field). Returns single aggregate score. Only valid measurement until dataClean lands.
- **private_local** = scoring against pseudo-gold from dataClean app (3-teacher consensus, 943 items). Doesn't exist yet; gated on Phase 5.

Both private scores use the same inference run as input. Difference is scoring path, not inference.

## Phase 1 — V4 (tagged) on public
**Status:** Pending V4 restart with per-sample temperature tagging.
V4 was launched on `fixed_50_v1` slice without temperature tagging on individual samples. Restarted with tagging so we can post-hoc analyze which temperature rungs contributed which votes.
- **Output:** `results/V4_temp_diversification_fixed50_v1.jsonl` (50 items, each sample now carries a `temperature` field).
- **Goal:** Confirm V4 is operational and not producing degenerate output. Enable per-temperature analysis.
- **Decision rule:** V4's public score does NOT gate Phase 2. Run14b launches regardless of V4 outcome.
- **Walltime considerations:** V4 wall time is ~5x V0-V3 per item due to 4 sequential `generate()` calls + high-temperature samples generating longer reasoning. Expect 2-3 pods to complete (with resume between).

## Phase 2 — run14b on private_kaggle (baseline anchor)
**Config:**

| Param | Value |
|---|---|
| Variant | V0_baseline (from `scripts/variants.py`) |
| Prompt | v1-baseline (byte-identical to Run 09) |
| SC | N=8, single temperature |
| max_new_tokens | 32768 |
| max_model_len | 36864 (= max_new_tokens + 4096) |
| temperature | 0.6 |
| top_p | 0.95 |
| top_k | 20 |
| presence_penalty | 1.0 |
| repetition_penalty | 1.0 |
| Input | `--data-path private.jsonl` (at repo root, NOT `data/private.jsonl`) |
| Output | `results/run14b_sc8_v1_private943_tok32k_pp1.jsonl` |
| gpu_memory_utilization | 0.85 (script default; raise to 0.92 by editing run_vllm_sc.py if smoke shows preemption) |

**Pod preference:** A30 if available. Blackwell MIG slice acceptable; smoke first.

**Smoke gate:** Launch on first 5-10 items. If preemption rate >50/item or wall time >5min/item, drop `max_new_tokens` to 24k and re-smoke. If still failing, drop to 16k (Run 09 config).

**Walltime estimate:** 30-40 hours across 5-7 pods (incremental writes + resume mandatory).

Then: Convert JSONL → CSV (`scripts/to_submission_csv.py` or equivalent), submit to Kaggle, record `private_kaggle` score in `experiments.md`.

**Expected:** 0.62-0.66 (Run 09 baseline is 0.614 at 16k tokens; bump to 32k + presence_penalty=1.0 should rescue most of Run 09's 68 no-box items).

**Purpose:** Clean baseline score on Kaggle under the new V0 defaults. Anchor for Phase 3 comparison.

## Phase 3 — run14c on private_kaggle (bundled prompt-engineering stack)
**Config:** Bundle every V0-V4 lever simultaneously:

- v1-baseline prompt (base)
- V1's counting-top user prefix for multi-answer items
- V2's bookend suffix for multi-answer items
- V3's shape filter on SC vote pool
- V4's temperature ladder [0.5, 0.7, 0.9, 1.1] (2 samples per temp, 8 total via SC ladder)
- Everything else matches run14b (32k tokens, presence_penalty=1.0)

**Output:** `results/run14c_bundled_sc8_private943.jsonl`

**Walltime estimate:** 50-70 hours (V4 batching overhead applies, total may exceed run14b by ~50%).

Then: Convert to CSV, submit to Kaggle, record score in `experiments.md`.

**Purpose:** Test whether the V0-V4 prompt-engineering levers compound when stacked.

**Acknowledged limitation:** Non-scientific. Single bundled comparison loses attribution (we won't know which lever did the work) but gains signal at n=943 (public n=50 was too noisy for compound effects to be visible).

## Phase 4 — Decision
Compare run14b vs run14c `private_kaggle` scores:

| Outcome | Interpretation | Action |
|---|---|---|
| 14c > 14b by ≥2pp | Levers compound | Ship 14c. Pivot to dataClean+SFT for next gains. |
| 14c ≈ 14b (±2pp) | Levers neutral when stacked | Ship 14b. Commit hard to dataClean+SFT. |
| 14c < 14b by ≥2pp | Levers interfere when stacked | Ship 14b. Commit hard to dataClean+SFT. |

Whichever wins becomes the active inference-time submission. Final selection (which 2 of all submissions to mark as "official Kaggle picks") happens later, not now.

## Phase 5 — dataClean app build (parallel, async)
Independent of Phases 1-4. Can start at any time, including before Phase 2 launches.

**Reference docs:**
- `dataClean_CLAUDE.md` (working agreements for the dataClean repo)
- `dataClean_SETUP.md` (bootstrap + implementation prompt for claude_vscode)
- `DESIGN_dataset_pipeline.md` (architecture, API config, cost budget, prompts, consensus logic)

**Output:** Per the design doc — 943 items × 3-teacher consensus → pseudo-gold + best reasoning trace per item.

**Cost:** ~$30-50 in API calls (per DESIGN.md §5).

**Unlocks:**
- Order audit on Run 09 (Phase 7)
- `private_local` scoring for any future run
- SFT training data for Phase 6

## Phase 6 — SFT v3 (conditional)
**Gated on:** Phase 4 decision + Phase 5 completion.

**Strategy:** Train QLoRA on dataClean pseudo-gold traces.

**Configs to try, in order:**
1. Overfit-encouraged: r=64, weight_decay=0, more epochs (per memory edit #2, Piazza-confirmed allowed)
2. Standard: r=32, weight_decay=0.01 (if time permits)

Compare both on `private_kaggle`.

Then: Merge adapter to BF16, swap into vLLM, inference on `private.jsonl`, submit.

**Expected:** Highest-variance lever in the project. v1 SFT failed (truncation + masked labels). v2 NuminaMath was wrong data category. v3 uses dataClean's curated traces — first attempt with verified-correct teacher signal.

**Target:** +5pp over best inference-time score (whichever of 14b or 14c wins Phase 4).

## Phase 7 — Order audit (post-dataClean)
Once dataClean pseudo-gold exists:
- Compare Run 09's multi-answer item answer order vs pseudo-gold order
- Count items with correct values but wrong order
- Quantifies free points available from order-fixing alone (memory edit #3)
- Applies retroactively to run14b and run14c outputs (same input, same model behavior)

If order audit shows ≥10 items had right values but wrong order, the prompt update for inference-time order-correctness becomes an explicit next experiment.

## NOT in this plan (deliberately deferred)

- SC=16 experiments. Per literature: diminishing returns vs SFT upside. Cost: 2x. Marginal: +1-2pp expected. Worse expected value than dataClean+SFT.
- 64k token budget. Memory pressure on DSMLP, marginal gain (rescues id=1040-class hard items only).
- Confidence-aware abstention (DESIGN.md §6.1). Backlog.
- run14a (pure Run 09 replication). Skip unless run14b lands suspiciously low. Use to diagnose DSMLP-vs-RunPod stack drift only if needed.
- Repeated independent prompt-engineering ablations. V0-V4 confirmed the prompt-engineering ceiling at n=50. Don't go around this loop again.

## Hard constraints (carry-forward)

- **Token budget rule:** `max_model_len = max_new_tokens + 4096` (never set equal)
- **Locked sampling:** `temperature=0.6, top_p=0.95, top_k=20, min_p=0, rep_pen=1.0` (V4 deviates with temperature ladder)
- **judger.py is NOT used for accuracy decisions.** Only Kaggle is truth until dataClean produces pseudo-gold.
- **Public set retired as eval surface** (~10% gold errors).
- **Submission slots are not scarce** (3/day, repeatedly confirmed).
- **DSMLP walltime is 6 hours per pod.** Incremental writes + resume mandatory for any long run.
- **`private.jsonl` lives at repo root, NOT `data/private.jsonl`.** Always pass `--data-path private.jsonl`.

## Revisions

- 2026-05-13: Plan locked.
