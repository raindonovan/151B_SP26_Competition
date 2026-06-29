#!/usr/bin/env python3
"""
make_preview.py — regenerate data/PREVIEW.md + data/preview/*.png

A *visual* eyeball of both datasets, following the Hugging Face dataset-card
convention (Data Fields = a data dictionary; Data Instances = real rendered
sample rows) plus distribution charts. Static markdown + small PNGs so it
renders on GitHub and stays diffable in git (no heavy interactive HTML report).

Run from the repo root:  python3 data/make_preview.py
Outputs:  data/PREVIEW.md  and  data/preview/*.png
"""
import json, os, textwrap, html
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
SAMP = os.path.join(HERE, "samples")
PREVIEW_DIR = os.path.join(HERE, "preview")
os.makedirs(PREVIEW_DIR, exist_ok=True)

INK = "#2b2b2b"
ACCENT = "#3b6ea5"      # private / primary
ACCENT2 = "#c2693a"     # public / secondary
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 110, "font.size": 9,
    "axes.edgecolor": "#999", "axes.linewidth": 0.8, "axes.grid": True,
    "grid.color": "#e6e6e6", "grid.linewidth": 0.7, "axes.axisbelow": True,
    "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
})


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def mdbar(count, maxc, width=22):
    n = int(round(width * count / maxc)) if maxc else 0
    return "█" * n + "▁" * (width - n)


def dist_table(title, counts, total):
    """counts: list of (label, n) -> markdown table with bar + pct."""
    maxc = max((n for _, n in counts), default=0)
    rows = [f"| {title} | count | % | |", "|---|---:|---:|:--|"]
    for label, n in counts:
        rows.append(f"| {label} | {n:,} | {100*n/total:.1f}% | `{mdbar(n, maxc)}` |")
    return "\n".join(rows)


def fence(text, lang=""):
    return f"```{lang}\n{text}\n```"


def trunc(s, n):
    s = s if isinstance(s, str) else str(s)
    return s if len(s) <= n else s[:n].rstrip() + " …"


def head_tail(s, head=560, tail=220):
    s = s if isinstance(s, str) else str(s)
    if len(s) <= head + tail + 40:
        return s
    return s[:head].rstrip() + f"\n\n   […  {len(s) - head - tail:,} chars elided  …]\n\n" + s[-tail:].lstrip()


# ----------------------------------------------------------------------------
# 1. data/raw  —  questions & answers
# ----------------------------------------------------------------------------
priv = load_jsonl(os.path.join(RAW, "private_all.jsonl"))
pub = load_jsonl(os.path.join(RAW, "public_all.jsonl"))


def qtype_counts(rows):
    from collections import Counter
    c = Counter(r["question_type"] for r in rows)
    return [(t, c.get(t, 0)) for t in ["MCQ", "FREE_SINGLE", "FREE_MULTI"]]


def slot_series(rows):
    return pd.Series([r["n_ans_slots"] for r in rows])


# --- chart: question-type, private vs public (grouped bar) ---
def chart_qtypes():
    types = ["MCQ", "FREE_SINGLE", "FREE_MULTI"]
    pv = dict(qtype_counts(priv)); pb = dict(qtype_counts(pub))
    x = range(len(types)); w = 0.4
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    ax.bar([i - w/2 for i in x], [pv[t] for t in types], w, label=f"private ({len(priv)})", color=ACCENT)
    ax.bar([i + w/2 for i in x], [pb[t] for t in types], w, label=f"public ({len(pub)})", color=ACCENT2)
    for i in x:
        ax.text(i - w/2, pv[types[i]] + 4, pv[types[i]], ha="center", va="bottom", fontsize=8)
        ax.text(i + w/2, pb[types[i]] + 4, pb[types[i]], ha="center", va="bottom", fontsize=8)
    ax.set_xticks(list(x)); ax.set_xticklabels(types)
    ax.set_ylabel("items"); ax.set_title("Question types"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(PREVIEW_DIR, "raw_question_types.png")); plt.close(fig)


# --- chart: answer-slot count distribution ---
def chart_slots():
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    for rows, color, lab in [(priv, ACCENT, "private"), (pub, ACCENT2, "public")]:
        s = slot_series(rows).clip(upper=12)
        vc = s.value_counts().sort_index()
        ax.plot(vc.index, vc.values, marker="o", ms=4, color=color, label=lab)
    ax.set_xlabel("answer slots  (n_ans_slots, capped at 12)")
    ax.set_ylabel("items"); ax.set_yscale("log")
    ax.set_title("How many values each answer needs"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(PREVIEW_DIR, "raw_answer_slots.png")); plt.close(fig)


