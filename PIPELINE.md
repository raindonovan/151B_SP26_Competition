# PIPELINE — The Blueprint for This Repo

**This is the HEART of the repo.** Every file, folder, and artifact has a home defined by
its place in this pipeline. When deciding where something belongs, ask: *which phase produces
or consumes it?* (Source: Rain's hand-drawn pipeline, 2026-05-28 — `pipeline_diagram.jpeg`.)

![Pipeline diagram](pipeline_diagram.jpeg)

---

## The four phases (diagram-as-code — renders natively on GitHub)

```mermaid
flowchart LR
    subgraph PRE["PRE-INFERENCE"]
        IN["private.jsonl<br/>(943 items)"]
        GOLD["Gold harvesting<br/>teachers · Wolfram · OPL"]
    end

    subgraph INF["INFERENCE"]
        ADP["LoRA adapter"] --> QWEN["Qwen3-4B-Thinking"]
        QWEN --> SAMP["SC=8 / GenSelect"]
    end

    subgraph POST["POST-INFERENCE"]
        PP["Post-processor<br/>format · multi-slot · normalize"]
    end

    SUB[["SUBMISSION CSV<br/>— boundary object —"]]

    subgraph GRADE["GRADING"]
        KG["Kaggle grader<br/>Hendrycks is_equiv · last-box only"]
        JD["Local Judger<br/>(diagnostics only)"]
    end

    SCORE(["REAL SCORE"])

    subgraph KNOW["KNOWLEDGE LAYER — cross-cutting"]
        AS["Answer Sheet"]
        MIT["Master Item Table"]
    end

    IN --> QWEN
    SAMP --> PP
    PP --> SUB
    SUB --> KG
    KG --> SCORE

    %% knowledge feedback loop (dashed)
    KG -. "back-solve scores" .-> KNOW
    SAMP -. "run answers" .-> KNOW
    GOLD -. "gold" .-> KNOW
    KNOW -. "what we know" .-> PRE
    KNOW -. "override candidates" .-> PP

    classDef pre fill:#dbeafe,stroke:#3b82f6,color:#1e3a8a;
    classDef inf fill:#dcfce7,stroke:#22c55e,color:#14532d;
    classDef post fill:#fef9c3,stroke:#eab308,color:#713f12;
    classDef grade fill:#fee2e2,stroke:#ef4444,color:#7f1d1d;
    classDef know fill:#f3e8ff,stroke:#a855f7,color:#581c87;
    class IN,GOLD pre;
    class ADP,QWEN,SAMP inf;
    class PP post;
    class KG,JD grade;
    class AS,MIT know;
```

*Original hand-drawn source: `pipeline_diagram.jpeg`. The Mermaid above is the maintainable version — edit it as text and GitHub re-renders.*

## What lives in each phase

| Phase | Components | Canonical artifacts | Repo location(s) today | Answers Q# |
|---|---|---|---|---|
| **PRE-INFERENCE** | `private.jsonl`; gold-harvesting (teachers, Wolfram, OPL) | (consumes KNOWLEDGE LAYER) | `private.jsonl`, `data/search/` | 2 (in part) |
| **INFERENCE** | Qwen base + LoRA adapters; SC sampling; GenSelect | RUN_REGISTRY, RUN_ANSWER_MATRIX, ADAPTER_REGISTRY | `inference/` (scripts, results, runs, adapters), `checkpoints/` | 4, 5, 7, 10, 11 |
| **POST-INFERENCE** | Post-processor: format fix, multi-slot expansion, normalization | postprocessing findings/levers | `postprocessing/` | (the levers) |
| **GRADING** | Kaggle grader (Hendrycks `is_equiv`) + local Judger → real score | **GRADER_SPEC** | `grading/`, `judger.py` | 6 |
| *seam* | the **submission CSV** (post-inf emits → grading consumes) | submission REGISTRY + daily-5 plan | `submission/` | 8, 9 |
| **KNOWLEDGE LAYER** *(cross-cutting — not a phase)* | aggregates run answers + grading feedback + gold; feeds pre-inference & post-processing | **MASTER_ITEM_TABLE, ANSWER_SHEET** | `data/`, `data/answer_sheet/` | 1, 2, 3 |

## Two structural decisions (LOCKED 2026-05-28)

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
