#!/data/data/com.termux/files/usr/bin/bash
# Usage: set_kv KEY VALUE   (writes to ~/hands-off/state/auto_sources.env)
set -e
CONF="$HOME/hands-off/state/auto_sources.env"
mkdir -p "$(dirname "$CONF")"
touch "$CONF"
sed -i 's/\r$//' "$CONF"
key="$1"; val="$2"
[ -z "$key" ] && { echo "Usage: set_kv KEY VALUE"; exit 1; }
# rewrite line or append
awk -v k="$key" -v v="$val" '
BEGIN{set=0}
$0 ~ ("^"k"=") { print k"="v; set=1; next }
{ print }
END{ if(!set) print k"="v }
' "$CONF" > "$CONF.tmp" && mv "$CONF.tmp" "$CONF"
echo "[ok] $key set"
