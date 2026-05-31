# Post-Deadline Audit Queue

Audit tasks identified during the competition that cannot be completed before the deadline but **must not be forgotten**. Each entry includes scope, discovery date, evidence, and the specific action required.

---

## A1 — HISTORICAL OVERRIDE AUDIT: Day-8 append mechanism on multi-slot items

**Status:** OPEN. **Priority:** HIGH (Rain explicit: "DO DO NOT FORGET"). **Discovered:** Day 9 (2026-05-30, evening PT) during NoThinking ∪ R20 join CSV build.

### The bug

The Day-8 `apply_overrides` mechanism worked by **appending** `\n\n\boxed{value}` to the end of the response field. The Kaggle / `math_equivalence` grader's free-form extractor takes the **last contiguous group** of `\boxed{...}` expressions in the response.

- For **single-value** overrides on responses ending in a single `\boxed{}`, the append produced one new group of size 1 after the original group of size 1. Grader took the new group. **Worked.**
- For **multi-slot** overrides on responses ending in `$$\boxed{a}\boxed{b}\boxed{c}$$`-style multi-slot answers, the append merged old + new into ONE contiguous group. Grader read ALL the boxes (old + new) as a single answer. **Failed silently.**

### Evidence

Day 9 NoThinking join build verification:
- id=345 under append override: graded as `-0.8333, 0.8333, -5/6, 5/6` (4 slots, wrong) instead of `-5/6, 5/6` (2 slots, right)
- 10 of 10 multi-slot overrides tested graded FALSE under the append mechanism
- All 10 grade TRUE after switching to full-replace

Build commit: `64e4eb7` (apply_overrides.py refactor + verification); SHA recorded in `1e4e20f`.

### The fix (already shipped)

`postprocessing/scripts/apply_overrides.py` switched to **full-replace** semantics: the entire response field is replaced with a clean `\boxed{value}` rather than appended-to. All 13 (and 282) overrides in the conservative + diagnostic CSVs grade `auto_judge==True` vs gold under the new mechanism.

### Audit scope (post-deadline)

1. **Identify which historical Kaggle submissions used the Day-8 append mechanism.** Check `submission/REGISTRY.md` (or `docs/SUBMISSION_REGISTRY.md`) for any submission whose override-application step ran under the pre-fix `apply_overrides.py` or under `splice_csvs.py` / Day-8 splice variants that may have had the same bug.
2. **For each affected submission, identify multi-slot override items.** Cross-reference the override CSVs that fed each submission against private.jsonl's multi-slot items (items where the gold answer has 2+ comma-separated slots).
3. **Re-grade affected submissions locally** with the corrected full-replace mechanism. Compare to the Kaggle scores in REGISTRY.
4. **Quantify the impact:** how many scored slice items were affected per submission? Did any of our scored submissions have "invisible failures" inflating the appearance of a worse-than-actual variant or deflating a better-than-actual variant?

### Why this matters post-deadline

- **Research integrity for the final report**: any claim like "the v3-perslot variant scored X" or "MED tier contributes +0.3pp" should be re-verified if the underlying submission used append on multi-slot.
- **Future projects**: the canonical override mechanism for future work needs to be full-replace, not append. Worth documenting prominently in `postprocessing/CLAUDE.md` so a future session doesn't reintroduce the bug.

### Owner

Whoever picks up the next claude_strategy session post-deadline. Should fire ChatGPT cross-check on the re-grade methodology before publishing any revised numbers.

---

## A2 — V-SERIES + R14 SHALLOW BATCH

**Status:** OPEN. **Priority:** MEDIUM. **Discovered:** ongoing throughout Day 9.

Catalog R15-R19 (V0_baseline / V1_counting_top / V2_counting_bookend / V3_shape_filter / V4_temp_diversification) and R14 (`run13_v2openr1_50_rp110`, repetition_penalty=1.10 ablation). Apply T1 template (now requires all 5 sampling params + PARAM LEVER flag per `strategy/AUDIT_TEMPLATES.md`).

These are param-lever ablations from the dev arc that would have informed morning-runs candidate ranking but didn't fit in the Day 9 audit budget. Useful for:
- Research write-up (what worked / didn't in prompt-engineering vs param-tuning)
- Future projects (which sampling-param configurations to start from)

---

## A3 — R10b PERTURBED-PERSLOT ABLATION

**Status:** OPEN. **Priority:** LOW. **Discovered:** Day 9 audit chronology.

`expA_run08_perslot_perturbed` ran alongside R10. Shallow catalog only. Tells us whether perturbed v3-perslot is worse / equal / less-worse than vanilla v3-perslot. Mostly research-curiosity value given v3-perslot was a confirmed net-negative lever (R10 deep audit, R20 4-way matrix).

---

## A4 — NOTHINKING 98-ITEM PROBE + TARGETED RESCUE VARIANTS

**Status:** OPEN. **Priority:** LOW-MEDIUM. **Discovered:** Day 9 NoThinking 943 audit.

Two NoThinking artifacts deferred from the Day 9 audit:
- `inference/results/hybrid/tnr-B/nothinking_probe98_20260526T065456Z.jsonl` — Phase 1 98-item probe
- `inference/results/hybrid/tnr-B/targeted_rescue_nothinking_20260526T230849Z.jsonl` — targeted rescue variant

For the research project specifically, the probe's per-item behavior + comparison to the full-943 run could surface calibration findings (does the technique generalize from probe to full?). Worth a light pass.

---

## A5 — GENSELECT RE-TEST (FIX CANDIDATE WINDOW)

**Status:** OPEN. **Priority:** MEDIUM (post-deadline; could have been competition-relevant if discovered earlier).

`inference/runs/selection/genselect_poc/findings.md` documents that the POC failed due to candidate inputs truncated to ~500 chars — NOT a Qwen capability issue. "Qwen is bad at self-verification" is an UNVALIDATED conclusion in the project.

Post-deadline: fix the candidate window, run a proper smoke test (5 items first per the discipline rule the POC's own post-mortem established), then full 943 if smoke passes. Resolves an open question about Qwen-as-judge capability and would be a clean addition to the research write-up.

---

## A6 — SONNET-ON-QWEN EMPIRICAL VALIDATION

**Status:** OPEN. **Priority:** MEDIUM for research.

Day 9 surfaced a verification gap: while research consensus (May 23 multi-source review) supports single-teacher Sonnet-preferred for SFT on Qwen3-4B-Thinking-2507, we don't have a clean isolated experiment in our project history showing that Sonnet traces specifically produce coherent Qwen outputs. The v3/v4/v5 SFT runs either failed for architectural reasons or used non-Sonnet traces (e.g., v2 OpenR1 worked with R1 traces).

Post-deadline: if the 8-item adapter is built and trained tomorrow, its results will themselves be the Sonnet-on-Qwen empirical test. Document the findings explicitly in the research write-up.
