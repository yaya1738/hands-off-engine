#!/usr/bin/env bash
set -euo pipefail
REMOTE="do138"
ssh "$REMOTE" <<'BASH'
set -e
STATE="/root/hands-off-out/state"

echo "[step] decider.service"
systemctl start decider.service || echo "[warn] decider.service failed to start (maybe already running)"
sleep 2

echo "[step] ho-decision-infra.py"
/usr/bin/python3 /usr/local/bin/ho-decision-infra.py || echo "[warn] ho-decision-infra.py failed"

echo "[step] ho_add_test_orders.py"
/usr/bin/python3 /usr/local/bin/ho_add_test_orders.py || echo "[warn] ho_add_test_orders.py failed"

echo "[step] ho_executor_plan.sh"
/usr/local/bin/ho_executor_plan.sh || echo "[warn] ho_executor_plan.sh failed"

echo "[step] ho_executor_from_plan.py"
/usr/bin/python3 /usr/local/bin/ho_executor_from_plan.py || echo "[warn] ho_executor_from_plan.py failed"

echo
echo "[check] execution_plan.effective.json (head)"
sed -n '1,120p' "$STATE/execution_plan.effective.json" 2>/dev/null || sed -n '1,120p' "$STATE/execution_plan.json" 2>/dev/null || echo "[info] no execution_plan json yet"
BASH
