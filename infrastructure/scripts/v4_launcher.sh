#!/bin/bash
# V4 temp-diversification run (with resume support).
# Launch: setsid bash scripts/v4_launcher.sh >> logs/V4_temp_diversification_fixed50_v1.log 2>&1 < /dev/null &
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
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] GPU free memory: ${free_gib} GiB (${free_mib} MiB). Threshold: ${min_gib} GiB."
    if [ "$free_gib" -lt "$min_gib" ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: GPU not free enough (need >=${min_gib} GiB, have ${free_gib} GiB). Kill stale processes first." >&2
        nvidia-smi >&2
        exit 1
    fi
}

LINES=$(wc -l < results/V4_temp_diversification_fixed50_v1.jsonl 2>/dev/null || echo 0)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V4 launcher started. ($LINES/$EXPECTED lines already done)."

check_cuda_lib
check_gpu_free 18

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting V4."

python3 scripts/run_vllm_sc.py \
  --run-id V4_temp_diversification_fixed50_v1 \
  --variant V4_temp_diversification \
  --slice "$SLICE" \
  --output results/V4_temp_diversification_fixed50_v1.jsonl \
  >> logs/V4_temp_diversification_fixed50_v1.log 2>&1

V4_LINES=$(wc -l < results/V4_temp_diversification_fixed50_v1.jsonl 2>/dev/null || echo 0)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] V4 done ($V4_LINES/$EXPECTED lines)."
