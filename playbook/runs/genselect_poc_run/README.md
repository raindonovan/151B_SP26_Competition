# RUN: GenSelect PoC

**Type**: Inference-time selection (Best-of-N via second-pass LLM-as-judge)
**Date**: ~2026-05-26
**Owner**: tnr-0 (inference), claude_strategy (analysis)
**Status**: Output exists, partial analysis done, formal analysis pending in `findings.md`

## What this was

NVIDIA's AIMO-2 1st-place technique (GenSelect): generate N candidate solutions to a problem, then have a model read all N and pick the best one. Better than majority voting on math problems in their hands.

Our implementation:
- 8 SC candidates per item from run14b
- Each candidate assembled into a "judge" prompt
- Qwen runs second pass: "you are given a problem and 8 solutions, pick the best one"
- Selected answer extracted and written to submission

## Artifacts

- `results/genselect_poc_results.json` (141KB) — phase 1 PoC
- `results/genselect_poc_r2_results.json` (238KB) — phase 2 retry
- `results/genselect_runner.jsonl` (1.6MB) — full runner output
- `scripts/genselect_poc.py`, `scripts/genselect_phase2.py`, `scripts/genselect_runner.py`, `scripts/genselect_smoke.py`

## See also

- `findings.md` — what went wrong, what we learned
