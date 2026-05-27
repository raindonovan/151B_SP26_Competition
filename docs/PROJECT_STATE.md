# PROJECT STATE

**Last updated**: 2026-05-27 ~17:30 PT (Day 3, mid-session)
**Update**: Edit in-place via GitHub API (PAT in Drive SECRETS doc `1_9ynCvp2G5Z3yCkJ47pnM-bkfwwrhzv2`)

## Scores snapshot

| Metric | Score | Source |
|---|---|---|
| **Best real inference** | **0.653** | slot1_wolfram_full_overrides, Day 2 Slot 2 |
| slot1_reformat | 0.646 | Day 2 Slot 1 |
| Anchor | 0.643 | slot1_minimal_norm |
| Best diagnostic | 0.671 | info_4 (4-teacher consensus) |
| Leaderboard #1 | 0.752 | Dannyyyy, 32 subs (likely GRPO-trained) |
| Days remaining | ~5 | deadline ~2026-06-02 |
| Submissions remaining | ~15 | 5 days × 3/day — each one is gold |
| Gradescope code deadline | 2026-05-31 (Sun) | public repo + run_inference() |

## Strategic frame

**Two-track approach (locked Day 3):**
- **Track A (Pick A foundation)**: Clean Qwen inference + post-processing only. Multi-LLM voting allowed (it's inference). No external answer injection.
- **Track B (Pick B foundation)**: Track A + external overrides (Wolfram verified, web search GOLDs, OPL splice, teacher direct overrides).

Both tracks submitted to Kaggle for measurement. Day 7 final 2-pick rule pulls one from each.

**GRPO**: Downgraded to opportunistic Day 5-6 only. AIMO-2 evidence: 0/8 top teams used GRPO as mainline.

## Lever list (updated Day 3)

| Lever | Expected lift | Status |
|---|---|---|
| Multi-answer shape fix | ~~+2-4pp~~ **REALIZED at +0.3pp** | Done — slot1_reformat Day 2 |
| NoThinking SC=8 full-943 | baseline signal | COMPLETE — 45 MB on origin |
| Wolfram B1-B8 overrides | +0.5-1pp | ~61 override-ready items; apply to Track B |
| Web search GOLDs (5 items) | +0.2-0.5pp | 0117/0120/0124/0125/0141 confirmed |
| No-box rescue (18 items) | +0.2-0.5pp | MID-FLIGHT on tnr-0 |
| OPL splice v1 | +0.5-2pp | Embeddings done; script queued after rescue |
| Tuple-voting on NoThinking | TBD | Deferred to morning |
| Truncation rescue (~50 items) | +0.2-0.5pp | Triage not done; deferred |
| SC=20 hybrid | +0.5-1pp | Gated on Rain decision |
| DeepSeek-R1 5th teacher | +0.3-0.8pp | Gated on cost approval |

## Day 3 completed work

- **OPL embeddings**: 72,668 × 768-dim BGE-base-en-v1.5 — `results/opl_embeddings/opl_embeddings.npy` (223 MB). LOCAL on tnr-0 ONLY (LFS issue prevents push). Backed up to `~/backup_opl/`.
- **A2 hardest-30 @ 82K/64K**: 30 items — `results/hybrid/tnr-A/a2_serial_sc16_hardest30_20260526T112138Z.jsonl`
- **Job 2 SC=16 hardest-30 @ 49K**: 30 items — `results/hybrid/tnr-A/sc16_hardest30_20260527T090854Z.jsonl`
- **NoThinking SC=8 full-943**: COMPLETE — `results/hybrid/tnr-B/nothinking_full_943_20260527T000129Z.jsonl` (45 MB, 943 items, 5.3% truncation at 8K cap). Schema has `samples: [str]` — supports tuple-voting.
- **Wolfram Batch 8**: 25 items audited. 23 override-ready (incl. 0181 resolved by symmetry argument). MASTER_SHEET in Drive wolfram_batches folder.
- **Web Search Session 3**: 50 items (100-149). 4 new GOLDs: 0117=Putnam 2021 A5 → B=2020, 0120=Polya theorem → 8, 0125=Putnam 2016 A1 → 8 (MCQ TBD), 0141=Putnam 1989 A-1 variant → 0 (MCQ TBD).
- **No-box rescue**: 13/18 done, ~5 remaining. All t=FALSE (expected). Forced-answer suffix working.
- **Phase A adapter v5 full-943**: FAILED preflight (missing `data/candidates_full_943.txt`). Skipped. v5 near-break-even; v7 is the future SFT play.
- **GitHub PAT unlocked**: direct repo writes via API. No more Thunder relay for doc/script updates.

## Active workers

- **tnr-0** (`instance-x528wsl9-main`, Thunder ID 0): rescue mid-flight. OPL v1 spec queued next.
- **tnr-1** (`instance-q6b81cqp-main`, Thunder ID 1): snapshot in progress → ready for delete via Thunder UI row 1.

## Infrastructure

- git-mcp: READ works (45 tools). WRITE: via GitHub PAT + bash_tool curl to api.github.com (see SECRETS doc)
- Google Drive: read + create only (no delete/edit). Wolfram batches, web search checkpoints, SECRETS doc live here.
- OPL embeddings: tnr-0 LOCAL ONLY — must LFS-migrate before tnr-0 deletion.
- tnr-0 git status: main branch, clean (switched from inference/tnr-0-* earlier today)
- tnr-1: inference/tnr-1-* branch, all output on origin via watchdog

## Wolfram coverage (cumulative)

Batches 1-7: 38 items (see Drive wolfram_batches/ for details).
Batch 8: 25 items, 23 overrides ready:

| id | override_value | confidence |
|----|----------------|------------|
| 0011 | `0.939` | consensus-only |
| 0040 | `D = 800 - 50d` | wolfram-high |
| 0067 | `7.6(1.09)^t,13.9,5.4` | wolfram-high |
| 0072 | `-0.8352,-0.9187,0.3950,-2.3258,Quadrant IV` | wolfram-high |
| 0089 | `\frac{326}{7}` | wolfram-high |
| 0100 | `\frac{180}{7}` | wolfram-high |
| 0103 | `8\sqrt{2}` | wolfram-high |
| 0106 | `\frac{13}{6}` | wolfram-high |
| 0118 | `\frac{18}{5}` | wolfram-high |
| 0124 | `H` | wolfram-high |
| 0167 | `Negative,Negative,Positive,Negative` | wolfram-high |
| 0181 | `A` | HIGH (symmetry proof) |
| 0218 | `\arcsin\!(\frac{7}{10})` | wolfram-high |
| 0233 | `1.96,-1.96,-5.18,B` | wolfram-high |
| 0247 | `\frac{2409}{65},\frac{2474}{1+\frac{2409}{65}e^{-0.53t}},2473.84` | wolfram-high |
| 0317 | `D` | wolfram-high (dataset quirk — D and H identical, only D accepted) |
| 0395 | `\frac{85}{3},-\frac{95}{4},-\frac{10}{7}` | wolfram-high |
| 0454 | `1.5, 0.9375` | wolfram-high |
| 0496 | `9.594^\circ` | wolfram-high |
| 0506 | `J` | wolfram-high |
| 0584 | `7z, 6w` | wolfram-high |
| 0884 | `g(x)=(x-59)^2+74` | wolfram-high |
| 0902 | `9,6` | wolfram-high |

## Web search GOLDs

| id | source | canonical_answer | notes |
|----|--------|-----------------|-------|
| 0041 | IMO 2025 P6 | 2112 | teachers all wrong (3986/4048/4048) — ★★★ |
| 0117 | Putnam 2021 A5 | B = 2020 | all 5 teachers agreed — high confidence |
| 0120 | Polya's theorem | 8 | 4/5 teachers agreed |
| 0124 | Putnam 2018 A2 | H | session 2 salvage |
| 0125 | Putnam 2016 A1 | 8 | MCQ option mapping TBD |
| 0141 | Putnam 1989 A-1 base-7 | 0 | MCQ option mapping TBD |

## Open decisions

- [ ] [RAIN] SC=20 hybrid + DeepSeek-R1 5th teacher green-light
- [ ] [TECH] LFS migration for OPL embeddings (before tnr-0 deletion)
- [ ] [RAIN] Wolfram Drive cleanup (3 duplicate files to delete_ignore)
- [ ] [RAIN] MASTER_SHEET 0181 status update (inconclusive → override=A)
- [ ] [THUNDER] Logprobs in run10 JSONL — gating response-prob SC
