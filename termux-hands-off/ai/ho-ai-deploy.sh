#!/usr/bin/env bash
set -euo pipefail

echo "===== AI-RUNNER DEPLOY HOOK ====="
echo "Timestamp: $(date -Is)"

# Base paths
AI_SRC="/root/hands-off-out/ai"
AI_DEST="/root/hands-off-out/ai"
SYSTEMD_UNIT="/etc/systemd/system/ai-runner.service"

# Ensure AI directories exist on droplet
echo "[1/6] Creating AI directories..."
mkdir -p "$AI_DEST/tasks" "$AI_DEST/results" "$AI_DEST/processed"

# Verify ai_runner.py exists (already mirrored by rsync)
if [ ! -f "$AI_SRC/ai_runner.py" ]; then
  echo "[ERROR] ai_runner.py not found at $AI_SRC/ai_runner.py"
  exit 1
fi
echo "[2/6] ai_runner.py verified at $AI_SRC/ai_runner.py"

# Make ai_runner.py executable
chmod +x "$AI_SRC/ai_runner.py"
echo "[3/6] ai_runner.py marked executable"

# Copy example task if it doesn't exist in tasks/ yet
if [ -f "$AI_SRC/example_task.json" ] && [ ! -f "$AI_DEST/tasks/example_task.json" ]; then
  cp "$AI_SRC/example_task.json" "$AI_DEST/tasks/example_task.json"
  echo "[4/6] example_task.json copied to tasks/"
else
  echo "[4/6] example_task.json already exists or not needed"
fi

# Install systemd unit
if [ -f "$AI_SRC/ai-runner.service" ]; then
  cp "$AI_SRC/ai-runner.service" "$SYSTEMD_UNIT"
  echo "[5/6] ai-runner.service installed to $SYSTEMD_UNIT"
else
  echo "[ERROR] ai-runner.service not found at $AI_SRC/ai-runner.service"
  exit 1
fi

# Reload systemd and restart service
echo "[6/6] Reloading systemd and restarting ai-runner..."
systemctl daemon-reload
systemctl enable ai-runner || true
systemctl restart ai-runner || echo "[WARN] ai-runner restart failed (may be first run)"

# Check status
sleep 1
if systemctl is-active --quiet ai-runner; then
  echo "[SUCCESS] ai-runner.service is active"
else
  echo "[WARN] ai-runner.service is not active - check systemctl status ai-runner"
fi

echo "===== AI-RUNNER DEPLOY COMPLETE ====="
