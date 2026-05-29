# OPL Run — Decision

## CURRENT STATUS: DEAD (Day 7, 2026-05-29)

**OPL bulk-override is empirically disconfirmed. We are NOT pursuing further OPL work.**

See `findings.md` Day-7 headline for the smoking-gun spot-check. The short version: of the 39 OK-status items the embedding matcher extracted, **0 align with 3/3 teacher consensus**. The highest-similarity match (id=15, sim=0.9055) matched a completely different Loyola Chicago precalc problem. If the highest is a false positive, the rest of the OK bucket is worse.

## What this means in practice

- **No bulk-override CSV.** The Day-7 plan in the previous version of this doc (apply 39 OK items as overrides, expect +3-4pp) is cancelled. The expected gain was a ceiling that assumed parameter equality between OPL templates and our questions — that assumption is false.
- **No PARAMETERIZED re-solve.** The 844 PARAM items would require either Perl interpreter integration or sibling-grep — both expensive, and if the OK bucket (which had cleanly-extracted answers) is mostly false positives, PARAM is almost certainly worse.
- **No OPL grep-spawn.** The proposed clone-WeBWorK-and-grep workflow was a salvage attempt before the join data was in. The join evidence makes it not worth doing.
- **No routing/classification signal build-out.** Theoretically OPL paths tell us "this is a Loyola Chicago precalc chapter 9 problem" which could route Wolfram queries or seed SFT subsets — but no payoff path within the 2-day deadline window.

## What we keep

- All the OPL infra (embeddings, candidates.csv, extracted.jsonl, matcher scripts) — sunk cost, zero cost to keep. If a specific OPL question comes up later ("what was the OPL match for item N?") we can spot-query it.
- This doc + `findings.md` Day-7 entry — so the next strategy session doesn't re-estimate +3-4pp from the bare OK-count.

## Where the time goes instead

Per `strategy/SESSION_HANDOFF.md` Pending tasks (in priority order):

1. **Rebuild `undercount_plus_frac_v2`** against the updated `data/MASTER_ANSWERS.csv` (wolf B13-B16 added ~17 new undercount candidates). Strongest single next-action.
2. Lock Pick A on Kaggle UI.
3. Pick B decision (depends on #1).
4. Compute `qwen_cross_config_agree` column.
5. T1 inference-run scan.
6. Spec the remaining format-probe submission slots.

## Owner

DEAD CHANNEL — no owner. Reference only.

## History

- 2026-05-26/27: OPL embedding run (tnr-0 local + claude_strategy analysis).
- Day 4-6: held as "Day 7 hail-mary" pending submission-slot availability.
- Day 7 (2026-05-29): claude_strategy ran the OPL × teacher-consensus join. 0/39 T1-promoted. Empirical disconfirmation. Channel marked dead.
