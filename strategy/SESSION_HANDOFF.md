# SESSION_HANDOFF.md — claude_strategy session state

> Read this FIRST when resuming a claude_strategy chat. Detailed findings live in their canonical homes; this is the index.

**Last updated:** 2026-05-31 ~00:45 PT (Day 9 close — deep-audit cohort complete, Pick B framework validated on Kaggle at 0.664, structural normalizer build scheduled for 05:00 Sun)

**HEAD at handoff:** see latest commit on `main`. Previous Day 8 handoff archived at `strategy/SESSION_HANDOFF_day8_close.md`.

**Time-to-deadline:** ~23 hours

---

## State summary

- **Pick A:** LOCKED at 0.745 (R20 + overrides + teacher overlay)
- **Pick B candidates:** slots 1 + 2 both scored **0.664** on Kaggle — framework CONFIRMED
- **Kaggle slots remaining:** 8 of 10 (3 current-pool expire ~18:50 Sun PT + 5 reset-pool refresh at Kaggle daily reset)
- **Deep-audit cohort (R08, R09, R10, R20, R20b):** all 5 closed, all T3-verified
- **NoThinking 943:** elevated to Pick B candidate, T1.5 + T3 verified, 13 unique-correct items confirmed
- **Final adapter-target seed:** **8 items** [41, 61, 103, 104, 127, 231, 264, 282] (post-T3 corrections from initial heuristic 11)
- **17-item still-truncated-at-32K set:** [93, 112, 161, 204, 229, 275, 308, 312, 376, 383, 445, 498, 586, 652, 724, 799, 809] — high-budget probe target

## Tonight's submissions (Day 9 close)

| Slot | CSV | Kaggle | Delta vs R20 baseline (0.646) |
|---|---|---|---|
| 1 | `picks_nothinking_join_conservative_v1.csv` | **0.664** | +1.8pp |
| 2 | `picks_nothinking_join_conservative_763safe_v1.csv` | **0.664** | +1.8pp (identical) |

