STATUS: PROPOSED. Pending human pass by strategy + rain. Do not consume downstream until canonical teacher_weighting_policy.md is committed.

# Teacher Weighting Policy (PROPOSED)

## Section 1 — Anchor precedence (LOCKED)
1. A+ multi-source: use, conf=VERY_HIGH (7 items)
2. A single-source: use, conf=HIGH, subject to Q3/Q4 review
3. Source conflicts already resolved at audit layer; see data/search/anchor_audit_report.md.

Multi-source A+ anchors win outright. Single-source A anchors route to review under Q3/Q4 triggers.

## Section 2 — Teacher precision table (subtype x anchor_tier)

| teacher | subtype | A+ (h/n) | A (h/n) | overall prec |
|---|---|---|---|---|
| sonnet | MCQ_single | 5/5 | 46/58 | 0.81 |
| sonnet | FREE_num_single | 0/1 | 52/70 | 0.732 |
| sonnet | FREE_other_single | 0/0 | 31/51 | 0.608 |
| sonnet | FREE_multi | 1/1 | 69/124 | 0.56 |
| gpt4 | MCQ_single | 2/5 | 38/57 | 0.645 |
| gpt4 | FREE_num_single | 0/1 | 53/70 | 0.746 |
| gpt4 | FREE_other_single | 0/0 | 28/51 | 0.549 |
| gpt4 | FREE_multi | 1/1 | 59/122 | 0.488 |
| oss | MCQ_single | 4/5 | 43/55 | 0.783 |
| oss | FREE_num_single | 0/1 | 50/70 | 0.704 |
| oss | FREE_other_single | 0/0 | 33/51 | 0.647 |
| oss | FREE_multi | 1/1 | 69/122 | 0.569 |
| xhigh | MCQ_single | 5/5 | 57/58 | 0.984 |
| xhigh | FREE_num_single | 0/1 | 47/70 | 0.662 |
| xhigh | FREE_other_single | 0/0 | 28/51 | 0.549 |
| xhigh | FREE_multi | 1/1 | 64/126 | 0.512 |

## Section 3 — Hypotheses tested vs Phase 2

- H1 (xhigh leads most subtypes): **FAIL** (leads 1/4 comparable subtypes)
- H2 (xhigh + one of sonnet/oss outweighs pair on tiebreak): **INSUFFICIENT_DATA** (provisional; routes ties to review until settled)
- H3 (gpt4 carries non-trivial weight): **FAIL** (gpt4 overall 181/307, prec 0.59)
- H4 (sonnet strongest comparator): **PASS** (overall precisions {'sonnet': 0.658, 'gpt4': 0.59, 'oss': 0.656, 'xhigh': 0.647})

## Section 4 — Gold-build voting rules (LOCKED)
- Anchor precedence (Section 1) applies first.
- MCQ vote counts only as a proper letter (^[A-Z](,[A-Z])*$).
- FREE_multi vote counts only with exact slot count.
- Lone gpt4 never breaks a tie.
- Tie-breakers within teacher bloc: PROVISIONAL pending H2. Until H2 settles, route ties to review.

## Section 5 — Items flagged for human review
- Q3 (all teachers vs anchor): 9 items
- Q4 (>=3 consensus vs single-source A): 29 items
- anchor rows with audit_action != pass: ['0097', '0252', '0285']

## Section 6 — Expected coverage per subtype

| subtype | total anchor attempts (all teachers) |
|---|---|
| MCQ_single | 248 |
| MCQ_set | 0 |
| FREE_num_single | 284 |
| FREE_other_single | 204 |
| FREE_multi | 498 |
