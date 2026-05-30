#!/usr/bin/env python3
"""wolfram_extract — derive a fail-closed answer sheet from the Wolfram audit.

Reads the raw audit table READ-ONLY and produces two mutually-exclusive sheets
over the frozen 477-id DONE universe:
  data/search/wolfram/wolfram_alpha_answer_sheet.csv  (promoted rows)
  data/search/wolfram/wolfram_alpha_residual.csv      (skipped rows + reason)

Spec authored by claude_strategy. Fail-closed throughout: any structural doubt
routes a row to residual rather than promoting a wrong value. Re-uses ONLY
`_slots` and `_to_number` from scripts/gold_equiv.py (no re-implemented parsing).

The earlier ad-hoc structural_screen.py / normalize_delta.py (commits 9e10af7,
b3dd057) were REVERTED for cause and are NOT resurrected here — this is fresh.
"""
import csv, hashlib, json, re, sys

sys.path.insert(0, '.')
from gold_equiv import _slots, _to_number  # the ONLY shared parsing primitives

WOLF = 'data/search/wolfram/WOLF_RESULTS.csv'
PRIV = 'private.jsonl'
OUT_SHEET = 'data/search/wolfram/wolfram_alpha_answer_sheet.csv'
OUT_RESID = 'data/search/wolfram/wolfram_alpha_residual.csv'

# --- universe / known sets ------------------------------------------------
KNOWN_DATASET_BUG = {'0011', '0317', '0570', '0585', '0622', '0858', '0894'}
# §5 of RESULTS_SUMMARY.md tags exactly 0542 as the F22 variance-convention item.
F22_IDS = {'0542'}
CONV_IDS = {'0542'} | F22_IDS

MARKERS = ('?', '...', '…')
NOTES_INCOMPLETE = ['undercount', 'missing', 'needs source', 'unknown', 'partial']
NOTES_INCOMPLETE_RE = re.compile(r'slot\s*\d+\s*(unknown|needs|missing)', re.I)
CONV_NOTES = ['convention-dependent', 'pop/sample', 'variance convention',
              'population vs sample']
# Phase 0.8 prose tokens (word-boundary, case-insensitive).
PROSE_TOKENS = ['in', 'is', 'are', 'the', 'an', 'and', 'or', 'with',
                'where', 'this', 'that', 'then', 'of']
PROSE_RE = re.compile(r'\b(' + '|'.join(PROSE_TOKENS) + r')\b', re.I)
# 0.4 annotation pattern: "<stuff-no-parens> ( <stuff> )" with trailing ).
ANNOT_RE = re.compile(r'^[^()]+\s*\([^)]+\)\s*$')
MCQ_LETTERSET_RE = re.compile(r'^[A-Z](,[A-Z])*$')


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def annot_paren_is_nonmath(answer):
    """0.4: the parenthetical content is non-numeric/non-mathematical."""
    if not ANNOT_RE.match(answer.strip()):
        return False
    m = re.search(r'\(([^)]+)\)\s*$', answer.strip())
    if not m:
        return False
    inner = m.group(1).strip()
    # mathematical/numeric if _to_number parses it, or it's a pure
    # numeric/operator/relation string (digits, math ops, ~, letters used as
    # math like ln). Non-math => words like 'quadrants'.
    if _to_number(inner) is not None:
        return False
    # treat as math if it contains only math-ish chars (no alpha words >2 long
    # except known math fns), else non-math.
    if re.search(r'[~=<>]|\bln\b|\blog\b|sqrt|\bpi\b', inner):
        return False
    # any alphabetic word of length >= 3 that isn't a math fn => annotation
    words = re.findall(r'[A-Za-z]{3,}', inner)
    return len(words) > 0


def load_questions():
    q = {}
    for line in open(PRIV):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        q['%04d' % int(r['id'])] = r['question']
    return q


# --- Phase 2 option parsing ----------------------------------------------
OPT_PATTERNS = [
    re.compile(r'^([A-Z])\.', re.M),
    re.compile(r'^\(([A-Z])\)', re.M),
    re.compile(r'^([A-Z])\)', re.M),
]


def parse_options(question):
    """Strict single-pass option parser. Returns list[(letter, rhs)] or None."""
    for pat in OPT_PATTERNS:
        matches = list(pat.finditer(question))
        if len(matches) < 2:
            continue
        letters = [m.group(1) for m in matches]
        # contiguous prefix A.. with N>=2, no gaps, document order
        expected = [chr(ord('A') + i) for i in range(len(letters))]
        if letters != expected:
            continue
        pairs = []
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(question)
            rhs = question[start:end].strip()
            pairs.append((m.group(1), rhs))
        return pairs
    return None


