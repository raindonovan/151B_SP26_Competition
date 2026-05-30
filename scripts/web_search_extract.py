#!/usr/bin/env python3
"""web_search_extract — fail-closed answer sheet from the web_search retrieval table.

Reads data/search/web_search/regular_search/search_results.csv READ-ONLY and the
private.jsonl item records, and produces two mutually-exclusive sheets over the
74-row answered universe (search_status in {GOLD, PARTIAL}):
  data/search/web_search/web_search_answer_sheet.csv  (promoted)
  data/search/web_search/web_search_residual.csv      (skipped + reason)

Screen-then-promote pipeline (round-3 spec, D1 value-equality baked in):
  Phase 0  structural screen (partial / forbidden source / low conf / understock)
  Phase 1A MCQ exact option-string equality (dominant path)
  Phase 1B clean_letter MCQ
  Phase 1C clean FREE (numeric / other)
  Phase 2  numeric MCQ fallback (value-equality via vals_equal)
  Phase 3  list-equality fallback (defensive)

Re-uses ONLY shared primitives from gold_equiv (_slots, _to_exact, vals_equal,
load_records) and annotation_verdict from wolfram_extract.
"""
import csv, hashlib, re, sys

sys.path.insert(0, '.')
from gold_equiv import _slots, _to_exact, vals_equal, load_records
from wolfram_extract import annotation_verdict

SEARCH = 'data/search/web_search/regular_search/search_results.csv'
PRIV = 'private.jsonl'
OUT_SHEET = 'data/search/web_search/web_search_answer_sheet.csv'
OUT_RESID = 'data/search/web_search/web_search_residual.csv'

FORBIDDEN = ['huggingface', 'proofrank', 'rimo', 'judgebench', 'ai-mo',
             '/olympiads', 'apex', 'aimo', 'dataset_card']
WEAK_IDS = {'0097', '0263', '0778'}
MCQ_LETTERSET_RE = re.compile(r'^[A-Z](,[A-Z])*$')

PROMO_ENUM = {'clean_value_numeric', 'clean_value_other', 'clean_letter',
              'mcq_exact_option_match', 'mcq_letter_mapped_numeric', 'mcq_letter_mapped_list'}
SKIP_ENUM = {'partial_classification', 'forbidden_source', 'low_confidence',
             'multi_slot_understocked', 'mcq_options_missing_or_invalid',
             'mcq_options_not_numeric', 'mcq_answer_not_numeric', 'mcq_no_match',
             'mcq_ambiguous', 'mcq_exact_match_ambiguous', 'mcq_answer_not_numeric_list',
             'mcq_list_no_match', 'mcq_list_ambiguous', 'free_unrecognized_form'}


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def _id4(x):
    return str(int(str(x).strip())).zfill(4)


def conf_pass(c):
    cl = str(c).strip().lower()
    if cl == 'high':
        return True
    try:
        return float(c) >= 90
    except (ValueError, TypeError):
        return False


def forbidden_url(url):
    u = (url or '').lower()
    return any(sub in u for sub in FORBIDDEN)


def valid_options(rec):
    opts = (rec or {}).get('options')
    if isinstance(opts, list) and len(opts) >= 2 \
       and all(isinstance(o, str) and o.strip() for o in opts):
        return opts
    return None


def stored_slot_count(answer, category):
    if category == 'MCQ' and re.match(r'^[A-Z](,[A-Z])*$', answer):
        return answer.count(',') + 1
    if category == 'MCQ':
        return 1
    return len(_slots(answer))


def _norm(s):
    return re.sub(r'\s+', ' ', str(s)).strip()


def phase2_ws(answer, rec):
    """Numeric MCQ fallback (value-equality). ('promote', letter) | ('residual', reason)."""
    opts = valid_options(rec)
    if opts is None:
        return ('residual', 'mcq_options_missing_or_invalid')
    letters = [chr(ord('A') + i) for i in range(len(opts))]
    opt_vals = [_to_exact(o) for o in opts]
    if any(v is None for v in opt_vals):
        return ('residual', 'mcq_options_not_numeric')
    w = _to_exact(answer)
    if w is None:
        return ('residual', 'mcq_answer_not_numeric')
    hits = [letters[i] for i, ov in enumerate(opt_vals) if vals_equal(w, ov)]
    if len(hits) == 1:
        return ('promote', hits[0])
    if len(hits) == 0:
        return ('residual', 'mcq_no_match')
    return ('residual', 'mcq_ambiguous')


