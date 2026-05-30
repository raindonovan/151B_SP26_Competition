> LIVE TALLY lives in `README.md` Status block: **57 GOLD / 13 PARTIAL /
> 873 NOT_FOUND** (2026-05-30). Every per-pass count BELOW in this file is a
> historical snapshot from that pass (e.g. "138/943: 42 GOLD") — accurate for its
> date, NOT the current state. Do not read them as live.

---
## Signoff — claude_search/vscode — 2026-05-29
### What I did
- Completed full 943-item coverage of search_results.csv (was 377, now 943).
- Genuinely computed/verified the T4 priority items: 18 MCQ + 36 single-answer + ~40 multi-answer (OEIS, Putnam/AoPS, direct math).
- Cross-referenced the remaining 566 from MASTER_ANSWERS teacher consensus / answer-sheet, honestly labeled by source_type and confidence.
### Status: 635 GOLD / 277 PARTIAL / 31 NOT_FOUND
### Key flags for triage
- Item 7: HMMT 2025 official = 448, teacher = 328. Use 448.
- Item 141: Wolfram = 0, teacher = \boxed{1}. 0 not an option -> likely \boxed{1}.
- Items 445, 786: computed values not in MCQ option sets (possible transcription issue).
- 31 NOT_FOUND are hard olympiad (161,198,199,229,250,275,312,376,422,...).
### Caveat for next agent
317 "GOLD" rows are teacher_consensus cross-refs, NOT independent web verification. Do not over-trust. The ~249 PARTIAL weak-consensus items are where independent solving would most improve the answer sheet.

---
## Signoff — claude_vscode (web_search) — 2026-05-29 (pass b, sequential 0..80)
- Covered items 0 through 80 sequentially (skipping the 15 pre-existing genuine
  hits: 7,33,45,91,97,182,184,200,204,222,223,263,440,474,570).
- Stopped at: item 80. Next unsearched id = 81 (skip 91 which has a row).
- New GOLD this pass (3): 
  - 17 = 181 (Putnam 2015 A2 official solution PDF, verbatim option)
  - 41 = 2112 (IMO 2025 P6, Evan Chen notes "answer is 2112", free-form)
  - 47 = "1,2,4" (MSE 2^m|3^m-1 solutions {0,1,2,4}; natural-number subset = option)
- Everything else 0..80 = NOT_FOUND (honest). This region is ~95% generic
  textbook drills (order-of-ops, z-test/ANOVA computation, mixture/ratio word
  problems, basic trig) with no unique findable source, plus a few SYNTHETIC
  competition variants (item 58 altered FE; item 19 j_155 variant) that don't
  exist online.
- RULE APPLIED (Rain, this session): record an MCQ option ONLY when a real
  page's stated value matches exactly ONE option VERBATIM. No algebraic
  equivalence, no computing a letter. This downgraded item 10 (real integral
  source, but piecewise-formula options) and item 78 (plane verified on Shaalaa,
  but the asked quantity 5*sqrt2*d is not stated) to NOT_FOUND.
- See FINDINGS.md "Pass 2026-05-29b" for the GOLD-source patterns.

---
## Signoff — claude_vscode (web_search) — 2026-05-29 (pass c, OEIS mining)
- Switched from sequential to FINGERPRINT-TARGETED searching (Rain's call: focus
  by findings). Triaged all remaining items for OEIS/competition signatures.
- BIG WIN: the "We now define an algorithm: definition of a(n) is <name>... x_list
  [...]" items are OEIS sequences verbatim. Read the b-file, match a(x_list) to an
  option programmatically. 22 OEIS GOLD this pass.
- GOLD count: 15 (session start) -> 39 (now). New: 17,41,47 (named comps) +
  OEIS: 175,255,266,274,305,324,405,518,596,647,663,675,709,711,772,805,808,
  862,874,877,934,940.
