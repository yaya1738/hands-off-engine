#!/bin/bash
# Quick add today's cash explosion opportunity

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "========================================================================"
echo "  💰 ADD TODAY'S CASH EXPLOSION OPPORTUNITY 💰"
echo "========================================================================"
echo ""
echo "This will add a new cash generation opportunity discovered today."
echo ""

# Run interactive add
python3 business/cash_explosion_opportunities.py --add

echo ""
echo "========================================================================"
echo ""
echo "View dashboard: python3 business/cash_explosion_opportunities.py --dashboard"
echo "Update emergency plan: python3 business/emergency_financial_response.py"
echo ""
