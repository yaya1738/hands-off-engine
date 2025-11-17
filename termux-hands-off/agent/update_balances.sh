#!/data/data/com.termux/files/usr/bin/bash
set -e
JSON="$HOME/hands-off/state/finance.json"
[ -f "$JSON" ] || cat > "$JSON" <<'J'
{
  "balances": {"cash_usd":0,"crypto_usd":0,"polymarket_usd":0},
  "history":[]
}
J

echo
echo "[Balances] Enter USD amounts (blank = keep current)"
read -p "  Cash USD: " CASH
read -p "  Crypto USD: " CRYPTO
read -p "  Polymarket USD: " PM

python - <<'PY'
import json, os, pathlib
p = pathlib.Path.home()/ "hands-off"/"state"/"finance.json"
d = json.load(open(p))
def f(x,cur):
    try: 
        return float(x) if (x is not None and x.strip()!="") else cur
    except: 
        return cur
cash     = os.environ.get("CASH")
crypto   = os.environ.get("CRYPTO")
pm       = os.environ.get("PM")
d["balances"] = {
  "cash_usd":      f(cash,   d["balances"].get("cash_usd",0)),
  "crypto_usd":    f(crypto, d["balances"].get("crypto_usd",0)),
  "polymarket_usd":f(pm,     d["balances"].get("polymarket_usd",0))
}
json.dump(d, open(p,"w"), indent=2)
print("[ok] balances ->", d["balances"])
PY

echo
read -p "[PnL] Add a quick PnL row for today? (y/N): " ADDPNL
if [ "$ADDPNL" = "y" ] || [ "$ADDPNL" = "Y" ]; then
  read -p "  cash_pnl: " CASH_PNL
  read -p "  crypto_pnl: " CRYPTO_PNL
  read -p "  polymarket_pnl: " PM_PNL
  CASH_PNL="${CASH_PNL:-0}" CRYPTO_PNL="${CRYPTO_PNL:-0}" PM_PNL="${PM_PNL:-0}" python - <<'PY'
import json, os, time, pathlib
p = pathlib.Path.home()/ "hands-off"/"state"/"finance.json"
d = json.load(open(p))
d.setdefault("history",[]).append({
  "ts": int(time.time()),
  "cash_pnl": float(os.environ.get("CASH_PNL",0)),
  "crypto_pnl": float(os.environ.get("CRYPTO_PNL",0)),
  "polymarket_pnl": float(os.environ.get("PM_PNL",0))
})
json.dump(d, open(p,"w"), indent=2)
print("[ok] history appended")
PY
fi

PY=python
OUT="$HOME/hands-off/state/decision_output.json"
$PY "$HOME/hands-off/agent/decision_engine.py" | tee "$OUT" >/dev/null
echo
echo "[Recommend]"
jq . "$OUT" 2>/dev/null || cat "$OUT"
