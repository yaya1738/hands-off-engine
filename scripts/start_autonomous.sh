#!/bin/bash
#
# Start the Unified Autonomous System
#
# This script starts the complete autonomous infrastructure management system.
# The system will:
# - Monitor hardware health continuously
# - Provision/upgrade servers automatically
# - Protect trading at all costs
# - Require NO user intervention
#
# Usage:
#   ./start_autonomous.sh              # Start with defaults
#   ./start_autonomous.sh --dry-run    # Test mode (no actual provisioning)
#   ./start_autonomous.sh --budget 1000  # Custom budget
#
# Standard: Yair Siegel Master Level Operations - Full Self-Control

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}     UNIFIED AUTONOMOUS SYSTEM - STARTUP${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 not found${NC}"
    exit 1
fi

# Check for required environment variables
check_env() {
    if [ -n "$DO_API_TOKEN" ]; then
        echo -e "${GREEN}✓ DigitalOcean API configured${NC}"
    elif [ -n "$AWS_ACCESS_KEY_ID" ]; then
        echo -e "${GREEN}✓ AWS API configured${NC}"
    else
        echo -e "${YELLOW}⚠ No cloud provider configured - running in mock mode${NC}"
        echo -e "${YELLOW}  Set DO_API_TOKEN or AWS_ACCESS_KEY_ID for live provisioning${NC}"
    fi
}

check_env

# Change to project directory
cd "$PROJECT_DIR"

# Default arguments
BUDGET="500"
DRY_RUN=""
EXTRA_ARGS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --budget)
            BUDGET="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
    esac
done

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Budget: \$${BUDGET}/month"
echo -e "  Dry Run: ${DRY_RUN:-disabled}"
echo ""

# Start the system
echo -e "${GREEN}Starting autonomous system...${NC}"
echo ""

exec python3 -m autonomous.unified_system \
    --budget "$BUDGET" \
    $DRY_RUN \
    $EXTRA_ARGS