def phase3_ws(answer, rec):
    """List-equality fallback (defensive). ('promote', letter) | ('residual', reason)."""
    opts = valid_options(rec)
    if opts is None:
        return ('residual', 'mcq_options_missing_or_invalid')
    letters = [chr(ord('A') + i) for i in range(len(opts))]
    ans_vals = [_to_exact(s) for s in _slots(answer)]
    if any(v is None for v in ans_vals):
        return ('residual', 'mcq_answer_not_numeric_list')
    hits = []
    for i, opt in enumerate(opts):
        opt_slots = _slots(opt)
        if len(opt_slots) != len(ans_vals):
            continue
        opt_vals = [_to_exact(s) for s in opt_slots]
        if any(v is None for v in opt_vals):
            continue
        if all(vals_equal(a, b) for a, b in zip(ans_vals, opt_vals)):
            hits.append(letters[i])
    if len(hits) == 1:
        return ('promote', hits[0])
    if len(hits) == 0:
        return ('residual', 'mcq_list_no_match')
    return ('residual', 'mcq_list_ambiguous')


def classify(row, rec):
    """Return ('sheet', promotion_class, answer) | ('residual', skip_reason)."""
    status = (row['search_status'] or '').strip().upper()
    cat = (row['category'] or '').strip().upper()
    answer = (row['found_answer'] or '').strip()
    conf = row['confidence']

    # --- Phase 0 structural screen (first-hit wins) ---
    if status == 'PARTIAL':
        return ('residual', 'partial_classification')
    if forbidden_url(row['source_url']):
        return ('residual', 'forbidden_source')
    if not conf_pass(conf):
        return ('residual', 'low_confidence')
    nq = (rec or {}).get('question', '').count('[ANS]')
    na = stored_slot_count(answer, cat)
    if nq >= 2 and na < nq:
        return ('residual', 'multi_slot_understocked')

    # --- MCQ paths ---
    if cat == 'MCQ':
        opts = valid_options(rec)
        # Phase 1A exact option-string equality (dominant)
        if opts is not None:
            letters = [chr(ord('A') + i) for i in range(len(opts))]
            hits = [letters[i] for i, o in enumerate(opts) if _norm(o) == _norm(answer)]
            if len(hits) == 1:
                return ('sheet', 'mcq_exact_option_match', hits[0])
            if len(hits) > 1:
                return ('residual', 'mcq_exact_match_ambiguous')
            # len 0 -> fall through
        # Phase 1B clean_letter
        if MCQ_LETTERSET_RE.match(answer):
            letter = ','.join(sorted(answer.split(','))) if ',' in answer else answer
            return ('sheet', 'clean_letter', letter)
        # Phase 2 numeric MCQ fallback
        res, val = phase2_ws(answer, rec)
        if res == 'promote':
            return ('sheet', 'mcq_letter_mapped_numeric', val)
        reason2 = val
        # Phase 3 list-equality fallback (only if >=2 slots)
        if len(_slots(answer)) >= 2:
            res3, val3 = phase3_ws(answer, rec)
            if res3 == 'promote':
                return ('sheet', 'mcq_letter_mapped_list', val3)
            return ('residual', val3)
        return ('residual', reason2)

    # --- FREE path: Phase 1C ---
    if _to_exact(answer) is not None:
        return ('sheet', 'clean_value_numeric', answer)
    slots = _slots(answer)
    slot_count_ok = (na == nq) if nq >= 1 else (len(slots) >= 1)
    if slot_count_ok and slots and all(annotation_verdict(s) is None for s in slots):
        return ('sheet', 'clean_value_other', answer)
    return ('residual', 'free_unrecognized_form')


# --- smoke gate -----------------------------------------------------------
WS_SMOKE_PROMO = {
    '0007': 'clean_value_numeric',
    '0041': 'clean_value_numeric',   # answer '2112'
    '0097': 'clean_value_other',     # source_quality weak
    '0184': 'clean_letter',
    '0125': 'mcq_exact_option_match',
    '0175': 'mcq_exact_option_match',
    '0182': 'mcq_exact_option_match',
}
WS_SMOKE_PROMO_EITHER = {'0017': {'mcq_exact_option_match', 'mcq_letter_mapped_numeric'}}
WS_SMOKE_ANSWER = {'0041': '2112'}
WS_SMOKE_RESID = {
    '0265': 'multi_slot_understocked',
    '0492': 'multi_slot_understocked',
    '0045': 'low_confidence',
    '0091': 'low_confidence',
    '0047': 'low_confidence',
    '0200': 'low_confidence',
    '0567': 'low_confidence',
    '0813': 'low_confidence',
    '0060': 'partial_classification',
}
WS_NEG_EXACT = ['0175', '0255', '0329', '0405', '0805']   # must be mcq_exact_option_match
PHASE1A_COVERAGE = ['0125', '0175', '0182', '0255', '0329', '0405', '0805']