chart_qtypes(); chart_slots()


def example_card(rows, qtype):
    r = next(r for r in rows if r["question_type"] == qtype)
    opts = r.get("options") or []
    lines = [f"item id **{r['id']}**  ·  `{r['question_type']}`  ·  n_ans_slots = {r['n_ans_slots']}", ""]
    lines.append("**Q:** " + trunc(r["question"].replace("\n", " "), 420))
    if opts:
        lines.append("")
        lines.append("**options:** " + "  ".join(f"`{o}`" for o in opts))
    ans = r["answer"]
    ans_s = ", ".join(map(str, ans)) if isinstance(ans, list) else str(ans)
    lines.append("")
    lines.append(f"**answer:** `{ans_s}`" + ("  *(list)*" if isinstance(ans, list) else "  *(scalar)*"))
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# 2. data/samples  —  SC inference samples
# ----------------------------------------------------------------------------
S = pd.read_parquet(os.path.join(SAMP, "samples.parquet"))
RUNS = pd.read_parquet(os.path.join(SAMP, "runs.parquet"))
S["resp_len"] = S["response"].str.len()
depth = S.groupby("item_id").size()


def vc_list(col, order=None):
    vc = S[col].value_counts(dropna=False)
    if order:
        return [(str(k), int(vc.get(k, 0))) for k in order]
    return [("null" if pd.isna(k) else str(k), int(v)) for k, v in vc.items()]


def chart_samples_cat():
    fig, axes = plt.subplots(1, 3, figsize=(8.6, 2.8))
    specs = [
        ("sc_n", [1, 8, 16], ACCENT, "SC depth (sc_n)"),
        ("think_mode", None, ACCENT2, "think mode"),
        ("finish_reason", None, "#5a8a5a", "finish_reason"),
    ]
    for ax, (col, order, color, title) in zip(axes, specs):
        vc = S[col].value_counts(dropna=False)
        if order:
            vc = vc.reindex(order).fillna(0)
        labels = ["null" if (isinstance(k, float) and pd.isna(k)) else str(k) for k in vc.index]
        ax.bar(labels, vc.values, color=color)
        ax.set_title(title); ax.tick_params(axis="x", rotation=0)
        for i, v in enumerate(vc.values):
            ax.text(i, v, f"{int(v):,}", ha="center", va="bottom", fontsize=7)
        ax.margins(y=0.18)
    fig.suptitle("Sample distributions", y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(PREVIEW_DIR, "samples_categorical.png"), bbox_inches="tight"); plt.close(fig)


def chart_resp_len():
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    kchars = (S["resp_len"] / 1000).clip(upper=60)
    ax.hist(kchars, bins=40, color=ACCENT, alpha=0.85)
    med = S["resp_len"].median() / 1000
    ax.axvline(med, color=ACCENT2, ls="--", lw=1.2, label=f"median {med:.1f}k")
    ax.set_xlabel("response length (thousands of chars, capped 60k)")
    ax.set_ylabel("samples"); ax.set_title("Raw response length"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(PREVIEW_DIR, "samples_response_length.png")); plt.close(fig)


def chart_depth():
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    ax.hist(depth.clip(upper=40), bins=40, color="#5a8a5a", alpha=0.85)
    ax.set_xlabel("samples per item (capped 40)")
    ax.set_ylabel("items (of 943)")
    ax.set_title("Per-item sample depth")
    fig.tight_layout(); fig.savefig(os.path.join(PREVIEW_DIR, "samples_depth.png")); plt.close(fig)


def chart_runs():
    r = S.groupby("run_id").size().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.barh(range(len(r)), r.values, color=ACCENT)
    ax.set_yticks(range(len(r))); ax.set_yticklabels(r.index, fontsize=7)
    for i, v in enumerate(r.values):
        ax.text(v, i, f" {v:,}", va="center", fontsize=7)
    ax.set_xlabel("samples"); ax.set_title("Samples per run (14 runs)")
    fig.tight_layout(); fig.savefig(os.path.join(PREVIEW_DIR, "samples_per_run.png")); plt.close(fig)


chart_samples_cat(); chart_resp_len(); chart_depth(); chart_runs()


