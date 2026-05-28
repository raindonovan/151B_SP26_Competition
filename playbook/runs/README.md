# RUNS — Analysis structure

**Purpose**: Each completed inference/training run gets its own folder here with output, analysis, and decision.

## Folder structure per run

```
playbook/runs/<run_name>/
├── README.md         — what this run is, when it ran, who ran it
├── config.json       — exact config (model, sampling, prompts, etc.)
├── output.jsonl      — raw output (or pointer to results/ location if too big)
├── summary.json      — automated summary (accuracy, agreement, truncation, etc.)
├── analysis.md       — REQUIRED: human/Claude analysis of the run
├── decision.md       — REQUIRED: what we're doing with these results
```

## Discipline rule

**A run is NOT considered analyzed until `analysis.md` AND `decision.md` exist.**

If a run completes and we move on without writing these, that's a P0 failure — we likely waste the compute.

## Backlog — runs to analyze

| Run | Location | Status |
|---|---|---|
| GenSelect PoC r2 | `results/genselect_poc_r2_results.json` | UNANALYZED — see POSTMORTEMS.md P3 |
| GenSelect runner full | `results/genselect_runner.jsonl` | UNANALYZED |
| Hardest-30 SC=16 (tnr-A a2) | `results/hybrid/tnr-A/a2_serial_sc16_hardest30_*` | UNANALYZED |
| Hardest-30 SC=16 (Job 2) | `results/hybrid/tnr-A/sc16_hardest30_20260527T*` | UNANALYZED |
| NoThinking 943 | `results/hybrid/tnr-B/nothinking_full_943_20260527T000129Z.jsonl` | UNANALYZED |
| PACE | `results/pace/*` | UNANALYZED — need to read docs/PACE_METHODOLOGY.md |
| SFT v4 adaptive | `results/sft_v4_adaptive/*` | UNANALYZED — see POSTMORTEMS.md P1 |
| SFT v5 inference | inferred from sft_v5_checkpoint_comparison.json | UNANALYZED — see POSTMORTEMS.md P2 |
| OPL match | `results/opl_match/*` | PARTIALLY ANALYZED (this session) — needs formal analysis.md |
| no_box_rescue 2026-05-27 | `results/no_box_rescue_20260527T152423Z.jsonl` | INTEGRATED into Day 3 slots, formal analysis pending |

Goal: clear backlog by end of Day 4. Free information sitting unread is a waste of completed compute.
