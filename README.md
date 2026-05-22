# CSE 151B Spring 2026 — Math Reasoning Competition

This repo contains the code, experiments, and submissions for the UCSD CSE 151B
Spring 2026 Kaggle competition: improving mathematical reasoning of
`Qwen/Qwen3-4B-Thinking-2507` on a 943-item private test set spanning high-school
to graduate-level math.

**Best Kaggle score (anchor):** 0.614 (Run 09 SC-8 V1, 2026-05-13)

## What's here

| File / Dir | Description |
|---|---|
| `CLAUDE.md` | Operating contract for the execution agent (claude_vscode) |
| `CLAUDE_STRATEGY.md` | Operating contract for the planning agent (claude_strategy) |
| `CLAUDE_THUNDER.md` | Operating contract for the SFT training agent (claude_thunder) |
| `HANDOFF.md` | Point-in-time project state for session continuity |
| `PLAN.md` | Current phase plan and deferred work |
| `COMPETITION.md` | Official Kaggle competition rules and submission format |
| `DESIGN.md` | Historical design + SFT evaluation methodology (§1209-1262) |
| `experiments.md` | Run log (Runs 03 through run14b) |
| `papers.md` | Paper findings log |
| `PIVOT.md` | Pointer to Phase 3 v1 → V0-V4 pivot |
| `SESSION_LOG.md` | Post-mortems for major failures |
| `private.jsonl` | 943-item private test set (at repo root) |
| `data/public.jsonl` | Public test set (retired as eval surface) |
| `scripts/` | Inference runners, GPU cleanup, format fixers, sampling variants |
| `training/` | SFT scripts (v1 archived; v3 plan in PLAN.md) |
| `results/` | Per-run JSONL outputs |
| `submissions/` | Kaggle submission CSVs |
| `report/` | Milestone report drafts |
| `archive_v1_postmortem/` | Preserved v1 SFT failure artifacts |

## Methodology summary

The project explored three approaches in sequence:

1. **Prompt engineering** (Phase 1, concluded): V0-V4 prompt variants ablation.
   V0 baseline locked.
2. **Self-consistency** (Phase 2, anchor): SC=8 majority voting on 943-item set.
   Scored 0.614 on Kaggle.
3. **Supervised fine-tuning** (Phase 3 v1 failed, Phase 3 v3 in progress):
   LoRA training on teacher-consensus pseudo-gold. See PLAN.md.

## Companion repos

- **DataApp:** https://github.com/beepbeeepimajeep/DataApp
  Generates teacher consensus answers (Sonnet + GPT-5.4 + GPT-OSS + GPT-5.5-xhigh)
  for SFT v3 pseudo-gold dataset construction.

## Compute infrastructure

- **DSMLP** (UCSD): A30 24GB pods for inference (vLLM 0.20.2, 6h walltime limit)
- **Thunder Compute** (paid, laptop-side): A100/H100 for SFT v3 training
  (Unsloth + TRL + vLLM)

## How to reproduce

This is an active competition workspace, not a tutorial. The starter-code notebook
(`starter_code_cse151b_comp.ipynb`) covers basic inference and scoring. For actual
reproduction of Runs 09 / run14b, see `experiments.md` and the launcher scripts in
`scripts/`.

## Constraints

- Required model: `Qwen/Qwen3-4B-Thinking-2507` (no alternatives at inference)
- No external API calls or tool-augmented generation at inference time
- 3 Kaggle submissions per day, 2 final submissions selectable at deadline
