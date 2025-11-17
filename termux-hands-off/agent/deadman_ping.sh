#!/data/data/com.termux/files/usr/bin/bash
# usage: deadman_ping.sh <name>
set -e
NAME="$1"; [ -n "$NAME" ] || exit 0
touch "$HOME/hands-off/state/lastping.$NAME"
date +%s > "$HOME/hands-off/state/lastping.$NAME"
