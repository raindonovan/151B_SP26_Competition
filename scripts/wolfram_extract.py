#!/usr/bin/env python3
"""wolfram_extract — derive a fail-closed answer sheet from the Wolfram audit.

Reads the raw audit table READ-ONLY and produces two mutually-exclusive sheets
over the frozen 477-id DONE universe:
  data/search/wolfram/wolfram_alpha_answer_sheet.csv  (promoted rows)
  data/search/wolfram/wolfram_alpha_residual.csv      (skipped rows + reason)

Round-3 (claude_strategy spec):
  FIX 1 — annotation predicate is per-slot with an interval pre-check
          (looks_like_interval) and a math-token whitelist (MATH_TOKENS);
          unbalanced parens fail CLOSED to 'syntax_unparseable'.
  FIX 2 — the regex option parser is dropped; MCQ mapping uses the structured
          `options` list from private.jsonl (via load_records) and value-exact
          comparison through _to_exact.

Fail-closed throughout: any structural doubt routes a row to residual rather
than promoting a wrong value. Re-uses ONLY `_slots`, `_to_number`, `_to_exact`,
`load_records` from scripts/gold_equiv.py (no re-implemented parsing).
"""
import csv, hashlib, re, sys

sys.path.insert(0, '.')
from gold_equiv import _slots, _to_number, _to_exact, load_records, vals_equal

WOLF = 'data/search/wolfram/WOLF_RESULTS.csv'
PRIV = 'private.jsonl'
OUT_SHEET = 'data/search/wolfram/wolfram_alpha_answer_sheet.csv'
OUT_RESID = 'data/search/wolfram/wolfram_alpha_residual.csv'

# --- universe / known sets ------------------------------------------------
KNOWN_DATASET_BUG = {'0011', '0317', '0570', '0585', '0622', '0858', '0894'}
# §5 of RESULTS_SUMMARY.md tags exactly 0542 as the F22 variance-convention item.
F22_IDS = {'0542'}
CONV_IDS = {'0542'} | F22_IDS
# Strategy ruling (2026-05-30, Option 3): hard-list the sentence/concept answers
# that Phase 0.8's token gate under-catches, routed to residual before the token
# check. Reversible; leaves the gate logic untouched. See FINDINGS Finding 25.
PROSE_OR_NONANSWER_EXPLICIT = {'0252', '0469', '0491', '0544', '0556', '0758'}

MARKERS = ('?', '...', '…')
NOTES_INCOMPLETE = ['undercount', 'missing', 'needs source', 'unknown', 'partial']
NOTES_INCOMPLETE_RE = re.compile(r'slot\s*\d+\s*(unknown|needs|missing)', re.I)
CONV_NOTES = ['convention-dependent', 'pop/sample', 'variance convention',
              'population vs sample']
# Phase 0.8 prose tokens (word-boundary, case-insensitive).
PROSE_TOKENS = ['in', 'is', 'are', 'the', 'an', 'and', 'or', 'with',
                'where', 'this', 'that', 'then', 'of']
PROSE_RE = re.compile(r'\b(' + '|'.join(PROSE_TOKENS) + r')\b', re.I)
MCQ_LETTERSET_RE = re.compile(r'^[A-Z](,[A-Z])*$')

# --- FIX 1: math-token whitelist + interval pre-check + per-slot predicate --
MATH_TOKENS = {
    # trig + inverse + hyperbolic
    'sin', 'cos', 'tan', 'sec', 'csc', 'cot',
    'sinh', 'cosh', 'tanh', 'sech', 'csch', 'coth',
    'arcsin', 'arccos', 'arctan', 'arccsc', 'arcsec', 'arccot',
    'asin', 'acos', 'atan',
    # log/exp
    'log', 'ln', 'lg', 'exp',
    # functions
    'sqrt', 'abs', 'floor', 'ceil', 'max', 'min', 'mod', 'lcm', 'gcd',
    'det', 'tr', 'rank', 'sgn', 'round',
    # named Greek
    'pi', 'phi', 'psi', 'chi', 'eta', 'mu', 'nu', 'xi', 'rho', 'tau', 'zeta',
    'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta', 'iota', 'kappa',
    'lambda', 'omicron', 'sigma', 'upsilon', 'omega',
    # LaTeX commands
    'frac', 'dfrac', 'tfrac', 'cdot', 'times', 'div', 'pm', 'mp', 'leq', 'geq',
    'neq', 'approx', 'equiv', 'infty', 'infin', 'infinity', 'inf', 'oo', 'sum',
    'prod', 'int', 'lim', 'partial', 'nabla', 'vec', 'hat', 'bar', 'tilde',
    'boxed', 'mathbb', 'mathcal', 'mathrm', 'mathbf', 'mathit',
    'left', 'right', 'displaystyle', 'overline', 'underline', 'overrightarrow',
    # set notation
    'union', 'cup', 'cap', 'intersect', 'subset', 'supset',
    # math keywords
    'undefined', 'dne', 'und', 'none', 'iff', 'iif',
    'imaginary', 'real', 'complex', 'rational', 'irrational',
}


