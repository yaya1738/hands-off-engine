#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
================ HANDS-OFF HELP ================
Core status & safety
  ho           - master quick panel (hostate + cockpit + snapshot)
  hostate      - one-line state summary (as_of, health, mode, tradeable, budget, events, plan_live_usd, finance_total_usd)
  hohealth     - remote health + infra snapshot (health.json + infra.txt)
  hocockpit    - full cockpit: gate + plan + orders + finance
  hosnapshot   - compact JSON snapshot for bots/dashboards

Trading / executor
  hoexec       - run executor_from_plan once (currently DRYRUN-only)
  hoexecsafe   - run executor_from_plan with health/infra/gate checks

Mirroring & infra
  homirror     - mirror state from Termux to droplet (+ refresh .last_ok on remote)

Finance
  hofinance    - show finance summary + current orders (from droplet)
  hofinancepush- push latest finance JSON/summary to remote/IFTTT/Telegram if configured

Meta
  hohelp       - show this help

Notes:
  - LIVE trading is globally controlled on the droplet; right now everything is DRYRUN-only.
  - Always glance at: hostate and/or ho before touching anything execution-related.
================ END HANDS-OFF HELP ============
EOF
