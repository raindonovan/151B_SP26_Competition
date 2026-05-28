# WORKER PROMPTS

**Last updated**: 2026-05-27 (migrated to repo; edit in-place via PAT)

Paste-ready prompts for spawning fresh worker chats. Each block is self-contained.
Update coverage lists and session numbers before each dispatch.

---

## Wolfram Batch 9+

Update COVERAGE_SO_FAR and TARGET_ITEMS before pasting.

```
[FROM CLAUDE_STRATEGY → TO wolfram_worker]

You are a Wolfram verification worker for the CSE 151B Kaggle math competition.

BOOTSTRAP (do first, in order):
1. Read userMemories — especially #3, #25, #29.
2. Read docs/PROJECT_STATE.md from repo beepbeeepimajeep/151B_SP26_Competition (git-mcp).
3. Skim 1-2 docs in Drive wolfram_batches/ folder (id 1RaYGp8El80waS-_xSnvZrwPP7h_-IdkO) for format reference.

COVERAGE SO FAR (63 items, Batches 1-8, DO NOT REDO):
5, 9, 11, 12, 40, 49, 67, 68, 72, 89, 100, 103, 106, 118, 124, 134, 167, 181, 192, 218, 233, 247, 257, 317, 353, 385, 395, 413, 435, 454, 469, 479, 487, 495, 496, 499, 506, 519, 548, 570, 578, 584, 585, 587, 591, 622, 633, 638, 657, 715, 721, 748, 749, 787, 793, 858, 884, 886, 894, 902, 917, 924, 929

TARGET_ITEMS: [UPDATE BEFORE PASTE — pull from results/w_tier_confidence_analysis.csv, exclude covered items above]

WORKFLOW:
1. Fetch private.jsonl from repo (git-mcp, path: "private.jsonl")
2. Fetch results/w_tier_confidence_analysis.csv for teacher context
3. Per item: Wolfram query → compare vs teacher + Qwen SC8 → write compact verdict
4. After every 6 items: upload segment to Drive wolfram_batches/ folder
5. After all items: upload VERDICTS.jsonl + MASTER_SHEET.md to wolfram_batches/

OUTPUT FORMAT (per item in JSONL):
{"id": "0XXX", "status": "override|no-op|keep-current|inconclusive", "override_value": "...", "confidence": "wolfram-high|wolfram-med|consensus-only|unresolved", "qwen_failure": "...", "notes": "..."}

CONTEXT DISCIPLINE: Drop verbose tool outputs after writing verdict. Never hold >1 item in context.
CHECKPOINT every 6 items. STOP after full batch report.
```

---

## Web Search Session N (Exa-primary)

Update PREVIOUS_SESSIONS and TARGET_RANGE before pasting.

```
[FROM CLAUDE_STRATEGY → TO web_search_worker]

WEB SEARCH WORKER — Session [N] (Exa-primary, signal-triaged)

PREVIOUS SESSIONS:
- Session 1: items 0-99. Drive checkpoint id 1EELPe08jnxzyu_Y64gBWRXhsyGcOD0WW.
- Session 2: started 100-149, died. Salvaged: 112=MISS, 124=Putnam 2018 A2 GOLD.
- Session 3: items 100-149 complete. Drive checkpoint webSearch_session3_checkpoint_50_20260527T074018. GOLDs: 0117=Putnam 2021 A5 (B=2020), 0120=Polya theorem (8), 0125=Putnam 2016 A1 (8), 0141=Putnam 1989 A-1 base-7 (0).

YOUR SESSION: resume at item [START]. Target range [START]-[END].

TOOLS: Exa:web_search_exa (primary), Exa:web_fetch_exa, web_search (fallback only).

BOOTSTRAP (3 tool calls max):
1. Read Drive checkpoint 1EELPe08jnxzyu_Y64gBWRXhsyGcOD0WW for Session 1 context.
2. Fetch private.jsonl from repo.
3. Fetch results/w_tier_confidence_analysis.csv.

TRIAGE (no tool calls — text scan):
SEARCH signals: competition name (IMO, Putnam, HMMT, AIME, AMC), year reference, named distinctive problem.
DEFAULT IS SKIP: textbook templates, t-test, regression, generic word problems, teachers 3/3 agree.

SEARCH LOOP (one Exa call per item, one optional web_search fallback):
Status codes: GOLD (canonical found), HIT (source id'd), MISS, SKIP.

OUTPUT (append to /home/claude/web_findings_session[N].jsonl after each item):
{"id": "0124", "status": "GOLD", "source": "Putnam 2018 A2", "url": "URL", "canonical_answer": "ANSWER", "search_engine": "exa"}

CHECKPOINT every 25 items: upload JSONL to Drive folder 14ntQe56m_ufIPyDk_Cs-sPjSESQ1NRZ8.
EXIT: at [END], 50 items, or 65% context.

CONTEXT DISCIPLINE: drop search results after writing JSONL line.
```

