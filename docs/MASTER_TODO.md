# MASTER TODO Session 6 -- 2026-05-26 evening

Last updated: 2026-05-26 evening, after slot1_minimal_norm=0.643 + Thunder Gate 4 launch.

> **Migrated to repo 2026-05-27 ~01:30. "IN FLIGHT" section partially stale** -- see `docs/IMMEDIATE_CONTEXT.md` for current state.

## IN FLIGHT (as of 5/26 eve)

- tnr-0: Phase A1 (SC=16 weak default 128, 49K/24K) -> A2 (SC=16 hardest 30, 82K/64K). ETA ~3.5 hr.
- tnr-1: B1 (NoThinking probe 98, 5K) -> B2 conditional (full 943) -> B4a -> B4b -> B5. ETA ~3 hr.
- Watchdog on each Thunder pushing per-instance branches every 5 min.

## PENDING -- TONIGHT (after Thunder completes)

- [ ] Audit phase outputs
- [ ] Re-run truncated samples at higher token budget
- [ ] USC normalize-then-vote on SC=16 outputs
- [ ] Build 3-part hybrid splice candidate CSV
- [ ] Build NoThinking-derived submission candidate (if B2 ran)
- [ ] Prep id=184/317 override resolution CSV

## DAY 2 -- 5/27

### Morning (3 Kaggle slots fresh)
- [ ] Slot 1: 3-part hybrid splice (normalized)
- [ ] Slot 2: NoThinking submission (if B2 ran)
- [ ] Slot 3: id=184/317 override resolution

### Afternoon
- [ ] Interpret morning Kaggle scores -> real-inference ceiling estimate
- [ ] **v7 DECISION POINT**: GO if ceiling <0.68, NO-GO if >=0.68
- [ ] Extended PACE start: Wolfram-verify computable items across all 943
- [ ] v5 epoch test (3/6/9 checkpoint comparison)
- [ ] Sheet v6 build with anti-bias rules

## DAY 3 -- 5/28

### Based on v7 decision
- [ ] IF v7 GO: train v7 multi-teacher on Thunder, infer, submit
- [ ] IF v7 NO-GO: GenSelect zero-shot on Tier 5 / no-box items

## DAYS 4-5 -- BUFFER

- [ ] Final submission selection (2 final picks)
- [ ] Continue Extended PACE if items remain
- [ ] DataApp repo cleanup -- only if time

## STRATEGIC BACKLOG

- [ ] DoRA training -- PARKED
- [ ] Diverse-prompt ensemble -- PARKED (superseded by SC=16+NoThinking)
- [ ] Confidence-weighted voting -- PARKED
- [ ] PRM verification -- PARKED
- [ ] Bayesian back-solve full rebuild -- DEFER

## DEAD (retired)

- Format normalizer beyond minimal
- dfrac->frac probe submission
- comma_collapse rule
- Format-driven adapter recovery
- SFT v6 trivial retrain
- V0-V4 variant ablation
- Higher SC count on hard items (A2 already covers)

## LOCKED FACTS

- 3 submissions/day Kaggle cap
- Canonical Kaggle format: `\dfrac` + comma+space + single `\boxed{}`
- Grader extracts LAST `\boxed{}`, string-match with dialect tolerance
- 18 no-box items unsolvable by LLM consensus
- vLLM 0.20.2 natively supports thinking_token_budget
- Minimal normalizer rescues ~4 items
- Adapter v5: ~3 semantic items regression vs base, NOT format-broken
- TP=2 works on Qwen3-4B-Thinking-2507 with 2x A100-80GB
- NoThinking prefill: append `"Okay, I think I have finished thinking.\n</think>\n\n"` after chat template
- NoThinking max_tokens: **8192** (5K caused 17% truncation)

## VALUE-PER-HOUR RANKING

1. Audit Thunder outputs + build hybrid splice -- +1-3pp expected
2. Apply normalizer to all Day 2 submissions -- +0.4pp confirmed
3. id=184/317 override test -- settles v7 question
4. Extended PACE on 200 items -- +1-2pp expected
5. v5 epoch test -- low expected return
6. v7 training (conditional) -- +2-4pp IF ceiling <0.68
7. GenSelect zero-shot on 71 items -- +0.3-0.5pp
8. DataApp cleanup -- zero score impact
