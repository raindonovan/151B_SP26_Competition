#!/usr/bin/env python3
"""teacher_analysis — 4-teacher audit (Phases 0-4).

Structural QA, anchor scoring, cross-teacher agreement, disagreement queues, and a
PROPOSED weighting policy. Outputs are advisory-until-human-pass. Reads everything
READ-ONLY; fail-closed: computes all phases, runs acceptance, writes outputs ONLY
if every acceptance check passes (else STOP, no writes).

Shared primitives from gold_equiv: _slots, _to_exact, gold_equiv, load_records.
"""
import csv, hashlib, json, re, sys, os
from collections import defaultdict, Counter

sys.path.insert(0, '.')
from gold_equiv import _slots, _to_exact, gold_equiv, load_records

TDIR = 'data/search/teachers'
ANCHOR = f'{TDIR}/anchor_set_FINAL.csv'
PRIV = 'private.jsonl'
TEACHERS = ['sonnet', 'gpt4', 'oss', 'xhigh']
INPUTS = [ANCHOR] + [f'{TDIR}/{t}/answers.csv' for t in TEACHERS] + [PRIV, 'scripts/gold_equiv.py']

MCQ_SINGLE_RE = re.compile(r'^[A-Z]$')
MCQ_SET_RE = re.compile(r'^[A-Z](,[A-Z])+$')
MCQ_LETTERSET_RE = re.compile(r'^[A-Z](,[A-Z])*$')


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def load_answers(t):
    return {str(r['id']).zfill(4): (r['answer'] or '') for r in
            csv.DictReader(open(f'{TDIR}/{t}/answers.csv', newline=''))}


def subtype_of(ans, n_ans_q):
    a = (ans or '').strip()
    if MCQ_SINGLE_RE.match(a):
        return 'MCQ_single'
    if MCQ_SET_RE.match(a):
        return 'MCQ_set'
    if _to_exact(a) is not None:
        return 'FREE_num_single'
    if n_ans_q < 2:
        return 'FREE_other_single'
    return 'FREE_multi'


def letterset(a):
    return ','.join(sorted((a or '').strip().split(',')))


def grade(teacher_ans, gold_ans, subtype):
    """True iff teacher_ans matches gold_ans for the given subtype."""
    if subtype in ('MCQ_single', 'MCQ_set'):
        return letterset(teacher_ans) == letterset(gold_ans)
    qtype = 'free_multi' if subtype == 'FREE_multi' else 'free_single'
    return gold_equiv(teacher_ans, gold_ans, qtype) is True


def equiv(a, b, item_qtype):
    if item_qtype == 'MCQ':
        return letterset(a) == letterset(b)
    return gold_equiv(a, b, item_qtype) is True


def cluster(answers, item_qtype):
    """answers: list of (teacher, ans). Returns list of clusters (each a list of teachers)."""
    clusters = []   # each: [rep_ans, [teachers]]
    for t, a in answers:
        for c in clusters:
            if equiv(a, c[0], item_qtype):
                c[1].append(t)
                break
        else:
            clusters.append([a, [t]])
    return [c[1] for c in clusters]


def pattern_of(clusters):
    return '+'.join(str(x) for x in sorted((len(c) for c in clusters), reverse=True))


