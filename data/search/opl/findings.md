# OPL Run — Findings

## Headline

**OPL is answer-sheet gold for ~30-40 items at T2-T3 confidence. NOT training gold. NOT +5-12pp.**

## Bucket distribution (from candidates.csv, 2057 rows analyzed)

| Bucket | Count | % | Meaning |
|---|---|---|---|
| PARAM (parameterized OPL template) | 844 | 41% | Would need to plug our values into Perl template — heavy lift |
| LOW | 82 | 4% | Low confidence match |
| MED | 16 | 0.8% | Medium confidence |
| **HIGH** | **1** | 0% | Only id=15 (sim=0.9055, OPL says "0") |

**By `top_status`:**
- PARAMETERIZED: 844 (template, not directly usable)
- FAILED: 60 (matcher couldn't extract)
- **OK: 39** (clean concrete answer extracted, directly comparable to current Qwen submission)

**Of the 39 OK-status items: ALL 39 currently disagree with current Qwen submission.** That's the signal pool.

## Similarity distribution

- min: 0.622, median: 0.812, max: 0.992
- ≥0.90 similarity: 228 items
- ≥0.95 similarity: 122 items
- ≥0.99 similarity: 3 items

## Realistic projection (revised, anchored to actual data)

**Lower bound (OPL direct match only):**
- 39 OK-status items × 88% expected hit rate (per Wolfram override calibration) = 34 correct
- 34 / 943 = **+3.6pp**

**Mid bound (OPL + similarity ≥0.95 PARAM-solved):**
- ~50 additional items × 70% (lower because re-derived) = 35 more
- Combined: **+6-8pp**

**Upper bound (OPL + teacher consensus stack on uncertain items):**
- Requires layering with answer sheet methodology (the info_4 pattern)
- **+10-12pp**, requires additional engineering

**Earlier "+5-12pp" projection was inherited speculation. Actual realized value if shipped today: +3-4pp.**

## What OPL IS NOT

- ❌ Training data (no CoT traces, just answers and template scripts)
- ❌ A direct 943-item answer key
- ❌ Worth +5-12pp on direct application
- ❌ Useful for items without close template matches

## What OPL IS

- ✅ ~30-40 T2/T3 answer-sheet candidates (overrides territory)
- ✅ A classification signal (what kind of math is this question testing → routes Wolfram queries better)
- ✅ A potential seed for SFT v7 dataset (IF we generate CoT for these 39 items, they become training data — but OPL itself isn't the data)

## Why Rain was confused

The +5-12pp framing in earlier memory was hypothesis-mode — assuming we'd layer OPL with teacher consensus and template-solving. Reality after running: 39 direct-match items, +3.6pp ceiling for direct override approach. The "what else does OPL add" question has the answer: not much else, unless we treat it as a routing signal for other work.

## Constraints

- Overrides off the table until Day 7 (per Rain).
- OPL's value as a classification/routing signal hasn't been quantified.
- The 844 PARAMETERIZED items are not actionable without significant engineering.
