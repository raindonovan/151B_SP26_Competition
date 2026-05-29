# Submission Forensics

Created: 2026-05-28
Status: Active reference for interpreting the submission corpus after RED_ALERT and AMBER corrections.

## Why this file exists

The repo already has:
- `RED_ALERT_LB_SUBSET.md` for the 283-item public-leaderboard slice problem
- `AMBER_ALERT.md` for unresolved interpretation hazards
- `GRADER_SPEC.md` for grader behavior

What was still missing was one document answering a narrower question:

**What can the existing submission corpus actually tell us, once we compare submissions the way Kaggle compares them?**

This file is that answer.

The key methodological rule is simple:

> Do not compare raw CSV rows. Compare the grader-visible answer after extraction and Hendrycks normalization.

That means:
- MCQ: FIRST `\boxed{LETTER}` via `re.search`, else last bare capital
- Free-form: LAST `\boxed{...}` via `rfind`, then Hendrycks `_strip_string`

Any claim in this file is meant to survive that lens.

---

## Sources used

Primary evidence:
- `submission/REGISTRY.md`
- `submission/csvs/*.csv`
- `submission/28_05/csvs/*.csv`
- `submission/29_05/csvs/*.csv`

Interpretation constraints:
- `submission/RED_ALERT_LB_SUBSET.md`
- `submission/AMBER_ALERT.md`
- `grading/GRADER_SPEC.md`
- `grading/hendrycks_extraction_reference.py`
- `grading/hendrycks_is_equiv_reference.py`

Item-level support data:
- `data/MASTER_ANSWERS.csv`
- `data/answer_sheet/unified_answer_sheet.csv`
- `postprocessing/format_candidates_117.csv`

Cross-check / correction notes:
- `submission/SCRATCH.md`
- `grading/SCRATCH.md`
- `postprocessing/FINDINGS.md`
- `grading/JUDGER_AND_PUBLIC_SET.md`

---

## Method

For each submission CSV, interpret each row the way Kaggle would:

1. Read the item type from `data/MASTER_ANSWERS.csv`
2. If MCQ: extract the FIRST boxed letter
3. If free-form: extract the LAST boxed answer
4. Normalize free-form with Hendrycks `_strip_string`
5. Compare submissions on those grader-visible answers, not on raw response text

This matters because many submissions changed long traces without changing the answer Kaggle actually sees.

### Consequence

There are three different notions of “changed item”:
- raw row changed in CSV
- boxed answer text changed
- grader-visible normalized answer changed

Only the third one has leaderboard meaning.

---

## Executive summary

### 1. The submission corpus is useful, but mainly for small controlled probes

The clean information in the repo comes from small differential sets:
- 8-item fraction probe
- 21-item undercount probe
- 6-item MCQ full-replace probe
- 5-item MED ablation

The broad overlays teach much less item-level truth than the repo sometimes implied.

### 2. RED_ALERT changes what "learning from submissions" means

Kaggle feedback is on a fixed unknown ~283-item public slice, not all 943.

So a submission delta tells us:

$$
283 \cdot \Delta \text{score}
=
\sum_{i \in S}
\left(
\mathbf{1}[\text{new correct on slice item } i]
-
\mathbf{1}[\text{old correct on slice item } i]
\right)
$$

where $S$ is the set of grader-visible changed items.

That gives a net count over a changed set, not direct per-item truth unless the set is tiny.

### 3. The repo's strongest late conclusions are mostly right

These are supported by both grader logic and submission behavior:
- MCQ append-to-end overrides were no-ops
- undercount is a real high-yield lever
- fraction-form rescue is a real high-yield lever
- raw search overlay failed mostly because of application/format mistakes, not because search content is inherently useless
- local judger results should not drive submission decisions

### 4. Item 42 is strong, but not leaderboard-certain

The evidence for item 42 = `No, Yes, A` is strong across teachers, sheet, and backsolve. But no existing submission isolates item 42, so the current corpus does not let us certify it via leaderboard oracle logic alone.

### 5. Remaining submissions should not all be spent on generic grader-format learning

At this point, the big grader rules are mostly known already. The highest-value remaining submission use is:
- localizing the wins inside already-proven change sets
- testing one or two unresolved narrow formatting hypotheses
- reserving a few slots for final-pick validation

---

## What the corpus cleanly proves

### A. Some planned submission changes were invisible to Kaggle

Using grader-visible comparison:

| Pair | Score delta | Grader-visible changed items | Meaning |
|---|---:|---:|---|
| `slot1_kitchen_sink_C` vs `slot3_mcq_teacher_override` | `0.000` | `0` | Intended 26 MCQ changes, actual Kaggle-visible changes = none |
| `slot1_kitchen_sink_C` vs `slot1_frac_override` | `+0.007` | `8` | Clean fraction probe |
| `slot1_kitchen_sink_C` vs `slot4_undercount_expand` | `+0.014` | `21` | Clean undercount probe |
| `slot4_undercount_expand` vs `mcq_prepend_fix` | `-0.003` | `6` | Clean MCQ disagreement probe |
| `slot2_no_trailing_zero_strip` vs `slot1_kitchen_sink_C` | `0.000` | `102` | Trailing-zero cleanup changed many answers but netted no slice gain |

