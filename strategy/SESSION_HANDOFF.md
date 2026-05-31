# SESSION_HANDOFF.md — claude_strategy session state

> Read this FIRST when resuming a claude_strategy chat. Detailed findings live in their canonical homes; this is the index.

**Last updated**: 2026-05-30 (Day 8 close — 5 submissions scored, NEW BEST 0.745, overlay stack near ceiling, Pick B path is Qwen-only). Built by claude_vscode from session state; HEAD reference set below.

**HEAD at handoff**: `1814bc3` (Log Day 8 results) → this commit amends/follows it. Update if re-pushed.

## ⏰ DEADLINE: 2026-05-31 (tomorrow). Submission budget ~12 slots left.

The single most important manual action: **deselect the old 0.438 / 0.420 Kaggle picks and lock the 0.745 sheet as Pick A** so we are never exposed to a stale pick at the deadline. This is a Rain-only UI step.

## ⚡ ACTIVE STATE (Day 8 close): overlay stack near ceiling, pivot to Qwen-only

Day 8 ran the 30_05 slot sweep (control → anchor → 4/4 bloc → full-v7 ship-A → format probe). Results below establish the **external-evidence overlay ceiling at ≈ +3.2pp over 0.713**, with diminishing returns. The strategic consequence: **all remaining upside (and Pick B specifically, per rule #11) must come from the Qwen-only inference path** — not from more teacher/anchor/Opus overlays.

### Day 8 Kaggle results (5 submissions — REGISTRY #37-#41)
| Slot | CSV | Score | Δ base | Verdict |
|---|---|---|---|---|
| 1 control | 30_05_slot1_control.csv | 0.713 | 0.000 | ✅ control valid, no regression Day5→8 |
| 2 +anchor | 30_05_slot2_anchor.csv | 0.738 | +0.025 | ✅ positive (far below +8-15pp predicted — grader format-strict) |
| 3 +4/4 bloc | 30_05_slot3_bloc.csv | 0.738 | +0.025 | ❌ NULL — zero leverage on top of anchor |
| 4 v2 ship-A | 30_05_slot4_aggressive_v2.csv | **0.745** | +0.032 | ✅ **NEW BEST (Day 8)** — full v7 ship-A (Opus flips + 5th teacher) |
| 5 format probe | 30_05_slot5_format_probe.csv | 0.745 | +0.032 | ❌ NULL — render_d Opus-form indeterminate |

Detail: `submission/30_05/SCORES.md` + `submission/30_05/SLOTS_1_4_REPORT.md`.

### 3 key learnings (Day 8)
1. **4/4 teacher bloc = NULL leverage on top of anchor** (0.738→0.738). Those items were already correct in the anchor base or sit off the ~283 scored slice.
2. **Opus = +0.7pp, the only lever beyond anchor.** The 4 anchor flips + 57-item 5th-teacher overlay are what make slot 4 v2 the best (0.745). Small (~2 slice items) but real.
3. **Format probe = NULL.** render_d (Opus form) vs render_b (anchor form) gave no net change. Content/format conflation makes the A/B indeterminate — can't isolate "format accepted" from "value already counted."

Net: anchor (+2.5) → Opus (+0.7) → 4/4 flat → format probe flat. **Overlay ceiling ≈ +3.2pp; diminishing returns evident.**

## TL;DR — Where we are

- **Best score: 0.745** (`submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v2.csv` = full v7 ship_class=A; REGISTRY #40). +3.2pp over the 0.713 base. Gap to leader (~0.85) ≈ 10.5pp.
- **Pick A = 0.745** (slot 4 v2) — the safety floor / best-so-far. **Pick B path is Qwen-derived ONLY (rule #11)** — no teacher/anchor/Opus overlays eligible.
- **v7 answer sheet is LOCKED.** `data/answer_sheet_v7_FINAL.csv` (943×11): math_answer (truth) vs submission_answer (Kaggle string), with format_status / format_strategy / ship_class. Distribution: tier T1 308 / T2 410 / T3 39 / T4 182 / T5 4; format_status submission_proven 773 / format_suspect 71 / untested 98 / known_bad 1; ship A 869 / B 69 / C 5. Schema + lineage: `data/ANSWER_SHEET_v7_README.md`.
- **Opus 4.7 production outputs landed** in `data/search/teachers/opus/` (535 items: answers.csv, results.csv, items.jsonl, anchor_v2_candidates.csv [316], opus_5th_teacher.csv [219], README). These fed the v7 flips + 5th-teacher overlay.
- **Kaggle grader is value-equality** (numeric ~1e-8 rel-tolerance via sympy/LaTeX): `4.000==4`, `0.6==3/5` PASS. Canonical engine = `grading/grader.py`. Strict-Hendrycks is DEPRECATED. The local grader is DIRECTIONAL ONLY (use ordering, not magnitudes — it cannot resolve sub-2pp Kaggle deltas).
- **Known bug (post-deadline fix queued):** `gold_equiv` factorial overflow — `gold_equiv("4050","2025!")` returns True (factorial → inf → rel-tolerance passes), which wrongly marked row 0488 submission_proven. Patched manually in v7/slot4_v2/format probe (appended `\boxed{4050}`). Root cause logged; do NOT trust `gold_equiv` on factorial/overflow surfaces.

## Tomorrow's north star (Day 9)

**The Qwen-only path is the only remaining upside.** Three mechanisms, in priority order:
1. **Inference-audit cross-run consensus** — for each item, scan all Qwen runs (SC8/SC16/SC32/nothinking) and promote cross-run-agreeing answers. This is the Bucket A / Bucket B classification from `strategy/HOW_WE_KNOW_CORRECTNESS.md`.
2. **Phase-0 log-weighted self-consistency** — re-aggregate existing SC samples with log-weighting rather than plain majority vote.
3. **The 12hr A100 run** — if available, a longer/higher-SC Qwen run on the contested items.

All three are Qwen-derived and therefore Pick-B-eligible under rule #11. The teacher/anchor/Opus overlay path is exhausted (ceiling +3.2pp) and is NOT eligible for Pick B.

## Pending tasks (in priority order)

1. **Lock Kaggle picks** — deselect 0.438 / 0.420; set Pick A = 0.745 (slot 4 v2). Rain-only UI step. **Do this first — it's the deadline safety floor.**
2. **Build the Qwen-only Pick B candidate** — cross-run consensus + log-weighted SC over existing runs. This is the only path with Pick-B upside (rule #11). If it clears 0.745, it's Pick A and 0.745 becomes Pick B; if it clears 0.713 but not 0.745, it's a diverse Pick B.
3. **Run the T1 inference scan** (Bucket A/B per `HOW_WE_KNOW_CORRECTNESS.md`) over the v7 T4/T5 items (182+4 = 186) — the items where v7 still falls back to base/qwen, i.e., where Qwen consensus could promote truth.
4. **Post-deadline:** fix the `gold_equiv` factorial-overflow bug in `scripts/gold_equiv.py` (guard against non-finite parse results before rel-tolerance compare).
5. **PAT rotation** — Rain to revoke the burned classic token end of competition (Sun 5/31). See `SECURITY.md` 2026-05-29 (c).

## Submission budget

~12 slots remaining before 5/31 deadline. Day 8 spent 5 (the overlay sweep). Revised allocation:
- ~6-8 for the **Qwen-only path** (cross-run consensus variants, log-weighted SC, A100 run) — this is where upside lives now.
- ~2 for score-locks (ensure Pick A = highest scored CSV at deadline).
- ~2 reserve (emergency, re-probe).

The format-probe slot allocation from the Day-7 plan is **retired** — Day 8's format probe was NULL and the overlay path is exhausted.

## Locked findings (canonical homes — do not duplicate, just reference)

| Finding | Home |
|---|---|
| Day 8 results + overlay ceiling +3.2pp + 3 learnings | `submission/30_05/SCORES.md`, `submission/REGISTRY.md` (#37-#41) |
| v7 answer sheet schema, lineage, distribution | `data/ANSWER_SHEET_v7_README.md` |
| Opus 4.7 production outputs (535 items) | `data/search/teachers/opus/README` |
| Kaggle grader = value-equality (1e-8 rel-tol); grader.py canonical | `postprocessing/FINDINGS.md` |
| Tier-1 items graded wrong on format (F7) | `postprocessing/FINDINGS.md` |
| Normalization audit: 0.713 came from submission-build pipeline, not normalizer.py | `postprocessing/AUDIT_REPORT.md`, `postprocessing/HISTORICAL_STACK.md` |
| Kaggle scores on ~283 LB slice, not 943; final ranking is 943 | `submission/RED_ALERT_LB_SUBSET.md` |
| Math-vs-format mental model, two-bucket SFT framework | `strategy/HOW_WE_KNOW_CORRECTNESS.md` |
| OPL bulk-override empirically disconfirmed (Day 7) | `data/search/opl/findings.md` |

## Locked SOPs

| SOP | What it says | Where |
|---|---|---|
| **GIT BOOTSTRAP** | One-command setup for any fresh Claude sandbox: `curl -sSL .../setup_git.sh \| bash -s -- "$PAT"`. Run FIRST in every session. | `scripts/setup_git.sh` + root `CLAUDE.md` |
| CREDENTIALS RULE (rev. 2026-05-29) | Never embed PAT in spawn prompts or committed files. Rain MAY provide PAT in chat for that Claude's runtime. Fine-grained ≤7-day. | `CLAUDE.md` + `SECURITY.md` |
| GOLD-RULE | File findings in canonical home same session. Folder map in CLAUDE.md. | `CLAUDE.md` |
| Agent lifecycle | Role&Relevance in spawn prompt; mandatory SCRATCH.md signoff before ending. | `CLAUDE.md` |
| Terminology | "test set" = ~283 slice; "FINAL test set" = 943. | `CLAUDE.md` |
| Local grader DIRECTIONAL ONLY | Local judger/grader ~28pp more lenient than Kaggle; use ordering not magnitudes; never for accuracy decisions. | `submission/30_05/SLOTS_1_4_REPORT.md` |
| Pick B rule #11 | Pick B must be Qwen-derived ONLY (no teacher/anchor/Opus overlays). | this doc + `submission/30_05/SCORES.md` |

## Tool-set notes for next claude_strategy

Opus 4.7 chat UI has a **"Code" chip** at the bottom of the message input. When enabled, claude_strategy gets `bash_tool / create_file / view / str_replace` and can clone-edit-push directly. When disabled, falls back to GitHub MCP (read-only; writes 403) + VSCODE COMMIT BLOCK relay.

**Verify on first message**: run an `ls` or innocuous bash command. If bash_tool isn't available, tell Rain to check the Code chip.

**claude_vscode** is the persistent execution runtime (this session's author). It holds a separate clone at `/home/raindonovan/151B_SP26_Competition` — commits there must be pushed to be visible on other clones (Day-8 lesson: a real commit looked "missing" on Rain's PC only because it was unpushed).

## Recent session signoff

### Day 8 (2026-05-30, claude_vscode — execution runtime)

**Math work (the actual competition stuff):**
- Built and scored the **30_05 slot sweep** (5 submissions): control 0.713, anchor 0.738, 4/4 bloc 0.738, full-v7 ship-A **0.745 (NEW BEST)**, format probe 0.745. Logged in `submission/REGISTRY.md` #37-#41, `submission/30_05/SCORES.md`, `SLOTS_1_4_REPORT.md`.
- Established the **overlay ceiling ≈ +3.2pp over 0.713** with diminishing returns: anchor +2.5, Opus +0.7, then 4/4 and format probe both NULL. Strategic consequence: pivot to Qwen-only for all remaining upside and for Pick B (rule #11).
- Built **`data/answer_sheet_v7_FINAL.csv`** (943×11) — the math/submission split master with format_status / ship_class, plus `answer_sheet_v7_probe_overlay.csv` (69 rows) and `ANSWER_SHEET_v7_README.md`. Applied YELLOW audit fixes (0383/0570 content-uncertain ship-A; 0405/0586 secondary-confirmed untested ship-A), added the 0836 anchor flip (CHATGPT secondary review), and patched row 0488 (`\boxed{4050}` math truth) after catching the gold_equiv factorial-overflow bug.
- Landed **Opus 4.7 production outputs** (535 items) into `data/search/teachers/opus/` from the DataApp build — anchor_v2_candidates (316), opus_5th_teacher (219), full items.jsonl.
- Built `scripts/score_inference_vs_sheet.py` (reusable value-equality scorer) and `scripts/build_slots_1_4.py` / `scripts/build_answer_sheet_v7.py`.

**Audit / infrastructure work:**
- Completed the **normalization-stack audit** (`postprocessing/AUDIT_REPORT.md` + `HISTORICAL_STACK.md`): the 0.713 stack comes from the **answer-sheet/submission-build pipeline, NOT `normalizer.py`**. Documented a `normalizer.py` defect (multi_answer_normalize over-collects boxes). Established that the 4 root `judger.py` edits (commit c07e149) are **inert** (tested: zero verdict changes); `grading/grader.py` is canonical.
- Surfaced and self-corrected a missing-on-PC commit (separate-clone / unpushed root cause) and an incomplete Opus commit (`git add` skipped gitignored data/search → fixed with `git add -f` in `153e5a7`).

**Known issues logged:**
- `gold_equiv` factorial-overflow bug (post-deadline fix queued, Pending #4).
- Day 8's overlay ceiling means Pick B has NO upside path unless the Qwen-only work clears 0.745.

### What's left for next claude_strategy
- See Pending tasks above. **#1 (lock Kaggle picks)** is the deadline safety floor — do it first. **#2 (Qwen-only Pick B)** is the only remaining upside path.
- The teacher/anchor/Opus overlay path is **exhausted** (+3.2pp ceiling). Do not spend slots re-probing it.
- Read `submission/30_05/SCORES.md` before planning Day 9 slots.

### Day 7 (2026-05-29, claude_strategy)
- Confirmed best score 0.713 (29_05 undercount_plus_frac.csv). Resolved the "phantom normalization stack" fork (it was real and pushed at `origin/copilot/normalizer-inference-review-20260529`, commit c07e149; merged to main at 620301c). OPL bulk-override empirically disconfirmed (0/39 T1-promoted). Built `undercount_frac_mcq.csv`. Revised CREDENTIALS RULE; shipped `scripts/setup_git.sh`. wolf agent landed B9-B16 (~144 Wolfram verifications). Full detail: git history + `data/search/opl/findings.md`.

### Day 6 (2026-05-28, claude_strategy)
- Documented F7 (tier-1 graded wrong on format). Wrote HOW_WE_KNOW_CORRECTNESS.md. Locked NORMALIZATION_RULES.md. MCQ append-bug identified (AMBER #3). Designed wolfram/ workflow.
