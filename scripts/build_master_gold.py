#!/usr/bin/env python3
"""build_master_gold.py (v3) — Qwen-independent gold sheet with type-routed comparison.
Sources: teachers + Wolfram + search (consolidated). Excludes qwen/backsolve/rescue.
Comparison: scripts/gold_equiv.py (type-routed, judger + sympy parse-coverage)."""
import csv, sys, os
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts')
from gold_equiv import gold_equiv
from collections import Counter

def load(p, k):
    with open(p, newline='') as f: return {r[k]: r for r in csv.DictReader(f)}
T = load('data/master_item_tracker.csv', 'id')
M = load('data/MASTER_ANSWERS.csv', 'item_id')
QT = {r['id']: (r.get('type','') or '').strip() for r in csv.DictReader(open('data/search/wolfram/MASTER_QUESTIONS.csv'))}

# consolidated search GOLD
search_gold = {}
for r in csv.DictReader(open('data/search/web_search/search_results.csv')):
    if (r.get('search_status','') or '').strip().upper()=='GOLD' and (r.get('found_answer','') or '').strip():
        search_gold[r['item_id']] = (r['found_answer'].strip(), (r.get('source_url','') or '').strip())

def _letter(x): return len(x.strip())==1 and x.strip().isalpha()
rows=[]
for iid,t in T.items():
    qtype = QT.get(iid) or ('MCQ' if t.get('is_mcq','').strip().lower()=='true' else 'free_single')
    is_mcq = qtype=='MCQ'
    a3=(t.get('teacher_agree_count','') or '').strip(); a3=int(a3) if a3.isdigit() else 0
    cons=(t.get('teacher_consensus','') or '').strip()
    wc=(t.get('wolfram_confidence','') or '').strip().upper(); wa=(t.get('wolfram_override','') or '').strip()
    wh = wc=='HIGH' and bool(wa)
    sg=search_gold.get(iid); sa=sg[0] if sg else ''; sgold=bool(sg)
    has_indep = wh or sgold
    indep_ans, indep_src = (wa,'wolfram_HIGH') if wh else ((sa,'search_GOLD') if sgold else ('',''))

    iv=''
    if has_indep and a3>=2 and cons:
        r = gold_equiv(indep_ans, cons, qtype)
        iv = {True:'agree', False:'disagree', None:'review'}[r]
    conflict = iv=='disagree'

    if is_mcq and a3>=2 and _letter(cons): best,src = cons,('teacher_3of3' if a3==3 else 'teacher_2of3')
    elif wh: best,src = wa,'wolfram_HIGH'
    elif sgold: best,src = sa,'search_GOLD'
    elif a3==3: best,src = cons,'teacher_3of3'
    elif a3==2: best,src = cons,'teacher_2of3'
    else: best,src = '','none'

    if a3==3 and has_indep and iv=='agree': tier='T1'
    elif a3==3 or (a3==2 and has_indep and iv=='agree'): tier='T2'
    elif a3==2 or (has_indep and a3<=1): tier='T3'
    else: tier='T4'
    if conflict: tier='T4'

    rows.append({'item_id':iid,'qtype':qtype,'tier':tier,'gold_source':src,'gold_best_answer':best,
        'teacher_agree_3t':a3,'teacher_consensus':cons,'wolfram_answer':wa,'wolfram_confidence':wc,
        'search_answer':sa,'search_gold':sgold,'indep_source':indep_src,'indep_vs_teacher':iv,
        'gold_conflict_flag':conflict,'n_ans_slots':t.get('n_ans_slots_q',''),
        'question_preview':(t.get('question_preview','') or '')[:80]})

os.makedirs('data/answer_sheet',exist_ok=True)
out='data/answer_sheet/master_gold_v1.csv'
with open(out,'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

print(f'wrote {out} ({len(rows)} items) | search GOLD in sheet:', sum(1 for r in rows if r['search_gold']))
print('tier:  ', dict(sorted(Counter(r['tier'] for r in rows).items())))
print('indep_vs_teacher:', dict(Counter(r['indep_vs_teacher'] for r in rows if r['indep_vs_teacher'])))
print('has gold_best_answer:', sum(1 for r in rows if r['gold_best_answer']),'/',len(rows))
print()
print('=== REAL conflicts after type-routed compare ===')
n=0
for r in rows:
    if r['gold_conflict_flag']:
        n+=1; iv=r['wolfram_answer'] if r['indep_source']=='wolfram_HIGH' else r['search_answer']
        print(f"  {r['item_id']:>4} [{r['qtype']:<11}] {r['indep_source']}={iv[:26]!r} vs teachers={r['teacher_consensus'][:26]!r}")
print(f'TOTAL real conflicts: {n}  (was 43 -> 27 -> now)')
