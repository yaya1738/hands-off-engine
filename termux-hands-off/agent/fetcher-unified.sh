#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/hands-off/agent"
STATE="$HOME/hands-off/state"

# 1. Run main fetcher
python3 "$BASE/fetcher.py"

# 2. Compact instantly (no waiting for cron)
python3 "$BASE/pm_trim.py"

# 3. Trigger mirror
touch "$STATE/mirror.trigger"
