#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
REG="$HOME/hands-off/state/tg/bots"
CUR="$HOME/hands-off/state/tg/current_alias"

[ -f "$CUR" ] || { echo "[err] no current bot set. Run: tg_manager.sh list | tg_manager.sh use <alias>"; exit 1; }
alias="$(cat "$CUR")"
envf="$REG/$alias.env"
# shellcheck disable=SC1090
. "$envf"
[ -n "${TOKEN:-}" ] || { echo "[err] TOKEN missing for '$alias'"; exit 1; }
[ -n "${CHAT_ID:-}" ] || { echo "[err] CHAT_ID missing for '$alias' (run: tg_manager.sh id $alias)"; exit 1; }

API="https://api.telegram.org/bot${TOKEN}"
TEXT="${1:-Heartbeat} @ $(date -Iseconds)"
curl -s -X POST "${API}/sendMessage" -d chat_id="$CHAT_ID" -d text="$TEXT" >/dev/null && echo "[ok] Telegram message sent"
