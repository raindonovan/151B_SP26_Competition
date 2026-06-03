# submission/03_06 — RUN_REPORT

Built by claude_vscode, 2026-06-03. File assembly only — no GPU, no Kaggle submit.

## Source files (verified before build)

| key | path | sha1 | rows |
|---|---|---|---|
| BASE | submission/csvs/run14b_sc8_v1.csv | 7fd5a33af245… | 943 |
| NTJ | submission/csvs/picks/picks_nothinking_join_conservative_v1.csv | 7b2f6e221c4c… | 943 |
| TXOV | submission/csvs/picks/overrides_texas_oil_conservative.csv | 15ead1702ccf… | 40 overrides |
| THJL | inference/base_model/TH_targeted_rescue_thinking_sc16_f61/targeted_rescue_20260526T201046Z.jsonl | cd52bfabb73b… | (jsonl) |
| EXPR | submission/csvs/picks/expression_form_audit.csv | ab7d33b097c2… | 13 ids (1 FLAG: 763) |
| UNDER | data/undercount_candidates.csv | 2d6e2ec5dda4… | 82 (slot-3 blocked) |
| FRAC | submission/28_05/csvs/slot1_frac_override.csv | 22410a0a6e51… | 943 (slot-4 blocked) |

**Pre-flight gate PASS:** NTJ/NTOV/TXOV/FRAC/EXPR/UNDER all unpadded int ids, id-space ⊆ BASE (0..942). No row-position merge.

## Slots

### slot1_baseline_R20
- Byte copy of BASE. sha1 = `7fd5a33af245…` (== BASE). 0.646 floor.

### slot2_nothinking_join
- Byte copy of NTJ. sha1 = `7b2f6e221c4c…` (== NTJ). Kaggle 0.664 confirmed.

### slot5_max_inference_alone (built on slot2)
- **Layer a — cross-run consensus (TXOV, 40 ids):** in-place replace last `\boxed{}` value
  with each id's `override_value`. id 302's consensus value (`H`) already matched slot-2's
  box → no-op (correct). 39 effective consensus changes.
- **Layer b — high-budget Thinking rescues (THJL):** ids 9, 435, 479, 638 set to the EXACT
  `voted_answer` pulled from `targeted_rescue_*.jsonl` (not findings.md):
  - 9 → `L - 8x, 6F`
  - 435 → `0.4457, 0.5368, A`
  - 479 → `40.36, 43.64, 40.01, 43.99`
  - 638 → `0.15, (-infty, -1.75) U (1.75, infty), 0.88, D`
  - 435 and 479 are also in TXOV; thinking_rescue applied **after** consensus (THJL is the
    authoritative exact-voted value) — recorded as `thinking_rescue` in change_log.
- **Expression-form safety (EXPR):** only FLAG row is 763 → `13, \frac{8}{3}` (expanded,
  value-equality verified). Replaced parent's factored/unevaluated `4+9,8\div3`. Other EXPR
  ids are SAFE (no action).
- **Result:** 42 rows changed vs slot 2. row count 943, id-set == BASE, order preserved,
  box-count invariant holds on every changed row (replace-in-place; no box added/removed;
  reasoning text outside the box byte-identical). sha1 = `c4b72274e809…`.
- Changed ids: 2, 9, 25, 55, 67, 82, 143, 145, 169, 177, 184, 242, 273, 297, 299, 354, 370,
  387, 435, 449, 479, 480, 489, 491, 502, 537, 638, 647, 653, 655, 657, 694, 756, 763, 794,
  812, 833, 842, 858, 887, 897, 923. (change_log.csv has id/layer/before_box/after_box.)

## Blocked slots
- **slot3** — `data/undercount_candidates.csv` is teacher-sourced (`use_teacher`/teacher
  override_source), not Qwen-only; the Qwen multi-box signal is reasoning-noise (item-15
  defect risk). No clean Qwen-only consolidation source. Held for strategy.
- **slot4** — `submission/28_05/csvs/slot1_frac_override.csv` is a full 943-row pipeline CSV
  (604 rows differ from BASE, incl. teacher multi-slot expansions), not the "8 frac ids" the
  spec describes. Held for strategy (need the actual 8-id value-preserving frac list).
