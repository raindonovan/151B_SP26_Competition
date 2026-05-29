# Wolfram SCRATCH.md — Low-friction capture

Dump anything interesting here. Rain sorts later.

---
## Phase 1 bootstrap — 2026-05-29

Built MASTER_QUESTIONS.csv from 943-item master_item_tracker.csv + 66 legacy wolfram_overrides.csv.
Subject classifier uses full question text from private.jsonl (not truncated previews).
Subject distribution: statistics=163, algebra=124, trig=71, geometry=62, number_theory=62, calculus=46, linear_algebra=27, other=388.
"other" is 41% — many are word problems without explicit domain keywords. Classified as MAYBE-computable.

Priority queue: 118 P1 (disagreement+computable), 59 P2 (teacher split), 108 P3 (multi-slot), 219 P4 (single-slot), 372 P5 (other).

Note: DISPUTED item is 0141 (Putnam 1989 A-1 base-7 variant — math gives 0, but 0 not in MCQ options A-H). Do not apply this override.

Batch09 targets are all P1 (Qwen disagrees with teacher + computable subject). Starting with items 0000, 0002, 0004...

---
