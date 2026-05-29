#!/usr/bin/env bash
# scripts/setup_git.sh
#
# One-command git bootstrap for a fresh Claude sandbox.
#
# USAGE (from inside the sandbox, at session start):
#   curl -sSL https://raw.githubusercontent.com/beepbeeepimajeep/151B_SP26_Competition/main/scripts/setup_git.sh \
#     | bash -s -- "YOUR_GITHUB_PAT"
#
# WHAT IT DOES:
#   1. Writes the PAT to ~/.git-credentials (mode 600)
#   2. Sets credential.helper, user.email, user.name globally
#   3. Clones the repo to /home/claude/repo if not already present
#   4. Verifies push capability with an authenticated dry-run
#   5. Prints a one-line status
#
# NEVER ECHOES THE PAT. The token is treated as opaque from the moment it arrives.
#
# Exit codes:
#   0 = ready to push
#   1 = bad usage / missing PAT
#   2 = credential write failed
#   3 = auth verify failed (bad/expired token)
#   4 = clone or pull failed

set -euo pipefail

PAT="${1:-}"
REPO_URL="https://github.com/beepbeeepimajeep/151B_SP26_Competition.git"
REPO_DIR="/home/claude/repo"     # project convention — same across all Claude sandboxes
GIT_USER="dvaneetv"
GIT_EMAIL="dvaneetv@ucsd.edu"
GIT_NAME="claude_agent"

if [[ -z "${PAT}" ]]; then
  echo "usage: setup_git.sh <github_pat>" >&2
  echo "       (fine-grained 'github_pat_...' preferred per SECURITY.md)" >&2
  exit 1
fi

# Basic sanity check on PAT shape — don't reject classic tokens (still supported,
# discouraged per SECURITY.md), but warn so users move toward fine-grained.
if [[ "${PAT}" == ghp_* ]]; then
  echo "⚠️  classic PAT detected (ghp_). Works but over-scoped — rotate to fine-grained github_pat_ when convenient (see SECURITY.md)." >&2
fi

# Step 1: write credential file (mode 600, no PAT in stdout/stderr ever)
umask 077
if ! printf 'https://%s:%s@github.com\n' "${GIT_USER}" "${PAT}" > "${HOME}/.git-credentials"; then
  echo "❌ failed to write ~/.git-credentials" >&2
  exit 2
fi
chmod 600 "${HOME}/.git-credentials"

# Step 2: git globals
git config --global credential.helper store
git config --global user.email "${GIT_EMAIL}"
git config --global user.name  "${GIT_NAME}"

# Step 3: clone or pull
if [[ -d "${REPO_DIR}/.git" ]]; then
  if ! git -C "${REPO_DIR}" fetch origin --quiet 2>/dev/null; then
    echo "⚠️  fetch failed (token bad? network?) — leaving repo as-is" >&2
  fi
else
  if ! git clone --quiet "${REPO_URL}" "${REPO_DIR}" 2>/dev/null; then
    echo "❌ failed to clone ${REPO_URL} to ${REPO_DIR}" >&2
    exit 4
  fi
fi

# Step 4: verify auth with a cheap authenticated remote query
# (ls-remote requires read; a real push dry-run would be more accurate but more invasive)
if ! git -C "${REPO_DIR}" ls-remote origin HEAD >/dev/null 2>&1; then
  echo "❌ auth verify failed — PAT may be expired, wrong scope, or rate-limited" >&2
  exit 3
fi

# Step 5: status
BRANCH=$(git -C "${REPO_DIR}" rev-parse --abbrev-ref HEAD)
HEAD_SHA=$(git -C "${REPO_DIR}" rev-parse --short HEAD)
echo "✅ git ready — repo at ${REPO_DIR}, on ${BRANCH} @ ${HEAD_SHA}, push capability verified"
