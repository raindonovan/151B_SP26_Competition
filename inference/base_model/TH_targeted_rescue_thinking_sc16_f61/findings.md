# T2 Audit — Thinking-twin targeted_rescue (slot-composition follow-up)

**Date:** 2026-05-31 (Day 9 close) · **Auditor:** claude_vscode · **Commit:** built on `58ca321`
**Analyzer:** canonical `analyze_run.py` v3-final-final (761f903) via `prep_nothinking_for_analyzer.py --run-id TH_... --budget 24576` (the prep is mode-agnostic structural restructuring; analyzer NOT modified).

## Subset + provenance
- **`targeted_rescue_20260526T201046Z`** · 2026-05-26 20:13 UTC · **Thinking mode** (samples contain `</think>`; mean **6102** output tokens; max 22617 → thinking_budget ~24576) · **SC@16** · same **61 curated hard items** as the NoThinking twin (`NT_targeted_rescue_nothinking_sc16_f61_t8k`).
- This is the **Thinking half of a NoThinking-vs-Thinking paired experiment** on the same hard R20-failure slice.

## Standalone score + composition
- Scored **13/36** on the hard slice (vs NoThinking-twin's 7/36). hard_independent_DIRTY **0.3636** (vs NoThinking-twin's 0.1818). Truncated 0; gold_conflict 5.
- **THINK-twin beats NoThinking-twin 20/61 vs 13/61** on the identical 61 items → on hard multi-slot/precision items, the **long Thinking budget outperforms NoThinking** (the reverse of the full-943 picture, where NoThinking added orthogonal solves).

## Slot-composition check — the 5 items {9, 435, 479, 499, 638}
| id | gold | R20 | NT-943 | THINK | classification |
|---|---|---|---|---|---|
| 9 | `L-8x, 6F` | `\frac{L-8x}{6F}` ✗ | `\frac{L-8x}{6F}` ✗ | `L-8x, 6F` ✓ | **THINK uniquely correct** |
| 435 | `0.4457, 0.5368,…` | `A` ✗ | `0.4458,…` ✗ | `0.4457,…` ✓ | **THINK uniquely correct** |
| 479 | `40.36, 43.64,…` | `40.01,…` ✗ | `40.356,…` ✗ | `40.36, 43.64` ✓ | **THINK uniquely correct** |
| 499 | `36.9, 0.3225,…` | `36.9, 0.3225` ✓ | ✓ | ✓ | R20 already correct |
| 638 | `0.15, (-infty,…` | `D` ✗ | `0.151` ✗ | `0.15, (-inft…` ✓ | **THINK uniquely correct** |

## New-rescue count (the load-bearing number)
- **NEW-RESCUE COUNT = 4** (items where THINK correct AND R20 wrong AND NT-943 wrong): **9, 435, 479, 638**. (The full 61-item sweep confirms exactly these 4 — no others.)
- **ALL 4 are on INDEPENDENT (trustworthy) gold** — 0 on unverifiable sheet_dependent. Unlike texas-oil (26/40 unverifiable), every Thinking-twin rescue is gold-confirmed. This is a HIGH-PRECISION result.
- ≥ 3 → **real slot-7/8 lever candidate.**

## Intersections (shapes tomorrow's priority)
- **∩ 17-still-truncated-at-32K set: 0** — these are NOT truncation rescues (none flagged truncated; they need long *generation* on multi-part items but complete within budget).
- **∩ 8-item adapter seed [41,61,103,104,127,231,264,282]: 0** — none are the persistent-true-miss adapter targets.
- **All 4 are FRESH** (neither set). High-budget Thinking rescues a DISTINCT class: **multi-slot / high-precision items** where the long reasoning budget produces the full, correctly-rounded tuple that R20's SC-vote collapses (e.g. 435→`A`, 638→`D`) or NoThinking mis-rounds (479 `40.356` vs `40.36`).

## T2 verdict
- **High-budget Thinking IS a real slot-7/8 lever:** 4 fresh, gold-verified rescues beyond R20 ∪ NT-943, distinct from truncation and adapter-seed classes; THINK > NoThinking on hard items (20 vs 13 / 61).
- **Tomorrow-impact:** a **high-budget (24K+) Thinking SC run on R20-wrong multi-slot/precision items** is a justified morning Thunder candidate — and complementary to NT-943 (which rescues a different, NoThinking-orthogonal class). The mechanism is **generation length on multi-part answers**, not truncation rescue — so target R20's multi-slot B/A_lucky items, not the 17-truncated set.
- **Caveat:** n=4 on a 61-item curated slice; the *rate* won't necessarily generalize, and the +1.8pp NT-943 lesson (realized ≠ scaling floor) applies. Treat as "worth a morning slot," not "guaranteed +Xpp."

## Provenance/discipline notes
- The prep script labels method `vllm-sc-nothinking` even for this Thinking run (cosmetic — the prep is structural only; analyzer uses extract/judge, not the label). Flagged: a future prep tweak could carry the true mode; inert here.
- Raw 19MB jsonl git-LFS-tracked. analysis files <10MB → raw. Closes at T2.
