"""
Select 100 search candidates from silver-tier items.
Matches the MCQ/free-form distribution of the full dataset.
Prioritizes higher-confidence items (more likely to validate).
"""
import json
import csv
import random
import os

# Load private.jsonl
items_by_id = {}
with open(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'private.jsonl')) as f:
    for line in f:
        item = json.loads(line)
        items_by_id[str(item.get('id', ''))] = item

# Categorize items
def categorize(item):
    if isinstance(item.get('options'), list) and item['options']:
        return 'MCQ'
    else:
        return 'FREE'

# Load answer sheet if available, otherwise use placeholder confidence
answer_sheet_path = os.path.join(os.path.dirname(__file__), '..', '..', 'answer_sheet')
sheet_data = {}

# Try to load any available answer sheet
for fname in ['unified_answer_sheet_v6.csv', 'unified_answer_sheet_legacy.csv']:
    fpath = os.path.join(answer_sheet_path, fname) if fname != 'unified_answer_sheet_legacy.csv' else os.path.join(os.path.dirname(__file__), '..', '..', fname)
    if os.path.exists(fpath):
        try:
            with open(fpath) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item_id = str(row.get('item_id', row.get('id', '')))
                    conf = row.get('confidence_pct', row.get('confidence', '50'))
                    try:
                        sheet_data[item_id] = float(conf)
                    except:
                        sheet_data[item_id] = 50.0
            print(f"Loaded {len(sheet_data)} items from {fname}")
            break
        except Exception as e:
            print(f"Failed to load {fname}: {e}")

# Build candidate pool: silver tier (50-89% confidence)
silver = []
for item_id, item in items_by_id.items():
    conf = sheet_data.get(item_id, 50.0)
    if 50 <= conf < 90:
        cat = categorize(item)
        silver.append({
            'item_id': item_id,
            'category': cat,
            'confidence': conf,
            'question_preview': item.get('question', '')[:100].replace('\n', ' ')
        })

# Sort by confidence descending (higher confidence = more likely to validate)
silver.sort(key=lambda x: x['confidence'], reverse=True)

# Distribution: 32% MCQ, 68% FREE (matching full dataset)
mcq_target = 32
free_target = 68

mcq_pool = [s for s in silver if s['category'] == 'MCQ']
free_pool = [s for s in silver if s['category'] == 'FREE']

# Take top N from each category (highest confidence first)
selected_mcq = mcq_pool[:mcq_target]
selected_free = free_pool[:free_target]
selected = selected_mcq + selected_free

print(f"\nSilver pool: {len(silver)} items ({len(mcq_pool)} MCQ, {len(free_pool)} FREE)")
print(f"Selected: {len(selected)} items ({len(selected_mcq)} MCQ, {len(selected_free)} FREE)")

# Write candidates CSV
out_path = os.path.join(os.path.dirname(__file__), 'candidates_100.csv')
with open(out_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['item_id', 'category', 'confidence', 'question_preview'])
    writer.writeheader()
    for s in selected:
        writer.writerow(s)

# Write empty search results tracker
tracker_path = os.path.join(os.path.dirname(__file__), 'search_results.csv')
with open(tracker_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'item_id', 'category', 'search_status', 'found_answer', 
        'source_url', 'source_type', 'confidence', 'notes'
    ])
    writer.writeheader()
    for s in selected:
        writer.writerow({
            'item_id': s['item_id'],
            'category': s['category'],
            'search_status': 'UNSEARCHED',
            'found_answer': '',
            'source_url': '',
            'source_type': '',
            'confidence': s['confidence'],
            'notes': ''
        })

print(f"Wrote {out_path}")
print(f"Wrote {tracker_path}")
