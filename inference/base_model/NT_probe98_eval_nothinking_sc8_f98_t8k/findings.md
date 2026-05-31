# NT_probe98_eval_nothinking_sc8_f98_t8k — findings (T2 variance audit)

**Run:** `nothinking_probe98_20260526T065456Z` · SC@8 · **NoThinking mode** (prefill `</think>` bypass) · 98 items · token cap 8192 · 2026-05-26 06:58 UTC.
**Comparator:** `NT_eval_nothinking_sc8_p943_t8k` on the exact same 98 item IDs.
**Analyzer:** v3-final-final on an ADAPTED copy made with `prep_nothinking_for_analyzer.py --run-id NT_probe98_eval_nothinking_sc8_f98_t8k`.

## a. Provenance / config verification — PASS
- The raw probe file is `inference/results/hybrid/tnr-B/nothinking_probe98_20260526T065456Z.jsonl`.
- ID set matches `data/candidates_nothinking_98.txt` **exactly**: `98/98` present, no extras, no misses.
- Raw schema matches the later NT-943 run exactly: same top-level keys, `samples` as raw strings, parallel `sample_extracted` / `sample_n_output_tokens`, `mode=base`, `n_samples=8` on every row.
- Run spans `2026-05-26T06:58:51Z` to `2026-05-26T08:13:33Z`; `wall_seconds` ranges `4.40` to `117.92`, mean `46.24`.
- No summary.json exists. Provenance is from the raw jsonl, same as NT-943.

## b. Standalone score / composition — materially weaker than NT-943 on the shared slice
- **Bucket:** A=27 · A_lucky_sample=4 · B=13 · unknown=54
- **Scored set** (`bucket!=unknown`): `27/44 = 0.6136`
- **hard_independent_CLEAN:** empty on this probe. This run cannot serve as a hard-clean gate.
- **hard_independent_DIRTY:** `0/7 = 0.0000`
- **unanimous_teachers:** `27/37 = 0.7297`
- **Truncated:** `0`
- **Extracted-empty:** `0`
- **shape_fallback:** `46/98` rows, which is the first warning sign that this slice is dominated by multi-slot / formatting fragility rather than token-cap failures.

### Probe-category cuts
- **no_box (18 IDs):** all 18 remain `unknown`, but the probe emits non-empty boxed answers on all of them. Structural signal exists; gold signal does not.
- **weak_ab (50 IDs):** probe gets `8` correct vs NT-943 `23` correct on the same IDs. This is the clearest sign that the probe is not a faithful proxy for the later full run.
- **t1_control (30 IDs):** probe gets `23` correct vs NT-943 `28`. Regressions on supposed controls are non-trivial: `52, 185, 268, 332, 669, 821`. One control improves (`877`).

## c. Cross-run consistency vs NT-943 — low on the load-bearing slice
- **Exact voted-answer match:** `28/98`
- **Exact `(votes, n_voting)` match:** `22/98`
- **Exact `sample_extracted` multiset match:** `14/98`
- **Bucket match across all 98:** `85/98`, but this is inflated by `54/54` `unknown -> unknown` holds.
- **Bucket match on the scored union only:** `31/44`
- **math_correct match on the scored union only:** `32/44`

### Shared scored-set composition shifts (same 44 rows)
| run | A | A_lucky | B | voted-correct |
|---|---:|---:|---:|---:|
| NT-943 on these 98 ids | 37 | 1 | 6 | 37 |
| probe98 | 27 | 4 | 13 | 27 |

The probe is not just rephrasing the same answers differently. It loses **10 voted-correct items** on the exact same scored subset.

### Transition sets that matter
- **NT-943 A -> probe B (8):** `5, 52, 122, 240, 268, 332, 584, 821`
- **NT-943 A -> probe A_lucky_sample (3):** `185, 403, 669`
- **NT-943 B -> probe A_lucky_sample (1):** `709`
- **NT-943 A_lucky_sample -> probe A (1):** `877`

Interpretation:
- Six of the eight `A -> B` regressions are clean multi-slot collapses with `shape_fallback=True` and unanimous voting for the partial answer: `52, 122, 240, 268, 332, 584`.
- `821` is the MCQ analogue of the same problem: NT-943 had the full slot tuple `C, A, A, A`; probe collapses to `A`.
- `5` is worse than a vote-collapse story. It changes the ANOVA tuple itself to a different rounded / miscomputed answer and lands in `B` with `votes=1, n_voting=1`.
- The three `A -> A_lucky_sample` cases mean the correct answer still appeared in probe samples, but the vote did not hold it.

## d. Rescue-stability on the 15 NT-rescue items — FAIL on observed overlap
The full NT-943 run's 15 unique-correct-vs-R20 items are:

`5, 181, 257, 282, 345, 474, 578, 584, 633, 642, 712, 715, 763, 868, 917`

Only **2** of those 15 are present in the 98-item probe: **`5` and `584`**.

- **id=5:** NT-943 is `A`; probe98 is `B`. The probe swaps the correct multi-value ANOVA answer for a miscomputed / misformatted alternative.
- **id=584:** NT-943 is `A`; probe98 is `B`. The probe collapses `7z, 6w` to `6w`.

So the probe provides **zero positive confirmation** for the NT rescue lever. More strongly: on the only two rescue IDs it actually covers, it fails both.

## e. What this probe is actually good for
- It confirms provenance: `data/candidates_nothinking_98.txt` and `data/candidates_nothinking_breakdown.md` do refer to this exact run.
- It confirms the NoThinking path was live on 2026-05-26 with the same raw schema and decoding family later used by NT-943.
- It gives a negative variance read: **probe98 is not a deterministic or even near-deterministic mirror** of the later full run.

It is **not** strong evidence for or against the final NT-943 Pick-B lever, because:
- it contains no hard-clean items,
- 54/98 rows are `unknown`, and
- it only overlaps **2/15** of the rescue set.

## f. VERDICT: **YELLOW** — useful lineage check, weak determinism evidence
- **PASS** for provenance / exact ID-set identification.
- **FAIL** as a stability mirror of NT-943 on the scored slice (`27/44` vs `37/44`, only `28/98` exact voted matches).
- **FAIL** as rescue confirmation (`0/2` retained on the rescue-overlap items).

Operational take: treat probe98 as an early noisy precursor, not as a reason to down-rank the later NT-943 lever and not as a reason to trust it blindly. The real Pick-B evidence remains the fully-audited NT-943 run, not this 98-item probe.