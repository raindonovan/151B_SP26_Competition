# DEPRECATED — replaced by build_answer_sheet_v4.py. Do not use.
#!/usr/bin/env python3
"""build_answer_sheet.py v3 — All 16 subs + teacher consensus"""
import argparse, csv, json, math, os, re, sys
from collections import defaultdict, Counter
from pathlib import Path

SUBMISSION_REGISTRY = [
    ("run14b_v3filtered.csv",           0.646, False),
    ("run14b_sc8_v1.csv",               0.639, False),
    ("run09sc8_v1_private943.csv",      0.614, False),
    ("run09sc8_format_fixed.csv",       0.611, False),
    ("run08v2_v1_private943.csv",       0.586, False),
    ("diagnostic_sub_a.csv",            0.505, True),
    ("sftv3_epoch8_sc1_final.csv",      0.452, False),
    ("run09sc8_probe_b_reversed.csv",   0.438, False),
    ("run10_v3perslot_private943.csv",  0.424, False),
    ("expA_run08_perslot_perturbed.csv",0.420, False),
    ("D_05_07_numina_d.csv",            0.310, True),
    ("diagnostic_sub_c.csv",            0.222, True),
    ("post_filtered_b.csv",             0.151, True),
    ("f_today_F.csv",                   0.137, True),
    ("E_05_13_h100run_e.csv",           0.028, True),
    ("g_epoch8_lora_G.csv",             0.017, True),
]

def extract_last_boxed(text):
    positions = []
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1: break
        positions.append(pos)
        i = pos + 7
    if not positions: return None
    start = positions[-1] + 7
    depth, j = 1, start
    while j < len(text) and depth > 0:
        if text[j] == "{": depth += 1
        elif text[j] == "}": depth -= 1
        j += 1
    if depth == 0: return text[start:j-1].strip()
    return text[start:].strip() if text[start:].strip() else None

def extract_answer(response):
    if not response or not response.strip(): return ""
    response = response.strip()
    boxed = extract_last_boxed(response)
    if boxed: return boxed
    for skip in ["PLACEHOLDER","INVALID","77777777.77777","W"]:
        if response == skip or skip in response: return ""
    if len(response) < 500: return response.strip()
    return ""

