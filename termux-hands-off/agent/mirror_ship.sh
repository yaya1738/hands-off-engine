#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/hands-off"
STATE="$BASE/state"
OUT="$BASE/out"
CONF="$STATE/mirror.env"
LOGDIR="$HOME/.cron-logs"
LOCAL_MIRROR="$HOME/hands-off-out"

mkdir -p "$STATE" "$OUT" "$LOGDIR" "$LOCAL_MIRROR"

# Defaults (can be overridden by mirror.env)
DO_USER=""
DO_IP=""
DST="/root/hands-off-out"

# Load config if present
[ -f "$CONF" ] && . "$CONF"

if [ -z "$DO_USER" ] || [ -z "$DO_IP" ]; then
  echo "[mirror] disabled: DO_USER/DO_IP not set in $CONF" >&2
  exit 0
fi

REMOTE="${DO_USER}@${DO_IP}"
STAGING="${DST}.staging"
STAMP_LOCAL="$STATE/mirror.last"
TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "[mirror] start $TS -> $REMOTE:$DST"

# Ensure staging dirs on remote (Safe: only touching your hands-off area)
ssh "$REMOTE" "mkdir -p '$STAGING/out' '$STAGING/state'"

# 1) Sync local OUT to remote staging
rsync -az --delete --exclude 'state/' "$OUT/"   "$REMOTE:$STAGING/out/"

# 2) Sync local STATE to remote staging
rsync -az --delete --exclude 'state/' --exclude "health*" --exclude "infra*" "$STATE/" "$REMOTE:$STAGING/state/"

# 3) Atomically move staging -> final + stamp .last_ok on remote
ssh "$REMOTE" "set -e;
  DST='$DST';
  STAGING='$STAGING';
  STAMP_REMOTE=\"\$DST/.last_ok\";
  mkdir -p \"\$DST\";
  rsync -az --delete --exclude 'state/' \"\$STAGING/\" \"\$DST/\";
  date -u +\"%Y-%m-%dT%H:%M:%SZ\" > \"\$STAMP_REMOTE\";
"

# 4) Pull canonical remote mirror back to local
echo "[mirror] syncing \$REMOTE:\$DST -> \$LOCAL_MIRROR"
if ! rsync -az --delete "$REMOTE:$DST/" "$LOCAL_MIRROR/"; then
  echo "[warn] rsync remote->local failed; local mirror may be stale" >&2
fi

echo "$TS" > "$STAMP_LOCAL"
echo "[mirror] done $TS"

# Touch remote .last_ok so infra can see a fresh mirror timestamp
if [ -n "${DO_IP:-}" ]; then
  echo "[mirror] touching remote .last_ok on $DO_USER@$DO_IP"
  ssh "$DO_USER@$DO_IP" "mkdir -p /root/hands-off-out && touch /root/hands-off-out/.last_ok" || echo "[warn] failed to touch remote .last_ok"
fi

# --- ensure .last_ok in the canonical STATE dir after every mirror ---
if [ -n "${REMOTE:-}" ]; then
  echo "[mirror] forcing fresh .last_ok in /root/hands-off-out/state on $REMOTE"
  ssh "$REMOTE" 'date -u +%FT%TZ > /root/hands-off-out/state/.last_ok' || \
    echo "[warn] failed to touch /root/hands-off-out/state/.last_ok"
fi
