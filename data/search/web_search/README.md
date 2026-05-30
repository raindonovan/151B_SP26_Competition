# web_search/ — answer-retrieval for the 943-item competition set

This area holds our attempt to find a **verified answer** for each of the 943
private-set items. It settled on a **single live track**, `regular_search/`. Two
other tracks were set up as options, tried/never-run, and removed — their records
are kept so the lessons aren't lost.

```
web_search/
├── CLAUDE.md             ← shared agent instructions (read first)
├── README.md             ← this file
├── TOOLING_RETIRED.md    ← record of a 2nd track (read past render/Cloudflare walls) — 0 GOLD, removed
├── COMPUTE_RETIRED.md    ← record of a 3rd track (compute answers, quarantined) — scaffolded, never run, removed
└── regular_search/       ← plain web search/fetch (Exa) — the canonical, only live track
```

## The one rule that governs the work

**GOLD = a real, independent web page LITERALLY STATES the answer to THIS exact
problem, read verbatim.** Same numbers, same setup, >=90% match. No deriving, no
computing, no copying a teacher/answer-sheet, no "close enough" twin with
different constants. An honest `NOT_FOUND` is a correct, valuable result.

## The retired tracks (why they existed, why they're gone)

- **`search_with_tooling/`** — for reading STATED answers past render/Cloudflare
  walls (AoPS MathJax-images behind Cloudflare). Produced **0 GOLD** from this
  sandbox; needs a real browser for ~3 Mock-AIME items. Removed. Full rationale +
  the 3 items (173, 471, 486) in `TOOLING_RETIRED.md`.
- **`search_with_compute/`** — a quarantined home for answers we COMPUTE
  (Wolfram/SymPy/derivation), with a deliberately different schema so a computed
  value could never be mistaken for web GOLD (the 362-fake-row lesson). Stayed
  **scaffolded but EMPTY** — no compute was ever run — so it was removed as
  clutter. Full rationale + candidate items in `COMPUTE_RETIRED.md`. If revived,
  it's a `data/` answer-sheet concern, not the web_search agent's.

## Canonical file & downstream consumers

`regular_search/search_results.csv` is the **canonical** search-GOLD source.
`scripts/build_master_gold.py` reads GOLD rows from it (path updated to
`regular_search/` when this folder was split on 2026-05-29).

## Current status (2026-05-30)

- regular_search: 943/943 searched — **60 GOLD / 14 PARTIAL / 869 NOT_FOUND**.
  (Source of truth is `regular_search/README.md`'s Status block / the CSV itself.)

## Forbidden sources

HuggingFace / benchmark / "gold_answer" aggregators (ProofRank, RIMO, JudgeBench,
AI-MO/olympiads, Apex) are **forbidden** — they may contain our own private
answers (circular). A hit there is NOT a source; record NOT_FOUND. Seen on items
53, 250, 383. See `regular_search/FINDINGS.md`.
