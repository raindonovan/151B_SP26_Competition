# ANSWER_SHEET_SCHEMA.md — MASTER_ANSWERS.csv columns & tier formula

## Existing columns (keep)
`item_id, teacher_sonnet, teacher_gpt4, teacher_oss, wolfram_answer, wolfram_confidence, search_answer, search_status, qwen_sc8_voted, sheet_best_answer, sheet_tier, category, format_only_diff_teacher, undercount_flag, ...`

## New columns to add

| Column | Type | Source | What it means | How to compute |
|---|---|---|---|---|
| `qwen_cross_config_agree` | bool | scan inference runs | TRUE iff voted answer from SC8 ∧ SC16 ∧ SC32 ∧ nothinking all match (Hendrycks-normalized) | For each item, collect voted answer per run; compare pairwise using Hendrycks `is_equiv`; TRUE only if ALL configs unanimous |
| `qwen_cross_config_answer` | str | scan inference runs | the unanimous answer (when `qwen_cross_config_agree=TRUE`); else blank | the value all configs agreed on |
| `structural_pass` | tri-state (TRUE/FALSE/blank) | per-item structural rule | TRUE = no structural violation; FALSE = violates a constraint; blank = no applicable rule | type-specific: probability ∈ [0,1]; matrix marked symmetric IS symmetric; AIME-style asks for integer 0-999 → answer is integer in range; count question → non-negative integer; etc. |
| `source_corpus` | enum | search + heuristic | `AIME / AoPS / Putnam / textbook / WeBWorK / AMC / unknown` | from search hit URL pattern; or keyword heuristic on question text |
| `wolfram_canonical_form` | bool | Wolfram | TRUE iff question asks for "factored form" / "simplest form" / "canonical form" AND Wolfram answered HIGH | regex on question + check wolfram_confidence=HIGH |
| `tier` | enum | derived | `T1 / T2 / T3 / T4 / T5` | per tier formula below |

## Tier formula (LOCKED)
T1 (ground-truth confidence ≥99%):
3/3 teachers agree
AND at least one independent non-LLM source agrees
(wolfram_confidence=HIGH
OR search_status=GOLD
OR qwen_cross_config_agree=TRUE)
AND structural_pass ≠ FALSE
T2 (strong confidence ~90%):
(3/3 teachers agree AND no independent source has weighed in yet)
OR (2/3 teachers + at least one independent non-LLM source agrees with majority)
AND structural_pass ≠ FALSE
T3 (medium confidence ~75%):
majority teacher (≥2/3) AND qwen_sc8 agrees with majority
AND no contradicting independent source
T4 (low ~50%):
any of: teachers split, Qwen disagrees with all teachers,
independent source contradicts teachers — single weak signal only
T5 (very low):
no clear signal; needs probe to upgrade

## Compute order

1. `qwen_cross_config_agree` + `qwen_cross_config_answer` — scan all run JSONLs, Hendrycks-compare per item across configs
2. `structural_pass` — apply structural rules per item type/subject
3. `source_corpus` — from search results URLs + keyword heuristic fallback
4. `wolfram_canonical_form` — regex on question text + wolfram_confidence check
5. `tier` — apply formula above

## How `qwen_cross_config_agree` is the highest-leverage column

It costs nothing to compute (data we already have) and could expand T1 from the current ~90 items to perhaps 200-300 overnight. Every additional T1 item is a new local-eval anchor, ground-truth row for the inference scan, and SFT label candidate.

## Implementation responsibility

This is an agent task (scanning JSONLs needs shell). Spawn a data_agent pointed at `data/CLAUDE.md` with this schema; have it produce an updated `MASTER_ANSWERS.csv` + a derived `testing/tier1_ground_truth.csv` (just the T1 rows with the canonical answer).
