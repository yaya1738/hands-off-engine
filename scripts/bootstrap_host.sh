#!/usr/bin/env bash
set -euo pipefail

# Provider-neutral host bootstrap. This script never copies secrets, asks for
# trading credentials, provisions cloud resources, or enables live financial execution.

SSH_HOST="${1:-}"
REMOTE_ROOT="${2:-}"
REPO_URL="${REPO_URL:-https://github.com/yaya1738/hands-off-engine.git}"
REF="${REF:-main}"

if [[ -z "$SSH_HOST" ]]; then
  echo "Usage: $0 <ssh-host> [remote-repo-path]" >&2
  exit 2
fi

ssh -o BatchMode=yes -o ConnectTimeout=10 "$SSH_HOST" 'printf "connected\n"'

ssh "$SSH_HOST" "REPO_URL='$REPO_URL' REF='$REF' REMOTE_ROOT='$REMOTE_ROOT' bash -s" <<'REMOTE'
set -euo pipefail

REMOTE_ROOT="${REMOTE_ROOT:-$HOME/hands-off-engine}"

sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-pip git curl jq tmux

if [[ -d "$REMOTE_ROOT/.git" ]]; then
  git -C "$REMOTE_ROOT" fetch --prune origin
  git -C "$REMOTE_ROOT" checkout "$REF"
  git -C "$REMOTE_ROOT" reset --hard "origin/$REF"
else
  mkdir -p "$(dirname "$REMOTE_ROOT")"
  git clone --branch "$REF" --single-branch "$REPO_URL" "$REMOTE_ROOT"
fi

python3 -m venv "$REMOTE_ROOT/.venv"
"$REMOTE_ROOT/.venv/bin/python" -m pip install --disable-pip-version-check --upgrade pip
if [[ -f "$REMOTE_ROOT/requirements.txt" ]]; then
  "$REMOTE_ROOT/.venv/bin/pip" install --disable-pip-version-check -r "$REMOTE_ROOT/requirements.txt"
fi

# Install the existing persistent Factory user service. No credentials are copied.
cd "$REMOTE_ROOT"
bash deploy/install-user-runtime.sh

# Explicitly verify the financial kill switch without attempting execution.
"$REMOTE_ROOT/.venv/bin/python" - <<'PY'
from scripts.autonomous_daemon import LIVE_TRADING_ENABLED
assert LIVE_TRADING_ENABLED is False
print("live financial execution: HARD-DISABLED")
PY

printf '\nbootstrap complete: %s\n' "$REMOTE_ROOT"
REMOTE
