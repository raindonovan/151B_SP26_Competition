# TOOLING_RETIRED.md — the `search_with_tooling/` track (tried, failed, removed)

Created and removed 2026-05-29/30. Kept as a record so nobody re-spends effort on
the same dead end.

## What it was for

A third retrieval track for items where a real web page DOES state the answer but
our normal fetcher couldn't read it. Two specific walls motivated it:

1. **MathJax image-stripping.** Exa `web_fetch_exa` (and built-in WebFetch) return
   *rendered text only*. On AoPS-wiki the boxed final answer is a generated image /
   `<script type="math/tex">` tag, so the number comes back BLANK ("...the answer
   is .  "). The data is in markup the fetcher discards.
2. **Cloudflare bot-gating.** artofproblemsolving.com is behind Cloudflare: plain
   `curl` (any user-agent, even `action=raw` / `api.php`) gets a 403 challenge page.
   Exa's headless browser passes Cloudflare but then strips the math.

## What was tried (all verified in-sandbox, 2026-05-30)

- Sandbox HAS outbound network + `curl`, `python3`, `node` v24, `pandoc`.
- curl-reachable (HTTP 200), can fetch raw + parse LaTeX ourselves: oeis.org,
  kskedlaya.org, web.evanchen.cc, wiki.randommath.com.
- curl-BLOCKED (403, Cloudflare): artofproblemsolving.com — including `action=raw`.
- wiki.randommath.com renders answers as TEXT (good) but mirrors only OFFICIAL
  AIME/AMC, NOT the AoPS **Mock** contests (404).

## Why it failed

The only items that genuinely needed tooling were 3 **Mock-AIME** problems whose
answers live ONLY on AoPS (no non-Cloudflare mirror exists). Reading them needs a
real headless browser (Playwright) to beat Cloudflare AND read the rendered
MathJax — and even that may be defeated by Cloudflare from a datacenter IP.
Decision: not worth an `npm install playwright` + ~150MB browser + an outward-facing
bot-evasion attempt for **3 items**. Net GOLD from the track: **0**.

Note: every OTHER AoPS-hosted item was solved by swapping to a non-Cloudflare
mirror (Putnam->kskedlaya, IMO/TST->evanchen, official AIME->randommath) — which is
ordinary `regular_search`, not "tooling."

## The 3 items it was meant for (still `NOT_FOUND` in regular_search;
   answers exist on AoPS but are image+Cloudflare-gated)

- **173** Mock AIME 2 Pre-2005 P4 — 5^k (0<=k<=2004), 5^2004 has 1401 digits, how
  many begin with digit 1. CAUTION: do NOT assume 604 — that is the digit-count of
  2^2004 from a DIFFERENT problem (2004 AMC 12B P25, answer 195). Read the page.
- **486** Mock AIME 4 2006-07 P8 — incr seq a_1<=..<=a_10<=2007, a_i-i even,
  =C(m,n), m mod 1000. AoPS derivation = C(1008,10) -> m=1008 -> 8 (indicated).
- **471** Ray Li Mock Geo AIME 2011 P3 — tri ABC BC=9, BP=PQ=2, QC=5; circ APQ cuts
  AB,AC at D,E; BD=CE; AB/AC=m/n; find m+n. Options {41,45,43,47,49}.

## Cheapest way to actually finish these 3

A human opens the 3 AoPS pages in a browser and pastes the boxed numbers; verify
each against its option and flip to GOLD. Or a future agent on un-gated infra with
a real browser. Not worth automating from here.
