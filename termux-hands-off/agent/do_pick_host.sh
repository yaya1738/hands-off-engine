#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
INV="$HOME/hands-off/state/hosts.txt"
OUT="$HOME/hands-off/state/mirror.env"

pick_ip=
pick_port=

try_ports=(22 443 2222)

while IFS= read -r line; do
  l="$(echo "$line" | sed 's/#.*$//' | xargs)"; [ -z "$l" ] && continue
  ip="$(echo "$l" | awk '{print $1}')"
  name="$(echo "$l" | awk '{print $2}')"; name="${name:-unknown}"
  for p in "${try_ports[@]}"; do
    if (echo > /dev/tcp/$ip/$p) >/dev/null 2>&1 ; then
      echo "[ok] $ip:$p reachable ($name)"
      pick_ip="$ip"; pick_port="$p"
      break 2
    else
      echo "[skip] $ip:$p not reachable ($name)"
    fi
  done
done < "$INV"

if [ -z "${pick_ip:-}" ]; then
  echo "[err] No reachable hosts/ports from $INV"
  exit 1
fi

cat > "$OUT" <<ENV
DO_IP=$pick_ip
DO_USER=root
DST=/root/hands-off/backup
STRICT_HOST_CHECKING=no
SSH_PORT=$pick_port
ENV

echo "[ok] mirror.env updated -> DO_IP=$pick_ip SSH_PORT=$pick_port"
