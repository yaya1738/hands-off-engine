#!/bin/bash
#
# DEPLOY AUTONOMOUS SYSTEM
#
# Installs and starts the complete autonomous infrastructure system.
# This script:
# 1. Creates necessary directories
# 2. Installs systemd services
# 3. Starts all components
# 4. Verifies everything is running
#
# Standard: Yair Siegel Master Level Operations

set -e

echo "=============================================="
echo "DEPLOYING AUTONOMOUS INFRASTRUCTURE SYSTEM"
echo "=============================================="
echo ""

BASE_DIR="/root/hands-off-engine"
LOG_DIR="/var/log/hands-off"
STATE_DIR="${BASE_DIR}/state"

# Create directories
echo "[1/6] Creating directories..."
mkdir -p "${LOG_DIR}"
mkdir -p "${STATE_DIR}"
mkdir -p "${STATE_DIR}/sync"
chmod 755 "${LOG_DIR}"

# Make scripts executable
echo "[2/6] Setting permissions..."
chmod +x "${BASE_DIR}/autonomous/"*.py
chmod +x "${BASE_DIR}/scripts/"*.sh 2>/dev/null || true

# Install systemd services
echo "[3/6] Installing systemd services..."
cp "${BASE_DIR}/scripts/systemd/master-controller.service" /etc/systemd/system/
cp "${BASE_DIR}/scripts/systemd/scaling-engine.service" /etc/systemd/system/
cp "${BASE_DIR}/scripts/systemd/self-healer.service" /etc/systemd/system/
cp "${BASE_DIR}/scripts/systemd/infra-monitor.service" /etc/systemd/system/ 2>/dev/null || true

# Reload systemd
echo "[4/6] Reloading systemd..."
systemctl daemon-reload

# Enable services
echo "[5/6] Enabling services..."
systemctl enable master-controller.service
systemctl enable scaling-engine.service
systemctl enable self-healer.service
systemctl enable infra-monitor.service 2>/dev/null || true

# Start services
echo "[6/6] Starting services..."
systemctl start master-controller.service
sleep 3
systemctl start scaling-engine.service
sleep 2
systemctl start self-healer.service
sleep 2
systemctl start infra-monitor.service 2>/dev/null || true

echo ""
echo "=============================================="
echo "DEPLOYMENT COMPLETE"
echo "=============================================="
echo ""

# Show status
echo "Service Status:"
echo "---------------"
for service in master-controller scaling-engine self-healer infra-monitor; do
    status=$(systemctl is-active ${service}.service 2>/dev/null || echo "not-found")
    printf "  %-20s : %s\n" "${service}" "${status}"
done

echo ""
echo "Log files:"
echo "  ${LOG_DIR}/master_controller.log"
echo "  ${LOG_DIR}/scaling_engine.log"
echo "  ${LOG_DIR}/self_healer.log"
echo ""
echo "Commands:"
echo "  View status:  systemctl status master-controller"
echo "  View logs:    journalctl -u master-controller -f"
echo "  Scaling:      python3 ${BASE_DIR}/autonomous/scaling_engine.py status"
echo ""
