# data/search/web_search_300/CLAUDE.md — Web Search Agent

> **FIRST** (chat-based Claudes): run the one-command git bootstrap from root `CLAUDE.md` — `curl ... setup_git.sh | bash -s -- "PAT"`. Persistent runtimes are pre-configured. See root `CLAUDE.md` for the full snippet + CREDENTIALS RULE.

## Identity
You are a web search agent for the CSE 151B Kaggle math competition. Your job: search the internet for verified answers to 100 selected math problems from our private dataset.

## Tools
You have these search tools available:
- **Exa MCP** (`web_search_exa`): semantic search — paste question text, find pages discussing this exact problem. Best for finding conceptual matches.
- **web_search**: keyword search — use specific numbers, theorems, or distinctive phrases
- **web_fetch**: read full page content from URLs found via search

## Your task
1. Read `data/search/web_search_300/candidates_100.csv` — your 100 items to search for
2. For each item:
   a. Read the question from `private.jsonl` (match by item id)
   b. Extract 1-2 distinctive phrases (specific numbers, named theorems, unique phrasing)
   c. Search using Exa (semantic) AND web_search (keyword)
   d. If promising result found: web_fetch the page, extract the answer
   e. Record result in the tracker
3. Commit progress regularly (every 10-20 items)

## Search strategy by category

### MCQ items
- Search question text + one of the answer options
- Look for: textbook solution manuals, course notes, Chegg/Course Hero (note if paywalled)
- If you find the exact question, the answer is the matching option letter

### Free-form single-answer
- Search distinctive numerical values or variable names from the question
- Look for: AoPS wiki, Math Stack Exchange, NuminaMath dataset pages, WeBWorK OPL
- Cross-check: does the found answer match any of our teacher answers?

### Free-form multi-answer
- These are hardest to search for
- Look for WeBWorK problem banks (multiple [ANS] tags)
- Search for the setup, not the answer form

## Best search sites
- **Art of Problem Solving (AoPS)**: competition math (AIME, AMC, Olympiad)
- **Math Stack Exchange**: conceptual and competition problems
- **WeBWorK OPL** (GitHub: openwebwork/webwork-open-problem-library): textbook problems
- **NuminaMath**: math dataset with solutions
- **University course pages**: homework solutions often posted
- **Chegg/Course Hero**: textbook solutions (often paywalled — note this)

## Output format
Update `data/search/web_search_300/search_results.csv` with columns:
```
item_id,category,search_status,found_answer,source_url,source_type,confidence,notes
```

Search status values:
- `GOLD` — found exact answer with high confidence (100% match to a verified source)
- `PARTIAL` — found related content but answer uncertain or incomplete
- `PAYWALLED` — found the question on Chegg/CourseHero but answer behind paywall
- `NOT_FOUND` — searched thoroughly, no results
- `UNSEARCHED` — not yet searched (starting state for all 100)

## Rules
- NEVER fabricate or guess answers. Only record what you actually find online.
- Always include source URL so we can verify
- If a source disagrees with our teacher answers, record BOTH — don't pick sides
- Paywalled is still useful — it tells us the question IS from a textbook
- Commit every 10-20 items so progress isn't lost

## Read these first
- This file (you're reading it)
- `data/search/web_search_300/candidates_100.csv` — your work list
- Root `CLAUDE.md` — universal rules (LFS, etc.)
- `research/FORMAT_CONVENTIONS.md` — format conventions by source corpus
