#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRIVATE_ROOT="${HANDS_OFF_PRIVATE_DIR:-$HOME/.config/hands-off-engine}"
DEST="$PRIVATE_ROOT/termux/auto_sources.env"

mkdir -p "$(dirname "$DEST")"
chmod 700 "$PRIVATE_ROOT" "$PRIVATE_ROOT/termux" 2>/dev/null || true

if [[ -f "$DEST" ]]; then
  chmod 600 "$DEST" 2>/dev/null || true
  echo "Private auto-sources config already exists; left unchanged."
  exit 0
fi

for SOURCE in \
  "$REPO_ROOT/termux-hands-off/state/auto_sources.env" \
  "$HOME/hands-off/state/auto_sources.env"; do
  if [[ -f "$SOURCE" ]]; then
    cp -p "$SOURCE" "$DEST"
    chmod 600 "$DEST"
    echo "Migrated local auto-sources config to the private directory."
    echo "Source retained until the operator verifies the private copy."
    exit 0
  fi
done

echo "No legacy auto-sources config found. Create it locally after reviewing the private setup guide."
exit 0
