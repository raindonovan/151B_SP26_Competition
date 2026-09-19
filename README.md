# CSE 151B Spring 2026 — Math Reasoning Competition

Code, experiments, data, and submissions for the UCSD CSE 151B Spring 2026 Kaggle
competition: improving the mathematical reasoning of `Qwen/Qwen3-4B-Thinking-2507`
on a 943-item held-out test set spanning high-school to graduate-level math, using
only model-intrinsic methods at inference time.

**Best-scoring submission:** 0.745 public / 0.684 private
(`submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v2.csv`; see `submission/REGISTRY.md`).
The course final report in `gradescope/finalreport/` gives the full account of results,
including the official final score and what went wrong at pick selection.

## What's here

| Path | Description |
|---|---|
| `PIPELINE.md` | The blueprint: which phase produces or consumes every artifact |
| `COMPETITION.md` | Competition rules, eval, data and submission formats, staff rulings |
| `START_HERE.md` | Entry point for the central strategy agent |
| `CLAUDE.md`, `agents/` | Operating contracts for the Claude agents that ran execution |
| `data/` | Questions and answers (`data/raw/`), every generated sample (`data/samples/`), gold sets, teacher and Wolfram verification (`data/search/`) |
| `inference/` | vLLM runners, run catalog, per-run outputs, LoRA adapter logs |
| `postprocessing/` | Answer extraction, normalization rules, grader-format findings |
| `grading/` | `grader.py`, the local mirror of the Kaggle grader (validated 943/943 post-competition) |
| `submission/` | Dated submission folders, CSVs, registry of every scored submission |
| `strategy/` | Plans, handoffs, reviews, adapter notes |
| `research/`, `report/` | Literature notes and figures |
| `gradescope/` | Milestone and final reports, starter notebook, reproduction entry point |
| `post_comp/` | Post-competition stats, debrief, and follow-on planning |
| `archive/` | Superseded designs, handoffs, session logs, and postmortems |
| `private.jsonl` | The 943-item test set |

## Approach

1. **Prompt ablation** (V0–V4 variants on a fixed 50-item slice). V0 baseline locked.
2. **Self-consistency inference** at scale: SC@8 and SC@16 majority voting over the full 943 with
   token budgets up to 81,920, ~47k local generations and ~213M generated tokens across the campaign.
3. **Post-processing and format alignment** against a local grader mirror, driven by
   format rules discovered from score deltas.
4. **Gold verification**: frontier-teacher consensus, Wolfram, search, and back-solve to build a
   verified answer set for measuring runs offline.
5. **LoRA fine-tuning** (six adapter generations, transductive pseudo-labels). Explored thoroughly;
   none beat the inference-only stack. See `strategy/ADAPTER_NOTES.md` and `inference/adapters/`.

## Compute

- **UCSD DSMLP**: A30 pods for inference (6h walltime).
- **Thunder Compute**: A100 / H100 for adapter training and multi-shard inference.
- **Local**: RTX 4090 for long single-GPU runs.

## Constraints

- Required model: `Qwen/Qwen3-4B-Thinking-2507`, no alternatives at inference.
- No external API calls or tool-augmented generation at inference time.
- Limited Kaggle submissions per day; two final picks selectable at deadline.

## Reproduce

Single entry point: `inference/scripts/run_inference.py` → `run_inference()`.
Loads the base model (no adapter), runs SC inference, post-processes, and writes
`submission.csv` (`id,response`). Requires vLLM 0.10.2 / 0.11.1 and one GPU.

```bash
python3 inference/scripts/run_inference.py
```

The starter notebook is at `gradescope/starter_code_cse151b_comp.ipynb`.

## Companion repo

- **DataApp**: https://github.com/beepbeeepimajeep/DataApp — teacher-consensus answer
  generation (Sonnet, GPT-5.4, GPT-OSS, GPT-5.5) used for gold verification and SFT datasets.

## After the competition

`data/` was rebuilt as two audited datasets (questions + answers, and every raw sample) for
summer research on self-consistency voting. Competition-wide numbers are in
`post_comp/COMPETITION_STATS.md`.
