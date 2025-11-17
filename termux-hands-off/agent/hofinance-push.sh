#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"
VIEW_URL="http://127.0.0.1:8001/txt/finance"

echo "================ HANDS-OFF FINANCE ==============="

ssh "$REMOTE" "curl -fsS \"$VIEW_URL\" || echo '{\"updated\":\"STUB\",\"accounts\":[],\"total_usd\":0.0,\"prev_usd\":0.0,\"delta_usd\":0.0}'"
echo
