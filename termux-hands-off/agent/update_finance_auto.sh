#!/data/data/com.termux/files/usr/bin/bash
set -e

CONF="$HOME/hands-off/state/auto_sources.env"
JSON="$HOME/hands-off/state/finance.json"
mkdir -p "$(dirname "$JSON")"
[ -f "$JSON" ] || echo '{"balances":{"cash_usd":0,"crypto_usd":0,"polymarket_usd":0},"history": []}' > "$JSON"

. "$CONF" 2>/dev/null || true

read_json() { jq -r "$1" "$JSON"; }
# Forward ALL args to jq (filter + --arg ...):
set_json()  { jq "$@" "$JSON" > "$JSON.tmp" && mv "$JSON.tmp" "$JSON"; }

cur_cash=$(read_json '.balances.cash_usd'     2>/dev/null || echo 0)
cur_crypto=$(read_json '.balances.crypto_usd' 2>/dev/null || echo 0)
cur_pm=$(read_json '.balances.polymarket_usd' 2>/dev/null || echo 0)

# --- Polymarket USDC (Polygon via Polygonscan) ---
pm_usd="$cur_pm"
if [ -n "$POLYMARKET_USDC_ADDR" ] && [ -n "$POLYGONSCAN_API_KEY" ]; then
  USDC=0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
  url="https://api.polygonscan.com/api?module=account&action=tokenbalance&contractaddress=$USDC&address=$POLYMARKET_USDC_ADDR&tag=latest&apikey=$POLYGONSCAN_API_KEY"
  raw=$(curl -fsSL "$url" || true)
  bal=$(echo "$raw" | jq -r '.result' 2>/dev/null || echo "")
  if [[ "$bal" =~ ^[0-9]+$ ]]; then
    pm_usd=$(python - <<PY
b=int("$bal")
print(round(b/1_000_000,2))
PY
)
  fi
fi

# --- BTC -> USD (Blockstream + Coinbase) ---
btc_usd=0
if [ -n "$BTC_ADDRESS" ]; then
  addr_json=$(curl -fsSL "https://blockstream.info/api/address/$BTC_ADDRESS" || true)
  if [ -n "$addr_json" ]; then
    funded=$(echo "$addr_json" | jq -r '.chain_stats.funded_txo_sum' 2>/dev/null)
    spent=$(echo "$addr_json" | jq -r '.chain_stats.spent_txo_sum' 2>/dev/null)
    bal_sats=$(( funded - spent ))
    if [ "$bal_sats" -ge 0 ] 2>/dev/null; then
      btc=$(python - <<PY
sats=$bal_sats
print(sats/100_000_000)
PY
)
      spot_btc=$(curl -fsSL "https://api.coinbase.com/v2/prices/BTC-USD/spot" | jq -r '.data.amount' 2>/dev/null || echo "")
      if echo "$spot_btc" | grep -Eq '^[0-9]+(\.[0-9]+)?$'; then
        btc_usd=$(python - <<PY
btc=float("$btc"); spot=float("$spot_btc")
print(round(btc*spot,2))
PY
)
      fi
    fi
  fi
fi

# --- ETH (mainnet) -> USD (Etherscan + Coinbase) ---
eth_usd=0
if [ -n "$ETH_ADDRESS" ] && [ -n "$ETHERSCAN_API_KEY" ]; then
  raw_eth=$(curl -fsSL "https://api.etherscan.io/api?module=account&action=balance&address=$ETH_ADDRESS&tag=latest&apikey=$ETHERSCAN_API_KEY" || true)
  wei=$(echo "$raw_eth" | jq -r '.result' 2>/dev/null || echo "")
  if [[ "$wei" =~ ^[0-9]+$ ]]; then
    eth=$(python - <<PY
wei=int("$wei")
print(wei/1e18)
PY
)
    spot_eth=$(curl -fsSL "https://api.coinbase.com/v2/prices/ETH-USD/spot" | jq -r '.data.amount' 2>/dev/null || echo "")
    if echo "$spot_eth" | grep -Eq '^[0-9]+(\.[0-9]+)?$'; then
      eth_usd=$(python - <<PY
eth=float("$eth"); spot=float("$spot_eth")
print(round(eth*spot,2))
PY
)
    fi
  fi
fi

# --- Consolidate + overrides ---
: "${btc_usd:=0}"
: "${eth_usd:=0}"
total_crypto=$(python - <<PY
btc=float("$btc_usd")
eth=float("$eth_usd")
print(round(btc+eth,2))
PY
)

cash_usd="$cur_cash"
[ -n "$CASH_OVERRIDE_USD" ] && cash_usd="$CASH_OVERRIDE_USD"

# write balances (use --arg strings; cast with tonumber in jq)
set_json '.balances.cash_usd = ($cash|tonumber)
         | .balances.crypto_usd = ($crypto|tonumber)
         | .balances.polymarket_usd = ($pm|tonumber)' \
  --arg cash "$cash_usd" \
  --arg crypto "$total_crypto" \
  --arg pm "$pm_usd"

# append snapshot to history
ts=$(date +%s)
jq --argjson ts "$ts" \
   --arg cash "$cash_usd" \
   --arg crypto "$total_crypto" \
   --arg pm "$pm_usd" \
   '.history += [{"ts": $ts,
                  "cash_pnl": ($cash|tonumber),
                  "crypto_pnl": ($crypto|tonumber),
                  "pm_pnl": ($pm|tonumber)}]' "$JSON" > "$JSON.tmp" && mv "$JSON.tmp" "$JSON"

echo "[ok] finance.json updated @ $(date -u +"%Y-%m-%dT%H:%MZ")"
jq '.balances' "$JSON" 2>/dev/null || true
