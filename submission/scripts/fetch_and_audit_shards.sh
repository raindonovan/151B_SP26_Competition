#!/usr/bin/env bash
set -euo pipefail

# Fetch adapter shard CSVs from Thunder boxes and validate them before splice.
#
# Usage:
#   bash submission/scripts/fetch_and_audit_shards.sh --dry-run
#   bash submission/scripts/fetch_and_audit_shards.sh

ROOT="${ROOT:-$HOME/151B_SP26_Competition}"
SUB_DIR="$ROOT/submission"
SSH_USER="${SSH_USER:-ubuntu}"
CONNECT_TIMEOUT="${CONNECT_TIMEOUT:-10}"
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    *)
      echo "Unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

declare -a SHARDS=(
  "tnr-0:v5_part_tnr0.csv"
  "tnr-1:v5_part_tnr1.csv"
  "tnr-02:v5_part_tnr02.csv"
  "tnr-3:v5_part_tnr3.csv"
)

mkdir -p "$SUB_DIR"
cd "$SUB_DIR"

echo "== fetch plan =="
for spec in "${SHARDS[@]}"; do
  host="${spec%%:*}"
  file="${spec##*:}"
  remote_csv="$SSH_USER@$host:~/151B_SP26_Competition/submission/$file"
  remote_jsonl="$SSH_USER@$host:~/151B_SP26_Competition/results/inference_run.jsonl"
  local_tmp="${file}.tmp"
  local_out="${file}"
  echo "  prefer CSV: $remote_csv -> $SUB_DIR/$local_out"
  echo "  fallback JSONL: $remote_jsonl -> reconstructed $SUB_DIR/$local_out"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    rm -f "$local_tmp"
    # Prefer shard CSV if it exists and has at least 1 data row.
    if ssh -o ConnectTimeout="$CONNECT_TIMEOUT" "$SSH_USER@$host" \
      "python3 - <<'PY'
import csv
from pathlib import Path
p = Path('~/151B_SP26_Competition/submission/$file').expanduser()
if not p.exists():
    raise SystemExit(1)
with p.open(newline='', encoding='utf-8') as f:
    rd = csv.DictReader(f)
    rows = sum(1 for _ in rd)
if rows <= 0:
    raise SystemExit(2)
print(rows)
PY" >/dev/null 2>&1; then
      echo "  [$host] using shard CSV $file"
      scp -o ConnectTimeout="$CONNECT_TIMEOUT" "$remote_csv" "$local_tmp"
    else
      echo "  [$host] shard CSV missing/empty; reconstructing from results/inference_run.jsonl"
      ssh -o ConnectTimeout="$CONNECT_TIMEOUT" "$SSH_USER@$host" \
        "python3 - <<'PY'
import csv, json, sys
from pathlib import Path
p = Path('~/151B_SP26_Competition/results/inference_run.jsonl').expanduser()
if not p.exists():
    raise SystemExit('missing results/inference_run.jsonl')
rows = {}
with p.open(encoding='utf-8') as f:
    for ln in f:
        ln = ln.strip()
        if not ln:
            continue
        try:
            o = json.loads(ln)
        except Exception:
            continue
        iid = o.get('id')
        ans = o.get('voted_answer')
        if iid is None or ans is None:
            continue
        ans = str(ans)
        if not ans.strip():
            continue
        try:
            iid = int(iid)
        except Exception:
            continue
        rows[iid] = ans
if not rows:
    raise SystemExit('no usable id/voted_answer rows in inference_run.jsonl')
w = csv.DictWriter(sys.stdout, fieldnames=['id','response'])
w.writeheader()
for iid in sorted(rows):
    w.writerow({'id': iid, 'response': rows[iid]})
PY" > "$local_tmp"
    fi
    mv "$local_tmp" "$local_out"
  fi
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "DRY RUN only; no files copied."
  exit 0
fi

echo
echo "== basic file presence =="
ls -lh v5_part_tnr*.csv

echo
echo "== schema/rows audit =="
python3 - <<'PY'
import csv
from pathlib import Path

sub = Path(".")
files = [
    "v5_part_tnr0.csv",
    "v5_part_tnr1.csv",
    "v5_part_tnr02.csv",
    "v5_part_tnr3.csv",
]

all_ids = {}
for name in files:
    p = sub / name
    if not p.exists():
        raise SystemExit(f"FAIL missing file: {name}")
    with p.open(newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames != ["id", "response"]:
            raise SystemExit(f"FAIL bad schema in {name}: {rd.fieldnames}")
        rows = list(rd)
    if not rows:
        raise SystemExit(f"FAIL empty shard: {name}")
    ids = []
    empties = 0
    for r in rows:
        try:
            iid = int(str(r["id"]).strip())
        except Exception:
            raise SystemExit(f"FAIL non-int id in {name}: {r.get('id')!r}")
        ids.append(iid)
        if not (r.get("response") or "").strip():
            empties += 1
    if len(ids) != len(set(ids)):
        raise SystemExit(f"FAIL duplicate ids inside {name}")
    for iid, r in zip(ids, rows):
        prev = all_ids.get(iid)
        if prev is not None and prev != r["response"]:
            raise SystemExit(f"FAIL id collision across shards: id={iid}")
        all_ids[iid] = r["response"]
    print(f"OK {name}: rows={len(rows)} ids={len(ids)} empty_responses={empties}")

print(f"OK total_unique_override_ids={len(all_ids)}")
PY

echo
echo "Shard fetch+audit PASS."