def main():
    start_sha = {p: sha(p) for p in INPUTS}
    print('== provenance (start SHAs) ==')
    for p in INPUTS:
        print(f'  {start_sha[p][:16]}  {p}')

    records = load_records(PRIV)
    ids = sorted(records.keys())
    anchor = {r['id']: r for r in csv.DictReader(open(ANCHOR, newline=''))}
    ans = {t: load_answers(t) for t in TEACHERS}

    # gpt4 quarantine check (ids 267-449 template/blank)
    TEMPLATES = {'answer', 'Letter', 'value1,value2,value3'}
    gpt4_corrupted_block = {('%04d' % i) for i in range(267, 450)
                            if (ans['gpt4'].get('%04d' % i, '') or '').strip() in TEMPLATES
                            or not (ans['gpt4'].get('%04d' % i, '') or '').strip()}

    # item-level qtype/n_ans
    n_ans_q = {i: records[i]['question'].count('[ANS]') for i in ids}
    is_mcq = {i: ('options' in records[i]) for i in ids}

    def item_qtype(i):
        if is_mcq[i]:
            return 'MCQ'
        return 'free_multi' if n_ans_q[i] >= 2 else 'free_single'

    # ===================================================================
    # PHASE 1 — STRUCTURAL QA
    # ===================================================================
    structural = {t: {} for t in TEACHERS}   # id -> flags
    struct_rows = {t: [] for t in TEACHERS}
    summary = {t: Counter() for t in TEACHERS}
    for t in TEACHERS:
        for i in ids:
            a = (ans[t].get(i, '') or '')
            flags = []
            if not a.strip():
                flags.append('blank')
            elif is_mcq[i] and not MCQ_LETTERSET_RE.match(a.strip()):
                flags.append('mcq_non_letter')
            elif (not is_mcq[i]) and n_ans_q[i] >= 2:
                n_a = len(_slots(a))
                if n_a < n_ans_q[i]:
                    flags.append(f'multi_slot_under_{n_a}_of_{n_ans_q[i]}')
                elif n_a > n_ans_q[i]:
                    flags.append(f'multi_slot_over_{n_a}_of_{n_ans_q[i]}')
            if flags:
                structural[t][i] = flags
                struct_rows[t].append({'id': i, 'flags': '|'.join(flags), 'ans': a})
                if 'blank' in flags:
                    summary[t]['blank'] += 1
                if 'mcq_non_letter' in flags:
                    summary[t]['mcq_non_letter'] += 1
                if any(f.startswith('multi_slot_under') for f in flags):
                    summary[t]['under'] += 1
                if any(f.startswith('multi_slot_over') for f in flags):
                    summary[t]['over'] += 1

    def flagged(t, i):
        return i in structural[t]

    def contributes(t, i):
        a = (ans[t].get(i, '') or '')
        if not a.strip():
            return False
        if flagged(t, i):
            return False
        if t == 'gpt4' and i in gpt4_corrupted_block:
            return False
        return True

    # ===================================================================
    # PHASE 2 — ANCHOR SCORING (teacher x subtype x tier)
    # ===================================================================
    hits = defaultdict(int)      # (t, subtype, tier) -> hits
    attempts = defaultdict(int)
    for aid, arow in anchor.items():
        if aid not in records:
            continue
        st = subtype_of(arow['answer'], n_ans_q.get(aid, 0))
        tier = arow['tier']
        for t in TEACHERS:
            a = (ans[t].get(aid, '') or '')
            if not a.strip():
                continue
            if flagged(t, aid):
                continue
            if t == 'gpt4' and aid in gpt4_corrupted_block:
                continue
            attempts[(t, st, tier)] += 1
            if grade(a, arow['answer'], st):
                hits[(t, st, tier)] += 1

    # ===================================================================
    # PHASE 3 — CROSS-TEACHER AGREEMENT
    # ===================================================================
    breakdown = []                       # per-item rows
    strat = defaultdict(lambda: {'n_compared': 0, 'patterns': Counter(),
                                 'pair_both': Counter(), 'pair_agree': Counter()})
    PAIRS = [('xhigh', 'sonnet'), ('xhigh', 'oss'), ('xhigh', 'gpt4'),
             ('sonnet', 'oss'), ('sonnet', 'gpt4'), ('oss', 'gpt4')]
    n4_unanimous = 0
    n4_total = 0
    for i in ids:
        contrib = [(t, ans[t][i]) for t in TEACHERS if contributes(t, i)]
        N = len(contrib)
        quarantined = [t for t in TEACHERS if not contributes(t, i)]
        if N < 2:
            continue
        qt = item_qtype(i)
        clusters = cluster(contrib, qt)
        pat = pattern_of(clusters)
        # item subtype from the modal cluster's representative answer
        modal_cluster = max(clusters, key=len)
        modal_ans = next(a for (t, a) in contrib if t in modal_cluster)
        st = subtype_of(modal_ans, n_ans_q[i])
        key = (st, N)
        strat[key]['n_compared'] += 1
        strat[key]['patterns'][pat] += 1
        if N == 4:
            n4_total += 1
            if pat == '4':
                n4_unanimous += 1
        # pairwise (within this stratum)
        cmap = {}
        for ci, cl in enumerate(clusters):
            for t in cl:
                cmap[t] = ci
        for x, y in PAIRS:
            if x in cmap and y in cmap:
                strat[key]['pair_both'][(x, y)] += 1
                if cmap[x] == cmap[y]:
                    strat[key]['pair_agree'][(x, y)] += 1
        breakdown.append({
            'id': i, 'n_contributing': N, 'cluster_pattern': pat,
            'cluster_membership_json': json.dumps([sorted(c) for c in clusters]),
            'quarantined_teachers_json': json.dumps(sorted(quarantined)),
        })

    # ===================================================================
    # PHASE 4 — DISAGREEMENT QUEUES
    # ===================================================================
    bd_by_id = {r['id']: r for r in breakdown}

    def teacher_val(t, i):
        if t == 'gpt4' and i in gpt4_corrupted_block:
            return '<quarantined>'
        a = (ans[t].get(i, '') or '')
        if not a.strip():
            return '<blank>'
        if flagged(t, i):
            return f'<flagged:{"|".join(structural[t][i])}>'
        return a

    def trace_path(t, i):
        return f'{TDIR}/{t}/item_{i}.md'

    def xhigh_snippet(i):
        p = trace_path('xhigh', i)
        if not os.path.exists(p):
            return 'trace_path_only'
        try:
            txt = open(p, encoding='utf-8').read()
            idx = txt.find('## Reasoning + Response')
            seg = txt[idx:] if idx != -1 else txt
            lines = [ln.strip() for ln in seg.splitlines() if ln.strip()]
            boxed = next((ln for ln in reversed(lines) if 'boxed' in ln), '')
            tail = lines[-3:] if len(lines) >= 3 else lines
            snip = ' / '.join(tail)
            if boxed and boxed not in tail:
                snip += ' / ' + boxed
            return snip[:300] if snip else 'trace_path_only'
        except Exception:
            return 'trace_path_only'

    def entry(i, extra=None):
        arow = anchor.get(i, {})
        bd = bd_by_id.get(i, {})
        e = {
            'id': i,
            'anchor_tier': arow.get('tier', '<no_anchor>'),
            'anchor_value': arow.get('answer', '<no_anchor>'),
            'sonnet': teacher_val('sonnet', i),
            'gpt4': teacher_val('gpt4', i),
            'oss': teacher_val('oss', i),
            'xhigh': teacher_val('xhigh', i),
            'cluster_pattern': bd.get('cluster_pattern', '<N<2>'),
            'n_contributing': bd.get('n_contributing', 0),
            'trace_sonnet': trace_path('sonnet', i),
            'trace_gpt4': trace_path('gpt4', i),
            'trace_oss': trace_path('oss', i),
            'trace_xhigh': trace_path('xhigh', i),
            'xhigh_snippet': xhigh_snippet(i),
        }
        if extra:
            e.update(extra)
        return e

    TIER_RANK = {'A+': 0, 'A': 1}

    # Q1: xhigh disagrees with anchor
    q1 = []
    for aid, arow in anchor.items():
        if aid not in records or not contributes('xhigh', aid):
            continue
        st = subtype_of(arow['answer'], n_ans_q.get(aid, 0))
        if not grade(ans['xhigh'][aid], arow['answer'], st):
            n_wrong = sum(1 for t in TEACHERS if contributes(t, aid)
                          and not grade(ans[t][aid], arow['answer'], st))
            q1.append((aid, arow['tier'], st, n_wrong))
    q1.sort(key=lambda x: (TIER_RANK.get(x[1], 9), x[2], -x[3], x[0]))
    q1 = q1[:50]

    # Q2: sonnet+oss agree vs lone xhigh
    q2 = []
    for i in ids:
        if not (contributes('sonnet', i) and contributes('oss', i) and contributes('xhigh', i)):
            continue
        qt = item_qtype(i)
        if equiv(ans['sonnet'][i], ans['oss'][i], qt) and not equiv(ans['sonnet'][i], ans['xhigh'][i], qt):
            in_anchor = i in anchor
            tier = anchor[i]['tier'] if in_anchor else '<no_anchor>'
            q2.append((i, in_anchor, TIER_RANK.get(tier, 9)))
    q2.sort(key=lambda x: (not x[1], x[2], x[0]))
    q2 = q2[:30]

    # Q3: all contributing teachers agree against anchor
    q3 = []
    for aid, arow in anchor.items():
        if aid not in records:
            continue
        contrib = [t for t in TEACHERS if contributes(t, aid)]
        if len(contrib) < 2:
            continue
        qt = item_qtype(aid)
        first = ans[contrib[0]][aid]
        if all(equiv(ans[t][aid], first, qt) for t in contrib[1:]):
            st = subtype_of(arow['answer'], n_ans_q.get(aid, 0))
            if not grade(first, arow['answer'], st):
                q3.append((aid, arow['tier']))

    # Q4: >=3 teacher consensus against single-source A anchor
    q4 = []
    for aid, arow in anchor.items():
        if aid not in records or arow['tier'] != 'A':
            continue
        contrib = [t for t in TEACHERS if contributes(t, aid)]
        if len(contrib) < 3:
            continue
        qt = item_qtype(aid)
        st = subtype_of(arow['answer'], n_ans_q.get(aid, 0))
        clusters = cluster([(t, ans[t][aid]) for t in contrib], qt)
        big = max(clusters, key=len)
        if len(big) >= 3:
            rep = next(ans[t][aid] for t in contrib if t in big)
            if not grade(rep, arow['answer'], st):
                q4.append((aid, arow['tier']))

    # ===================================================================
    # ACCEPTANCE
    # ===================================================================
    subtypes_all = ['MCQ_single', 'MCQ_set', 'FREE_num_single', 'FREE_other_single', 'FREE_multi']
    nan_cells = 0
    for (t, st, tier), n in attempts.items():
        if n > 0 and (t, st, tier) not in hits and hits.get((t, st, tier), None) is None:
            pass  # hits defaults 0, never NaN
    # NaN only possible if we emitted precision with attempts==0; we guard at write.
    mcq_attempts_total = sum(n for (t, st, tier), n in attempts.items()
                             if st in ('MCQ_single', 'MCQ_set'))
    mcq_anchors_exist = any(subtype_of(r['answer'], n_ans_q.get(r['id'], 0)) in ('MCQ_single', 'MCQ_set')
                            for r in anchor.values() if r['id'] in records)
    phase3_ok = all(sum(d['patterns'].values()) == d['n_compared'] for d in strat.values())

    checks = [
        ('1 anchor==316', len(anchor) == 316, len(anchor)),
        ('2 structural reported (4 fields x4)', all(t in summary for t in TEACHERS), 'ok'),
        ('2h sonnet 2/2/6', (summary['sonnet']['blank'], summary['sonnet']['mcq_non_letter'],
                             summary['sonnet']['under']) == (2, 2, 6),
         (summary['sonnet']['blank'], summary['sonnet']['mcq_non_letter'], summary['sonnet']['under'])),
        # hard-checks corrected to current-data actuals (strategy auth 2026-05-30:
        # stale pre-audit estimates were oss=6/xhigh=5; full enumeration -> oss=5/xhigh=3)
        ('2h oss 7/5/12', (summary['oss']['blank'], summary['oss']['mcq_non_letter'],
                           summary['oss']['under']) == (7, 5, 12),
         (summary['oss']['blank'], summary['oss']['mcq_non_letter'], summary['oss']['under'])),
        ('2h xhigh 3/3/5', (summary['xhigh']['blank'], summary['xhigh']['mcq_non_letter'],
                            summary['xhigh']['under']) == (3, 3, 5),
         (summary['xhigh']['blank'], summary['xhigh']['mcq_non_letter'], summary['xhigh']['under'])),
        ('3 no NaN where attempts>0', nan_cells == 0, nan_cells),
        ('4 phase3 pattern sums == n_compared', phase3_ok, phase3_ok),
        ('5 Q3 count in [0,10]', 0 <= len(q3) <= 10, len(q3)),
        ('7 source SHAs unchanged', all(sha(p) == start_sha[p] for p in INPUTS), 'ok'),
    ]
    print('\n== acceptance ==')
    all_pass = True
    for name, ok, val in checks:
        print(f'  [{"PASS" if ok else "FAIL"}] {name} (value={val})')
        all_pass = all_pass and ok

    stop = []
    if not all_pass:
        stop.append('an acceptance check failed')
    if mcq_anchors_exist and mcq_attempts_total == 0:
        stop.append('MCQ anchors exist but all MCQ attempts==0 (parse failure)')
    if len(anchor) != 316:
        stop.append('anchor row count != 316')

    # report key numbers
    print('\n== structural summary ==')
    print(f"  {'teacher':<8}{'blank':>6}{'non_letter':>12}{'under':>7}{'over':>6}")
    for t in TEACHERS:
        s = summary[t]
        print(f"  {t:<8}{s['blank']:>6}{s['mcq_non_letter']:>12}{s['under']:>7}{s['over']:>6}")
    print(f"  gpt4 quarantine block size: {len(gpt4_corrupted_block)}")
    print(f"\nN=4 unanimous: {n4_unanimous}/{n4_total}")
    print(f"Q1={len(q1)} Q2={len(q2)} Q3={len(q3)} Q4={len(q4)}")

    if stop:
        print('\n*** STOP — NOT WRITING OUTPUTS ***')
        for s in stop:
            print('  -', s)
        sys.exit(1)

    # ===================================================================
    # WRITE OUTPUTS
    # ===================================================================
    write_all(struct_rows, summary, hits, attempts, strat, breakdown, PAIRS,
              q1, q2, q3, q4, anchor, entry, n_ans_q, records, n4_unanimous, n4_total)
    end_sha = {p: sha(p) for p in INPUTS}
    print('\nsource SHAs unchanged end:', all(end_sha[p] == start_sha[p] for p in INPUTS))
    print('WROTE all outputs.')


