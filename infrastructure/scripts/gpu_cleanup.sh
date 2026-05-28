#!/bin/bash
# GPU cleanup utilities for ML launchers.
# Source this script and call kill_stale_enginecore before launching vLLM.
#
# Usage:
#   source scripts/gpu_cleanup.sh
#   kill_stale_enginecore
#   check_gpu_ready

kill_stale_enginecore() {
    local used_mib used_gib pids
    used_mib=$(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null | \
               grep "VLLM::EngineCore" | awk '{sum+=$NF} END {print sum}')

    if [ -z "$used_mib" ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] No stale EngineCore found."
        return 0
    fi

    used_gib=$(( used_mib / 1024 ))

    # If EngineCore is using >15 GiB, it's definitely stale (process should be dead, GPU cleaned)
    if [ "$used_gib" -gt 15 ]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARNING: Stale EngineCore using ${used_gib} GiB. Killing..."
        pids=$(nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader 2>/dev/null | \
               grep "VLLM::EngineCore" | awk '{print $1}')
        for pid in $pids; do
            kill -9 "$pid" 2>/dev/null
        done
        sleep 2
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] EngineCore cleanup complete."
    fi
}

check_cuda_lib() {
    if ! ldconfig -p 2>/dev/null | grep -q libcudart; then
        if [ ! -f "$HOME/private/.local/lib/python3.13/site-packages/nvidia/cu13/lib/libcudart.so.13" ]; then
            echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: libcudart.so.13 not found. Check LD_LIBRARY_PATH." >&2
            exit 1
        fi
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
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ABORT: GPU not free enough (need >=${min_gib} GiB, have ${free_gib} GiB)." >&2
        nvidia-smi >&2
        exit 1
    fi
}

check_gpu_ready() {
    local min_gib=${1:-18}
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] === GPU Health Check ==="
    check_cuda_lib
    kill_stale_enginecore
    check_gpu_free "$min_gib"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] GPU ready."
}
