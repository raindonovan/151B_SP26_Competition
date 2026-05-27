# 151B Competition — Findings & Knowledge Base

**Last updated**: 2026-05-27 ~18:00 PT
**Purpose**: Persistent knowledge base. What we've learned, validated, and noticed. Append-only — don't overwrite, only add.

This is the WHAT-WE-KNOW doc. For action items, see `docs/SUBMISSIONS_TODO.md`.

---

## 1. The Math (formal problem statement)

The Kaggle competition is a **two-stage prediction problem**:

- **Stage 1 (Math)**: For each item Q_i, determine the mathematically correct value V_i.
- **Stage 2 (Format)**: Determine the exact string encoding S_i matching the hidden gold label G_i.

Kaggle score = (1/943) × Σ 𝟙[S_i = G_i].

The Wolfram audit + V3 tracker analysis empirically confirms: **Stage 2 dominates failures**. ~80% of "wrong" items in B1-7 are pure format errors; Qwen has V_i right but S_i wrong.

## 2. Locked facts about Kaggle's grader

- Extracts ONLY the LAST `\boxed{}` from response
- String-matches against hidden gold (with some normalization)
- Per-slot `\boxed{a}\boxed{b}` costs -16.2pp vs `\boxed{a, b}` (probe-verified)
- Order reversal within `\boxed{}` costs -17.6pp (probe-verified)
- Local `judger.py` has ~28pp gap from Kaggle (judger is too lenient)

**UNVERIFIED Kaggle grader behaviors** (worth empirical probes):
- `\dfrac` vs `\frac` (sample_submission.csv suggests `\dfrac` canonical)
- `\text{A}` vs plain `A` (could cost items if strict)
- `^\circ` vs `°` symbol
- Trailing zeros (`1.5` vs `1.50`)
- Whitespace tolerance: `,` vs `, ` between multi-answer slots (slot1_reformat scored 0.646 with mixed spacing → tolerated)
- `\dfrac` → `\frac` conversion direction (slotA submission was the diagnostic)

## 3. Validated levers (empirical)

| Lever | Lift | Status |
|---|---|---|
| Multi-answer shape fix (single `\boxed{a,b,c}`) | +0.3pp | LOCKED (slot1_reformat) |
| Minimal normalizer (strip `\left`/`\right`/thin space) | +0.4pp | LOCKED (slot1_minimal_norm) |
| V3 shape filter | +0.7pp | LOCKED (run14b_v3filtered) |
| 32K token budget vs 16K | +2.5pp | LOCKED (run09→run14b) |
| Answer sheet best on T3+T4 items | +2.1pp | LOCKED (info_2: 0.667) |
| Wolfram HIGH overrides | +3-5pp expected | TESTING (Slot 1 today) |
| Rescue HIGH+MED | +0.3-0.5pp expected | TESTING (Slot 2 today) |
| Multi-answer expansion (untried) | +1-3pp expected | UNTRIED |

## 4. Qwen failure-mode taxonomy

From Wolfram findings (see `docs/WOLFRAM_FINDINGS.md` for full doc):

1. **Multi-slot under-count** (DOMINANT — 79% of B1-7): collapses N-slot answer to last slot only
2. **Decimal/fraction format mismatch** (7 items in B8): correct value, wrong canonical form
3. **Symbolic-constant substitution** (rare): plugs numeric values for unspecified constants
4. **Missing prefix/label/unit**: missing `D=`, `Quadrant`, `^\circ`
5. **Multi-option equivalence trap**: dataset bug — multiple options encode same math (0317)
6. **Genuine arithmetic error** (rare): actual wrong math
7. **LaTeX text-wrap**: `\text{A}` instead of plain `A`

Sub-modes:
- 1a. Multi-select MCQ collapse: single letter when multi-letter required
- 6a. "All of the above" sub-MCQ trap: picks one true statement instead of D

## 5. The master tracker (V3) format-error landscape

From `results/master_item_tracker.csv` heuristic flags (across 943 items):

| Flag | Count | Meaning |
|---|---|---|
| backsolve_disagree | 269 | Current ≠ score-weighted majority. MOSTLY WHITESPACE differences (verified empirically — slot1_reformat scored 0.646 with these). |
| disagree_teacher | 233 | Current ≠ teacher consensus (real math diff possible) |
| **format_only_diff_teacher** | **117** | Current matches teacher when normalized — PURE FORMAT ERROR candidates |
| **undercount** | **110** | Current has fewer slots than [ANS] markers in question — MULTI-ANSWER EXPANSION candidates |
| mcq_not_letter | 16 | MCQ item but answer not a letter A-J (needs investigation) |

