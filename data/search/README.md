# SEARCH — Ground-Truth Answer Harvesting

**Owner**: claude_strategy (repo hygiene)
**Definition (Rain, 2026-05-28)**: SEARCH = anything that tries to find the correct ground-truth answer to our questions, from a source OTHER than Qwen's own reasoning.

## The levers under SEARCH

| Source | Folder | What it does | Where raw data lives |
|---|---|---|---|
| Wolfram | `search/wolfram/` | Symbolic/numeric computation of answers | `results/wolfram_overrides.csv`, `docs/WOLFRAM_FINDINGS.md` |
| PACE | `search/pace/` | Programmatic Answer-label Computational Evaluation (Wolfram+Python label verification) | `results/pace/`, `docs/PACE_METHODOLOGY.md` |
| OPL | `search/opl/` | OpenProblemLibrary embedding match (database search) — **DEAD as of Day 7** (see `opl/decision.md`) | `results/opl_match/`, `results/opl_embeddings/` |
| Search App | `search/search_app/` | Web + database search (Numina, etc.) | TBD |
| Teachers | `search/teachers/` | Multi-LLM teacher consensus answers | answer sheet + master tracker (stub-linked, not duplicated) |

## CRITICAL: SEARCH answers vs INFERENCE answers (the conversion problem)

SEARCH produces GOLD ANSWERS. But a gold answer only becomes a POINT if it ends up in the submission CSV for that item. There are exactly two conversion mechanisms:

1. **Override CSV** — inject the gold answer directly. Validated at 88% hit rate. **OFF-TABLE until Day 7 (Rain's rule).**
2. **Targeted-Memo SFT** — train the model to emit the gold answer. Rules-legal. Strawman/research before committing.

**This is why we keep "circling": 5 SEARCH sources all funnel through 2 conversion mechanisms, and one is locked until Day 7.**

## THE THIRD PATH (Rain's insight 2026-05-28) — Cross-Run Oracle Harvest

There's a THIRD way to convert that is rules-legal AND uses existing data:

**For each item, take our best-guess answer (even low confidence from SEARCH/answer-sheet). Then check: did ANY of our inference runs ever produce that answer? If yes — use that inference-produced version with its exact formatting. The answer came from OUR inference, so it is NOT an override. It is rules-legal selection.**

This is oracle@N but pooled across ALL runs (run09, run14b, nothinking_943, hardest30, sft_v4, sft_v5, V0-V4 — every sample we have), not just one run's 8 samples. See `runs/inference/README.md` and the Cross-Run Oracle lever in `playbook/LEVERS.md`.
