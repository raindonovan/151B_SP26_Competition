# 29_05 CSV Picks — Findings Log

This file is the working notebook for the staged picks placed in `submission/29_05/csvs/`.

It is meant to hold four things for each pick:
- why the pick exists
- what exact question it is testing
- the Kaggle result once submitted
- the interpretation and downstream action

---

## Current staged picks

| Pick | File | Type | Primary goal |
|---|---|---|---|
| 1 | `PICK_01_control_undercount_plus_frac.csv` | control | Re-anchor the current best known stack in this submission block |
| 2 | `PICK_02_minimal_grader_normalized.csv` | tiny normalizer probe | Test whether extremely safe typography-only cleanup still changes anything on the live judge |
| 3 | `PICK_03_label_prefix_probe.csv` | targeted adverse probe | Test whether multi-character label prefixes are still harmful |

---

## Background for this batch

### Why this batch exists

This batch was staged after a repo-wide grader and submission audit, followed by a failure analysis of the canonical normalizer.

The main constraints going into these picks were:
- undercount plus the 8-item fraction layer is the strongest currently validated stack
- the canonical normalizer in `postprocessing/scripts/normalizer.py` initially failed badly on live-style submission data because it over-collected boxed answers and truncated complete multi-answer outputs
- that catastrophic failure has since been fixed, but these three picks were staged as the first safe probe set before broad canonical-normalizer submission use was reintroduced

### What we believed before staging

- Structural rules were still the most trustworthy class of grader knowledge.
- Trailing-zero stripping was not worth an early slot as a standalone probe.
- Blanket MCQ teacher overrides were not a high-EV follow-up.
- The first useful unresolved format family to probe cleanly was multi-character label prefixes.

---

## Pick 1 — `PICK_01_control_undercount_plus_frac.csv`

### Intent

This is the control file for the batch.

It is the existing undercount-plus-frac stack, brought into `submission/29_05/csvs/` so the rest of this batch has a stable local reference point.

### Why this is the control

This stack is the strongest validated combination from prior evidence:
- undercount expansion already improved score materially from the 0.692 base
- the 8-item fraction layer already improved score on its own
- the same fraction layer also improved score again when stacked on the undercount base

So this file is not exploratory. It is the anchor.

### Question it answers

If submitted in this batch, it answers only one question:

> Does the currently believed best stack still behave like the control we think it is?

### Pre-submit expectation

Expected behavior: baseline / control score.

### Result

Kaggle score: _not confirmed from screenshot_

### Analysis

The score for the control file is not visible in the provided screenshot.

Operational note: the screenshot appears to show `PICK_03_label_prefix_probe.csv` twice and does not show `PICK_01_control_undercount_plus_frac.csv` by name. So the control score should not be inferred without checking the Kaggle submission history directly.

---

## Pick 2 — `PICK_02_minimal_grader_normalized.csv`

### Intent

This is the smallest safe normalizer probe.

It was built with `postprocessing/scripts/apply_grader_normalization.py` in `minimal` mode rather than with the full canonical normalizer.

### Exact transform family

This pick only applies tiny typography-level cleanup to the content of the last boxed answer:
- strip thin-space macros
- strip `\left` and `\right`

No broad structural rewrite, no fraction promotion, no aggressive cleanup.

### Why this probe matters

This pick asks the safest version of the normalizer question:

> Is there still any live value in tiny, obviously safe answer-surface cleanup?

If this is flat, then the smallest formatting-only surfaces are probably exhausted and we should not waste early slots on broader “safe cleanup” bundles.

### Local validation before staging

- Raw row changes versus the control: 1
- Grader-visible answer changes versus the control: 0

So this is effectively a near-no-op probe. That is intentional.

### Pre-submit expectation

Expected behavior: flat or near-flat versus Pick 1.

### Result

Kaggle score: **0.713**

Delta vs Pick 1: _unknown from screenshot because Pick 1 is not shown by name_

### Analysis

This probe came back flat at 0.713.

That is exactly what the local validation suggested: the file changed 1 raw row and 0 grader-visible answers versus the control candidate. So this result is consistent with the view that tiny typography-only cleanup is currently inert on the live judge.

Practical conclusion: early submission budget should not be spent on broad bundles of similarly tiny cleanup rules unless they introduce a genuinely new grader-visible surface.

### Planned interpretation

- If flat: tiny typography cleanup is effectively dead as an early submission lever.
- If positive: even the smallest surface cleanup still matters and justifies a careful next-step normalizer probe.
- If negative: something that looked obviously safe is not actually safe on the live judge, which raises the bar for all broader normalizer submissions.

---

## Pick 3 — `PICK_03_label_prefix_probe.csv`

### Intent

This is a clean adverse probe for multi-character label prefixes.

