# PLAYBOOK TODO

**Updated**: 2026-05-28 (Day 4 start)
**Note**: This is the PLAYBOOK-specific TODO. Canonical project TODO lives at `docs/SUBMISSIONS_TODO.md`.

## P0 — Do today (Day 4 morning, cheap free-info)

- [ ] **Oracle@8 analysis on run14b** (1hr) — tells us if Lever 3 (selection) is the big lever
- [ ] **Score NoThinking SC=8 full-943 standalone** via Kaggle slot (free, diagnostic anchor)
- [ ] **Extract 39 OPL OK-status items** as override candidate CSV → spot-check 5-10
- [ ] **Analyze hardest-30 SC=16 results** (`results/hybrid/tnr-A/a2_serial_*` + `sc16_hardest30_*`) — check if any new correct answers we don't have
- [ ] **TIR feasibility research** — dispatch to research agent: "is there a vLLM-compatible TIR wrapper for Qwen3-4B-Thinking that's been used by AIMO contestants?" (see RESEARCH.md)

## P1 — Day 4 afternoon / Day 5 (commit infrastructure)

- [ ] Decide TIR-first or oracle@8-first based on morning analysis
- [ ] If TIR feasible: build sandbox wrapper, smoke test on 5 items, then 943
- [ ] If GenSelect re-run: fix candidate truncation bug, smoke test, scale to 943
- [ ] SFT v7 dataset generation kicked off on dataApp (parallel-track)

## P2 — Day 5-6 (execute chosen lever)

- [ ] Run TIR on full 943 OR SFT v7 inference (whichever is feasible)
- [ ] Layer Lever 5 (multi-slot expansion) as universal post-processing in run_inference.py
- [ ] Submit best result to Kaggle

## P3 — Day 7 (final picks)

- [ ] Pick A: best inference-only path
- [ ] Pick B: Pick A + verified overrides (Day 7 hail-mary)
- [ ] Submit to Kaggle by 2026-06-02

## RESEARCH AGENT QUEUE

(see playbook/RESEARCH.md for full prompts)

- [ ] R1: TIR + vLLM + Qwen3-4B-Thinking implementations — find a recipe or template
- [ ] R2: Process Reward Model — building one without external API; Qwen2.5-Math-PRM-7B HF
- [ ] R3: Distillation success cases on Qwen3-4B — what worked, what failed
- [ ] R4: GenSelect implementation gotchas — candidate input format, selector prompt design

## OPEN QUESTIONS FOR RAIN

- Confirm: canonical TODO is `docs/SUBMISSIONS_TODO.md` (in repo)? Or are you treating `STRATEGY_DAY4_LOCKED.md` as canonical TODO?
- Approval to dispatch R1-R4 to research agents (round 2 prompts)?
- Which Day 4 AM task starts FIRST? (recommend: oracle@8 — cheapest, highest info per hour)