**Interpretation:** Framework confirmed. 763 expression-form vs canonical form scored identically (either not on slice or grader handles both — future builds don't need disambiguator companions for expression items).

**Slice-landing rate calibration:** ~5 of 13 rescues landed on the 283-item slice = **38% rate**, vs my 30% prior. Use 35-40% for future slot estimates.

## ⏰ 05:00 Sun decisions (in priority order)

Read in this order: `submission/SLOT_PLAN.md` → `strategy/MORNING_RUNS_WATCHLIST.md` → this section

### 1. Structural normalizer build (HIGHEST EV remaining lever)
- **Build at 05:00-08:00 Sun.** Three tiers per cohort findings:
  - **Tier 1 universal** (highest priority, build first): includes **NEW: wrap-on-detect for 19 unboxed rows** (R20 source rows with no `\boxed{}` — fail Kaggle extraction unconditionally; ~6 expected slice rescues at 38% rate). Also: multi-slot collapse, MCQ-first-box, duplicate-option overcount (id 302/839 pattern), trailing-zero/precision rules.
  - **Tier 2 class-based**: detect "exact form expected" from question text (rescues id=89/345 pattern); detect "N quantities expected" for slot-count alignment.
  - **Tier 3 per-item overrides** via `postprocessing/per_item_overrides.csv` (schema'd, currently empty). Seeds: id=9 (gold split-form), id=167 (option-mapping), id=345 (precision), id=591 (undercount).
- **Expected delta vs 0.646 baseline:** +2-3pp on its own (priors are lower bounds because Day-8 append bug suppressed historical measurement — see POST_DEADLINE_AUDITS.md A1).

### 2. Morning runs on 3 Thunder A100s in parallel (~05:00-09:30 Sun)
- Read `strategy/MORNING_RUNS_WATCHLIST.md` decision algorithm
- Candidate ranking (from Day 9 evidence):
  - **High-budget probe on 17 still-truncated items** (81920/65536 tokens): ~30 min A100, low engineering, concrete target
  - **SC@32 on contested slice**: ~45 min A100, no engineering, ~11-14 A_lucky candidates
  - **NoThinking on the 17 still-truncated items**: leverages tonight's NoThinking-works finding on the items most likely to need it
  - **DeepConf**: thinner than predicted (R20 had only 3 items at >=5/8); deprioritize unless V-series shows multi-temp signal (unlikely tonight)
- **Adapter eval (SFT v5 ckpt-1176)**: separate Thunder if available; default-include for cross-run diversity
- **Adapter training on 8-item seed**: low priority given tiny target count; only if structural normalizer + morning runs aren't producing expected delta

### 3. Sunday submissions (slots 3-8 per SLOT_PLAN.md)
- Sun ~10:30: slot 3 = full normalizer on R20 (~0.669 expected)
- Sun ~12:00: slot 4 = normalizer + NT join stack (~0.676 expected, first true Pick-B frontrunner)
- Sun ~13:00: slot 5 = best morning-run winner
- Sun ~14:30: slot 6 = second-best morning-run winner
- Sun ~16:00: slot 7 = slot 4 + slot 5 stack (ceiling test, ~0.681 expected)
- Sun ~18:00: slot 8 = slot 4 + slot 6 OR normalizer v2 (finalist alternative)
- Sun ~20:00: slot 9 = diagnostic 14 (282 calibration) ONLY IF SPARE
- Sun ~22:00: slot 10 = emergency reserve / last-built finalist

### 4. Gradescope code submission (deadline Sun 23:59 PT)
- Single `run_inference()` entry point per memory #17
- Add all group members to Gradescope
- Public GitHub repo + README (GPU type, inference time, weight setup)
- Verification: top-10 = full private re-run; rest = 200 random Qs

## Discipline lock-ins (read before any big decision)

- **Memory #24 extended Day 9:** "DEEP AUDITS NO LIGHT AUDITS unless trivially so — applies to ALL big decisions, not just runs. claude_vscode same standard."
- **Locked audit pattern (high-stakes):** my-audit -> ChatGPT cross-check -> synthesize
- **Memory #11 (Pick B):** Qwen-derived only (output + format norm; no teacher overrides in submission_answer)
- **Memory #25 (LB-subset lens):** Kaggle score = ~283-item slice; prefer robust picks over slice-tuned overrides
- **Memory #2 (judger gap):** 28pp local-vs-Kaggle gap; local scores directional only
- **Memory #30 + `strategy/POST_DEADLINE_AUDITS.md`:** A1 historical-override audit pending; Day-8 append bug means historical priors are LOWER BOUNDS

## Open questions (deferred)

- Sonnet-on-Qwen empirical validation (A6 — tomorrow's adapter, if trained, IS this experiment)
- Diagnostic 14 (282) submission deferred to slot 9 / only-if-spare
- 19-unboxed-rows: ~6 expected slice rescues — embedded in tier-1 normalizer build

## Anti-patterns to avoid (Day 9 lessons)

- **Don't re-investigate the phantom normalization stack** (resolved Day 7, merged 620301c)
- **Don't reintroduce Day-8 append override mechanism** for multi-slot — use canonical full-replace via `apply_overrides.py`
- **Don't add 282 to automatic Pick-B joins** without further evidence (disputed gold; can probe via slot 9)
- **Don't isolate per-format-rule contributions on Kaggle** — offline-testable; preserve slots
- **Don't burn slots on individual rule isolation** — bundle the full normalizer into one submission for aggregate measurement

## Where to find things

- **Tonight's full picture:** read this doc, then `submission/REGISTRY.md`, then `submission/SLOT_PLAN.md`
- **The deep audits:** `inference/base_model/R{08,09,10,20,20b}_*/findings.md` (each has its own ChatGPT T3 verdict appended)
- **NoThinking audit:** `inference/base_model/NT_eval_nothinking_sc8_p943_t?/findings.md`
- **Audit templates:** `strategy/AUDIT_TEMPLATES.md` (T1, T2, T3, T4 + paste-fill spawn prompts)
- **Pre-flight discipline:** `infrastructure/pre_flight/` + memory #19
- **Post-deadline audit queue:** `strategy/POST_DEADLINE_AUDITS.md` (A1-A6)
- **Morning planning detail:** `strategy/MORNING_RUNS_WATCHLIST.md`
- **Submission strategy:** `submission/SLOT_PLAN.md` (the 10-slot locked plan)