def main():
    sha_search_start = sha(SEARCH)
    print('== provenance ==')
    print('search_results.csv sha256:', sha_search_start)

    rows = list(csv.DictReader(open(SEARCH, newline='')))
    universe = [r for r in rows
                if (r['search_status'] or '').strip().upper() in {'GOLD', 'PARTIAL'}]
    print('answered universe (GOLD|PARTIAL):', len(universe))

    records = load_records(PRIV)

    sheet_rows, resid_rows = [], []
    promo_counts, skip_counts = {}, {}
    route_map = {}   # id4 -> ('sheet', pc, answer) | ('residual', reason)

    for row in universe:
        rid = _id4(row['item_id'])
        rec = records.get(rid)
        verdict = classify(row, rec)

        if verdict[0] == 'sheet':
            _dest, pc, ans = verdict
            sq = 'weak' if rid in WEAK_IDS else 'strong'
            sheet_rows.append({
                'id': rid, 'answer': ans, 'category': (row['category'] or '').strip(),
                'confidence': row['confidence'], 'promotion_class': pc,
                'source_quality': sq, 'source_type': row['source_type'],
                'source_url': row['source_url'], 'source_found_answer': row['found_answer'],
                'source_notes': row['notes'],
            })
            promo_counts[pc] = promo_counts.get(pc, 0) + 1
            route_map[rid] = ('sheet', pc, ans)
        else:
            reason = verdict[1]
            resid_rows.append({
                'id': rid, 'category': (row['category'] or '').strip(),
                'confidence': row['confidence'], 'skip_reason': reason,
                'source_found_answer': row['found_answer'], 'source_url': row['source_url'],
                'source_type': row['source_type'], 'source_notes': row['notes'],
            })
            skip_counts[reason] = skip_counts.get(reason, 0) + 1
            route_map[rid] = ('residual', reason)

    # --- smoke gate (BEFORE acceptance / write) --------------------------
    print('\n== web_search smoke gate ==')
    smoke_fail = []

    def _check(sid, want_dest, want, extra=''):
        got = route_map.get(sid)
        if got is None:
            smoke_fail.append(f'{sid}: not in universe')
            print(f'  [FAIL] {sid}: not found'); return
        ok = got[0] == want_dest
        if want_dest == 'sheet':
            if isinstance(want, set):
                ok = ok and got[1] in want
            else:
                ok = ok and got[1] == want
            if ok and sid in WS_SMOKE_ANSWER:
                ok = got[2] == WS_SMOKE_ANSWER[sid]
            if ok and sid in WEAK_IDS:
                sqrow = next((r for r in sheet_rows if r['id'] == sid), None)
                ok = sqrow is not None and sqrow['source_quality'] == 'weak'
        else:
            ok = ok and got[1] == want
        det = f'{got[0]}/{got[1]}' + (f' ans={got[2]}' if got[0] == 'sheet' else '')
        print(f'  [{"PASS" if ok else "FAIL"}] {sid}: {det}  (want {want_dest}/{want}){extra}')
        if not ok:
            smoke_fail.append(f'{sid}: got {got}, want {want_dest}/{want}')

    for sid, pc in WS_SMOKE_PROMO.items():
        _check(sid, 'sheet', pc)
    for sid, pcset in WS_SMOKE_PROMO_EITHER.items():
        _check(sid, 'sheet', pcset)
    for sid, rs in WS_SMOKE_RESID.items():
        _check(sid, 'residual', rs)
    for sid in WS_NEG_EXACT:
        _check(sid, 'sheet', 'mcq_exact_option_match', extra=' [neg-ctrl]')

    # --- acceptance (10 checks) ------------------------------------------
    sheet_ids = {r['id'] for r in sheet_rows}
    resid_ids = {r['id'] for r in resid_rows}
    univ_ids = {_id4(r['item_id']) for r in universe}

    understock_in_sheet = sum(1 for r in resid_rows if False)  # placeholder, see check 4
    sheet_understock = 0
    for r in sheet_rows:
        rec = records.get(r['id'])
        nq = (rec or {}).get('question', '').count('[ANS]')
        na = stored_slot_count((r['source_found_answer'] or '').strip(), r['category'].strip().upper())
        if nq >= 2 and na < nq:
            sheet_understock += 1
    conf_bad = sum(1 for r in sheet_rows if not conf_pass(r['confidence']))
    mcq_bad = 0
    for r in sheet_rows:
        if (r['category'] or '').strip().upper() == 'MCQ':
            a = r['answer']
            if not MCQ_LETTERSET_RE.match(a):
                mcq_bad += 1
            elif ',' in a and list(a.split(',')) != sorted(a.split(',')):
                mcq_bad += 1
    promo_enum_bad = sum(1 for r in sheet_rows if r['promotion_class'] not in PROMO_ENUM)
    skip_enum_bad = sum(1 for r in resid_rows if r['skip_reason'] not in SKIP_ENUM or not r['skip_reason'])
    cov_bad = [sid for sid in PHASE1A_COVERAGE
               if route_map.get(sid, (None, None))[:2] != ('sheet', 'mcq_exact_option_match')]
    sha_search_end = sha(SEARCH)
    sha_unchanged = sha_search_end == sha_search_start

    checks = [
        ('1 total==74', len(sheet_rows) + len(resid_rows) == 74, len(sheet_rows) + len(resid_rows)),
        ('2 disjoint', sheet_ids.isdisjoint(resid_ids), len(sheet_ids & resid_ids)),
        ('3 union==universe', (sheet_ids | resid_ids) == univ_ids, len(sheet_ids | resid_ids)),
        ('4 no understocked in sheet', sheet_understock == 0, sheet_understock),
        ('5 sheet conf>=90 or high', conf_bad == 0, conf_bad),
        ('6 MCQ sheet letterset+sorted', mcq_bad == 0, mcq_bad),
        ('7 promotion_class enum closed', promo_enum_bad == 0, promo_enum_bad),
        ('8 skip_reason enum closed', skip_enum_bad == 0, skip_enum_bad),
        ('9 Phase1A coverage', len(cov_bad) == 0, cov_bad or 'all 7 exact'),
        ('10 source SHA unchanged', sha_unchanged, sha_unchanged),
    ]

    print('\n== fail-closed acceptance ==')
    all_pass = True
    for name, ok, val in checks:
        print(f'  [{"PASS" if ok else "FAIL"}] {name} (value={val})')
        all_pass = all_pass and ok

    print('\n== promotion_class counts ==')
    for k in sorted(promo_counts):
        print(f'  {k}: {promo_counts[k]}')
    print('== skip_reason counts ==')
    for k in sorted(skip_counts):
        print(f'  {k}: {skip_counts[k]}')
    print(f'\npromoted total={len(sheet_rows)}  residual total={len(resid_rows)}')

    stop = []
    if smoke_fail:
        stop.append(f'{len(smoke_fail)} smoke misroute(s)')
    if not all_pass:
        stop.append('a fail-closed check failed')
    if len(sheet_rows) < 40:
        stop.append(f'promoted {len(sheet_rows)} < 40')
    if not sha_unchanged:
        stop.append('source SHA changed mid-run')

    if stop:
        print('\n*** STOP — NOT WRITING OUTPUTS ***')
        for s in stop:
            print('  -', s)
        for s in smoke_fail:
            print('   smoke:', s)
        sys.exit(1)

    _write_sheet(sheet_rows)
    _write_resid(resid_rows)
    print('\nWROTE', OUT_SHEET, 'and', OUT_RESID)
    return sha_search_end


def _write_sheet(rows):
    cols = ['id', 'answer', 'category', 'confidence', 'promotion_class', 'source_quality',
            'source_type', 'source_url', 'source_found_answer', 'source_notes']
    with open(OUT_SHEET, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\r\n')
        w.writeheader()
        for r in sorted(rows, key=lambda r: r['id']):
            w.writerow(r)


def _write_resid(rows):
    cols = ['id', 'category', 'confidence', 'skip_reason', 'source_found_answer',
            'source_url', 'source_type', 'source_notes']
    with open(OUT_RESID, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\r\n')
        w.writeheader()
        for r in sorted(rows, key=lambda r: r['id']):
            w.writerow(r)


if __name__ == '__main__':
    main()
