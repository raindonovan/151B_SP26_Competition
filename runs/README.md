# RUNS — Master Index

**Owner**: claude_strategy (repo hygiene)
**Purpose**: Every experiment we've run gets a folder here with its analysis. Raw data stays in `results/`; the ANALYSIS, FINDINGS, and DECISION live here.

## Why this exists

We kept losing gold: runs completed, results sat unanalyzed in `results/`, and "what we learned" got scattered across docs/, Drive, and ad-hoc notes. This folder is the single home for "what each run was, what we found, what we decided." If a run isn't documented here, it's not analyzed.

## Naming convention (NO MORE CODES like F5 / P1 / W2)

Folders and sections use DESCRIPTIVE names. A run folder is named for what it was: `sft_v5`, `genselect_poc`, `run14b_sc8_32k`. Findings inside use plain-English headers, not codes.

## Structure

```
runs/
├── README.md              ← this index
├── adapters/              ← all SFT / LoRA training runs
│   ├── sft_v1_3arm/       ← May 6 catastrophe (NuminaMath/OpenR1/Frugal)  [TODO populate]
│   ├── sft_v3/            ← scored 0.452                                  [TODO populate]
│   ├── sft_v4/            ← scored 0.597                                  [TODO populate — sft/v4/ UNREAD]
│   └── sft_v5/            ← break-even ~0.646; memorization paradox       [DONE]
├── inference/             ← model inference runs
│   ├── run14b_sc8_32k/    ← 0.646, our best inference baseline           [TODO populate]
│   ├── nothinking_943/    ← NoThinking SC=8 full 943, never scored        [TODO populate]
│   └── hardest30_sc16/    ← hard-item amplification, never analyzed       [TODO populate]
├── selection/             ← inference-time selection
│   └── genselect_poc/     ← truncation bug, never properly analyzed       [DONE]
├── matching/              ← question matching
│   └── opl/               ← OpenProblemLibrary embedding match            [DONE]
└── verification/          ← label/answer verification
    └── pace/              ← Programmatic Answer-label Comp. Evaluation     [TODO populate]
```

## Per-run folder contents

Each run folder should have:
- `README.md` — what the run was, when, config, where raw data lives
- `findings.md` — what we learned (plain-English headers)
- `decision.md` — what we're doing about it (only when a decision exists)

## Status table

| Run | Category | Kaggle score | Analyzed? | Notes |
|---|---|---|---|---|
| sft_v1_3arm | adapters | not submitted | TODO | 3-arm catastrophe; assistant_only_loss silently disabled |
| sft_v3 | adapters | 0.452 | TODO | |
| sft_v4 | adapters | 0.597 | TODO | sft/v4/ folder UNREAD — composition unknown |
| sft_v5 | adapters | ~0.646 (break-even) | DONE | memorization ≠ generalization; 87% T1-easy training |
| run14b_sc8_32k | inference | 0.646 | TODO | BEST INFERENCE; 32K tokens gave +2.5pp over 16K |
| nothinking_943 | inference | never scored | TODO | 45MB, 5.3% truncation; diversity ensemble candidate |
| hardest30_sc16 | inference | never scored | TODO | hard-item amplification |
| genselect_poc | selection | n/a | DONE | truncation bug; Qwen-as-judge inconclusive |
| opl | matching | n/a | DONE | 39 OK-status gold items |
| pace | verification | n/a | TODO | label verification; ~200-300 computable |

## NEXT-SESSION TASK #1 — FULL REPO READ + GOLD HUNT

claude_strategy has NOT done a true full repo read. These large files are UNREAD and may contain floating gold:
- `DESIGN.md` (69KB)
- `experiments.md` (87KB)
- `prompt_engineering_research.md` (71KB)
- `papers.md`, `variants_and_prompts.md`, `HANDOFF.md` (32KB)
- `sft/v3/`, `sft/v4/` folders (adapter composition unknown)
- `report/`, `research/`, `tests/`, `data/`, `pre_flight/` directories

**Task**: read every doc, populate the TODO run folders above, surface any gold answers / findings / working levers not yet captured. Dedicate a fresh-context session to this. This is the #1 priority per Rain (organization is the greatest lever today/tomorrow).
