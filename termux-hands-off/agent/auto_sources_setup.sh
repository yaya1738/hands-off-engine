#!/data/data/com.termux/files/usr/bin/bash
set -e
CONF="$HOME/hands-off/state/auto_sources.env"
. "$CONF" 2>/dev/null || true
echo
echo "[Auto Sources] Set details (Enter to keep current)"
read -p "  Polymarket USDC (Polygon) address [$POLYMARKET_USDC_ADDR]: " _A
read -p "  Polygonscan API key [$POLYGONSCAN_API_KEY]: "              _K
read -p "  Bitcoin address [$BTC_ADDRESS]: "                          _B
read -p "  Cash override USD (blank = keep/compute from prior) [$CASH_OVERRIDE_USD]: " _C
POLYMARKET_USDC_ADDR="${_A:-$POLYMARKET_USDC_ADDR}"
POLYGONSCAN_API_KEY="${_K:-$POLYGONSCAN_API_KEY}"
BTC_ADDRESS="${_B:-$BTC_ADDRESS}"
CASH_OVERRIDE_USD="${_C:-$CASH_OVERRIDE_USD}"
cat > "$CONF" <<E
POLYMARKET_USDC_ADDR=$POLYMARKET_USDC_ADDR
POLYGONSCAN_API_KEY=$POLYGONSCAN_API_KEY
BTC_ADDRESS=$BTC_ADDRESS
CASH_OVERRIDE_USD=$CASH_OVERRIDE_USD
E
echo "[ok] saved -> $CONF"
