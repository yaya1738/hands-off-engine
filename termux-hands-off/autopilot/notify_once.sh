#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
export EDGE_THRESHOLD="${EDGE_THRESHOLD:-${1:-0.05}}"
cd "$HOME/hands-off/autopilot"
source "$HOME/hands-off/.venv/bin/activate"
OUT=$(python polymarket_sniffer.py)
TS=$(date -u +"%Y%m%d")
echo "$OUT" >> "edges-$TS.log"
if echo "$OUT" | grep -q "^01\."; then
  termux-notification --id 42069 --title "Polymarket edges" --content "$(echo "$OUT" | sed -n '1,20p')" --priority high || true
fi
echo "$OUT"

# BEGIN EDGE ENGINE

BASE="$HOME/hands-off/autopilot"
LOGFILE="$BASE/edges-$(date -u +%Y%m%d).log"
python "$BASE/edge_engine.py" | tee -a "$LOGFILE"
if grep -q "\[BUY" "$LOGFILE"; then
  "$BASE/notify_edges.sh" "$LOGFILE" || true
  "$BASE/notify_telegram.sh" "$LOGFILE" || true
fi
# END EDGE ENGINE

# BEGIN FETCH POLYMARKET
BASE="$HOME/hands-off/autopilot"
python "$BASE/fetch_polymarket.py" || true
# END FETCH POLYMARKET
python "$BASE/dedupe_candidates.py" || true
