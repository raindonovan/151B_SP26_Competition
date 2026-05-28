# PIPELINE — The Blueprint for This Repo

**This is the HEART of the repo.** Every file, folder, and artifact has a home defined by
its place in this pipeline. When deciding where something belongs, ask: *which phase produces
or consumes it?* (Source: Rain's hand-drawn pipeline, 2026-05-28 — `pipeline_diagram.jpeg`.)

![Pipeline diagram](pipeline_diagram.jpeg)

---

## The four phases

```
  PRE-INFERENCE          INFERENCE              POST-INFERENCE      GRADING
 ┌──────────────┐     ┌──────────────┐        ┌──────────────┐   ┌──────────────────┐
 │ private.jsonl│ ──▶ │  Qwen        │ ──────▶ │ Post         │──▶│ Kaggle grader    │
 │ + what we    │     │  + Adapter   │ infer.  │ Processor    │   │   + Judger       │──▶ REAL SCORE
 │   KNOW       │     │ (SC=8,       │ output  │ (format fix, │   │ (Hendrycks       │
 │ (teachers,   │     │  GenSelect…) │         │  multi-slot, │   │  is_equiv)       │
 │  Wolfram,OPL)│     │              │         │  normalize)  │   └──────────────────┘
 └──────▲───────┘     └──────────────┘         └──────────────┘            │
        │                                            │ emits              │
        │                                       ┌────▼──────┐             │
        │   knowledge loop (dashed):            │ SUBMISSION│ ── fed in ──┘
        └────── grading feedback refines ───────┤   CSV     │
                the answer sheet / item table   └───────────┘  (boundary object:
                                                                post-inf → grading)
```

## What lives in each phase

| Phase | Components | Canonical artifacts | Repo location(s) today | Answers Q# |
|---|---|---|---|---|
| **PRE-INFERENCE** | `private.jsonl`; gold-harvesting (teachers, Wolfram, OPL); accumulated knowledge | MASTER_ITEM_TABLE, ANSWER_SHEET | `private.jsonl`, `data/`, `data/search/`, `data/answer_sheet/` | 1, 2, 3 |
| **INFERENCE** | Qwen base + LoRA adapters; SC sampling; GenSelect | RUN_REGISTRY, RUN_ANSWER_MATRIX, ADAPTER_REGISTRY | `inference/` (scripts, results, runs, adapters), `checkpoints/` | 4, 5, 7, 10, 11 |
| **POST-INFERENCE** | Post-processor: format fix, multi-slot expansion, normalization | postprocessing findings/levers | `postprocessing/` | (the levers) |
| **GRADING** | Kaggle grader (Hendrycks `is_equiv`) + local Judger → real score | **GRADER_SPEC** | `grading/`, `judger.py` | 6 |
| *seam* | the **submission CSV** (post-inf emits → grading consumes) | submission REGISTRY + daily-5 plan | `submission/` | 8, 9 |

## Two structural notes (refine as needed)

1. **The submission is a boundary object, not a phase.** It's what post-inference emits and grading
   consumes — it sits on the seam. That's why "purpose of each submission" (Q8) and "daily-5 goals" (Q9)
   straddle phases 3 and 4.

2. **There is a knowledge feedback loop.** ANSWER_SHEET and MASTER_ITEM_TABLE are not produced by any one
   phase — they are built FROM grading outputs (back-solving probable gold from submission scores) + run
   outputs + teacher/Wolfram gold, and they feed BACK into pre-inference ("what we know") and into
   post-processing (override candidates). The pipeline is linear for one pass; the knowledge layer wraps
   the whole loop and gets smarter every submission. (Dashed arrow above.)

## How to use this blueprint

- **Placing a file:** identify the phase that produces/consumes it → that phase's folder is its home.
- **Answering a "where is X?" question:** find X in the artifacts column above → follow to its location.
- **The 11 organization questions** all resolve to a (phase, artifact) coordinate — see the table.
