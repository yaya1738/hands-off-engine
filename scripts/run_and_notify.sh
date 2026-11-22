#!/usr/bin/env bash
set -euo pipefail

echo "BLOCKED: legacy run-and-notify wrapper is disabled pending verified financial truth and credential remediation."
echo "No state defaults were created, no pipeline was run, and no notification was sent."
echo "For read-only shadow research, invoke scripts/run_pipeline.py directly; it now requires a verified balance or an explicit model-only bankroll."
exit 1