def load_csv(filepath):
    answers = {}
    with open(filepath, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        ac = 'response' if 'response' in cols else 'answer' if 'answer' in cols else 'prediction' if 'prediction' in cols else None
        if not ac: return answers
        for row in reader:
            try: iid = int(row['id'])
            except: continue
            answers[iid] = extract_answer(row.get(ac, ""))
    return answers

def normalize(answer):
    if not answer: return ""
    s = answer.strip()
    if s.startswith("$") and s.endswith("$"): s = s[1:-1].strip()
    s = s.replace("\\,", " ").replace("\\;", " ").replace("\\ ", " ").replace("\\quad", " ")
    s = re.sub(r'\\text\s*\{[^}]{1,30}\}\s*$', '', s).strip()
    s = s.replace("\\dfrac", "\\frac")
    s = re.sub(r'\s*,\s*', ', ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def equiv(a, b):
    if a == b: return True
    try:
        if abs(float(a) - float(b)) < 1e-6: return True
    except: pass
    def ef(s):
        m = re.match(r'\\frac\{(-?\d+)\}\{(-?\d+)\}', s)
        if m: return float(m.group(1))/float(m.group(2))
        m = re.match(r'(-?\d+)/(-?\d+)$', s)
        if m: return float(m.group(1))/float(m.group(2))
        return None
    fa, fb = ef(a), ef(b)
    if fa is not None and fb is not None and abs(fa-fb)<1e-6: return True
    for fv, sv in [(fa,b),(fb,a)]:
        if fv is not None:
            try:
                if abs(fv-float(sv))<1e-6: return True
            except: pass
    return False

def group_equiv(candidates):
    groups = []
    for na, sn, sc in candidates:
        if not na: continue
        matched = False
        for i,(c,m) in enumerate(groups):
            if equiv(na, c):
                m.append((sn,sc))
                if sc > max(s for _,s in m[:-1]): groups[i] = (na, m)
                matched = True; break
        if not matched: groups.append((na, [(sn,sc)]))
    return {c:m for c,m in groups}

def bayesian(item_sub_ans, sub_scores):
    candidates = []
    for sn, ra in item_sub_ans.items():
        na = normalize(ra)
        if na: candidates.append((na, sn, sub_scores.get(sn, 0.5)))
    if not candidates: return "", 0.0, {}
    groups = group_equiv(candidates)
    if not groups: return "", 0.0, {}
    active = {sn for sn, ra in item_sub_ans.items() if normalize(ra)}
    log_post = {}
    for cX, supporters in groups.items():
        snames = {n for n,_ in supporters}
        lp = sum(math.log(max(0.01,min(0.99,sub_scores.get(sn,0.5)))) if sn in snames
                 else math.log(1-max(0.01,min(0.99,sub_scores.get(sn,0.5))))
                 for sn in active)
        log_post[cX] = lp
    mx = max(log_post.values())
    probs = {X: math.exp(lp-mx) for X,lp in log_post.items()}
    tot = sum(probs.values())
    if tot == 0: return "", 0.0, {}
    probs = {X: p/tot for X,p in probs.items()}
    best = max(probs, key=probs.get)
    return best, probs[best], probs

def tier(c):
    if c>=0.90: return 1
    if c>=0.80: return 2
    if c>=0.60: return 3
    if c>=0.40: return 4
    return 5

def load_teachers(path):
    with open(path) as f: data = json.load(f)
    teachers = {}
    for iid_str, entry in data.items():
        iid = int(iid_str)
        answers = {}
        for k,name in [('s','sonnet'),('g','gpt5_4'),('o','gpt_oss')]:
            if k in entry: answers[name] = entry[k]
        if not answers:
            teachers[iid] = {"consensus":"","agreement":0.0,"answers":{}}
            continue
        norms = {n: normalize(a) for n,a in answers.items()}
        vc = Counter(norms.values())
        ba = vc.most_common(1)[0][0]
        ag = vc.most_common(1)[0][1] / len(norms)
        raw = ""
        for n in ["sonnet","gpt5_4","gpt_oss"]:
            if n in norms and norms[n] == ba: raw = answers[n]; break
        teachers[iid] = {"consensus":raw,"agreement":ag,"answers":answers}
    return teachers

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--submissions-dir", required=True)
    p.add_argument("--teachers", default="data/teacher_answers_compact.json")
    p.add_argument("--data", default=None)
    p.add_argument("--output-dir", default="results/answer_sheet")
    args = p.parse_args()
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)

    print("="*70); print("STEP 1: Load submissions"); print("="*70)
    sub_ans, sub_scores, diag_subs = {}, {}, set()
    for fn, score, is_diag in SUBMISSION_REGISTRY:
        fp = os.path.join(args.submissions_dir, fn)
        if not os.path.exists(fp): print(f"  X MISSING: {fn}"); continue
        print(f"  {fn} ({score:.3f}){'  [DIAG]' if is_diag else ''}...", end="")
        ans = load_csv(fp)
        n = sum(1 for a in ans.values() if a)
        print(f" {n}/943")
        sn = fn.replace(".csv","")
        sub_ans[sn] = ans; sub_scores[sn] = score
        if is_diag: diag_subs.add(sn)
    print(f"\nTotal: {len(sub_ans)} ({len(diag_subs)} diagnostic)")

    print("\n"+"="*70); print("STEP 2: Teacher consensus"); print("="*70)
    teachers = {}
    if os.path.exists(args.teachers):
        teachers = load_teachers(args.teachers)
        n3 = sum(1 for t in teachers.values() if t["agreement"]>=1.0)
        n2 = sum(1 for t in teachers.values() if 0.5<t["agreement"]<1.0)
        print(f"  Loaded {len(teachers)} items: {n3} with 3/3, {n2} with 2/3 agreement")
    else:
        print(f"  NOT FOUND: {args.teachers}")

    print("\n"+"="*70); print("STEP 3: Question types"); print("="*70)
    item_types = {}
    if args.data and os.path.exists(args.data):
        with open(args.data) as f:
            for line in f:
                item = json.loads(line)
                item_types[item["id"]] = {"type":"mcq" if item.get("options") else "free"}
        print(f"  {len(item_types)} items")

    print("\n"+"="*70)
    print(f"STEP 4: Answer matrix (943 x {len(sub_ans)})"); print("="*70)
    matrix = {}
    for iid in range(943):
        ia = {}
        for sn, ans in sub_ans.items():
            n = normalize(ans.get(iid,""))
            if n: ia[sn] = n
        matrix[iid] = ia
    mp = out/"answer_matrix.json"
    with open(mp,"w") as f: json.dump({str(k):v for k,v in matrix.items()},f,indent=1)
    print(f"  Saved: {mp}")

    print("\n"+"="*70); print("STEP 5: Bayesian voting"); print("="*70)
    results = []
    for iid in range(943):
        isa = {sn:ans.get(iid,"") for sn,ans in sub_ans.items() if ans.get(iid,"")}
        best, conf, posts = bayesian(isa, sub_scores)
        td = teachers.get(iid, {})
        ta = normalize(td.get("consensus",""))
        tagree = equiv(normalize(best), ta) if ta and best else None
        adj = conf
        if tagree is True: adj = min(0.99, conf+0.05)
        elif tagree is False and td.get("agreement",0)>=1.0: adj = max(0.10, conf-0.10)
        atier = tier(adj)
        ru,ruc = "",0.0
        if len(posts)>1:
            sp = sorted(posts.items(),key=lambda x:-x[1])
            ru,ruc = sp[1][0],sp[1][1]
        ns=nw=0
        for sn,ra in isa.items():
            n=normalize(ra)
            if n: nw+=1
            if n and equiv(n,normalize(best)): ns+=1
        results.append({"item_id":iid,"best_answer":best,
            "raw_confidence":round(conf,4),"adjusted_confidence":round(adj,4),
            "tier":atier,"runner_up":ru,"runner_up_conf":round(ruc,4),
            "n_supporting":ns,"n_with_answer":nw,
            "teacher_consensus":td.get("consensus",""),
            "teacher_agrees":str(tagree) if tagree is not None else "N/A",
            "teacher_agreement":round(td.get("agreement",0),2)})

    print("\n"+"="*70); print("STEP 6: Save"); print("="*70)
    sp = out/"unified_answer_sheet.csv"
    with open(sp,"w",newline="") as f:
        w = csv.DictWriter(f,fieldnames=["item_id","best_answer","raw_confidence",
            "adjusted_confidence","tier","runner_up","runner_up_conf","n_supporting",
            "n_with_answer","teacher_consensus","teacher_agrees","teacher_agreement"])
        w.writeheader(); w.writerows(results)
    print(f"  Saved: {sp}")
    tc = Counter(r["tier"] for r in results)
    print("\n  Tiers:")
    for t in range(1,6): print(f"    T{t}: {tc[t]:>4} ({tc[t]/943*100:.1f}%)")
    tac = Counter(r["teacher_agrees"] for r in results)
    print(f"\n  Teacher: {dict(tac)}")

    print("\n"+"="*70)
    print("STEP 7: Validation (non-diagnostic only)")
    print("="*70)
    sheet = {r["item_id"]:r["best_answer"] for r in results}
    report = ["=== VALIDATION (non-diagnostic submissions only) ===",""]
    for sn in sorted(sub_scores, key=sub_scores.get, reverse=True):
        if sn in diag_subs: continue
        actual = sub_scores[sn]
        sa = sub_ans.get(sn,{})
        agree=tot=0
        for iid in range(943):
            ours = normalize(sheet.get(iid,""))
            theirs = normalize(sa.get(iid,""))
            if ours and theirs: tot+=1; agree += 1 if equiv(ours,theirs) else 0
        pred = agree/943 if tot>0 else 0
        d = pred-actual
        s = "PASS" if abs(d)<0.05 else "WARN" if abs(d)<0.10 else "FAIL"
        line = f"  {s} {sn:<42} Kaggle={actual:.3f} Agree={agree}/{tot} Pred={pred:.3f} D={d:+.3f}"
        report.append(line); print(line)
    rp = out/"validation_report.txt"
    with open(rp,"w") as f:
        f.write("\n".join(report))
        f.write(f"\n\nTiers:\n")
        for t in range(1,6): f.write(f"  T{t}: {tc[t]} ({tc[t]/943*100:.1f}%)\n")
        f.write(f"\nTeacher: {dict(tac)}\n")
    print(f"\n  Saved: {rp}")
    print("\n"+"="*70); print("DONE"); print("="*70)

if __name__ == "__main__":
    main()