def looks_like_interval(slot):
    s = slot.strip()
    if not s or s[0] not in '[(' or s[-1] not in '])':
        return False
    depth = 0
    has_top_level_comma = False
    for ch in s:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
            if depth < 0:
                return False
        elif ch == ',' and depth == 1:
            has_top_level_comma = True
    return depth == 0 and has_top_level_comma


def annotation_verdict(slot):
    """Returns 'annotation' | 'syntax_unparseable' | None (clean)."""
    s = slot.strip()
    if looks_like_interval(s):
        return None
    if not s.endswith(')'):
        return None
    depth = 0
    open_idx = -1
    for i in range(len(s) - 1, -1, -1):
        if s[i] == ')':
            depth += 1
        elif s[i] == '(':
            depth -= 1
            if depth == 0:
                open_idx = i
                break
    if open_idx == -1:
        return 'syntax_unparseable'   # fail CLOSED on unbalanced
    body = s[:open_idx].strip()
    inner = s[open_idx + 1:-1]
    if re.match(r'^[A-Z](,[A-Z])*$', body):
        return 'annotation'
    alpha_words = re.findall(r'[A-Za-z]{3,}', inner)
    if alpha_words and not all(w.lower() in MATH_TOKENS for w in alpha_words):
        return 'annotation'
    return None


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


# --- FIX 2: structured-options MCQ mapper --------------------------------
def phase2_map(row, jsonl_record):
    """Numeric-only MCQ mapper using the structured `options` list.
    Returns ('promote', letter) or ('residual', reason)."""
    opts = (jsonl_record or {}).get('options')
    if not isinstance(opts, list) or len(opts) < 2 \
       or not all(isinstance(o, str) and o.strip() for o in opts):
        return ('residual', 'mcq_options_missing_or_invalid')
    letters = [chr(ord('A') + i) for i in range(len(opts))]
    opt_vals = [_to_exact(o) for o in opts]
    if any(v is None for v in opt_vals):
        return ('residual', 'mcq_options_not_numeric')
    w = _to_exact(row['wolfram_answer'])
    if w is None:
        return ('residual', 'mcq_answer_not_numeric')
    hits = [letters[i] for i, ov in enumerate(opt_vals) if vals_equal(w, ov)]
    if len(hits) == 1:
        return ('promote', hits[0])
    if len(hits) == 0:
        return ('residual', 'mcq_no_match')
    return ('residual', 'mcq_ambiguous')


# --- Phase 0 structural screen -------------------------------------------
def structural_screen(row, question):
    """Return ('CLEAN', None) | ('PHASE2', None) | ('residual', reason)."""
    conf = (row['confidence'] or '').strip().upper()
    ans = (row['wolfram_answer'] or '').strip()
    notes = (row['notes'] or '')
    typ = (row['type'] or '').strip()
    rid = row['id']

    # 1
    if conf not in {'HIGH', 'MED'}:
        return ('residual', 'low_confidence')
    # 2
    if rid in KNOWN_DATASET_BUG:
        return ('residual', 'known_dataset_bug')
    # 3
    if any(mk in ans for mk in MARKERS):
        return ('residual', 'marker_in_answer')
    # 4 annotation contamination / syntax (FIX 1: per-slot, after _slots split,
    #   with interval pre-check; unbalanced parens fail closed)
    slots = _slots(ans) if typ == 'free_multi' else [ans]
    for slot in slots:
        v = annotation_verdict(slot)
        if v == 'annotation':
            return ('residual', 'annotation_contamination')
        if v == 'syntax_unparseable':
            return ('residual', 'syntax_unparseable')
    # 5
    nlow = notes.lower()
    if any(k in nlow for k in NOTES_INCOMPLETE) or NOTES_INCOMPLETE_RE.search(notes):
        return ('residual', 'notes_admit_incomplete')
    # 6
    if typ == 'free_multi':
        try:
            n_slots = int(row['n_ans_slots'])
        except (ValueError, TypeError):
            n_slots = -1
        if len(_slots(ans)) != n_slots:
            return ('residual', 'slot_mismatch')
    # 7 convention-sensitive (evidence union, in order)
    conv = False
    if rid in CONV_IDS:
        conv = True
    elif any(k in nlow for k in CONV_NOTES):
        conv = True
    elif question is not None and re.search(r'\bvariance\b|standard deviation', question, re.I) \
            and not re.search(r'sample\s+(variance|standard)', question, re.I):
        conv = True
    if conv:
        return ('residual', 'convention_sensitive')
    # 7.5 (strategy Option 3) explicit prose/non-answer hard-list — between
    # convention (7) and the token-based prose gate (8).
    if rid in PROSE_OR_NONANSWER_EXPLICIT:
        return ('residual', 'prose_or_nonanswer')
    # 8 prose / non-answer (free_single / free_multi only)
    if typ in {'free_single', 'free_multi'}:
        nonnum = False
        if typ == 'free_single':
            nonnum = _to_number(ans) is None
        else:  # free_multi
            nonnum = any(_to_number(s) is None for s in _slots(ans))
        if nonnum and PROSE_RE.search(ans):
            return ('residual', 'prose_or_nonanswer')
    # 9 MCQ not a clean letter-set -> Phase 2
    if typ == 'MCQ' and not MCQ_LETTERSET_RE.match(ans):
        return ('PHASE2', None)
    # else CLEAN
    return ('CLEAN', None)


