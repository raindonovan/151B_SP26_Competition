#!/usr/bin/env python3
"""
Per-item attribution table for every adapter override.  Issue #8.

Replaces reasoning-from-score-deltas with one row per overridden item.  Reads
only artifacts already in the repo; writes override_table.csv + a summary.

Denominators (COMPETITION.md:44-48):
  public  = ~283 items, a ~30% SUBSET of the private set   -> 1 item = 0.353pp
  private = the FULL 943                                   -> 1 item = 0.106pp
So every override is in the private set by construction; only ~30% of them
land in public.
"""
import csv, json, os, sys, difflib, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = lambda *a: os.path.join(ROOT, *a)

# ---------------------------------------------------------------- the two override sets
ELEVEN = [89, 127, 182, 302, 317, 389, 429, 463, 762, 776, 839]

def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def submission_map(path):
    """id -> response, for a Kaggle submission csv."""
    rows = read_csv(path)
    key_id = 'id' if 'id' in rows[0] else list(rows[0])[0]
    key_rs = 'response' if 'response' in rows[0] else list(rows[0])[-1]
    return {int(r[key_id]): r[key_rs] for r in rows}

picka = submission_map(P('submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v2.csv'))
v5fin = submission_map(P('submission/v5_final.csv'))
FIFTY = sorted(i for i in picka if picka[i] != v5fin.get(i))

# ---------------------------------------------------------------- evidence sources
decomp = {int(r['item_id']): r for r in read_csv(P('data/v5_per_item_decomp.csv'))}
sheet  = {int(r['id']): r for r in read_csv(P('data/answer_sheet_v7_FINAL.csv'))}
backs  = {int(r['item_id']): r for r in read_csv(P('data/back_solve_detail.csv'))}

train = {}
with open(P('data/sft_v5_dataset.jsonl'), encoding='utf-8') as f:
    for line in f:
        o = json.loads(line)
        iid = o.get('item_id', o.get('id'))
        asst = ''
        for m in o.get('messages', []):
            if m.get('role') == 'assistant':
                asst = m.get('content', '')
        if iid is not None:
            train[int(iid)] = asst

adapter_resp = {}
with open(P('inference/results/hybrid/adapter_v5_run.jsonl'), encoding='utf-8') as f:
    for line in f:
        o = json.loads(line)
        iid = o.get('item_id', o.get('id'))
        if iid is None:
            continue
        txt = o.get('response') or o.get('text') or ''
        if not txt:
            for k in ('samples', 'responses', 'generations'):
                v = o.get(k)
                if isinstance(v, list) and v:
                    txt = v[0] if isinstance(v[0], str) else json.dumps(v[0])
                    break
        adapter_resp[int(iid)] = txt

def trace_sim(iid):
    a, b = adapter_resp.get(iid), train.get(iid)
    if not a or not b:
        return ''
    return round(difflib.SequenceMatcher(None, a, b).ratio(), 4)

# ---------------------------------------------------------------- build
def row_for(iid, which):
    d = decomp.get(iid, {})
    s = sheet.get(iid, {})
    b = backs.get(iid, {})
    in_train = iid in train
    indep = (d.get('gold_provenance') == 'HIGH') or ('wolfram' in (s.get('math_sources') or '').lower()) \
            or ('search' in (s.get('math_sources') or '').lower())
    return {
        'item_id': iid,
        'override_set': which,
        'tier': d.get('tier', s.get('math_source_tier', '')),
        'is_mcq': d.get('is_mcq', ''),
        'in_training_set': in_train,
        'base_answer': d.get('base_voted_answer', ''),
        'adapter_answer': d.get('adapter_voted_answer', ''),
        'gold_answer': d.get('gold_answer', s.get('math_answer', '')),
        'gold_provenance': d.get('gold_provenance', ''),
        'math_sources': s.get('math_sources', ''),
        'math_source_tier': s.get('math_source_tier', ''),
        'gold_independent': indep,
        'backsolve_answer': b.get('predicted_kaggle_answer', ''),
        'backsolve_conf': b.get('confidence_pct', ''),
        'backsolve_tier': b.get('tier', ''),
        'adapter_correct': d.get('adapter_correct', ''),
        'base_correct': d.get('base_correct', ''),
        'classification': d.get('classification', ''),
        'trace_similarity': trace_sim(iid),
        'circular': bool(in_train and not indep),
    }

rows = [row_for(i, '11_overlay') for i in ELEVEN] + [row_for(i, '50_v5final') for i in FIFTY]
out = P('post_comp/adapter_analysis/override_table.csv')
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

# ---------------------------------------------------------------- report
print(f'50-set recovered from v5_final.csv vs Pick A: {len(FIFTY)} items')
print(f'  ids: {FIFTY}')
print(f'overlap between the two override sets: {sorted(set(ELEVEN) & set(FIFTY))}')
print()
e = [r for r in rows if r['override_set'] == '11_overlay']
print('--- the 11 overlay ---')
print(f"  in training set : {sum(r['in_training_set'] for r in e)}/11")
print(f"  independent gold: {sum(r['gold_independent'] for r in e)}/11")
print(f"  CIRCULAR (in train AND gold not independent): {sum(r['circular'] for r in e)}/11")
print('  classification  :', dict(collections.Counter(r['classification'] for r in e)))
sims = [r['trace_similarity'] for r in e if r['trace_similarity'] != '']
if sims:
    print(f"  trace similarity: n={len(sims)} min={min(sims)} median={sorted(sims)[len(sims)//2]} max={max(sims)}")
f5 = [r for r in rows if r['override_set'] == '50_v5final']
print('--- the 50 (v5_final.csv) ---')
print(f"  in training set : {sum(r['in_training_set'] for r in f5)}/{len(f5)}")
print(f"  have decomp row : {sum(1 for r in f5 if r['classification'])}/{len(f5)}")
print(f"  independent gold: {sum(r['gold_independent'] for r in f5)}/{len(f5)}")
print()
print('wrote', out)
