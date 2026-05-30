# web_search/ — answer-retrieval tracks for the 943-item competition set

This area holds our attempt to find a **verified answer** for each of the 943
private-set items. Work is split into **three sibling tracks** by *how* the answer
was obtained. Each track has the same trio of files (`search_results.csv`,
`FINDINGS.md`, `SCRATCH.md`) plus its own `README.md`.

```
web_search/
├── CLAUDE.md                ← shared agent instructions (read first)
├── README.md                ← this file
├── regular_search/          ← plain web search/fetch (Exa) — the canonical baseline
├── search_with_tooling/     ← retrieving STATED answers past render/Cloudflare walls
└── search_with_compute/     ← answers obtained by COMPUTING (quarantined, never GOLD)
```

## The one rule that governs all three tracks

**GOLD = a real, independent web page LITERALLY STATES the answer to THIS exact
problem, read verbatim.** Same numbers, same setup, >=90% match. No deriving, no
computing, no copying a teacher/answer-sheet, no "close enough" twin with
different constants. An honest `NOT_FOUND` is a correct, valuable result.

The three tracks differ ONLY in retrieval mechanism, not in this bar — with one
explicit exception: **compute output is never GOLD** (see that track's README).

## Track summary

| track | what it is | can it produce GOLD? |
|---|---|---|
| `regular_search/` | Exa `web_search_exa` / `web_fetch_exa`. The canonical, full-943 file. | Yes |
| `search_with_tooling/` | Same GOLD bar, but uses curl/raw-HTML/headless-browser to read a STATED answer the plain fetcher couldn't (MathJax images, Cloudflare). | Yes |
| `search_with_compute/` | Answers we COMPUTED (Wolfram/SymPy/derivation). | **No** — separate schema, never merged into the search files. |

## Canonical file & downstream consumers

`regular_search/search_results.csv` is the **canonical** search-GOLD source.
`scripts/build_master_gold.py` reads GOLD rows from it. (When this folder was
split into the 3-track layout on 2026-05-29, that script's path was updated to
point at `regular_search/`.) The other two tracks are secondary/auxiliary.

## Current status (2026-05-30)

- regular_search: 943/943 searched — **52 GOLD / 7 PARTIAL / 884 NOT_FOUND**.
- search_with_tooling: 3 rows, all `BLOCKED_NEEDS_PLAYWRIGHT` (AoPS Mock-AIME items
  that need a real browser to read the rendered answer; not worth a Playwright
  install for 3 items — see its README/FINDINGS).
- search_with_compute: scaffolded, **empty** by design (compute not run; focusing
  on retrieval).

## Forbidden sources (all tracks)

HuggingFace / benchmark / "gold_answer" aggregators (ProofRank, RIMO, JudgeBench,
AI-MO/olympiads, Apex) are **forbidden** — they may contain our own private
answers (circular). A hit there is NOT a source; record NOT_FOUND. Seen on items
53, 250, 383. See `regular_search/FINDINGS.md`.
