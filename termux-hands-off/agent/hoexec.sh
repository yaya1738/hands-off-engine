#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"

ssh "$REMOTE" "/usr/local/bin/ho_executor_from_plan.py"
