# Inference Run History — Narrative

> Author: claude_strategy · Date: 2026-05-31 (Day 9) · Audience: Rain + post-deadline research write-up
> Purpose: For every inference run we have artifacts for, explain what it was, what it tested, what we learned, current status. Companion to `CATALOG.md` (the dry rename table); this is the **prose** version.

---

## How to read this

Each entry has the same shape:
- **One-line ID** with R-number / new-name / date
- **What it was** — the actual config (model, mode, slice, sampling)
- **What it tested** — the hypothesis or purpose
- **Key result** — score on a relevant metric (with caveats — local audit score vs Kaggle vs slice)
- **Status / what we use it for now**

Glossary:
- **fixed50_v1** = 50-item slice of `data/public.jsonl` (17 MCQ + 33 free). Public set is LLM-synthesized with ~10% gold errors per JUDGER_AND_PUBLIC_SET.md — **directional only**, not absolute.
- **p943** = full private set (`data/private.jsonl`), 943 items. The actual competition slice. Kaggle scores on a fixed ~283-item subset of this.
- **SC@N** = self-consistency with N samples, majority vote on extracted answer.
- **Token cap notation**: `t8k` = max_new_tokens=8192; `t16k`=16384; `t32k`=32768; `t81k`=81920.
- **Audit score ≠ Kaggle**: Per CATALOG C6 reframe, `analyze_run.py`'s headline number is on the easier independent-gold subset; ~28pp local-vs-Kaggle gap. Use bucket labels (A / A_lucky / B / unknown) for capability signal.

---

# PART 1 — Smoke + dev iteration (R00–R07)

These predate the production cohort. They exist to validate the inference path, not to inform Pick B.

### R00 — `eval_v1_single_f20_t8k` (2026-04-?)
- **What it was**: First real call on the Qwen3-4B-Thinking-2507 base via vLLM. 20 items of fixed20 slice, single sample, max_new_tokens=8192, prompt v1-baseline.
- **What it tested**: Does the model + vLLM + extraction path work end-to-end on real eval data?
- **Result**: Development pass; no headline accuracy worth quoting (slice too small + 8K budget too tight).
- **Status**: Closed — pure infra validation.

### R01 — `starter_v1_single_f5_t8k`
- **What it was**: 5-item scaffolding using the course-provided starter notebook flow. Single sample.
- **What it tested**: Results-writing path — does our CSV land in the right schema?
- **Result**: Scaffolding only.
- **Status**: Closed.

### R02 — `smoke_v1_single_f5_t2k`
- **What it was**: 5 items at max_new_tokens=2048 — deliberately tight token budget.
- **What it tested**: How aggressive is truncation at a small budget? Bracketing the right token cap.
- **Result**: Heavy truncation as expected.
- **Status**: Closed (paired with R03 to triangulate budget).

### R03 — `smoke_v1_single_f5_t8k`
- **What it was**: R02's twin at max_new_tokens=8192 (4× larger).
- **What it tested**: Token-cap bracket. 2K (R02) vs 8K (R03). 8K worked for most items.
- **Result**: Confirmed 8K as the smoke budget; later production runs went to 16K and then 32K.
- **Status**: Closed.

### R04 — `parity_v1_single_f20_t8k`
- **What it was**: 20 items, vLLM serving path A/B check.
- **What it tested**: Are our outputs reproducible across vLLM versions/hardware?
- **Status**: Closed.