def phase2_map(row, question):
    """Numeric-only MCQ mapper. Returns ('promote', letter) or ('residual', reason)."""
    if question is None:
        return ('residual', 'mcq_options_not_parseable')
    pairs = parse_options(question)
    if pairs is None:
        return ('residual', 'mcq_options_not_parseable')
    opt_vals = []
    for _letter, rhs in pairs:
        v = _to_number(rhs)
        if v is None:
            return ('residual', 'mcq_options_not_numeric')
        opt_vals.append(v)
    w = _to_number(row['wolfram_answer'])
    if w is None:
        return ('residual', 'mcq_no_match')
    hits = [pairs[i][0] for i, ov in enumerate(opt_vals)
            if abs(w - ov) / max(1.0, abs(ov)) < 1e-6]
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
    # 4
    if annot_paren_is_nonmath(ans):
        return ('residual', 'annotation_contamination')
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

    questions = load_questions()

    sheet_rows, resid_rows = [], []
    promo_counts, skip_counts = {}, {}
    mapped_attempts, mapped_ambiguous = 0, 0

    for row in U:
        rid = row['id']
        q = questions.get(rid)
        verdict, info = structural_screen(row, q)

        if verdict == 'residual':
            resid_rows.append(_resid(row, info))
            skip_counts[info] = skip_counts.get(info, 0) + 1
            continue

        if verdict == 'PHASE2':
            mapped_attempts += 1
            res, val = phase2_map(row, q)
            if res == 'promote':
                pc = 'mcq_letter_mapped_numeric'
                sheet_rows.append(_sheet(row, val, pc))
                promo_counts[pc] = promo_counts.get(pc, 0) + 1
            else:
                if val == 'mcq_ambiguous':
                    mapped_ambiguous += 1
                resid_rows.append(_resid(row, val))
                skip_counts[val] = skip_counts.get(val, 0) + 1
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

    # --- fail-closed acceptance ------------------------------------------
    sheet_ids = {r['id'] for r in sheet_rows}
    resid_ids = {r['id'] for r in resid_rows}
    U_ids = {r['id'] for r in U}
    annot_bad = sum(1 for r in sheet_rows if annot_paren_is_nonmath(r['answer']))
    marker_bad = sum(1 for r in sheet_rows if any(m in r['answer'] for m in MARKERS))
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
    RESID_ENUM = {'low_confidence', 'known_dataset_bug', 'marker_in_answer',
                  'annotation_contamination', 'notes_admit_incomplete',
                  'slot_mismatch', 'convention_sensitive', 'prose_or_nonanswer',
                  'mcq_options_not_parseable', 'mcq_options_not_numeric',
                  'mcq_no_match', 'mcq_ambiguous'}
    resid_enum_bad = sum(1 for r in resid_rows if r['skip_reason'] not in RESID_ENUM
                         or not r['skip_reason'])

    checks = [
        ('1 total==477', len(sheet_rows) + len(resid_rows) == 477,
         len(sheet_rows) + len(resid_rows)),
        ('2 disjoint', sheet_ids.isdisjoint(resid_ids), len(sheet_ids & resid_ids)),
        ('3 union==U', (sheet_ids | resid_ids) == U_ids,
         len(sheet_ids | resid_ids)),
        ('4 no markers in sheet', marker_bad == 0, marker_bad),
        ('5 no annotation in sheet', annot_bad == 0, annot_bad),
        ('6 free_multi slotcount', fm_bad == 0, fm_bad),
        ('7 MCQ letterset+sorted', mcq_bad == 0, mcq_bad),
        ('8 confidence in {HIGH,MED}', conf_bad == 0, conf_bad),
        ('9 residual enum non-empty', resid_enum_bad == 0, resid_enum_bad),
    ]

    print('\n== fail-closed acceptance ==')
    all_pass = True
    for name, ok, val in checks:
        print(f'  [{"PASS" if ok else "FAIL"}] {name} (value={val})')
        all_pass = all_pass and ok

    amb_rate = (mapped_ambiguous / mapped_attempts) if mapped_attempts else 0.0
    print(f'\nPhase2 mapped attempts={mapped_attempts}, ambiguous={mapped_ambiguous}'
          f' ({amb_rate:.0%})')

    # stop conditions
    sha_wolf_end, sha_priv_end = sha(WOLF), sha(PRIV)
    stop = []
    if not all_pass:
        stop.append('a fail-closed check failed')
    if amb_rate > 0.25:
        stop.append(f'mcq_ambiguous rate {amb_rate:.0%} > 25%')
    if sha_wolf_end != sha_wolf_start or sha_priv_end != sha_priv_start:
        stop.append('source file SHA changed mid-run')

    print('\n== promotion_class counts ==')
    for k in sorted(promo_counts):
        print(f'  {k}: {promo_counts[k]}')
    print('== skip_reason counts ==')
    for k in sorted(skip_counts):
        print(f'  {k}: {skip_counts[k]}')
    print(f'\nanswer_sheet total={len(sheet_rows)}  residual total={len(resid_rows)}')

    if stop:
        print('\n*** STOP — NOT WRITING OUTPUTS ***')
        for s in stop:
            print('  -', s)
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
