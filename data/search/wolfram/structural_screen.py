"""structural_screen.py — Stage 1 of the screen-then-normalize pipeline.

Operates RAW on WOLF_RESULTS.csv DONE rows. Identifies structural defects that
normalization must NEVER paper over, and buckets every DONE row:

  BUCKET 1  structurally invalid     -> do NOT normalize (data-quality problem)
  BUCKET 2  structurally valid       -> normalize + compare (normalizer's job)
  BUCKET 3  convention-sensitive     -> normalize for inspection only, no auto-promote

Self-contained: needs no reference signal. Structure is judged on the Wolfram
answer's own surface + the declared type/slot-count + the question text (for
convention sensitivity). Prints examples so every classification is auditable.
"""
import csv, json, re, sys
sys.path.insert(0, 'scripts')
from gold_equiv import _slots, _is_letter

ROWS = [r for r in csv.DictReader(open('data/search/wolfram/WOLF_RESULTS.csv'))
        if r['wolfram_status'] == 'DONE']
Q = {}
for line in open('private.jsonl'):
    d = json.loads(line); Q[str(d['id']).zfill(4)] = d['question']

# prose / non-final-answer markers (free types only). Deliberately conservative.
PROSE = re.compile(r'\b(form|outlier|undefined|INCONCLUSIVE|see|note|approx|hint|'
                   r'unknown|where|is an|are |the answer|consensus)\b', re.I)

def clean_letter_set(a):
    parts = [p.strip() for p in a.split(',')]
    return len(parts) >= 1 and all(_is_letter(p) for p in parts)

invalid, conv, valid = {}, {}, []
def tag(d, k, rid): d.setdefault(k, []).append(rid)

for r in ROWS:
    a, t, ns, rid = r['wolfram_answer'].strip(), r['type'], r['n_ans_slots'], r['id']
    qt = Q.get(rid, '')
    bad = False
    # 1. MCQ storing a derived value instead of an option letter (grader wants a LETTER)
    if t == 'MCQ' and not clean_letter_set(a):
        tag(invalid, 'mcq_stores_value', rid); bad = True
    # 2. ellipsis / question-mark / open uncertainty in the answer surface
    if '...' in a or '\u2026' in a or '?' in a:
        tag(invalid, 'ellipsis_or_qmark', rid); bad = True
    # 3. prose / explanation instead of a final answer (non-MCQ)
    if t != 'MCQ' and PROSE.search(a):
        tag(invalid, 'prose_or_nonanswer', rid); bad = True
    # 4. free_multi declared-vs-actual slot-count mismatch (incomplete/over-packed)
    if t == 'free_multi':
        try: nsi = int(ns)
        except: nsi = 0
        if nsi > 0 and len(_slots(a)) != nsi:
            tag(invalid, 'slot_count_mismatch', rid); bad = True
    # convention-sensitive (structurally fine, but answer depends on an unstated convention)
    cv = False
    if re.search(r'\bvariance\b|standard deviation', qt, re.I) and \
       not re.search(r'sample (variance|standard)', qt, re.I):
        tag(conv, 'variance_pop_vs_sample', rid); cv = True
    if re.search(r'\bround|decimal place|nearest\b', qt, re.I):
        tag(conv, 'rounding_sensitive', rid); cv = True
    if not bad and not cv:
        valid.append(rid)

ALL_INV = {x for v in invalid.values() for x in v}
ALL_CONV = {x for v in conv.values() for x in v}

if __name__ == '__main__':
    print(f'DONE rows screened: {len(ROWS)}')
    print(f'\nBUCKET 1 — structurally INVALID (do NOT normalize): {len(ALL_INV)} unique')
    for k, v in sorted(invalid.items(), key=lambda kv: -len(kv[1])):
        print(f'   {k:22} {len(v):4}   e.g. {v[:10]}')
    print(f'\nBUCKET 3 — convention-sensitive, inspect-only (excl. already-invalid): '
          f'{len(ALL_CONV - ALL_INV)} unique')
    for k, v in sorted(conv.items(), key=lambda kv: -len(kv[1])):
        vv = [x for x in v if x not in ALL_INV]
        print(f'   {k:22} {len(vv):4}   e.g. {vv[:10]}')
    print(f'\nBUCKET 2 — structurally valid -> normalize + compare: {len(valid)}')
    # dump bucket membership for the next stage
    json.dump({'invalid': sorted(ALL_INV), 'invalid_by_class': invalid,
               'convention': sorted(ALL_CONV - ALL_INV), 'conv_by_class': conv,
               'valid': valid},
              open('/home/claude/screen_buckets.json', 'w'), indent=0)
