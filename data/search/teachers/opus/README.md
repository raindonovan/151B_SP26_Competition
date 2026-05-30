# Opus 4.7 — production teacher run (5th teacher + anchor v2)

**Source:** Opus 4.7 production run via DataApp (`~/cse151b/DataApp/dataapp_outputs/opus/`, DataApp commit `f437b9e`).
**Landed into 151B:** 2026-05-30 by claude_vscode.
**Config:** `claude-opus-4-7`, temperature 0.6, thinking OFF, max_tokens 32768, streaming.
**Targets:** 535 items = **316 anchor** (re-verify the audited gold) + **219 uncovered** (items lacking strong teacher coverage). NOT all 943.

## Verification
- **Diamond items confirmed from data:** `0041 → 2112` ✅, `0285 → 735` ✅ (present in `answers.csv`/`results.csv`).
- **Anchor v2 corroboration (316 items):** corroborate **209** · contradict **78** · inconclusive **29** (`opus_verdict` in `anchor_v2_candidates.csv`).
- Row counts: `answers.csv`/`results.csv`/`items.jsonl` = 535; `anchor_v2_candidates.csv` = 316; `opus_5th_teacher.csv` = 219.
- IDs are 4-digit zero-padded (`0041`), joinable with the other `data/search/teachers/*/answers.csv`.

## Files
| File | Rows | Use |
|---|---|---|
| `answers.csv` | 535 | `[id, answer]` — Opus as a 5th teacher; joins with sonnet/gpt4/oss/xhigh answers |
| `results.csv` | 535 | per-item metadata (`opus_answer, n_tokens_output, wall_time_s, cost_usd, finish_reason, caphit_forced, error`) — cost/perf analysis |
| `items.jsonl` | 535 | full reasoning traces (`response_full`, `extracted_raw`, ...) — **LFS-tracked** — SFT data candidates |
| `anchor_v2_candidates.csv` | 316 | `id, anchor_answer, opus_answer, agree, anchor_tier, anchor_source, opus_verdict` — anchor revision decisions |
| `opus_5th_teacher.csv` | 219 | Opus + per-teacher columns + `opus_matches_majority, qtype` — slot 6-10 overlay building |

## Notes
- `answers.csv` is **derived** here from `results.csv` (`id` zero-padded, `answer = opus_answer`); the four extra DataApp-side files (`caphit_ids.json`, `progress.json`, `run.log`) were not landed (not in the target list).
- Opus is a TEACHER signal (DataApp pipeline), distinct from the competition inference model (Qwen3-4B-Thinking) — external APIs are not used at inference.
