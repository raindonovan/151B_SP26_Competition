#!/usr/bin/env python3
"""
Build a comprehensive non-LFS audit CSV combining tnr-0 + tnr-1 Thunder probe results
with R20 baseline + gold metadata. Designed to unblock Cursor's audit when LFS files
are not accessible.

Output: inference/base_model/audit/thunder_combined_audit.csv
"""

import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, '.')
from grading.grader import Grader

REPO = Path(__file__).parent.parent.parent

def main():
    g = Grader()
    
    # Load private items metadata
    items_meta = {}
    for line in open(REPO / 'private.jsonl'):
        item = json.loads(line)
        items_meta[item['id']] = item
    
    # Load R20 analysis
    lines = [l for l in open(REPO / 'inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/analysis/analysis.csv') if not l.startswith('#')]
    r20 = {int(r['item_id']): r for r in csv.DictReader(io.StringIO(''.join(lines)))}
    
    # Load both Thunder boxes
    thunder = {}  # iid -> {'box': 'tnr0'|'tnr1', 'data': record}
    for box, path in [
        ('tnr0', 'inference/base_model/thinking_probe_tnr0_20260531T065751Z/samples.jsonl'),
        ('tnr1', 'inference/base_model/thinking_probe_tnr1_20260531T065534Z/samples.jsonl'),
    ]:
        for line in open(REPO / path):
            r = json.loads(line)
            thunder[r['id']] = {'box': box, 'data': r}
    
    # Build per-item rows
    rows = []
    for iid, entry in thunder.items():
        box = entry['box']
        t = entry['data']
        r20_row = r20.get(iid, {})
        item = items_meta.get(iid, {})
        options = item.get('options') or []
        is_mcq = bool(options)
        is_multi_slot = (item.get('question', '').count('[ANS]') >= 2) or (r20_row.get('category') == 'free_multi')
        
        thunder_ans = t.get('voted_answer', '')
        thunder_votes = t.get('votes', 0)
        thunder_n_voting = t.get('n_voting', 16)
        sample_extracted = t.get('sample_extracted', [])
        sample_n_tokens = t.get('sample_n_output_tokens', [])
        n_unique_answers = len(set(str(s).strip() for s in sample_extracted if s is not None))
        avg_tokens = (sum(sample_n_tokens) / len(sample_n_tokens)) if sample_n_tokens else 0
        max_tokens = max(sample_n_tokens) if sample_n_tokens else 0
        
        r20_ans = r20_row.get('extracted_answer', '')
        r20_correct = (r20_row.get('math_correct') == 'True')
        r20_vote_size = int(r20_row['sc_vote_size']) if r20_row.get('sc_vote_size','').strip() else 0
        gold = r20_row.get('gold_answer', '')
        gold_source = r20_row.get('gold_source', '')
        indep_gold = gold_source in ('wolfram_HIGH', 'search_GOLD', 'unanimous_teachers')
        
        # Compute Thunder correctness (only valid for indep-gold; multi-slot grader caveat noted)
        thunder_correct = None
        grader_match_kind = ''
        if indep_gold and gold:
            try:
                thunder_correct = g.is_equal(thunder_ans, gold, options=options)
                # Flag potential false-positive multi-slot match: if gold has commas and
                # thunder_ans doesn't, and gold has 3+ comma slots
                gold_slots = [s.strip() for s in gold.split(',') if s.strip()]
                ans_slots = [s.strip() for s in str(thunder_ans).split(',') if s.strip()]
                if thunder_correct and len(gold_slots) >= 3 and len(ans_slots) == 1:
                    grader_match_kind = 'POSSIBLE_MULTI_SLOT_FALSE_POSITIVE'
                elif thunder_correct:
                    grader_match_kind = 'CONFIRMED'
            except Exception as e:
                thunder_correct = None
                grader_match_kind = f'ERROR:{type(e).__name__}'
        
        # Rescue status
        rescue_status = ''
        if not r20_correct and thunder_correct == True:
            rescue_status = 'RESCUED'
        elif not r20_correct and thunder_correct == False:
            rescue_status = 'MISSED'
        elif r20_correct and thunder_correct == False:
            rescue_status = 'REGRESSED'
        elif r20_correct and thunder_correct == True:
            rescue_status = 'KEPT'
        elif indep_gold:
            rescue_status = 'INDETERMINATE'
        # else: unmeasurable (sheet_dependent)
        
        # Answer-change vs R20
        answer_changed = (str(thunder_ans).strip() != str(r20_ans).strip())
        
        # Vote concentration buckets
        vote_bucket = 'strong' if thunder_votes >= 10 else ('weak' if thunder_votes >= 4 else 'single')
        
        rows.append({
            'id': iid,
            'box': box,
            'category': r20_row.get('category', ''),
            'tier': r20_row.get('tier', ''),
            'is_mcq': is_mcq,
            'is_multi_slot': is_multi_slot,
            'gold': gold,
            'gold_source': gold_source,
            'indep_gold': indep_gold,
            'r20_extracted_answer': r20_ans,
            'r20_correct': r20_correct,
            'r20_sc_vote_size': r20_vote_size,
            'thunder_voted_answer': thunder_ans,
            'thunder_votes': thunder_votes,
            'thunder_n_voting': thunder_n_voting,
            'thunder_vote_bucket': vote_bucket,
            'thunder_n_unique_answers': n_unique_answers,
            'thunder_avg_tokens': round(avg_tokens, 1),
            'thunder_max_tokens': max_tokens,
            'thunder_correct': thunder_correct,
            'grader_match_kind': grader_match_kind,
            'rescue_status': rescue_status,
            'answer_changed_from_r20': answer_changed,
            # All 16 per-sample extracted answers, JSON-stringified (no newlines)
            'sample_extracted_json': json.dumps(sample_extracted, ensure_ascii=True),
        })
    
    # Sort: by box, then by rescue_status priority (RESCUED first), then by id
    status_priority = {'RESCUED': 0, 'REGRESSED': 1, 'KEPT': 2, 'MISSED': 3, 'INDETERMINATE': 4, '': 5}
    rows.sort(key=lambda r: (r['box'], status_priority.get(r['rescue_status'], 9), r['id']))
    
    # Write CSV
    out_dir = REPO / 'inference/base_model/audit'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'thunder_combined_audit.csv'
    
    fieldnames = list(rows[0].keys())
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)  # all fields quoted, no embedded-newline risk
        w.writeheader()
        for r in rows:
            w.writerow(r)
    
    # Summary stats
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes, {len(rows)} rows)")
    print()
    print("Combined Thunder summary:")
    print(f"  Total items: {len(rows)}")
    print(f"  By box: tnr0={sum(1 for r in rows if r['box']=='tnr0')}, tnr1={sum(1 for r in rows if r['box']=='tnr1')}")
    print(f"  Independent-gold subset (measurable): {sum(1 for r in rows if r['indep_gold'])}")
    print()
    print(f"  Rescue status distribution: {dict(Counter(r['rescue_status'] for r in rows))}")
    print(f"  Vote concentration: {dict(Counter(r['thunder_vote_bucket'] for r in rows))}")
    print(f"  Grader match kind: {dict(Counter(r['grader_match_kind'] for r in rows if r['grader_match_kind']))}")
    print()
    print(f"  Answer-changed from R20: {sum(1 for r in rows if r['answer_changed_from_r20'])}/{len(rows)}")
    print(f"  Strong-vote rescues (≥10): {sum(1 for r in rows if r['rescue_status']=='RESCUED' and r['thunder_votes']>=10)}")
    print(f"  Possible multi-slot false-positives: {sum(1 for r in rows if r['grader_match_kind']=='POSSIBLE_MULTI_SLOT_FALSE_POSITIVE')}")

if __name__ == '__main__':
    main()
