# data/search/web_search/FINDINGS.md

Canonical home for web search discoveries. Add to this file whenever a search session yields a notable finding.

---

## Session stats as of 2026-05-29

| Batch | Items | GOLD | PARTIAL | NOT_FOUND | UNSEARCHED |
|-------|-------|------|---------|-----------|------------|
| Batch 1 (top-level) | 100 | 69 | 13 | 18 | 0 |
| Batch 2 (web_search_200) | 100 | 99 | 1 | 0 | 0 |
| Batch 3 (web_search_300) | 100 | 0 | 0 | 0 | 100 |
| **MASTER TABLE** | **278** | **168** | **14** | **18** | **78** |

Master table: `data/search/web_search/search_results.csv`

---

## Key discoveries

### OEIS A006769 = item 223 (elliptic divisibility sequence)
- Question asks for the EDS associated with "37a1": y²+y=x³-x at point (0,0), for n=23..32
- OEIS A006769 gives exact values: `[-620297, 2382785, 7869898, 7001471, -126742987, -398035821, 1687054711, -7911171596, -47301104551, 43244638645]`
- Exact match with option A. All 3 teachers agree A. → GOLD.
- **For future OEIS items**: paste exact sequence description into Exa search, first result usually hits.

### Competition items solved by direct math (not web search)
All 4 competition items in batch 2 were solvable analytically without finding a source page:
- **Item 797** (AB=3, BC=2007, CA=2008 triangle): CD/DF=670 (C) via vector parametrization
- **Item 377** (polynomial 2006 distinct integer roots): min nonzero coefficients = 1004 = 4×251, largest prime factor = 251 (B) via Descartes rule
- **Item 471** (circumcircle APQ, BD=CE): m+n=43 (C) via power of a point
- **Item 597** (equal areas CBD/BAE/ACF): min area = 84 (B) via 120/b=112/a=104/c → sides 13,14,15

**AoPS web search returned no direct hits.** Lesson: for competition items, compute directly if the math is accessible.

### Item 141 — CONFLICT (flag for triage)
- Question: "alternating 1-0-1 numbers in base 7, how many are prime?"
- Computation: 1₇=1 (not prime), 101₇=50=2×25 (not prime), 10101₇=2451=3×19×43 (not prime). All composite.
- **Wolfram says 0.** All 3 teachers say A = \\boxed{1}. No 0 in options.
- Likely a textbook problem using old 1-is-prime convention, or the intended answer counts 1 as prime.
- Current best guess: teachers are right (A=1) because 0 is not an available option. But flag for Rain.

### ROI by source/method
1. **Direct math computation** — 100% yield, fastest. Works on all calculus, competition geometry, probability, LS approximation, entropy, etc.
2. **OEIS** — 100% yield when item is a known integer sequence. Go directly to OEIS.
3. **AoPS / competition web search** — 0% yield in batch 2 (Exa missed all 4 competition items). Compute directly instead.
4. **WeBWorK pattern items** — 100% yield via direct computation (all [ANS] items in batch 2 were solvable without web search).

### What teacher consensus alone covers
All 22 UNSEARCHED items in batch 2 had 3/3 teacher consensus BEFORE searching.
Direct computation confirmed all 21 GOLD items. Conclusion: 3/3 teacher consensus + direct computation ≥ web search for most item types. Web search adds value mainly for:
- OEIS/sequence items (exact verification)
- Competition problems with known source (e.g., AMC 1999 Problem 14 found on AoPS)
- Textbook problems where gold format matters (fractions vs decimals, etc.)

---

## PARTIAL/conflict items needing triage

| item_id | teacher answer | search/computation finding | status | action |
|---------|---------------|---------------------------|--------|--------|
| 141 | A (\\boxed{1}) | Wolfram: 0; all ≥50 are composite, 1 not prime | PARTIAL | Rain triage — is 1 prime in this context? |
| (batch 1 PARTIAL items) | see search_results.csv | — | PARTIAL | still need verification |

---

## Session 2 results — 2026-05-29 (claude_search_02 continued)

**Final master table totals: 245 GOLD / 15 PARTIAL / 18 NOT_FOUND / 0 UNSEARCHED**

Batch 3 (78 items): completed.

### Key conflicts discovered in session 2

**Item 7 — HMMT 2025 snakes problem (HIGH PRIORITY)**
- Teacher answer: 328 (conf=32, n=11 — very low confidence)
- HMMT 2025 Feb Comb #10 official solution: **448**
- Source: https://hmmt-archive.s3.amazonaws.com/tournaments/2025/feb/comb/solutions.pdf
- Formula: E₂ = 2(n²-1) for n=15 snakes → 448
- RECOMMENDATION: Use 448, not 328. Teachers are almost certainly wrong here.

**Item 141 (from session 1) — base-7 primes**
- Teacher answer: \boxed{1}
- Wolfram: 0 (1 is not prime by modern convention)
- All base-7 alternating numbers ≥50 are composite; 1 is not prime
- RECOMMENDATION: A=\boxed{1} is the intended answer (0 not available as option)

### High-value methodology notes

**OEIS items are fastest**: A006769 (item 223), A005379 (item 45), A061909 (item 91) all found with one Exa search.

**Competition items solve faster by computation than web search**: All 6 competition problems (797,377,471,597,930,78) were solved directly. AoPS searches returned no useful hits.

**Direct computation beats everything for standard math**: 
- Integrals, volumes, entropy rates, LS approximation, matrix determinants — all computed directly
- Statistics problems (ANOVA, paired t-test, CI) — computed with formula + numbers
- 90%+ of items resolved without any web search

### Items still flagged for triage (Rain)
| item_id | issue |
|---------|-------|
| 7 | teacher=328 vs HMMT_source=448. Recommend 448. |
| 141 | teacher=\boxed{1} vs Wolfram=0. Both defensible, 0 not an option. |
| 64 | conf=23.77 n=2 — very weak signal |
| 93 | teacher='sWith' — appears garbled/truncated |
