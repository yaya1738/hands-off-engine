#!/usr/bin/env bash
set -euo pipefail
APP="$HOME/hands-off/autopilot/admin_server.py"
LOG="$HOME/var/log/admin_server.log"
python -m py_compile "$APP"
nohup python "$APP" >>"$LOG" 2>&1 &
echo "[admin] (re)started"