- NOT_FOUND OEIS (couldn't read a clean/unambiguous b-file, computing forbidden):
  88,162,402,434,506,873; also 911 (icosahedron-teleport, no matching page).
- METHOD NOTE for next agent: fetch ONE b-file per call (batched fetches collide
  on overlapping indices), and ALWAYS match the value-list to options with a
  script - the distractor options are off-by-tiny-deltas and fool the eye.
- STILL TO DO: many OEIS-fingerprint items remain unsearched in the triage list
  (e.g. 711-done, but 88/402/434/506/873 need a better OEIS hit; plus the
  competition-prose items 919,636,629,510,823,856,235,911 are mostly hard/original
  olympiad - likely NOT_FOUND but worth a quick AoPS/archive check). Generic-drill
  items 81-942 not individually searched (low yield, per established pattern).
- See FINDINGS.md "Pass 2026-05-29c" for the full b-file workflow + gotchas.

---
## Signoff — claude_vscode (web_search) — 2026-05-29 (pass d, named comps)
- Worked the competition-prose items. GOLD count 39 -> 42.
- New GOLD: 285 (2025 AIME I P15=735), 312 (USA TST 2025 P1=171), 125 (Putnam
  2016 A1=8, verbatim option). New PARTIAL: 117 (Putnam 2021 A5), 286 (Putnam
  2023 A1) - source+rule recorded, option left for downstream per Rain's call.
- NEW STATUS VALUE in use: PARTIAL = identified comp + page states rule/formula
  but not our exact value (modified constant / derived sub-question). Don't
  compute the option; record the source+rule.
- Coverage now 138/943 searched: 42 GOLD, 3 PARTIAL, 93 NOT_FOUND.
- Remaining unsearched ~805 are dominated by generic textbook drills (very low
  yield) + a tail of original/geometry olympiad prose (no stated-answer pages)
  + fabricated-aggregation items (base real, Sum synthetic -> NOT_FOUND).
- BEST NEXT MOVES if continuing: (1) any leftover items whose text names a major
  competition (AIME/IMO/USAMO/Putnam/TST/HMMT) - fetch the archive/Evan-Chen
  sols. (2) re-scan for OEIS phrasing in case any slipped the triage. Generic
  drills 81-942 remain individually unsearched by design (established ~0 yield).
- See FINDINGS.md "Pass 2026-05-29d".

---
## Signoff — claude_vscode (web_search) — 2026-05-29 (pass e, FULL 943 sweep COMPLETE)
- ALL 943 items now have a row in search_results.csv. Final: 48 GOLD / 7 PARTIAL / 888 NOT_FOUND.
- Swept the remaining ~800 in 8 batches of ~100 (id order). New GOLD found in the
  sequential sweep (back half, ids 629+): 668 (v2 LTE=103, MSE), 719 (cube 2-color
  Burnside=23, MSE), 799 (HMMT2025 Feb Team#4 rooks=8096), 376 (HMMT2025 Feb Team#10
  gcd; UPGRADED from earlier NOT_FOUND), 856 (Putnam2022 A5=290). New PARTIAL: 471
  (Ray Li geo), 486 (Mock AIME4 P8), 644 (phi(n)|n), 173/117/286 earlier.
- KEY LESSON: competition SOLUTIONS PDFs (Putnam kskedlaya, HMMT archive) render as
  readable TEXT and often contain MULTIPLE of our items -> fetch the whole sols PDF.
  Reading HMMT 2025 Feb Team sols gave 2 GOLD (799, 376) at once.
- KEY BLOCKER: AoPS wiki answers are LaTeX IMAGES -> stripped by Exa text fetch.
  AIME/Mock-AIME items whose answer only lives on AoPS are PARTIAL not GOLD (173,486,471).
  Next agent: re-fetch those from Random Math Wiki (renders text) or a browser to GOLD them.
- FORBIDDEN sources confirmed (do NOT use): HuggingFace ProofRank/RIMO/JudgeBench/
  AI-MO benchmarks (circular with our corpus) - hit on 53, 250, 383.
- The 7 PARTIAL rows carry identified source + indicated option for downstream completion.
- Exa MCP token expired mid-session once; Rain re-authorized. If it dies again, page-
  reading stops (WebSearch snippets alone are NOT enough to read answers verbatim).

---
## Signoff — claude_vscode (web_search) — 2026-05-30 (pass: playbook 2nd-pass)
### What I did
- Executed Rain's ranked playbook. Item 7 already promoted PARTIAL->GOLD = 448/3
  (HMMT 2025 Feb Comb sols PDF, dropped "/3" corrected).
- OEIS descriptor 2nd-pass on 88, 402, 434, 506, 549, 873 (descriptor/g.f./
  transform-name searches, not x_list format).
### What worked
- **549 -> GOLD**. "Number of ways to write n as sum of two squares, allowing
  permutations" = OEIS A000161 ("partitions of n into 2 squares"). b-file
  a(98..107)=[1,0,2,1,0,0,1,0,1,0] uniquely matches option idx 9 VERBATIM
  (programmatic). Earlier pass mis-tried A000925 (has a 4, no match) and gave up.
  LESSON: when a descriptor is ambiguous among OEIS entries, enumerate candidate
  A-numbers and b-file-match ALL of them to the options before declaring NOT_FOUND.
### What didn't work (confirmed NOT_FOUND, 2nd-pass)
- 88 (n*(x+..+x^q) into k polys), 402 (mult. a(p)=floor((p+1)/2)),
  434 (circle pts into size-2/3 subsets), 506 (mean of consec balanced primes),
  873 (reversion of x(x-1)^2/(1-x+x^3)). Each descriptor maps to NO clean named
  OEIS entry with a readable b-file. Searches returned only different sequences.
### Status: 60 GOLD / 14 PARTIAL / 869 NOT_FOUND (README synced, source of truth).
### What's left (handoffs, NOT in-sandbox)
- 173 / 471 / 486: answers exist on AoPS but are MathJax-image + Cloudflare-gated.
  Cheapest fix = human opens the 3 AoPS pages in a browser, pastes boxed numbers,
  verify vs option, flip to GOLD. See ../TOOLING_RETIRED.md for the exact items.
- PARTIALs 117/286 (Putnam) and the rule-application set (60/227/319/368/452/603/927)
  correctly stay PARTIAL: page states the RULE/formula, not our exact value;
  closing them needs computation (forbidden for this agent), per Rain's playbook #5.
