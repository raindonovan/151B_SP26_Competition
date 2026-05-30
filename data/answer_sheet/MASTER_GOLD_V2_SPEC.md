# MASTER_GOLD_V2 — Design Spec

**Status:** v2.3 — FINAL, implementation-ready (three critique passes, no remaining blockers). For `claude_vscode`.
**Owner:** claude_strategy. **Engine deps:** `scripts/gold_equiv.py` (which internally owns all `judger.py` usage — the builder does NOT import `judger.py` directly), `postprocessing/scripts/normalizer.py`.
**Builds:** `scripts/build_master_gold_v2.py` (sibling of the existing v1 builder), `data/answer_sheet/master_gold_v2.csv`, `data/answer_sheet/normalization_diagnostic.csv`.

---

## 1. Purpose

Produce a single **Qwen-independent surrogate-gold answer sheet** that grades inference runs for Bucket A/B classification. The sheet's `gold_best_answer` is the answer key; runs are graded against it.

This is **v2**. It supersedes `master_gold_v1.csv` by fixing a systematic flaw: v1 computes teacher agreement by **string match on raw answers**, which produces false disagreements whenever teachers give the same value in different surface form. The canonical example:

```
id=193   sonnet="A, C, D"   gpt4="A,\ C,\ D"   oss="A,\;C,\;D"
v1 teacher_agree = 1   (correct value: 3)
```

Multi-answer items are hit hardest — false-disagreement rate scales with slot count (12–14% no-gold at 1 slot vs 30–43% at 4+ slots), because more slots means more chances for a delimiter/order/representation difference to break a string comparison. An unknown fraction of the 178 v1 "no-gold" (T4) items are **false T4**: teachers actually agree, the comparator just can't see it.

v2 fixes this by **normalizing every signal's answer upstream, then computing agreement via type-routed equivalence**, not string match.

---

## 2. Scope and non-goals

**In scope:** consolidating teachers + Wolfram + search into one gold sheet; recomputing agreement and tiers under normalization + value-equality; emitting a diagnostic that makes every normalization decision inspectable.

