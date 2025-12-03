#!/data/data/com.termux/files/usr/bin/bash
set -e
read -p "Sheets webhook URL: " SHEETS_WEBHOOK
read -p "Token (same as in Apps Script): " SHEETS_TOKEN
read -p "Tab name [default equity]: " SHEETS_TAB
[ -z "$SHEETS_TAB" ] && SHEETS_TAB="equity"

~/hands-off/agent/set_kv.sh SHEETS_WEBHOOK "$SHEETS_WEBHOOK"
~/hands-off/agent/set_kv.sh SHEETS_TOKEN "$SHEETS_TOKEN"
~/hands-off/agent/set_kv.sh SHEETS_TAB "$SHEETS_TAB"

echo
echo "[ok] Saved webhook + token. Testing push..."
finpush
