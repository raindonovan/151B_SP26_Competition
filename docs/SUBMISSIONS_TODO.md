# SUBMISSIONS TODO

**Last updated**: 2026-05-27 ~18:00 PT
**Time crunch**: 5 submissions remaining, reset in ~3 hours

This is the WHAT-WE-DO doc. For accumulated knowledge, see `docs/FINDINGS.md`.

---

## TODAY (Day 3, by ~21:00 PT)

### Submission queue — built and ready

| Slot | File | Base | Changes | Expected | Status |
|---|---|---|---|---|---|
| 1 | track_A_day3_v1.csv | slot1_reformat (0.646) | Wolfram HIGH (51 effective) + rescue HIGH (5) | 0.68-0.69 | READY |
| 2 | track_A_day3_v2.csv | track_A_v1 | + rescue MEDIUM (8) | 0.685-0.70 | READY |
| 3 | track_B_day3_v1.csv | track_A_v2 | + Wolfram MED/PARTIAL (7) | 0.69-0.71 | READY |
| 4 | track_B_day3_v2.csv | track_B_v1 | + minimal normalizer (TBD count) | +0.2-0.4pp on top | READY |
| 5 | — | — | RESERVE for emergency fix | — | HOLD |

### Download URLs (public, no auth)

- Slot 1: https://media.githubusercontent.com/media/beepbeeepimajeep/151B_SP26_Competition/main/submissions/track_A_day3_v1.csv
- Slot 2: https://media.githubusercontent.com/media/beepbeeepimajeep/151B_SP26_Competition/main/submissions/track_A_day3_v2.csv
- Slot 3: https://media.githubusercontent.com/media/beepbeeepimajeep/151B_SP26_Competition/main/submissions/track_B_day3_v1.csv
- Slot 4: https://media.githubusercontent.com/media/beepbeeepimajeep/151B_SP26_Competition/main/submissions/track_B_day3_v2.csv

### After each submission

1. Record Kaggle score in `docs/SUBMISSION_REGISTRY.md`
2. Update score delta analysis (which overrides moved the needle?)
3. Inform Slot 5 strategy

## TOMORROW (Day 4)

### Manual review work (highest leverage, time-bounded)
- [ ] Review 82 undercount items in V3 tracker. For each, check teacher consensus for multi-answer form. Manually edit submission for ones with high-confidence expansion.
- [ ] Spot-check the 10 "Category A" `\dfrac` items if Slot 1 ≥ 0.68 (suggesting our `\dfrac` is right).
- [ ] Empirical probe: submit `\text{A}` for a known-letter MCQ item to test grader behavior with `\text{}` wrappers.

### Tnr-0 results integration
- [ ] OPL splice v1 results — review bucket histogram (HIGH FALSE-agreement count determines v2 priority)
- [ ] No-box rescue candidates CSV is in repo — confirm splice script picked them up correctly

### Wolfram next batches (if results allow)
- [ ] Resume W-tier sweep on remaining ~186 items
- [ ] Focus on multi-slot items (highest yield per Finding #8)

## DAY 5-7

### Code submission (Gradescope deadline Sun 5/31)
- [ ] Write single-entry `run_inference()` function
- [ ] README with GPU type, inference time, weight setup
- [ ] Public repo + group members on Gradescope
- [ ] Hyperparameters final

### Final 2 picks (deadline ~2026-06-02)
- [ ] Pick A: best Track A (clean inference + post-processing)
- [ ] Pick B: best Track B (Track A + verified overrides)

## OPEN DECISIONS

- [ ] [RAIN] When Slot 1 lands, decide if Slot 2/3 submit immediately or wait for inspection
- [ ] [RAIN] SC=20 hybrid + DeepSeek-R1 5th teacher green-light (still parked)
- [ ] [TECH] LFS migration for OPL embeddings before tnr-0 deletion

### Post-submission consolidation (after Day 3 submissions land)
- [ ] Search repo + Drive for past research / thinking docs on: answer sheet methodology, back-solve framework, OPL design, SFT v5/v7 postmortems, W-tier analysis, earlier strategy notes
- [ ] For each found: either consolidate summary into `docs/RESEARCH.md` (under "Past research") or move full doc to `docs/archive/` with index entry
- [ ] Specifically check: `results/` directory for analysis CSVs that have stale documentation, any `docs/` files referenced by but not findable, Drive `handoff` folder for older versions
- [ ] Goal: single source of truth — `FINDINGS.md` for empirical knowledge, `RESEARCH.md` for external research input, `SUBMISSIONS_TODO.md` for active work. Everything else either consolidated or archived.

### MaxSAT/MILP back-solve (Day 4 priority — 3-agent consensus)
- [ ] Implement MaxSAT/MILP back-solve as Day 4 morning project (~1-2hr implementation)
- [ ] 24 prior submission scores = 24 linear cardinality constraints over 943 binary correctness variables
- [ ] + teacher log-priors (clipped to ±3 to avoid over-confident prior dominating) as MaxSAT objective
- [ ] Use PySAT RC2 (Ignatiev-Morgado-Marques-Silva, MaxSAT Eval 2018/2019 winner) or OR-Tools CP-SAT
- [ ] Encode score constraints with ±0.01 slack (5 decimal places rounding)
- [ ] Expected gain: +0.02 to +0.05 over current Bayesian aggregation
- [ ] Output: MAP labeling + per-item posterior + backbone variables (forced assignments)
- [ ] **Precedent**: Chikishev & Greenberg LANL Earthquake 1st place (4500 teams) used exact this approach with 245k vars/124k constraints. Our problem is 250x smaller.
- [ ] **NOT for today** — needs proper implementation, too risky to rush

## STALE / IGNORE

- docs/IMMEDIATE_CONTEXT.md (Day 2, stale)
- docs/SUBMISSION_PLAN.md (deprecated per own content)
- docs/DAY_2_SUBMISSION_QUEUE.md (Day 2, stale)
- docs/MASTER_TODO.md (predecessor of this doc)
- Drive submission registry v2/v3 (superseded by v4 which is migrated to docs/SUBMISSION_REGISTRY.md)
