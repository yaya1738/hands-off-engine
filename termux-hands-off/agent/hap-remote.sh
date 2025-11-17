#!/usr/bin/env bash
set -euo pipefail

MSG="${1:-auto: remote autopush}"

echo "===== REMOTE AUTOPUSH $(date -Is) ====="
ssh do138 "cd /root/hands-off && /usr/local/bin/hogitpush \"$MSG\""
