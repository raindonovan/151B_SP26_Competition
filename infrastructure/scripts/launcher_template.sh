#!/bin/bash
# Launcher template for future runs. Copy and customize.
#
# Usage:
#   cp scripts/launcher_template.sh scripts/run<N>_launcher.sh
#   # Edit run<N>_launcher.sh to set RUN_ID, VARIANT, DATA_PATH, etc.
#   setsid bash scripts/run<N>_launcher.sh >> logs/run<N>.log 2>&1 < /dev/null &

cd /home/dvaneetv/private/151B_SP26_Competition
mkdir -p logs results

export LD_LIBRARY_PATH=$HOME/private/.local/lib/python3.13/site-packages/nvidia/cu13/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$HOME/private/.local/lib/python3.13/site-packages:$PYTHONPATH

# ===== CUSTOMIZE THESE =====
RUN_ID="run<N>"
VARIANT="V0_baseline"
DATA_PATH="private.jsonl"
DATA_END=943
MAX_NEW_TOKENS=32768
MAX_MODEL_LEN=36864
OUTPUT="results/${RUN_ID}.jsonl"
# ==========================

source scripts/gpu_cleanup.sh

LINES=$(wc -l < "$OUTPUT" 2>/dev/null || echo 0)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $RUN_ID launcher started. ($LINES/$DATA_END lines already done)."

check_gpu_ready 18

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting $RUN_ID."

python3 scripts/run_vllm_sc.py \
  --run-id "$RUN_ID" \
  --variant "$VARIANT" \
  --data-path "$DATA_PATH" \
  --data-end "$DATA_END" \
  --max-new-tokens "$MAX_NEW_TOKENS" \
  --max-model-len "$MAX_MODEL_LEN" \
  --output "$OUTPUT"

LINES=$(wc -l < "$OUTPUT" 2>/dev/null || echo 0)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $RUN_ID done ($LINES/$DATA_END lines)."
