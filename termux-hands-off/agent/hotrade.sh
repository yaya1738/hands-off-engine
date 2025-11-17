#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

echo "===== GATE ====="
ssh "$REMOTE" "/usr/local/bin/ho_gate"
echo

echo "===== PLAN ====="
ssh "$REMOTE" 'if [ -x /usr/local/bin/ho_plan_view.py ]; then /usr/local/bin/ho_plan_view.py; else /usr/local/bin/ho_plan_view; fi'
echo

echo "===== ORDERS ====="
ssh "$REMOTE" 'if [ -x /usr/local/bin/ho_orders_view.py ]; then /usr/local/bin/ho_orders_view.py; else /usr/local/bin/ho_orders_view; fi'
echo

echo "===== INSIGHT ====="
ssh "$REMOTE" 'if [ -x /usr/local/bin/ho_insight.py ]; then /usr/local/bin/ho_insight.py; else /usr/local/bin/ho_insight; fi'
