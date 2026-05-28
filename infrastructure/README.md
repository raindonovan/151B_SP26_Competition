# infrastructure/ — Build, Deploy, Compute Setup

Launcher scripts, GPU cleanup, pre-flight checks, watchdog, compute configs.

## Contents
- `scripts/` — launchers, gpu_cleanup.sh, overnight_queue.sh, push_watchdog.sh
- `pre_flight/` — pre-flight audit and production command docs
- `requirements_thunder.txt` — Thunder Compute dependencies

## Compute environments
- DSMLP: A30 24GB, 6hr walltime
- Thunder: H100/A100 via tnr CLI (shut down, snapshots preserved)
