#!/data/data/com.termux/files/usr/bin/bash
set -e
PY=python
OUT="$HOME/hands-off/state/decision_output.json"
LOG="$HOME/.cron-logs/decision.log"
$PY "$HOME/hands-off/agent/decision_engine.py" | tee "$OUT" >> "$LOG" 2>&1
# optional mirror
if [ -f "$HOME/hands-off/state/mirror.env" ]; then
  source "$HOME/hands-off/state/mirror.env"
  if [ -n "$DO_IP" ]; then
    ssh -o StrictHostKeyChecking=no ${DO_USER:-root}@${DO_IP} "mkdir -p ${DST:-/root/hands-off-out}" || true
    scp -o StrictHostKeyChecking=no "$OUT" ${DO_USER:-root}@${DO_IP}:${DST:-/root/hands-off-out}/decision.json >/dev/null 2>&1 || true
  fi
fi
