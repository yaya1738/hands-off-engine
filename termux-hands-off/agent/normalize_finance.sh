#!/data/data/com.termux/files/usr/bin/bash
set -e
STATE="$HOME/hands-off-out/state"
IN="$STATE/finance.json"
TMP="$STATE/.finance.patched.$$"
[ -s "$IN" ] || exit 0
jq 'def num: (try tonumber catch 0);
   .accounts = ((.accounts // (.balances // {})) | with_entries(.value = {balance: (.value|num)}))
 | .net_usd = (.accounts | to_entries | map(.value.balance) | add // 0)' \
  "$IN" > "$TMP" && mv "$TMP" "$IN"
