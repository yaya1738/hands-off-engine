#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="$HOME/hands-off/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/termux_wire_github.log"

log() {
  printf "%s [TERMUX-WIRE-GH] %s\n" "$(date -Iseconds)" "$*" >>"$LOG_FILE"
}

REPO="$HOME/hands-off-engine"

# --- Single-instance lock for this script ---
LOCK_BASE="$HOME/.locks"
LOCKDIR="$LOCK_BASE/termux_wire_github"
mkdir -p "$LOCK_BASE"

if ! mkdir "$LOCKDIR" 2>/dev/null; then
  log "Another termux_wire_github run is still in progress (lockdir exists); exiting."
  exit 0
fi

cleanup() {
  rmdir "$LOCKDIR" 2>/dev/null || true
}
trap cleanup EXIT

# --- Sanity checks ---
if [ ! -d "$REPO/.git" ]; then
  log "Repo $REPO not found or not a git repo; exiting."
  exit 0
fi

cd "$REPO"

# --- Handle .git/index.lock safely ---
if [ -e ".git/index.lock" ]; then
  if ps aux | grep "[g]it" | grep "$REPO" >/dev/null 2>&1; then
    log ".git/index.lock present and a git process is active; skipping this tick."
    exit 0
  else
    log ".git/index.lock present but no git process for this repo; removing stale lock."
    rm -f ".git/index.lock"
  fi
fi

log "Running git fetch origin..."
if ! git fetch origin >>"$LOG_FILE" 2>&1; then
  log "git fetch origin failed"
  exit 1
fi

log "Checking out main..."
if ! git checkout main >>"$LOG_FILE" 2>&1; then
  log "git checkout main failed"
  exit 1
fi

log "Pulling origin/main..."
if ! git pull origin main >>"$LOG_FILE" 2>&1; then
  log "git pull origin main failed"
  exit 1
fi

log "Wire completed OK."