It does not rerun raw search overlays. It keeps the existing grader-visible answer values and only changes the final answer surface on a targeted carrier set.

### Exact carrier set

The probe targets these 13 free-form ids:
- 20
- 97
- 108
- 139
- 163
- 236
- 256
- 296
- 431
- 462
- 576
- 642
- 795

### Exact transform

For each targeted row, the probe appends a final boxed answer of the form:

`Answer=<current grader-visible answer>`

The content is intentionally unchanged. Only the label-prefix surface is changed.

### Why this probe matters

This pick asks a much cleaner question than the old raw search overlay:

> Are multi-character prefixes like `Answer=` still harmful under the current judge?

That isolates one stale-risk rule family without mixing in search-content quality, collapsed multi-answer issues, or symbolic-form confounds.

### Local validation before staging

- Grader-visible answer changes versus the control: 13
- Those 13 changed rows are exactly the targeted carrier items

### Pre-submit expectation

Expected behavior: if the old strict behavior is still live, this should lose relative to Pick 1.

### Result

Kaggle score: **0.713**

Delta vs Pick 1: _unknown from screenshot because Pick 1 is not shown by name_

### Analysis

This probe also came back flat at 0.713.

Interpretation: the targeted `Answer=` prefix on the 13 carrier items did not move the leaderboard score. That weakens the old strict-prefix hypothesis substantially for the current judge state.

What this does **not** prove:
- it does not prove every possible multi-character label is safe
- it does not prove raw search overlays are safe
- it does not prove larger expression-surface changes are inert

What it **does** prove:
- the specific `Answer=<existing grader-visible answer>` surface on this 13-item carrier set is not a live lever on the current public slice
- generic label-prefix fishing should move down the queue

### Planned interpretation

- If negative: label stripping remains a real live lever.
- If flat: the current judge may now tolerate these prefixes better than the old strict model did.
- If positive: that would be surprising and would require re-checking the exact answer-surface extraction assumptions before drawing conclusions.

---

## Canonical normalizer status at staging time

The broad canonical normalizer in `postprocessing/scripts/normalizer.py` was investigated during this chat.

### Initial failure

When first tested end-to-end on the control submission, it changed far too many grader-visible answers because:
- it gathered too many boxed expressions from the full response on multi-answer items
- it truncated complete final boxed answers based on expected slot count metadata

### Fixes applied during this chat

Those failures were repaired by:
- switching multi-answer extraction to the last contiguous boxed group
- preferring a complete final boxed multi-answer when it already exists
- stopping destructive truncation of complete final multi-answer outputs

### Current local comparison after the fix

Against the same undercount-plus-frac control:
- `conservative` mode: 2 grader-visible deltas
- `default` mode: 5 grader-visible deltas

So the catastrophic failure is gone. The canonical normalizer is no longer in the old broken state that originally caused these safer probes to be staged.

This matters for later picks, but these three files remain the first staged batch for this folder.

---

## Results table

| Pick | Score | Delta vs Pick 1 | Immediate conclusion | Next action |
|---|---|---|---|---|
| 1 | _not confirmed from screenshot_ | baseline | Control score not visible by name in the provided image | Check Kaggle history before using as the baseline for this batch |
| 2 | 0.713 | unknown from screenshot | Minimal typography-only cleanup is flat / inert | Do not spend more early slots on tiny safe-cleanup bundles |
| 3 | 0.713 | unknown from screenshot | `Answer=` prefix probe is flat on the targeted 13-item carrier set | Deprioritize generic label-prefix probing |

### Upload-note from screenshot

The screenshot appears to show:
- `PICK_03_label_prefix_probe.csv` at **0.713**
- `PICK_02_minimal_grader_normalized.csv` at **0.713**
- `PICK_03_label_prefix_probe.csv` again at **0.713**

So either:
- the label-prefix probe was uploaded twice, both times scoring 0.713
or
- one of the visible names in the screenshot is mislabeled in the UI capture

Until the Kaggle history is checked directly, the control file should be treated as unconfirmed in this findings log.

---

## Batch-level analysis

Current signal from the visible results:

- The minimal normalizer probe is flat. That is aligned with the local pre-submit validation and strongly suggests tiny typography cleanup is not where early submission EV is hiding.
- The targeted label-prefix probe is also flat. On the current public slice, this specific prefix family does not appear to be a live scorer.
- Because the screenshot does not show the control file by name, the batch should be interpreted as: two negative/flat probes plus one unverified submission identity.

Immediate strategic consequence:

- move away from tiny cleanup probes
- move away from generic label-prefix probes
- focus the next slots on either the repaired canonical normalizer in a tightly controlled mode, or on a different unresolved surface family with real grader-visible change

---

## Notes

- This file should be updated after each submission returns.
- If later picks are staged into this same folder, add them below with the same structure rather than scattering rationale across chat or scratch files.
