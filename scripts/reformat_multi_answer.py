#!/usr/bin/env python3
"""Repair multi-answer items where LAST \boxed{} has fewer values than expected.
Consolidates dedup'd values from earlier boxes into a single canonical \boxed{a, b, c}.
SAFE: only modifies items where unique-value count >= expected; skips under-generation.
NEVER touches single-answer items or items where LAST already has expected count.
"""
import csv, re, json, sys

def extract_boxed_with_pos(s):
    boxed = []
    i = 0
    while True:
        idx = s.find('\\boxed{', i)
        if idx == -1: break
        start = idx + len('\\boxed{')
        depth = 1; j = start
        while j < len(s) and depth > 0:
            if s[j] == '{': depth += 1
            elif s[j] == '}': depth -= 1
            j += 1
        if depth == 0:
            boxed.append((idx, j, s[start:j-1]))
        i = j
    return boxed

def split_top_level(s):
    depth = 0; parts = ['']
    for ch in s:
        if ch == '{': depth += 1; parts[-1] += ch
        elif ch == '}': depth -= 1; parts[-1] += ch
        elif ch == ',' and depth == 0: parts.append('')
        else: parts[-1] += ch
    return [p.strip() for p in parts if p.strip()]

def repair(response, expected_n):
    boxed = extract_boxed_with_pos(response)
    if not boxed:
        return None, 'no_box'
    last_idx, last_end, last_content = boxed[-1]
    last_values = split_top_level(last_content)
    if len(last_values) >= expected_n:
        return None, 'already_canonical'
    all_values = []
    for _, _, content in boxed:
        all_values.extend(split_top_level(content))
    deduped = []
    for v in all_values:
        if not deduped or deduped[-1] != v:
            deduped.append(v)
    if len(deduped) < expected_n:
        return None, 'under_generation'
    new_values = deduped[-expected_n:]
    new_boxed = '\\boxed{' + ', '.join(new_values) + '}'
    new_response = response[:last_idx] + new_boxed + response[last_end:]
    return new_response, 'repaired'

def main():
    if len(sys.argv) != 4:
        print('usage: reformat_multi_answer.py <input.csv> <private.jsonl> <output.csv>')
        sys.exit(1)
    in_csv, private_jsonl, out_csv = sys.argv[1:]
    multi_answer = {}
    with open(private_jsonl) as f:
        for line in f:
            item = json.loads(line)
            n_ans = item.get('question', '').count('[ANS]')
            if n_ans >= 2:
                multi_answer[int(item['id'])] = n_ans
    stats = {'repaired':0, 'already_canonical':0, 'under_generation':0, 'no_box':0, 'not_multi':0}
    examples = []
    with open(in_csv) as f, open(out_csv, 'w') as out:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(out, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            iid = int(row['id'])
            if iid not in multi_answer:
                stats['not_multi'] += 1
                writer.writerow(row); continue
            new_response, status = repair(row['response'], multi_answer[iid])
            stats[status] += 1
            if status == 'repaired' and len(examples) < 8:
                old_last = extract_boxed_with_pos(row['response'])[-1][2]
                new_last = extract_boxed_with_pos(new_response)[-1][2]
                examples.append((iid, multi_answer[iid], old_last[:60], new_last[:60]))
                row['response'] = new_response
            elif status == 'repaired':
                row['response'] = new_response
            writer.writerow(row)
    print(f'Stats: {stats}')
    print(f'\nRepaired examples (id, expected, old_last, new_last):')
    for iid, exp, old, new in examples:
        print(f'  id={iid:4d}  exp={exp}  {old!r} -> {new!r}')

if __name__ == '__main__':
    main()
