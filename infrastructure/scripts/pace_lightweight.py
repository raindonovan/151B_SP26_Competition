#!/usr/bin/env python3
"""Lightweight PACE: identify still-broken items after slot1_minimal_norm,
classify by computability, prep verification on computable subset.
Output: results/pace/pace_today.csv with classification + placeholders for
sympy_result / sympy_confidence / notes to be filled in by downstream steps.
"""
import csv
import json
import os
import re
import sys
from collections import Counter

SLOT_PATH = 'submissions/slot1_minimal_norm.csv'
PRIVATE_PATH = 'private.jsonl'
OUT_DIR = 'results/pace'
os.makedirs(OUT_DIR, exist_ok=True)
OUT = f'{OUT_DIR}/pace_today.csv'


def extract_boxed(s):
    boxed = []
    i = 0
    while True:
        idx = s.find('\\boxed{', i)
        if idx == -1:
            break
        start = idx + len('\\boxed{')
        depth = 1
        j = start
        while j < len(s) and depth > 0:
            if s[j] == '{':
                depth += 1
            elif s[j] == '}':
                depth -= 1
            j += 1
        if depth == 0:
            boxed.append(s[start:j-1])
        i = j
    return boxed


def split_top_level(s):
    depth = 0
    parts = ['']
    for ch in s:
        if ch == '{':
            depth += 1
            parts[-1] += ch
        elif ch == '}':
            depth -= 1
            parts[-1] += ch
        elif ch == ',' and depth == 0:
            parts.append('')
        else:
            parts[-1] += ch
    return [p.strip() for p in parts if p.strip()]


def classify_computability(question):
    """Heuristic: is this question computable via sympy or symbolic methods?"""
    q = question.lower()
    if any(kw in q for kw in ['integral', '\\int', 'integrate', 'antiderivative']):
        return 'integral'
    if any(kw in q for kw in ['derivative', '\\frac{d', 'differentiate']):
        return 'derivative'
    if any(kw in q for kw in ['mean', 'median', 'mode', 'variance', 'standard deviation',
                                'covariance', 'correlation', 'regression coefficient',
                                'confidence interval', 'p-value', 'z-score', 't-statistic',
                                'chi-square', 'anova', 'f-statistic']):
        return 'statistics'
    if any(kw in q for kw in ['solve', 'equation', 'system', 'matrix', 'determinant',
                                'eigenvalue', 'inverse']):
        return 'algebra'
    if any(kw in q for kw in ['probability', 'binomial', 'poisson', 'normal distribution',
                                'expected value', 'variance']):
        return 'probability'
    if any(kw in q for kw in ['limit', 'series', 'sum', 'sequence']):
        return 'calculus'
    if any(kw in q for kw in ['proof', 'show that', 'prove']):
        return 'proof'  # NOT computable
    if any(kw in q for kw in ['explain', 'describe', 'interpret', 'discuss', 'comment']):
        return 'explanatory'  # NOT computable
    return 'unknown'


COMPUTABLE = {'integral', 'derivative', 'statistics', 'algebra', 'probability', 'calculus'}


def main():
    # Load multi-answer expected counts
    multi_answer = {}
    questions = {}
    with open(PRIVATE_PATH) as f:
        for line in f:
            item = json.loads(line)
            iid = int(item['id'])
            q = item.get('question', '')
            questions[iid] = q
            n = q.count('[ANS]')
            if n >= 2:
                multi_answer[iid] = n

    # Identify still-broken items in the slot
    broken = []
    with open(SLOT_PATH) as f:
        for row in csv.DictReader(f):
            iid = int(row['id'])
            if iid not in multi_answer:
                continue
            boxed = extract_boxed(row['response'])
            if not boxed:
                broken.append((iid, multi_answer[iid], 'no_box', None))
                continue
            last_values = split_top_level(boxed[-1])
            if len(last_values) < multi_answer[iid]:
                broken.append((iid, multi_answer[iid], 'under_count', boxed[-1]))

    print(f'Slot input:                       {SLOT_PATH}')
    print(f'Still-broken multi-answer items: {len(broken)}')

    classified = []
    for iid, expected_n, broken_kind, current_last in broken:
        q = questions.get(iid, '')
        comp_class = classify_computability(q)
        classified.append({
            'id': iid,
            'expected': expected_n,
            'broken_kind': broken_kind,
            'comp_class': comp_class,
            'computable': comp_class in COMPUTABLE,
            'q_preview': q[:200].replace('\n', ' '),
            'current_last_boxed': current_last,
        })

    class_counts = Counter(c['comp_class'] for c in classified)
    print('\nClass breakdown:')
    for cls, n in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f'  {cls:15s}  {n:3d}')

    computable_items = [c for c in classified if c['computable']]
    print(f'\nComputable subset: {len(computable_items)} items')

    with open(OUT, 'w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=['id', 'expected', 'broken_kind', 'comp_class',
                                                  'computable', 'q_preview', 'current_last_boxed',
                                                  'sympy_result', 'sympy_confidence', 'notes'])
        writer.writeheader()
        for c in classified:
            c['sympy_result'] = ''
            c['sympy_confidence'] = ''
            c['notes'] = ''
            writer.writerow(c)

    print(f'\nClassification CSV written: {OUT}')
    print('Next step: attempt sympy on computable subset, leave non-computable for Wolfram (via claude_strategy in chat).')


if __name__ == '__main__':
    main()
