#!/usr/bin/env python3
"""
Section B Selection Script — kitchen-sink residual target_set computation.

Implements Section B of inference/runs/KITCHEN_SINK_DISPATCH_PLAN.md.

OPERATIONAL DEVIATION FROM LITERAL SPEC:
The spec says "start with R20 rows where bucket == 'B' or bucket == 'A_lucky_sample'."
That filter is too narrow — bucket B/A_lucky represents 72 items but R20-wrong universe
(math_correct=='False') is 187 items. The expanded residual produces a workable target;
the literal filter produces only 3 items with rescue-potential signal.

This script uses math_correct=='False' as the R20-wrong universe.

Output:
- submission/csvs/picks/kitchensink_target_set.csv
- submission/csvs/picks/kitchensink_target_ids.txt
"""

import csv
import io
import json
from pathlib import Path


def main():
    repo_root = Path(__file__).parent.parent.parent
    
    # ---- Load R20 analysis ----
    r20_csv = repo_root / 'inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/analysis/analysis.csv'
    lines = [l for l in open(r20_csv) if not l.startswith('#')]
    rdr = csv.DictReader(io.StringIO(''.join(lines)))
    r20_rows = list(rdr)
    
    # ---- Load private items metadata ----
    items = {json.loads(l)['id']: json.loads(l) for l in open(repo_root / 'private.jsonl')}
    
    # ---- Load exclusions ----
    thunder_118 = set()
    with open(repo_root / 'submission/csvs/picks/thinking_probe_target_set.csv') as f:
        for r in csv.DictReader(f):
            thunder_118.add(int(r['id']))
    
    nt13 = set()
    with open(repo_root / 'submission/csvs/picks/overrides_nothinking_join_conservative.csv') as f:
        for r in csv.DictReader(f):
            nt13.add(int(r.get('id') or r.get('item_id') or list(r.values())[0]))
    
    # HIGH-confidence per_item_overrides (already covered by Tier-1 normalizer + Pick A locked)
    high_overrides = set()
    with open(repo_root / 'postprocessing/per_item_overrides.csv') as f:
        for r in csv.DictReader(f):
            high_overrides.add(int(r['id']))
    
    print(f"Inputs: {len(r20_rows)} R20 rows, Thunder118={len(thunder_118)}, NT-13={len(nt13)}, HIGH-overrides={len(high_overrides)}")
    
    # ---- Step 1: residual universe (R20-wrong, NOT in Thunder118, NOT in NT-13, NOT in HIGH overrides) ----
    # OPERATIONAL: use math_correct=='False' instead of literal bucket B/A_lucky
    # OPERATIONAL: also exclude HIGH overrides (already handled by Tier-1 normalizer)
    residual = [
        r for r in r20_rows
        if r['math_correct'] == 'False'
        and int(r['item_id']) not in thunder_118
        and int(r['item_id']) not in nt13
        and int(r['item_id']) not in high_overrides
    ]
    print(f"Step 1: R20-wrong residual (excluding Thunder118, NT-13, HIGH-overrides) = {len(residual)}")
    
    # ---- Step 2: compute rescue-potential signal per item ----
    candidates = []
    for r in residual:
        iid = int(r['item_id'])
        item = items.get(iid, {})
        
        top_vote = int(r['sc_vote_size']) if r['sc_vote_size'] else None
        # vote_margin requires second-place vote count, which isn't in this CSV.
        # Use top<=5 alone as close_vote signal (margin requires raw samples; defer).
        close_vote = top_vote is not None and top_vote <= 5
        
        is_multi_slot = (
            (item.get('question', '').count('[ANS]') >= 2)
            or (r['category'] == 'free_multi')
        )
        multi_slot_precision_risk = is_multi_slot
        
        if close_vote or multi_slot_precision_risk:
            candidates.append({
                'id': iid,
                'reason_close_vote': close_vote,
                'reason_multi_slot_precision': multi_slot_precision_risk,
                'top_vote_count': top_vote if top_vote is not None else '',
                'second_vote_count': '',  # not available in analysis CSV
                'vote_margin': '',  # not available without raw samples
                'r20_bucket': r['bucket'],
                'gold_source': r['gold_source'],
                'in_thunder118': False,
                'in_nt13': False,
                'category': r['category'],
                'gold_independent_flag': r['gold_independent_flag'],
            })
    
    print(f"Step 2-3: items with rescue-potential signal = {len(candidates)}")
    
    # ---- Step 4: cap at 40, priority rank ----
    # Priority: smallest vote_margin (proxy: lowest top_vote_count), then close_vote, then multi_slot, then independent-gold
    def priority_key(c):
        return (
            int(c['top_vote_count']) if c['top_vote_count'] else 9,  # lower vote count first
            0 if c['reason_close_vote'] else 1,  # close_vote first
            0 if c['reason_multi_slot_precision'] else 1,  # multi_slot second
            0 if c['gold_source'] in ('wolfram_HIGH', 'search_GOLD', 'unanimous_teachers') else 1,  # independent-gold first
        )
    
    candidates.sort(key=priority_key)
    final = candidates[:40]
    print(f"Step 4: capped at 40, final = {len(final)} items")
    
    # ---- Stats ----
    indep_gold = [c for c in final if c['gold_source'] in ('wolfram_HIGH', 'search_GOLD', 'unanimous_teachers')]
    print(f"  Intersection with independent-gold: {len(indep_gold)} items")
    print(f"  -> stop rule mode: {'+2 standard' if len(indep_gold) >= 20 else '+1 with zero regressions (size-aware amendment, subset<20)'}")
    
    # ---- Step 5: write outputs ----
    target_csv = repo_root / 'submission/csvs/picks/kitchensink_target_set.csv'
    target_ids = repo_root / 'submission/csvs/picks/kitchensink_target_ids.txt'
    
    with open(target_csv, 'w', newline='') as f:
        fieldnames = ['id', 'reason_close_vote', 'reason_multi_slot_precision', 
                     'top_vote_count', 'second_vote_count', 'vote_margin',
                     'r20_bucket', 'gold_source', 'in_thunder118', 'in_nt13',
                     'category', 'gold_independent_flag']
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for c in final:
            w.writerow(c)
    
    with open(target_ids, 'w') as f:
        for c in final:
            f.write(f"{c['id']}\n")
    
    print(f"\nWrote: {target_csv}")
    print(f"Wrote: {target_ids}")
    print(f"\nFirst 10 target ids: {[c['id'] for c in final[:10]]}")


if __name__ == '__main__':
    main()
