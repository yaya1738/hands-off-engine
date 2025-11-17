#!/data/data/com.termux/files/usr/bin/sh
set -e
python "$HOME/hands-off/agents/cards_limits_fill.py"
python "$HOME/hands-off/agents/per_card_guardrail.py" >/dev/null 2>&1 || true
python "$HOME/hands-off/agents/rotate_today.py"      >/dev/null 2>&1 || true
python "$HOME/hands-off/agents/per_card_minpay.py"   >/dev/null 2>&1 || true
python "$HOME/hands-off/agents/finance_daily.py"     >/dev/null 2>&1 || true
python "$HOME/hands-off/agents/weekly_summary.py"    >/dev/null 2>&1 || true
python "$HOME/hands-off/agents/dashboard_builder.py" >/dev/null 2>&1 || true
termux-open-url "http://127.0.0.1:8123" >/dev/null 2>&1 || termux-open-url "file://$HOME/hands-off/dashboard/index.html"
echo "[done] refreshed cards, guardrails, summaries, dashboard"
