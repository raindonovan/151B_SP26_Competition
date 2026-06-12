# inference/FINDINGS.md — Cross-cutting inference findings (adapter + base_model)

> **Scope**: findings that hold across BOTH adapter and base-model inference runs. Adapter-only patterns → `inference/adapter/FINDINGS.md`. Base-only patterns → `inference/base_model/FINDINGS.md`. Single-run findings → that run's `findings.md`.
>
> This document is seeded from the pre-Day-7 carryover in `inference/RESEARCH.md` and `inference/SCRATCH.md`, and will be expanded as we catalog each run.

## Locked configuration (applies to BOTH adapter and base_model inference)

- **Model**: `Qwen3-4B-Thinking-2507` (locked by competition rules — no substitution).
- **Sampling**: `temperature=0.6, top_p=0.95, top_k=20, min_p=0`. `presence_penalty` preferred over `repetition_penalty`.
- **Token budget**: `max_tokens=49152, thinking_budget=24576` for typical items; `81920/65536` for hardest items.
- **NoThinking**: prefill-only (`"Okay, I think I have finished thinking.\n</think>\n\n"`). `enable_thinking=False` is a silent no-op on this model.
- **Greedy decoding**: contraindicated for thinking mode (official Qwen guidance).
- **Adapter loading**: keep as PEFT adapter (NO merge). The 2026-05-22 attempt to merge v5 weights regressed.

## Two-bucket framework for tier-1 items (CONFIRMED, Day 6)

See `postprocessing/FINDINGS.md` F7 and `strategy/HOW_WE_KNOW_CORRECTNESS.md` for the full framework.

For every tier-1 item (`wolfram_confidence=HIGH ∧ search_status=GOLD ∧ 3/3 teachers`), classify the inference output as:
- **Bucket A**: some run (any SC/NoThink/etc.) produced the correct MATH → format-fix and submit. NO adapter needed for this item.
- **Bucket B**: NO run ever produced the correct math → real math regression. Adapter training candidate.

The format layer applies to BOTH buckets — even Bucket-A items can be graded wrong if emitted in the wrong format (the F7 finding, +2 slice items from pure decimal→fraction flip).

**Operational implication**: cross-reference every tier-1 item's gold answer against the voted answer in EVERY run's `samples.jsonl`. Needs format-aware Hendrycks-normalized comparison, not raw string match.

**Status (Day 7)**: framework is locked; the actual cross-run scan has NOT been executed yet. It's the north star per `strategy/SESSION_HANDOFF.md`.

## Cross-cutting patterns (to be populated as we catalog)

_Will be filled in run-by-run. Examples of what would land here:_
- "SC plateau at N≈16 across all base_model AND adapter runs we've tested"
- "Per-temperature SC diversification helps base_model but not adapter (or vice versa)"
- etc.

---
## [Rain] 2026-06-04 — External validation (NoThinking / 151B paper line)

**GOLD (filed same session):** Independent field confirmation that **truncation** and **thinking-length** are the core failure axes on this model family, and that **inference-time scaling beats SFT** on this task — direct support for our token-budget and inference-first findings.

**Repo tie-in:** Locked budgets at `inference/FINDINGS.md` L11 (`49152/24576`, hard items `81920/65536`); R20 deep audit shows truncation as the dominant 16K failure mode and 32K rescuing 72/89 always-truncated-at-16K items (`inference/SCRATCH.md` L247, L338). SFT lines peaked below inference-only SC@8 (`strategy/INFERENCE_TECHNIQUES.md` L9–L13: 0.646 base vs SFT v3–v5 ≤0.639); competition outcome aligned with inference discipline over adapter/SFT (`post_comp/POST_COMP_DEBRIEF_MEETING.md` L57–L63, win-forward `30_05_slot4_aggressive_v2` 0.745/0.684).

## Per-folder findings docs

- `inference/adapter/FINDINGS.md` — adapter-only cross-run patterns
- `inference/base_model/FINDINGS.md` — base-model-only cross-run patterns

## Related external docs

- `strategy/INFERENCE_TECHNIQUES.md` — tried-vs-untried inventory
- `strategy/HOW_WE_KNOW_CORRECTNESS.md` — the keystone mental model
- `postprocessing/FINDINGS.md` — the F-series (esp. F7 on tier-1 format errors)
