# search_with_tooling/ — retrieving STATED answers past render/access walls

Sibling of `../regular_search/`. **Same GOLD bar, same schema.** The ONLY
difference is the retrieval *mechanism*: this track uses extra tooling (raw-HTML
curl, LaTeX parsing, headless browser) to read an answer that a real web page
DOES state but that the plain Exa fetcher could not return.

Tooling is for RETRIEVAL ONLY. It never computes/derives an answer. If the page
doesn't state our value, it's NOT_FOUND/PARTIAL here too. Computed answers belong
in `../search_with_compute/`, never here.

## Why this track exists — the tooling gap (diagnosed 2026-05-29, verified)

Two walls blocked `regular_search` even when the answer WAS on the web:

1. **MathJax image-stripping.** Exa `web_fetch_exa` (and built-in WebFetch) return
   *rendered text only*. On AoPS-wiki the boxed final answer is a generated image /
   `<script type="math/tex">` tag, so the number comes back BLANK. The data is in
   markup the fetcher discards.
2. **Cloudflare bot-gating.** AoPS sits behind Cloudflare: plain `curl` (any UA,
   even `action=raw` / `api.php`) gets a 403 challenge page. Exa's headless browser
   DOES pass Cloudflare — it just strips the math afterward.

Verified environment facts (this sandbox): outbound network works; `curl`,
`python3`, `node` v24, `pandoc` present (no Playwright/browser installed).
curl-reachable (200): oeis.org, kskedlaya.org, web.evanchen.cc, wiki.randommath.com.
curl-BLOCKED (403, Cloudflare): artofproblemsolving.com.

## Toolbox (in order of effort)

- **T1 — curl | python on non-Cloudflare mirrors.** Fetch RAW HTML (browser UA),
  regex out `\boxed{...}` / `math/tex` / "the answer is X". Recovers numbers Exa
  drops. Zero install. (This is how item 644 converted via the OEIS A007694 b-file.)
- **T2 — mirror-swap for AoPS items.** Most AoPS answers have a non-CF twin:
  Putnam->kskedlaya, IMO/TST->evanchen, OFFICIAL AIME/AMC->wiki.randommath
  (renders numbers as text — why 285/312 converted). NOTE: randommath does NOT
  carry AoPS **Mock** contests (404), which is why 173/486/471 are stuck.
- **T3 — headless browser (needs install + approval).** `npx playwright` drives
  real Chromium that (a) solves the Cloudflare challenge and (b) reads rendered
  MathJax alt-text. Only path for AoPS-only items with no mirror. Requires
  `npm install playwright` + ~150MB browser download -> get Rain's OK first
  (and Cloudflare may still defeat vanilla Playwright).

## CSV schema (same as regular_search)

```
item_id,category,search_status,found_answer,source_url,source_type,confidence,notes
```

## search_status values

- `GOLD` / `PARTIAL` / `NOT_FOUND` — same meaning as regular_search.
- `BLOCKED_NEEDS_PLAYWRIGHT` — tooling-specific: the answer IS on AoPS (identified,
  derivation visible) but is both Cloudflare-gated to curl AND MathJax-image-
  stripped, with no non-Cloudflare mirror. Requires T3. The blocker + indicated
  answer are noted so a browser-capable agent can finish in seconds.

## Status (2026-05-30)

3 rows, all `BLOCKED_NEEDS_PLAYWRIGHT` (Mock-AIME items, AoPS-only):
- 173 Mock AIME 2 Pre-2005 P4 (5^k leading-digit-1 count) — CAUTION: do NOT assume
  604; that is the digit-count of 2^2004 from a DIFFERENT problem (2004 AMC 12B P25,
  ans 195). Read the page, don't recall.
- 486 Mock AIME 4 2006-07 P8 (incr seq; C(1008,10) -> m mod 1000 = 8 indicated).
- 471 Ray Li Mock Geo AIME 2011 P3 (m+n, options {41,45,43,47,49}).

Decision (2026-05-30): Playwright NOT installed — payoff is 3 items, success vs
Cloudflare uncertain, and it's an outward-facing bot-evasion action. Cheapest fix
is a human opening the 3 AoPS pages in a browser and pasting the boxed numbers.