### R05 — `eval_v1_single_f50_t16k`
- **What it was**: First 50-item baseline at 16K tokens, single sample, v1-baseline prompt.
- **What it tested**: Establishes the 50-item dev-iteration loop config (the fixed50_v1 slice's grandparent).
- **Status**: Closed.

### R06 — `eval_v2mcq_single_f50_t16k`
- **What it was**: 50 items, MCQ-specific prompt variant (v2-mcq), single sample, 16K.
- **What it tested**: Does an MCQ-tailored prompt help MCQ accuracy specifically?
- **Result**: Inconclusive — slice too small to detect MCQ-specific effects. The v2-mcq prompt was abandoned in favor of v1-baseline going forward.
- **Status**: Closed — prompt variant not adopted.

### R07 — `eval_v1_sc8_f50_t16k`
- **What it was**: First SC@8 proof-of-concept. 50 items, v1-baseline, 16K, n_samples=8.
- **What it tested**: Does self-consistency at N=8 improve accuracy at fixed prompt/budget?
- **Result**: Directional SC lift on fixed50.
- **Status**: Closed — ancestor of R09 (the p943 SC@8 production run). R07 itself was dev-only (50 items not Pick-B-relevant).

---

# PART 2 — The production p943 cohort (R08–R10, R20, R20b)

These are the load-bearing runs that fed Pick A construction. All on private 943.

### R08 — `eval_v1_single_p943_t16k` (2026-05-04)
- **What it was**: First full private-set evaluation. 943 items, single sample, max_new_tokens=16384, v1-baseline prompt.
- **What it tested**: Establish baseline single-sample capability on the actual competition slice.
- **Result**: Local audit score (scored set n=498) = **0.8173**. Kaggle (post-processed) = **0.586** (REGISTRY #1). Hard_independent_CLEAN = 0.625 (passes 0.60-0.95 gate). A_lucky_sample = 0 (none possible without SC).
- **Status**: Cohort baseline. **Submission slot was 0.586**; the 28pp local-vs-Kaggle gap dates from this run.

### R09 — `eval_v1_sc8_p943_t16k` (2026-05-04→05)
- **What it was**: R08's SC twin — identical model, prompt, tokens, but **n_samples=8** (self-consistency).
- **What it tested**: Pure SC effect at fixed everything else.
- **Result**: Local 0.8474 (+3.0pp vs R08); Kaggle **0.614** (REGISTRY #4). 18 A_lucky_sample items (first observation of vote-fragility patterns). hard_independent_CLEAN 0.6875.
- **Status**: First SC-on-p943 evidence. Confirms SC helps but reveals A_lucky (vote loss): item 763 had 6/8 samples correct but the vote went the other way.

### R10 — `eval_v3perslot_single_p943_t16k` (2026-05-05)
- **What it was**: Single-sample, 16K, but with the **v3-perslot prompt** (multi-answer per-slot framing).
- **What it tested**: Pure prompt-variant effect (vs R08's v1-baseline).
- **Result**: Local 0.7952 (LOWEST of cohort); Kaggle **0.424** (REGISTRY #2 = worst p943 submission). hard_independent_CLEAN 0.75 (highest!).
- **Interpretation**: v3-perslot helps hard multi-part items (wolfram 6/7 vs R08's 3/7) but hurts the broad easy set. **Net negative.**
- **Status**: Confirmed dead lever for general Pick B. v3-perslot retired from production.
- **Note**: `strategy/INFERENCE_TECHNIQUES.md` L9 and `TEST_PIPELINE.md` L21 incorrectly listed R10 as "SC@8 → 0.646" — that's R14b/R20, not R10. R10 was single-sample at 0.424.

### R10b — `expA_run08_perslot_perturbed` (reserved, not deeply cataloged)
- **What it was**: R10 with sampling perturbation (different seed/randomness) on v3-perslot.
- **What it tested**: Is R10's poor performance due to bad luck or a real prompt-variant ceiling?
- **Status**: SHALLOW catalog only per POST_DEADLINE_AUDITS A3. Low priority (v3-perslot already confirmed dead).

### R20 — `eval_v1_sc8_p943_t32k_pp1` (2026-05-22) — THE PICK A FOUNDATION
- **What it was**: SC@8, v1-baseline, **max_new_tokens=32768** (2× R09), presence_penalty=1.0, repetition_penalty=1.0.
- **What it tested**: Token-budget effect (R09's structural sibling at 16K vs R20 at 32K).
- **Result**: Local **0.8554** (HIGHEST of cohort); Kaggle **0.646** (REGISTRY #4 cohort). hard_independent_CLEAN **0.8125** (best). A_lucky_sample = 14, including 3 DeepConf-territory items (≥5/8 lost vote: 296, 302, 839).
- **Trend**: R08 0.625 → R09 0.6875 → R10 0.75 → R20 **0.8125** on hard-independent. Both SC and tokens help the hard set.
- **Status**: **THE 0.646 best-inference baseline.** All Pick A submissions (0.745 = R20 + Opus + 5th teacher) are built off R20's response field. Locked.

### R20b — `eval_v1_sc8_p943_t32k_pp1_v3filt`
- **What it was**: R20's response samples filtered through the **v3 shape-filter** before voting. No new GPU run — post-processing layer that drops malformed samples and re-votes.
- **What it tested**: Does shape-filtering the SC samples improve the vote?
- **Result**: Local 0.8635 (+0.0081 vs R20); Kaggle **0.646** (REGISTRY #14, IDENTICAL to R20). 142 items had ≥1 sample rejected; 55 items had `voted_answer` change vs R20.
- **Interpretation**: The filter cleans up A_lucky→A on 4 items locally (consensus items that were vote-fragile in R20). On Kaggle, the filter is a **DEAD LEVER** — same 0.646. Audit T3 GREEN (no scored wrong→right flips).
- **Status**: Confirmed neutral. **Do not use R20b as a "second independent rescuer" in EV calculations** — it's R20-derivative with 96.18% pairwise agreement per T4 audit.

---

# PART 3 — SFT-merged failure era (R11–R14)

These four runs are all on **failed SFT v1 / v2 models** — pre-v3/v4/v5 era. Document them so the lesson sticks.

### R11 — `smoke_openr1_v1_1k_5` (reserved)
- **What it was**: 5-item smoke of the OpenR1 v1 1K-trace SFT adapter.
- **What it tested**: Does the adapter even produce coherent output?
- **Result**: Confirmed adapter loads; output catastrophic (no `\boxed{}` mostly).
- **Status**: Confirmed v1 SFT failed. Adapter archived. See `inference/adapters/sft_v1_postmortem/`.

### R12 — `v2_numina_concise_50` (reserved)
- **What it was**: 50 items with the **Numina-concise v2 SFT adapter** (different training set).
- **What it tested**: Does a Numina-concise SFT recover capability?
- **Result**: Also failed. Adapter abandoned.
- **Status**: Closed — confirmed dead.

### R13 — `run11_v2openr1_50_tok16384` (reserved) — RAMBLE DIAGNOSIS
- **What it was**: 50 items, **OpenR1 v2 SFT merged with Qwen3-4B-Thinking-2507**, single sample, 16K tokens, **repetition_penalty=1.0** (default), v1-baseline prompt.
- **What it tested**: Does the OpenR1-v2-16K SFT adapter (sister to R11) work when MERGED into base weights?
- **Result**: **Catastrophe.** 7/50 = 0.14 overall. 0/17 MCQ (all wrong). 30/50 items had `missing_boxed=True` — the model **rambled without ever producing `\boxed{}`**. Avg gen tokens 9308 (near 16K cap, 5 cutoffs).
- **Root cause**: OpenR1-Math-220k traces were truncated at max_seq_length=4096 during SFT training. Model learned to ramble without ever closing out the answer. See `inference/adapters/UNTRACKED_OPENR1_V2.md`.
- **Status**: Closed. Lever (repetition_penalty=1.0 on broken SFT) confirmed broken.

### R14 — `run13_v2openr1_50_rp110_dsmlp` (reserved) — REP-PENALTY RESCUE
- **What it was**: R13's twin with **repetition_penalty=1.1** (the only delta). Same OpenR1-v2-16K merged model, same fixed50, 16K cap, v1-baseline prompt, single sample.
- **What it tested**: Does rep_penalty=1.1 break the model out of the rambling loop?

**R14 AUDIT FINDINGS (this session, Day 9):**

Headline comparison **R13 (rep_penalty=1.0) → R14 (rep_penalty=1.1)** on same OpenR1-v2 merged model, same fixed50:

| Metric | R13 (rp=1.0) | R14 (rp=1.1) | Δ |
|---|---|---|---|
| Overall accuracy | 7/50 = **0.14** | 24/50 = **0.48** | **+0.34** |
| MCQ accuracy | 0/17 = **0.00** | 13/17 = **0.76** | **+0.76** |
| Free accuracy | 7/33 = 0.21 | 11/33 = 0.33 | +0.12 |
| missing_boxed | 30/50 (60%) | 1/50 (2%) | **−58pp** |
| cutoffs | 5 | 1 | −4 |
| avg_gen_tokens | 9308 | 3600 | **−61%** |
| gen_tokens p50 | 13973 | 1907 | −86% |

- **rep_penalty=1.1 dramatically rescued the rambling failure mode.** Boxed-answer rate went from 40% to 98%; MCQ accuracy from 0% to 76%.
- avg_gen_tokens collapsed from 9308 to 3600 — the model stopped looping and produced concise answers.
- **BUT**: this is on a **failed SFT model**, not the base Qwen3-Thinking. The lever rescues a *broken* model; it's not a free improvement on the working base.
- **Caveat for base Qwen3-4B-Thinking-2507**: Sun et al. (paper referenced in research priors) recommends `presence_penalty>0` and `repetition_penalty=1.0` for this model. Adding rep_penalty=1.1 on the base would likely HURT (the working model has no rambling problem to fix). We have no R14-on-base-model data; do not generalize.

**Status**: **CLOSED.** R14 is a useful lesson for "if SFT model rambles, try rep_penalty=1.1 as rescue" but is not a Pick B lever for tonight (we're using R20's base-Qwen SC@8, which doesn't have the failure mode). No new marginal IDs.

---

# PART 4 — V-series prompt + filter ablations (R15–R19)

Audited fully in `V_series_audit/AUDIT_SUMMARY.md`. Brief recap:

### R15 = V0_baseline_fixed50_v1
- **What it was**: SC@8 baseline on fixed50, v1-prompt, all default params (temp=0.6, top_p=0.95, top_k=20, presence_penalty=1.0, repetition_penalty=1.0, n_samples=8, max_new_tokens=32768).
- **Result**: 0.700 overall, agreement quantiles 0.625 / 1.0 / 1.0.
- **Status**: Reference point for V1-V4. CLOSED.

### R16 = V1_counting_top_fixed50_v1
- **What it was**: V0 with prompt v2-counting-top (counting hint at top of prompt). Tokens halved to 16K.
- **What it tested**: Does prefacing with counting/structure hint change vote stability or accuracy?
- **Result**: 0.720 (+1 item vs V0). n_voted_changed_call 7→10 (more vote swings). No oracle gain.
- **Status**: Prompt-engineering moves vote winners around without unlocking new capability. CLOSED.

### R17 = V2_counting_bookend_fixed50_v1
- **What it was**: V1's twin with counting hint at TOP AND BOTTOM of prompt.
- **Result**: 0.720 (+1 vs V0). MCQ 14/17 (DROP from V0's 15/17), Free 22/33 (UP from V0's 20/33). cutoffs_per_sample 8→16.
- **Status**: Redistribution across MCQ/Free, no net gain. CLOSED.

### R18 = V3_shape_filter_fixed50_v1
- **What it was**: V2's prompt with **shape filter** active at inference time (rejects malformed samples before vote).
- **What it tested**: Does in-inference shape filtering improve vote outcome?
- **Result**: 0.720. **Lowest unanimity (22) and p50 agreement (0.875)** — filter creates vote fragility but no oracle rescue.
- **Status**: Shape filter creates fragility, doesn't create rescues — fragmented samples are correlated-wrong. CLOSED.

### R19 = V4_temp_diversification_fixed50_v1 — **ABORTED**
- **What it was**: Intended V4 with temperature-schedule diversification across SC samples.
- **Result**: PARTIAL_PRE_TAGGING has 8 items, final jsonl has 5 (ids 29, 48, 53, 54, 56). No summary.json.
- **Status**: **INSUFFICIENT DATA**. Run aborted before completion. Restart post-deadline for research write-up if useful.

**V-series net for Pick B**: No marginal private-set IDs (public ↔ private ID space disjoint). Category signal (multi-slot / no-box / fragmentation) confirms normalizer's chosen scope. All five CLOSED.

---

# PART 5 — NoThinking probes (NT_*)

NoThinking mode = prefill `</think>` bypass to skip the reasoning phase. Orthogonal-mode signal for ensemble diversity.

### NT_eval_nothinking_sc8_p943_t8k (`nothinking_full_943_20260527`) — THE 943-NT REFERENCE
- **What it was**: Full 943 private set, **NoThinking mode**, SC@8, max_new_tokens=8192 (NT outputs are short, no reasoning needed). 2026-05-27.
- **What it tested**: Standalone NoThinking capability + ensemble-diversity signal for Pick B join.
- **Result**: Audit scored set acc=0.7289 (vs R20's 0.8554 — NT is materially WEAKER alone). **BUT**: A_lucky_sample = **66** items (vs R20's 14) — NoThinking is high-variance/high-diversity. **Cross-run vs R20: NT rescues 49 items R20 missed, of which 26 are NT-ONLY (no Thinking corroboration).** Load-bearing for Pick B.
- **Status**: Pick B foundation. The Conservative-13 NT-join (slots 1+2) selects 13 high-confidence NT-only rescues to overlay R20. All 13 verified in T4 matrix audit.

### NT_probe98_eval_nothinking_sc8_f98_t8k (`nothinking_probe98_20260526`) — T2 variance check
- **What it was**: 98-item probe of NoThinking, paired vs the same 98 items in NT-943.
- **What it tested**: Is the NT-943 run a stable mirror of NT-probe behavior? Variance check.
- **Result**: Scored 0.6136 on probe vs NT-943's behavior on same 98 items shows divergence. T2 audit YELLOW: lineage confirmed but **not a stable mirror** — bucket distribution differs materially. shape_fallback fired on 46/98 (47%, very high).
- **Status**: NT mode is **MIXED/NOISY** — down-weight in slot 7/8 EV.

### NT_targeted_rescue_nothinking_sc16_f61_t8k (`targeted_rescue_nothinking_20260526`)
- **What it was**: 61 curated R20-failure items, NoThinking, **SC@16** (double the SC width).
- **What it tested**: Does higher SC width on NoThinking rescue R20 failures?
- **Result**: 7/36 = 0.19 scored (deliberately hard slice; 43/61 are T5). **NEW UNIQUE rescues vs R20 ∪ NT-943: 1 item (232). tr WORSE than NT-943 on 6 items. Net = +1 − 6 = −5.** Stacking would HARM.
- **Status**: Closed Day 9 (T2 audit). **Do not stack on Pick B.** Stochastic variance, not capability.

---

# PART 6 — Thinking-mode probes (TH_*)

### TH_targeted_rescue_thinking_sc16_f61 (`targeted_rescue_20260526`) — Thinking twin of the NT 61-item rescue
- **What it was**: Same 61 R20-failure items as NT_targeted_rescue, but **Thinking mode** (no prefill bypass), SC@16, max_new_tokens=24576 (thinking budget). Mean output 6102 tokens.
- **What it tested**: NoThinking-vs-Thinking head-to-head on hard items.
- **Result**: Scored **13/36 (vs NT-twin's 7/36) — Thinking wins** on this hard slice. **NEW UNIQUE rescues vs R20 ∪ NT-943: 4 items (9, 435, 479, 638), all on INDEPENDENT gold.**
- **Interpretation**: On hard multi-slot/precision items, **long Thinking budget outperforms NoThinking**. This is the REVERSE of the full-943 picture, where NT added orthogonal solves on easier items.
- **Status**: T3 audit GREEN (Day 9). The 4 rescues feed into slot 7/8 high-budget-Thinking Pick B candidates.

### tnr-0 + tnr-1 — Day 9 in-flight Thunder runs
- **What it is**: Two Thunder A100 boxes running Thinking SC@16 with max_new_tokens=81920 / thinking_budget=65536 on a **118-item target set** (`thinking_probe_target_set.csv`).
- **What it tests**: Higher thinking budget on the broader 118-item R20-failure pool. Best-case ceiling: +56 measurable items (target's independent-gold subset).
- **Status**: IN FLIGHT as of this writing. Outputs not yet committed. ETA ~13:42 UTC. Will populate `in_thunder` column in `pickb_marginal_accounting.csv` when they land.

---

# PART 7 — Adapters (SFT runs, not inference per se, but listed for completeness)

### sft_v1_postmortem (2026-05-06)
3-arm SFT v1 experiment, all 3 arms failed: rambling without `\boxed{}`. The OpenR1-v1 1K and OpenR1-v2-16K adapters from this era show up in R11/R13/R14. Lesson: max_seq_length=4096 truncation kills R1-style training.

### sft_v3, sft_v4
Documented in `inference/adapters/sft_v{3,4}/`. v3 superseded by v4; v4 superseded by v5. Both archival.

### sft_v5 — ACTIVE
The current 8-item adapter (QLoRA, ckpt-1176, 505MB LFS). Trained on a small curated SFT set. NOT MERGED — kept as adapter per locked rule. Status: trained, not currently in any submission stack pending value-equality re-vote rescue analysis (per Cursor meta-audit recommendation: "UNLOCK conditional: adapter seed should be reopened only if value-equality re-vote flips any seed member from persistent miss to vote artifact").

### selection/genselect_poc — DEFERRED
GenSelect proof-of-concept failed because candidate inputs were truncated to ~500 chars (not a Qwen capability issue). "Qwen is bad at self-verification" is an UNVALIDATED conclusion. Per A5 in POST_DEADLINE_AUDITS: fix candidate window, re-run post-deadline.

---

# PART 8 — What this all means for tonight (TLDR)

The cohort tells one story:

1. **R20 (SC@8, v1-baseline, 32K) is the inference ceiling for Pick A** at 0.646. Pick A locked at 0.745 = R20 + Opus overlay + 5th teacher.
2. **NT-943 contributes 49 distinct rescues** vs R20, of which 26 are NT-only and 13 are the Conservative-13 NT-join (Pick B slots 1+2 foundation).
3. **TH-twin contributes 4 distinct rescues** beyond R20 ∪ NT-943, all independent-gold. Slot 7/8 candidate.
4. **R20b is a derivative** (96% R20-agreement). Do not treat as independent rescuer.
5. **Prompt variants (V-series) don't unlock new capability** — they shuffle vote winners. No new private-set IDs.
6. **rep_penalty=1.1 (R14) rescues failed SFT** but doesn't apply to base Qwen.
7. **NoThinking targeted_rescue** stacks NEGATIVE on top of NT-943.
8. **The remaining Day-9 levers are post-inference**: Tier-1 normalizer (structural fixes), value-equality re-vote (vote-aggregation), and Thunder tnr-0/tnr-1 (in-flight, 118-item attempt).

**No new inference experiments tonight.** Execute queued workstreams, integrate, synthesize Pick B candidates via `pickb_marginal_accounting.csv`.

---

# Cross-references
- `CATALOG.md` — dry rename + status table (this doc's complement)
- `CROSS_RUN_MATRIX.csv` — per-item correctness across R08/R09/R10/R20/R20b/NT
- `V_series_audit/AUDIT_SUMMARY.md` — V0-V4 deep cut
- `../base_model/{run}/findings.md` — per-run findings (cataloged subset)
- `../../submission/csvs/picks/pickb_marginal_accounting.csv` — dedup table for Pick B construction
- `../../submission/TEXAS_OIL_FINDINGS.md` — texas-oil submission lever evidence
- `../../strategy/SESSION_HANDOFF.md` — Day-8-close handoff