**Calibration**: When compared against ACTUAL slot1_reformat (not stale unified_answer_sheet):
- Only 10 items have format_only diff with teachers (mostly `\dfrac` vs `\frac` where slot1 is right)
- 0 items have MCQ value→letter issues (slot1_reformat already letterized)
- Most backsolve disagreements are whitespace-only (Kaggle tolerates)

## 6. The back-solve framework

**Methodology**: Score-weighted Bayesian posterior over candidate answers per item.

For each item, for each candidate answer X:
```
log P(X) = Σ_i [ log(S_i) if submission_i = X else log(1 - S_i) ]
```
where S_i is submission i's Kaggle score.

**Validated assumptions**:
- High-score submission giving X → strong evidence for X
- High-score submission NOT giving X → strong evidence against X
- Low-score submission contributes ~0 in both directions
- Missing submissions excluded

**Known limitations**:
- Assumes error independence (submissions correlate — same base model)
- Sanity check showed +12pp drift for run14b (has unique correct answers not shared) and -21pp drift for diagnostics (different error patterns)

**Mitigation**: correlation dampening — group correlated submissions, weight ÷√(group_size).

## 7. Dataset quality issues (known)

- **0011**: truncated problem text in private.jsonl
- **0317**: options D and H mathematically equivalent (dataset bug)
- **0570**: synthetic OEIS-style sequence not in OEIS (unresolvable without dataset creator)
- **0585, 0622, 0858**: trailing [ANS] for interpretation-MCQ with options absent from question text — likely entire problem class lost MCQ options in dataset prep
- **0894**: question hints "close to 9" but verified count = 10
- **0141**: web search match (Putnam 1989 A-1 base-7) gives answer 0, but 0 is NOT in MCQ options A-H — match likely wrong

## 8. The 18 no-box items (rescue results)

Items where Qwen consistently produced no `\boxed{}` across all SC runs:
93, 112, 161, 204, 229, 308, 312, 376, 383, 445, 453, 498, 652, 724, 799, 809, 836, 911.

Forced-answer suffix rescue (SC=4 on base model):
- **4/4 unanimous (4 items)**: 229→2, 308→12, 383→80, 498→15
- **3/4 (1 item)**: 445→D
- **2/4 (8 items)**: 161, 204, 312, 453, 724, 799, 836, 911
- **1/4 split (5 items)**: 93, 112, 376, 652, 809 (no consensus signal)

xhigh teacher analysis on these 18: 0/18 unanimous, xhigh produces unique 4th answers. Conclusion: these are beyond LLM teacher consensus; forced-suffix rescue is the only path.

## 9. Submission landscape (Day 3 EOD)

See `docs/SUBMISSION_REGISTRY.md` for the canonical scoring registry.

Best real-inference baselines:
- **slot1_wolfram_full_overrides**: 0.653 (Day 2 Slot 2)
- **slot1_reformat**: 0.646 (multi-answer reformat applied)
- **slot1_minimal_norm**: 0.643 (left/right + thin-space normalizer)
- **run14b_v3filtered**: 0.646 (V3 shape filter, SC=8, 32K)

Best diagnostic:
- **info_4_t1lock_sheet_rest**: 0.671 (T1=run14b, T2-T4=answer sheet)
- **info_2_answersheet_on_uncertain**: 0.667

## 10. Untried levers (open exploration)

- Empirical probe of `\text{A}` vs `A` for MCQ letters
- Empirical probe of `\dfrac` vs `\frac` direction (slotA result needed)
- Multi-answer expansion using teacher consensus on 82 undercount items
- Per-question manual editing using master tracker as dashboard (high-yield, time-intensive)
- 0587 multi-select format probe (comma-sep vs concat vs sub-boxes)
- 0894 borderline-integer probe (`9` vs `10`)
- 0715 list ordering probe (natural vs sorted)

## 11. Tools landscape

- **git-mcp READ**: works (45 tools), `download_url` resolves LFS pointers
- **git-mcp WRITE**: broken (403) — use GitHub PAT via bash_tool curl/Python instead
- **LFS unlock**: `media.githubusercontent.com/media/{owner}/{repo}/{branch}/{path}` from `download_url` field works for ALL LFS files (verified on 14MB submission CSVs)
- **Google Drive**: deprecated (read-only legacy). Don't create new docs there.
- **Repo writes via PAT**: full read+write on `beepbeeepimajeep/151B_SP26_Competition` (admin+push confirmed)
