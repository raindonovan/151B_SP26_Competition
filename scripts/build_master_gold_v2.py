#!/usr/bin/env python3
"""build_master_gold_v2.py — v2 gold sheet with normalizer-aware teacher clustering.
Sibling of build_master_gold.py. Reuses loaders and gold_equiv import from v1.
Does NOT import judger.py directly — all comparisons go through gold_equiv.

Key v2 improvements vs v1:
  - Normalizes every signal answer BEFORE computing agreement (fixes false T4s)
  - Teacher agreement via pairwise gold_equiv clustering, not string match
  - Deterministic cluster representative (modal surface, tie-break sonnet>gpt4>oss)
  - CONFLICT items emit no gold_best_answer (gold_source='conflict')
  - MCQ gold must be a bare letter
  - Full normalization diagnostic emitted per-signal
"""
import csv, json, sys, os
from collections import Counter
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts'); sys.path.insert(0, 'postprocessing/scripts')
from gold_equiv import gold_equiv
from normalizer import Normalizer

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_csv(p, key):
    with open(p, newline='', encoding='utf-8') as f:
        return {r[key]: r for r in csv.DictReader(f)}

def load_jsonl(p):
    items = {}
    with open(p, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                items[int(r['id'])] = r
    return items

T = load_csv('data/master_item_tracker.csv', 'id')
M = load_csv('data/MASTER_ANSWERS.csv', 'item_id')
items_private = load_jsonl('private.jsonl')

# v1 for tier_v1 reference
v1_rows = {}
try:
    for r in csv.DictReader(open('data/answer_sheet/master_gold_v1.csv', newline='', encoding='utf-8')):
        v1_rows[r['item_id']] = r
except FileNotFoundError:
    pass

# Consolidated search GOLD (primary source per spec)
search_gold = {}
for r in csv.DictReader(open('data/search/web_search/search_results.csv', newline='', encoding='utf-8')):
    if (r.get('search_status','') or '').strip().upper() == 'GOLD' and (r.get('found_answer','') or '').strip():
        search_gold[r['item_id']] = (r['found_answer'].strip(), (r.get('source_url','') or '').strip())

# MASTER_ANSWERS.csv GOLD fallback (only if consolidated source has nothing)
master_search_gold = {}
for iid, row in M.items():
    if (row.get('search_status','') or '').strip().upper() == 'GOLD' and (row.get('search_answer','') or '').strip():
        master_search_gold[iid] = (row['search_answer'].strip(), 'MASTER_ANSWERS_fallback')

# ---------------------------------------------------------------------------
# qtype inference (from tracker — no external file; avoids zero-padded ID bug)
# ---------------------------------------------------------------------------
def infer_qtype(tracker_row, private_item):
    if str(tracker_row.get('is_mcq', '')).lower() == 'true' or private_item.get('options'):
        return 'MCQ'
    n = int(tracker_row.get('n_ans_slots_q') or 0)
    return 'free_multi' if n >= 2 else 'free_single'

# ---------------------------------------------------------------------------
# Normalizer (conservative mode only for v2)
# ---------------------------------------------------------------------------
_NORM = Normalizer('conservative')

exception_log = []   # (item_id, signal, raw, exc_str)
empty_log = []       # (item_id, signal, raw)
diagnostic_rows = [] # for normalization_diagnostic.csv

def normalize_signal(item_id, signal, raw, item_dict):
    """Wrap raw in \\boxed{}, normalize, return (normalized, flags).
    On exception: falls back to raw with NORMALIZER_EXCEPTION flag.
    On empty-from-non-empty: falls back to raw with EMPTY_OUTPUT_FALLBACK flag.
    Never raises.
    """
    raw = (raw or '').strip()
    if not raw:
        return '', []
    response = f'\\boxed{{{raw}}}'
    try:
        res = _NORM.normalize_with_report(response, item_dict)
        normalized = res.candidate
        flags = list(res.flags)
        if raw and not normalized.strip():
            empty_log.append((item_id, signal, raw))
            normalized = raw
            flags.append('EMPTY_OUTPUT_FALLBACK')
        return normalized, flags
    except Exception as e:
        exception_log.append((item_id, signal, raw, str(e)))
        return raw, ['NORMALIZER_EXCEPTION']

# ---------------------------------------------------------------------------
# Source priority constants
# ---------------------------------------------------------------------------
SRC_RANK = {'sonnet': 0, 'gpt4': 1, 'oss': 2}
TIER_ORDER = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4, 'T5': 5, '': 99}

