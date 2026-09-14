#!/bin/bash
# Installation script for fault-tolerant infrastructure

set -e  # Exit on error

echo "=========================================="
echo "Hands-Off Engine - Fault-Tolerant Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}ERROR: Do not run this script as root${NC}"
    echo "Run as: ./install.sh"
    exit 1
fi

# Detect installation method
echo "Choose installation method:"
echo "  1. Systemd services (recommended for VPS)"
echo "  2. Docker Compose (recommended for cloud)"
echo "  3. Hybrid (add infrastructure to existing setup)"
echo ""
read -p "Enter choice [1-3]: " INSTALL_METHOD

# Install Python dependencies
echo ""
echo -e "${GREEN}Installing Python dependencies...${NC}"
pip3 install --user structlog psutil requests || {
    echo -e "${RED}Failed to install Python dependencies${NC}"
    exit 1
}

# Make scripts executable
echo -e "${GREEN}Making scripts executable...${NC}"
chmod +x infrastructure/*.py
chmod +x scripts/*.sh

# Create directories
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p /var/log/hands-off-engine || sudo mkdir -p /var/log/hands-off-engine
mkdir -p backups
mkdir -p state

case $INSTALL_METHOD in
    1)
        echo ""
        echo -e "${GREEN}Installing systemd services...${NC}"

        # Copy service files
        sudo cp infrastructure/systemd/*.service /etc/systemd/system/
        sudo cp infrastructure/systemd/*.timer /etc/systemd/system/

        # Reload systemd
        sudo systemctl daemon-reload

        # Enable services
        echo -e "${GREEN}Enabling services...${NC}"
        sudo systemctl enable hands-off-selfheal
        sudo systemctl enable hands-off-health-monitor
        sudo systemctl enable hands-off-pipeline.timer

        # Start services
        echo -e "${GREEN}Starting services...${NC}"
        sudo systemctl start hands-off-selfheal
        sudo systemctl start hands-off-health-monitor
        sudo systemctl start hands-off-pipeline.timer

        # Check status
        echo ""
        echo -e "${GREEN}Service status:${NC}"
        sudo systemctl status hands-off-selfheal --no-pager || true
        sudo systemctl status hands-off-health-monitor --no-pager || true

        echo ""
        echo -e "${GREEN}Installation complete!${NC}"
        echo ""
        echo "View logs with:"
        echo "  sudo journalctl -u hands-off-selfheal -f"
        echo "  sudo journalctl -u hands-off-health-monitor -f"
        echo ""
        echo "Check health:"
        echo "  python3 infrastructure/health_monitor.py"
        ;;

    2)
        echo ""
        echo -e "${GREEN}Installing Docker Compose...${NC}"

        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            echo -e "${YELLOW}Docker not found. Installing Docker...${NC}"
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
            echo -e "${YELLOW}Please log out and back in for Docker group membership to take effect${NC}"
            echo -e "${YELLOW}Then run this script again${NC}"
            exit 0
        fi

        # Check if docker-compose is installed
        if ! command -v docker-compose &> /dev/null; then
            echo -e "${YELLOW}Docker Compose not found. Installing...${NC}"
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi

        cd infrastructure

        # Build images
        echo -e "${GREEN}Building Docker images...${NC}"
        docker-compose build

        # Start services
        echo -e "${GREEN}Starting containers...${NC}"
        docker-compose up -d selfheal health-monitor admin-server

        # Check status
        echo ""
        echo -e "${GREEN}Container status:${NC}"
        docker-compose ps

        echo ""
        echo -e "${GREEN}Installation complete!${NC}"
        echo ""
        echo "View logs with:"
        echo "  docker-compose logs -f selfheal"
        echo "  docker-compose logs -f health-monitor"
        echo ""
        echo "Check health:"
        echo "  docker-compose exec health-monitor python3 /app/infrastructure/health_monitor.py --json"
        ;;

    3)
        echo ""
        echo -e "${GREEN}Installing infrastructure services only...${NC}"

        # Just install and start monitoring services
        sudo cp infrastructure/systemd/hands-off-selfheal.service /etc/systemd/system/
        sudo cp infrastructure/systemd/hands-off-health-monitor.service /etc/systemd/system/

        sudo systemctl daemon-reload
        sudo systemctl enable hands-off-selfheal hands-off-health-monitor
        sudo systemctl start hands-off-selfheal hands-off-health-monitor

        echo ""
        echo -e "${GREEN}Installation complete!${NC}"
        echo ""
        echo "Self-healing and health monitoring are now active."
        echo "Your existing cron jobs will continue to run."
        echo ""
        echo "Check status:"
        echo "  sudo systemctl status hands-off-selfheal"
        echo "  python3 infrastructure/health_monitor.py"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Create a test backup
echo ""
echo -e "${GREEN}Creating initial backup...${NC}"
python3 infrastructure/backup_manager.py --create

# Run health check
echo ""
echo -e "${GREEN}Running health check...${NC}"
python3 infrastructure/health_monitor.py

echo ""
echo -e "${GREEN}=========================================="
echo "Setup complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Review logs to ensure services are running"
echo "  2. Configure alerts (Telegram, email)"
echo "  3. Set up cloud backups (optional)"
echo "  4. Review docs/FAULT_TOLERANT_ARCHITECTURE.md"
echo ""
echo "For help:"
echo "  - View logs: sudo journalctl -u hands-off-selfheal -f"
echo "  - Check health: python3 infrastructure/health_monitor.py"
echo "  - Manual backup: python3 infrastructure/backup_manager.py --create"
echo "  - Force heal: python3 infrastructure/selfheal.py --force --service=orchestrator"
echo ""
