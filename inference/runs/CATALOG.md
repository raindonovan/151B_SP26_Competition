# inference/runs/CATALOG.md — Master rename + status index

> **Purpose**: single source of truth for every inference run we've done. As we work through them session-by-session (one run per session per Rain's Day-7 rule), this catalog gets the run's: old name → new name → status → key finding link.
>
> **Out of scope**: SFT TRAINING runs (those stay in `inference/adapters/`). This catalog is INFERENCE only (with-adapter or base-model), plus smoke tests.
>
> **AUDIT-SCORE REFRAME (C6, Day 9)**: `analyze_run.py`'s audit score is for per-item bucket labels (A / A_lucky_sample / B / unknown). It is NOT a Kaggle-mirror. The local judger has a known ~28pp gap, and the restricted independent-gold subset (wolfram_HIGH / search_GOLD / unanimous_teachers) is systematically easier than the full LB slice. Read bucket labels and per-source accuracy, not the headline rate, as a Kaggle predictor.

## Naming convention

```
R{NN}_{purpose}_{variant}_{decoding}_{items}_{tokens}/
```

See `inference/adapter/README.md` or `inference/base_model/README.md` for full field definitions.

## Per-session workflow

Each session catalogs ONE run. Rough sequence:

1. Pick next un-cataloged run from the table below (earliest first).
2. Read everything related: the jsonl, summary.json, any analysis docs that reference it (use the cross-ref list at the bottom).
3. Determine which folder it belongs in (`adapter/` or `base_model/`).
4. Propose new name per the convention. Verify no R-number collision in this catalog.
5. Create the per-run folder under the right home (`inference/{adapter|base_model}/R{NN}_.../`).
6. Move artifacts (jsonl, summary, logs, scripts copy) into the folder via `git mv` (preserves LFS pointers).
7. Write per-run `README.md` + `findings.md` (+ `decision.md` if applicable).
8. Update ALL cross-references across the repo (see grep list at bottom).
9. Mark status DONE in the table below.
10. Commit + push.
11. End session. Next session takes the next run.

## Status table (chronological by RUN TIMESTAMP — `summary.json.started_at` where available, git first-commit as fallback)

Legend: 🟢 done · 🟡 in progress · ⚪ untouched

**Locked chronology** (Day 9 2026-05-30). Numeric `runXX` filename convention was NOT applied chronologically: run09 ran BEFORE run10; run12 never existed; "run13" is in fact the 14th run; V-series is mid-development, not earliest; run14b ran 2026-05-22 (the May 27 commit was the LFS-track, not the run).

