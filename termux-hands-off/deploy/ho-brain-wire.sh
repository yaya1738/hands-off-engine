#!/usr/bin/env bash
# ho-brain-wire.sh
# Batch 26 Wiring v4 — Brain services deployment script
# This script:
#   - Installs all ho-brain-* systemd units
#   - Enables + restarts ONLY ho-brain-viewer.service (Phase 1)
#   - Leaves Phase 2 units (orchestrator/decider/executor) installed but disabled
#   - Performs health checks and validates DRYRUN mode

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
RUNTIME_ROOT="/root/hands-off-out"
SYSTEMD_SRC="${RUNTIME_ROOT}/systemd"
SYSTEMD_DST="/etc/systemd/system"
LOG_DIR="${RUNTIME_ROOT}/state/logs"
MODE_FILE="${RUNTIME_ROOT}/state/flags/mode.json"
VIEWER_ENV="${RUNTIME_ROOT}/config/brain-viewer.env"
SERVICES_ENV="${RUNTIME_ROOT}/config/brain-services.env"
VIEWER_UNIT="ho-brain-viewer.service"

PHASE2_UNITS=(
  "ho-brain-orchestrator.service"
  "ho-brain-orchestrator.timer"
  "ho-brain-decider.service"
  "ho-brain-decider.timer"
  "ho-brain-executor.service"
  "ho-brain-executor.timer"
)

# ============================================================================
# Step 1: Ensure basic directories exist
# ============================================================================
echo "[ho-brain-wire] Ensuring required directories exist..."
mkdir -p "${LOG_DIR}"

# ============================================================================
# Step 2: Read DRYRUN/LIVE mode (logging only, no mutation)
# ============================================================================
if [ -f "${MODE_FILE}" ]; then
  echo "[ho-brain-wire] Mode file: ${MODE_FILE}" | tee -a "${LOG_DIR}/brain-viewer.log"
  # Print first line of mode file content
  head -n 1 "${MODE_FILE}" | tee -a "${LOG_DIR}/brain-viewer.log" || true
else
  echo "[ho-brain-wire] WARNING: mode file not found (${MODE_FILE}); assuming DRYRUN enforced elsewhere" | tee -a "${LOG_DIR}/brain-viewer.log"
fi

# ============================================================================
# Step 3: Sanity-check required config files
# ============================================================================
echo "[ho-brain-wire] Checking required config files..."
if [ ! -f "${VIEWER_ENV}" ] || [ ! -f "${SERVICES_ENV}" ]; then
  echo "[ho-brain-wire] ERROR: required env files missing (${VIEWER_ENV} or ${SERVICES_ENV})" | tee -a "${LOG_DIR}/brain-viewer.log"
  exit 1
fi
echo "[ho-brain-wire] Config files OK" | tee -a "${LOG_DIR}/brain-viewer.log"

# ============================================================================
# Step 4: Install units from runtime → /etc/systemd/system
# ============================================================================
echo "[ho-brain-wire] Installing systemd units..."

# Find all ho-brain-* units in source directory
for unit in "${SYSTEMD_SRC}"/ho-brain-*.service "${SYSTEMD_SRC}"/ho-brain-*.timer; do
  if [ ! -f "${unit}" ]; then
    continue
  fi

  dst="${SYSTEMD_DST}/$(basename "${unit}")"

  # Backup existing unit if present
  if [ -f "${dst}" ]; then
    ts="$(date +%Y%m%d%H%M%S)"
    echo "[ho-brain-wire] Backing up existing ${dst} to ${dst}.bak.${ts}" | tee -a "${LOG_DIR}/brain-viewer.log"
    mv "${dst}" "${dst}.bak.${ts}"
  fi

  # Copy new unit
  echo "[ho-brain-wire] Installing $(basename "${unit}")" | tee -a "${LOG_DIR}/brain-viewer.log"
  cp "${unit}" "${dst}"
done

# ============================================================================
# Step 5: Reload systemd
# ============================================================================
echo "[ho-brain-wire] Running systemctl daemon-reload..." | tee -a "${LOG_DIR}/brain-viewer.log"
systemctl daemon-reload

# ============================================================================
# Step 6: Enable Phase 1 only (brain viewer)
# ============================================================================
echo "[ho-brain-wire] Enabling ${VIEWER_UNIT}..." | tee -a "${LOG_DIR}/brain-viewer.log"
systemctl enable "${VIEWER_UNIT}"

# ============================================================================
# Step 7: Start/restart brain viewer
# ============================================================================
echo "[ho-brain-wire] Restarting ${VIEWER_UNIT}..." | tee -a "${LOG_DIR}/brain-viewer.log"
if ! systemctl restart "${VIEWER_UNIT}"; then
  echo "[ho-brain-wire] ERROR: Failed to restart ${VIEWER_UNIT}" | tee -a "${LOG_DIR}/brain-viewer.log"
  echo "[ho-brain-wire] Recent journal entries:" | tee -a "${LOG_DIR}/brain-viewer.log"
  journalctl -u "${VIEWER_UNIT}" -n 20 --no-pager | tee -a "${LOG_DIR}/brain-viewer.log"
  exit 1
fi

# Wait a moment for service to start
sleep 2

# ============================================================================
# Step 8: HTTP sanity check (safe under set -e)
# ============================================================================
echo "[ho-brain-wire] Running HTTP health check..." | tee -a "${LOG_DIR}/brain-viewer.log"

# Source viewer env to get port
if [ -f "${VIEWER_ENV}" ]; then
  # shellcheck source=/dev/null
  . "${VIEWER_ENV}"
fi

if [ -n "${BRAIN_VIEWER_PORT:-}" ]; then
  # Disable errexit for health check (soft-fail)
  set +e
  curl -fsS "http://127.0.0.1:${BRAIN_VIEWER_PORT}/health" >/dev/null 2>&1
  rc=$?
  if [ $rc -ne 0 ]; then
    curl -fsS "http://127.0.0.1:${BRAIN_VIEWER_PORT}/txt/brain" >/dev/null 2>&1
    rc=$?
  fi
  set -e

  if [ $rc -ne 0 ]; then
    echo "[ho-brain-wire] WARNING: brain viewer HTTP check failed" | tee -a "${LOG_DIR}/brain-viewer.log"
  else
    echo "[ho-brain-wire] brain viewer HTTP check OK" | tee -a "${LOG_DIR}/brain-viewer.log"
  fi
else
  echo "[ho-brain-wire] WARNING: BRAIN_VIEWER_PORT not set; skipping HTTP check" | tee -a "${LOG_DIR}/brain-viewer.log"
fi

# ============================================================================
# Step 9: Confirm Phase 2 units remain disabled (logging only)
# ============================================================================
echo "[ho-brain-wire] Verifying Phase 2 units are disabled..." | tee -a "${LOG_DIR}/brain-viewer.log"

for u in "${PHASE2_UNITS[@]}"; do
  if systemctl is-enabled "${u}" >/dev/null 2>&1; then
    echo "[ho-brain-wire] WARNING: ${u} is enabled (should be disabled)" | tee -a "${LOG_DIR}/brain-viewer.log"
  else
    echo "[ho-brain-wire] ${u} is not enabled (expected)" | tee -a "${LOG_DIR}/brain-viewer.log"
  fi
done

# ============================================================================
# Step 10: Success
# ============================================================================
echo "[ho-brain-wire] Brain wiring deployment completed successfully" | tee -a "${LOG_DIR}/brain-viewer.log"
echo "[ho-brain-wire] Phase 1 (viewer) is active, Phase 2 units are installed but disabled" | tee -a "${LOG_DIR}/brain-viewer.log"
exit 0
