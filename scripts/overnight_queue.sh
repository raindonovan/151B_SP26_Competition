#!/bin/bash
# V1 resume (5 remaining) → V2 full run.
# Launch: setsid bash scripts/overnight_queue.sh > logs/overnight_queue.log 2>&1 < /dev/null &
set -e
cd /home/dvaneetv/private/151B_SP26_Competition
mkdir -p logs results

export LD_LIBRARY_PATH=$HOME/private/.local/lib/python3.13/site-packages/nvidia/cu13/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$HOME/private/.local/lib/python3.13/site-packages:$PYTHONPATH

SLICE=data/slices/fixed_50_v1.json
EXPECTED=50

check_cuda_lib() {
    if [ ! -f "$HOME/private/.local/lib/python3.13/site-packages/nvidia/cu13/lib/libcudart.so.13" ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: libcudart.so.13 not found. Check LD_LIBRARY_PATH." >&2
        exit 1
    fi
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] libcudart.so.13 OK."
}

check_gpu_free() {
    local min_gib=${1:-18}
    local free_mib
    free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')
    if [ -z "$free_mib" ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARNING: nvidia-smi unavailable, skipping GPU free-memory check."
        return 0
    fi
    local free_gib=$(( free_mib / 1024 ))
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] GPU free memory: ${free_gib} GiB. Threshold: ${min_gib} GiB."
    if [ "$free_gib" -lt "$min_gib" ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: GPU not free (need >=${min_gib} GiB, have ${free_gib} GiB). Kill stale processes first." >&2
        nvidia-smi >&2
        exit 1
    fi
}

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Queue started. Resuming V1 ($(wc -l < results/V1_counting_top_fixed50_v1.jsonl 2>/dev/null || echo 0)/$EXPECTED lines already done)."
check_cuda_lib
check_gpu_free 18

python3 scripts/run_vllm_sc.py \
  --run-id V1_counting_top_fixed50_v1 \
  --variant V1_counting_top \
  --slice "$SLICE" \
  --max-model-len 20480 \
  --max-new-tokens 16384 \
  --output results/V1_counting_top_fixed50_v1.jsonl \
  >> logs/V1_counting_top_fixed50_v1.log 2>&1

V1_LINES=$(wc -l < results/V1_counting_top_fixed50_v1.jsonl 2>/dev/null || echo 0)
if [ "$V1_LINES" -ne "$EXPECTED" ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: V1 produced $V1_LINES lines, expected $EXPECTED. Check logs/V1_counting_top_fixed50_v1.log."
  exit 1
fi
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V1 done ($V1_LINES lines). Sleeping 30s for EngineCore CUDA cleanup..."
sleep 30
check_gpu_free 18
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting V2."

python3 scripts/run_vllm_sc.py \
  --run-id V2_counting_bookend_fixed50_v1 \
  --variant V2_counting_bookend \
  --slice "$SLICE" \
  --max-model-len 20480 \
  --max-new-tokens 16384 \
  --output results/V2_counting_bookend_fixed50_v1.jsonl \
  > logs/V2_counting_bookend_fixed50_v1.log 2>&1

V2_LINES=$(wc -l < results/V2_counting_bookend_fixed50_v1.jsonl 2>/dev/null || echo 0)
if [ "$V2_LINES" -ne "$EXPECTED" ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: V2 produced $V2_LINES lines, expected $EXPECTED. Check logs/V2_counting_bookend_fixed50_v1.log."
  exit 1
fi
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V2 done ($V2_LINES lines). Queue complete."
