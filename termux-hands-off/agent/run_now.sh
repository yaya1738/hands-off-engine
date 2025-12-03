#!/data/data/com.termux/files/usr/bin/bash
set -e
PY=python
OUT="$HOME/hands-off/state/decision_output.json"
$PY "$HOME/hands-off/agent/decision_engine.py" | tee "$OUT" >/dev/null
echo "[ok] wrote $OUT"
