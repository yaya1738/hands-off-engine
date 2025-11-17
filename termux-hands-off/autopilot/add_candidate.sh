#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
# usage: add_candidate KEY P_FAIR P_MKT [NOTE...]
KEY="$1"; P_FAIR="$2"; P_MKT="$3"; shift 3 || true
NOTE="${*:-manual}"
printf '{"key":"%s","p_fair":%s,"p_mkt":%s,"note":"%s"}\n' "$KEY" "$P_FAIR" "$P_MKT" "$NOTE" >> "$HOME/hands-off/autopilot/candidates.jsonl"
echo "[OK] added: $KEY fair=$P_FAIR mkt=$P_MKT"
