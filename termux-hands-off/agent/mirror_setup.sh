#!/data/data/com.termux/files/usr/bin/bash
set -e
CONF="$HOME/hands-off/state/mirror.env"
[ -f "$CONF" ] || cat > "$CONF" <<'E'
DO_IP=
DO_USER=root
DST=/root/hands-off-out
MIRROR_SERVE=0
SERVE_PORT=8080
E

echo
echo "[Mirror] Enter the droplet details (leave blank to keep current)"
source "$CONF"
read -p "  Droplet IP [$DO_IP]: " _IP
read -p "  SSH user [$DO_USER]: " _USER
read -p "  Remote folder [$DST]: " _DST
read -p "  Publish over HTTP? 0/1 [$MIRROR_SERVE]: " _SERVE
read -p "  HTTP port [$SERVE_PORT]: " _PORT
DO_IP="${_IP:-$DO_IP}"
DO_USER="${_USER:-$DO_USER}"
DST="${_DST:-$DST}"
MIRROR_SERVE="${_SERVE:-$MIRROR_SERVE}"
SERVE_PORT="${_PORT:-$SERVE_PORT}"
cat > "$CONF" <<E
DO_IP=$DO_IP
DO_USER=$DO_USER
DST=$DST
MIRROR_SERVE=$MIRROR_SERVE
SERVE_PORT=$SERVE_PORT
E
echo "[ok] mirror settings saved -> $CONF"
