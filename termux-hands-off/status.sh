#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
echo "== PIDs =="
for f in "$HOME/hands-off/autopilot/loop.pid" "$HOME/hands-off/control.pid"; do
  [ -f "$f" ] && printf "%s : %s\n" "$(basename "$f")" "$(cat "$f")" || printf "%s : (none)\n" "$(basename "$f")"
done
echo
echo "== Latest run =="
tail -n 40 "$HOME/hands-off/autopilot/edges-$(date -u +%Y%m%d).log" 2>/dev/null || echo "no log yet"
echo
echo "== Control server =="
tail -n 20 "$HOME/hands-off/control.log" 2>/dev/null || echo "no control log yet"
