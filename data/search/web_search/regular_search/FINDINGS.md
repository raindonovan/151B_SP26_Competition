# data/search/web_search/FINDINGS.md

## Pass 2026-05-30f — TEXTBOOK-CONCEPT MCQ seam (new angle, +8 GOLD)

After the competition/OEIS veins were exhausted, a new angle paid off: the
CONCEPTUAL-FACT stats/math MCQs (which I'd bulk-skipped as "drills" in the first
sweep). These have a CANONICAL answer stated verbatim across multiple authoritative
pages (PSU/Emory/Laerd/AAPOR/LibreTexts/Wikipedia/Saylor), so they are genuinely
findable by plain web_search_exa — NO special tooling.

GOLD won this way (answer IS the stated fact, single-answer):
  252 one-way ANOVA conditions = C (indep/normal/equal-var)
  265 nominal-data central measure = mode (A)
  477 questionnaire: avoid leading questions (A)
  492 r=0.90 -> R^2 = 81% variation explained (A)  [R^2=r^2 stated verbatim]
  567 false statement = "intervals may overlap" (A)  [intervals must NOT overlap]
  813 CI impossible = non-normal+small+unknown-var (A)
  893 gender = qualitative variable (A)
  903 histogram area left of median = exactly 0.50 (A)

THE DISCIPLINE LINE (important — keep it):
- GOLD only when the ANSWER IS THE STATED FACT (a definition/property read straight
  off authoritative pages, single-answer).
- PARTIAL when the answer is a COMPUTED APPLICATION of a canonical fact, or a
  MULTI-SLOT assembly of per-statement facts:
    227 (df=pairs-1=9), 452 (chi2 df=(r-1)(c-1)=42)  [1-step application]
    319, 927 (multi-slot True/False over canonical identities)
    368 (4-slot function-notation interpretation; rule canonical, slots applied)
    60  (variable=age; canonical definition but option-selection is inference)
  -> these carry the indicated answer in found_answer for a downstream finish,
     but are NOT GOLD (would require me to compute/assemble).