def sample_card(row):
    meta = (f"`{row['run_id']}`  ·  item **{row['item_id']}**  ·  sample {row['sample_index']}  ·  "
            f"sc_n={row['sc_n']}  ·  {row['think_mode']}  ·  finish={row['finish_reason']}  ·  "
            f"{int(row['resp_len']):,} chars")
    return meta, head_tail(row["response"])


# pick one thinking + one nothinking example (short-ish, clean stop)
def pick(mode):
    sub = S[(S["think_mode"] == mode) & (S["finish_reason"] == "stop")]
    if sub.empty:
        sub = S[S["think_mode"] == mode]
    sub = sub[sub["resp_len"].between(1500, 6000)]
    return (sub.iloc[0] if not sub.empty else S[S["think_mode"] == mode].iloc[0])


ex_think = pick("thinking")
ex_noth = pick("nothinking")


# ---- runs bird's-eye: inventory table + cross-tab matrices ----
def _cell(v, dash="—"):
    if v is None:
        return dash
    s = str(v)
    return dash if s in ("", "None", "nan", "NaT") else s


def fmt_budget(v):
    return "—" if pd.isna(v) else f"{int(v/1024)}k"


def runs_inventory_md():
    r = RUNS.copy()
    r["full"] = r["n_items"] == 943
    r = r.sort_values(["full", "sc_n", "n_items"], ascending=[False, True, False])
    out = ["| run_id | SC | mode | budget | coverage | samples | date | prompt | what it is |",
           "|---|--:|---|--:|---|--:|---|---|---|"]
    for _, x in r.iterrows():
        cov = "**943** · full" if x["full"] else f"{int(x['n_items'])} · subset"
        date = _cell(str(x.get("date"))[:10] if _cell(x.get("date")) != "—" else None)
        out.append(
            f"| `{x['run_id']}` | {int(x['sc_n'])} | {x['think_mode']} | {fmt_budget(x['token_budget'])} | "
            f"{cov} | {int(x['n_samples']):,} | {date} | {_cell(x.get('prompt_version'))} | "
            f"{trunc(_cell(x.get('notes'), ''), 44)} |")
    return "\n".join(out)


def coverage_matrix_md():
    r = RUNS.copy()
    r["full"] = r["n_items"] == 943
    items_at = S.groupby("sc_n")["item_id"].nunique().to_dict()
    rows = ["| SC depth | full-943 runs | hard-subset runs | distinct items w/ ≥1 sample |",
            "|---|---|---|---:|"]
    for sc in [1, 8, 16]:
        full = r[(r.sc_n == sc) & r.full]["run_id"].tolist()
        sub = r[(r.sc_n == sc) & ~r.full]
        full_s = ", ".join(f"`{x}`" for x in full) if full else "—"
        if len(sub):
            lo, hi = int(sub.n_items.min()), int(sub.n_items.max())
            rng = f"{lo}" if lo == hi else f"{lo}–{hi}"
            sub_s = (f"`{sub.iloc[0]['run_id']}` ({int(sub.iloc[0]['n_items'])} items)"
                     if len(sub) == 1 else f"{len(sub)} runs ({rng} items each)")
        else:
            sub_s = "—"
        rows.append(f"| **SC@{sc}** | {full_s} | {sub_s} | {items_at.get(sc, 0)} |")
    return "\n".join(rows)


def mode_depth_matrix_md():
    ct = pd.crosstab(S["think_mode"], S["sc_n"], margins=True, margins_name="all")
    cols = [c for c in ct.columns]
    head = "| samples | " + " | ".join(f"SC@{c}" if c != "all" else "**all**" for c in cols) + " |"
    sep = "|---|" + "|".join(["--:"] * len(cols)) + "|"
    rows = [head, sep]
    for idx in ct.index:
        label = f"**{idx}**" if idx == "all" else idx
        rows.append("| " + label + " | " + " | ".join(f"{int(ct.loc[idx, c]):,}" for c in cols) + " |")
    return "\n".join(rows)

# ----------------------------------------------------------------------------
# assemble PREVIEW.md
# ----------------------------------------------------------------------------
priv_qt, pub_qt = qtype_counts(priv), qtype_counts(pub)
ps, pbs = slot_series(priv), slot_series(pub)

