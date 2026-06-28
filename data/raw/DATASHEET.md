# Datasheet — CSE 151B/251B SP26 Math Reasoning: Questions & Answers (raw/reference)

Follows the *Datasheets for Datasets* structure (Gebru et al., 2018). This folder is the
**immutable source-of-truth** for the project: the competition questions and their official
answers. Everything else (inference samples, analyses) derives from this.

`schema_version: 1.0` · `dataset_version: 2026-06-28` · owner: Rain van Eetveldt (`raindonovan`)

## Motivation

- **Why it exists:** the cornerstone reference data for the **Summer Research Program** — a
  sample-level re-grade of self-consistency inference (re-extract → re-vote → grade against
  truth), e.g. *how often was a correct answer present in a sample but outvoted*. That work
  needs trustworthy questions + answers as a fixed foundation.
- **Origin:** the UCSD CSE 151B/251B SP26 Kaggle competition (improve mathematical reasoning
  of a frozen `Qwen/Qwen3-4B-Thinking-2507` on a held-out math test set).

## Composition

Two sets — **public** (1126) and **private** (943) — each split into **questions** (inputs)
and **answers** (labels), plus a joined convenience view. Questions and answers join on `id`.

| File | Rows | Fields |
|---|---|---|
| `private_questions.jsonl` | 943 | `id, question, options, question_type, n_ans_slots, is_matharena` |
| `private_answers.jsonl` | 943 | `id, answer` |
| `private_all.jsonl` | 943 | questions ⋈ answers (all of the above) |
| `public_questions.jsonl` | 1126 | `id, question, options, question_type, n_ans_slots` |
| `public_answers.jsonl` | 1126 | `id, answer` |
| `public_all.jsonl` | 1126 | questions ⋈ answers |
| `_original/` | — | the exact Kaggle files as received (provenance anchor) |

**Fields.**
- `id` — integer item id (private 0–942; public 0–1125). Unique within a set.
- `question` — problem text (verbatim).
- `options` — list of MCQ option strings; `[]` for free-form.
- `question_type` — one of **`MCQ`** (options present), **`FREE_SINGLE`** (no options, one
  required value), **`FREE_MULTI`** (no options, ≥2 required values). *Derived* (see Preprocessing).
- `n_ans_slots` — number of required answer values (positive integer = answer length; observed range 1–42, private max 18, public max 42). *Derived* from the answer.
- `is_matharena` — (private only) 1 if the item came from the MathArena benchmark (50 items), else 0.
- `answer` — the official answer: a **string** for single-value items, a **list of strings**
  for multi-value items.

**Type distribution.** Private: MCQ 300 · FREE_SINGLE 305 · FREE_MULTI 338. Public: MCQ 375 ·
FREE_SINGLE 337 · FREE_MULTI 414. (Note: there are **no** multi-select MCQs — MCQ is always
single-letter.)

## Collection process

- **Private questions** ← Kaggle test file `private.jsonl` (943, no labels released during the
  competition).
- **Private answers** ← the **official Kaggle grading solution sheet** (the file used to score
  the leaderboard), obtained post-competition. All 943 are solved.
- **Public set** ← the Kaggle public/labeled file `public.jsonl` (1126, question + answer +
  options-for-MCQ, self-contained).
- The originals are copied verbatim into `_original/`.

## Preprocessing / cleaning / labeling

- Joined questions and answers by `id`.
- **Answer normalization:** source answers were parsed from their literal form (private used
  JSON-style lists, public used Python-style lists) into a consistent representation — a bare
  string for single answers, a list for multi. Values are **not** altered, only re-serialized.
- **Derived** `question_type` (options present → MCQ; else FREE_SINGLE/FREE_MULTI by answer
  count) and `n_ans_slots` (answer list length).
- **Dropped the `Usage` / leaderboard-split column** deliberately — we do not track which test
  items were public-LB vs private-LB. ("public"/"private" here refer only to the two Kaggle
  *files*, not a leaderboard subset.)
- Immutable originals preserved in `_original/` for any unanticipated future use.

## Uses

- **Intended:** ground truth for the sample-level SC analysis (grade `samples` against
  `private_answers`), question-type-stratified analysis, the eval/forensics build.
- **Critical provenance fact:** *every inference run we have was against the **private** set
  (943).* The **public** set has **no** inference — it is a labeled reference set only. Do not
  assume any sample data exists for public items.
- **Not for:** representing a *live* leaderboard score. The competition is over; this is
  retrospective analysis. Official final score was 0.428 (selected picks); best submission
  0.684 — both reported honestly in the final report.

## Distribution

- Housed in **two** repos: built and version-controlled here in
  `151B_SP26_Competition/data/raw/`, and transferred to
  **`github.com/raindonovan/summer_research`** as the research home.
- Plain JSONL; load with `json.loads` per line or `pandas.read_json(path, lines=True)`.

## Limitations

- **No coverage limitation** — every private (943) and public (1126) item has an official answer.
- `question_type` / `n_ans_slots` are *derived* heuristics (from options + answer shape), not
  an official field; re-derive if you disagree with the rule.
- `is_matharena` exists only for the private set (it is a column of the private solution sheet).
- **Public and private are not fully content-disjoint.** At least one item appears in both
  (private id 784 == public id 117 — identical question and answer `17/60`), inherited from
  the Kaggle source pools. Do not assume the two sets share no items (relevant if public is
  used to tune/validate something later measured on private).

*Audited 2026-06-28 (Codex, `findings/data_raw_audit.md`): build verified faithful to source
on counts, joins, answer fidelity, types, options, `is_matharena`, encoding; the two items
above were its findings.*

## Maintenance

- Versioned by `schema_version` / `dataset_version` above. Changes are made here first, then
  re-transferred to `summer_research`. The `_original/` files never change.
