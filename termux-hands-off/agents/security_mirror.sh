#!/data/data/com.termux/files/usr/bin/sh
set -e
BASE="$HOME/hands-off"
PRIVATE_ROOT="${HANDS_OFF_PRIVATE_DIR:-$HOME/.config/hands-off-engine}"
PRIVATE_RUNTIME="$PRIVATE_ROOT/legacy_runtime"
OUT="$BASE/security_snapshot.tar"
ENC="$BASE/security_snapshot.enc"
PASSF="$HOME/.config/hands-off/enc_passphrase.txt"
mkdir -p "$(dirname "$PASSF")"

# prompt once if missing
if [ ! -f "$PASSF" ]; then
  echo "Enter a strong passphrase for safety mirror:"
  read -r PASS
  echo "$PASS" > "$PASSF"
  chmod 600 "$PASSF"
fi

# collect files (extend as needed)
tar -cf "$OUT" \
  "$HOME/.config/hands-off/vault.json" \
  "$PRIVATE_RUNTIME/agents/external_accounts.json" \
  "$PRIVATE_RUNTIME/agents/cards.json" \
  "$PRIVATE_RUNTIME/agents/emergency_info.json" \
  "$PRIVATE_RUNTIME/agents/finance_rules.json" \
  "$PRIVATE_RUNTIME/logs/finance_balances.log" \
  "$PRIVATE_RUNTIME/logs/finance_credit.log" \
  "$PRIVATE_RUNTIME/logs/polymarket_positions.jsonl" \
  "$PRIVATE_RUNTIME/logs/polymarket_positions.csv" \
  "$PRIVATE_ROOT/finance/dollar_access.json" \
  "$PRIVATE_ROOT/security/yair_identity_profile.json" \
  2>/dev/null || true

# encrypt (AES-256)
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 150000 \
  -in "$OUT" -out "$ENC" -pass file:"$PASSF"

rm -f "$OUT"
echo "[ok] safety mirror -> $ENC"
# optional cloud push via rclone (remote: secure) 
if command -v rclone >/dev/null 2>&1; then 
  rclone copy -q "$ENC" secure:/hands-off/ || true; 
fi
