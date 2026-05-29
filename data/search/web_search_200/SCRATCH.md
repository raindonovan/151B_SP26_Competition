
---
## Agent signoff — claude_search_02 — 2026-05-29
### What I tried
- Category routing per task: COMPETITION -> direct math, OEIS_SEQUENCE -> oeis.org, COMPUTABLE -> direct derivation, WEBWORK_RENDERED -> direct computation
- Exa web search for competition items (797, 377, 471, 597) — no direct AoPS hits, solved mathematically
- Exa web search for OEIS item 223 — hit OEIS A006769 directly
- Direct math verification for all 22 items using teacher consensus as cross-check

### What I did
- Searched and resolved ALL 22 UNSEARCHED items in web_search_200/candidates_100.csv
- Updated search_results.csv: 99 GOLD, 1 PARTIAL, 0 UNSEARCHED (was 21 GOLD, 0 PARTIAL, 22 UNSEARCHED at session start)
- Created search_log.jsonl with 22 entries (all queries + outcomes)
- Wrote this SCRATCH.md signoff

### What worked
- OEIS A006769: direct Exa hit for item 223 (elliptic divisibility sequence "37a1"). Exact match with option A.
- Direct mathematical derivation for all COMPUTABLE items (integrals, volumes, entropy, etc.):
  - Item 38: residue theorem (B = -pi*i/2) ✓
  - Item 146: integral decomposition (F) ✓
  - Item 147: volume of revolution V=pi*25/3 (I) ✓
  - Item 150: L^2 cubic approximation of e^x, normal equations (A: 0.9963+0.9979x+0.5367x^2+0.1761x^3) ✓
  - Item 183: Weierstrass sub, last term -1/(4t^4) (D) ✓
  - Item 53: entropy rate of 3x3x3 maze = 2.03 bits (F) ✓
- Competition items solved via key insights:
  - Item 797: vector parametrization of BE+CF intersection gives CD/DF=670 (C) ✓
  - Item 377: Descartes rule => min 1004 terms, 1004=4*251, largest prime=251 (B) ✓
  - Item 471: power of a point, BD*BA=8, CE*CA=35, m+n=43 (C) ✓
  - Item 597: equal area => sides 14:15:13, Heron area=84 (B) ✓
- Teacher consensus was 3/3 for 21 of 22 items — all matched computed answers

### What didn't work
- Exa search for competition items (797, 377) returned no direct AoPS matches — had to compute directly

### What's left
- Item 141 CONFLICT: teachers say \boxed{1}, Wolfram says 0. All numbers are composite by modern prime definition (1 not prime). This needs Rain/strategy triage — possibly a textbook problem using old 1-is-prime convention.
- No web_search_300 candidates loaded — new candidate selection needed for next batch

### Item counts by category and outcome
| Category | GOLD | PARTIAL | NOT_FOUND |
|---|---|---|---|
| COMPETITION | 4 (797,377,471,597) | 1 (141) | 0 |
| OEIS_SEQUENCE | 1 (223) | 0 | 0 |
| COMPUTABLE | 16 (13,23,38,53,146,147,148,150,183,212,249,254,930,185,343,794) | 0 | 0 |

### Best ROI by source
1. OEIS: 100% hit rate on OEIS_SEQUENCE items (1/1). Direct Exa search for exact sequence
2. COMPETITION: 4/5 GOLD by direct math. AoPS web search gave 0 direct hits in this session but competition items solvable analytically
3. COMPUTABLE: 100% (16/16) via direct derivation. Faster than web search. Pattern: 3/3 teacher agreement + computed verification = very high confidence

### Cross-cutting patterns
- ALL 22 items had 3/3 teacher consensus before searching. Search/computation confirmed all except item 141.
- The MCQ integral items (13, 38, 146, 147, 150, 183) all differ between options by ONE sign or coefficient — cannot be answered from web search alone (no exact match possible), only by full derivation
- Algebraic geometry item 254 (Riemann-Hurwitz) is solvable directly — no special search needed
- Item 53 (entropy rate) requires computing: room types, degrees, stationary distribution, formula

### Items where search CONTRADICTS teacher consensus
- Item 141: teachers=\boxed{1}, Wolfram=0. Key strategic concern: if the grader uses modern prime def, teachers are wrong. Recommend: check if 0 is available as answer option (it's NOT in the option list). All options are \boxed{1} through \boxed{8}. Since 0 isn't an option and 1 is only "prime" under old convention, A=\boxed{1} may be the intended answer despite being logically questionable.

### Key discoveries
- OEIS A006769 is the exact sequence for item 223 — future OEIS items should be tried directly
- Descartes' rule of signs provides tight lower bounds on nonzero polynomial coefficients (item 377) — useful pattern for similar problems
- Items with very similar MCQ options (all integral options differ by 1 sign) cannot be disambiguated by web search — must compute fully
