#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1
LOGDIR=results
OUTLOG="$LOGDIR/sft_inference_killer.out"
mkdir -p "$LOGDIR"
cur=$(grep -oP '✓ Batch \K[0-9]+' "$LOGDIR/sft_inference.log" | sort -n | tail -n1 || true)
if [ -z "$cur" ]; then cur=0; fi
next=$((cur+1))
echo "[watcher] waiting for Batch $next at $(date)" >> "$OUTLOG"
while ! grep -q "✓ Batch $next in" "$LOGDIR/sft_inference.log"; do sleep 5; done
echo "[watcher] detected Batch $next at $(date)" >> "$OUTLOG"
P="$LOGDIR/sftv3_epoch8_sc1_greedy.jsonl"
if [ -f "$P" ]; then
  # create a timestamped backup before fsyncing
  TS=$(date -u +%Y%m%dT%H%M%SZ)
  BAK="$LOGDIR/sftv3_epoch8_sc1_greedy.jsonl.bak.$TS"
  cp --preserve=mode,timestamps "$P" "$BAK" || echo "[watcher] backup cp failed" >> "$OUTLOG"
  # fsync the backup and original to ensure data is flushed
  python3 - <<'PY'
import os, sys
p = "results/sftv3_epoch8_sc1_greedy.jsonl"
bak = "results/sftv3_epoch8_sc1_greedy.jsonl.bak.%s" % (os.environ.get('TS',''))
if os.path.exists(p):
    with open(p, 'ab') as f:
        f.flush()
        os.fsync(f.fileno())
    print('fsynced', p)
else:
    print('no output file')
PY
else
  echo "[watcher] no output file to fsync at $(date)" >> "$OUTLOG"
fi
# Send SIGINT to running tmux session to allow graceful shutdown, then kill session
if tmux ls | grep -q '^sft_run:' 2>/dev/null; then
  tmux send-keys -t sft_run C-c
  sleep 2
  tmux kill-session -t sft_run || true
else
  echo "[watcher] tmux session sft_run not found" >> "$OUTLOG"
fi
sync
echo "[watcher] stopped at $(date)" >> "$OUTLOG"
