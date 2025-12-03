#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
INBOX="$HOME/hands-off/inbox"; mkdir -p "$INBOX"
for f in "$INBOX"/*.log; do
  [ -e "$f" ] || continue
  # forward only new lines (track offsets)
  off="$f.off"; touch "$off"
  start="$(cat "$off" 2>/dev/null || echo 0)"
  total="$(wc -l < "$f" | tr -d ' ')"; [ "$total" -gt "$start" ] || continue
  awk -v s="$start" 'NR>s' "$f" | while IFS= read -r line; do
    IFS='|' read -r SRC SEV TITLE BODY <<<"${line}"; SRC="${SRC:-gen}"; SEV="${SEV:-info}"; TITLE="${TITLE:-Inbox}"
    [ -n "$BODY" ] || BODY="(no body)"
    "$HOME/hands-off/agent/alert_mux.sh" --src "$SRC" --sev "$SEV" --title "$TITLE" --body "$BODY" || true
  done
  echo "$total" > "$off"
done
