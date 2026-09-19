# v5 adapter-vs-base per-item decomposition (Phase 0 / patch B2)

v5 trained set: **391 items**. Adapter SC@3 vs base R20 SC@8, both judged vs gold by **value-equality** (grading.grader.Grader.is_equal — the current Kaggle grader). `*_strict` CSV columns preserve the Hendrycks is_equiv hedge.

## Class totals

| class | count | % of 391 |
|---|---|---|
| adapter_win | 8 | 2.0% |
| adapter_loss | 1 | 0.3% |
| both_correct | 379 | 96.9% |
| both_wrong | 3 | 0.8% |

**Net adapter contribution = adapter_win − adapter_loss = 8 − 1 = +7 items** (on the trained set; consistent with ~break-even global if ≈0).

## Class × tier

| class | T1 | T2 | T3 | T4 | T5 | T0 |
|---|---|---|---|---|---|---|
| adapter_win | 0 | 0 | 0 | 2 | 6 | 0 |
| adapter_loss | 0 | 0 | 0 | 1 | 0 | 0 |
| both_correct | 2 | 341 | 29 | 3 | 4 | 0 |
| both_wrong | 0 | 0 | 2 | 1 | 0 | 0 |

## Class × item type

| class | MCQ | free-form |
|---|---|---|
| adapter_win | 3 | 5 |
| adapter_loss | 1 | 0 |
| both_correct | 196 | 183 |
| both_wrong | 2 | 1 |

## Class × gold provenance

| class | HIGH | MED | LOW |
|---|---|---|---|
| adapter_win | 2 | 6 | 0 |
| adapter_loss | 1 | 0 | 0 |
| both_correct | 345 | 34 | 0 |
| both_wrong | 3 | 0 | 0 |

## Top-line interpretation

- **Hard items (T3/T4/T5, n=48)**: adapter_win 8, adapter_loss 1 → **net +7**.
- **Easy items (T1/T2, n=343)**: adapter_win 0, adapter_loss 0 → **net +0**.
- **MCQ (n=202)**: net +2 (win 3 / loss 1). **Free-form (n=189)**: net +5 (win 5 / loss 0).
- **Did the adapter help where v7 plans to target (T3/T4/T5 wrong-residual)? → HELPED (net +7 on hard items, value-equality grader).**

## ⚠️ Caveats (this is WEAK evidence — read before acting)

1. **Memorization, not generalization.** The adapter was TRAINED on these exact 391 items, so `both_correct` (379, 97%) and adapter-correctness partly measure target memorization, not held-out capability. The adapter's marginal contribution over base is what matters, and base already gets ~97% of the trained set right.
2. **Primary metric = value-equality (Kaggle grader). is_equiv (strict) OVERSTATES adapter wins.** Under strict is_equiv the net was +12 / +9-hard; **6 of those 14 'wins' were FORMAT-ARTIFACTS** where the base answer is value-equal-but-format-divergent (ids 14, 118, 132, 302, 556, 839 — trailing-zero like `10.80`≡`10.8`, dup-option like `H,H`≡`H` / `G,G`≡`G`, and ln/log + decimal-vs-fraction surface diffs). Those evaporate under value-equality AND are ALREADY handled by the Tier-1 structural normalizer — so they are NOT adapter-unique value. The class totals above use value-equality (primary), leaving **8 real-capability wins** (ids 89, 184, 317, 404, 429, 463, 762, 776). **Superseded 2026-09-19 — see the official-key regrade below: 6 wins / 4 losses, none of them a reasoning change.**
3. **Tiny absolute numbers.** Net is single-digit items on a 391 trained set; consistent with v5's ~break-even global score. The adapter is not a large lever; the real-capability hard-item wins (post-format-filter) are the only defensible signal for v7.

## Post-competition regrade against the official key (2026-09-19)

The tables above grade against the competition-time answer sheet. Regraded against the official Kaggle key (`data/raw/private_answers.jsonl`) with the validated grader path (`Grader.auto_judge` over gold slots, the path that reproduced 943/943 on the official solutions):

| class | vs answer sheet | vs official key |
|---|---|---|
| both_correct | 379 | 352 |
| adapter_win | 8 | 6 |
| adapter_loss | 1 | 4 |
| both_wrong | 3 | 29 |
| **net** | **+7** | **+2** |

- Wins vs key: 317, 463 (answer changed; labels were written into the trace), 429, 776 (value vs option letter), 302, 839 (duplicated MCQ letter collapsed).
- Losses vs key: 184 (sheet label wrong), 762 (factored form does not grade equal to the key), 238 (thin-space LaTeX in the answer), 831 (adapter vote split 2-1, the one non-reproduction).
- Of the 8 listed above: 89 is both-wrong vs the key (key is 46.5), 404 is both-correct, 184 and 762 are losses.
- The adapter's voted answer equals its training label on 390/391 items; the answer sheet disagreed with the key on 33 of the 391. Every loss was a label or format error, not a failed memorization.
- Item 317: options D and H are the same expression; the base derived it and boxed H, the adapter recited the same derivation and boxed the accepted letter D.

Full write-up and literature: GitHub issue #14. Interactive per-item forensics: https://claude.ai/artifact/STcxiVKPyyDYt4ArikHQXb
