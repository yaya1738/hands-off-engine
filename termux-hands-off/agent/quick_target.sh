#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

read -p "Enter droplet Public IPv4: " IP
[ -n "$IP" ] || { echo "[err] no IP"; exit 1; }

# Try ports in order
for P in 22 443 2222; do
  if (echo > /dev/tcp/$IP/$P) >/dev/null 2>&1; then
    echo "[ok] $IP:$P reachable"
    CHOSEN_PORT="$P"
    break
  else
    echo "[skip] $IP:$P not reachable"
  fi
done

[ -n "${CHOSEN_PORT:-}" ] || { echo "[err] no reachable SSH port on $IP"; exit 2; }

# Update hosts.txt so the picker has at least one good host
mkdir -p "$HOME/hands-off/state"
printf "%s\tmanual\n" "$IP" > "$HOME/hands-off/state/hosts.txt"

# Write mirror.env directly (the picker will also update it later)
cat > "$HOME/hands-off/state/mirror.env" <<ENV
DO_IP=$IP
DO_USER=root
DST=/root/hands-off/backup
STRICT_HOST_CHECKING=no
SSH_PORT=$CHOSEN_PORT
ENV
echo "[ok] mirror.env set to $IP:$CHOSEN_PORT"

# Run sync + health
bash "$HOME/hands-off/agent/mirror_sync.sh"   >> "$HOME/.cron-logs/mirror.log" 2>&1 || true
bash "$HOME/hands-off/agent/mirror_health.sh" >> "$HOME/.cron-logs/mirror.log" 2>&1 || true

# Show last lines
tail -n 120 "$HOME/.cron-logs/mirror.log" || true