| Old name | R# | Folder | Run timestamp (UTC) | Purpose | Status | Notes |
|---|---|---|---|---|---|---|
| `run03_tok8192_20` | R00 | base_model | 2026-05-01 21:22 | eval | ⚪ | 20 items @ 8K — earliest run on record (git-log fallback; no summary.json) |
| `starter_results` | R01 | base_model | 2026-05-01 21:25 | starter | ⚪ | initial scaffold output, ~3 min after R00 (git-log fallback) |
| `run_vllm_smoke_5_tok2048` | R02 | base_model | 2026-05-03 02:17 | smoke | ⚪ | 5 items, 2K tokens — same commit as R03 (git-log fallback) |
| `run_vllm_smoke_5_tok8192` | R03 | base_model | 2026-05-03 02:17 | smoke | ⚪ | 5 items, 8K tokens |
| `run04_vllm_parity_20_tok8192` | R04 | base_model | 2026-05-03 02:31 | parity | ⚪ | 20 items @ 8K, vLLM parity check |
| `run05_v1_50_tok16384` | R05 | base_model | 2026-05-03 16:53 | eval | ⚪ | first 50-item run |
| `run06_v2mcq_50_tok16384` | R06 | base_model | 2026-05-03 17:16 | eval | ⚪ | v2mcq variant |
| `run07_sc8_v1_50_tok16384` | R07 | base_model | 2026-05-03 19:23 | eval | ⚪ | first SC8 run |
| `run08v2_v1_private943_tok16384` | R08 | base_model | 2026-05-04 05:49 | eval | ⚪ | first p943 full eval (single-sample) |
| `run09sc8_v1_private943_tok16384` | R09 | base_model | 2026-05-04 17:32 | eval | ⚪ | SC8 on p943 (referenced widely in submission/) |
| `run10_v3perslot_private943_tok16384` | R10 | base_model | 2026-05-05 19:55 | eval | ⚪ | v3perslot variant, single-sample p943 (git-log fallback) |
| `expA_run08_perslot_perturbed` | R10b | base_model | 2026-05-05 19:55 | ablation | ⚪ | perslot perturbation, ran alongside R10 |
| `smoke_openr1_v1_1k_5` | R11 | base_model | 2026-05-07 00:23 | smoke | ⚪ | openr1 prompt smoke |
| `v2_numina_concise_50` | R12 | base_model | 2026-05-09 17:30 | eval | ⚪ | numina-concise variant |
| `run11_v2openr1_50_tok16384` | R13 | base_model | 2026-05-10 18:12 | eval | ⚪ | openr1 variant |
| `run13_v2openr1_50_rp110_dsmlp` | R14 | base_model | 2026-05-11 17:27 | ablation | ⚪ | rp1.10 ablation (run12 never existed in this repo) |
| `V0_baseline_fixed50_v1` | R15 | base_model | 2026-05-12 15:50 | baseline | ⚪ | V-series prompt-engineering ablations begin here |
| `V1_counting_top_fixed50_v1` | R16 | base_model | 2026-05-13 11:42 | ablation | ⚪ | counting prompt variant |
| `V2_counting_bookend_fixed50_v1` | R17 | base_model | 2026-05-13 11:43 | ablation | ⚪ | bookend prompt variant |
| `V3_shape_filter_fixed50_v1` | R18 | base_model | 2026-05-13 20:24 | ablation | ⚪ | shape filter |
| `V4_temp_diversification_fixed50_v1` | R19 | base_model | 2026-05-13 23:37 | ablation | ⚪ | multi-temp SC (git-log fallback — no summary.json) |
| `run14b_sc8_v1_private943_tok32k_pp1` | **R20** | base_model | **2026-05-22 13:56** | eval | ⚪ | **0.646 BEST inference baseline**; feeds 0.745 with overlays |
| `run14b_sc8_v1_private943_tok32k_pp1_v3filtered` | R20b | base_model | 2026-05-22 (derived) | eval | ⚪ | v3-filtered variant of R20 |

**Pick-B-relevant p943 cohort**: R08, R09, R10, R20, R20b. These are the only full-private runs and the only candidates that move tonight's Pick B via cross-run consensus.

