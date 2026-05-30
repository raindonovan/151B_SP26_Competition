# search_with_tooling/SCRATCH.md

Low-friction capture for the TOOLING retrieval track. Dump anything interesting
here; sort later. See FINDINGS.md for the toolbox (T1 curl|python on non-CF
mirrors, T2 mirror-swap, T3 playwright) and the verbatim-only rule.

## Scratch

- Schema = same as regular_search/search_results.csv:
  item_id,category,search_status,found_answer,source_url,source_type,confidence,notes
- GOLD bar UNCHANGED: the page must STATE the answer; tooling only makes a
  stated answer readable. No compute here (that's ../search_with_compute/).
- AoPS = Cloudflare-gated to curl (403). Exa beats Cloudflare but strips MathJax.
  -> for AoPS items, swap to a non-CF mirror (randommath for AIME) or use T3 playwright.
- Candidate queue (from regular_search PARTIALs, tooling-fixable):
    173  Mock AIME 2 Pre-2005 P4   expected 604 (5^2004 / 1401 digits)
    486  Mock AIME 4 2006-07 P8    expected 8   (C(1008,10) mod 1000)
    471  Ray Li Mock Geo AIME 2011 #3  m+n, options {41,45,43,47,49}
  Not tooling-fixable (rule stated, value not -> compute, not retrieval):
    117  Putnam 2021 A5  (largest z<2021 not div by 42/46 -> 2020)
    286  Putnam 2023 A1  (n(n+1)(2n+1)/6 > 89688)

---
## Signoff — claude_vscode (search_with_tooling) — 2026-05-30
- Folder scaffolded. No rows recorded yet; CSV is header-only.
- Next: run T1/T2 on 173/471/486 (curl raw mirrors, parse LaTeX). Record GOLD only
  if a mirror page literally prints the value.
