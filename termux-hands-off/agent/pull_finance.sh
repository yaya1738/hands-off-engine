#!/data/data/com.termux/files/usr/bin/bash
set -e
STATE="$HOME/hands-off-out/state"
mkdir -p "$STATE"

ok=0

# 1) Preferred: scp via your host alias (same creds as `ssh do138`)
if scp -o StrictHostKeyChecking=no do138:/root/hands-off-out/state/finance.json "$STATE/finance.json" 2>/dev/null; then
  ok=1
fi
scp -o StrictHostKeyChecking=no do138:/root/hands-off-out/state/decision_report.json "$STATE/decision_report.json" 2>/dev/null || true

# 2) Fallbacks (HTTP) in case scp fails
if [ "$ok" -ne 1 ]; then
  curl -fsS http://138.68.103.156/file/state/finance.json -o "$STATE/finance.json" 2>/dev/null || true
  curl -fsS http://138.68.103.156/file/finance.json -o "$STATE/finance.json" 2>/dev/null || true
  curl -fsS http://138.68.103.156/file/state/decision_report.json -o "$STATE/decision_report.json" 2>/dev/null || true
  curl -fsS http://138.68.103.156/file/decision_report.json -o "$STATE/decision_report.json" 2>/dev/null || true
fi

if [ -s "$STATE/finance.json" ]; then
  echo "[ok] finance.json updated $(date -u '+%F %T UTC')"
else
  echo "[warn] finance.json still missing $(date -u '+%F %T UTC')"
fi

# normalize shape for alert script
"$HOME/hands-off/agent/normalize_finance.sh"