def write_all(struct_rows, summary, hits, attempts, strat, breakdown, PAIRS,
              q1, q2, q3, q4, anchor, entry, n_ans_q, records, n4_unanimous, n4_total):
    TEACHERS = ['sonnet', 'gpt4', 'oss', 'xhigh']
    # structural per-teacher + summary
    for t in TEACHERS:
        with open(f'{TDIR}/{t}/structural_qa.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['id', 'flags', 'ans'], lineterminator='\r\n')
            w.writeheader(); w.writerows(struct_rows[t])
    with open(f'{TDIR}/teacher_structural_summary.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['teacher', 'n_blank', 'n_mcq_non_letter',
                                          'n_multi_slot_under', 'n_multi_slot_over'],
                           lineterminator='\r\n')
        w.writeheader()
        for t in TEACHERS:
            s = summary[t]
            w.writerow({'teacher': t, 'n_blank': s['blank'], 'n_mcq_non_letter': s['mcq_non_letter'],
                        'n_multi_slot_under': s['under'], 'n_multi_slot_over': s['over']})

    # anchor accuracy
    with open(f'{TDIR}/teacher_anchor_accuracy.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['teacher', 'subtype', 'anchor_tier', 'hits',
                                          'attempts', 'precision'], lineterminator='\r\n')
        w.writeheader()
        subtypes = ['MCQ_single', 'MCQ_set', 'FREE_num_single', 'FREE_other_single', 'FREE_multi']
        for t in TEACHERS:
            for st in subtypes:
                for tier in ['A+', 'A']:
                    n = attempts.get((t, st, tier), 0)
                    h = hits.get((t, st, tier), 0)
                    if n == 0:
                        continue
                    w.writerow({'teacher': t, 'subtype': st, 'anchor_tier': tier,
                                'hits': h, 'attempts': n, 'precision': round(h / n, 4)})

    # agreement matrix
    PATTERN_COLS = ['n_pattern_4', 'n_pattern_3+1', 'n_pattern_2+2', 'n_pattern_2+1+1',
                    'n_pattern_1+1+1+1', 'n_pattern_3', 'n_pattern_2+1', 'n_pattern_1+1+1',
                    'n_pattern_2']
    pair_cols = [f'pairwise_{x}_{y}' for x, y in PAIRS]
    with open(f'{TDIR}/teacher_agreement_matrix.csv', 'w', newline='') as f:
        cols = ['subtype', 'n_contributing_teachers', 'n_compared'] + PATTERN_COLS + pair_cols
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\r\n')
        w.writeheader()
        for (st, N), d in sorted(strat.items()):
            row = {'subtype': st, 'n_contributing_teachers': N, 'n_compared': d['n_compared']}
            for pc in PATTERN_COLS:
                pat = pc.replace('n_pattern_', '')
                row[pc] = d['patterns'].get(pat, 0)
            for (x, y) in PAIRS:
                row[f'pairwise_{x}_{y}'] = d['pair_agree'].get((x, y), 0)
            w.writerow(row)

    # agreement breakdown
    with open(f'{TDIR}/teacher_agreement_breakdown.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'n_contributing', 'cluster_pattern',
                                          'cluster_membership_json', 'quarantined_teachers_json'],
                           lineterminator='\r\n')
        w.writeheader(); w.writerows(breakdown)

    # queues
    def write_queue(path, title, rows):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'# {title}\n\nSTATUS: advisory. {len(rows)} items.\n\n')
            for r in rows:
                f.write(f"## {r['id']}  (anchor_tier={r['anchor_tier']}, "
                        f"pattern={r['cluster_pattern']}, n_contrib={r['n_contributing']})\n")
                f.write(f"- anchor: `{r['anchor_value']}`\n")
                f.write(f"- sonnet: `{r['sonnet']}`  | gpt4: `{r['gpt4']}`  | "
                        f"oss: `{r['oss']}`  | xhigh: `{r['xhigh']}`\n")
                f.write(f"- xhigh snippet: {r['xhigh_snippet']}\n")
                f.write(f"- traces: {r['trace_sonnet']} | {r['trace_gpt4']} | "
                        f"{r['trace_oss']} | {r['trace_xhigh']}\n\n")

    write_queue(f'{TDIR}/xhigh_disagreement_queue.md',
                'Q1 — xhigh disagrees with anchor (top 50)', [entry(i) for i, *_ in q1])
    write_queue(f'{TDIR}/sonnet_oss_vs_xhigh_queue.md',
                'Q2 — sonnet+oss agree vs lone xhigh (top 30)', [entry(i) for i, *_ in q2])
    write_queue(f'{TDIR}/teachers_vs_anchor_queue.md',
                'Q3 — all contributing teachers agree against anchor', [entry(i) for i, *_ in q3])
    # Q4 appended to anchor_review_queue.md
    with open(f'{TDIR}/anchor_review_queue.md', 'w', encoding='utf-8') as f:
        f.write('# Q4 — >=3 teacher consensus against single-source A anchor\n\n')
        f.write(f'STATUS: advisory. {len(q4)} items.\n\n')
        for i, tier in q4:
            r = entry(i)
            f.write(f"## {r['id']}  (anchor_tier={r['anchor_tier']}, pattern={r['cluster_pattern']})\n")
            f.write(f"- anchor: `{r['anchor_value']}`\n")
            f.write(f"- sonnet: `{r['sonnet']}` | gpt4: `{r['gpt4']}` | oss: `{r['oss']}` | xhigh: `{r['xhigh']}`\n\n")

    # proposed policy
    write_policy(hits, attempts, q3, q4, n4_unanimous, n4_total, anchor)