def _is_bare_letter(x):
    return len(x.strip()) == 1 and x.strip().isalpha()

# ---------------------------------------------------------------------------
# Main build loop
# ---------------------------------------------------------------------------
rows = []
for iid_str, t in T.items():
    item_dict = items_private.get(int(iid_str), {'id': int(iid_str)})
    qtype = infer_qtype(t, item_dict)

    # v1 reference values
    v1 = v1_rows.get(iid_str, {})
    tier_v1 = v1.get('tier', '')
    old_teacher_agree = int((v1.get('teacher_agree_3t', '') or '0') or 0)

    # -----------------------------------------------------------------------
    # Step 1: Normalize every signal
    # -----------------------------------------------------------------------
    teacher_srcs = [
        ('sonnet', t.get('teacher_sonnet', '') or ''),
        ('gpt4',   t.get('teacher_gpt54', '')  or ''),
        ('oss',    t.get('teacher_gpt_oss', '') or ''),
    ]

    sig_raw  = {}
    sig_norm = {}
    sig_flags = {}
    for src, raw in teacher_srcs:
        norm, flags = normalize_signal(iid_str, f'teacher_{src}', raw, item_dict)
        sig_raw[src]   = raw.strip()
        sig_norm[src]  = norm
        sig_flags[src] = flags
        if raw.strip():
            diagnostic_rows.append({
                'item_id': iid_str, 'qtype': qtype,
                'signal': f'teacher_{src}',
                'raw_answer': raw.strip(),
                'normalized_answer': norm,
                'flags': '|'.join(flags),
            })

    # Wolfram
    wc = (t.get('wolfram_confidence', '') or '').strip().upper()
    wa = (t.get('wolfram_override', '')   or '').strip()
    wolfram_active = (wc == 'HIGH') and bool(wa)
    if wolfram_active:
        norm_wolfram, wflags = normalize_signal(iid_str, 'wolfram', wa, item_dict)
        diagnostic_rows.append({
            'item_id': iid_str, 'qtype': qtype, 'signal': 'wolfram',
            'raw_answer': wa, 'normalized_answer': norm_wolfram, 'flags': '|'.join(wflags),
        })
    else:
        norm_wolfram = ''

    # Search — consolidated source first, MASTER_ANSWERS fallback
    sg = search_gold.get(iid_str) or master_search_gold.get(iid_str)
    sa_raw = sg[0] if sg else ''
    sgold  = bool(sg)
    if sgold:
        norm_search, sflags = normalize_signal(iid_str, 'search', sa_raw, item_dict)
        diagnostic_rows.append({
            'item_id': iid_str, 'qtype': qtype, 'signal': 'search',
            'raw_answer': sa_raw, 'normalized_answer': norm_search, 'flags': '|'.join(sflags),
        })
    else:
        norm_search = ''

    # -----------------------------------------------------------------------
    # Step 2: Teacher agreement via pairwise gold_equiv clustering
    # -----------------------------------------------------------------------
    nt = [(src, sig_norm[src]) for src in ('sonnet', 'gpt4', 'oss') if sig_norm[src].strip()]
    clusters = []
    for src, ans in nt:
        placed = False
        for c in clusters:
            if gold_equiv(ans, c[0][1], qtype) is True:
                c.append((src, ans))
                placed = True
                break
        if not placed:
            clusters.append([(src, ans)])

    largest = max(clusters, key=len) if clusters else []
    new_teacher_agree = len(largest)

    # Deterministic representative: modal surface, tie-break by SRC_RANK
    if new_teacher_agree >= 2:
        surf_counts = Counter(norm for _, norm in largest)
        top_count = max(surf_counts.values())
        cand_surfaces = {s for s, n in surf_counts.items() if n == top_count}
        chosen = min(
            (m for m in largest if m[1] in cand_surfaces),
            key=lambda m: SRC_RANK[m[0]]
        )
        norm_teacher_consensus = chosen[1]
        raw_teacher_consensus  = sig_raw[chosen[0]]
    else:
        norm_teacher_consensus = ''
        raw_teacher_consensus  = ''

    # -----------------------------------------------------------------------
    # Step 3: Independent source vs teacher consensus (gold_equiv)
    # -----------------------------------------------------------------------
    has_indep = wolfram_active or sgold

    if wolfram_active:
        norm_indep = norm_wolfram
        raw_indep  = wa
        indep_src  = 'wolfram_HIGH'
    elif sgold:
        norm_indep = norm_search
        raw_indep  = sa_raw
        indep_src  = 'search_GOLD'
    else:
        norm_indep = raw_indep = indep_src = ''

    indep_vs_teacher = ''
    if has_indep and new_teacher_agree >= 2 and norm_teacher_consensus:
        r = gold_equiv(norm_indep, norm_teacher_consensus, qtype)
        indep_vs_teacher = {True: 'agree', False: 'disagree', None: 'review'}[r]
    conflict = (indep_vs_teacher == 'disagree')

    # -----------------------------------------------------------------------
    # Step 4: gold_best_answer + tier
    # -----------------------------------------------------------------------
    if conflict:
        # CONFLICT: no trusted gold — preserve candidates in their columns
        gold_norm = gold_raw = ''
        gold_src  = 'conflict'
    elif qtype == 'MCQ' and new_teacher_agree >= 2 and _is_bare_letter(norm_teacher_consensus):
        gold_norm = norm_teacher_consensus.strip().upper()
        gold_raw  = raw_teacher_consensus
        gold_src  = 'teacher_3of3' if new_teacher_agree == 3 else 'teacher_2of3'
    elif wolfram_active:
        gold_norm = norm_wolfram
        gold_raw  = wa
        gold_src  = 'wolfram_HIGH'
    elif sgold:
        gold_norm = norm_search
        gold_raw  = sa_raw
        gold_src  = 'search_GOLD'
    elif new_teacher_agree == 3:
        gold_norm = norm_teacher_consensus
        gold_raw  = raw_teacher_consensus
        gold_src  = 'teacher_3of3'
    elif new_teacher_agree == 2:
        gold_norm = norm_teacher_consensus
        gold_raw  = raw_teacher_consensus
        gold_src  = 'teacher_2of3'
    else:
        gold_norm = gold_raw = ''
        gold_src  = 'none'

    # Tier formula (v2 — no qwen clause)
    if new_teacher_agree == 3 and has_indep and indep_vs_teacher == 'agree':
        tier_v2 = 'T1'
    elif new_teacher_agree == 3 or (new_teacher_agree == 2 and has_indep and indep_vs_teacher == 'agree'):
        tier_v2 = 'T2'
    elif new_teacher_agree == 2 or (has_indep and new_teacher_agree <= 1):
        tier_v2 = 'T3'
    else:
        tier_v2 = 'T4'
    if conflict:
        tier_v2 = 'T4'

    # Tier direction
    tier_changed = (tier_v1 != tier_v2) if tier_v1 else False
    if not tier_v1 or not tier_v2:
        tier_dir = 'N/A'
    elif TIER_ORDER[tier_v1] > TIER_ORDER[tier_v2]:
        tier_dir = 'promoted'
    elif TIER_ORDER[tier_v1] < TIER_ORDER[tier_v2]:
        tier_dir = 'demoted'
    else:
        tier_dir = 'unchanged'

    rows.append({
        'item_id':               iid_str,
        'qtype':                 qtype,
        'tier_v1':               tier_v1,
        'tier_v2':               tier_v2,
        'tier_changed':          tier_changed,
        'tier_direction':        tier_dir,
        'old_teacher_agree':     old_teacher_agree,
        'new_teacher_agree':     new_teacher_agree,
        'raw_teacher_consensus': raw_teacher_consensus,
        'norm_teacher_consensus':norm_teacher_consensus,
        'raw_independent_answer':raw_indep,
        'norm_independent_answer': norm_indep,
        'indep_source':          indep_src,
        'indep_vs_teacher':      indep_vs_teacher,
        'gold_conflict_flag':    conflict,
        'gold_best_answer_norm': gold_norm,
        'gold_best_answer_raw':  gold_raw,
        'gold_source':           gold_src,
        'n_ans_slots':           t.get('n_ans_slots_q', ''),
        # v1 columns preserved for side-by-side audit
        'wolfram_answer':        wa,
        'wolfram_confidence':    wc,
        'search_answer':         sa_raw,
        'search_gold':           sgold,
        'question_preview':      (t.get('question_preview', '') or '')[:80],
    })

