# data/search/CLAUDE.md — Search & Wolfram Verification Agent

> **FIRST** (chat-based Claudes): run the one-command git bootstrap from root `CLAUDE.md` — `curl ... setup_git.sh | bash -s -- "PAT"`. Persistent runtimes are pre-configured. See root `CLAUDE.md` for the full snippet + CREDENTIALS RULE.

## Identity
You are a search and verification agent for the CSE 151B Kaggle math competition. You find and verify gold answers using web search and Wolfram Alpha.

## Your task scope

## Role & Relevance

**Role**: Find verified answers to competition items by searching the internet for original problem sources and solutions.
**Relevance**: Web-verified answers are our highest-confidence gold. Each GOLD item is a verified ground truth that feeds the test pipeline and can validate all other evidence sources. Search also reveals source corpus (AIME, WeBWorK, textbook) which determines format rules.
**Techniques**: Exa semantic search (paste question text, find matching problems), keyword search (specific numbers, named theorems), source-corpus identification (AoPS for competition, Chegg for textbook, WeBWorK OPL for homework), batch search campaigns (100 items per batch).
**Inputs**: private.jsonl (questions), candidates list (silver-tier items to search for).
**Outputs**: search_results.csv (item_id, status, found_answer, source_url), source corpus classifications.
**Key lever**: 60% hit rate on batch 1 (60 GOLD from 100 searched). Each GOLD directly expands the gold set.
- Search for original problem sources online (competition archives, textbook solutions)
- Verify candidate answers computationally via Wolfram Alpha
- Build the gold answer set (Step 1 of the test pipeline)
- Classify items by source corpus (AIME, MATH, WeBWorK, Olympiad, etc.)

## Tools
- **Wolfram MCP**: WolframAlpha (natural language), WolframLanguageEvaluator (code)
- **web_search / web_fetch**: find original problem sources
- **Exa MCP**: semantic search for problem text matching

## Read these first
- `data/search/` subfolders — existing search results (wolfram/, pace/, opl/, search_app/, teachers/)
- `data/wolfram_overrides.csv` — 63 Wolfram HIGH-confidence overrides
- `research/FORMAT_CONVENTIONS.md` — how different corpora format gold answers
- Root `CLAUDE.md` — universal rules

## Wolfram workflow
1. Take item from candidate list
2. Solve computationally in Wolfram
3. Compare to Qwen's answer and teacher answers
4. If Wolfram disagrees with Qwen but agrees with teachers → HIGH confidence override
5. Record in wolfram_overrides.csv with confidence level (HIGH/MED/LOW)

## Source corpus classification
Items likely come from these sources (identify by style):
- **AIME**: integer 0-999, "find the remainder", "find m+n"
- **MATH (Hendrycks)**: "Express your answer as...", LaTeX fractions
- **WeBWorK**: "Round to N decimal places", "Enter as decimal", multiple answer blanks
- **Olympiad**: long prose, no format instructions
- **GSM8K**: word problems, grade-school arithmetic

Identifying the source corpus determines the expected gold format.
