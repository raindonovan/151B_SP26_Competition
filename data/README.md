# Data — bird's-eye view

Everything here comes from the **CSE 151B SP26** Kaggle math-reasoning competition
(frozen base model **`Qwen/Qwen3-4B-Thinking-2507`**). Two cornerstone datasets, built and
audited, that together support the summer-research question:

> *When self-consistency votes, how often was a correct answer sitting in one of the samples
> but got outvoted?* (re-extract → re-vote → grade vs. truth.)

## The two datasets at a glance

| | `data/raw/` | `data/samples/` |
|---|---|---|
| **What** | The questions + their official answers | Every raw model sample we generated |
| **Grain** | one row per question | one row per individual SC sample |
| **Size** | public 1,126 + private 943 | 32,646 samples across 14 runs |
| **Format** | JSONL (small, in git) | Parquet 134 MB (LFS) + JSONL export |
| **Role** | ground truth / labels | the thing being analyzed |
| **Audited** | ✓ (issue #1) | ✓ (issue #3, full raw-text scan) |

They join on one key: **`samples.item_id` → `data/raw/private_answers.id`**.

---

## 1. `data/raw/` — questions & answers

The competition shipped two sets. **"public" and "private" are the two Kaggle files** — *not* a
leaderboard split (we dropped that).

| set | items | what it is | MCQ / FREE_SINGLE / FREE_MULTI |
|---|---|---|---|
| **private** | 943 | the **held-out test set** (every inference run targets this) | 300 / 305 / 338 |
| **public** | 1,126 | a separate **labeled reference set** (no inference run on it) | 375 / 337 / 414 |

- **Question types** (derived): `MCQ` (has options, answer is a letter), `FREE_SINGLE` (one value),
  `FREE_MULTI` (≥2 values). `n_ans_slots` = number of required values (private 1–18, public up to 42).
- **Files per set**: `*_questions.jsonl` (inputs), `*_answers.jsonl` (labels), `*_all.jsonl` (joined).
  `_original/` keeps the verbatim Kaggle files. `is_matharena` flags 50 private items from MathArena.
- **Heads-up**: public and private are **not** fully disjoint — `private 784` == `public 117`
  (same question + answer `17/60`).

## 2. `data/samples/` — self-consistency inference samples (base model)

Every raw response the base model produced, one per row, **untouched** (no extracted/voted answer
stored — that's the whole point: re-extract cleanly).

- **Coverage**: all **943** private items have ≥1 sample.
- **Sample depth varies** (full-943 only at low SC; deep SC only on hard-item subsets):
  - SC@1: 1,886 · **SC@8: 23,416** · SC@16: 7,344
- **Mode**: thinking 23,342 · nothinking 9,304 (NoThinking = closed-`<think>` prefill).
- **Truncation**: 1,139 samples hit the token cap (`finish_reason = length`); 14,733 clean `stop`;
  16,774 unrecorded.
- **14 runs**, e.g. the full-943 SC@8 runs (`R09` 16k, `R20` 32k, `NT` nothinking), single-sample
  baselines (`R08`, `R10`), and SC@16 hard-item probes (`TH_tr`, `NT_tr`, `kitchensink`, …). The
  `runs.parquet` manifest documents each (model, prompt, budget, coverage, provenance).
- **Columns**: `sample_uid, run_id, item_id, sample_index, sc_n, think_mode, model_variant,
  response, gen_tokens, finish_reason, temperature`.
- **Clean**: 3 duplicate/derived runs were removed; an exhaustive raw-text audit found only ~9
  cosmetic encoding artifacts in *reasoning* (never in a `\boxed{}` answer), left raw.

---

## How to use it

```python
import pyarrow.parquet as pq, json
samples = pq.read_table("data/samples/samples.parquet").to_pandas()
answers = {json.loads(l)["id"]: json.loads(l)["answer"]
           for l in open("data/raw/private_answers.jsonl")}
# samples["item_id"].map(answers)  ->  truth per sample, ready to re-grade
```

## Status & where to dig deeper

- Both datasets are **built, convention-compliant, independently audited (Codex), and version-pinned.**
- Per-dataset detail: `data/raw/DATASHEET.md` and `data/samples/DATASHEET.md`.
- Audit reports: `findings/data_raw_audit.md`, `findings/data_samples_audit.md`.
- Upstream provenance (original run files) lives in the competition repo
  `raindonovan/151B_SP26_Competition`; the parquet here is the preserved source of truth.
