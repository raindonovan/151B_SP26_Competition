# search_with_compute/FINDINGS.md

## What this folder is

This is the **COMPUTE** track — answers obtained by COMPUTING (Wolfram Alpha,
SymPy, a script, direct derivation), NOT by reading a stated answer off a web
page. It is a sibling of `../regular_search/` and `../search_with_tooling/`,
both of which are *web-retrieval* tracks.

## HARD WALL: compute output is NOT web GOLD. Keep it separate.

- Rows here are **NEVER** labeled GOLD and **MUST NOT** be copied into
  `../regular_search/search_results.csv` or `../search_with_tooling/`.
- This is a deliberately quarantined track so that a computed value can never be
  mistaken for a web-verified one.
- Schema is intentionally DIFFERENT from the search tracks (compute_status /
  computed_answer / method, not search_status / found_answer / source_url) so the
  two can't be merged by accident.

## Why the wall exists (the 2026-05-28/29 lesson)

A prior pass drifted into computing/copying answers and labeling them GOLD; ~362
fake "search" rows had to be stripped. The whole web_search task's #1 guardrail is
"WEB SEARCH ONLY — never compute, never copy." This folder exists so that
legitimately-useful computation has a home WITHOUT violating that guardrail: it
lives here, clearly tagged as computed, and is only ever used downstream as a
SECONDARY signal (e.g. cross-check, or candidate when no web source exists), never
as web-verified gold.

## Status values (this track)

- compute_status: COMPUTED | UNVERIFIED | CONFLICT | SKIPPED
- method: e.g. wolfram_alpha, sympy, python_script, hand_derivation, oeis_formula
- confidence: how trustworthy the computation is (exact closed form > numeric
  approximation > messy multi-step).

## Scope (which items belong here)

Items where there is NO web page stating the answer, but the problem is cleanly
computable, e.g. (from regular_search NOT_FOUND/PARTIAL):
- definite integrals with a closed form (item 92: int_0^1 x^(m-1)/(1+x^n) dx),
- |GL_2(F_p)| = (p^2-1)(p^2-p) (item 569),
- ceil-sqrt partial sums (item 303),
- prime factorization of 30! (item 561),
- Putnam-variant indices where only the rule is web-stated
  (117 largest z<2021 not div by 42/46; 286 n(n+1)(2n+1)/6 > 89688).

## Operational note

This folder is SCAFFOLDED but EMPTY pending Rain's explicit go-ahead to actually
run compute (Wolfram etc.). Per the current instruction we are FOCUSING ON TOOLING
FIRST. Do not populate compute rows until told to. When enabled, prefer Wolfram /
SymPy for exactness and record the exact query used in `method`/`notes` so it is
reproducible and auditable.
