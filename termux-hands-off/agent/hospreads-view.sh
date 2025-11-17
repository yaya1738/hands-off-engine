#!/usr/bin/env bash
set -euo pipefail

ssh do138 'python3 - << "PY"
import json, pathlib

path = pathlib.Path("/root/hands-off-out/state/spreads_report.json")
data = json.loads(path.read_text())

print("=== SPREADS REPORT ===")
print("as_of:", data.get("as_of"))
print("markets_total:", data.get("markets_total"))
print("with_any_quotes:", data.get("with_any_quotes"))
print("tightest_yes_spreads_count:", data.get("tightest_yes_spreads_count"))
print("tightest_no_spreads_count:", data.get("tightest_no_spreads_count"))
print("best_underround_count:", data.get("best_underround_count"))
print("best_overround_count:", data.get("best_overround_count"))

markets = data.get("markets") or data.get("markets_sample") or []

print()
print("markets in report:", len(markets))

# If we ever add sample markets later, show a few of them
for m in markets[:10]:
    mid = m.get("mid")
    spread = m.get("yes_spread") or m.get("no_spread") or m.get("spread")
    print("- id:", m.get("id"), "| q:", (m.get("question") or "")[:80])
    print("  mid:", mid, "spread:", spread)
PY'
