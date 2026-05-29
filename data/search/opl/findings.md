# OPL Run — Findings

## Headline (Day 7 update — after teacher-consensus join)

**OPL OK-bucket is mostly false-positive text matches. Of 39 OK items, 0 align with 3/3 teacher consensus. Realistic override value: probably <1pp on Kaggle LB, not the earlier +3-4pp estimate.**

## Day 7: OPL × teacher-consensus join (NEW)

Ran `data/search/opl/join_with_teachers.py` over the 39 OK-status items × 3 teachers (sonnet, gpt-4, oss) in `data/MASTER_ANSWERS.csv`. Results in `data/search/opl/findings_join.csv`.

| Classification | Count | Meaning |
|---|---|---|
| **T1-promoted** (3/3 teachers AND OPL agree) | **0** | The bucket we hoped to find — zero items |
| **OPL-disagrees** (3/3 teachers agree, OPL says something different) | **25** | Teachers unanimous, OPL likely wrong-problem match |
| **Split-teacher** (teachers not unanimous, OPL is tiebreaker candidate) | **14** | Of secondary interest; OPL evidence still suspect per id=15 spot-check |

### Spot-check: id=15 (highest similarity = 0.9055)

- **Our question**: *"Are the functions below polynomials? ... $f(x)=x^{8}+4$ has degree [ANS] ..."*
- **Teacher consensus + sheet_best**: `8,NONE` (3/3 teachers agree, sheet tier=2)
- **OPL match path**: `OpenProblemLibrary/LoyolaChicago/Precalc/Chap9Sec2/Q01.pg`
- **OPL extracted answers**: `0`, `1`
- **Verdict**: OPL matched a completely different precalc problem on textual similarity alone. The 0.9055 score reflects shared phrasing ("enter the answer", "function below"), not problem equivalence.

If even the **highest**-similarity match is a false positive, the lower-similarity 38 are almost certainly worse.

### Implication for submission strategy

- OPL bulk-override is now **disconfirmed** as a high-value lever. The earlier +3-4pp estimate in this doc was a ceiling that assumed parameter equality; the join shows that ceiling is unreachable in the OK-bucket as-extracted.
- **Pick B aggressive** (conservative + T1-promoted OPL): degenerates to == Pick B conservative, since the T1-promoted set is empty.
- **Split-teacher bucket (14 items)** could in principle be a tiebreaker source, but the id=15 spot-check makes us doubt OPL evidence quality here too. Recommendation: do NOT use OPL split-teacher overrides in any submission until per-item spot-checks confirm semantic match (not just text-similarity match).
- Salvage value remaining: OPL as a **classification/routing signal** for what kind of math each question is (per "What OPL IS" below).

## Earlier findings (pre-join, kept for traceability)

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
