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
