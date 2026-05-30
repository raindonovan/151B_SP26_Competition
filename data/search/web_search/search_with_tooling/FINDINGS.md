# search_with_tooling/FINDINGS.md

## What this folder is

This is the **TOOLING-assisted retrieval** track. It is a sibling of
`../regular_search/` (plain Exa web search/fetch) and `../search_with_compute/`
(answers obtained by computing). Same CSV schema, same GOLD bar.

The ONLY difference from regular_search is the *retrieval mechanism*. The rule is
unchanged: **GOLD = a real web page LITERALLY STATES the answer to THIS problem,
read verbatim.** Tooling does NOT relax that — it just gets past walls that made a
genuinely-stated answer unreadable to the plain Exa fetcher.

Tooling is for retrieval ONLY. It must NEVER be used to compute, simplify, or
derive an answer. If the page does not state the value, it stays NOT_FOUND /
PARTIAL here too — exactly as in regular_search. Computed answers go in
`../search_with_compute/`, never here, and are never labeled GOLD.

## Why this track exists (the tooling gap, diagnosed 2026-05-29)

Two concrete failure modes blocked regular_search even when the answer WAS on the web:

1. **MathJax image-stripping.** Exa `web_fetch_exa` and built-in WebFetch return
   *rendered text only*. On AoPS-wiki and similar MediaWiki+MathJax sites the final
   boxed answer is a generated image / `<script type="math/tex">` tag, so the number
   comes back BLANK ("...the answer is .  "). The data is in the markup the fetcher
   discards. Affected PARTIALs: 173 (Mock AIME 2 Pre-2005 P4), 486 (Mock AIME 4
   2006-07 P8), 471 (Ray Li Mock Geo AIME 2011 #3).

2. **Cloudflare bot-gating.** AoPS sits behind Cloudflare. A bare `curl` (any
   user-agent) and even the MediaWiki `api.php` return a 403 / "Attention Required"
   challenge page. Exa's headless browser DOES get through Cloudflare (that's why
   Exa can render AoPS at all) — it just strips the math afterward.

## Environment facts (verified 2026-05-29, this sandbox)

- Outbound network works from the sandbox: `curl https://oeis.org/... -> HTTP 200`.
- Local tools present: curl 7.81, python3 3.10, node v24, pandoc 2.9. (No lynx/w3m/jq.)
- Hosts that answer plain curl (NO Cloudflare) -> fetch raw + parse LaTeX ourselves:
    oeis.org (200), kskedlaya.org (200), web.evanchen.cc (200),
    wiki.randommath.com (200).
- Hosts that BLOCK plain curl: artofproblemsolving.com (403, Cloudflare).

## Retrieval toolbox (in order of preference / effort)

T1. **curl | python on non-Cloudflare mirrors.** For OEIS / Putnam-archive
    (kskedlaya) / Evan Chen / Random Math Wiki / MSE / arXiv, fetch the RAW HTML
    with a browser UA and parse the LaTeX/answer out with a regex
    (\\boxed{...}, math/tex tags, "the answer is X"). This recovers numbers Exa
    drops. Zero install. PROVEN: pulled A007694 raw HTML + its sequence inline.
    -> This already converted item 644 (PARTIAL->GOLD via OEIS A007694 b-file:
       count of n<=2010 with phi(n)|n = 41, read as the 41st term).

T2. **Mirror-swap for AoPS-only AIME items.** Most AoPS answers have a
    non-Cloudflare twin: Putnam->kskedlaya, IMO/TST->evanchen, AIME->
    wiki.randommath.com (renders numbers as TEXT; this is why items 285/312
    converted but 173/486/471 did not — randommath just wasn't curl'd directly).
    For a stuck AoPS PARTIAL, find + fetch its randommath / non-AoPS equivalent.

T3. **Headless browser (heavier; needs install + approval).** node is present;
    `npx playwright` / puppeteer drives real Chromium that (a) solves the
    Cloudflare JS challenge and (b) reads the rendered MathJax alt/aria-label
    text. This is the only path for items that exist ONLY on AoPS with no mirror.
    Requires `npm install playwright` + a ~150MB browser download -> get Rain's OK
    before installing/running.

## Status / log

(rows recorded in search_results.csv; running notes here)

- Track created 2026-05-29. Folder structure: regular_search / search_with_tooling
  / search_with_compute, all siblings under web_search/.
- First convertible target list (regular_search PARTIALs that are a tooling, not
  knowledge, gap): 173, 471, 486 (AoPS image-strip -> try randommath/mirror via T1/T2),
  286/117 are NOT tooling-fixable (page states rule/formula, not our value -> would
  require compute -> belong in search_with_compute or stay PARTIAL), 7 is a human
  source-conflict call.