The first row is especially important:

`slot3_mcq_teacher_override` is grader-visible identical to `slot1_kitchen_sink_C`.

That is the cleanest proof that the old MCQ append mechanism was broken.

### B. The broad search overlay was not mostly a content test

`slot2_search_gold_overlay` changed 67 grader-visible free-form answers and scored `-0.021`.

The repo's later correction is right: this does **not** justify the blanket statement “search gold is bad.”

It justifies the narrower statement:

> Search answers applied raw were harmful because many were shape-wrong for the grader.

Confirmed failure modes already documented in `submission/SCRATCH.md` include:
- dropped slots on multi-answer items
- added labels like `Mean=` / `A=` / `B=`
- unevaluated `*` expressions
- collapsing multi-answer outputs to one value

This is a format-application failure first, a content failure second.

### C. The two best live levers are additive

The fraction probe and undercount probe behave cleanly and additively:

| Pair | Score delta | Visible changed set |
|---|---:|---|
| `slot1_kitchen_sink_C` -> `slot1_frac_override` | `+0.007` | 8 fraction items |
| `slot1_kitchen_sink_C` -> `slot4_undercount_expand` | `+0.014` | 21 undercount items |
| `slot4_undercount_expand` -> `undercount_plus_frac` | `+0.007` | same 8 fraction items |

That exact replication is unusually strong evidence.

What it proves:
- the fraction win is not a fluke tied only to the original base
- the two levers act on disjoint grader-visible items in the tested slice signal

What it does **not** prove:
- which exact fraction items are in the slice
- which exact undercount items are in the slice

### D. Small probes are the only honest path to item-level inference

The cleanest existing scored differential sets are:

| Pair | Changed items | Score delta | Clean statement |
|---|---:|---:|---|
| `slot1_kitchen_sink_C` vs `slot4_minus_wolfram_med` | 5 | `-0.003` | At least one slice-relevant win exists among `{11, 585, 622, 787, 858}` for keeping MED |
| `slot4_undercount_expand` vs `mcq_prepend_fix` | 6 | `-0.003` | The raw-teacher MCQ replacement lost one net slice item among `{18, 457, 670, 675, 695, 720}` |
| `slot1_kitchen_sink_C` vs `slot1_frac_override` | 8 | `+0.007` | Two net slice wins live inside `{135, 207, 529, 716, 784, 817, 919, 936}` |
| `slot1_kitchen_sink_C` vs `slot4_undercount_expand` | 21 | `+0.014` | Four net slice wins live inside the 21 visible undercount fixes |

This is the right scale of claim.

Anything much broader than that becomes too underdetermined to support specific item conclusions.

---

## What the corpus does NOT cleanly prove

### 1. It does not identify exact slice membership for specific item IDs

No existing scored submission pair isolates a single changed item.

That means current data does **not** support statements like:
- “item 135 is definitely in the slice”
- “item 787 is definitely off-slice”

The honest level is set-level inference, not singleton certainty.

### 2. It does not justify 943-wide per-item backsolve interpretations

RED_ALERT kills that interpretation. The score channel only sees the ~283 public slice.

So backsolve-derived item claims should be treated as weak support unless reinforced by non-score evidence.

### 3. It does not prove broad answer-sheet overlays are item-level truth machines

Compared to `run14b_v3filtered`, the broad diagnostic submissions changed many grader-visible answers:

| Pair | Visible changed items |
|---|---:|
| `run14b_v3filtered` vs `info_2_answersheet_on_uncertain` | 271 |
| `run14b_v3filtered` vs `info_4_t1lock_sheet_rest` | 301 |
| `run14b_v3filtered` vs `slot1_kitchen_sink_C` | 188 |

Those submissions are real and useful as slice-level score measurements.

But they are far too broad to support strong per-item claims from score alone.

---

## Item 42

### Question

Can we say item 42 is correct?

### Short answer

Strongly likely yes. Strictly certain from leaderboard evidence alone, no.

### Evidence chain

From `data/MASTER_ANSWERS.csv`:
- item 42 category = FREE
- `sheet_best_answer = "No, Yes, A"`
- high sheet confidence
- all three teachers agree on `No, Yes, A`
- backsolve agrees

From `data/answer_sheet/unified_answer_sheet.csv`:
- item 42 adjusted confidence is high
- tier = 1
- teacher agreement = 1.0
- runner-up is only the reversed order `A, Yes, No`

From `postprocessing/format_candidates_117.csv`:
- item 42 is a spacing-only difference: `No, Yes, A` vs `No,Yes,A`
- Hendrycks strips spaces, so this is not a real grader distinction

From the submission corpus:
- almost every serious submission uses grader-visible `No,Yes,A`
- `slot2_search_gold_overlay` and `slot5_combined_all` are the main exceptions, where the answer degraded to `No,Yes`
- that degradation belongs to the already-documented raw-search application failure class