- The "twin trap" still bites here: numeric template drills (potato-chip P-value,
  boat downstream, paint-room rates) appear online with RANDOMIZED/back-solved
  constants; the template is everywhere but OUR instance's stated answer is nowhere
  -> NOT_FOUND. (item 46's sd=20.3575072960673 is a back-solved constant: unfindable.)
- Seam now ~exhausted: the remaining NOT_FOUND concept-flagged items are
  computation problems (integrals, eigenvalues, determinants, prob densities) ->
  compute-track, not findable facts.

---

## search_results.csv = genuine web-search hits only

This file contains ONLY items where a verbatim web search returned a real
external source with the answer (source_url is a live URL). Everything that was
computed/solved locally, or copied from teacher consensus, has been removed —
those were never search results.

Count: 15 genuine hits **(STALE — this was the very first pass).** For the LIVE
tally always use `README.md` Status block (currently 57 GOLD / 13 PARTIAL /
873 NOT_FOUND, 2026-05-30). All counts elsewhere in this FINDINGS file and in
SCRATCH.md are per-pass historical snapshots, not the current state.

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

## Pass 2026-05-29d (claude_vscode) — named-competition prose items

Targeted the competition-prose (non-OEIS) items. GOLD when a MAJOR competition
problem is character-identical AND a real solution page states the answer:
- 285 = 735 : 2025 AIME I Problem 15 (Random Math Wiki states boxed 735).
- 312 = 171 : USA TST 2025 Problem 1, Ana/Banana (Evan Chen sols: 83+89-1=171).
- 125 = 8   : Putnam 2016 A1, l-th derivative div by 2016 (Putnam sols: j=8;
              option [6]=\boxed{8} verbatim).

NEW RULE (Rain, this pass) for IDENTIFIED-BUT-MODIFIED competition problems —
the source page states the governing FORMULA/RULE but a constant was changed or
a derived sub-question is asked, so the page does NOT state our exact value:
  -> search_status = PARTIAL. Record source + the stated rule/formula in
     found_answer/notes; DO NOT compute/pick the option. Leaves the strong
     signal for a downstream solver without drifting into computation.
  - 117 PARTIAL: Putnam 2021 A5 (E(z) div by 2021 IFF z not div by 42 nor 46);
    asks largest z<2021 -> 2020 indicated but left unpicked.
  - 286 PARTIAL: Putnam 2023 A1 (|p_x''(0)|=x(x+1)(2x+1)/6); threshold 89688.

FABRICATED-AGGREGATION trap (common in this corpus): a real base problem is
wrapped in a synthetic 'Sum_{n=a}^{b} S(n)' the original never asks. Even when
the base problem is found verbatim, the aggregate answer is stated nowhere and
computing it is forbidden -> NOT_FOUND. Examples: 83 (Turbo rotating-arrows,
base on Scribd IMO mock; Sum_{n=10}^{20} S(n) fabricated), 120 (k(n,p) +
Sum_{n=11}^{15} fabricated), 58 (altered FE + contrived sum). Record the base
problem's origin as a hint only.

Geometry-olympiad prose (95, 308, etc.) and original/synthetic olympiad items
(161, 198, 229, 235, 248, 275) almost never have a findable stated-answer page
-> NOT_FOUND. Don't over-invest; one targeted Exa search each is enough.

## Pass 2026-05-29e (claude_vscode) — batched 100-at-a-time sweep

Working the remaining ~700 in id-batches of 100. Batches 1 (ids 1-194) and 2
(ids 195-314): 0 GOLD each. This id range is the textbook-drill-heavy front;
its few findable gems were already harvested in earlier passes. The remaining
distinctive items here are COMPUTABLE TEXTBOOK MATH-FACTS (max genus of degree-4
curve in P^3 = Castelnuovo bound; # 3-sheeted covers of punctured torus = index-3
subgroups of F_2; log-telescope pair counts; cube-section pentagon areas; mixti-
linear/Sawayama-Thebault geometry) -- the THEORY is online but no page states our
exact numeric answer, so they're NOT_FOUND (computing the option is forbidden).

*** LEAK / CIRCULAR-SOURCE WARNING (NEW, important) ***
Item 250 (threnodic strings) was found verbatim in the HuggingFace dataset
**INSAIT-Institute/ProofRank** (tags 'apex_2025_10', also contains 'aime_2026_*'
entries with gold_answer fields). This is an AI-EVALUATION BENCHMARK that overlaps
our own competition's source corpus -- using its values would be CIRCULAR (same
failure mode as the JudgeBench HuggingFace leak noted for item 53). 
RULE: HuggingFace eval datasets (ProofRank/JudgeBench/AI-MO/olympiads/Apex), and
any "benchmark"/"dataset"/"gold_answer" aggregator, are FORBIDDEN as sources --
they may literally contain our private answers. Treat a hit there as NOT a source;
record NOT_FOUND. A real, independent solution page (archive PDF, AoPS wiki text,
MSE, OEIS b-file) is still required for GOLD. (RIMO benchmark also hit on item 383.)

*** TOOLING LIMITATION: AoPS wiki answers render as IMAGES, not text. ***
When Exa web_fetch_exa reads an artofproblemsolving.com/wiki page, all the LaTeX
(including the final boxed numeric answer) comes back BLANK/stripped -- only the
prose survives. So for AIME/Mock-AIME items whose answer lives on AoPS, I can
read the DERIVATION but not the explicit number. Consistent handling: record
PARTIAL (source identified + derivation/binomial stated; the indicated option
noted) rather than GOLD. Examples this pass: 173 (Mock AIME 2 P4 -> 604),
486 (Mock AIME 4 2006-07 P8 -> C(1008,10), m mod 1000 = 8 = opt[1]),
471 (Ray Li Mock Geo AIME P3, only the problem PDF found, no answer).
NEXT-AGENT TIP: to convert these PARTIALs to GOLD, fetch the answer from a
NON-AoPS mirror that renders numbers as text (Random Math Wiki wiki.randommath.com
worked for 285/312; some pages on artofproblemsolving COMMUNITY threads, or a
Google cache) -- or read the AoPS page in a browser. The PARTIAL rows already
carry the identified source + the indicated option.

## Pass 2026-05-29e batches 4+: ids 419-525 (batch 4)
2 PARTIAL (471 Ray Li geo, 486 Mock AIME 4 P8), rest NOT_FOUND. Searched 471,
486, 488 (Turbo-Linetown, no source). This range has several real AIME/Mock-AIME
problems but their answers are AoPS-image-gated -> PARTIAL not GOLD.
