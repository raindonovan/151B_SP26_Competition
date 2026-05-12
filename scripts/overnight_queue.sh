#!/bin/bash
# Sequential V1 → V2 queue, runs after V0 completes.
# Launch: nohup scripts/overnight_queue.sh > logs/overnight_queue.log 2>&1 &
set -e
cd /home/dvaneetv/private/151B_SP26_Competition

export LD_LIBRARY_PATH=$HOME/private/.local/lib/python3.13/site-packages/nvidia/cu13/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$HOME/private/.local/lib/python3.13/site-packages:$PYTHONPATH

SLICE=data/slices/fixed_50_v1.json
EXPECTED=50

V0_PID=$(cat /tmp/v0_baseline.pid)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Waiting for V0 (PID $V0_PID)..."
while ps -p "$V0_PID" > /dev/null 2>&1; do sleep 30; done

V0_LINES=$(wc -l < results/V0_baseline_fixed50_v1.jsonl 2>/dev/null || echo 0)
if [ "$V0_LINES" -ne "$EXPECTED" ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: V0 produced $V0_LINES lines, expected $EXPECTED. Check logs/V0_baseline_fixed50_v1.log."
  exit 1
fi
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V0 done ($V0_LINES lines). Starting V1."

python3 scripts/run_vllm_sc.py \
  --run-id V1_counting_top_fixed50_v1 \
  --variant V1_counting_top \
  --slice "$SLICE" \
  --output results/V1_counting_top_fixed50_v1.jsonl \
  > logs/V1_counting_top_fixed50_v1.log 2>&1

V1_LINES=$(wc -l < results/V1_counting_top_fixed50_v1.jsonl 2>/dev/null || echo 0)
if [ "$V1_LINES" -ne "$EXPECTED" ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: V1 produced $V1_LINES lines, expected $EXPECTED. Check logs/V1_counting_top_fixed50_v1.log."
  exit 1
fi
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V1 done ($V1_LINES lines). Starting V2."

python3 scripts/run_vllm_sc.py \
  --run-id V2_counting_bookend_fixed50_v1 \
  --variant V2_counting_bookend \
  --slice "$SLICE" \
  --output results/V2_counting_bookend_fixed50_v1.jsonl \
  > logs/V2_counting_bookend_fixed50_v1.log 2>&1

V2_LINES=$(wc -l < results/V2_counting_bookend_fixed50_v1.jsonl 2>/dev/null || echo 0)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V2 done ($V2_LINES lines). Queue complete."
