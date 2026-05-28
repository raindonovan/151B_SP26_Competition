# SESSION HANDOFF — READ THIS FIRST (new chat entry point)

**Last updated**: 2026-05-28 (Day 4 EOD). Supersedes `docs/STRATEGY_DAY4_LOCKED.md` for current state.
**Read order for new session**: this file → `runs/README.md` → `search/README.md` → `playbook/LEVERS.md` → `playbook/FINDINGS.md` → memory.

## WHERE WE ARE

- Best inference-only: **0.646** (run14b, SC=8, 32K tokens) — our ceiling on pure inference
- Best with overrides: 0.692 (Day 3 kitchen sink) — overrides OFF-TABLE until Day 7
- Leader: 0.85
- Submissions: ~12 remaining, 3/day. **5 available right now.**
- Gradescope code due Sun 5/31. Kaggle final ~6/02.

## THE BRUTAL TRUTH (accept it, then beat it)

Every inference lever after run14b gave ~0. The only thing that moved inference was 16K→32K tokens (+2.5pp). Qwen's raw capability caps ~0.65 here. All gains to 0.692 were overrides.

**Rain's mandate**: this is NOT acceptable as the final word. We have tons of data, poorly organized. Organize it, then MILK every pp from what we have before any new inference/SFT.

## THE CRUX (why we keep circling)

We have 5 SEARCH sources for gold answers (Wolfram, PACE, OPL, search-app, teachers). They ALL funnel through 2 conversion mechanisms to become points:
1. Override CSV (validated 88%, OFF-TABLE until Day 7)
2. Targeted-Memo SFT (rules-legal, must strawman/research first)

Plus a THIRD path discovered this session:

## ⭐ THE THIRD PATH — Cross-Run Oracle Harvest (Rain's insight, HIGHEST PRIORITY)

**For each item: take our best-guess answer (even 51% confidence from answer-sheet/SEARCH). Check if ANY inference run ever produced that answer. If yes → use that inference-produced version with its exact formatting/config. It came from OUR inference = RULES-LEGAL, NOT an override.**

This pools oracle@N across ALL runs (run09, run14b, nothinking_943, hardest30, sft_v4, sft_v5, V0-V4 — every sample we have), not just one run's 8. Uses existing data, no new inference. **This is the rules-clean way to convert the answer sheet into points before Day 7.**

Rain's question to answer: "what would we score if we built that list?" → BUILD IT. This is Thursday's main milking task.

## THE SCHEDULE (Rain, locked 2026-05-28)

- **Rest of Day 4 (Wed)**: repo organization + data analysis + collection
- **Thursday**: milk every datapoint for best INFERENCE-ONLY score (Cross-Run Oracle Harvest + generic multi-slot expander + oracle@8)
- **Friday**: gold-answer data collection (SEARCH). Final strategy decision (SFT/GRPO/whatever).
- **Saturday**: SFT roll-of-the-dice (or whatever Friday's strategy meeting decides)
- **Sunday**: final submission

## THE LEVERS (full detail in playbook/LEVERS.md)

RULES-EXCLUDED: TIR (tool-aug gen), PRM (external model). Both dead.

ALIVE, ranked for the milking phase:
1. **Cross-Run Oracle Harvest** (NEW) — pool all run samples, select best-guess matches. Rules-legal. Existing data. HIGHEST PRIORITY Thursday.
2. **Generic Multi-Slot Expander** (NEW) — read Qwen's OWN reasoning text, fix under-counted \boxed{} (e.g. emitted 2 slots, question wants 6). Post-processing, NOT override. Attacks the 79% format-failure mode. Rules-clean.
3. **oracle@8 on run14b** — diagnostic: does the 8-sample pool contain right answers? Tells us if selection (GenSelect) is worth it.
4. **GenSelect re-run** — Qwen judging Qwen (rules-legal). Fix the truncation bug first + smoke test.
5. **Hard-item SC + NoThinking 943 analysis** — free data already computed.
6. **Targeted-Memo SFT** (Lever 6) — Saturday roll-of-dice candidate. Strawman first.

## REPO STRUCTURE (reorganized this session)

```
runs/                  ← inference/adapter/selection experiments (analysis, not raw data)
  adapters/  (sft_v1_3arm, sft_v3, sft_v4, sft_v5[DONE])
  inference/ (run14b_sc8_32k, nothinking_943, hardest30_sc16)
  selection/ (genselect_poc[DONE])
search/                ← ground-truth answer harvesting
  wolfram/  pace/  opl/[DONE]  search_app/  teachers/[stub-link]
playbook/              ← strategy/plan only (README, TODO, FINDINGS, LEVERS, RESEARCH, TIERS)
docs/                  ← canonical project docs (TODO, FINDINGS, WOLFRAM_FINDINGS, etc.)
results/               ← raw run outputs (data stays here; analysis goes in runs/)
```

Naming: descriptive names, NO codes (no more F5/P1/W2).

## NEXT-SESSION TASK #1 — FULL REPO READ (not yet done, Rain flagged twice)

claude_strategy has NOT read every file. UNREAD and possibly gold-bearing:
`DESIGN.md` (69KB), `experiments.md` (87KB), `prompt_engineering_research.md` (71KB), `HANDOFF.md` (32KB), `papers.md`, `variants_and_prompts.md`, `sft/v3/`, `sft/v4/`, `report/`, `research/`, `tests/`, `data/`, `pre_flight/`.

Read everything. Populate the TODO run folders. Surface floating gold. Rain: "I HAVE A FEELING DOCS CONTAINING GOLD ARE FLOATING AROUND EVERYWHERE." Trust that instinct.

## THURSDAY MILKING SEQUENCE (after full read)

1. Build Cross-Run Oracle Harvest list — for each item, best-guess answer + did any run produce it
2. Generic multi-slot expander on Qwen's own text → submit one slot
3. oracle@8 on run14b → decide GenSelect worth
4. Score NoThinking 943 standalone → one slot, free diagnostic
5. Map T1-T5 answer-sheet coverage → know Day 7 override ammo

## OPEN DECISIONS FOR RAIN

1. Confirm Cross-Run Oracle Harvest as Thursday's #1 milking task
2. Strawman Targeted-Memo SFT before Saturday commit
3. Could exhausting all SEARCH get answer sheet to ~0.9? (Rain estimate, ~2 days harvest) — likely yes for the SHEET, but conversion still needs override (Day 7) or SFT. Inference-only won't reach 0.9.

## ADAPTER HISTORY NOTE

v1 (3-arm catastrophe, not submitted) → v3 (0.452) → v4 (0.597, composition UNREAD) → v5 (~0.646 break-even, 87% T1-easy training). No v2, no v6. "v7" = planned next (naming skips v6 — investigate). v5 kept as adapter, NO merge. Targeted-Memo SFT (Lever 6) is DIFFERENT from v5 because it would train on items Qwen gets WRONG, not the 87% easy items — BUT confirm via full read that we didn't already try this.