### Honest conclusion

The repo has strong multi-source evidence that the intended answer for item 42 is `No, Yes, A`.

What is missing is a clean leaderboard singleton probe for item 42 itself.

So the strongest honest statement is:

> Item 42 is one of the highest-confidence answers in the repo, but current submissions do not prove it through isolated slice feedback.

---

## What we know about grader format with high confidence

These rules are on solid footing because they are supported by both code/reference and submissions:

### Extraction
- MCQ uses the FIRST boxed letter
- Free-form uses the LAST boxed answer

### Safe auto-normalizations
- whitespace stripped globally
- `dfrac` / `tfrac` to `frac`
- `\left` / `\right` stripped
- degree markers stripped
- `\sqrt3` -> `\sqrt{3}`
- `\frac12` -> `\frac{1}{2}`
- standalone integer `a/b` -> `\frac{a}{b}`
- exact standalone `0.5` -> `\frac{1}{2}`
- short LHS `x=` / `D=` style prefixes stripped

### Known live non-normalizations
- fraction vs decimal in general
- symbolic vs decimal
- `*` vs `\cdot`
- multi-char prefixes like `Mean=` / `A=` / `B=`
- order in comma-lists
- per-slot boxes vs one combined box
- trailing zeros

### Important caution

`postprocessing/STRICT_NORMALIZER_SPEC.md` contains a mix of:
- proven grader facts
- plausible but unverified transformation policies

It should be read as an aggressive proposal spec, not as pure established fact.

---

## Errors this analysis corrects

### Error 1: "Slot 3 tested 26 MCQ overrides"

False in the grader-visible sense.

It tested 0 visible changes.

### Error 2: "Slot 5 combined all four overlays"

False if read literally as Kaggle-visible behavior.

The MCQ portion did not land. Grader-visible it was 84 free-form changes and 0 MCQ changes.

### Error 3: "Search gold is harmful"

Too strong.

Correct version:

> Search answers applied raw were harmful.

### Error 4: "Broad answer-sheet submissions tell us item-level truth"

Too strong.

They change hundreds of visible answers, so their scores are real but badly underdetermined for per-item inference.

### Error 5: "Remaining submission learning should all be generic format discovery"

Too broad.

Most high-value grader-format rules are already known. Remaining learning should be narrower and more tactical.

---

## Recommendation for the remaining submission budget

### The key decision question

With only a few days and limited submissions left, should all remaining submissions be used to learn more about grader format?

### Answer

No.

Not all, and not if “format learning” means broad speculative normalizer experiments.

### Why not

Because by now the competition is in a different regime.

The big format rules are already mostly known:
- MCQ first box
- free-form last box
- undercount matters
- fraction-vs-decimal matters
- ordering matters
- spaces do not matter
- raw labeled answers can break strict grading

The marginal value of learning another generic normalization fact is now lower than the value of:
- localizing which items inside known-good sets are slice-positive
- validating one or two unresolved narrow formatter hypotheses
- protecting final-pick quality on the full 943

### A better split of the remaining budget

1. Use most submissions for **small differential probes on already-proven levers**.
   This is the fastest path to converting “a good 8-item set” into “one of these 4-item halves contains the wins.”

2. Spend at most one or two submissions on **narrow unresolved formatting/application questions**.
   Example: normalized-search microprobe, not another broad raw-search overlay.

3. Reserve a few submissions for **final-pick validation**.
   RED_ALERT means the leaderboard is only the slice, but you still need to ensure your final candidates are not mechanically broken and still score competitively.

### Concrete recommended next three submissions

Assume `undercount_plus_frac.csv` is the operational base.

#### Submission 1 — fraction split A
Revert half of the 8 fraction wins back to the undercount base:
- `{135, 207, 529, 716}`

Interpretation:
- if score drops, at least one slice-positive fraction item lives in that half
- if score holds, likely both slice-positive items are in the other half

#### Submission 2 — fraction split B
Revert the other half:
- `{784, 817, 919, 936}`

Together with submission 1, this localizes the fraction signal better than the current repo can.

#### Submission 3 — normalized search microprobe
Do **not** rerun raw search. Build a 6-8 item probe where the only change is converting previously broken search answers into grader-safe form:
- preserve slot count
- strip labels
- avoid `*`
- avoid collapsing multi-answer structure
- free-form only

This answers the unresolved question:

> Was search itself bad, or was raw search application bad?

### What not to spend submissions on

- another broad answer-sheet stack
- another generic strict-normalizer bundle touching dozens of unverified transforms
- any MCQ append-to-end scheme
- broad backsolve-driven overlays treated as if they reveal 943-wide truth

---

## Bottom line

The submission corpus is genuinely useful.

But it is useful in a stricter way than the repo sometimes framed:
- excellent for mechanism discovery
- good for small-set slice inference
- weak for broad per-item certainty

The most important habit is to think in **grader-visible changed sets**, not in raw CSV edits and not in post-hoc stories.

If we keep that discipline, the remaining submission budget can still extract meaningful knowledge.