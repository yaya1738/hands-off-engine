#!/usr/bin/env bash
set -euo pipefail

# Provider-neutral verification. Never prints secrets and never starts financial execution.

SSH_HOST="${1:-}"
REMOTE_ROOT="${2:-$HOME/hands-off-engine}"

if [[ -z "$SSH_HOST" ]]; then
  echo "Usage: $0 <ssh-host> [remote-repo-path]" >&2
  exit 2
fi

issues=0

if ssh -o BatchMode=yes -o ConnectTimeout=10 "$SSH_HOST" 'printf "SSH: OK\n"'; then
  :
else
  echo "SSH: FAILED"
  exit 1
fi

ssh "$SSH_HOST" "REMOTE_ROOT='$REMOTE_ROOT' bash -s" <<'REMOTE'
set -euo pipefail

fail=0

for tool in python3 git curl jq; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "tool $tool: OK"
  else
    echo "tool $tool: MISSING"
    fail=1
  fi
done

if [[ ! -d "$REMOTE_ROOT/.git" ]]; then
  echo "repository: MISSING ($REMOTE_ROOT)"
  fail=1
else
  echo "repository: OK"
  echo "commit: $(git -C "$REMOTE_ROOT" rev-parse --short HEAD)"
fi

if [[ -f "$REMOTE_ROOT/deploy/factory-runtime.service" ]]; then
  grep -q 'Restart=always' "$REMOTE_ROOT/deploy/factory-runtime.service" || fail=1
  grep -q 'HANDS_OFF_LIVE_TRADING_ENABLED=0' "$REMOTE_ROOT/deploy/factory-runtime.service" || fail=1
  echo "factory service definition: OK"
else
  echo "factory service definition: MISSING"
  fail=1
fi

if [[ -f "$REMOTE_ROOT/scripts/autonomous_daemon.py" ]]; then
  "$REMOTE_ROOT/.venv/bin/python" - <<'PY' 2>/dev/null || fail=1
from scripts.autonomous_daemon import LIVE_TRADING_ENABLED
assert LIVE_TRADING_ENABLED is False
print("live financial execution: HARD-DISABLED")
PY
else
  echo "autonomous daemon: MISSING"
  fail=1
fi

if command -v systemctl >/dev/null 2>&1 && systemctl --user is-enabled hands-off-engine-factory.service >/dev/null 2>&1; then
  echo "factory service enabled: OK"
else
  echo "factory service enabled: NOT VERIFIED"
fi

exit "$fail"
REMOTE

printf '\nProvider-neutral host verification complete.\n'
