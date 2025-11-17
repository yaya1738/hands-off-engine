#!/usr/bin/env bash
set -euo pipefail
REMOTE="do138"

ssh "$REMOTE" 'bash -s' <<'BASH'
set -euo pipefail

# Preferred: dedicated summary script
if command -v /usr/local/bin/ho-summary2.sh >/dev/null 2>&1; then
  /usr/local/bin/ho-summary2.sh
  exit 0
fi

# Fallback: try viewer endpoints
try_curl() {
  local url="$1"
  if curl -fsS "$url" >/tmp/ho_summary_out.$$ 2>/dev/null; then
    cat /tmp/ho_summary_out.$$
    rm -f /tmp/ho_summary_out.$$
    return 0
  fi
  return 1
}

if try_curl "http://127.0.0.1:8000/txt/summary"; then
  exit 0
fi

if try_curl "http://127.0.0.1:8001/txt/summary"; then
  exit 0
fi

STATE="/root/hands-off-out/state"
if [ -f "$STATE/summary.txt" ]; then
  sed -n '1,200p' "$STATE/summary.txt"
  exit 0
fi

echo '{"detail":"summary not available"}'
BASH
