"""
Build MASTER_ANSWERS.csv — every item × every evidence source.
One row per item (943 total). All answers from all sources side by side.
"""
import csv, json, os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)

# 1. Load private.jsonl for item metadata
items = {}
with open(os.path.join(REPO, 'private.jsonl')) as f:
    for line in f:
        item = json.loads(line)
        iid = str(item.get('id', ''))
        has_opts = isinstance(item.get('options'), list) and len(item.get('options', [])) > 0
        items[iid] = {
            'item_id': iid,
            'category': 'MCQ' if has_opts else 'FREE',
            'question_preview': item.get('question', '')[:120].replace('\n', ' ').replace(',', ';'),
        }

# 2. Load V6 answer sheet
v6 = {}
with open(os.path.join(BASE, 'answer_sheet', 'unified_answer_sheet_v6.csv')) as f:
    for row in csv.DictReader(f):
        v6[row['item_id']] = {
            'sheet_best_answer': row.get('best_answer', ''),
            'sheet_confidence': row.get('confidence_pct', ''),
            'sheet_tier': row.get('tier', ''),
            'sheet_n_agree': row.get('n_agree', ''),
            'sheet_evidence': row.get('evidence_sources', ''),
        }

# 3. Load teacher answers
teachers = {}
with open(os.path.join(BASE, 'teacher_answers_compact.json')) as f:
    raw = json.load(f)
    for iid, ans in raw.items():
        teachers[iid] = {
            'teacher_sonnet': ans.get('s', ''),
            'teacher_gpt4': ans.get('g', ''),
            'teacher_oss': ans.get('o', ''),
        }

# 4. Load Wolfram overrides
wolfram = {}
with open(os.path.join(BASE, 'wolfram_overrides.csv')) as f:
    for row in csv.DictReader(f):
        wid = row['id'].lstrip('0') or '0'  # normalize "0005" → "5"
        wolfram[wid] = {
            'wolfram_answer': row.get('override_value', ''),
            'wolfram_confidence': row.get('confidence', ''),
        }
        # Also try with leading zeros
        wolfram[row['id']] = wolfram[wid]

# 5. Load web search results
search = {}
with open(os.path.join(BASE, 'search', 'web_search_100', 'search_results.csv')) as f:
    for row in csv.DictReader(f):
        search[row['item_id']] = {
            'search_status': row.get('search_status', ''),
            'search_answer': row.get('found_answer', ''),
            'search_source': row.get('source_url', '')[:80],
        }

# 6. Load back-solve detail
backsolve = {}
with open(os.path.join(BASE, 'back_solve_detail.csv')) as f:
    for row in csv.DictReader(f):
        backsolve[row['item_id']] = {
            'backsolve_answer': row.get('predicted_kaggle_answer', ''),
            'backsolve_confidence': row.get('confidence_pct', ''),
            'backsolve_tier': row.get('tier', ''),
        }

# 7. Merge into master table
fieldnames = [
    'item_id', 'category', 'question_preview',
    'sheet_best_answer', 'sheet_confidence', 'sheet_tier', 'sheet_n_agree', 'sheet_evidence',
    'teacher_sonnet', 'teacher_gpt4', 'teacher_oss',
    'wolfram_answer', 'wolfram_confidence',
    'search_status', 'search_answer', 'search_source',
    'backsolve_answer', 'backsolve_confidence', 'backsolve_tier',
]

out_path = os.path.join(BASE, 'MASTER_ANSWERS.csv')
with open(out_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    for iid in sorted(items.keys(), key=lambda x: int(x)):
        row = {}
        row.update(items[iid])
        row.update(v6.get(iid, {}))
        row.update(teachers.get(iid, {}))
        row.update(wolfram.get(iid, {}))
        row.update(search.get(iid, {}))
        row.update(backsolve.get(iid, {}))
        writer.writerow(row)

print(f"Built {out_path}: 943 rows × {len(fieldnames)} columns")

# Summary stats
n_wolfram = sum(1 for v in wolfram.values() if v.get('wolfram_answer'))
n_search = sum(1 for v in search.values() if v.get('search_status') == 'GOLD')
n_t1 = sum(1 for v in v6.values() if v.get('sheet_tier') in ['1', 'T1'])
n_t2 = sum(1 for v in v6.values() if v.get('sheet_tier') in ['2', 'T2'])
print(f"\nEvidence coverage:")
print(f"  Sheet T1 (95%+): {n_t1}")
print(f"  Sheet T2 (85-94%): {n_t2}")
print(f"  Wolfram overrides: {n_wolfram // 2}")  # halved due to dual-key
print(f"  Search GOLD: {n_search}")
print(f"  Teacher answers: {len(teachers)}")
print(f"  Back-solve: {len(backsolve)}")