# ---------------------------------------------------------------------------
# Step 5: Write outputs
# ---------------------------------------------------------------------------
os.makedirs('data/answer_sheet', exist_ok=True)

FIELDNAMES_V2 = [
    'item_id', 'qtype', 'tier_v1', 'tier_v2', 'tier_changed', 'tier_direction',
    'old_teacher_agree', 'new_teacher_agree',
    'raw_teacher_consensus', 'norm_teacher_consensus',
    'raw_independent_answer', 'norm_independent_answer', 'indep_source',
    'indep_vs_teacher', 'gold_conflict_flag',
    'gold_best_answer_norm', 'gold_best_answer_raw', 'gold_source',
    'n_ans_slots',
    # v1 preserved
    'wolfram_answer', 'wolfram_confidence', 'search_answer', 'search_gold',
    'question_preview',
]

out_v2 = 'data/answer_sheet/master_gold_v2.csv'
with open(out_v2, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=FIELDNAMES_V2)
    w.writeheader()
    w.writerows(rows)

diag_out = 'data/answer_sheet/normalization_diagnostic.csv'
with open(diag_out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['item_id', 'qtype', 'signal', 'raw_answer', 'normalized_answer', 'flags'])
    w.writeheader()
    w.writerows(diagnostic_rows)

# ---------------------------------------------------------------------------
# Summary + mandatory normalizer block
# ---------------------------------------------------------------------------
tier_v2_dist = dict(sorted(Counter(r['tier_v2'] for r in rows).items()))
tier_v1_dist = dict(sorted(Counter(r['tier_v1'] for r in rows if r['tier_v1']).items()))
promotions  = [r for r in rows if r['tier_v1'] == 'T4' and r['tier_v2'] in ('T1', 'T2', 'T3')]
demotions   = [r for r in rows if r['tier_v1'] in ('T1', 'T2') and r['tier_v2'] == 'T4']
has_gold    = sum(1 for r in rows if r['gold_best_answer_norm'])
n_conflict  = sum(1 for r in rows if r['gold_conflict_flag'])
n_signals   = len(diagnostic_rows)

