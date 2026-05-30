# Signal Audit — Status & Handoff (2026-05-30)

Goal: audit the 3 answer-sheet signal sources (TEACHERS, WOLFRAM, SEARCH) on their
RAW data before building any answer sheet. The sheet is the gate to inference.
No clean ground truth exists for the 943-item set — every reliability number is an
estimate from partial, fallible proxies. Say so.

## Current state of the 3 audits
1. TEACHERS — in progress. Per-LLM raw + re-extracted answers live in
   data/search/teachers/{sonnet,gpt4,oss,xhigh}/ (item_XXXX.md + answers.csv),
   pulled fresh from DataApp (commit f470416). No joined sheets (binned, see below).
   - ChatGPT teacher audit: prompt drafted; must read the per-LLM answers.csv (NOT
     the old compact, which is archived). Use value-equality (scripts/gold_equiv.py),
     beware the conformity trap, build any proxy-gold from INDEPENDENT sources only.
2. WOLFRAM — pending. ChatGPT audit prompt fired (repo-aware, reads all of
   data/search/wolfram/ incl. notes/FINDINGS/TODO; uses notes column; outputs one
   fenced CSV block). strategy is ALSO doing its own Wolf audit in parallel.
   Handoff back via data/search/wolfram/CHATGPT_AUDIT_PASS2.md (push), then diff here.
3. SEARCH — not started. Verify the 43 GOLD are real web hits (real source_urls,
   answer matches source), not the computed/copied contamination caught before.
   Also: a new search/search_with_tooling track was RETIRED (0 GOLD, afb85fb).
   And check item 41 (Wolfram/websearch HIGH "2112" vs all teachers ~3986/4048).

## Teacher data quality (found, pre-audit)
Missing/corrupted extractions by teacher (usable counts):
- gpt4: 171 blank, items 267-449 — GENUINE RateLimitError in raw .md (not extraction
  bug). Needs Batch-API rerun. usable 772/943. WORST.
- oss: 7 blank (95,187,405,467,498,506,525) — raw is prompt-template only. usable 936.
- sonnet: 2 blank (498,786) — token cap / template echo. usable 941.
- xhigh: 0 corrupt, 3 missing (68,112,259 — refusal/token-cap/wrong, prior holdouts). usable 940. CLEANEST.
dataApp rerun prompt for ALL 183 missing (with root-cause diagnosis per teacher) is
out to claude_dataApp. After it lands, re-pull raw + re-extract here.

## Key findings so far (provisional)
- xhigh APPEARS to be the strongest single teacher, but ONLY where Wolfram can
  confirm (w_tier benchmark gave xhigh ~78% strict vs others 55-65%). That benchmark
  was Wolfram-anchored + teacher-restricted (correct_answer was ALWAYS one of the
  teachers, 0/167 independent) -> circular-ish + Wolfram-dependent. So "xhigh best"
  is PROVISIONAL on the Wolfram audit, NOT established.
- strategy's own xhigh check vs an independent Wolfram+search proxy put all of
  sonnet/oss/xhigh ~62% on free-form (tied), gpt4 lower. That proxy was ~86% Wolfram
  = also unaudited. So BOTH analyses rest on unvetted Wolfram. Don't trust either
  magnitude; the robust bits are: gpt4 is corrupt 18%, and 4-way teacher unanimity
  is a strong (Wolfram-independent) near-gold anchor.
- MCQ teacher reliability CANNOT be measured against Wolfram proxy (teachers give a
  LETTER, Wolfram often stores a derived VALUE -> false mismatch). Needs a
  letter-normalized gold before judging MCQ.

## Reset done this session (archived, reversible)
archive/pre_audit_reset_20260530/ holds the binned drift: data/answer_sheet/* (all
unified_answer_sheet + v4/v5/v5_1/v6, answer_matrix, MASTER_GOLD_V2_SPEC,
validation_report), w_tier_confidence_analysis.csv (circular benchmark),
unified_answer_sheet_legacy.csv, build_master_gold.py (old tier builder),
teacher_answers_compact.json (joined). Fresh start: per-LLM only.

## Grader note (from earlier this session)
Canonical grader = grading/grader.py (Grader) — value-equality, our Kaggle mirror.
"judger" name deprecated; strict Hendrycks kaggle_like_is_equiv deprecated.
build_review_sheet.py switched to value-equality. Trust story is INVERTED vs old
docs (value-equality, not strict) — pending final Kaggle confirmation.

## ON ICE
The 2-version answer-sheet fork (Wolfram-vs-consensus weights vs conservative-vs-
aggressive override threshold). Resume only AFTER the 3 audits + a clean sheet.

## NEXT ACTION for the fresh session
1. Read this file + the 4 teacher FINDINGS.md + everything in data/search/wolfram/.
2. Do strategy's own Wolfram audit (read WOLF_RESULTS.csv + its notes/FINDINGS/TODO/
   SCRATCH/RESULTS_SUMMARY) while ChatGPT's pass runs; cross-check when it returns.
3. Watch for: dataApp gpt4-rerun landing (re-pull), ChatGPT Wolfram pass
   (CHATGPT_AUDIT_PASS2.md), ChatGPT teacher pass.
Repo is the source of truth. Verify committed output, never trust an agent report
at face value (we caught a wrong-remote false alarm and a real RateLimitError this way).
