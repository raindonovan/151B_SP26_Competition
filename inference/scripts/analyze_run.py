"""analyze_run.py — per-run inference analyzer (ANALYSIS_SCHEMA.md, locked).

Builds the 3 schema artifacts for ONE inference run:
  analysis.csv            — 943 rows + run-meta comment header
  analysis.jsonl          — 943 rows, full_response + full_reasoning_trace + all_boxed_extracted
  analysis_samples.jsonl  — SC runs only, n_samples × 943 rows

RE-USE (do not rewrite the grader/normalizer):
  - grading.grader.Grader  (== root judger.Judger, value-equality engine):
      .extract_boxed_answer(resp)  → the grader's last-contiguous-box view (extracted_answer)
      .extract_all_boxed(resp)     → list of all boxed contents (all_boxed_extracted)
      .auto_judge(pred, gold_list, options_list) → math-correct (numeric/symbolic tol)
      .split_by_comma(s)           → split gold/answer into slots
  - postprocessing.scripts.apply_grader_normalization.find_last_box / normalize_row
      (minimal cosmetic mode) — for the format-fix probe used in format_correct.

Gold + tier come from data/MASTER_ANSWERS.csv (surrogate-gold hierarchy, schema §
"Salvaged design ideas"). MCQ options come from the run jsonl. private.jsonl (root)
carries only id+question and is accepted but not required for metadata.

CPU-only. No GPU, no model load.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
import sys
from collections import Counter

# repo root on path so `grading` and root `judger` import cleanly regardless of cwd
_THIS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_THIS, "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from grading.grader import Grader  # value-equality engine (canonical)
# NOTE (C5): apply_grader_normalization is cosmetic-only (no structural fix), so it is
# no longer used for format_correct — format_correct == math_correct under current
# capability. Re-import a structural normalizer here when one becomes reusable.

# ── Gold / tier derivation (surrogate hierarchy, schema §"Salvaged design ideas") ──
# MASTER_ANSWERS columns:
#   item_id, category, question_preview, sheet_best_answer, sheet_confidence,
#   sheet_tier, sheet_n_agree, sheet_evidence, teacher_sonnet, teacher_gpt4,
#   teacher_oss, wolfram_answer, wolfram_confidence, search_status, search_answer,
#   search_source, backsolve_answer, backsolve_confidence, backsolve_tier
#
# Priority (highest → lowest), per ANALYSIS_SCHEMA gold_source hierarchy:
#   Wolfram_HIGH > unanimous_teachers > answer_sheet_HIGH > backsolve_HIGH > sheet_fallback


def _norm(s):
    return (s or "").strip()


def derive_gold(row: dict) -> tuple[str, str, bool, str]:
    """Return (gold_answer, gold_source, gold_independent_flag, conflict_note).

    LEAKAGE-PROOF (C1): independence is computed from RAW MASTER_ANSWERS columns
    ONLY — wolfram_confidence, search_status, and the three-way raw teacher
    equality. ZERO reads of sheet_n_agree / sheet_evidence / sheet_confidence /
    any precomputed gold_source. The fused sheet_best_answer is contaminated
    (built partly from the runs we audit), so it is used for DISPLAY ONLY on
    non-independent rows.

    gold_source precedence (C7), strict order:
      wolfram_HIGH > unanimous_teachers > search_GOLD > sheet_dependent
    gold_answer is taken from the WINNING source. On value conflict between
    signals, the higher-precedence source wins and a conflict note is recorded.
    """
    sheet = _norm(row.get("sheet_best_answer"))
    wolf = _norm(row.get("wolfram_answer"))
    search_ans = _norm(row.get("search_answer"))
    t_sonnet = _norm(row.get("teacher_sonnet"))
    t_gpt4 = _norm(row.get("teacher_gpt4"))
    t_oss = _norm(row.get("teacher_oss"))

    # --- raw independence signals (C1) ---
    is_wolfram_HIGH = (_norm(row.get("wolfram_confidence")) == "HIGH")
    is_search_GOLD = (_norm(row.get("search_status")) == "GOLD")
    is_unanimous_teachers = (
        t_sonnet != "" and t_gpt4 != "" and t_oss != ""
        and t_sonnet == t_gpt4 and t_gpt4 == t_oss
    )
    gold_independent_flag = is_wolfram_HIGH or is_search_GOLD or is_unanimous_teachers

    # --- conflict detection (C7, informational) ---
    conflict_note = ""
    independent_vals = []
    if is_wolfram_HIGH:
        independent_vals.append(wolf)
    if is_unanimous_teachers:
        independent_vals.append(t_sonnet)
    if is_search_GOLD:
        independent_vals.append(search_ans)
    if len({v for v in independent_vals if v}) > 1:
        conflict_note = f"gold_conflict: wolfram={wolf}, teachers={t_sonnet}; "

    # --- precedence assignment (C7) ---
    if is_wolfram_HIGH:
        return (wolf, "wolfram_HIGH", True, conflict_note)
    if is_unanimous_teachers:
        return (t_sonnet, "unanimous_teachers", True, conflict_note)
    if is_search_GOLD:
        return (search_ans, "search_GOLD", True, conflict_note)
    return (sheet, "sheet_dependent", False, conflict_note)  # display-only value


def tier_int(row: dict) -> int:
    try:
        return int(_norm(row.get("sheet_tier")) or 0)
    except ValueError:
        return 0


# ── Run-level metadata ─────────────────────────────────────────────────────────
def build_run_meta(first_row: dict, run_id: str | None, kaggle_score, input_path, n_items, is_sc, n_samples):
    return {
        "run_id": run_id or first_row.get("run_id") or os.path.basename(input_path),
        "model": first_row.get("model"),
        "method": first_row.get("method"),
        "n_samples": n_samples,
        "max_new_tokens": first_row.get("max_new_tokens"),
        "temperature": first_row.get("temperature"),
        "n_items": n_items,
        "date_run": _dt.date.today().isoformat(),
        "kaggle_score": kaggle_score,
        "input_jsonl_path": input_path,
        "is_self_consistency": is_sc,
    }


# ── Per-item analysis ───────────────────────────────────────────────────────────
ANALYSIS_COLS = [
    "item_id", "category", "tier", "gold_answer", "gold_source",
    "gold_independent_flag", "gold_uncertain_flag",
    "extracted_answer", "extracted_empty_flag", "truncated_flag",
    "format_correct", "format_check_capability", "math_correct",
    "format_failure_subtype", "bucket", "bucket_b_review_needed",
    "n_tokens_total", "n_tokens_thinking",
    "sc_vote_size", "sc_total_samples",
    "response_preview", "notes",
]

SAMPLE_COLS = [
    "item_id", "sample_index", "sample_extracted", "sample_correct",
    "sample_truncated", "sample_temperature", "sample_top_p", "sample_seed",
    "sample_n_tokens",
]


def split_response_think(resp: str) -> tuple[str, str]:
    """(thinking_trace, final_answer_text). </think> is the boundary."""
    if not isinstance(resp, str):
        return "", ""
    idx = resp.rfind("</think>")
    if idx < 0:
        return "", resp
    return resp[:idx], resp[idx + len("</think>"):]


def n_thinking_tokens_estimate(thinking: str) -> int:
    """Cheap whitespace token estimate for the thinking portion (no tokenizer load)."""
    return len(thinking.split()) if thinking else 0


def gold_list_for(gold_answer: str, grader: Grader) -> list[str]:
    if not gold_answer:
        return []
    return [s for s in grader.split_by_comma(gold_answer)]


def judge_math(grader: Grader, full_response: str, gold_answer: str, options, fail_fast: bool = False) -> bool:
    """math_correct via auto_judge. gold split to slots; options list matched in length."""
    gold_slots = gold_list_for(gold_answer, grader)
    if not gold_slots:
        return False
    opts = options if isinstance(options, list) else None
    # auto_judge zips gold with options; supply a same-length options list (None per slot
    # unless real MCQ options exist and gold is single-slot).
    if opts and len(gold_slots) == 1:
        opt_list = [opts]
    else:
        opt_list = [None] * len(gold_slots)
    try:
        return bool(grader.auto_judge(full_response, gold_slots, opt_list))
    except Exception:
        if fail_fast:  # C14
            raise
        return False


def format_correct_probe(grader: Grader, full_response: str, gold_answer: str, options, math_ok: bool) -> bool:
    """format_correct (C5 INTERIM POLICY): currently equals math_correct.

    apply_grader_normalization.py is cosmetic-only (dfrac_only / minimal modes —
    thin-space + \\left/\\right strip, no structural fix). The structural
    normalizer (undercount collapse / multi-answer order / MCQ first-box) does
    NOT live in a reusable module yet, so we cannot recover format-only items
    here. format_correct == math_correct is therefore CORRECT under current
    capability, not a bug. Re-enable a real format check when postprocessing
    extracts a reusable structural module. (format_check_capability column
    records this; format_failure_subtype stays deferred/empty.)
    """
    return math_ok


def analyze(args):
    grader = Grader()

    # Load MASTER_ANSWERS keyed by int item_id
    master = {}
    with open(args.master_answers, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                master[int(row["item_id"])] = row
            except (KeyError, ValueError):
                continue

    # Load run jsonl
    run_rows = []
    with open(args.run_jsonl, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                run_rows.append(json.loads(line))
    if not run_rows:
        print("FAIL: run jsonl is empty", file=sys.stderr)
        sys.exit(1)

    first = run_rows[0]
    is_sc = isinstance(first.get("samples"), list) and len(first.get("samples")) > 0
    n_samples = len(first.get("samples", [])) if is_sc else 1
    run_meta = build_run_meta(first, args.run_id, args.kaggle_score, args.run_jsonl, len(run_rows), is_sc, n_samples)

    os.makedirs(args.output_dir, exist_ok=True)
    analysis_rows = []
    jsonl_rows = []
    sample_rows = []

    for r in run_rows:
        iid = r["id"]
        m = master.get(iid, {})
        category = _norm(m.get("category")) or ("MCQ" if r.get("is_mcq") else "FREE")
        tier = tier_int(m)
        if m:
            gold_answer, gold_source, gold_independent, conflict_note = derive_gold(m)
        else:
            gold_answer, gold_source, gold_independent, conflict_note = ("", "sheet_dependent", False, "")
        gold_uncertain = tier in (4, 5)
        options = r.get("options")  # list or None
        notes = conflict_note  # C7/C12: notes accumulate (gold_conflict + canonical_sample_fallback)

        # voted / single response
        if is_sc:
            voted = r.get("voted_answer", "")
            samples = r.get("samples", [])
            # C11: deterministic canonical sample — among samples whose extracted matches the
            # voted answer, pick min (gen_tokens, sample_index): shortest correct response
            # (best preview), sample_index breaks ties. Fully sample-order-independent.
            matching = [(i, s) for i, s in enumerate(samples)
                        if _norm(s.get("extracted_answer")) == _norm(voted)]
            if matching:
                chosen_sample = min(matching, key=lambda iv: (iv[1].get("gen_tokens", 0), iv[0]))[1]
            else:
                chosen_sample = samples[0] if samples else {}
                notes += "canonical_sample_fallback; "  # C12
            full_response = chosen_sample.get("response", "")
            max_tok = r.get("max_new_tokens") or first.get("max_new_tokens") or 0
            gen_tokens = chosen_sample.get("gen_tokens", 0)
            truncated = bool(chosen_sample.get("hit_token_cap")) or (
                isinstance(gen_tokens, int) and max_tok and gen_tokens >= max_tok - 10
            )
        else:
            full_response = r.get("response", "")
            samples = []
            voted = ""
            max_tok = r.get("max_new_tokens") or first.get("max_new_tokens") or 0
            gen_tokens = r.get("gen_tokens", 0)
            truncated = bool(r.get("hit_token_cap")) or (
                isinstance(gen_tokens, int) and max_tok and gen_tokens >= max_tok - 10
            )

        extracted = grader.extract_boxed_answer(full_response) if full_response else ""
        all_boxed = grader.extract_all_boxed(
            split_response_think(full_response)[1] or full_response
        ) if full_response else []
        # C3: single source of truth — flag iff the final extracted string is empty.
        extracted_empty = (extracted == "")

        thinking, _final = split_response_think(full_response)
        n_think = n_thinking_tokens_estimate(thinking)

        # math correctness on the voted/chosen response
        math_ok = judge_math(grader, full_response, gold_answer, options, args.fail_fast) if gold_answer else False

        # per-sample (SC) — also feeds bucket A_lucky_sample "any sample right"
        any_sample_right = math_ok
        n_samples_math_correct = 1 if math_ok else 0
        sc_vote_size = None
        if is_sc:
            n_samples_math_correct = 0
            voted_matches = 0
            for si, s in enumerate(samples):
                s_resp = s.get("response", "")
                s_extracted = grader.extract_boxed_answer(s_resp) if s_resp else ""
                s_correct = judge_math(grader, s_resp, gold_answer, options, args.fail_fast) if gold_answer else False
                if s_correct:
                    any_sample_right = True
                    n_samples_math_correct += 1
                if _norm(s.get("extracted_answer")) == _norm(voted):
                    voted_matches += 1
                s_max = max_tok
                s_gen = s.get("gen_tokens", 0)
                s_trunc = bool(s.get("hit_token_cap")) or (
                    isinstance(s_gen, int) and s_max and s_gen >= s_max - 10
                )
                sample_rows.append({
                    "item_id": iid,
                    "sample_index": si,
                    "sample_extracted": s_extracted,
                    "sample_correct": s_correct,
                    "sample_truncated": s_trunc,
                    "sample_temperature": s.get("temperature"),
                    "sample_top_p": r.get("top_p"),
                    "sample_seed": s.get("seed"),
                    "sample_n_tokens": s_gen,
                })
            sc_vote_size = voted_matches

        # format correctness (C5: interim policy == math_correct)
        format_ok = format_correct_probe(grader, full_response, gold_answer, options, math_ok)

        # bucket (C8: independence-order flip — computational/web gold beats sheet_tier;
        # unanimous-teachers stays deferred to sheet_tier). gold_source already encodes
        # the winning signal by C7 precedence, so we branch on it.
        def _bucket_decide():
            if math_ok:
                return "A"
            if is_sc and n_samples_math_correct > 0:
                return "A_lucky_sample"
            return "B"

        if gold_source == "wolfram_HIGH":
            bucket = _bucket_decide()                     # computational truth overrides tier
        elif gold_source == "search_GOLD":
            bucket = _bucket_decide()                     # web-verified overrides tier
        elif gold_source == "unanimous_teachers" and tier in (1, 2, 3):
            bucket = _bucket_decide()
        elif gold_source == "unanimous_teachers" and tier in (4, 5):
            bucket = "unknown"                            # teachers agree but sheet flagged low-conf
        else:
            bucket = "unknown"

        # C4: collapse all whitespace to single spaces (no newlines/double-spaces)
        # C13: FIRST 200 chars of the canonical response (spec said head, not tail).
        preview = re.sub(r"\s+", " ", (full_response or ""))[:200].strip()

        analysis_rows.append({
            "item_id": iid,
            "category": category,
            "tier": tier,
            "gold_answer": gold_answer,
            "gold_source": gold_source,
            "gold_independent_flag": gold_independent,
            "gold_uncertain_flag": gold_uncertain,
            "extracted_answer": extracted,
            "extracted_empty_flag": extracted_empty,
            "truncated_flag": bool(truncated),
            "format_correct": bool(format_ok),
            "format_check_capability": "cosmetic_only_until_structural",
            "math_correct": bool(math_ok),
            "format_failure_subtype": "",  # DEFERRED per task
            "bucket": bucket,
            "bucket_b_review_needed": (bucket == "B"),  # C10
            "n_tokens_total": gen_tokens,
            "n_tokens_thinking": n_think,
            "sc_vote_size": sc_vote_size if sc_vote_size is not None else "",
            "sc_total_samples": n_samples if is_sc else 1,
            "response_preview": preview,
            "notes": notes,
        })

        jsonl_rows.append({
            "item_id": iid,
            "category": category,
            "tier": tier,
            "gold_answer": gold_answer,
            "gold_source": gold_source,
            "gold_independent_flag": gold_independent,
            "gold_uncertain_flag": gold_uncertain,
            "extracted_answer": extracted,
            "all_boxed_extracted": all_boxed,
            "extracted_empty_flag": extracted_empty,
            "truncated_flag": bool(truncated),
            "format_correct": bool(format_ok),
            "format_check_capability": "cosmetic_only_until_structural",
            "math_correct": bool(math_ok),
            "bucket": bucket,
            "bucket_b_review_needed": (bucket == "B"),  # C10
            "n_samples_math_correct": n_samples_math_correct if is_sc else (1 if math_ok else 0),
            "sc_vote_size": sc_vote_size if sc_vote_size is not None else None,
            "sc_total_samples": n_samples if is_sc else 1,
            "full_response": full_response,
            "full_reasoning_trace": thinking,
            "voted_answer": voted if is_sc else None,
            "notes": notes,
        })

    # ── write analysis.csv (run-meta comment header, then CSV) ──
    csv_path = os.path.join(args.output_dir, "analysis.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        # C6: audit-score reframe
        f.write("# AUDIT-SCORE REFRAME: Audit score is for per-item bucket labels. "
                "Not a Kaggle-mirror. Local judger has known 28pp gap; restricted "
                "independent-gold subset is systematically easier.\n")
        for k, v in run_meta.items():
            f.write(f"# {k}: {v}\n")
        w = csv.DictWriter(f, fieldnames=ANALYSIS_COLS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(analysis_rows)

    # ── write analysis.jsonl (row 0 carries _run_meta) ──
    jsonl_path = os.path.join(args.output_dir, "analysis.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        if jsonl_rows:
            jsonl_rows[0] = {"_run_meta": run_meta, **jsonl_rows[0]}
        for jr in jsonl_rows:
            f.write(json.dumps(jr, ensure_ascii=False) + "\n")

    # ── write analysis_samples.jsonl (SC only; C14: --skip-samples suppresses) ──
    samples_path = None
    if is_sc and not args.skip_samples:
        samples_path = os.path.join(args.output_dir, "analysis_samples.jsonl")
        with open(samples_path, "w", encoding="utf-8") as f:
            for sr in sample_rows:
                f.write(json.dumps(sr, ensure_ascii=False) + "\n")

    # ── summary to stdout ──
    bucket_dist = Counter(r["bucket"] for r in analysis_rows)
    src_dist = Counter(r["gold_source"] for r in analysis_rows)
    scored = [r for r in analysis_rows if r["bucket"] != "unknown"]
    scored_n = len(scored)
    scored_math = sum(1 for r in scored if r["math_correct"])
    # C16: hard_independent split — CLEAN (T1/T2/T3) is the gate set; DIRTY (T4/T5) report-only
    hard_all = [r for r in scored if r["gold_source"] in ("wolfram_HIGH", "search_GOLD")]
    hard_clean = [r for r in hard_all if int(r["tier"]) in (1, 2, 3)]
    hard_dirty = [r for r in hard_all if int(r["tier"]) in (4, 5)]
    hard_clean_math = sum(1 for r in hard_clean if r["math_correct"])
    hard_dirty_math = sum(1 for r in hard_dirty if r["math_correct"])
    unan = [r for r in scored if r["gold_source"] == "unanimous_teachers"]
    unan_math = sum(1 for r in unan if r["math_correct"])
    n_indep = sum(1 for r in analysis_rows if r["gold_independent_flag"])
    n_conflict = sum(1 for r in analysis_rows if "gold_conflict" in (r["notes"] or ""))
    n_b_review = sum(1 for r in analysis_rows if r["bucket_b_review_needed"])
    n_trunc = sum(1 for r in analysis_rows if r["truncated_flag"])
    n_empty = sum(1 for r in analysis_rows if r["extracted_empty_flag"])
    print(f"run_id={run_meta['run_id']}  is_sc={is_sc}  n_samples={n_samples}  items={len(analysis_rows)}")
    print(f"bucket: A={bucket_dist['A']} A_lucky_sample={bucket_dist['A_lucky_sample']} "
          f"B={bucket_dist['B']} unknown={bucket_dist['unknown']}")
    print(f"scored_set (bucket!=unknown): n={scored_n}  math_correct={scored_math}  "
          f"acc={scored_math/scored_n:.4f}" if scored_n else "scored_set: EMPTY")
    print(f"(c-new-fixed) hard_independent_CLEAN (wolfram+search @ T1/T2/T3): n={len(hard_clean)} "
          f"correct={hard_clean_math} acc={hard_clean_math/len(hard_clean):.4f}  [GATE 0.60-0.95]"
          if hard_clean else "(c-new-fixed) hard_independent_CLEAN: EMPTY")
    print(f"(c-info) hard_independent_DIRTY (wolfram+search @ T4/T5): n={len(hard_dirty)} "
          f"correct={hard_dirty_math} acc={hard_dirty_math/len(hard_dirty):.4f}  [no gate; normalizer gap]"
          if hard_dirty else "(c-info) hard_independent_DIRTY: EMPTY")
    print(f"(d) unanimous_teachers (report-only): n={len(unan)} correct={unan_math} "
          f"acc={unan_math/len(unan):.4f}" if unan else "(d) unanimous_teachers: EMPTY")
    print(f"gold_source: wolfram_HIGH={src_dist['wolfram_HIGH']} "
          f"unanimous_teachers={src_dist['unanimous_teachers']} "
          f"search_GOLD={src_dist['search_GOLD']} sheet_dependent={src_dist['sheet_dependent']}")
    print(f"gold_independent_flag True={n_indep}  bucket_b_review_needed={n_b_review}")
    print(f"gold_conflict notes={n_conflict}  truncated={n_trunc}  extracted_empty={n_empty}")
    print(f"wrote: {csv_path}")
    print(f"wrote: {jsonl_path}")
    if samples_path:
        print(f"wrote: {samples_path}  ({len(sample_rows)} rows)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-jsonl", required=True)
    p.add_argument("--master-answers", required=True)
    p.add_argument("--private-jsonl", required=False, default=None,
                   help="root private.jsonl (id+question only; accepted but not required)")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-id", default=None)
    p.add_argument("--kaggle-score", type=float, default=None)
    # C14: batch flags (default False)
    p.add_argument("--skip-samples", action="store_true", default=False,
                   help="do not write analysis_samples.jsonl (faster batch runs)")
    p.add_argument("--fail-fast", action="store_true", default=False,
                   help="raise on the first per-item error instead of skipping it")
    args = p.parse_args()
    analyze(args)


if __name__ == "__main__":
    main()
