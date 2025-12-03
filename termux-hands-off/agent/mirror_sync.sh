bash "$HOME/hands-off/agent/do_pick_host.sh" >/dev/null 2>&1 || true
bash "$HOME/hands-off/agent/do_pick_host.sh" >/dev/null 2>&1 || true
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

CONF="$HOME/hands-off/state/mirror.env"
[ -f "$CONF" ] || { echo "[err] $CONF missing"; exit 1; }
# shellcheck disable=SC1090
. "$CONF"

SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=10"
if [ "${STRICT_HOST_CHECKING:-no}" != "yes" ]; then
  SSH_OPTS="$SSH_OPTS -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
fi

# Telegram helper (optional)
TG_CONF="$HOME/hands-off/state/tg/bots/handsoff.env"
tg() {
  [ -f "$TG_CONF" ] || return 0
  # shellcheck disable=SC1090
  . "$TG_CONF"
  [ -n "${TOKEN:-}" ] && [ -n "${CHAT_ID:-}" ] || return 0
  curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
    -d chat_id="$CHAT_ID" -d text="$1" >/dev/null || true
}

# Ensure remote path exists
ssh -p "${SSH_PORT:-22}" $SSH_OPTS "${DO_USER}@${DO_IP}" "mkdir -p '$DST/state' '$DST/agent'"

# Write a heartbeat stamp locally
STAMP_LOCAL="$HOME/hands-off/state/.mirror_stamp"
date -u +%Y-%m-%dT%H:%M:%SZ > "$STAMP_LOCAL"

# Common rsync flags
R="-az --delete --partial --numeric-ids --inplace --compress-level=9"

# Excludes (keeps bandwidth low)
EXC=(
  "--exclude=.git/"
  "--exclude=__pycache__/"
  "--exclude=.venv/"
  "--exclude=venv/"
  "--exclude=.mypy_cache/"
  "--exclude=.pytest_cache/"
  "--exclude=.cron-logs/"
  "--exclude=*.log"
)

# Push state and agent
rsync $R "${EXC[@]}" "$HOME/hands-off/state/"  "${DO_USER}@${DO_IP}:$DST/state/"  -e "ssh -p ${SSH_PORT:-22} $SSH_OPTS"
rsync $R "${EXC[@]}" "$HOME/hands-off/agent/"  "${DO_USER}@${DO_IP}:$DST/agent/"  -e "ssh -p ${SSH_PORT:-22} $SSH_OPTS"

# Also push a compact manifest to verify integrity
MAN="$HOME/hands-off/state/.manifest.txt"
( cd "$HOME/hands-off" && \
  { [ -d state ] && find state -type f -maxdepth 5 -printf '%P\t%s\n' | sort || true; \
    [ -d agent ] && find agent -type f -maxdepth 5 -printf '%P\t%s\n' | sort || true; } \
) > "$MAN"

rsync $R "$MAN" "${DO_USER}@${DO_IP}:$DST/.manifest.txt" -e "ssh -p ${SSH_PORT:-22} $SSH_OPTS"

echo "[ok] mirror_sync complete → $DO_USER@$DO_IP:$DST"
tg "✅ Mirror sync OK → $DO_IP:$DST"
