# data/search/web_search/FINDINGS.md

## search_results.csv = genuine web-search hits only

This file contains ONLY items where a verbatim web search returned a real
external source with the answer (source_url is a live URL). Everything that was
computed/solved locally, or copied from teacher consensus, has been removed —
those were never search results.

Count: 15 genuine hits.

Sources that produced hits: OEIS (sequence items), AoPS/Putnam/HMMT archives
(competition items), MathWorld, Math StackExchange, a few course-PDF/homework
sites. Most of the 943 questions (textbook [ANS] bank problems and original
competition problems) do NOT surface by verbatim search and are correctly absent.

## Pass 2026-05-29b (claude_vscode) — sequential 0..55

Worked sequentially from item 0. New GOLD this pass:
- item 17: Putnam 2015 A2 (a_n=4a_{n-1}-a_{n-2}, odd prime factor of a_2015).
  kskedlaya.org putnam-archive 2015s.pdf states "One possible answer is 181";
  181 is a verbatim option. Source = official Putnam solution PDF.
- item 41: IMO 2025 Problem 6 (2025x2025 Matilda tiles). Evan Chen
  IMO-2025-notes.pdf states "The answer is 2112 = 2025+2*45-3". Free-form.
- item 47: 2^m | 3^m-1. MSE 2563956 states solutions {0,1,2,4}; option "1,2,4"
  is the verbatim natural-number subset (0 = n=0 edge case excluded).

MCQ-mapping rule in force (Rain, this pass): record an option only when a real
page's stated value matches exactly ONE option VERBATIM. NO algebraic
equivalence, NO computation to pick a letter.
- This killed item 10 (the |dz|/|z-a|^2 integral): MSE gives 2*pi*rho/|rho^2-|a|^2|,
  a real source, but the options are piecewise LaTeX forms — choosing E needs
  algebraic equivalence -> NOT_FOUND. Recorded the source as origin hint only.
- Item 19 (j_155 variant of Putnam A2): page answers a_2015, not j_155 ->
  NOT_FOUND even though 181 is an option.

Patterns confirmed:
- GOLD concentrates in NAMED competition problems (Putnam/IMO/AIME archives,
  Evan Chen notes) and famous textbook problems (Cover&Thomas, classic MSE
  integrals/sequences). Search by the distinctive setup, then fetch the
  archive/solution PDF to read the stated answer.
- The vast majority of items are generic textbook drills (order of operations,
  ANOVA/z-test computation, mixture/ratio word problems, basic trig) that have
  NO unique findable source -> correctly NOT_FOUND. ~1 GOLD per ~15-20 drill-
  heavy items.
- Aggregator/eval-dataset hits (HuggingFace JudgeBench, problem banks) are NOT
  valid sources — possibly circular with our own corpus, and paywalled solution
  sites (Transtutors/Chegg/CourseHero) usually hide the numeric answer.
- Close-but-different numbers are the main trap: many drills have near-twins
  online with different constants (e.g. item 2 Pepsi 100/65 vs our 120/52).
  Different constants -> NOT_FOUND, never "close enough".
