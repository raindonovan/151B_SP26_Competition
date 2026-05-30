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

## Pass 2026-05-29c (claude_vscode) — OEIS b-file mining (HIGHEST YIELD)

After confirming GOLD concentrates in NAMED problems, triaged the remaining
items by competition/OEIS fingerprint instead of going sequentially. The single
biggest source by far: items phrased

  "We now define an algorithm: The definition of a(n) is: <OEIS sequence name>...
   Given the input x_list (a series of values): [i1,i2,...,i10], determine the
   corresponding output sequence y_list."

These are OEIS sequences verbatim. Workflow that works (NO computation):
  1. Search the definition text -> identify the OEIS A-number (match the NAME
     verbatim; several seqs can share a name -> disambiguate by DATA, step 4).
  2. web_fetch the b-file: https://oeis.org/Annnnnn/bnnnnnn.txt
  3. Read a(i1)..a(i10) DIRECTLY off the b-file 'index value' lines.
  4. Match that exact value-list to exactly ONE option (programmatically, to
     avoid eyeball errors) -> that option letter is GOLD.

GOLD won this pass (19 OEIS items): 274 A001471, 711 A057963, 862 A065423,
940 A257993, 175 A003418, 255 A084480, 709 A001175, 266 A014126, 324 A007425,
518 A003986, 405 A000716, 647 A002329, 934 A055573, 675 A003485, 772 A090281,
596 A007433, 808 A193231, 663 A107920, 805 A190528, 874 A004515, 877 A077239,
305 A339378. (Plus non-OEIS named: 17 Putnam2015A2, 41 IMO2025P6, 47 MSE.)

Gotchas learned:
- BATCHED b-file fetches collide: two b-files with overlapping index ranges get
  concatenated into one text block; a dict keyed by index gets OVERWRITTEN by the
  second file. Fetch ONE b-file per call, or split blocks by their '# Bnnnnnn'
  header before parsing.
- ALWAYS match programmatically. Eyeballing a 10-element list against 10
  near-identical options (the wrong options are deliberately off-by-small-deltas)
  is error-prone; I mis-called item 266 by eye before the script corrected it.
- Same-name sequences: 'Bisection (odd part) of Chebyshev sequence with
  Diophantine property' names ~6 different OEIS seqs (A077239/43/44/45/46...).
  Disambiguate by which b-file's a(i1..i10) matches an option (A077244 failed,
  A077239 hit for item 877).
- The b-file index = the n in a(n) with the sequence's own OFFSET; honor it
  (most start n=0 or n=1; the x_list values ARE the indices to read).

NOT_FOUND OEIS items (no clean readable b-file / ambiguous / derived):
  88 (poly decomposition), 162 (floor(i/j) antidiag - only self-computable),
  402 (mult. floor((p+1)/2)), 434 (circle partition sizes 2&3),
  506 (mean of consecutive balanced primes - derived from A006562),
  873 (reversion of x(x-1)^2/(1-x+x^3)). For these the answer would require
  computing, which is forbidden -> honest NOT_FOUND.
