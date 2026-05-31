# T2 Audit — NoThinking targeted_rescue

**Date:** 2026-05-31 (Day 9 close) · **Auditor:** claude_vscode · **Commit:** built on `5b2182e`
**Analyzer/grader:** canonical `analyze_run.py` v3-final-final (761f903) via `prep_nothinking_for_analyzer.py --run-id NT_targeted_rescue_nothinking_sc16_f61_t8k` (analyzer NOT modified). New build (no prior findings.md).

## Subset + provenance
- **`targeted_rescue_nothinking_20260526T230849Z`** · 2026-05-26 23:12 UTC · `mode: base` · **NoThinking** (sample0 starts "To solve…", no reasoning preamble; mean 1389 output tokens) · **SC@16** (16 samples) · token cap 8192 · **61 curated items**.
- **Paired with a Thinking-mode twin** `targeted_rescue_20260526T201046Z` (same 61 ids, "Okay, let's tackle…", mean 6102 tok) — a NoThinking-vs-Thinking experiment on the same hard set. (Thinking twin not cataloged here — separate audit if needed.)
- **Subset selection:** R20-failure-weighted hard items — of 61: **42 R20-wrong**, tier dist {T5:43, T4:8, T3:3, T0:7}, R20 bucket {unknown:25, B:25, A:7, A_lucky:4}. Selected on a **May-26 criterion that PREDATES the 32K-truncation analysis** → **0 of the 61 are R20-truncated, and 0 intersect the 17-still-truncated-at-32K set.**
- Config vs NT-943: same model/mode/cap, but **SC@16** (vs NT-943's SC@8) and a curated 61-item slice (vs full 943). Hardware/inference-commit not recorded in artifacts (provenance gap, same as all NT runs).

## Standalone score + composition
- **Bucket:** A=7 · A_lucky=10 · B=19 · unknown=25. **Scored 7/36 = 0.1944** — very low, but this is a deliberately hard R20-failure slice (43/61 T5), not comparable to full-set accuracy.
- **Truncated: 0** (NoThinking short). **shape_fallback: 6/61 = 9.8%** — elevated vs NT-943's ~3.7% (consistent with hard slice + the noise finding below; far below probe98's 47%).
- **n_voting:** healthy-ish spread (16/61 at full 16, but 15/61 at ≤2) — fragmented on the hard items, like probe98.

## New-rescue analysis vs R20 + NT-943 (load-bearing)
| Category | Count |
|---|---|
| R20 already correct (no rescue needed) | 19 |
| **NEW UNIQUE rescues (R20 wrong, NT-943 wrong, targeted_rescue RIGHT)** | **1** (id=232) |
| existing rescues (R20 wrong, NT-943 right, tr right) | 3 |
| **tr WORSE than NT-943 (NT-943 right, tr wrong)** | **6** (5, 257, 490, 499, 578, 715) |

- **Net vs NT-943 = +1 − 6 = −5.** Stacking targeted_rescue on top of the NT-943 join would **HARM** (it loses 6 NT-943 rescues to gain 1).
- The 1 new rescue (id=232, gold `40,37,3` — tr got it, R20+NT-943 both wrong) is a lucky single hit, not a pattern.

## 17-truncated-set intersection
- **0 of the 17 still-truncated-at-32K items are in this subset.** This run was curated months before that analysis and **says NOTHING about the "NoThinking high-budget on 17-truncated" morning candidate** — it neither supports nor refutes it. (That candidate remains untested; would need a fresh run on those specific 17 items.)

## Capability vs sampling signal
targeted_rescue vs NT-943 on the 61: exact-answer agreement 25/61; both-correct 12, both-wrong 42, **tr-only-right 1, NT-943-only-right 6**.
- **This is the "high-disagreement, SIMILAR-OR-WORSE correctness = stochastic variance" case** (the texas-oil / probe98 saturation pattern). Curating to hard items + bumping to SC@16 did **NOT** unlock new capability — it produced another noisy NoThinking pass that is slightly *worse* than NT-943 on the shared items (e.g. id=578: tr `7.62, 8.99, 95.4` vs gold `…9.00…` — a rounding miss NT-943 avoided).
- Interpretation: NoThinking on isolated hard items is as noisy as probe98 showed; targeting + more samples did not convert variance into capability.

## Pre-commit audit (memory #24)
(a) Same canonical analyzer + prep as all NT audits; ran with explicit `--run-id` (avoids the prep hardcode). 61 rows, 976 samples (16×61), 0 extracted_empty contradictions. ✓
(b) No prior findings.md (new build). ✓
(c) Correctness via `auto_judge` + MASTER_ANSWERS, not self-comparison. ✓
(d) Test matrix spot-check: id=232 (new-rescue, verified `40,37,3`==gold), id=5/578 (tr-worse, verified rounding/format misses), id=0 (control, all-correct), id=72 (both-wrong). ✓
(e) Verdict from numbers below. ✓

## T2 verdict
- **Targeted_rescue offers NEW rescues beyond NT-943: NO (marginal −5 net).** 1 new unique rescue, 6 regressions vs NT-943 → stacking harms. The NT-943 ceiling holds.
- **Capability vs sampling: SAMPLING (stochastic variance), not capability.** Curating + SC@16 did not beat the full NT-943 pass on the shared hard items.
- **Tomorrow-impact:** **targeted_rescue is research-only — do NOT stack it.** It does NOT inform the "NoThinking high-budget on 17-truncated" morning candidate (0 intersection) — that candidate is neither supported nor refuted here and must be evaluated on its own if Thunder time allows. Combined with probe98 (YELLOW) and texas-oil (PARTIAL), this closes the NoThinking workstream's "more NT passes help" question: **they don't; NT's value is the single full NT-943 join (+1.8pp), and the path to more is independent gold, not more/curated NT runs.**

## Open Qs
None — closes at T2. (No ChatGPT parallel pass per the spawn note; verdict is unambiguous at −5 net.)
