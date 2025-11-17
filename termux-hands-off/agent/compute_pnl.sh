#!/data/data/com.termux/files/usr/bin/bash
set -e
bash "$HOME/hands-off/agent/hourly_job.sh" >/dev/null 2>&1 || true
"$HOME/hands-off/agent/pnl_delta.py" >/dev/null 2>&1 || true
# log compact PnL line to both logs
"$HOME/hands-off/agent/pnl_logger.sh" >> "$HOME/.cron-logs/pnl.log" 2>&1 || true
"$HOME/hands-off/agent/pnl_logger.sh" >> "$HOME/.cron-logs/decision.log" 2>&1 || true