doc = []
A = doc.append
A("# Data — visual preview\n")
A("> A look-at-it companion to [`README.md`](README.md) (the prose overview) and the two "
  "`DATASHEET.md` files (the formal spec). Sample rows, field dictionaries, and distribution "
  "charts so you can eyeball both datasets in a minute. **Regenerate:** "
  "`python3 data/make_preview.py`.\n")

# ---- raw ----
A("---\n\n## 1. `data/raw/` — questions & answers\n")
A(f"**{len(priv):,} private** (the held-out test set) + **{len(pub):,} public** (labeled reference). "
  "One row per question.\n")

A("### Data fields\n")
A("| field | type | example | notes |")
A("|---|---|---|---|")
A("| `id` | int | `784` | unique within a set (private 0–942, public 0–1125) |")
A("| `question` | str | *\"A company's stock…\"* | problem text, verbatim |")
A("| `options` | list[str] | `[\"A) 12\", \"B) 15\", …]` | MCQ choices; `[]` for free-form |")
A("| `question_type` | str | `MCQ` | `MCQ` / `FREE_SINGLE` / `FREE_MULTI` (derived) |")
A("| `n_ans_slots` | int | `2` | number of required values (derived) |")
A("| `is_matharena` | int | `0` | private only: 1 if from MathArena (50 items) |")
A("| `answer` | str \\| list[str] | `[\"4\", \"16\"]` | scalar for single, list for multi |\n")

A("### Data instances — one of each question type (private)\n")
for qt in ["MCQ", "FREE_SINGLE", "FREE_MULTI"]:
    A(f"<small>**{qt}**</small>\n")
    A("> " + example_card(priv, qt).replace("\n", "\n> ") + "\n")

A("### Distributions\n")
A(f"![question types](preview/raw_question_types.png) ![answer slots](preview/raw_answer_slots.png)\n")
A(dist_table("question_type (private)", priv_qt, len(priv)) + "\n")
A(dist_table("question_type (public)", pub_qt, len(pub)) + "\n")
A(f"**n_ans_slots** — private: min {ps.min()}, median {int(ps.median())}, max {ps.max()}  ·  "
  f"public: min {pbs.min()}, median {int(pbs.median())}, max {pbs.max()}. "
  f"Most items need 1 value; a long tail needs many (private up to {ps.max()}, public up to {pbs.max()}).\n")

# ---- samples ----
A("---\n\n## 2. `data/samples/` — self-consistency inference samples\n")
A(f"**{len(S):,} samples** across **{S['run_id'].nunique()} runs**, one row per raw model sample "
  f"(base `Qwen3-4B-Thinking-2507`, private set). All **943** items covered. "
  "The `response` text is stored **raw** — no extracted/voted answer (that's the research point).\n")

A("### Runs at a glance — the inventory\n")
A("One row per run; this is the metadata bird's-eye. `coverage` = how many of the 943 items the "
  "run targeted (full-943 vs a hard-item subset); `SC` = self-consistency depth.\n")
A(runs_inventory_md() + "\n")
A("**Coverage × SC depth** — *where* each depth exists. The structural fact for the research: "
  "full-943 coverage exists only at SC@1 and SC@8; **every SC@16 run is a hard-item subset**, so "
  "per-item depth is uneven (reconstruct it from `run_id` + `sc_n`).\n")
A(coverage_matrix_md() + "\n")
A("**Samples by mode × SC depth** — the 32,646 samples cross-tabulated.\n")
A(mode_depth_matrix_md() + "\n")
A("![samples per run](preview/samples_per_run.png)\n")

A("### Data fields\n")
A("| field | type | example | notes |")
A("|---|---|---|---|")
A("| `sample_uid` | str | `R20_sc8_p943_t32k:600:3` | `run_id:item_id:sample_index` (primary key) |")
A("| `run_id` | str | `R20_sc8_p943_t32k` | which inference run |")
A("| `item_id` | int | `600` | joins to `raw/private_answers.id` |")
A("| `sample_index` | int | `3` | which sample within (item, run) |")
A("| `sc_n` | int | `8` | self-consistency depth of the run (1 / 8 / 16) |")
A("| `think_mode` | str | `thinking` | `thinking` or `nothinking` (closed-`<think>` prefill) |")
A("| `model_variant` | str | `base` | base model (adapter/sft extend later) |")
A("| `response` | str | *(long)* | the raw generation, untouched |")
A("| `gen_tokens` | int | `4173` | generated token count (null where unrecorded) |")
A("| `finish_reason` | str | `stop` | `stop` / `length` (truncated) / null |")
A("| `temperature` | float | `0.6` | sampling temperature |")
A("| `has_box` | bool | `true` | grader can extract a `\\boxed{}` answer (derived) |")
A("| `box_status` | str | `boxed` | `boxed` / `cut` (no box, ran out of tokens) / `no_emit` (no box, finished) |")
A("| `box_status_inferred` | bool | `false` | `cut`/`no_emit` inferred (run didn't log `finish_reason`) |\n")

