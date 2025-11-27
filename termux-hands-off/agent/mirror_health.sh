bash "$HOME/hands-off/agent/do_pick_host.sh" >/dev/null 2>&1 || true
bash "$HOME/hands-off/agent/do_pick_host.sh" >/dev/null 2>&1 || true
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

CONF="$HOME/hands-off/state/mirror.env"
# shellcheck disable=SC1090
. "$CONF"

SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=15 -o ServerAliveCountMax=3"
if [ "${STRICT_HOST_CHECKING:-no}" != "yes" ]; then
  SSH_OPTS="$SSH_OPTS -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
fi

TG_CONF="$HOME/hands-off/state/tg/bots/handsoff.env"
tg() {
  [ -f "$TG_CONF" ] || return 0
  # shellcheck disable=SC1090
  . "$TG_CONF"
  [ -n "${TOKEN:-}" ] && [ -n "${CHAT_ID:-}" ] || return 0
  curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
    -d chat_id="$CHAT_ID" -d text="$1" >/dev/null || true
}

# Pull remote manifest and compare counts/sizes quickly
TMP_REMOTE="$(mktemp)"
if ! ssh $SSH_OPTS "${DO_USER}@${DO_IP}" "test -f '$DST/.manifest.txt' && cat '$DST/.manifest.txt'" > "$TMP_REMOTE" 2>/dev/null; then
  echo "[err] remote manifest missing/unreadable"
  tg "⚠️ Mirror health: remote manifest missing/unreadable on $DO_IP"
  exit 0
fi

# Build local quick manifest snapshot (same format)
TMP_LOCAL="$(mktemp)"
( cd "$HOME/hands-off" && \
  { [ -d state ] && find state -type f -maxdepth 5 -printf '%P\t%s\n' | sort || true; \
    [ -d agent ] && find agent -type f -maxdepth 5 -printf '%P\t%s\n' | sort || true; } \
) > "$TMP_LOCAL"

# Simple diff (ignores ordering differences)
if ! diff -q "$TMP_LOCAL" "$TMP_REMOTE" >/dev/null 2>&1; then
  echo "[warn] manifest drift detected"
  tg "⚠️ Mirror drift detected vs $DO_IP:$DST"
else
  echo "[ok] mirror manifests aligned"
fi

# Age check: remote stamp freshness (should exist in state/.mirror_stamp)
REMOTE_AGE_MIN=$(ssh $SSH_OPTS "${DO_USER}@${DO_IP}" "TS=\$(cat '$DST/state/.mirror_stamp' 2>/dev/null || echo '1970-01-01T00:00:00Z'); python - <<'PY'
import sys,datetime
ts=sys.stdin.read().strip()
try:
  t=datetime.datetime.strptime(ts,'%Y-%m-%dT%H:%M:%SZ')
except:
  print(10**9); sys.exit(0)
age=(datetime.datetime.utcnow()-t).total_seconds()/60
print(int(age))
PY
")
if [ "${REMOTE_AGE_MIN:-999999}" -gt 120 ]; then
  echo "[warn] remote stamp is stale (${REMOTE_AGE_MIN} min)"
  tg "⚠️ Mirror stale: last sync ${REMOTE_AGE_MIN} min ago on $DO_IP"
else
  echo "[ok] remote stamp age ${REMOTE_AGE_MIN} min"
fi

rm -f "$TMP_LOCAL" "$TMP_REMOTE"
