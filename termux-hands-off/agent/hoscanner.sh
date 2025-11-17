#!/usr/bin/env bash
set -euo pipefail

REMOTE="do138"
FILE="/root/hands-off-out/state/scanner_report.json"

ssh "$REMOTE" "sed -n '1,80p' \"$FILE\" || echo \"[warn] no scanner_report.json yet\""
