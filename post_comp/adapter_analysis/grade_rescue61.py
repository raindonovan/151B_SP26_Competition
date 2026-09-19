#!/usr/bin/env python3
"""#10, offline half: grade adapter_rescue_61 -- the only held-out adapter data."""
import csv, io, json, os, sys, signal
sys.path.insert(0, '/home/raindonovan/151B-SP26-Competition')
from grading.grader import Grader

ROOT='/home/raindonovan/151B-SP26-Competition'
def rd(p):
    L=[l for l in open(os.path.join(ROOT,p),encoding='utf-8') if not l.startswith('#')]
    return list(csv.DictReader(io.StringIO(''.join(L))))

r20={int(x['item_id']):x for x in rd('inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/analysis/analysis.csv')}
train={int(json.loads(l).get('item_id', json.loads(l).get('id',-1))) for l in open(os.path.join(ROOT,'data/sft_v5_dataset.jsonl'))}

ad={}
with open(os.path.join(ROOT,'inference/results/hybrid/dsmlp-A30/adapter_rescue_61_20260526T210207Z.jsonl')) as f:
    for line in f:
        o=json.loads(line); i=o.get('item_id',o.get('id'))
        if i is not None: ad[int(i)]=o

G=Grader()
def eq(a,b,secs=5):
    def h(*_): raise TimeoutError
    old=signal.signal(signal.SIGALRM,h); signal.alarm(secs)
    try: return bool(G.is_equal(a,b))
    except Exception: return None
    finally: signal.alarm(0); signal.signal(signal.SIGALRM,old)

rows=[]
for i,o in sorted(ad.items()):
    g=r20.get(i,{})
    gold=g.get('gold_answer','')
    a=o.get('voted_answer') or o.get('extracted_answer') or o.get('answer') or ''
    b=g.get('extracted_answer','')
    if not gold: continue
    ac, bc = eq(a,gold), eq(b,gold)
    rows.append(dict(id=i, gold=gold, base=b, adapter=a, base_ok=bc, adapter_ok=ac,
                     indep=g.get('gold_independent_flag','')=='True',
                     multislot=(',' in gold or '=' in gold),
                     in_train=i in train))

ok=[r for r in rows if r['base_ok'] is not None and r['adapter_ok'] is not None]
win =[r for r in ok if r['adapter_ok'] and not r['base_ok']]
loss=[r for r in ok if r['base_ok'] and not r['adapter_ok']]
print(f'graded {len(ok)}/{len(rows)}  (held out: {sum(1 for r in rows if r["in_train"])} of 61 in training -> expect 0)')
print(f'  adapter {sum(r["adapter_ok"] for r in ok)}/{len(ok)}   base {sum(r["base_ok"] for r in ok)}/{len(ok)}')
print(f'  WIN {len(win)}   LOSS {len(loss)}   net {len(win)-len(loss):+d}')
print()
wm=[r for r in win if r['multislot']]
print(f'  of the {len(win)} wins, {len(wm)} are MULTI-SLOT gold (the base-extraction artifact):')
for r in wm: print(f'     {r["id"]:>4}  gold={r["gold"][:38]!r:42} base={r["base"][:20]!r}')
print(f'  wins on independent gold: {sum(1 for r in win if r["indep"])}/{len(win)}')
print(f'  NET after removing multi-slot artifacts: {len(win)-len(wm)-len(loss):+d}')
with open(os.path.join(ROOT,'post_comp/adapter_analysis/rescue61_graded.csv'),'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
