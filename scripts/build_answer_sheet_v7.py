"""Build data/answer_sheet_v7_FINAL.csv (Variant 1 master) + probe overlay + README.

Separates math_answer (correct value) from submission_answer (exact Kaggle string),
with format_status/format_strategy/ship_class so format risk is visible per row.
See data/ANSWER_SHEET_v7_README.md for schema. No Kaggle upload here.
"""
from __future__ import annotations
import csv, json, sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
csv.field_size_limit(sys.maxsize)
from gold_equiv import gold_equiv
from score_inference_vs_sheet import last_boxed, first_letter, _surface_from_inference_record

T = "data/search/teachers"
pad = lambda x: str(x).strip().zfill(4)

# ---- hard-coded CHATGPT_AUDIT inputs (verbatim from work-unit) ----
OPUS_5TH_TEACHER_57 = {
    "0006":3,"0008":4,"0027":3,"0037":4,"0051":3,"0069":3,"0122":3,"0132":4,"0136":3,"0138":3,
    "0149":3,"0151":3,"0155":4,"0215":3,"0238":4,"0262":4,"0271":3,"0287":3,"0310":4,"0319":4,
    "0328":3,"0342":4,"0365":4,"0396":3,"0424":4,"0437":4,"0443":3,"0480":3,"0483":3,"0488":3,
    "0489":3,"0516":4,"0520":3,"0523":3,"0525":3,"0532":3,"0539":3,"0543":3,"0544":3,"0595":4,
    "0599":3,"0608":3,"0617":3,"0633":4,"0645":3,"0681":3,"0705":4,"0718":3,"0737":3,"0756":3,
    "0761":3,"0766":3,"0838":4,"0843":3,"0908":3,"0925":3,"0929":4,
}
assert len(OPUS_5TH_TEACHER_57) == 57, len(OPUS_5TH_TEACHER_57)
# per-flip: (math_value, math_sources, provenance, reason)
_FLIP_STD = ("anchor_v2_opus_flip|opus_deep|xhigh", "anchor_v2_opus_flip",
             "deep Opus trace + cross-corroboration; anchor flip from CHATGPT_AUDIT")
FLIPS = {
    "0120": ("138",                _FLIP_STD[0], _FLIP_STD[1], _FLIP_STD[2]),
    "0248": ("\\dfrac{16192}{45}", _FLIP_STD[0], _FLIP_STD[1], _FLIP_STD[2]),
    "0308": ("\\dfrac{1980}{169}", _FLIP_STD[0], _FLIP_STD[1], _FLIP_STD[2]),
    "0836": ("15", "anchor_v2_opus_flip|opus_deep|chatgpt_secondary", "anchor_v2_opus_flip_secondary",
             "CHATGPT secondary review: anchor logic refuted by counterexample (chord-length divisibility); Opus correct"),
}
QUARANTINE = "0187"
REVIEW_NOTES = {
    "0383": "REVIEW_FUTURE: CHATGPT UNCERTAIN — theorem-level disagreement not closed by Opus trace",
    "0570": "REVIEW_FUTURE: CHATGPT UNCERTAIN — prompt may be compromised (synthetic OEIS-style); teacher answers split",
    "0405": "CHATGPT secondary review CONFIRMED anchor via DP recomputation of generating function",
    "0586": "CHATGPT secondary review CONFIRMED anchor via direct cubic regression",
}
SECONDARY_CONFIRMED = {"0405", "0586"}   # Fix 2: anchor confirmed → format_status untested, ship A (out of probe)
CONTENT_UNCERTAIN = {"0383", "0570"}     # Fix 1: content-uncertain → keep format_suspect but ship A (out of probe)
CONTRADICTION_CATEGORY_OVERRIDES = {
    "0167":"FORMAT_ARTIFACT","0448":"FORMAT_ARTIFACT","0713":"FORMAT_ARTIFACT",
    "0382":"PRECISION_DIFF","0187":"INCOMPARABLE",
}

def load_csv(p, key="id"):
    out = {}
    with open(p, newline="") as f:
        for r in csv.DictReader(f):
            out[pad(r[key])] = r
    return out

