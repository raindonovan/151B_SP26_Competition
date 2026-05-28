#!/bin/bash
# Waits for the V1/V2 queue to finish, then runs V3 (with resume support).
cd /home/dvaneetv/private/151B_SP26_Competition
mkdir -p logs results

export LD_LIBRARY_PATH=$HOME/private/.local/lib/python3.13/site-packages/nvidia/cu13/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$HOME/private/.local/lib/python3.13/site-packages:$PYTHONPATH

SLICE=data/slices/fixed_50_v1.json
EXPECTED=50
QUEUE_PID=$(cat /tmp/overnight_queue.pid 2>/dev/null || echo "")

# Verify libcudart is reachable before any vLLM launch.
check_cuda_lib() {
    if ! ldconfig -p 2>/dev/null | grep -q libcudart; then
        if [ ! -f "$HOME/private/.local/lib/python3.13/site-packages/nvidia/cu13/lib/libcudart.so.13" ]; then
            echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: libcudart.so.13 not found. Check LD_LIBRARY_PATH." >&2
            exit 1
        fi
    fi
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] libcudart.so.13 OK."
}

# Check GPU free memory (GiB). Abort if less than threshold.
check_gpu_free() {
    local min_gib=${1:-18}
    local free_mib
    free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')
    if [ -z "$free_mib" ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARNING: nvidia-smi unavailable, skipping GPU free-memory check."
        return 0
    fi
    local free_gib=$(( free_mib / 1024 ))
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] GPU free memory: ${free_gib} GiB (${free_mib} MiB). Threshold: ${min_gib} GiB."
    if [ "$free_gib" -lt "$min_gib" ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: GPU not free enough (need >=${min_gib} GiB, have ${free_gib} GiB). Kill stale processes first." >&2
        nvidia-smi >&2
        exit 1
    fi
}

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V3 launcher started. Waiting for queue (PID $QUEUE_PID) to finish..."

# Wait for queue process to exit — this guarantees V2 is done and GPU is free.
if [ -n "$QUEUE_PID" ]; then
    while kill -0 "$QUEUE_PID" 2>/dev/null; do
        sleep 30
    done
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Queue exited. Sleeping 30s for EngineCore CUDA cleanup..."
sleep 30

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Verifying V2..."
V2_LINES=$(wc -l < results/V2_counting_bookend_fixed50_v1.jsonl 2>/dev/null || echo 0)
if [ "$V2_LINES" -ne "$EXPECTED" ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: V2 has $V2_LINES lines (expected $EXPECTED). Not launching V3."
    exit 1
fi

check_cuda_lib
check_gpu_free 18

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V2 verified ($V2_LINES lines). Starting V3."

python3 scripts/run_vllm_sc.py \
  --run-id V3_shape_filter_fixed50_v1 \
  --variant V3_shape_filter \
  --slice "$SLICE" \
  --output results/V3_shape_filter_fixed50_v1.jsonl \
  >> logs/V3_shape_filter_fixed50_v1.log 2>&1

V3_LINES=$(wc -l < results/V3_shape_filter_fixed50_v1.jsonl 2>/dev/null || echo 0)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V3 done ($V3_LINES/$EXPECTED lines)."
