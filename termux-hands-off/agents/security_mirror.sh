#!/data/data/com.termux/files/usr/bin/sh
set -e
BASE="$HOME/hands-off"
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
  "$BASE/agents/external_accounts.json" \
  "$BASE/agents/cards.json" \
  "$BASE/agents/emergency_info.json" \
  "$BASE/logs/finance_balances.log" \
  "$BASE/logs/finance_credit.log" \
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
