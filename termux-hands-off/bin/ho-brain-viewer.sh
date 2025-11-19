#!/usr/bin/env bash
# ho-brain-viewer.sh
# Runtime wrapper for Hands-Off Brain Viewer (Phase 1)
# Batch 26 Wiring v4

set -euo pipefail

RUNTIME_ROOT="/root/hands-off-out"
LOG_DIR="${RUNTIME_ROOT}/state/logs"
VIEWER_LOG="${LOG_DIR}/brain-viewer.log"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Source shared service environment
if [ -f "${RUNTIME_ROOT}/config/brain-services.env" ]; then
  # shellcheck source=/dev/null
  . "${RUNTIME_ROOT}/config/brain-services.env"
else
  echo "[ho-brain-viewer] ERROR: brain-services.env not found" | tee -a "${VIEWER_LOG}"
  exit 1
fi

# Source viewer-specific environment
if [ -f "${RUNTIME_ROOT}/config/brain-viewer.env" ]; then
  # shellcheck source=/dev/null
  . "${RUNTIME_ROOT}/config/brain-viewer.env"
else
  echo "[ho-brain-viewer] ERROR: brain-viewer.env not found" | tee -a "${VIEWER_LOG}"
  exit 1
fi

# Log startup
echo "[ho-brain-viewer] Starting brain viewer at $(date)" | tee -a "${VIEWER_LOG}"
echo "[ho-brain-viewer] Port: ${BRAIN_VIEWER_PORT:-<not set>}" | tee -a "${VIEWER_LOG}"
echo "[ho-brain-viewer] State dir: ${BRAIN_STATE_DIR:-${RUNTIME_ROOT}/state}" | tee -a "${VIEWER_LOG}"

# Activate virtual environment if configured
if [ -n "${VENV_PATH:-}" ] && [ -d "${VENV_PATH}" ]; then
  echo "[ho-brain-viewer] Activating venv: ${VENV_PATH}" | tee -a "${VIEWER_LOG}"
  # shellcheck source=/dev/null
  . "${VENV_PATH}/bin/activate"
fi

# Set Python path if configured
if [ -n "${PYTHONPATH:-}" ]; then
  export PYTHONPATH
  echo "[ho-brain-viewer] PYTHONPATH: ${PYTHONPATH}" | tee -a "${VIEWER_LOG}"
fi

# Launch the Python viewer app
cd "${RUNTIME_ROOT}"
echo "[ho-brain-viewer] Launching Python app from ${RUNTIME_ROOT}/app/brain/viewer/app.py" | tee -a "${VIEWER_LOG}"

exec python3 -m app.brain.viewer.app 2>&1 | tee -a "${VIEWER_LOG}"
