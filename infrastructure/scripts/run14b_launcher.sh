#!/bin/bash
# run14b: V0_baseline SC-8 on private.jsonl (943 items, 32k tokens).
# Launch: setsid bash scripts/run14b_launcher.sh >> logs/run14b_sc8_v1_private943_tok32k_pp1.log 2>&1 < /dev/null &
cd /home/dvaneetv/private/151B_SP26_Competition
mkdir -p logs results

export LD_LIBRARY_PATH=$HOME/private/.local/lib/python3.13/site-packages/nvidia/cu13/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$HOME/private/.local/lib/python3.13/site-packages:$PYTHONPATH

OUTPUT=results/run14b_sc8_v1_private943_tok32k_pp1.jsonl
EXPECTED=943

source scripts/gpu_cleanup.sh

LINES=$(wc -l < "$OUTPUT" 2>/dev/null || echo 0)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] run14b launcher started. ($LINES/$EXPECTED lines already done)."

kill_stale_enginecore
check_cuda_lib

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting run14b."

python3 scripts/run_vllm_sc.py \
  --run-id run14b_sc8_v1_private943_tok32k_pp1 \
  --variant V0_baseline \
  --data-path private.jsonl \
  --data-end 943 \
  --max-new-tokens 32768 \
  --max-model-len 36864 \
  --output "$OUTPUT"

LINES=$(wc -l < "$OUTPUT" 2>/dev/null || echo 0)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] run14b done ($LINES/$EXPECTED lines)."
