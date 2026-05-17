#!/usr/bin/env python3
"""Auto-restart wrapper for run14b. Handles pod restarts and resumption.

Monitors run14b_launcher.sh output and automatically restarts on failure
until all 943 items are complete.

Usage:
    python3 scripts/run14b_autorestart.py

    Or in background:
    setsid python3 scripts/run14b_autorestart.py >> logs/run14b_autorestart.log 2>&1 < /dev/null &
"""

import subprocess
import time
import sys
from datetime import datetime
from pathlib import Path


def log(msg):
    """Log with timestamp."""
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def check_completion():
    """Check if run14b is complete (943 items)."""
    output_path = Path("results/run14b_sc8_v1_private943_tok32k_pp1.jsonl")
    if not output_path.exists():
        return 0, False

    try:
        lines = sum(1 for _ in open(output_path))
        is_complete = lines >= 943
        return lines, is_complete
    except Exception as e:
        log(f"ERROR reading output: {e}")
        return 0, False


def wait_for_completion(timeout_hours=6):
    """Wait for launcher to complete or timeout."""
    log(f"Waiting for launcher (timeout: {timeout_hours}h)...")
    start = time.time()
    timeout_sec = timeout_hours * 3600

    prev_lines = 0
    while True:
        elapsed = time.time() - start
        lines, is_complete = check_completion()

        if is_complete:
            log(f"✓ COMPLETE: {lines}/943 items done")
            return True

        if elapsed > timeout_sec:
            log(f"⚠ TIMEOUT after {elapsed/3600:.1f}h: {lines}/943 items")
            return False

        if lines > prev_lines:
            progress_pct = 100 * lines / 943
            log(f"Progress: {lines}/943 ({progress_pct:.1f}%)")
            prev_lines = lines

        time.sleep(30)  # Check every 30 seconds


def main():
    """Main loop: launch, wait, restart if needed."""
    launcher_script = Path("scripts/run14b_launcher.sh")
    max_retries = 100  # Allow many pod restarts

    if not launcher_script.exists():
        log(f"ERROR: {launcher_script} not found")
        sys.exit(1)

    log("Starting run14b auto-restart wrapper")
    log("========================================")

    for attempt in range(1, max_retries + 1):
        lines, is_complete = check_completion()

        if is_complete:
            log(f"✓ Run already complete: {lines}/943 items")
            break

        log(f"\n[Attempt {attempt}] Starting launcher (current: {lines}/943)")

        try:
            # Run launcher in foreground so we can see its output
            result = subprocess.run(
                ["bash", str(launcher_script)],
                timeout=6.5 * 3600,  # 6.5h timeout (account for startup overhead)
            )
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            log("Launcher timed out (expected at 6h walltime)")
            exit_code = -1
        except Exception as e:
            log(f"ERROR running launcher: {e}")
            exit_code = -1

        # Check if we've made progress
        lines_after, is_complete = check_completion()

        if is_complete:
            log(f"✓ Run complete: {lines_after}/943 items")
            break

        if lines_after == lines:
            log(f"⚠ No progress made (still {lines}/943). Waiting before retry...")
            time.sleep(60)
        else:
            log(f"Progress: {lines} → {lines_after} items (+{lines_after - lines})")

        if attempt < max_retries:
            log(f"Launcher exited (code {exit_code}). Restarting in 30s...")
            time.sleep(30)

    lines_final, is_complete = check_completion()
    if is_complete:
        log(f"\n✅ FINAL: {lines_final}/943 items complete")
        log("Run14b finished successfully")
        sys.exit(0)
    else:
        log(f"\n❌ FINAL: {lines_final}/943 items (incomplete after {max_retries} attempts)")
        sys.exit(1)


if __name__ == "__main__":
    main()
