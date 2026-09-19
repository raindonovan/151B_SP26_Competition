# Adapter results — per-item attribution and resolution limits

Issues [#8](https://github.com/raindonovan/151B_SP26_Competition/issues/8) and
[#9](https://github.com/raindonovan/151B_SP26_Competition/issues/9).
Offline only — no new inference, no new submissions. Reproduce with
`build_override_table.py` and `power_and_attribution.py` in this folder.

---

## 0. A denominator correction that changes the arithmetic

`COMPETITION.md:42-48` defines three eval surfaces. The one that matters here:

> **Public leaderboard** — accuracy on **~30% of the PRIVATE set (≈283 of 943 items)**
> **Full private (943)** — final ranking

So **private is the full 943**, and public is a ~283-item *subset of it* — not a
disjoint complement. Consequences:

| | items | 1 item |
|---|---|---|
| private | 943 | **0.1060 pp** |
| public | 283 | **0.3534 pp** |

- **Every** adapter override is in the private set by construction.
- Only ~30% of any override set lands in public.
- Any analysis that treats private as a ~660-item complement of public is wrong.
  (I made exactly that error in a first pass and it understated the effect by ~30%.)

---

## 1. The 11-item overlay — what the +0.004 can and cannot be

`submission/03_06/slot_adapter_rescue/03_06_R20_plus_adapter11.csv`,
**0.667 public / 0.587 private** against a base of **0.667 / 0.583**
(`submission/03_06/SCORES.md:43-44`).

| | base | adapter | delta | in items |
|---|---|---|---|---|
| private (943) | 0.583 | 0.587 | +0.004 | **+3.77** |
| public (283) | 0.667 | 0.667 | 0.000 | 0.00 |

Item by item, from `data/v5_per_item_decomp.csv` joined to the R20 analysis:

| id | class | tier | gold_source | indep | base | adapter |
|---|---|---|---|---|---|---|
| 89 | adapter_win | T4 | wolfram_HIGH | ✅ | `46.57` | `\frac{326}{7}` |
| 127 | both_wrong | T3 | search_GOLD | ✅ | `10.70` | `10.7` |
| 182 | both_wrong | T4 | search_GOLD | ✅ | `E` | `E` |
| 302 | both_correct | T2 | unanimous_teachers | ✅ | `H, H` | `H` |
| 317 | adapter_win | T4 | wolfram_HIGH | ✅ | `H` | `D` |
| 389 | both_wrong | T3 | search_GOLD | ✅ | `F` | `F` |
| 429 | adapter_win | T5 | sheet_dependent | ❌ | `7.05` | `A` |
| 463 | adapter_win | T5 | sheet_dependent | ❌ | `E` | `J` |
| 762 | adapter_win | T5 | sheet_dependent | ❌ | `110x^2 + 42x` | `2x(55x+21)` |
| 776 | adapter_win | T5 | sheet_dependent | ❌ | `17 \frac{1}{2}` | `A` |
| 839 | both_correct | T2 | unanimous_teachers | ✅ | `G, G` | `G` |

**All 11 are in the sft_v5 training set.** This overlay is pure recall; there is
no held-out content in it.

### The bound — the useful result

Only **6** of the 11 can possibly gain a point. Three are `both_wrong` and two are
`both_correct`; those contribute exactly 0 by construction. So:

- maximum achievable private delta = **6 items = +0.0064**
- observed = **+0.004 = 3.77 items**
- → roughly **4 of a possible 6** landed

The measurement is *bounded above*, which is worth more than the point estimate.
This is not "fine-tuning moved the score by +0.004"; it is "a hand-picked
6-item ceiling was ~2/3 realised".

And of those 6 wins, only **2 have independent gold** (89, 317 — both Wolfram).
The other **4 are scored against `sheet_dependent` gold on items the adapter was
trained on** — the scoring answer *is* the training label. Those are circular by
construction and cannot evidence capability.

### The public/private tension — currently unexplained

~3.3 of the 11 fall in public, carrying ~1.8 expected wins ≈ **+0.64 pp**.
Observed: **0.000**. Either the public draw missed the wins, or those wins are
not wins on Kaggle's gold. [#7](https://github.com/raindonovan/151B_SP26_Competition/issues/7)
(slice membership) decides it, and it is the single most informative thing left
that costs no compute.

---

## 2. `submission/v5_final.csv` is a different experiment from the one we assumed

Recovered the override set by diffing against Pick A: **exactly 50 cells**, ids
`0-71` (34), `444-451` (5), `700-723` (11). Disjoint from the 11 — **no overlap**.

The adapter that produced them is v7-pilot-A `v5_variance`, trained on **27 items**
(`inference/adapters/v7_pilot_a/dataset.jsonl`). Intersecting:

> **5 of the 50 overrides were trained on. 45 were not.**

That reframes [#6](https://github.com/raindonovan/151B_SP26_Competition/issues/6).
`v5_final.csv` is not another recall demo — it is the **largest held-out adapter
deployment in the repo**, 45 items the adapter never saw, and it has never been
scored. Only `adapter_rescue_61` (61 items, also ungraded,
[#10](https://github.com/raindonovan/151B_SP26_Competition/issues/10)) is comparable.

Gold quality on the 50: 28 independent, 22 `sheet_dependent`.

Caveat carried from #6: the 50 cells are **bare unboxed values** while Pick A's are
boxed. Confirm the grader's extraction treats them identically before reading
anything into a null.

---

## 3. What this does and does not settle

**Settled.** The +0.004 is ~4 items against a 6-item ceiling, on an overlay that is
100% in-training, where 4 of the 6 possible wins are scored against their own
training labels. It is not evidence of capability. `gradescope/finalreport/main.tex:320-323`
("a real but +0.004 effect… marginal at this scale") is the defensible reading;
`post_comp/LECTURE_19_FINDINGS.md:49` ("our v5 adapter SUCCEEDED… the success
signal") overstates what this particular measurement can carry.

**Not settled.** Whether targeted memorisation generalises at all. The two
datasets that could answer it — `v5_final.csv` (45 held-out) and
`adapter_rescue_61` (61 held-out) — are both ungraded. That is the gap worth
closing, and neither needs a new adapter.
