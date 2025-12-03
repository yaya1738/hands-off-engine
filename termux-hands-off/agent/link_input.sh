#!/data/data/com.termux/files/usr/bin/bash
set -e
read -p "Google Sheets link (starts with https://script.googleusercontent.com): " SHEETS_WEBHOOK
read -p "Password / token (same one you put in the Google Script): " SHEETS_TOKEN

~/hands-off/agent/set_kv.sh SHEETS_WEBHOOK "$SHEETS_WEBHOOK"
~/hands-off/agent/set_kv.sh SHEETS_TOKEN "$SHEETS_TOKEN"

echo
echo "[ok] Saved link and token."
echo "Testing push..."
finpush
