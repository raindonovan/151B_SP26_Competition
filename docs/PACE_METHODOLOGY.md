# PACE Methodology -- Verification with Wolfram + Python

**Last updated:** 2026-05-27 ~02:00 local. Established empirically during smoke wait via demo on 2 training items.

## Purpose

PACE = **Programmatic Answer-label Computational Evaluation**. Cross-verify answer-sheet / training-set labels using external math tools to catch wrong labels BEFORE they corrupt training or voting.

## Current scope (Extended PACE)

- ~200-300 computable items across all 943 private items (was: only the 391 SFT training items per memory #24)
- Goal: build Sheet v6 with PACE-corrected labels; deprioritize items with disputed labels
- Estimated effort: ~5-10 hours of claude_strategy work spread across days 2-5

## Tool palette

| Tool | Strength | Use when |
|---|---|---|
| **Wolfram Alpha (MCP)** | Symbolic algebra, integrals, FullSimplify, special functions | Closed-form math: integrals, derivatives, algebraic simplification, geometry with assumptions |
| **Python (stdlib)** | Iteration, modular arithmetic, digit ops, brute enumeration | Enumeration problems: digit sums, modular search, sequence checks |
| **SymPy (Python)** | Programmatic symbolic computation, batchable | Batched verification scripts; when Wolfram NL fails |
| **SciPy/NumPy** | Numerical methods, distributions, optimization | Statistics, hypothesis tests, optimization, simulation |
| **mpmath** | Arbitrary-precision | When floating-point precision matters |

The other "online math" tools (Symbolab, Mathway, Microsoft Math Solver, Photomath) are notably weaker on hard problems and should be skipped. Wolfram is the only one with a real symbolic engine behind it.

## Empirically discovered Wolfram gotchas (from demo)

1. **Wolfram's NL parser is weaker than its reputation suggests.** "Sum of digits of all integers from 1 to 79" -> No Results Found across 5 phrasings. The free Wolfram Alpha NL backend is much weaker than the Mathematica engine.

2. **Mathematica function syntax wins.** `FullSimplify[(64x^5)^(1/4)*(64x^7)^(1/4)] assuming x>0` worked perfectly. Bare `simplify (...)` gave an incomplete answer.

3. **Always add domain assumptions.** `assuming x>0` made the difference between `8 (x^5)^(1/4) (x^7)^(1/4)` and `8x^3`.

4. **Python fallback is REQUIRED, not optional.** Enumeration problems (digit sums, modular arithmetic, sequence checks) are Python's home turf -- Wolfram is unreliable here.

## Classification tree (which tool first)
problem text ->
+-- iterate over integers, digit ops, modular -> Python first
+-- symbolic algebra, integrals, derivatives -> Wolfram (Mathematica syntax + assumptions)
+-- statistics (distributions, hypothesis tests) -> SciPy
+-- number theory deep (factoring large N, Pell eqs) -> Wolfram, verify with Python
+-- geometry / trig identities -> Wolfram with assumptions
+-- word problems requiring algebraic setup -> Setup by hand, verify with Wolfram + Python

## Demo iterations (2026-05-27 ~02:00)

### Iteration 1 -- id=0937 (SFT v5 training set)

- **Q**: Sum of all digits in the integers from 1 to 79, inclusive
- **Training label**: 640
- **Wolfram NL**: failed across 5 attempts (variations of `"sum of digits 1 to 79"`, `Total[Flatten[IntegerDigits/@Range[79]]]`, sigma notation, etc.)
- **Python verification**: `sum(sum(int(d) for d in str(n)) for n in range(1, 80))` = 640 OK
- **Verdict**: Label CORRECT. Wolfram NL failed, Python won.

### Iteration 2 -- id=0111 (SFT v5 training set)

- **Q**: Simplify $\sqrt[4]{64x^5} \cdot \sqrt[4]{64x^7}$ assuming x > 0
- **Training label**: $8x^3$
- **Wolfram with `FullSimplify` + assumption**: $8x^3$ OK
- **Verdict**: Label CORRECT. Wolfram won (with correct syntax).

## Workflow per item

1. Read question text
2. Classify problem type
3. Try primary tool (per classification tree)
4. If primary fails, try fallback
5. If both tools agree -> label is verified
6. If tools disagree with each other -> hard problem, flag for manual review
7. If tools agree but disagree with sheet/training label -> **SHEET/LABEL MAY BE WRONG**, flag
8. Record verdict in `pace_log.jsonl`

## What to do with PACE findings

- **Verified correct**: no action; raise confidence in label
- **Verified WRONG** (tools agree but disagree with label): flag in Sheet v6 builder
  - For SFT training items: too late -- v5 already trained. Note for v7 dataset.
  - For private items in candidate submissions: override the disputed answer
  - For answer-sheet items used in info_4 patches: rebuild patches with corrected label
- **Inconclusive** (tools disagree with each other): exclude from confidence-weighted voting

## Iteration speed

The two demo iterations took ~3 minutes total including all Wolfram retries. At ~2 min/item, ~200 items = ~7 hours of claude_strategy work. Easily fits across days 2-5 in 30-60 min sessions.

## See also

- `docs/MASTER_TODO.md` -> "Extended PACE" task in Day 2 / Day 4-5
- `docs/STRATEGY_IDEAS.md` -> pace_patch rationale (catches wrong labels before memorization)
- Memory #24 -> "PACE_PATCH (locked): Targeted computational verification..."
