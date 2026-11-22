#!/data/data/com.termux/files/usr/bin/sh
set -eu
umask 077

REPO_ROOT="$HOME/hands-off-engine"
PRIVATE_ROOT="${HANDS_OFF_PRIVATE_DIR:-$HOME/.config/hands-off-engine}"
RAW_BASE="https://raw.githubusercontent.com/yaya1738/hands-off-engine/76c9c5f79aca24947e88a25e203b3dc447e097ef"
EXPECTED_MIGRATION_BLOB="45afab951b38332af6bdec7de430afbea9ca1bfd"

[ -d "$REPO_ROOT/.git" ] || { echo "STOP: expected checkout not found at $REPO_ROOT"; exit 2; }
command -v curl >/dev/null 2>&1 || { echo "STOP: curl is required"; exit 127; }
command -v git >/dev/null 2>&1 || { echo "STOP: git is required for script integrity verification"; exit 127; }
PYTHON_BIN="$(command -v python3 || command -v python || true)"
[ -n "$PYTHON_BIN" ] || { echo "STOP: Python is required"; exit 127; }

TMP_BASE="${TMPDIR:-$HOME/.cache}"
mkdir -p "$TMP_BASE"
chmod 700 "$TMP_BASE"
WORK="$(mktemp -d "$TMP_BASE/hands-off-private-migration.XXXXXX")"
chmod 700 "$WORK"
trap 'rm -rf "$WORK"' EXIT HUP INT TERM

curl -fsSL "$RAW_BASE/scripts/migrate_private_state.py" -o "$WORK/migrate_private_state.py"
chmod 600 "$WORK/migrate_private_state.py"
ACTUAL_MIGRATION_BLOB="$(git hash-object "$WORK/migrate_private_state.py")"
[ "$ACTUAL_MIGRATION_BLOB" = "$EXPECTED_MIGRATION_BLOB" ] || {
  echo "STOP: downloaded migration script failed Git blob verification"
  exit 2
}

"$PYTHON_BIN" "$WORK/migrate_private_state.py" \
  --source-root "$REPO_ROOT" \
  --legacy-runtime-root "$HOME/hands-off" \
  --secrets-root "$HOME/.config" \
  --cron-logs-root "$HOME/.cron-logs" \
  --backup-root "$HOME/hands-off-engine-backup" \
  --backup-root "$HOME/hands-off-engine-mirror" \
  --destination "$PRIVATE_ROOT"