# --- smoke gate (FIX-spec ids; STOP on any misroute) ----------------------
WOLF_SMOKE = {
    '0048': ('residual', 'annotation_contamination'),
    '0831': ('residual', 'annotation_contamination'),
    '0017': ('sheet', 'mcq_letter_mapped_numeric'),
    '0019': ('sheet', 'mcq_letter_mapped_numeric'),
    '0080': ('residual', 'mcq_ambiguous'),               # D1: value-equal hits {A,G} -> ambiguous
    '0267': ('residual', 'mcq_ambiguous'),               # D2 post-D1: 6 opts value-match -1/2 -> ambiguous
    '0001': ('residual', 'mcq_options_not_numeric'),
}
WOLF_SMOKE_ANSWER = {'0017': 'C', '0019': 'E'}
# FIX 3+4: 0114/0807 (symbolic MCQ, no symbolic phase) and 0297/0793 (convention-caught
# upstream, never reach annotation_verdict) dropped — they don't exercise the predicate.
WOLF_NEG = ['0218', '0841', '0323']

RESID_ENUM = {
    'notes_admit_incomplete', 'mcq_options_missing_or_invalid', 'low_confidence',
    'convention_sensitive', 'marker_in_answer', 'annotation_contamination',
    'prose_or_nonanswer', 'known_dataset_bug', 'slot_mismatch', 'syntax_unparseable',
    'mcq_options_not_numeric', 'mcq_answer_not_numeric', 'mcq_no_match', 'mcq_ambiguous',
}
PROMO_ENUM = {'clean_value', 'clean_letter', 'mcq_letter_mapped_numeric'}