**Deferred** (R# assigned when cataloged; not in the strict chronological loop):

| Old name | Folder | Notes |
|---|---|---|
| `genselect_poc_results.json` | base_model | GenSelect proof-of-concept |
| `genselect_poc_r2_results.json` | base_model | GenSelect r2 |
| `genselect_runner.jsonl` | base_model | GenSelect runner output |
| `hybrid/` | base_model | hybrid mode — inspect contents first |
| `no_box_rescue_*` | base_model | post-hoc rescue attempts |
| `sft_v4_adaptive/` | adapter | adapter inference run for v4 |
| `sft_v5_checkpoint_comparison.json` | adapter | v5 checkpoint comparison |
| `tritonai_test_items` | base_model | triton test items — investigate |
| `slot1_wolfram_raw_responses` | (TBD — likely `data/search/wolfram/`) | wolfram-related, may not belong here |

## Run artifacts to absorb during catalog work

These artifacts live OUTSIDE `inference/` but belong to specific runs. As each run is cataloged, move (or link + reference) them into the run folder:

- `infrastructure/logs/run14b_sc8_v1_private943_tok32k_pp1.log` → goes with R14
- `submission/csvs/run14b_sc8_v1.csv` → submission derived from R14, leave in submission/ but link both ways
- `submission/csvs/run09sc8_probe_b_reversed.csv` → derived from R09
- `submission/csvs/run09sc8_format_fixed.csv` → derived from R09
- `submission/csvs/run09sc8_v1_private943.csv` → derived from R09
- `data/candidates_nothinking_breakdown.md` + `data/candidates_nothinking_98.txt` → analysis OF a NoThinking inference run (need to identify which run)
- `data/candidates_sc16_hardest30_breakdown.md` → analysis of an SC16 hardest-30 run
- `data/candidates_pertier_breakdown.md` → cross-run analysis

## Cross-reference list (27 docs reference inference runs)

Whenever a run is renamed, sweep these docs for the old name and replace:

```
README.md
agents/CLAUDE_STRATEGY.md
agents/CLAUDE_VSCODE.md
data/ANSWER_SHEET_SCHEMA.md
data/FINDINGS.md
data/candidates_nothinking_breakdown.md
data/candidates_pertier_breakdown.md
data/candidates_sc16_hardest30_breakdown.md
data/search/README.md
infrastructure/pre_flight/audit_report.md
infrastructure/pre_flight/production_commands.md
postprocessing/results/slot1_minimal_report.md
postprocessing/results/slotA_report.md
strategy/FINDINGS.md
strategy/HOW_WE_KNOW_CORRECTNESS.md
strategy/INFERENCE_TECHNIQUES.md
strategy/LEVERS.md
strategy/RESEARCH.md
strategy/SESSION_HANDOFF.md
strategy/TEST_PIPELINE.md
strategy/TIME_MACHINE_BACKLOG.md
strategy/TODO.md
submission/AMBER_ALERT.md
submission/RED_ALERT_LB_SUBSET.md
submission/REGISTRY.md
```

Use this as the canonical sweep list per run. Don't expand it without checking with Rain — it was derived from a `grep -rln` on Day 7.

## R-number registry (collision prevention)

R-numbers are RESERVED at chronology-lock time and become CATALOGED when their per-run folder lands. Status="reserved" means R# is taken but the per-run folder hasn't been built yet (run still ⚪ in status table above).

| R# | Assigned to | Status |
|---|---|---|
| R00 | run03_tok8192_20 | reserved |
| R01 | starter_results | reserved |
| R02 | run_vllm_smoke_5_tok2048 | reserved |
| R03 | run_vllm_smoke_5_tok8192 | reserved |
| R04 | run04_vllm_parity_20_tok8192 | reserved |
| R05 | run05_v1_50_tok16384 | reserved |
| R06 | run06_v2mcq_50_tok16384 | reserved |
| R07 | run07_sc8_v1_50_tok16384 | reserved |
| R08 | run08v2_v1_private943_tok16384 | reserved |
| R09 | run09sc8_v1_private943_tok16384 | reserved |
| R10 | run10_v3perslot_private943_tok16384 | reserved |
| R10b | expA_run08_perslot_perturbed | reserved |
| R11 | smoke_openr1_v1_1k_5 | reserved |
| R12 | v2_numina_concise_50 | reserved |
| R13 | run11_v2openr1_50_tok16384 | reserved |
| R14 | run13_v2openr1_50_rp110_dsmlp | reserved |
| R15 | V0_baseline_fixed50_v1 | reserved |
| R16 | V1_counting_top_fixed50_v1 | reserved |
| R17 | V2_counting_bookend_fixed50_v1 | reserved |
| R18 | V3_shape_filter_fixed50_v1 | reserved |
| R19 | V4_temp_diversification_fixed50_v1 | reserved |
| R20 | run14b_sc8_v1_private943_tok32k_pp1 | reserved |
| R20b | run14b_sc8_v1_private943_tok32k_pp1_v3filtered | reserved |
