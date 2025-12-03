#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
REG="$HOME/hands-off/state/tg/bots"
CUR="$HOME/hands-off/state/tg/current_alias"
mkdir -p "$REG"

usage(){
  cat <<USAGE
tg_manager.sh COMMAND [args]

Commands:
  new [alias]
      Opens @BotFather to create a new bot, then stores the token under the alias.
  import [alias] [token]
      Registers an existing bot token under the alias (won't overwrite others).
  list
      Lists all saved bot aliases (and marks the current one).
  use [alias]
      Sets the current/active bot alias.
  id [alias]
      Detects and saves TELEGRAM_CHAT_ID for the alias (after you message your bot).
  test [alias] [message...]
      Sends a test message using the alias (default message = "Hands-Off test").

Tips:
- Use 'new' to add a brand-new bot via BotFather with minimal taps.
- Use 'import' if you already have a bot token from earlier.
- After 'new'/'import', run 'id' once (send any message to your bot -> press Enter) to save CHAT_ID.
- Run 'use' to switch which bot is active for scheduled alerts.

USAGE
}

api(){
  local alias="$1"; local path="$REG/$alias.env"
  [ -f "$path" ] || { echo "[err] alias '$alias' not found"; exit 1; }
  # shellcheck disable=SC1090
  . "$path"
  [ -n "${TOKEN:-}" ] || { echo "[err] TOKEN missing for '$alias'"; exit 1; }
  echo "https://api.telegram.org/bot${TOKEN}"
}

cmd_new(){
  local alias="${1:-}"
  [ -n "$alias" ] || { echo "[err] provide an alias: tg_manager.sh new mybot"; exit 1; }

  echo "[info] Opening @BotFather to create a new bot..."
  am start -a android.intent.action.VIEW -d "https://t.me/BotFather" >/dev/null 2>&1 || true
  echo
  echo "In Telegram @BotFather: send /newbot, follow prompts, copy the token"
  read -p "Paste the bot TOKEN here: " TOKEN
  [ -n "$TOKEN" ] || { echo "[err] empty token"; exit 1; }

  local f="$REG/$alias.env"
  { echo "TOKEN=$TOKEN"; echo "USERNAME="; echo "CHAT_ID="; } > "$f"
  echo "[ok] saved token under alias '$alias' -> $f"
  echo "$alias" > "$CUR"
  echo "[ok] set current alias to '$alias'"
}

cmd_import(){
  local alias="${1:-}"; local token="${2:-}"
  [ -n "$alias" ] && [ -n "$token" ] || { echo "[err] usage: tg_manager.sh import <alias> <token>"; exit 1; }
  local f="$REG/$alias.env"
  [ -f "$f" ] && echo "[warn] alias exists; updating token"
  { echo "TOKEN=$token"; echo "USERNAME="; echo "CHAT_ID="; } > "$f"
  echo "[ok] imported token into '$alias'"
  echo "$alias" > "$CUR"
  echo "[ok] set current alias to '$alias'"
}

cmd_list(){
  local cur=""; [ -f "$CUR" ] && cur="$(cat "$CUR" 2>/dev/null || true)"
  for f in "$REG"/*.env; do
    [ -e "$f" ] || { echo "(no bots saved yet)"; return 0; }
    alias="$(basename "$f" .env)"
    mark=" "
    [ "$alias" = "$cur" ] && mark="*"
    echo " $mark $alias"
  done
}

cmd_use(){
  local alias="${1:-}"
  [ -n "$alias" ] || { echo "[err] usage: tg_manager.sh use <alias>"; exit 1; }
  [ -f "$REG/$alias.env" ] || { echo "[err] alias '$alias' not found"; exit 1; }
  echo "$alias" > "$CUR"
  echo "[ok] current alias -> '$alias'"
}

cmd_id(){
  local alias="${1:-}"
  [ -n "$alias" ] || { echo "[err] usage: tg_manager.sh id <alias>"; exit 1; }
  local f="$REG/$alias.env"; [ -f "$f" ] || { echo "[err] alias '$alias' not found"; exit 1; }
  # shellcheck disable=SC1090
  . "$f"
  [ -n "${TOKEN:-}" ] || { echo "[err] TOKEN missing"; exit 1; }

  echo
  echo "[action] Open chat with YOUR bot in Telegram, send any message (e.g., 'hi')."
  read -p "Press Enter after you sent a message… " _

  local API="https://api.telegram.org/bot${TOKEN}"
  local UPD; UPD="$(curl -s "${API}/getUpdates")"
  local CID
  CID="$(echo "$UPD" | jq -r '
    (.result[]?.message?.chat?.id //
     .result[]?.edited_message?.chat?.id //
     .result[]?.channel_post?.chat?.id //
     .result[]?.my_chat_member?.chat?.id) | select(.!=null) | tostring' | tail -n1)"
  [ -n "${CID:-}" ] || { echo "[err] Could not detect chat id. Make sure you messaged the bot, then retry."; exit 1; }

  # persist CHAT_ID
  awk -v cid="$CID" '
    BEGIN{set=0}
    /^CHAT_ID=/ {print "CHAT_ID=" cid; set=1; next}
    {print}
    END{if(!set) print "CHAT_ID=" cid}
  ' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
  echo "[ok] CHAT_ID=$CID saved for alias '$alias'"
}

cmd_test(){
  local alias="${1:-}"; shift || true
  local msg="${*:-Hands-Off test}"
  [ -n "$alias" ] || { echo "[err] usage: tg_manager.sh test <alias> [message]"; exit 1; }
  local f="$REG/$alias.env"; [ -f "$f" ] || { echo "[err] alias '$alias' not found"; exit 1; }
  # shellcheck disable=SC1090
  . "$f"
  [ -n "${TOKEN:-}" ] || { echo "[err] TOKEN missing"; exit 1; }
  [ -n "${CHAT_ID:-}" ] || { echo "[err] CHAT_ID missing. Run: tg_manager.sh id $alias"; exit 1; }
  curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
    -d chat_id="$CHAT_ID" -d text="$msg" >/dev/null && echo "[ok] sent."
}

case "${1:-}" in
  new) shift; cmd_new "${1:-}";;
  import) shift; cmd_import "${1:-}" "${2:-}";;
  list) cmd_list;;
  use) shift; cmd_use "${1:-}";;
  id) shift; cmd_id "${1:-}";;
  test) shift; cmd_test "${1:-}" "${@:1}";;
  ""|-h|--help) usage;;
  *) echo "[err] unknown command"; usage; exit 1;;
esac