def main():
    sha_wolf_start, sha_priv_start = sha(WOLF), sha(PRIV)
    print('== provenance ==')
    print('WOLF_RESULTS.csv sha256:', sha_wolf_start)
    print('private.jsonl    sha256:', sha_priv_start)

    rows = list(csv.DictReader(open(WOLF, newline='')))
    U = sorted((r for r in rows if (r['wolfram_status'] or '').strip() == 'DONE'),
               key=lambda r: r['id'])
    assert len(U) == 477, f'universe freeze FAILED: len(U)={len(U)} != 477'
    print('universe |U| =', len(U), '(frozen)')

    records = load_records(PRIV)

    sheet_rows, resid_rows = [], []
    promo_counts, skip_counts = {}, {}
    mapped_attempts, mapped_ambiguous = 0, 0
    route_map = {}   # rid -> ('sheet', promotion_class, answer) | ('residual', skip_reason)

    for row in U:
        rid = row['id']
        rec = records.get(rid)
        q = rec.get('question') if rec else None
        verdict, info = structural_screen(row, q)

        if verdict == 'residual':
            resid_rows.append(_resid(row, info))
            skip_counts[info] = skip_counts.get(info, 0) + 1
            route_map[rid] = ('residual', info)
            continue

        if verdict == 'PHASE2':
            mapped_attempts += 1
            res, val = phase2_map(row, rec)
            if res == 'promote':
                pc = 'mcq_letter_mapped_numeric'
                sheet_rows.append(_sheet(row, val, pc))
                promo_counts[pc] = promo_counts.get(pc, 0) + 1
                route_map[rid] = ('sheet', pc, val)
            else:
                if val == 'mcq_ambiguous':
                    mapped_ambiguous += 1
                resid_rows.append(_resid(row, val))
                skip_counts[val] = skip_counts.get(val, 0) + 1
                route_map[rid] = ('residual', val)
            continue

        # CLEAN -> Phase 1 promotion
        typ = (row['type'] or '').strip()
        ans = (row['wolfram_answer'] or '').strip()
        if typ == 'MCQ':
            pc = 'clean_letter'
            if ',' in ans:  # comma-letter-set -> sort ASCII-ascending
                ans = ','.join(sorted(ans.split(',')))
        else:
            pc = 'clean_value'
        sheet_rows.append(_sheet(row, ans, pc))
        promo_counts[pc] = promo_counts.get(pc, 0) + 1
        route_map[rid] = ('sheet', pc, ans)

    # --- smoke gate (BEFORE acceptance / write) --------------------------
    print('\n== wolfram smoke gate ==')
    smoke_fail = []
    for sid, (want_dest, want_reason) in WOLF_SMOKE.items():
        got = route_map.get(sid)
        if got is None:
            smoke_fail.append(f'{sid}: not in universe');
            print(f'  [FAIL] {sid}: not found'); continue
        got_dest = got[0]
        got_reason = got[1]
        ok = (got_dest == want_dest and got_reason == want_reason)
        if ok and sid in WOLF_SMOKE_ANSWER:
            ok = (got[2] == WOLF_SMOKE_ANSWER[sid])
        ans_note = f" answer={got[2]}" if got_dest == 'sheet' else ''
        print(f'  [{"PASS" if ok else "FAIL"}] {sid}: {got_dest}/{got_reason}{ans_note}'
              f'  (want {want_dest}/{want_reason}'
              + (f' ans={WOLF_SMOKE_ANSWER[sid]}' if sid in WOLF_SMOKE_ANSWER else '') + ')')
        if not ok:
            smoke_fail.append(f'{sid}: got {got_dest}/{got_reason}, want {want_dest}/{want_reason}')
    for nid in WOLF_NEG:
        got = route_map.get(nid)
        ok = got is not None and got[0] == 'sheet'
        print(f'  [{"PASS" if ok else "FAIL"}] NEG {nid}: {got[0] if got else "MISSING"}/{got[1] if got else "-"} (want sheet, no skip)')
        if not ok:
            smoke_fail.append(f'NEG {nid}: not in sheet (got {got})')

    # --- fail-closed acceptance (12 checks) ------------------------------
    sheet_ids = {r['id'] for r in sheet_rows}
    resid_ids = {r['id'] for r in resid_rows}
    U_ids = {r['id'] for r in U}

    def _pred_clean(answer, qtype):
        slots = _slots(answer) if qtype == 'free_multi' else [answer]
        return all(annotation_verdict(s) is None for s in slots)

    marker_bad = sum(1 for r in sheet_rows if any(m in r['answer'] for m in MARKERS))
    annot_bad = sum(1 for r in sheet_rows if not _pred_clean(r['answer'], r['question_type']))
    fm_bad = sum(1 for r in sheet_rows if r['question_type'] == 'free_multi'
                 and len(_slots(r['answer'])) != _safe_int(r['n_ans_slots']))
    mcq_bad = 0
    for r in sheet_rows:
        if r['question_type'] == 'MCQ':
            a = r['answer']
            if not MCQ_LETTERSET_RE.match(a):
                mcq_bad += 1
            elif ',' in a and list(a.split(',')) != sorted(a.split(',')):
                mcq_bad += 1
    conf_bad = sum(1 for r in sheet_rows if r['confidence'].upper() not in {'HIGH', 'MED'})
    resid_enum_bad = sum(1 for r in resid_rows if r['skip_reason'] not in RESID_ENUM
                         or not r['skip_reason'])
    neg_present = sum(1 for nid in WOLF_NEG if nid in sheet_ids)
    n_annot = skip_counts.get('annotation_contamination', 0)
    n_syntax = skip_counts.get('syntax_unparseable', 0)

    sha_wolf_end, sha_priv_end = sha(WOLF), sha(PRIV)
    sha_unchanged = (sha_wolf_end == sha_wolf_start and sha_priv_end == sha_priv_start)

    checks = [
        ('1 total==477', len(sheet_rows) + len(resid_rows) == 477,
         len(sheet_rows) + len(resid_rows)),
        ('2 disjoint', sheet_ids.isdisjoint(resid_ids), len(sheet_ids & resid_ids)),
        ('3 union==U', (sheet_ids | resid_ids) == U_ids, len(sheet_ids | resid_ids)),
        ('4 no markers in sheet', marker_bad == 0, marker_bad),
        ('5 predicate None for every sheet answer', annot_bad == 0, annot_bad),
        ('6 free_multi slotcount', fm_bad == 0, fm_bad),
        ('7 MCQ letterset+sorted', mcq_bad == 0, mcq_bad),
        ('8 confidence in {HIGH,MED}', conf_bad == 0, conf_bad),
        ('9 residual enum closed', resid_enum_bad == 0, resid_enum_bad),
        ('10 neg-controls all in sheet', neg_present == len(WOLF_NEG), neg_present),
        ('11 annotation==34 AND syntax==0', n_annot == 34 and n_syntax == 0,
         f'annot={n_annot},syntax={n_syntax}'),
        ('12 source SHAs unchanged', sha_unchanged, sha_unchanged),
    ]

    print('\n== fail-closed acceptance ==')
    all_pass = True
    for name, ok, val in checks:
        print(f'  [{"PASS" if ok else "FAIL"}] {name} (value={val})')
        all_pass = all_pass and ok

    mapped_promotions = promo_counts.get('mcq_letter_mapped_numeric', 0)
    amb_rate = (mapped_ambiguous / mapped_attempts) if mapped_attempts else 0.0
    print(f'\nPhase2 mapped attempts={mapped_attempts}, promotions={mapped_promotions},'
          f' ambiguous={mapped_ambiguous} ({amb_rate:.0%})')

    print('\n== promotion_class counts ==')
    for k in sorted(promo_counts):
        print(f'  {k}: {promo_counts[k]}')
    print('== skip_reason counts ==')
    for k in sorted(skip_counts):
        print(f'  {k}: {skip_counts[k]}')
    print(f'\nanswer_sheet total={len(sheet_rows)}  residual total={len(resid_rows)}')

    # stop conditions
    stop = []
    if smoke_fail:
        stop.append(f'{len(smoke_fail)} smoke misroute(s)')
    if not all_pass:
        stop.append('a fail-closed check failed')
    if mapped_promotions < 10:
        stop.append(f'Phase2 mapped letters {mapped_promotions} < 10')
    if amb_rate > 0.25:
        stop.append(f'mcq_ambiguous rate {amb_rate:.0%} > 25%')
    if not sha_unchanged:
        stop.append('source file SHA changed mid-run')

    if stop:
        print('\n*** STOP — NOT WRITING OUTPUTS ***')
        for s in stop:
            print('  -', s)
        if smoke_fail:
            print('  smoke detail:')
            for s in smoke_fail:
                print('   ', s)
        sys.exit(1)

    _write_sheet(sheet_rows)
    _write_resid(resid_rows)
    print('\nWROTE', OUT_SHEET, 'and', OUT_RESID)
    return sha_wolf_end, sha_priv_end


