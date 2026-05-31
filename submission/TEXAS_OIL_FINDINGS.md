# TEXAS OIL FINDINGS — Multi-run Qwen ensemble (REVISED scope, pre-registered selector)

**Date:** 2026-05-31 (Day 9 close) · **Auditor:** claude_vscode · **Commit:** built on `5b52191`
**Analyzer/grader:** canonical `analyze_run.py` v3-final-final (761f903) + `grading.grader.Grader`. R20 scored-set 0.8554 = matches cohort audit (sanity-check b passed).
**Supersedes** the looser-heuristic pass in `TEXAS_OIL_DISCONFIRMED.md` (which tested H3 with single-candidate overrides → NET −34). Per ChatGPT's methodology audit, this revision **pre-registers** the selector and **restricts to a conservative 2+-run-agreement pool** — which flips the verdict to **PARTIAL**.

## Pre-registered selector (fixed before measurement)
- **H1 cross-run majority** on the universally-normalized (space-stripped) answer, **H2 SC-weighted vote** (Σ sc_vote_size/sc_total per agreeing run) as tiebreak. H3/H4 are exploratory diagnostics only, NOT deployed.
- **Conservative deployable pool:** items where **2+ qualifying runs agree** on a canonicalized answer that **differs from R20**. Single-run rescues → exploratory pool, NOT deployed.
- **No gold in the selector** (gold used only by this audit to MEASURE). Applied to all 943 (deployable form cannot reference gold_source).

## Phase 1 — rescue pool size
Per-run `math_correct` (all 943): R08 631 · R09 675 · R10 604 · R20 756 · R20b 788 · NT 582. Matrix: `submission/csvs/picks/cross_run_correctness_matrix.csv`.
Rescue pool (R20 wrong, ≥1 other right): 90 all-gold / **43 independent-gold** / 47 sheet_dependent (excluded as unreliable). Rescued by 1 run: 23 · 2 runs: 13 · 3 runs: 7 (independent).

## Conservative deployable pool (2+ run agreement)
- **Deployable overrides (gold-free selector, all 943, 2+ agree, ≠R20): 40 items.**
- On the **measurable independent-gold subset: helped 5-6, HURT 0.** Pre-commit no-regression gate: R20 baseline 444/547 → texas_oil_v1 **450/547 (+6), PASS** (no regression).
- **The risk: 26 of the 40 overrides land on `sheet_dependent`/uncertain gold** — unmeasurable locally. They could help or hurt on Kaggle. This is why the verdict is PARTIAL not CONFIRMED: the deployable set is non-damaging *where we can see*, but 65% of it is unverifiable.
- Agreement-count distribution of the 40: dominated by exactly-2-run agreement (the floor of the conservative bar).
- **Projected local-accuracy delta vs R20: +6 items on the 547 independent set.** (Slice projection DROPPED per revision #3 — the 38% rate was calibrated on 13 curated rescues and won't generalize to this noisier 40-item pool. Kaggle is the only valid prediction.)

## Exploratory pool (single-run rescues — NOT deployed)
- **23 single-run rescues** (independent gold). Single-rescuer by run: **NT 17**, R10 3, R08 3.
- Characterization: the 17 NT single-rescues ARE essentially the NT-943 join lever (already deployed as Pick-B slot 1, +1.8pp Kaggle) — they're real unique-correct, but **not extractable by cross-run agreement** (only NT got them). The 6 R10/R08 single-rescues are lucky-noisy (single older run, no corroboration). Single-run rescues need **independent gold to select** (which is exactly the NT-943 method); a gold-free 2+-agreement rule cannot reach them.

## H3/H4 diagnostic results (NOT deployed — Rule-#11 caution + damage)
On the 43-item independent rescue pool (correct-pick rate): H1 14.0% · H2 14.0% · **H3 shortest-canonical 25.6%** · H4 hybrid 11.6% · H5 oracle 100%. **H3 deployed permissively (prior run) = helped 11 / HURT 45 / NET −34** — it overrides correct R20 multi-slot answers with shorter wrong minority candidates. **This is the trap the conservative 2+-agreement bar avoids:** requiring agreement filters out the single-candidate minority noise. Canonical-form borderline (for ChatGPT): "shortest = canonical" is a bad proxy (favors slot-collapsed answers); a real tier-1 normalizer (undercount-collapse + precision) would change H3's behavior — but that's the structural-normalizer workstream, not a gold-free ensemble selector.

## Pre-registered selector verdict
**H1+H2-tiebreak on the conservative deployable pool: +6 local-accuracy on the independent set, 0 damage, Rule-#11-clean.** The structural reason it works where H3 failed: **2+ independent runs agreeing on a non-R20 answer is itself a gold-free correctness signal** (cross-run consensus on the *correction*), whereas a single minority candidate is indistinguishable from noise.

## Rule-#11 compliance (deployed CSV)
Every override value is a **Qwen run's actual `extracted_answer`**, selected purely by cross-run vote frequency (H1) + per-run SC consensus (H2) — both Qwen-only signals. No gold/teacher/sheet/Wolfram in the selector or the response field. CSV applied via canonical full-replace (`apply_overrides.py`), not the broken append. Legal.

## Verdict: **PARTIAL** (at the conservative bar)
- Texas-oil is **un-minable by permissive/majority heuristics** (DISCONFIRMED at the loose bar — see companion doc), BUT the **conservative 2+-agreement selector yields a clean +6-local, 0-damage, Rule-#11-legal override set of 40 items.**
- **Materially smaller and noisier than hoped:** only 14/40 are measurable+helpful; 26/40 are on uncertain gold (unverifiable risk). It does NOT close the 8pp Pick A gap.
- **Relationship to NT-943:** the 17 best unique-correct items (NT single-rescues) are NOT in this pool — they need gold-selection (the NT-943 method). Texas-oil and NT-943 are **complementary**, not competing: NT-943 mines gold-selectable single-run rescues; texas-oil mines gold-free multi-run-agreement rescues. Combined ceiling is still modest.
- **Deployable artifact:** `submission/csvs/picks/picks_texas_oil_v1.csv` (40 overrides) — a candidate Pick-B slot, but **lower-confidence than the NT-943 join** (65% unverifiable). Recommend it only as a *stacking* candidate on top of the NT-943 join, or as a spare-slot empirical test, NOT as a primary.

## Open Qs for ChatGPT cross-check
1. **The 26 unverifiable overrides** (sheet_dependent gold) are the whole risk. Is there a Qwen-only confidence gate (e.g. require 3+ agreement, or require SC-consensus ≥X) that shrinks to a higher-precision subset? At 3+ agreement the pool is much smaller — worth ChatGPT's view on the precision/recall tradeoff.
2. **Stacking interaction:** texas_oil_v1 overrides 40 items; the NT-943 join overrides 13. Overlap? If disjoint, a stacked CSV could combine both — but the texas-oil 26-unverifiable risk would ride along.
3. **Rule-#11 borderline (unchanged):** cross-mode agreement (NT∩Thinking) as a higher-quality selection feature — legal Qwen-only signal or smuggled quality prior?
