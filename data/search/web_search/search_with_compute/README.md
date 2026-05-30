# search_with_compute/ — answers obtained by COMPUTING (quarantined)

Sibling of `../regular_search/` and `../search_with_tooling/`, but fundamentally
different: rows here are answers we **COMPUTED** (Wolfram Alpha, SymPy, a script,
direct derivation), NOT answers read off a web page.

## HARD WALL — read this first

- Rows here are **NEVER labeled GOLD** and **MUST NOT** be copied into the search
  tracks' CSVs.
- The schema is intentionally DIFFERENT (no `search_status`/`found_answer`/
  `source_url`) so the two can't be merged by accident.
- Downstream, compute output is at most a **secondary signal** (cross-check, or a
  candidate when no web source exists) — never web-verified gold.

## Why the wall exists (the 2026-05-28/29 lesson)

The web_search task's #1 guardrail is "WEB SEARCH ONLY — never compute/copy." A
prior pass drifted into computing/copying answers and labeling them GOLD; ~362
fake "search" rows had to be stripped. This folder gives legitimate computation a
home WITHOUT contaminating the search GOLD: it lives here, clearly tagged.

## CSV schema (deliberately distinct from the search tracks)

```
item_id,category,compute_status,computed_answer,method,confidence,notes
```

- `compute_status` — COMPUTED | UNVERIFIED | CONFLICT | SKIPPED.
- `computed_answer` — the computed value.
- `method` — wolfram_alpha | sympy | python_script | hand_derivation | oeis_formula.
- `confidence` — exact closed form > clean discrete value > numeric approximation.
- `notes` — the EXACT query/expression used, so it is reproducible and auditable.

## Scope — which items belong here

Items with NO web page stating the answer but that are cleanly computable, e.g.:
- definite integrals with closed form (92: int_0^1 x^(m-1)/(1+x^n) dx),
- |GL_2(F_p)| = (p^2-1)(p^2-p) (569),
- ceil-sqrt partial sums (303), prime factorization of 30! (561),
- Putnam-variant items where only the RULE is web-stated, not our value
  (117: largest z<2021 not div by 42/46; 286: n(n+1)(2n+1)/6 > 89688).

## Status (2026-05-30)

**Scaffolded but EMPTY — no compute has been run.** Per current direction we are
focusing on retrieval (regular_search + tooling). Do NOT populate compute rows
until Rain explicitly enables it. When enabled, prefer Wolfram/SymPy for
exactness and record the exact query in `method`/`notes`.