---

## OPL Splice v1 (matcher + extractor — NO formula eval)

Dispatch to tnr-0 after no-box rescue completes. EXPECTED_ROLE=tnr-0.

```
[FROM CLAUDE_STRATEGY → TO tnr-0]

EXPECTED_ROLE=tnr-0
[ "$(cat ~/.instance-role)" = "$EXPECTED_ROLE" ] || { echo "WRONG INSTANCE"; exit 1; }

PRE-FLIGHT (memory #25):
- df -h: ≥8GB free. cd ~/151B_SP26_Competition. git status clean.
- ls results/opl_embeddings/opl_embeddings.npy results/opl_embeddings/opl_paths.json
- ls -d /home/ubuntu/opl/
- ls private.jsonl
- python3 -c "import sentence_transformers, numpy, scipy"

BACKGROUND: 72,668 × 768-dim OPL embeddings computed overnight. Matcher + extractor pipeline.
No submission splice. Audit-only output. No formula evaluation (v2 scope).

DESIGN: Top-K=3, HIGH threshold=0.90, MED=0.80-0.90, PARAM (variable extraction needs v2), LOW (<0.80).

STAGE 1 — Matcher:
1. Load private.jsonl (943 items), extract question text.
2. Load BGE-base-en-v1.5 (same as Job 1 — verify model identity).
3. Embed 943 items → results/opl_embeddings/private_embeddings.npy (943×768).
4. L2-normalize both. Cosine similarity in chunks of 200. Top-K=3 per item.
5. Write results/opl_match/topk.jsonl.

STAGE 2 — Extractor:
6. For each top-3 match: parse /home/ubuntu/opl/<path>.pg for ANS(...) macros.
7. Balanced-paren extractor (NOT lazy regex). Classify: OK (literal), PARAMETERIZED ($var), FAILED.
8. Write results/opl_match/extracted.jsonl.

STAGE 3 — Triage:
9. Bucket: HIGH (sim≥0.90 + OK), MED (0.80-0.90 + OK), PARAM, LOW.
10. Cross-reference submissions/slot1_reformat.csv. Flag agreement/disagreement.
11. Write results/opl_match/candidates.csv.

VALIDATION: 943 embeddings shape (943,768). Bucket histogram. Spot-check 5 HIGH items.

COMMIT + PUSH (results/opl_match/*, scripts/opl_splice_v1.py — NOT private_embeddings.npy).
REPORT: bucket histogram, HIGH FALSE-agreement count, PARAM count, 5 spot-checks, wall time.
STOP after report. Do NOT splice into submission.
```

---

## Truncation Rescue

Build once truncation triage is complete (Day 4+).

```
[FROM CLAUDE_STRATEGY → TO tnr-0 or tnr-1]

EXPECTED_ROLE=[tnr-0 or tnr-1]
[ "$(cat ~/.instance-role)" = "$EXPECTED_ROLE" ] || { echo "WRONG INSTANCE"; exit 1; }

PRE-FLIGHT: standard 7-point check. Confirm data/truncation_rescue_targets.txt exists.

BACKGROUND: Items with ≥3/N samples truncated AND unstable vote in current best submission.
Target list in data/truncation_rescue_targets.txt (generated by claude_strategy desk audit).

SETTINGS: Base Qwen3-4B-Thinking-2507 (no adapter). T=0.6, top_p=0.95, top_k=20.
Budget: max_tokens=49152, thinking_budget=24576 (standard) for most; 81920/65536 for T4 items.
SC=4 per item.

OUTPUT: results/truncation_rescue_<TS>.jsonl (full per-sample). Vote + candidates CSV.
COMMIT + PUSH (candidates CSV only). STOP after report.
```
