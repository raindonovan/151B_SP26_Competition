# Signoff — claude_grader_research (2026-05-28)

## What I tried:
- Read ALL specified repo files (15+ docs)
- Fetched complete Hendrycks `math_equivalence.py` via git-mcp (SHA b5c066f)
- Read EleutherAI lm-evaluation-harness hendrycks_math implementation
- Rebuilt `_strip_string` and `is_equiv` locally, ran 40+ edge case tests
- Searched for CSE 151B SP26 competition page (not found — private InClass Kaggle)
- Searched for AIMO PP1/PP2 winner writeups (Numina, NemoSkills)
- Searched for HuggingFace Math-Verify source and changelog
- Read starter notebook cells 11 (prompt) and 22 (scoring)
- Ran full normalization audit on all 943 answer sheet items
- Cross-referenced slash-fraction items against question text and teacher answers

## What I did:
- `grading/GRADER_RESEARCH.md` — 270+ line analysis with appendix
- `research/28_05_Grader/FINDINGS.md` — consolidated findings (8 sections)
- `research/28_05_Grader/hendrycks_reference.py` — local test harness
- Verified every claim with code execution

## What worked:
- git-mcp:get_file_contents fetched Hendrycks source when web_fetch hit 429
- Local reproduction enabled empirical testing of all edge cases
- Cross-referencing source code + submission data + teacher answers revealed WeBWorK finding

## What didn't:
- Could not find CSE 151B SP26 Kaggle page (InClass/private)
- Could not find server-side grader code directly
- web_fetch on github.com rate-limited

## What's left:
1. Build actual post-processing script (13 rules, priority-ordered)
2. Fix `\text{A}` → bare `A` in item 725
3. Source-corpus classify all 943 items (WeBWorK vs MATH vs AIME)
4. Build proper MCQ override (prepend/replace, not append)
5. Scan raw model outputs for format issues (not just answer sheet)

## Key discoveries:
1. WeBWorK items use `a/b` gold — converting to `\frac{}{}` BREAKS match
2. `0.5` and `a/b` auto-conversions are STANDALONE only (not in multi-answer)
3. `\text{A}` in item 725 likely costs a point
4. 13 new format rules documented (most absent from current sheet but matter for model outputs)
5. Complete `_strip_string` 17-step processing order verified
