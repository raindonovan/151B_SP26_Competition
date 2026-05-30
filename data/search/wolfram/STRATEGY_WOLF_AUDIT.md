# Strategy's Independent Wolfram Audit — 2026-05-30

**Auditor:** claude_strategy (fresh session, repo-only pickup).
**Purpose:** an independent pass over the Wolfram results to cross-check against
ChatGPT's parallel pass (`CHATGPT_AUDIT_PASS2.md`, pending). Guards the
conformity/circularity trap — this is NOT a re-read of the agent's own summary; it
re-derives a sample from scratch and stress-tests the load-bearing claims.

**Caveat (carry everywhere):** no clean ground truth exists for the 943 set. Every
number here is an estimate against fallible proxies. Wolfram is our one *independent*
(non-LLM) source, which is exactly why it's worth auditing on its own terms.

---

## 1. Structural integrity of WOLF_RESULTS.csv — CLEAN
- 943 rows, 943 unique ids, all 4-digit zero-padded.
- Status: 477 DONE / 373 UNVERIFIED / 92 INCONCLUSIVE / 1 DISPUTED — matches RESULTS_SUMMARY.
- Confidence: 309 HIGH + 161 MED + 4 PARTIAL + 2 MEDIUM + 1 consensus-only = 477. Checks out.
- 0 DONE rows with an empty answer or empty confidence; 0 UNVERIFIED rows with a leaked answer.
- No internal inconsistencies found in the scorecard.

## 2. DATA-HYGIENE BUG (minor, fix before gold build)
Confidence column has BOTH `MED` (161 rows) and `MEDIUM` (2 rows: **0787, 0894**).
The v3 gold build weights "HIGH 3.0, MED 1.2." If it keys on the exact string `MED`,
those 2 `MEDIUM` rows get dropped/unweighted. **Action:** normalize `MEDIUM`→`MED`
in the build join (or fix at source). Low stakes (2 items, both near-known-bugs) but
it's a silent-drop class of bug.

## 3. Confidence calibration — GOOD
The soft-confidence labels cluster on the independently-known dataset bugs:
- PARTIAL: 0585, 0622, 0858 (interpretation-MCQ truncation class), 0749 (slot-boundary).
- MEDIUM: 0894 (question hints 9, verified 10 — flagged borderline), 0787 (unit ambiguity).
- consensus-only: 0011 (truncated problem text).
i.e. the agent down-weighted exactly the items that are genuinely ambiguous. That's
the calibration we want.

## 4. Discrepancy set (the 58 "sheet is wrong" claims) — VALIDATED + directly actionable
Cross-referenced all 58 ids against type/confidence:
- **Type: 39 free_multi + 19 free_single = 58 free-form. ZERO MCQ.**
- **Confidence: 54 HIGH + 4 MED.**

Strategic consequence: the entire discrepancy set is **directly usable** — the
verified value drops into the gold sheet as the corrected answer with NO
letter-normalization needed. It also confirms the agent correctly avoided the MCQ
letter-vs-value false-mismatch trap (no MCQ was ever flagged as a discrepancy,
because a LETTER can't be cleanly compared to a derived VALUE).

### Independent spot-check — 7/7 confirmed (3 recomputed via Wolfram MCP)
| id | verified (Wolfram) | sheet "best" (wrong) | failure mode | check |
|----|--------------------|----------------------|--------------|-------|
| 0000 | 4, 16 | 16 | undercount (dropped slot a) | hand |
| 0024 | 1 | 2 | arithmetic (SSR) | **Wolfram MCP** |
| 0029 | 38.2 | 39 | bad rounding (26/68=38.235%) | hand |
| 0135 | 3/5 | 36 | catastrophic algebra | hand |
| 0171 | 20 | 21 | off-by-one area (4×5) | hand |
| 0313 | -2√14/15 | "-21414" | digit-concatenation | **Wolfram MCP** |
| 0557 | 5 | 6 | trivial off-by-one (\|5\|) | hand |

All 7 confirm: Wolfram value correct, sheet value genuinely wrong. No false discrepancies in the sample.

## 5. HIGH "match" bucket — genuinely solved, not rubber-stamped
Spot-checked a non-discrepancy HIGH item by independent computation:
- **0017** (a₀=1,a₁=2,aₙ=4aₙ₋₁−aₙ₋₂; least odd prime factor of a₂₀₁₅ = 181):
  Wolfram MCP confirms a₂₀₁₅ ≡ 0 (mod 181), and ≢ 0 (mod 3,5,7,11,13,31). 181 stands.

## 6. KEY LIMITATION to put to ChatGPT's pass (the circularity probe)
The strongest claim in the audit is: "the 254 unflagged solvable items → 0
discrepancies → the sheet was already right (B19–B29)." But the verification compares
*Wolfram value vs sheet best_answer*. Where the sheet's best_answer was itself
inherited from a teacher, a "match" can be partly circular if Wolfram and the teacher
landed on the same answer for the same (possibly wrong) reason — esp. on items with a
single canonical method. WOLF_RESULTS.csv does not carry the sheet's best_answer
column, so I can't test this here. **This is the thing to diff ChatGPT against:** does
ChatGPT, working the raw questions independently, reproduce the same verified values,
or does it surface discrepancies inside the "0-discrepancy" unflagged set?

## 7. Cross-check checklist for when CHATGPT_AUDIT_PASS2.md lands
1. Same ~58 discrepancies? (set diff — note any ChatGPT-only or strategy/Wolf-only)
2. Same *verified values* on the overlap? (value mismatches = the real signal)
3. Any of the 477 HIGH/MED that ChatGPT calls wrong?
4. Any discrepancy inside the 254 unflagged "confirmation" set? (tests §6)
5. Treat agreement skeptically if both used Wolfram as the engine — agreement of two
   Wolfram passes is consistency, not independent corroboration. Teacher-independent
   agreement is the stronger evidence.

## Bottom line
Wolfram scorecard is structurally sound and well-calibrated; the 58-item discrepancy
set is high-quality and 100% directly actionable (free-form, mostly HIGH). One trivial
string bug (MED/MEDIUM). The open question is circularity in the unflagged
"confirmation" pass — answerable only by ChatGPT's independent re-derivation, not by
re-reading our own notes.
