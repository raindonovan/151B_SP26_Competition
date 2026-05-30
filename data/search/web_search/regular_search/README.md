# regular_search/ — plain web-search retrieval (the canonical baseline)

The original, full-coverage track: every one of the 943 items has a row here,
found via Exa `web_search_exa` (semantic) + `web_fetch_exa` (read the page). This
is the **canonical search-GOLD file** that downstream scripts consume.

See `../README.md` for the shared GOLD rule and the 3-track overview.

## Files

- `search_results.csv` — one row per item (the deliverable).
- `FINDINGS.md` — patterns, source playbook, gotchas, leak warnings (read this).
- `SCRATCH.md` — low-friction capture + per-pass signoffs.

## CSV schema

```
item_id,category,search_status,found_answer,source_url,source_type,confidence,notes
```

- `item_id` — 0..942, matches `private.jsonl` id (UNPADDED).
- `category` — FREE or MCQ.
- `search_status` — see below.
- `found_answer` — the answer AS STATED on the page (GOLD/PARTIAL only; else blank).
- `source_url` — the exact page that states it (REQUIRED for GOLD).
- `source_type` — e.g. oeis, math.stackexchange, putnam_archive, aops, textbook_stats.
- `confidence` — match confidence (>=90 for GOLD).
- `notes` — match reasoning, mirror used, paywall flags, origin hints.

## search_status values

- `GOLD` — a real page states this exact problem's answer; >=90% match; verbatim.
- `PARTIAL` — source + governing rule/formula identified, but the page does NOT
  state our final value (e.g. constant changed, or a multi-slot answer only
  partly resolved). The indicated answer/option is noted for a downstream finish.
  No computing to close it.
- `NOT_FOUND` — searched honestly; no qualifying page. (The correct result for
  the large majority — most items are textbook-bank drills with no findable page.)

## Where GOLD comes from (proven veins)

1. **OEIS b-files** — for "We now define an algorithm: a(n) is <OEIS name>... x_list
   [...]" items: identify the A-number, read a(x_list) off the b-file, verbatim-
   match to one option. ~22 GOLD. Also count-type items (e.g. 644: #{n<=2010 :
   phi(n)|n} = 41st term of A007694).
2. **Named-competition solution PDFs** — Putnam (kskedlaya), IMO/TST (Evan Chen),
   HMMT archive, AIME (Random Math Wiki). Fetch the whole SOLUTIONS pdf; it often
   states several of our items at once (HMMT 2025 Feb Team gave 799 + 376).
3. **Famous-problem pages** — Math StackExchange / MathWorld for textbook classics
   (Burnside cube=23 item 719, LTE=103 item 668).
4. **Textbook CONCEPT MCQs** — canonical facts stated identically across
   authoritative pages (one-way ANOVA conditions=252, nominal->mode=265, avoid
   leading questions=477). These ARE findable.

## What is NOT findable (correctly NOT_FOUND)

- **Numeric textbook template drills** — the web hosts the same template with
  RANDOMIZED / back-solved constants (e.g. the "potato chip / P-value" family, the
  "boat downstream/upstream" family). The template is everywhere; OUR exact-number
  instance's stated answer is nowhere. Different constants -> NOT_FOUND, never the twin.
- **Synthetic / fabricated-aggregation items** (a real base wrapped in a made-up
  Sum_{n=a}^{b}); original/geometry olympiad prose; variant indices of a known comp.

## Status (2026-05-30): 60 GOLD / 14 PARTIAL / 869 NOT_FOUND (943 searched).

This block is the SOURCE OF TRUTH for the live tally (verify against the CSV with:
`python3 -c "import csv,collections;print(collections.Counter(r['search_status'] for r in csv.DictReader(open('search_results.csv'))))"`).
Per-pass snapshots in SCRATCH.md/FINDINGS.md are historical and NOT current.

GOLD ids: 7 17 33 41 45 47 91 97 125 175 182 184 200 204 222 223 252 255 263 265 266
274 285 305 312 324 329 376 405 440 474 477 492 518 549 567 570 596 644 647 663 668 675
709 711 719 772 778 799 805 808 813 856 862 874 877 893 903 934 940.
PARTIAL ids: 60 117 173 227 286 319 368 452 471 486 603 927.

(2026-05-30 second pass: 7 promoted PARTIAL->GOLD = 448/3 from HMMT 2025 Feb Comb sols PDF;
778 Hail-Mary GOLD = 0.685 from Molecular Driving Forces; 549 GOLD via OEIS A000161 b-file.
OEIS 2nd-pass on 88/402/434/506/873 confirmed NOT_FOUND — descriptors map to no clean
named entry/b-file. 173/471/486 remain AoPS image+Cloudflare-gated -> human-browser handoff.)
