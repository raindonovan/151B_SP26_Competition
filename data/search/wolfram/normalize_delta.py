"""normalize_delta.py — Stage 2/3 of screen-then-normalize.

Runs ONLY on the structurally-valid bucket from structural_screen.py.
Reference signal = the 4 independent teachers (sonnet/gpt4/oss/xhigh).

For each valid Wolfram row, compare Wolfram answer vs each available teacher answer:
  RAW agree   = exact string match (whitespace-normalized only)
  NORM agree  = gold_equiv(...) is True  (value-equality + latex/ascii/frac collapse)
  disagree    = gold_equiv(...) is False (genuine value difference)
  incomparable= gold_equiv(...) is None  (subset/undercount or letter-vs-num leak)

Per row we take the BEST teacher outcome (does ANY teacher agree?). The delta —
rows that agree only after normalization — is the normalizer's measured value-add.
Rows still disagreeing with every teacher after normalization are the genuine
discrepancy/unresolved set (these are signal, not noise).
"""
import csv, json, sys, signal
sys.path.insert(0, 'scripts')
from gold_equiv import gold_equiv

B = json.load(open('/home/claude/screen_buckets.json'))
VALID = set(B['valid'])
W = {r['id']: r for r in csv.DictReader(open('data/search/wolfram/WOLF_RESULTS.csv'))}

# teacher answers, CR-stripped, int id -> padded
TE = {m: {} for m in ['sonnet', 'gpt4', 'oss', 'xhigh']}
for m in TE:
    for row in csv.DictReader(open(f'data/search/teachers/{m}/answers.csv')):
        TE[m][row['id'].zfill(4)] = (row['answer'] or '').strip().rstrip('\r')

def norm_ws(s): return ' '.join(s.split())

class TO(Exception): pass
def _alarm(s, f): raise TO()
signal.signal(signal.SIGALRM, _alarm)
def safe_equiv(p, g, t):
    signal.alarm(8)
    try: return gold_equiv(p, g, t)
    except Exception: return 'ERR'
    finally: signal.alarm(0)

raw_match, norm_only, no_match, errs = [], [], [], []
detail = {}
for rid in sorted(VALID):
    w = W[rid]; wa = w['wolfram_answer'].strip(); qt = w['type']
    teach = {m: TE[m].get(rid, '') for m in TE}
    teach = {m: a for m, a in teach.items() if a and a not in ('answer', 'Letter', 'value1,value2,value3')}
    if not teach:
        no_match.append(rid); detail[rid] = 'no usable teacher'; continue
    any_raw = any(norm_ws(wa) == norm_ws(a) for a in teach.values())
    any_norm = False
    for a in teach.values():
        r = safe_equiv(wa, a, qt)
        if r == 'ERR': errs.append(rid)
        if r is True: any_norm = True; break
    if any_raw:
        raw_match.append(rid)
    elif any_norm:
        norm_only.append(rid)
    else:
        no_match.append(rid)

total = len(VALID)
print(f'BUCKET 2 (structurally valid) rows: {total}')
print(f'  raw exact-match to >=1 teacher          : {len(raw_match):4}  ({len(raw_match)/total:.0%})')
print(f'  match ONLY after normalization (DELTA)  : {len(norm_only):4}  ({len(norm_only)/total:.0%})  <- normalizer value-add')
print(f'  no teacher match even after normalize   : {len(no_match):4}  ({len(no_match)/total:.0%})  <- genuine disagreement / unresolved')
print(f'  (parse errors encountered, counted above): {len(set(errs))}')
print()
print('DELTA sample (agreed only after normalization — these are formatting noise):')
for rid in norm_only[:12]:
    w = W[rid]
    ta = next((TE[m].get(rid, '') for m in TE if TE[m].get(rid, '')), '')
    print(f'  {rid} W={w["wolfram_answer"][:34]!r:38} T={ta[:30]!r}')
print()
print('UNRESOLVED sample (disagree with all teachers post-normalize — genuine signal):')
for rid in no_match[:14]:
    w = W[rid]
    ta = next((TE[m].get(rid, '') for m in TE if TE[m].get(rid, '')), '')
    print(f'  {rid} [{w["type"]}] W={w["wolfram_answer"][:30]!r:34} T={ta[:26]!r}')
json.dump({'raw_match': raw_match, 'norm_only': norm_only, 'no_match': no_match},
          open('/home/claude/delta_buckets.json', 'w'))
