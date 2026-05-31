# TEXAS OIL AUDIT — Multi-run Qwen ensemble feasibility

**Date:** 2026-05-31 (Day 9 close) · **Auditor:** claude_vscode · **Commit:** built on `6a56079`
**Analyzer/grader:** canonical `analyze_run.py` v3-final-final (761f903) + `grading.grader.Grader` (same as all cohort audits). Pre-commit sanity (b): R20 scored-set acc = 426/498 = **0.8554**, exactly matching the cohort audit → Phase-1 numbers validated.
**Hypothesis:** the union of correct items across multiple Qwen runs is a Rule-#11-legal pool that a Qwen-only heuristic can mine for a Pick-B rescue set substantially larger than the NT-943 join (13 items, +1.8pp).

## Phase 1: Rescue-pool size — ON THE TABLE (pool > 25), continued
Per-run `math_correct` (all 943): R08 631 · R09 675 · R10 604 · R20 756 · R20b 788 · NT 582.
Matrix saved: `submission/csvs/picks/cross_run_correctness_matrix.csv` (id, 6 run cols, total_correct, gold_source, rescue flag).

**Rescue pool (R20 wrong AND ≥1 other Qwen run right):**
- **90 items on all-943 gold**, but only **43 on INDEPENDENT gold** (wolfram_HIGH/search_GOLD/unanimous_teachers). The other 47 sit on `sheet_dependent` gold (contaminated/uncertain — possible noise, excluded from the honest analysis).
- Rescued by exactly N other runs (independent set): 1→23, 2→13, 3→7.
- 43 > 25 → continued to Phase 2. **(Caveat already visible: R20b is a derivative of R20, not an orthogonal run, slightly inflating "rescuer" counts.)**

## Phase 2: Heuristic performance — heuristics FAIL on the pool
Correct-pick rate on the 43-item independent rescue pool (AUDIT measures with gold; the heuristics themselves use ONLY cross-run signal):
| Heuristic | correct picks | rate |
|---|---|---|
| H1 cross-run majority | 6/43 | 14.0% |
| H2 SC-weighted vote | 6/43 | 14.0% |
| H3 canonical (shortest-form) | 11/43 | 25.6% |
| H4 hybrid (H1→H2→H3) | 5/43 | 11.6% |
| **H5 oracle (ceiling, not deployable)** | **43/43** | **100%** |

Candidate-set sizes: mostly 2-4 unique answers per item.

**Why every deployable heuristic fails — the structural finding:**
- **R20's WRONG answer is the cross-run majority/co-majority on 41 of 43** pool items.
- **The CORRECT answer is a strict minority on 35 of 43.**
- 4 of the 6 runs share v1-ish config lineage (R08/R09/R10/R20/R20b), so they **agree on the same wrong answer**; the correct answer is the rare minority. Majority- and SC-weighted heuristics therefore vote *for* R20's wrong answer by construction. The minority-correct signal is **indistinguishable from minority-noise without gold.**

## Phase 3: Validation — DEPLOYED heuristic is NET-NEGATIVE, no CSV built
Best deployable heuristic (H3 shortest-canonical) applied selectively across the independent set (override only when shortest ≠ R20, else keep R20):
- **helped 11, HURT 45, NET −34.**
- It damages 4× more than it rescues: "shortest form" overrides many *correct* R20 multi-slot answers with shorter wrong minority candidates.
- **No `picks_texas_oil_v1.csv` was built** — it would regress the 0.8554 R20 baseline badly (pre-commit gate f would fail). Per the Phase-1/3 stop rule, the audit short-circuits here.

## Rule-#11 compliance
Moot (no CSV deployed), but for the record: the heuristics tested used only Qwen-only signals (cross-run vote frequency, per-run SC consensus, surface-form length) — no gold/teacher/sheet/Wolfram in the selection. Gold was used **only by the audit to MEASURE** correct-pick rate, never by the heuristics. So the framework is Rule-#11-clean; it just doesn't work.

## Verdict: **DISCONFIRMED**
- Pool exists (oracle 100%, 43 independent items) but is **un-minable by any Qwen-only heuristic** (best deployable: 25.6% pick rate, NET −34 when applied).
- **Root cause:** correct rescues are MINORITY answers; the runs' shared config lineage makes the WRONG answer the majority. Cross-run voting amplifies the consensus error, not the minority truth.
- **This is exactly why NT-943's join worked and texas-oil doesn't:** NT-943 used **independent gold to SELECT** the 13 items (then filled with Qwen values). Texas-oil tried to replace gold-selection with a vote heuristic — **and that selection step is irreplaceable.** Cross-run Qwen ensembling has no gold-free way to know *which* minority answer is the right one.
- **NT-943 join (+1.8pp, 13 items) is confirmed as the ceiling of gold-free cross-run Qwen ensembling** for Pick B. The path to more rescues is MORE INDEPENDENT GOLD (more wolfram/search verification to expand the selectable set), not more runs or smarter vote heuristics.

## Open Qs for ChatGPT cross-check
1. **Is there a Qwen-only signal I missed** that correlates with minority-correctness? I tested vote-frequency, SC-consensus, and surface-length. Candidates I did NOT test: per-run reasoning-trace length/confidence markers, agreement *between specific run pairs* (e.g. "NT agrees with R09 but not R20" as a feature). These edge toward over-fitting and I'd want methodology sign-off before pursuing — but flagging in case there's a principled one.
2. **R20b-as-a-run:** I included it but it's an R20 derivative (not orthogonal). Excluding it would shrink the pool slightly; doesn't change the DISCONFIRMED verdict (the structural minority problem is independent of R20b).
3. **Rule-#11 borderline:** "candidate appears in NoThinking AND a Thinking run" as a selection feature — is cross-mode-agreement a legal Qwen-only signal, or does it smuggle in a quality prior? Didn't deploy it (H1-H4 cover the defensible space); flagging as the one borderline.
