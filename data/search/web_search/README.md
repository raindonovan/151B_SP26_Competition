# web_search/ — answer-retrieval tracks for the 943-item competition set

This area holds our attempt to find a **verified answer** for each of the 943
private-set items. Work is split into **two sibling tracks** by *how* the answer
was obtained.

```
web_search/
├── CLAUDE.md                ← shared agent instructions (read first)
├── README.md                ← this file
├── TOOLING_RETIRED.md       ← record of a 3rd track that was tried and removed
├── regular_search/          ← plain web search/fetch (Exa) — the canonical baseline
└── search_with_compute/     ← answers obtained by COMPUTING (quarantined, never GOLD)
```

> A third track, `search_with_tooling/`, briefly existed (2026-05-29/30) for
> reading STATED answers past render/Cloudflare walls. It produced **0 GOLD** from
> this sandbox and was **removed**. The full rationale + the items it was meant for
> is preserved in `TOOLING_RETIRED.md` so the lesson isn't lost.

## The one rule that governs both tracks

**GOLD = a real, independent web page LITERALLY STATES the answer to THIS exact
problem, read verbatim.** Same numbers, same setup, >=90% match. No deriving, no
computing, no copying a teacher/answer-sheet, no "close enough" twin with
different constants. An honest `NOT_FOUND` is a correct, valuable result.

The two tracks differ only in retrieval mechanism, with one explicit exception:
**compute output is never GOLD** (see that track's README).

## Track summary

| track | what it is | can it produce GOLD? |
|---|---|---|
| `regular_search/` | Exa `web_search_exa` / `web_fetch_exa`. The canonical, full-943 file. | Yes |
| `search_with_compute/` | Answers we COMPUTED (Wolfram/SymPy/derivation). | **No** — separate schema, never merged into the search files. |

## Canonical file & downstream consumers

`regular_search/search_results.csv` is the **canonical** search-GOLD source.
`scripts/build_master_gold.py` reads GOLD rows from it (path updated to
`regular_search/` when this folder was split on 2026-05-29). `search_with_compute`
is secondary/auxiliary.

## Current status (2026-05-30)

- regular_search: 943/943 searched — **60 GOLD / 14 PARTIAL / 869 NOT_FOUND**.
- search_with_compute: scaffolded, **empty** by design (compute not run).

## Forbidden sources (both tracks)

HuggingFace / benchmark / "gold_answer" aggregators (ProofRank, RIMO, JudgeBench,
AI-MO/olympiads, Apex) are **forbidden** — they may contain our own private
answers (circular). A hit there is NOT a source; record NOT_FOUND. Seen on items
53, 250, 383. See `regular_search/FINDINGS.md`.