print(f"wrote {out_v2} ({len(rows)} items)")
print(f"wrote {diag_out} ({n_signals} signal rows)")
print()
print(f"tier_v1: {tier_v1_dist}")
print(f"tier_v2: {tier_v2_dist}")
print(f"has gold_best_answer_norm: {has_gold}/{len(rows)}")
print(f"promotions (T4→T2+): {len([r for r in promotions if r['tier_v2'] in ('T1','T2')])}")
print(f"promotions (T4→T3):  {len([r for r in promotions if r['tier_v2'] == 'T3'])}")
print(f"demotions (T1/T2→T4): {len(demotions)}")
print()
print("=== MANDATORY NORMALIZER SUMMARY ===")
print(f"exception count:            {len(exception_log)}")
print(f"empty-from-non-empty count: {len(empty_log)}")
print(f"total signal normalizations: {n_signals}")
PER_SIGNAL_THRESHOLD = max(5, int(0.01 * n_signals / 5))
suspect = len(exception_log) > PER_SIGNAL_THRESHOLD or len(empty_log) > PER_SIGNAL_THRESHOLD
if exception_log:
    print("EXCEPTIONS (first 5):")
    for (iid, sig, raw, exc) in exception_log[:5]:
        print(f"  [{iid}/{sig}] {raw[:30]!r}: {exc[:80]}")
if empty_log:
    print("EMPTY OUTPUTS (first 5):")
    for (iid, sig, raw) in empty_log[:5]:
        print(f"  [{iid}/{sig}] {raw[:30]!r}")
print(f"BUILD STATUS: {'SUSPECT' if suspect else 'CLEAN'}")
print()
print(f"=== CONFLICTS v2: {n_conflict} ===")
for r in rows:
    if r['gold_conflict_flag']:
        print(f"  {r['item_id']:>4} [{r['qtype']:<11}] {r['indep_source']}={r['raw_independent_answer'][:26]!r}"
              f" vs teachers={r['raw_teacher_consensus'][:26]!r}")
print()
print("teacher agree distribution (v2):", dict(sorted(Counter(r['new_teacher_agree'] for r in rows).items())))
