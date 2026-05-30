# COMPUTE_RETIRED.md — the `search_with_compute/` track (an option we set up, never ran, removed)

Scaffolded 2026-05-29/30, removed 2026-05-30. Kept as a record so the option —
and the reason it was walled off and then dropped — isn't lost. Companion to
`TOOLING_RETIRED.md` (the other retired sibling track).

## What it was for

A deliberately **quarantined** third track for items where NO web page states the
answer but the problem is cleanly computable (Wolfram Alpha, SymPy, a script,
direct derivation). It existed so legitimate computation had a home WITHOUT
contaminating the web-search GOLD set.

The web_search task's #1 guardrail is **"WEB SEARCH ONLY — never compute, never
copy."** This folder was the pressure valve for that rule: a computed value could
live here, clearly tagged as computed, used downstream only as a SECONDARY signal
(cross-check, or a candidate when no web source exists) — but **never** labeled
GOLD and **never** merged into the search CSVs.

## The hard wall it enforced (the 2026-05-28/29 lesson)

A prior pass drifted into computing/copying answers and labeling them GOLD; ~362
fake "search" rows had to be stripped. To make that mistake structurally
impossible, this track used a **deliberately different schema** so the two could
never be merged by accident:

```
# compute track (retired):  item_id,category,compute_status,computed_answer,method,confidence,notes
# search track (canonical): item_id,category,search_status,found_answer,source_url,source_type,confidence,notes
```

- `compute_status`: COMPUTED | UNVERIFIED | CONFLICT | SKIPPED
- `method`: wolfram_alpha | sympy | python_script | hand_derivation | oeis_formula
- Rows here were NEVER GOLD; downstream they were at most a secondary signal.

## Candidate items it was meant for (if compute were ever enabled)

Cleanly computable, no web page states the value (from regular_search NOT_FOUND/PARTIAL):

- **92** — definite integral with closed form: int_0^1 x^(m-1)/(1+x^n) dx
- **569** — |GL_2(F_p)| = (p^2-1)(p^2-p)
- **303** — ceil-sqrt partial sums
- **561** — prime factorization of 30!
- **117** — Putnam 2021 A5 variant: largest z<2021 not divisible by 42 nor 46
- **286** — Putnam 2023 A1 structure: n(n+1)(2n+1)/6 > 89688

These remain `NOT_FOUND`/`PARTIAL` in `regular_search/search_results.csv`. The web
page states only the RULE/formula for the PARTIALs (117, 286), not our value;
closing them needs computation, which the search agent does not do.

## Why it was removed (never produced anything)

The track stayed **scaffolded but EMPTY** for its entire life: the CSV never held
more than a header row, and no compute was ever run (we were directed to focus on
retrieval). Net output: **0 rows**. With the web-search phase wrapped at
**60 GOLD / 14 PARTIAL / 869 NOT_FOUND**, an empty, never-used quarantine folder
was just clutter. Deleted; this file preserves the rationale.

## If compute is ever revived

Re-create the folder with the distinct schema above (so it can never be confused
with search GOLD). Prefer Wolfram/SymPy for exactness; record the EXACT query in
`method`/`notes` so every row is reproducible and auditable. Compute output is a
**secondary signal only** — never web GOLD, never merged into the search CSV.
Owner: this is a `data/` (answer-sheet) concern, not the web_search agent's —
see `data/CLAUDE.md` (Wolfram overrides live in `data/wolfram_overrides.csv`).
