#!/data/data/com.termux/files/usr/bin/bash
set -e
CFG="$HOME/hands-off/state/deadman.cfg"
now="$(date +%s)"
while IFS='|' read -r NAME MINS TITLE; do
  [[ "$NAME" =~ ^#|^$ ]] && continue
  SLA=$(( MINS*60 ))
  f="$HOME/hands-off/state/lastping.$NAME"
  if [ ! -f "$f" ]; then
    "$HOME/hands-off/agent/alert_mux.sh" --src deadman --sev warn --title "No first ping: $TITLE" --body "$NAME has not pinged yet."
    continue
  fi
  last="$(cat "$f" 2>/dev/null || echo 0)"
  age=$(( now - last ))
  if [ "$age" -gt "$SLA" ]; then
    "$HOME/hands-off/agent/alert_mux.sh" --src deadman --sev crit --title "Stalled: $TITLE" --body "$NAME silent for $((age/60)) min (> $((SLA/60)) min)"
  fi
done < "$CFG"
