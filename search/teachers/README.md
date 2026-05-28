# Teachers (SEARCH lever) — STUB / LINK, not duplicated

Multi-LLM teacher consensus answers (Claude, GPT, DeepSeek, etc.).

**DECISION (repo hygiene)**: teacher data is NOT duplicated here. It lives canonically in:
- `results/master_item_tracker.csv` (teacher_consensus column)
- `results/unified_answer_sheet.csv` and `results/answer_sheet/`
- `results/undercount_candidates.csv` (teacher consensus for multi-slot items)

Reason: single source of truth. Duplicating teacher answers into search/teachers/ would create drift. This stub points to the canonical locations. If a teacher-specific analysis doc is written, it goes HERE; the raw answers stay in results/.
