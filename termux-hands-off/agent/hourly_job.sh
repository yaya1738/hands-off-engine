#!/data/data/com.termux/files/usr/bin/bash
set -e
bash "$HOME/hands-off/agent/update_finance_auto.sh" || true
bash "$HOME/hands-off/agent/run_now.sh"
# mirror if configured
if [ -f "$HOME/hands-off/state/mirror.env" ]; then
  . "$HOME/hands-off/state/mirror.env"
  OUT="$HOME/hands-off/state/decision_output.json"
  if [ -n "$DO_IP" ]; then
    ssh -o StrictHostKeyChecking=no ${DO_USER:-root}@${DO_IP} "mkdir -p ${DST:-/root/hands-off-out}" || true
    scp -o StrictHostKeyChecking=no "$OUT" ${DO_USER:-root}@${DO_IP}:${DST:-/root/hands-off-out}/decision.json >/dev/null 2>&1 || true
  fi
fi
