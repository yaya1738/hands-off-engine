#!/data/data/com.termux/files/usr/bin/sh
set -eu
umask 077

PRIVATE_ROOT="${HANDS_OFF_PRIVATE_DIR:-$HOME/.config/hands-off-engine}"
PRIVATE_RUNTIME="$PRIVATE_ROOT/legacy_runtime"
PRIVATE_BACKUPS="$PRIVATE_ROOT/backups"
PRIVATE_SECRETS="$PRIVATE_ROOT/secrets"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$PRIVATE_BACKUPS/security_snapshot-$STAMP.tar"
ENC="$OUT.enc"
PASSF="$PRIVATE_SECRETS/mirror_passphrase.txt"

mkdir -p "$PRIVATE_BACKUPS" "$PRIVATE_SECRETS"
chmod 700 "$PRIVATE_ROOT" "$PRIVATE_BACKUPS" "$PRIVATE_SECRETS"

# Reuse a passphrase migrated from the former private config, or prompt once.
if [ ! -f "$PASSF" ]; then
  echo "Enter a strong passphrase for the private safety mirror:"
  read -r PASS
  [ -n "$PASS" ] || { echo "Empty passphrase rejected"; exit 1; }
  printf '%s' "$PASS" > "$PASSF"
  chmod 600 "$PASSF"
fi

# Archive only existing private local paths. Nothing is written into the public checkout.
set --
for candidate in \
  "$PRIVATE_SECRETS/vault.json" \
  "$PRIVATE_SECRETS/termux-agent-vault.json" \
  "$PRIVATE_SECRETS/termux-agent-vault.json.bak" \
  "$PRIVATE_SECRETS/.env.polymarket" \
  "$PRIVATE_SECRETS/keys.vault" \
  "$PRIVATE_RUNTIME/agents/external_accounts.json" \
  "$PRIVATE_RUNTIME/agents/cards.json" \
  "$PRIVATE_RUNTIME/agents/emergency_info.json" \
  "$PRIVATE_RUNTIME/agents/finance_rules.json" \
  "$PRIVATE_RUNTIME/state" \
  "$PRIVATE_RUNTIME/agent" \
  "$PRIVATE_RUNTIME/logs" \
  "$PRIVATE_RUNTIME/data/finances" \
  "$PRIVATE_ROOT/logs" \
  "$PRIVATE_ROOT/termux-hands-off/state" \
  "$PRIVATE_ROOT/termux-hands-off/logs" \
  "$PRIVATE_ROOT/termux-hands-off/data/finances" \
  "$PRIVATE_ROOT/backups/security_snapshot.tar" \
  "$PRIVATE_ROOT/backups/security_snapshot-legacy.tar" \
  "$PRIVATE_ROOT/finance/private_finance_hub.json" \
  "$PRIVATE_ROOT/finance/dollar_access.json" \
  "$PRIVATE_ROOT/security/yair_identity_profile.json"
do
  if [ -e "$candidate" ]; then set -- "$@" "$candidate"; fi
done
for candidate in "$PRIVATE_SECRETS"/keys.vault.bak.*; do
  if [ -f "$candidate" ]; then set -- "$@" "$candidate"; fi
done
[ "$#" -gt 0 ] || { echo "No private files found to archive"; exit 1; }
tar -cf "$OUT" "$@"
chmod 600 "$OUT"
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 150000 \
  -in "$OUT" -out "$ENC" -pass file:"$PASSF"
chmod 600 "$ENC"
rm -f "$OUT"

echo "[ok] private safety mirror created at $ENC"
if command -v rclone >/dev/null 2>&1; then
  rclone copy -q "$ENC" secure:/hands-off/ || true
fi