def _safe_int(x):
    try:
        return int(x)
    except (ValueError, TypeError):
        return -1


def _sheet(row, answer, promotion_class):
    return {
        'id': row['id'],
        'answer': answer,
        'question_type': (row['type'] or '').strip(),
        'n_ans_slots': row['n_ans_slots'],
        'confidence': (row['confidence'] or '').strip(),
        'promotion_class': promotion_class,
        'source_wolfram_answer': row['wolfram_answer'],
        'source_batch': row['batch'],
    }


def _resid(row, skip_reason):
    return {
        'id': row['id'],
        'question_type': (row['type'] or '').strip(),
        'n_ans_slots': row['n_ans_slots'],
        'confidence': (row['confidence'] or '').strip(),
        'skip_reason': skip_reason,
        'source_wolfram_answer': row['wolfram_answer'],
    }


def _write_sheet(rows):
    cols = ['id', 'answer', 'question_type', 'n_ans_slots', 'confidence',
            'promotion_class', 'source_wolfram_answer', 'source_batch']
    with open(OUT_SHEET, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\r\n')
        w.writeheader()
        for r in sorted(rows, key=lambda r: r['id']):
            w.writerow(r)


def _write_resid(rows):
    cols = ['id', 'question_type', 'n_ans_slots', 'confidence', 'skip_reason',
            'source_wolfram_answer']
    with open(OUT_RESID, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\r\n')
        w.writeheader()
        for r in sorted(rows, key=lambda r: r['id']):
            w.writerow(r)


if __name__ == '__main__':
    main()
