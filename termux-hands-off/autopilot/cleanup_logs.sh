#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/hands-off/autopilot"
ls edges-*.log 2>/dev/null | sort | head -n -7 | xargs -r rm -f
