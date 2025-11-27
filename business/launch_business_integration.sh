#!/bin/bash
# Yair Siegel Business Integration Launcher
# Quick launcher for business integration system

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$REPO_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "  Yair Siegel Business Integration System"
echo "======================================================================"
echo ""

# Check if data directory exists
if [ ! -d "business/data" ]; then
    echo -e "${YELLOW}⚠ Business data directory not found. Will be created on first run.${NC}"
    echo ""
fi

# Show menu
echo "Available commands:"
echo ""
echo "  1) dashboard    - Show current business dashboard"
echo "  2) init         - Initialize business systems"
echo "  3) sync         - Run single synchronization"
echo "  4) cycle        - Run complete business cycle"
echo "  5) optimize     - Generate optimization report"
echo "  6) continuous   - Run continuous integration (1 hour cycles)"
echo "  7) sync-cont    - Run continuous sync (5 min cycles)"
echo "  8) status       - Show system status"
echo "  9) logs         - View recent logs"
echo "  q) quit         - Exit"
echo ""

read -p "Select option: " option

case $option in
    1|dashboard)
        echo -e "${GREEN}📊 Generating business dashboard...${NC}"
        python3 business/yair_siegel_business_integration.py --dashboard
        ;;
    2|init)
        echo -e "${GREEN}🚀 Initializing business systems...${NC}"
        python3 business/yair_siegel_business_integration.py --init
        ;;
    3|sync)
        echo -e "${GREEN}🔄 Running synchronization...${NC}"
        python3 business/business_sync_engine.py --once
        ;;
    4|cycle)
        echo -e "${GREEN}♻️ Running business cycle...${NC}"
        python3 business/yair_siegel_business_integration.py --cycle
        ;;
    5|optimize)
        echo -e "${GREEN}🎯 Generating optimization report...${NC}"
        python3 business/business_optimization_agent.py
        ;;
    6|continuous)
        echo -e "${GREEN}⚙️ Starting continuous integration (hourly cycles)...${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
        python3 business/yair_siegel_business_integration.py --continuous
        ;;
    7|sync-cont)
        echo -e "${GREEN}⚙️ Starting continuous sync (5 minute cycles)...${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
        python3 business/business_sync_engine.py --interval 300
        ;;
    8|status)
        echo -e "${GREEN}📋 System Status:${NC}"
        echo ""
        if [ -f "business/data/integration_state.json" ]; then
            echo "Integration State:"
            cat business/data/integration_state.json | jq '.'
            echo ""
        else
            echo -e "${YELLOW}Not initialized yet${NC}"
            echo ""
        fi
        if [ -f "business/data/yair_siegel_business_state.json" ]; then
            echo "Current Business Health:"
            cat business/data/yair_siegel_business_state.json | jq '.business_health'
        fi
        ;;
    9|logs)
        echo -e "${GREEN}📜 Recent Integration Logs (last 10):${NC}"
        if [ -f "business/data/integration_log.jsonl" ]; then
            tail -10 business/data/integration_log.jsonl | jq -r '[.timestamp, .event_type] | @tsv'
        else
            echo -e "${YELLOW}No logs yet${NC}"
        fi
        echo ""
        echo -e "${GREEN}📜 Recent Sync Events (last 10):${NC}"
        if [ -f "business/data/sync_log.jsonl" ]; then
            tail -10 business/data/sync_log.jsonl | jq -r '[.timestamp, .event_type] | @tsv'
        else
            echo -e "${YELLOW}No logs yet${NC}"
        fi
        ;;
    q|quit)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo "======================================================================"