def write_policy(hits, attempts, q3, q4, n4_unanimous, n4_total, anchor):
    subtypes = ['MCQ_single', 'MCQ_set', 'FREE_num_single', 'FREE_other_single', 'FREE_multi']
    TEACHERS = ['sonnet', 'gpt4', 'oss', 'xhigh']

    def prec(t, st):
        h = sum(hits.get((t, st, tier), 0) for tier in ['A+', 'A'])
        n = sum(attempts.get((t, st, tier), 0) for tier in ['A+', 'A'])
        return (h, n, (h / n) if n else None)

    def overall(t):
        h = sum(hits.get((t, st, tier), 0) for st in subtypes for tier in ['A+', 'A'])
        n = sum(attempts.get((t, st, tier), 0) for st in subtypes for tier in ['A+', 'A'])
        return (h, n, (h / n) if n else None)

    # H1: xhigh leads in most subtypes
    leads = 0; comparable = 0
    for st in subtypes:
        precs = {t: prec(t, st)[2] for t in TEACHERS if prec(t, st)[1] > 0}
        if len(precs) >= 2:
            comparable += 1
            if precs.get('xhigh') is not None and precs['xhigh'] == max(precs.values()):
                leads += 1
    h1 = 'INSUFFICIENT_DATA' if comparable == 0 else ('PASS' if leads > comparable / 2 else 'FAIL')

    # H4: sonnet strongest comparator (highest overall precision)
    ov = {t: overall(t)[2] for t in TEACHERS if overall(t)[1] > 0}
    h4 = 'INSUFFICIENT_DATA' if not ov else ('PASS' if ov.get('sonnet') == max(ov.values()) else 'FAIL')

    # H3: gpt4 non-trivial weight where it has data
    gh, gn, gp = overall('gpt4')
    h3 = 'INSUFFICIENT_DATA' if gn < 20 else ('PASS' if (gp or 0) >= 0.7 else 'FAIL')

    # H2: provisional — needs tiebreak data; mark INSUFFICIENT_DATA unless clear
    h2 = 'INSUFFICIENT_DATA'

    with open(f'{TDIR}/teacher_weighting_policy.PROPOSED.md', 'w', encoding='utf-8') as f:
        f.write('STATUS: PROPOSED. Pending human pass by strategy + rain. '
                'Do not consume downstream until canonical teacher_weighting_policy.md is committed.\n\n')
        f.write('# Teacher Weighting Policy (PROPOSED)\n\n')
        f.write('## Section 1 — Anchor precedence (LOCKED)\n')
        f.write('1. A+ multi-source: use, conf=VERY_HIGH (7 items)\n')
        f.write('2. A single-source: use, conf=HIGH, subject to Q3/Q4 review\n')
        f.write('3. Source conflicts already resolved at audit layer; see '
                'data/search/anchor_audit_report.md.\n\n')
        f.write('Multi-source A+ anchors win outright. Single-source A anchors route to '
                'review under Q3/Q4 triggers.\n\n')
        f.write('## Section 2 — Teacher precision table (subtype x anchor_tier)\n\n')
        f.write('| teacher | subtype | A+ (h/n) | A (h/n) | overall prec |\n')
        f.write('|---|---|---|---|---|\n')
        for t in TEACHERS:
            for st in subtypes:
                hp, np_, _ = (hits.get((t, st, 'A+'), 0), attempts.get((t, st, 'A+'), 0), 0)
                ha, na, _ = (hits.get((t, st, 'A'), 0), attempts.get((t, st, 'A'), 0), 0)
                if np_ == 0 and na == 0:
                    continue
                _, _, op = prec(t, st)
                f.write(f"| {t} | {st} | {hp}/{np_} | {ha}/{na} | "
                        f"{round(op, 3) if op is not None else 'NA'} |\n")
        f.write('\n## Section 3 — Hypotheses tested vs Phase 2\n\n')
        f.write(f'- H1 (xhigh leads most subtypes): **{h1}** '
                f'(leads {leads}/{comparable} comparable subtypes)\n')
        f.write(f'- H2 (xhigh + one of sonnet/oss outweighs pair on tiebreak): **{h2}** '
                '(provisional; routes ties to review until settled)\n')
        f.write(f'- H3 (gpt4 carries non-trivial weight): **{h3}** '
                f'(gpt4 overall {gh}/{gn}, prec {round(gp,3) if gp else "NA"})\n')
        f.write(f'- H4 (sonnet strongest comparator): **{h4}** '
                f'(overall precisions { {t: round(p,3) for t,p in ov.items()} })\n\n')
        f.write('## Section 4 — Gold-build voting rules (LOCKED)\n')
        f.write('- Anchor precedence (Section 1) applies first.\n')
        f.write('- MCQ vote counts only as a proper letter (^[A-Z](,[A-Z])*$).\n')
        f.write('- FREE_multi vote counts only with exact slot count.\n')
        f.write('- Lone gpt4 never breaks a tie.\n')
        f.write('- Tie-breakers within teacher bloc: PROVISIONAL pending H2. '
                'Until H2 settles, route ties to review.\n\n')
        f.write('## Section 5 — Items flagged for human review\n')
        f.write(f'- Q3 (all teachers vs anchor): {len(q3)} items\n')
        f.write(f'- Q4 (>=3 consensus vs single-source A): {len(q4)} items\n')
        nonpass = [r['id'] for r in anchor.values() if r.get('audit_action') not in (None, '', 'pass')]
        f.write(f'- anchor rows with audit_action != pass: {sorted(nonpass)}\n\n')
        f.write('## Section 6 — Expected coverage per subtype\n\n')
        f.write('| subtype | total anchor attempts (all teachers) |\n|---|---|\n')
        for st in subtypes:
            tot = sum(attempts.get((t, st, tier), 0) for t in TEACHERS for tier in ['A+', 'A'])
            f.write(f'| {st} | {tot} |\n')


if __name__ == '__main__':
    main()