**Out of scope / explicitly excluded from gold (circularity & reliability):**
- `qwen_sc8` / `qwen_cross_config` — Qwen is the *subject* of analysis; using it as gold grades Qwen against itself.
- `back_solve_*` — unreliable on the full 943 (Kaggle scores a ~283-item slice, so back-solved tiers don't generalize).
- `rescue_*` — Qwen-derived (rescue votes are SC-sample counts); same circularity as `qwen_sc8`.

**Not a normalizer end-to-end stress test.** This build wraps short clean answer strings in `\boxed{}`, which exercises *surface* normalization but NOT the normalizer's hardest path (extraction from long Qwen responses with multiple boxes and reasoning traces). Treat normalizer testing as a useful side effect, not a goal.

---

## 3. Inputs

All on `main`. Read-only.

| Source | Path | Key fields |
|---|---|---|
| Item tracker (base) | `data/master_item_tracker.csv` | `id`, `is_mcq`, `teacher_sonnet`, `teacher_gpt54`, `teacher_gpt_oss`, `teacher_gpt55xh`, `n_ans_slots_q`, `wolfram_override`, `wolfram_confidence`, `mcq_letters` |
| Search columns | `data/MASTER_ANSWERS.csv` | `item_id`, `search_answer`, `search_status`, `search_source` |
| Consolidated search (245 GOLD) | `data/search/web_search/search_results.csv` | `item_id`, `search_status`, `found_answer`, `source_url` |
| Item metadata for normalizer | `private.jsonl` (repo root; or `/home/dvaneetv/private/151B_SP26_Competition/private.jsonl`) | `id`, `question`, `options` (MCQ only) |
| Normalizer | `postprocessing/scripts/normalizer.py` | `Normalizer(mode).normalize_with_report(response, item) -> .candidate, .flags` |
| Comparator | `scripts/gold_equiv.py` | `gold_equiv(pred, gold, qtype) -> True / False / None` |

**Do NOT use `data/search/wolfram/MASTER_QUESTIONS.csv`.** It uses zero-padded ids (`'0000'`) while the tracker uses unpadded (`'0'`); the join silently fails (this caused a `free_multi=0` bug in the v1 builder). Infer `qtype` from the tracker instead (§5).

---

## 4. Architecture

```
raw signals (per item)            normalized signals
  teacher_sonnet ─┐                 norm_sonnet ─┐
  teacher_gpt4   ─┤  Normalizer      norm_gpt4   ─┤  pairwise gold_equiv
  teacher_oss    ─┤ (conservative,   norm_oss    ─┤  clustering  ──► teacher agreement
  wolfram        ─┤  \boxed{} wrap)  norm_wolfram─┤
  search(GOLD)   ─┘                  norm_search ─┘
                                          │
                       gold_equiv(indep, teacher_consensus, qtype)
                                          │
                                   gold_best_answer + tier  ──►  master_gold_v2.csv
                                          │
                              (raw+norm surfaces preserved)
```

Two engines, distinct jobs:
- **Normalizer** = canonicalizes *surface form* (delimiters, wrappers, structural fixes). Applied to every signal first.
- **`gold_equiv`** = type-routed *value equivalence* (judger value-equality + sympy parse coverage). Used for both teacher clustering and cross-signal comparison. **`gold_equiv` is the primary comparator everywhere a comparison is made** — never call `judger.judge_single_numerical_value` directly on free-form answers (it is single-scalar only and breaks on multi-answer lists).

---

## 5. qtype inference (from tracker — no external file)

```
def infer_qtype(tracker_row, private_item):
    if str(tracker_row.get('is_mcq','')).lower()=='true' or private_item.get('options'):
        return 'MCQ'
    n = int(tracker_row.get('n_ans_slots_q') or 0)
    return 'free_multi' if n >= 2 else 'free_single'
```
Validated distribution: MCQ=300, free_single=305, free_multi=338 (matches intended).

---

## 6. Processing steps

### Step 1 — Normalize every signal answer

**Search source resolution (explicit):** use `data/search/web_search/search_results.csv` when `search_status=='GOLD'` and `found_answer` is non-empty; otherwise fall back to `MASTER_ANSWERS.csv` **only if** `search_status=='GOLD'` and `search_answer` is non-empty. No other search source counts as GOLD.

Build `item_dict` from `private.jsonl` (must carry `options` for MCQ routing). For each item, for each signal with a non-empty answer (`teacher_sonnet`, `teacher_gpt4`=`teacher_gpt54`, `teacher_oss`=`teacher_gpt_oss`, `wolfram`=`wolfram_override`, `search` per the rule above):
```
response = f"\\boxed{{{raw_answer}}}"
try:
    res = Normalizer('conservative').normalize_with_report(response, item_dict)
    normalized = res.candidate
    if raw_answer.strip() and not normalized.strip():        # GUARD
        log_empty_output(item_id, signal, raw_answer)         # normalizer destroyed a value
        normalized = raw_answer                               # fall back to raw, flag it
    flags = res.flags
except Exception as e:
    log_exception(item_id, signal, raw_answer, e)             # per-signal exception log
    normalized, flags = raw_answer, ['NORMALIZER_EXCEPTION']
store(raw_answer, normalized, flags)
```
**Mode is `conservative` ONLY for v2.** `default`/`aggressive` (frac-promotion, heuristic transforms) are out of scope for the first build. **Report-vs-abort semantics:** the build ALWAYS completes (one bad signal falls back to raw, never kills the sheet). At the end emit a **mandatory summary block**: per-signal counts of exceptions and empty-from-non-empty outputs. If either count exceeds a threshold (suggest: >5 per signal, or >1% of all signals), mark the build **SUSPECT** (non-zero exit code / explicit flag in the summary) so it isn't silently trusted. Inspectable, but not self-destructing.

### Step 2 — Teacher agreement via pairwise clustering (NOT string-match)
```
qtype = infer_qtype(...)
nt = [(src, norm) for src, norm in [('sonnet',norm_sonnet),('gpt4',norm_gpt4),('oss',norm_oss)] if norm.strip()]
clusters = []   # each cluster: list of (src, norm)
for src, ans in nt:
    for c in clusters:
        if gold_equiv(ans, c[0][1], qtype) is True:
            c.append((src, ans)); break
    else:
        clusters.append([(src, ans)])
largest = max(clusters, key=len) if clusters else []
new_teacher_agree = len(largest)

# DETERMINISTIC representative (cluster members may share value but differ in surface):
# 1) pick the normalized surface that appears most often within the cluster (modal surface)
# 2) tie-break by source priority: sonnet > gpt4 > oss
from collections import Counter
SRC_RANK = {'sonnet':0, 'gpt4':1, 'oss':2}
if new_teacher_agree >= 2:
    surf_counts = Counter(norm for _, norm in largest)
    top = max(surf_counts.values())
    cand_surfaces = [s for s, n in surf_counts.items() if n == top]
    # among members carrying a top surface, choose the highest-priority source
    chosen = min((m for m in largest if m[1] in cand_surfaces), key=lambda m: SRC_RANK[m[0]])
    norm_teacher_consensus = chosen[1]
    raw_teacher_consensus  = raw answer of teacher `chosen[0]`
else:
    norm_teacher_consensus, raw_teacher_consensus = '', ''
```
Rationale: clustering by `gold_equiv` (not equality) catches order-only and representation-only equivalence that survives normalization — the exact false-T4 driver on multi-answer items. Note: `norm_teacher_consensus` is a **canonical representative** of the agreeing cluster, not the only equivalent surface — members may agree by value while still differing in normalized surface. Downstream consumers should treat it as "a" correct surface, not "the" unique one.

### Step 3 — Independent vs teachers (gold_equiv PRIMARY)
Independent present if `wolfram_confidence=='HIGH'` (use `norm_wolfram`) or `search_status=='GOLD'` (use `norm_search`); Wolfram outranks search.
```
if indep_present and new_teacher_agree >= 2 and norm_teacher_consensus:
    r = gold_equiv(norm_indep_answer, norm_teacher_consensus, qtype)
    indep_vs_teacher = {True:'agree', False:'disagree', None:'review'}[r]
conflict = (indep_vs_teacher == 'disagree')
```

### Step 4 — gold_best_answer + tier
Precedence (on normalized answers):
- **MCQ:** `norm_teacher_consensus` when `new_teacher_agree >= 2`. **Must be a bare letter** (e.g. `B`), never option text — strip any option-surface; if the consensus isn't a clean letter, treat as no MCQ gold.
- **free:** `norm_wolfram` (HIGH) > `norm_search` (GOLD) > `norm_teacher_consensus` (agree==3) > `norm_teacher_consensus` (agree==2).

Tier (qwen clause dropped — avoids grading Qwen against itself; conflict caps at T4):
```
T1 = new_agree==3 AND indep_present AND indep_vs_teacher=='agree'
T2 = new_agree==3, OR (new_agree==2 AND indep_present AND agree)
T3 = new_agree==2, OR (indep_present AND new_agree<=1)
T4 = otherwise;  force T4 if conflict
```

**CONFLICT HANDLING (critical — do not emit gold for disputed items).** If `gold_conflict_flag` is True, there is no trusted gold:
```
gold_best_answer_norm = ''        # NO final answer — item is unresolved
gold_best_answer_raw  = ''
gold_source           = 'conflict'
# preserve the competing candidates for manual review in the existing columns:
#   norm_teacher_consensus / raw_teacher_consensus  AND  norm/raw_independent_answer
```
This guarantees downstream run-grading never grades Qwen against a disputed answer. A conflict item carries its competing candidate surfaces but no `gold_best_answer`.

### Step 5 — Output (preserve BOTH surfaces)
`data/answer_sheet/master_gold_v2.csv`:
```
item_id, qtype, tier_v1, tier_v2, tier_changed, tier_direction,
old_teacher_agree, new_teacher_agree,
raw_teacher_consensus, norm_teacher_consensus,
raw_independent_answer, norm_independent_answer, indep_source,
indep_vs_teacher, gold_conflict_flag,
gold_best_answer_norm, gold_best_answer_raw, gold_source,
n_ans_slots
```
`data/answer_sheet/normalization_diagnostic.csv` (long format, one row per signal per item):
```
item_id, qtype, signal, raw_answer, normalized_answer, flags
```
Preserving raw + normalized surfaces is required: the submission pipeline separates *math agreement* from *submission surface* (Kaggle multi-answer grading is order-sensitive). We must be able to tell when normalization **fixed agreement** vs when it merely **overwrote an interpretable source surface**.

---

## 7. Normalizer caveats (do not treat as production-safe)
The main-branch normalizer is not in a fully-fixed state. **The primary operational risk is that its multi-answer extraction is not production-hardened:**
- it still extracts **all** boxed content globally (`normalizer.py` ~line 255);
- it still runs the **older multi-answer path** (~line 171).
These are the behaviors most likely to mishandle multi-slot answers — watch them closely on `free_multi` items (the population this whole build targets). A secondary, lesser risk: it imports old strict Hendrycks (`from hendrycks_local import is_equiv, strip_string`) for some internal decisions, which may carry its own equivalence blindspots.
Conservative mode avoids frac-promotion (mooted by the judge update) but does not make the normalizer correct by construction. Every output must be inspectable via `flags`, and `free_multi` outputs deserve extra scrutiny in the verification pass.

---

## 8. Verification (must run and report)
1. **Tier distribution v1 vs v2**, side by side. Expect **T1+T2 up, T4 down**.
2. **Promotions (T4→T2+):** list all; spot-check 15 to confirm teachers genuinely agree post-normalization (the id=193 pattern). These are the wins.
3. **Demotions (T2→T4):** should be near-zero. **Every demotion must be audited.** Most should be *explainable* — a legitimate demotion can occur if v1 had a false raw-string consensus, or if normalization exposes a real independent-source conflict that v1's string-match masked. **Unexplained** demotions indicate a normalizer bug. Audit each; do not accept any unexplained.
4. **Normalizer flag histogram** across all signals (what it actually did).
5. **Conflict count** v1 (5) vs v2.
6. **Spot-check 20 random `gold_best_answer_norm`** values — confirm the normalizer did not mangle the value.

---

## 9. Success criteria
- Runs clean on all 943 × signals; no exceptions.
- T4 drops; demotions ≈0.
- Diagnostic CSV makes every normalization step inspectable.
- v1 builder untouched; v2 is a sibling reusing `gold_equiv` + v1 tier logic.
- Spot-checks pass.

---

## 10. Implementation notes
- **`Normalizer('conservative')` only for v2.** `default`/`aggressive` modes are explicitly out of scope for this first build (frac-promotion is mooted by the judge update; heuristic transforms add risk).
- Build `scripts/build_master_gold_v2.py` as an **evolution of** `scripts/build_master_gold.py` (reuse its loaders, `gold_equiv` import, and tier logic). Do not write a disconnected pipeline. The builder imports `gold_equiv`, never `judger.py` directly.
- **Preserve v1 output columns where they exist; APPEND v2-specific columns rather than renaming.** This keeps side-by-side v1↔v2 auditing clean (a reviewer can diff the two sheets column-aligned).
- `master_gold_v2.csv` is force-added (`git add -f`) — `data/*` is broadly gitignored but the other answer-sheet CSVs are force-tracked; follow that convention.
- Credentials pre-configured on the runtime; if push auth fails: `scripts/setup_git.sh | bash -s -- "$PAT"`. Never commit or embed the PAT.
- When search/wolf land new GOLD/HIGH data, re-run is idempotent — just rebuild.
