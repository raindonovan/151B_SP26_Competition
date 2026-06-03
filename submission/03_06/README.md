# submission/03_06 — Qwen-only "inference-alone ceiling" ladder

## Goal

What is the best Kaggle score achievable from the **model alone** — Qwen-only, rule-#11
legal (Qwen-over-Qwen; selection may use gold, but every *submitted value* is Qwen's own
output)? Confirmed best so far = NoThinking join, **0.664**. This ladder tests whether
cheap Qwen-only levers stack **past 0.664**. Each slot adds exactly one layer so the
Kaggle deltas are directly readable.

**NONE of these use teacher / anchor / Opus / search / answer-sheet VALUES.** That path is
the 0.69–0.745 overlay stack and is explicitly **out of scope** here.

## Ladder

| Slot | CSV | Layer added | Source artifact | Qwen-only / rule-#11 |
|---|---|---|---|---|
| 1 | `slot1_baseline_R20/03_06_slot1_baseline_R20.csv` | — (anchor) | `submission/csvs/run14b_sc8_v1.csv` (R20 SC8/32K) | Pure Qwen base. 0.646 floor. |
| 2 | `slot2_nothinking_join/03_06_slot2_nothinking_join.csv` | NoThinking∪R20 join | `submission/csvs/picks/picks_nothinking_join_conservative_v1.csv` | Both halves are Qwen (Thinking + NoThinking). Confirmed 0.664. |
| 3 | **NOT BUILT — see "Blocked slots"** | multi-slot undercount consolidation | (no Qwen-only source) | — |
| 4 | **NOT BUILT — see "Blocked slots"** | value-preserving decimal→fraction | (source mismatch) | — |
| 5 | `slot5_max_inference_alone/03_06_slot5_max_inference_alone.csv` | cross-run consensus + high-budget Thinking rescues + expression-form safety | `overrides_texas_oil_conservative.csv` (40) + `targeted_rescue_*.jsonl` (ids 9,435,479,638) + `expression_form_audit.csv` (763) | All values are Qwen's own (consensus across Qwen runs; Thinking SC@16 voted answers; expanded-form of Qwen's own factored answer). |

**Built parent note:** slot 5 is built **on slot 2** (not slot 4), because slots 3 and 4
are blocked (below). Once 3/4 are resolved the canonical ladder parent for slot 5 should
be revisited; the slot-5 *layers* (consensus / thinking / expr-safety) are independent of
the 3/4 layers and stack cleanly on slot 2 to give a measurable Qwen-only ceiling now.

## Blocked slots (reported, not guessed — per spec "if absent, report; do not guess")

- **Slot 3 (undercount consolidation):** the committed source `data/undercount_candidates.csv`
  is **not a Qwen-only consolidation map**. Its only actionable rows are
  `use_teacher (N slots)` and its `override_source` column contains teacher/Wolfram values
  Qwen never emitted (fractions, letters, numbers) — forbidden in a Qwen-only ladder. The
  31 non-teacher rows are `manual_review (no multi-slot source)` with empty override_source
  (nothing to consolidate). 64/82 flagged ids *do* have >1 `\boxed{}` in Qwen's own
  response, but the box counts are reasoning-noise (e.g. id 585 has 43 boxes for 5 needed),
  so blind concatenation reintroduces the **item-15 additive defect** documented in
  `postprocessing/AUDIT_REPORT.md` (`multi_answer_normalize` over-collects intermediate
  boxes: `8, NONE` → `8, 8,NONE`). No reliable Qwen-only "final-answer slot" signal exists
  in the committed artifacts. **Held for strategy decision.**
- **Slot 4 (decimal→fraction):** the spec describes "the 8 ids in FRAC". The committed
  source `submission/28_05/csvs/slot1_frac_override.csv` is **not** an 8-item frac map — it
  is a full 943-row post-processed CSV that **differs from BASE on 604 rows** (decimal
  trimming, multi-slot teacher expansions, etc.). Applying it literally would inject 604
  changes — including teacher-sourced multi-slot expansions (e.g. id 25 → `\frac{8}{63}…`)
  — violating Qwen-only scope. **Held for strategy decision** (need the actual 8-id
  value-preserving frac list, or confirmation to derive it).

## Phase 2 — GPU levers (NOT built here; separate claude_thunder dispatch)

1. **GenSelect re-run** with full-length candidates + 5-item smoke (prior PoC died on ~500-char truncation).
2. **Multi-temperature SC** (diversify sampling temperature across the SC set).
3. **DeepConf** (plumb `logprobs=20` into `run_vllm_sc.py`, re-vote the contested slice with vote margin ≤5/8).
4. **Full high-budget Thinking SC@16 on ALL R20-wrong multi-slot items** (slot 5 only overlays the 4 we already have: 9, 435, 479, 638).