A("### Data instances — two real samples (head + tail)\n")
for ex in (ex_think, ex_noth):
    meta, body = sample_card(ex)
    A(meta + "\n")
    A(fence(body) + "\n")

A("### Distributions\n")
A("![sample categorical distributions](preview/samples_categorical.png)\n")
A("![response length](preview/samples_response_length.png) ![per-item depth](preview/samples_depth.png)\n")
A(dist_table("sc_n", vc_list("sc_n", order=[1, 8, 16]), len(S)) + "\n")
A(dist_table("think_mode", vc_list("think_mode"), len(S)) + "\n")
A(dist_table("finish_reason", vc_list("finish_reason"), len(S)) + "\n")
A(f"**response length** (chars): min {int(S.resp_len.min()):,} · median {int(S.resp_len.median()):,} · "
  f"max {int(S.resp_len.max()):,}.  **per-item depth:** min {int(depth.min())} · "
  f"median {int(depth.median())} · max {int(depth.max())} samples/item.\n")

# ---- no-box breakdown (box_status) ----
A("### Answer status — boxed vs cut vs no-emit\n")
nbx = S[~S["has_box"]]
ncut = int((S["box_status"] == "cut").sum()); nemit = int((S["box_status"] == "no_emit").sum())
A(f"**{int(S['has_box'].sum()):,}** of {len(S):,} samples carry a grader-extractable `\\boxed{{}}` "
  f"answer; **{len(nbx):,}** do not. A no-box sample casts a *null vote* in self-consistency — and the "
  f"split below says how recoverable that is. `finish_reason` describes the *generation* (a truncated "
  f"sample can still be boxed: {int(((S.finish_reason=='length')&S.has_box).sum())} are), so `box_status` "
  f"is a separate, answer-level column.\n")
A(dist_table("box_status", [("boxed", int((S.box_status=='boxed').sum())), ("cut", ncut), ("no_emit", nemit)], len(S)) + "\n")
A(f"So of the {len(nbx):,} no-box samples, **{ncut:,} ({100*ncut/len(nbx):.0f}%) were `cut`** — reasoning "
  f"ran out of tokens before boxing (recoverable with a bigger budget) — and **{nemit:,} "
  f"({100*nemit/len(nbx):.0f}%) `no_emit`** — finished but never boxed. "
  f"{int(nbx['box_status_inferred'].sum()):,} of the labels are inferred (`box_status_inferred`; "
  f"runs that didn't log `finish_reason`).\n")
# per-run table — cut rate is very run-dependent
_pr = (S.assign(nobox=~S.has_box)
         .groupby("run_id")
         .agg(samples=("has_box", "size"),
              nobox=("nobox", "sum"),
              cut=("box_status", lambda s: (s == "cut").sum()),
              no_emit=("box_status", lambda s: (s == "no_emit").sum()))
         .sort_values("nobox", ascending=False))
A("**No-box by run** (where the misses concentrate — the 8k-budget NoThinking run dominates):\n")
_rows = ["| run_id | samples | no-box | cut | no_emit | no-box % |", "|---|--:|--:|--:|--:|--:|"]
for rid, x in _pr[_pr["nobox"] > 0].iterrows():
    _rows.append(f"| `{rid}` | {int(x.samples):,} | {int(x.nobox):,} | {int(x.cut):,} | "
                 f"{int(x.no_emit):,} | {100*x.nobox/x.samples:.1f}% |")
A("\n".join(_rows) + "\n")

A("---\n")
A("*Generated by [`make_preview.py`](make_preview.py). Charts in [`preview/`](preview/). "
  "For the formal record see `raw/DATASHEET.md` and `samples/DATASHEET.md`.*\n")

with open(os.path.join(HERE, "PREVIEW.md"), "w") as f:
    f.write("\n".join(doc))

print("wrote data/PREVIEW.md")
print("charts:", sorted(os.listdir(PREVIEW_DIR)))
