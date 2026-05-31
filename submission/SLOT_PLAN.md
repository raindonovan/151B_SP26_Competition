# Pick-B Submission Plan — Locked Day 9 (2026-05-30 ~23:55 PT)

**Pick A: LOCKED at 0.745** (R20 + overrides + teacher overlay). Do not modify.

**Pick B: 10-slot plan below.** Synthesized from claude_strategy proposal + ChatGPT rigorous cross-check. **Remain flexible** — re-evaluate after each measurement. Memory rule "all big decisions get deep audits" applies to slot-allocation changes too.

## Slot allocation (10 slots, ~24 hr to deadline)

| # | When (PT) | Candidate | Hypothesis | Range (low / pt / high) | Gate |
|---|---|---|---|---|---|
| 1 | Sat ~midnight | Conservative 13 (`picks_nothinking_join_conservative_v1.csv`) | Qwen-over-Qwen NoThinking join is real Kaggle lift over 0.646 | 0.652 / 0.660 / 0.667 | None — anchor |
| 2 | Sat ~midnight | **763-safe variant** (pre-evaluate `4+9, 8÷3` → `13, 8/3`) | Disambiguate 763 grader-evaluation risk from framework | 0.651 / 0.661 / 0.668 | Build via vscode tonight |
| 3 | Sun ~10:30 | Full normalizer v1 on R20 | Structural lever; append-era priors are lower bounds (per A1 bug) | 0.655 / 0.669 / 0.678 | Normalizer built + audit-passed |
| 4 | Sun ~12:00 | Normalizer + Conservative 13 stack | Additive — NT join + structural fixes don't overlap | 0.662 / 0.676 / 0.686 | Slot 3 non-regressive |
| 5 | Sun ~13:00 | Best morning-run winner | Fresh inference adds orthogonal wins vs post-processing | 0.650 / 0.664 / 0.676 | Run clears its predeclared threshold (per MORNING_RUNS_WATCHLIST) |
| 6 | Sun ~14:30 | Second-best morning-run winner | Two distinct inference levers, not one noisy hit | 0.648 / 0.660 / 0.672 | Different changed set vs slot 5 |
| 7 | Sun ~16:00 | Slot 4 + slot 5 stack | Ceiling test | 0.666 / 0.681 / 0.692 | 4 and 5 both positive |
| 8 | Sun ~18:00 | Slot 4 + slot 6 OR normalizer v2 | Finalist alternative | 0.664 / 0.679 / 0.690 | Distinct value vs slot 7 |
| 9 | Sun ~20:00 | **Texas-oil** (`picks_texas_oil_v1.csv`, 40 overrides) — swap from diagnostic-14 (Day-9 lock) | 2+-agreement gold-free Qwen ensemble; **+6 items on 547-item measurable independent-gold subset per TEXAS_OIL_FINDINGS Phase 1 pre-commit gate; 26/40 unmeasurable risk (sheet_dependent gold).** [Day-9 self-audit per T4: prior "11/40 independent of normalizer + NT-13" rationale was misclassified — 9 of those 11 items had R20=1 (texas-oil override no-op/regress), 1 had no rescuers (id 184), only 1 was a clean rescue candidate (id 887). Slot 9 conclusion stands on empirical +6/547 baseline; flawed rationale removed.] | (vs Pick-B-best at slot 8) +0.0pp / +0.4pp / +0.7pp | Fire only if Pick B at slot 8 hasn't hit ceiling AND ≥1 unused slot remains. Drop if slot 4/7 already cleared ~0.685. Diagnostic-14 retired (per overlap audit: 282 calibration is niche, slot better-spent on texas-oil residual) |
| 10 | Sun ~22:00 | Emergency reserve / last-built finalist | Deadline insurance for surprise candidates | n/a | Last 2-3 hours only |

**Slots 1-5** consume the current-pool (5 slots expiring ~18:50 Sun PT).
**Slots 6-10** consume the reset-pool (5 slots refreshing Sun midnight Pacific).

## Tonight ceiling: 2 slots, then sleep

Per ChatGPT discipline: **at most 2 current-pool slots before sleep.** Slots 1 + 2 fire ~midnight. Hold 3 current-pool slots for the 10:00-18:00 Sun build window (slots 3-5). Reset-pool used Sun afternoon/evening (slots 6-10).

## Reserve threshold

**Keep 3 slots unspent until the last 2-3 hours.** Slots 8, 9, 10 are the reserve buffer. Don't burn them on speculative tests before ~20:00 Sun.

## Strongest failure mode this plan defends against

(ChatGPT-flagged, locked-in awareness:)

If slot 1 (Conservative 13) scores meaningfully below expected range AND we don't have slot 2 (763-safe variant) to disambiguate, we'd incorrectly conclude "join framework failed" and underinvest in slots 3-4 (the structural-normalizer + stack), which is empirically the highest-upside lever (append-era priors are lower bounds). **Tonight's slot 2 protects the integrity of tomorrow's 4-slot structural investment.**

## Discipline rules locked

- Deep audits, no light audits, unless trivially so — applies to ALL big decisions, not just runs (memory #24)
- Every slot tests a deliberate hypothesis (memory #1)
- claude_vscode same audit standard as claude_strategy
- Slot plan is FLEXIBLE — re-evaluate after each measurement; deviate only with deliberate hypothesis update

## What can change after each slot

| If we see... | Then... |
|---|---|
| Slot 1 in range, slot 2 ≈ slot 1 | Framework validated; 763 risk is real but small; full Sunday plan unchanged |
| Slot 1 below range, slot 2 above slot 1 | 763 hurt slot 1; framework fine; full plan unchanged (but watch for grader-evaluation issues in other items) |
| Both slots in range | Framework strongly validated; possibly skew Sunday more aggressively toward NT-join stacks |
| Both slots below range | Framework or slice composition issue; slow down Sunday, debug before slot 3 |
| Any slot scores 0.78+ | Real shot at competitive Pick B; lock that variant immediately as Pick B candidate |
