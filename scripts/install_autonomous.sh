#!/bin/bash
#
# Install Autonomous Infrastructure System
#
# This script installs and configures the autonomous infrastructure
# management system to run as a systemd service.
#
# Usage:
#   sudo ./install_autonomous.sh
#
# Standard: Yair Siegel Master Level Operations - Full Self-Control

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/hands-off-engine"
LOG_DIR="/var/log/hands-off"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}     AUTONOMOUS INFRASTRUCTURE INSTALLER${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Creating directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
chmod 755 "$INSTALL_DIR"
chmod 755 "$LOG_DIR"
echo -e "${GREEN}✓ Directories created${NC}"

echo -e "${BLUE}Step 2: Copying files...${NC}"
cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/scripts/"*.sh 2>/dev/null || true
echo -e "${GREEN}✓ Files copied${NC}"

echo -e "${BLUE}Step 3: Installing systemd service...${NC}"
cp "$INSTALL_DIR/scripts/systemd/hands-off-autonomous.service" /etc/systemd/system/
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd service installed${NC}"

echo -e "${BLUE}Step 4: Creating environment file...${NC}"
if [ ! -f /etc/hands-off-engine.env ]; then
    cat > /etc/hands-off-engine.env << 'EOF'
# Hands-Off Engine Environment Configuration
# Edit this file and add your API keys

# DigitalOcean (primary cloud provider)
# DO_API_TOKEN=your-digitalocean-api-token

# AWS (backup cloud provider)
# AWS_ACCESS_KEY_ID=your-aws-access-key
# AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Telegram Notifications (optional)
# TELEGRAM_BOT_TOKEN=your-telegram-bot-token
# TELEGRAM_CHAT_ID=your-telegram-chat-id

# Infrastructure Budget (USD per month)
INFRA_BUDGET=500
EOF
    echo -e "${YELLOW}⚠ Created /etc/hands-off-engine.env${NC}"
    echo -e "${YELLOW}  Please edit this file and add your API keys!${NC}"
else
    echo -e "${GREEN}✓ Environment file already exists${NC}"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}     INSTALLATION COMPLETE${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Edit /etc/hands-off-engine.env and add your API keys"
echo -e "  2. Enable the service: ${BLUE}systemctl enable hands-off-autonomous${NC}"
echo -e "  3. Start the service:  ${BLUE}systemctl start hands-off-autonomous${NC}"
echo -e "  4. Check status:       ${BLUE}systemctl status hands-off-autonomous${NC}"
echo -e "  5. View logs:          ${BLUE}journalctl -u hands-off-autonomous -f${NC}"
echo ""
echo -e "${YELLOW}The system will manage ALL infrastructure autonomously.${NC}"
echo -e "${YELLOW}User intervention is NOT required for normal operations.${NC}"
echo ""