def main():
    # inputs
    priv = {}
    for line in open(REPO/"private.jsonl"):
        r = json.loads(line); priv[pad(r["id"])] = r
    tracker = load_csv(REPO/"data/master_item_tracker.csv")
    anchor  = load_csv(REPO/f"{T}/anchor_set_FINAL.csv")
    brk     = load_csv(REPO/f"{T}/teacher_agreement_breakdown.csv")
    tans = {t: load_csv(REPO/f"{T}/{t}/answers.csv") for t in ["sonnet","gpt4","oss","xhigh"]}
    opus5 = load_csv(REPO/f"{T}/opus/opus_5th_teacher.csv")
    av2   = load_csv(REPO/f"{T}/opus/anchor_v2_candidates.csv")
    base  = {pad(r["id"]): r["response"] for r in csv.DictReader(open(REPO/"submission/csvs/undercount_plus_frac.csv"))}
    qwen = {}
    for line in open(REPO/"inference/results/run14b_sc8_v1_private943_tok32k_pp1_v3filtered.jsonl"):
        r = json.loads(line); qwen[pad(r["id"])] = _surface_from_inference_record(r)

    anchor_ids = set(anchor)
    four_bloc = {i for i,r in brk.items() if r["cluster_pattern"]=="4"}
    contradictions = {i for i,r in av2.items() if r.get("opus_verdict")=="contradict"}

    def qtype(i):
        t = tracker.get(i,{})
        is_mcq = str(t.get("is_mcq","")).strip().lower() in ("1","true","yes") or bool(priv.get(i,{}).get("options"))
        if is_mcq: return "MCQ"
        if (priv.get(i,{}).get("question","") or "").count("[ANS]") > 1: return "free_multi"
        return "free_single"

    # cross-check A6 disjointness: the 57 must reach step 1e (not pre-empted by anchor/4-of-4)
    pre = sorted(i for i in OPUS_5TH_TEACHER_57 if i in anchor_ids or i in four_bloc)
    print(f"A6 precheck — opus-57 pre-empted by anchor/4of4: {len(pre)} {pre if pre else ''}")

    rows = []
    for n in range(943):
        i = f"{n:04d}"
        qt = qtype(i)
        base_resp = base.get(i, "")
        base_ans = first_letter(base_resp) if qt=="MCQ" else last_boxed(base_resp)
        qwen_resp = qwen.get(i, "")
        qwen_ans = first_letter(qwen_resp) if qt=="MCQ" else last_boxed(qwen_resp)
        a = anchor.get(i); av = av2.get(i, {}); trk = tracker.get(i, {})
        reason = ""; notes = ""

        # ---- Step 1: math ----
        if i in FLIPS:
            math, msrc, prov, reason = FLIPS[i]
            tier = "T1"
        elif i == QUARANTINE:
            math, tier, msrc, prov = qwen_ans, "T4", "qwen_voted", "qwen_voted_raw (anchor quarantined)"
            reason = "anchor row referenced wrong problem family; CHATGPT_AUDIT quarantine"
        elif a:
            math = a["answer"]
            tier = "T1" if a.get("tier","")=="A" else "T2"
            msrc = "anchor|" + (a.get("source","") or "anchor")
            prov = "anchor_audited"
            notes = REVIEW_NOTES.get(i, "")
        elif i in four_bloc:
            math, tier, msrc, prov = tans["sonnet"].get(i,{}).get("answer",""), "T2", "teacher_4of4", "teacher_4of4"
        elif i in OPUS_5TH_TEACHER_57:
            na = OPUS_5TH_TEACHER_57[i]
            math = opus5.get(i,{}).get("opus_answer","")
            tier = "T2" if na==4 else "T3"
            msrc = "opus|teacher_4of4" if na==4 else "opus|teacher_3of4"
            prov = "opus_5th_teacher_chatgpt_curated"
        elif base_ans:
            math, tier, msrc, prov = base_ans, "T4", "qwen_voted", "0.713_stack"
        else:
            # DECISION 2: no-box rescue chain (base lacks \boxed{}, uncovered)
            rescue = (trk.get("rescue_answer","") or "").strip()
            besta = (trk.get("best_answer","") or "").strip()
            if rescue:   math, srctag = rescue, "rescue_answer"
            elif besta:  math, srctag = besta, "best_answer"
            else:        math, srctag = qwen_ans, "qwen"
            tier, msrc, prov = "T5", "rescue_fallback|" + srctag, "rescue_fallback"
            reason = "base lacks \\boxed{}; rescue-chain populated"

        value_equal = gold_equiv(math, base_ans, qt) is True

        # ---- Step 2: format_status (DECISION 1: contradictions tagged independently of value-equality) ----
        if i == QUARANTINE:
            fstatus = "known_bad"
        elif i in FLIPS:
            fstatus = "untested"  # confirmed T1 value-change, not format-suspect
        elif i in contradictions:
            cat = CONTRADICTION_CATEGORY_OVERRIDES.get(i, "REAL_DISAGREEMENT")
            if cat in ("FORMAT_ARTIFACT","PRECISION_DIFF"):
                fstatus = "format_suspect"; reason = reason or "anchor↔opus equivalent semantically; anchor format may not match Kaggle"
            elif cat == "INCOMPARABLE":
                fstatus = "known_bad"
            elif av.get("anchor_source","") in ("wolfram_only","web_search_only"):
                fstatus = "format_suspect"; reason = reason or f"anchor disputed by Opus; anchor source is {av.get('anchor_source','')}; flagged for format probe"
            else:
                fstatus = "untested"
        elif value_equal:
            fstatus = "submission_proven"
        else:
            fstatus = "untested"
        if i in SECONDARY_CONFIRMED:   # Fix 2: secondary review confirmed anchor → out of probe pool
            fstatus = "untested"

        # ---- Step 3: submission_answer + format_strategy (DECISION 1: B-ship — never regress proven strings) ----
        def rebuild(math_v):
            if qt == "MCQ":
                return "\\boxed{" + (first_letter(math_v) or str(math_v).strip()[:1].upper()) + "}", "replace_mcq_box"
            if qt == "free_multi":
                return "\\boxed{" + str(math_v) + "}", "single_box_multislot"
            body = qwen_resp if prov == "rescue_fallback" else base_resp
            return body.rstrip() + "\n\n\\boxed{" + str(math_v) + "}", "append_last_box"

        if i in FLIPS:
            sub, strat = rebuild(math)
        elif i == QUARANTINE:
            sub, strat = qwen_resp, "keep_raw"
        elif value_equal:
            sub, strat = base_resp, "keep_raw"   # PRESERVE PROVEN STRING (even if format_suspect)
        else:
            sub, strat = rebuild(math)

        # ---- Step 4: ship_class (format_suspect → B regardless) ----
        if fstatus == "known_bad": ship = "C"
        elif fstatus == "format_suspect": ship = "A" if i in CONTENT_UNCERTAIN else "B"  # Fix 1: content-uncertain → A
        elif fstatus == "submission_proven": ship = "A"
        elif tier in ("T1","T2") and fstatus == "untested": ship = "A"
        elif tier == "T3": ship = "A"
        elif tier == "T4": ship = "A"
        else: ship = "C"  # T5

        rows.append({"id":i,"math_answer":math,"submission_answer":sub,"math_source_tier":tier,
                     "math_sources":msrc,"format_status":fstatus,"format_strategy":strat,
                     "provenance_answer":prov,"reason_for_override":reason,"ship_class":ship,"notes":notes})

    cols = ["id","math_answer","submission_answer","math_source_tier","math_sources","format_status",
            "format_strategy","provenance_answer","reason_for_override","ship_class","notes"]
    out = REPO/"data/answer_sheet_v7_FINAL.csv"
    with open(out,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    # ---- probe overlay (Fix 3: real render variants) ----
    import re as _re
    from sympy import sympify, N
    try:
        from sympy.parsing.latex import parse_latex
    except Exception:
        parse_latex = None

    def ascii_plain(s):
        """render_a — Kaggle-friendly plain notation: de-LaTeX \\frac/\\dfrac/\\sqrt/\\pi, strip braces/$."""
        s = (s or "").strip()
        s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
        s = _re.sub(r"\\d?frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
        s = _re.sub(r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)", s)
        s = _re.sub(r"\\sqrt(\w)", r"sqrt(\1)", s)
        s = s.replace("\\pi", "pi").replace("\\cdot", "*").replace("\\left", "").replace("\\right", "")
        s = s.replace("$", "").replace("\\,", "").replace("\\ ", " ")
        return _re.sub(r"\s+", " ", s).strip()

    def to_decimal_one(part):
        part = (part or "").strip()
        if not part:
            return None
        try:
            v = float(part)
            return f"{v:.6g}"
        except ValueError:
            pass
        if parse_latex is None:
            return None
        try:
            expr = sympify(parse_latex(part))
            if expr.free_symbols:   # has variables → not a pure decimal
                return None
            return f"{float(N(expr)):.6g}"
        except Exception:
            return None

    def to_decimal(s):
        """render_c — decimal eval; multi-part comma; blank if any part non-numeric."""
        parts = [p.strip() for p in str(s).split(",")]
        outp = [to_decimal_one(p) for p in parts]
        if any(o is None for o in outp):
            return ""   # not fully numeric
        return ", ".join(outp)

    def teacher_literal(i):
        if i in anchor: return anchor[i].get("answer", "")
        if i in four_bloc: return tans["sonnet"].get(i, {}).get("answer", "")
        if i in opus5: return opus5[i].get("opus_answer", "")
        return ""

    def bucket(i, m):
        qt = qtype(i)
        if qt == "MCQ": return "mcq_letter_vs_word"
        if qt == "free_multi": return "multislot_spacing"
        if "frac" in m or "." in m: return "fraction_vs_decimal"
        if any(s in m for s in ["\\sqrt", "\\pi", "^"]): return "symbolic_vs_numeric"
        return "unit_in_string"

    bset = [r for r in rows if r["ship_class"] == "B"]
    pcols = ["id","math_answer_canonical","render_a_kaggle_friendly","render_b_exact_symbolic",
             "render_c_decimal","render_d_opus_alternative","preferred_render_current",
             "format_risk","content_risk","probe_bucket"]
    parse_fail = 0; rd_ne_rb = 0; rc_pop = 0; ra_ne_rb = 0
    with open(REPO/"data/answer_sheet_v7_probe_overlay.csv","w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=pcols); w.writeheader()
        for r in bset:
            i = r["id"]; m = r["math_answer"]
            ra = ascii_plain(m)
            rb = m
            rc = to_decimal(m)
            rd = av2.get(i, {}).get("opus_answer", "")   # Opus contradiction value (genuine alternative)
            is_numeric_item = (qtype(i) != "MCQ")
            if is_numeric_item and not rc and ("," not in m) and not _re.search(r"[A-Za-z]", m):
                parse_fail += 1   # looked numeric but failed to evaluate
            if rd and rd != rb: rd_ne_rb += 1
            if rc: rc_pop += 1
            if ra != rb: ra_ne_rb += 1
            w.writerow({"id":i,"math_answer_canonical":m,"render_a_kaggle_friendly":ra,
                        "render_b_exact_symbolic":rb,"render_c_decimal":rc,"render_d_opus_alternative":rd,
                        "preferred_render_current":m,"format_risk":"high","content_risk":"low",
                        "probe_bucket":bucket(i,m)})
    print(f"F4(revised) probe={len(bset)}: render_d!=render_b {rd_ne_rb}/69 (target 69) | render_c populated {rc_pop} (~27) | render_a!=render_b {ra_ne_rb} (>=2)")
    print(f"probe sympy parse-fail on numeric-looking: {parse_fail}/{len(bset)} ({100*parse_fail/max(1,len(bset)):.0f}%)")

    # stats
    tdist = Counter(r["math_source_tier"] for r in rows)
    fdist = Counter(r["format_status"] for r in rows)
    sdist = Counter(r["ship_class"] for r in rows)
    print("rows:", len(rows))
    print("tier:", dict(tdist)); print("format:", dict(fdist)); print("ship:", dict(sdist))
    print("probe(B) rows:", len(bset))
    # asserts
    by = {r["id"]:r for r in rows}
    assert by["0187"]["ship_class"]=="C" and by["0187"]["format_status"]=="known_bad", "A4 fail"
    for fid in FLIPS:
        assert by[fid]["math_source_tier"]=="T1" and "opus_flip" in by[fid]["provenance_answer"], f"A5/P2 fail {fid}"
        assert by[fid]["math_answer"]==FLIPS[fid][0], f"A5 value fail {fid}"
    assert by["0836"]["math_answer"]=="15" and by["0836"]["provenance_answer"].endswith("secondary"), "P2 fail 0836"
    assert "REVIEW_FUTURE" in by["0383"]["notes"], "P3 fail 0383"
    assert "REVIEW_FUTURE" in by["0570"]["notes"], "P4 fail 0570"
    for oid,na in OPUS_5TH_TEACHER_57.items():
        exp = "T2" if na==4 else "T3"
        assert by[oid]["math_source_tier"]==exp, f"A6 fail {oid}: {by[oid]['math_source_tier']} != {exp}"
    print("asserts A4/A5/A6/P2/P3/P4: PASS")
    nulls = [r["id"] for r in rows if not all(r[c] for c in ["id","math_answer","submission_answer","math_source_tier","format_status","format_strategy","ship_class"])]
    print("rows with null in required cols:", len(nulls), nulls[:10])

if __name__ == "__main__":
    main()
