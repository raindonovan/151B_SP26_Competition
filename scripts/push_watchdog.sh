#!/bin/bash
# Periodic results-push watchdog for Thunder inference runs.
#
# Usage: ./scripts/push_watchdog.sh <branch-name> [interval-seconds]
# Default interval: 300 (5 minutes)
# Stop with: kill %1   (if backgrounded with &) or  kill <PID>
#
# Looks for changes under results/ at each tick and, if any, commits + pushes.
# Designed to run on Thunder where the repo lives at ~/151B_SP26_Competition.

BRANCH=$1
INTERVAL=${2:-300}

if [ -z "$BRANCH" ]; then
    echo "Usage: $0 <branch-name> [interval-seconds]" >&2
    exit 1
fi

cd ~/151B_SP26_Competition || exit 1

git rev-parse --abbrev-ref HEAD | grep -qx "$BRANCH" || {
    echo "Watchdog: not on branch $BRANCH (current: $(git rev-parse --abbrev-ref HEAD)), exiting" >&2
    exit 1
}

echo "Watchdog started on branch $BRANCH, interval ${INTERVAL}s"

while sleep "$INTERVAL"; do
    if [ -n "$(git status -s results/)" ]; then
        git add results/
        git commit -m "watchdog snapshot $(date -u +%Y-%m-%dT%H:%M:%SZ)" >/dev/null 2>&1
        git push origin "$BRANCH" 2>&1 | tail -2
    fi
done
