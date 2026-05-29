# 29_05 — Two Targeted Hypothesis Submissions

> ## ⚠️ KNOWN ISSUES — READ BEFORE INTERPRETING SCORES
> - 🟡 **See `submission/AMBER_ALERT.md`** for unresolved concerns
> - These 2 builds use the **NEW BASE** `slot4_undercount_expand.csv` (0.706) from the 25_08 round, not kitchen_sink_C (0.692)
> - Build 2 uses **full-response-replace mechanism** for MCQ (per AMBER #3 fix), unlike 25_08 Slot 3 which used the broken append-to-end mechanism
> - EVs still use the **uniform random sampling prior** — no clean evidence the slice is uniform OR biased in any direction

**Built:** 2026-05-28 (late evening), after 25_08 results returned
**Base:** `submission/25_08/csvs/slot4_undercount_expand.csv` = 0.706 (NEW best)
**Strategy:** 2 INDEPENDENT submissions, each testing a single empirically-grounded hypothesis. No chaining required.
**Slice math:** Test set ≈ 283 items. 1 correct flip = +0.354pp. Expected slice items per overlay ≈ N × 0.30.

---

## Build 1 — `undercount_plus_frac.csv`

### What it does
Takes the 0.706 base. Appends `\n\n\boxed{\frac{a}{b}}` to 8 specific items. All 935 other items are byte-identical to slot4.

### Hypothesis tested
**Are slot 4's +4 slice items and slot 1's +2 slice items ADDITIVE?**
- Slot 4 (undercount expansion, 51 items, +4 slice) and Slot 1 (fraction conversion, 8 items, +2 slice) had **disjoint item sets** in 25_08 (no item ID overlap between the two override lists).
- If the levers are independent, stacking should give +6 slice items → predicted ~0.713.
- If interfere or correlate, less.

### Items overridden (8)
Identical to 25_08 Slot 1:
- 135 → `\frac{3}{5}` (8x+2=3x+5)
- 207 → `\frac{14}{5}` (perpendicular line slope)
- 529 → `\frac{429}{20}` (work-rate problem)
- 716 → `\frac{19}{33}` (coefficient of determination)
- 784 → `\frac{17}{60}` (distance between fractions)
- 817 → `\frac{88}{21}` (evaluate 8/7 + 8·(8/21))
- 919 → `\frac{3875}{12012}` (Putnam-style probability)
- 936 → `\frac{275}{16}` (find k for polynomial divisibility)

### Mechanism
- Append `\n\n\boxed{NEW}` to the existing response
- Grader for free-form: extracts LAST `\boxed{}` → our new box wins
- Per-item verification: all 8 land as the last box (confirmed pre-upload)

### Why this is independent of build 2
- Build 1 only touches FREE-form items
- Build 2 only touches MCQ items
- Zero item overlap → either can be uploaded first; results don't depend on each other

### Expected delta and outcomes
- 8 items changed → ~2.4 in slice
- Slot 1 already proved this lever has ~83% conditional yield
- **Predicted: +0.7 to +1.1pp → 0.713 to 0.717**
- If LESS than +0.007 (slot 1's gain), the additivity claim is broken — could indicate slot 4's wins included items that were ALSO winnable via frac conversion (e.g., item 25 in slot 4 already did decimal→fraction within its expansion).

---

## Build 2 — `mcq_prepend_fix.csv`

### What it does
Takes the 0.706 base. For 16 specific MCQ items, **replaces the entire response with just `\boxed{LETTER}`** (full replacement, no preserved reasoning trace). All 927 other items are byte-identical to slot4.

### Hypothesis tested
**Does raw 3-teacher MCQ consensus beat kitchen_sink_C's fusion-of-evidence (SC8 + Wolfram + answer sheet + prior teacher overrides) on the 16 "INVALID MCQ" items, when the override mechanism works?**

25_08 Slot 3 tried to test this with the append-to-end mechanism. That mechanism is broken for MCQ (`re.search` finds first `\boxed{LETTER}`, ignores appended last box). The submission scored exactly 0.692 = base = silent no-op. AMBER #3 confirmed.

Build 2 uses the **full-replace mechanism** that GRADER_SPEC §3 says will work: `response = "\boxed{LETTER}"` — the only box in the response, guaranteed to be both first and last.

### Items overridden (16)
"INVALID MCQ" subset from CLAUDE_STRATEGIES. Letters derived from `data/MASTER_ANSWERS.csv` teacher columns (sonnet, gpt4, oss), majority vote:

| Item | Letter | Teacher agreement |
|------|--------|---------------------|
| 18 | H | unanimous (3/3) |
| 117 | B | unanimous |
| 403 | J | unanimous |
| 443 | G | unanimous |
| 457 | C | 2/3 (sonnet+gpt4=C, oss=G) |
| 501 | F | unanimous |
| 518 | E | unanimous |
| 589 | D | unanimous |
| 670 | D | unanimous |
| 675 | B | unanimous |
| 682 | G | unanimous |
| 695 | E | unanimous |
| 720 | D | unanimous |
| 727 | A | unanimous |
| 786 | C | sheet+gpt4=C, sonnet truncated CoT mentions "indeed C", oss=number (data noise) |
| 935 | H | unanimous |

### Mechanism
- `row["response"] = "\boxed{LETTER}"` — full replacement
- Per-item verification: response is EXACTLY `\boxed{LETTER}`, first-box `re.search` finds it correctly (confirmed pre-upload for all 16)

### Why this is independent of build 1
- Build 2 only touches MCQ items
- Build 1 only touches FREE-form items
- Zero item overlap

### Expected delta and outcomes
- 16 items changed → ~4.8 in slice
- Teacher MCQ consensus is medium-strength evidence (correlated LLMs)
- If teachers reliably beat Qwen on these items: ~half flip wrong→right → +2-3 slice items → **+0.7 to +1.1pp → 0.713 to 0.717**
- If teachers no better than Qwen: ~0 net → 0.706
- If teachers worse than Qwen on these items: negative delta possible

### What we LEARN regardless of score
- **Score > 0.706:** Raw teacher MCQ consensus beats kitchen_sink fusion on these items; expand to more disagreement items
- **Score = 0.706:** Mechanism worked, but fusion and raw teachers are equivalent on these items
- **Score < 0.706:** Kitchen_sink fusion beats raw teacher consensus; the existing multi-source fusion is doing real work that raw teachers don't capture

**ACTUAL RESULT: 0.703 (−0.003 = −1 slice item).** Post-hoc audit revealed only 6 of 16 items were actual letter flips (the other 10 had teacher_letter = kitchen_sink_letter — no real test). On those 6 disagreements, fusion was right more often than raw teachers. **Not "teachers are unreliable" — "kitchen_sink_C fusion of evidence is stronger than raw 3-teacher consensus on disagreements."**

This is the first time we've empirically measured fusion-vs-raw-teacher on MCQ. Slot 3 of 25_08 was a no-op so we had no data on this question yet.

---

## What we DON'T test in this round (deliberately)

- Search-gold overlay — proven net-harmful in 25_08 (−6 slice items). Need source-quality stratification before retry.
- Symbolic exact forms (`\pi/4` style) — no curated candidate list yet
- Multi-char prefix stripping in current best — separate post-processor pass needed first
- Wolfram MED re-application — already in slot4 base via kitchen_sink inheritance

## Upload order (suggested, parallel is fine)

Both builds independent. Any order. Recommended: undercount_plus_frac.csv first (highest expected delta + most evidentially grounded), then mcq_prepend_fix.csv (lower confidence but tests AMBER #3 fix).

---

## Day 7 addendum (2026-05-29) — Pick B candidate

### undercount_frac_mcq.csv (BUILT, NOT YET SUBMITTED)

**Recipe**: `undercount_plus_frac.csv` (0.713) + 16 MCQ-prepend-fix overrides from `mcq_prepend_fix.csv`. The 8 frac IDs and 16 MCQ IDs share zero items, so the merge is a clean union → 24 total IDs differ from the `slot4_undercount_expand` base.

Build script: `submission/29_05/scripts/build_undercount_frac_mcq.py`.

**Expected score**: ~0.710. The 29_05 Build-2 result (mcq_prepend_fix alone on slot4 base = 0.703, −1 slice item net) suggests this stack will land at 0.713 + (−0.003) = ~0.710 under additivity, NOT a Pick-B improvement over the 0.713 pure-frac stack. Of the 16 MCQ overrides, only 6 were real letter flips; those netted −1 slice item.

**Recommendation**: do NOT submit this as Pick B yet. Either use a daily slot to probe the mcq_prepend_fix lever in isolation against the 0.713 base (to confirm whether it's net-positive on top of frac), or keep Pick B as the pure `undercount_plus_frac.csv` until a better candidate emerges.

### OPL-based Pick B candidate — NOT BUILT (intentional)

An earlier framing called for stacking T1-promoted OPL items on top of the three-lever build for an additional +3-4pp ceiling. The Day-7 OPL × teacher-consensus join (`data/search/opl/findings_join.csv`, `data/search/opl/findings.md`) found **0 T1-promoted items** in the OPL OK-bucket — the OK-bucket is mostly false-positive text matches (smoking gun: id=15 at sim=0.9055 matched a different problem entirely). OPL bulk-override is empirically disconfirmed as a high-value lever. No OPL-based stack built.
