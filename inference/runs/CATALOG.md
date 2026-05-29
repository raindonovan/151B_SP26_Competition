# inference/runs/CATALOG.md — Master rename + status index

> **Purpose**: single source of truth for every inference run we've done. As we work through them session-by-session (one run per session per Rain's Day-7 rule), this catalog gets the run's: old name → new name → status → key finding link.
>
> **Out of scope**: SFT TRAINING runs (those stay in `inference/adapters/`). This catalog is INFERENCE only (with-adapter or base-model), plus smoke tests.

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

## Status table (chronological, rough — order doesn't need to be perfect)

Legend: 🟢 done · 🟡 in progress · ⚪ untouched

| Old name | Proposed R# | Folder | Purpose (guess) | Status | Notes |
|---|---|---|---|---|---|
| `starter_results` | R00 | base_model | first attempt? | ⚪ | check if this is real run or stub |
| `run_vllm_smoke_5_tok2048` | R01 | base_model | smoke | ⚪ | 5 items, 2K tokens — earliest smoke |
| `run_vllm_smoke_5_tok8192` | R02 | base_model | smoke | ⚪ | 5 items, 8K tokens |
| `run03_tok8192_20` | R03 | base_model | smoke/eval | ⚪ | 20 items @ 8K |
| `run04_vllm_parity_20_tok8192` | R04 | base_model | vllm parity check | ⚪ | 20 items @ 8K |
| `run05_v1_50_tok16384` | R05 | base_model | eval | ⚪ | first 50-item run |
| `run06_v2mcq_50_tok16384` | R06 | base_model | eval | ⚪ | v2mcq variant |
| `run07_sc8_v1_50_tok16384` | R07 | base_model | eval | ⚪ | first SC8 run |
| `run08v2_v1_private943_tok16384` | R08 | base_model | eval | ⚪ | first p943 full eval |
| `run09sc8_v1_private943_tok16384` | R09 | base_model | eval | ⚪ | SC8 on p943, referenced in submission/ |
| `run10_v3perslot_private943_tok16384` | R10 | base_model | eval | ⚪ | v3perslot variant |
| `run11_v2openr1_50_tok16384` | R11 | base_model | eval | ⚪ | openr1 variant |
| `run13_v2openr1_50_rp110_dsmlp` | R13 | base_model | eval | ⚪ | rp1.10 ablation |
| `run14b_sc8_v1_private943_tok32k_pp1` | R14 | base_model | eval | ⚪ | **0.646 BEST inference baseline** |
| `run14b_sc8_v1_private943_tok32k_pp1_v3filtered` | R14b | base_model | eval | ⚪ | v3-filtered variant of R14 |
| `V0_baseline_fixed50_v1` | R??_baseline | base_model | baseline | ⚪ | early V0/V1/V2/V3/V4 series — chronology TBD |
| `V1_counting_top_fixed50_v1` | R??_counting | base_model | ablation | ⚪ | counting prompt variant |
| `V2_counting_bookend_fixed50_v1` | R?? | base_model | ablation | ⚪ | bookend prompt variant |
| `V3_shape_filter_fixed50_v1` | R?? | base_model | ablation | ⚪ | shape filter |
| `V4_temp_diversification_fixed50_v1` | R?? | base_model | ablation | ⚪ | multi-temp SC |
| `expA_run08_perslot_perturbed` | R?? | base_model | ablation | ⚪ | per-slot perturbation experiment |
| `genselect_poc_results.json` | R?? | base_model | poc | ⚪ | GenSelect proof-of-concept |
| `genselect_poc_r2_results.json` | R?? | base_model | poc | ⚪ | GenSelect r2 |
| `genselect_runner.jsonl` | R?? | base_model | poc | ⚪ | GenSelect runner output |
| `hybrid/` | R?? | base_model | ? | ⚪ | hybrid mode — needs inspection |
| `no_box_rescue_*` | R?? | base_model | rescue | ⚪ | post-hoc rescue attempts |
| `sft_v4_adaptive/` | R??_adapter_eval | adapter | sft_eval | ⚪ | adapter inference run for v4 |
| `sft_v5_checkpoint_comparison.json` | R?? | adapter | sft_eval | ⚪ | v5 checkpoint comparison |
| `slot1_wolfram_raw_responses` | R?? | (defer) | ? | ⚪ | wolfram-related, may belong in `data/search/wolfram/` not here |
| `smoke_openr1_v1_1k_5` | R?? | base_model | smoke | ⚪ | openr1 smoke |
| `tritonai_test_items` | R?? | base_model | ? | ⚪ | triton test items — investigate |
| `v2_numina_concise_50` | R?? | base_model | eval | ⚪ | numina-concise variant |

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

As R-numbers are assigned, log here to prevent reuse:

| R# | Assigned to | Date |
|---|---|---|
| _none yet_ | | |
