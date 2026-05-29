# Wolfram SCRATCH.md — Low-friction capture

Dump anything interesting here. Rain sorts later.

---
## Phase 1 bootstrap — 2026-05-29

Built MASTER_QUESTIONS.csv from 943-item master_item_tracker.csv + 66 legacy wolfram_overrides.csv.
Subject classifier uses full question text from private.jsonl (not truncated previews).
Subject distribution: statistics=163, algebra=124, trig=71, geometry=62, number_theory=62, calculus=46, linear_algebra=27, other=388.
"other" is 41% — many are word problems without explicit domain keywords. Classified as MAYBE-computable.

Priority queue: 118 P1 (disagreement+computable), 59 P2 (teacher split), 108 P3 (multi-slot), 219 P4 (single-slot), 372 P5 (other).

Note: DISPUTED item is 0141 (Putnam 1989 A-1 base-7 variant — math gives 0, but 0 not in MCQ options A-H). Do not apply this value (disputed).

Batch09 targets are all P1 (Qwen disagrees with teacher + computable subject). Starting with items 0000, 0002, 0004...

---

---
## Agent signoff — claude_wolf (claude_vscode) — 2026-05-29

### Which batches ran this session
B9, B10, B11, B12 (100 items total, 25 each)

### Total items verified this session
75 DONE (HIGH/MED) + 25 INCONCLUSIVE = 100 items
Cumulative: 140 DONE + 25 INCONCLUSIVE across all batches

### Confidence breakdown (this session)
- B9:  21 HIGH + 1 MED + 3 INCONCLUSIVE
- B10: 22 HIGH + 3 INCONCLUSIVE
- B11: 17 HIGH + 1 MED + 7 INCONCLUSIVE
- B12: 12 HIGH + 1 MED + 12 INCONCLUSIVE
Pattern: INCONCLUSIVE rate rising as P1 queue exhausted competition-heavy items.

### Key cumulative observations

Multi-slot undercount continues across ALL subjects (not just stats). Every batch had 8-10 discrepancies. OEIS algorithm MCQs are systematically INCONCLUSIVE — Wolfram can't compute a(n) for arbitrary OEIS sequences. Competition problems in P1 bucket where both Qwen and teacher guessed wrongly cannot be verified. New failure mode found: 0557 |5|=6 (trivial arithmetic error, off-by-1).

Wolfram query patterns that work:
- `statistics {data}` for mean/std
- `Mod[LinearRecurrence[{P,-Q},{a0,a1},N][[-1]], p]` for modular recurrences
- `InverseCDF[StudentTDistribution[df], p]` for t-critical values
- `2*Pi * Integrate[...]` for volumes of rotation

### Items needing follow-up
0016 (game theory, teacher=501), 0488 (Linetown, teacher=4050 suspect), 0058/0501/0682 (functional eq competition). All OEIS-pattern MCQs: 0255, 0647, 0675, 0772.

### What's left for next run
18 remaining P1 items (see TODO.md batch13), then P2 (59 teacher-split), P3 (108 multi-answer). ~777 UNVERIFIED. P2 should have better Wolfram hit rate than P1 since P2 items are mostly stats/math where teachers disagreed, not competition problems.

---
## Agent signoff — claude_wolf (claude_vscode) — 2026-05-29 (session 2 extended)

### Batches this session
B9, B10, B11, B12, B13, B14, B15, B16, B17 — 225 items total (9 batches)

### Totals
- DONE: 259 | INCONCLUSIVE: 31 | DISPUTED: 1 | UNVERIFIED: 652
- This session DONE: ~194 (from 75 of P1 + P2 + P3 buckets)

### Key strategic discovery (LOCKED in TODO.md + FINDINGS 17-22)
**format_flags are a reliable discrepancy filter:**
- FLAGGED items (undercount/disagree) → ~30% discrepancies
- UNFLAGGED items → ~0% discrepancies (verification-only)
- P1 (Qwen-vs-teacher disagree): high discrepancy but ~33% INCONCLUSIVE (competition/OEIS)
- P2 (teacher-split): 0 discrepancies (best already matches consensus)
- P3 flagged (B15-16): 17 discrepancies in 50 items
- P3 unflagged (B17): 0 discrepancies in 25 items

### New failure modes found this session
- F14: digit-concatenation (0313 -2√14/15→"-21414", 0411, 0936) — SYSTEMATIC, PP-recoverable
- F15: T/F binary-vs-word (0785,0896,0927: 0/1 vs False/True)
- F16/F21: best="INVALID"/"answer"/word = inference failure, direct correction
- F19: undercount = "drop earlier sub-parts" (answer only final part of a/b/c)
- F22: OPEN — population vs sample variance convention (0542), needs Kaggle probe

### Recurrence template found
a_n=4a(n-1)-a(n-2) appears in 0017, 0606, 0211 — all least-odd-prime=181.

### What's left / next session
- batch18 QUEUED: 22 flagged single-slot items (discrepancy candidates) + 3 unflagged
- Then unflagged P3/P4 (verification), P5 (mostly INCONCLUSIVE competition/OEIS)
- ACTION: resolve variance convention (F22) before mass variance corrections
- 652 items still UNVERIFIED but the high-value discrepancy veins (all flagged P1+P3-multi) are largely mined

### Recommendation
The discrepancy work is mostly done. Remaining batches are verification-anchoring
(unflagged) or low-yield (P5 competition). Next session: clear batch18 (last flagged vein),
then decide whether full coverage is worth it vs. focusing on the F22 variance probe.
