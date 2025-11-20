#!/usr/bin/env bash
# Emergency one-time fix for divergent Termux repo
# Run this ONCE in Termux to force-sync with GitHub, then delete it

set -euo pipefail

REPO="$HOME/hands-off-engine"
LOG_FILE="$HOME/hands-off/logs/emergency_fix.log"

mkdir -p "$(dirname "$LOG_FILE")"

log() {
  echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

log "========================================"
log "EMERGENCY SYNC FIX - Starting"
log "========================================"

if [ ! -d "$REPO/.git" ]; then
  log "ERROR: $REPO is not a git repo"
  exit 1
fi

cd "$REPO"

log "Fetching latest from origin..."
if ! git fetch origin 2>&1 | tee -a "$LOG_FILE"; then
  log "ERROR: git fetch failed"
  exit 1
fi

log "Checking out main branch..."
if ! git checkout main 2>&1 | tee -a "$LOG_FILE"; then
  log "ERROR: git checkout failed"
  exit 1
fi

log "Force-resetting to origin/main (discarding local changes)..."
if ! git reset --hard origin/main 2>&1 | tee -a "$LOG_FILE"; then
  log "ERROR: git reset failed"
  exit 1
fi

log "Cleaning untracked files..."
if ! git clean -fd 2>&1 | tee -a "$LOG_FILE"; then
  log "WARNING: git clean had issues, but continuing..."
fi

log "========================================"
log "EMERGENCY SYNC FIX - Complete!"
log "========================================"
log ""
log "Your repo is now perfectly synced with GitHub."
log "The regular wire will work cleanly from now on."
log ""
log "You can now delete this script:"
log "  rm $REPO/termux/emergency_sync_fix.sh"
log ""
