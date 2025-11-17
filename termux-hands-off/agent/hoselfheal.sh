#!/usr/bin/env bash
set -euo pipefail

ssh do138 'cd /root/hands-off-out/state && python3 - << "PY"
import json, pathlib

p = pathlib.Path("selfheal_report.json")
try:
    data = json.loads(p.read_text())
except Exception as e:
    print("[selfheal] could not read selfheal_report.json:", e)
    raise SystemExit(0)

print("=== SELFHEAL REPORT ===")
print("as_of:", data.get("as_of"))
print()

print("Services:")
for name, info in (data.get("services") or {}).items():
    print(f" - {name}: active={info.get('active')} action={info.get('action')} error={info.get('error')}")
print()

print("Files:")
for name, info in (data.get("files") or {}).items():
    age = info.get("age_seconds")
    if isinstance(age, (int, float)):
        age_str = f"{int(age)}s (~{int(age//60)} min)"
    else:
        age_str = "unknown"
    print(f" - {name}: exists={info.get('exists')} stale={info.get('stale')} age={age_str}")
print()

actions = data.get("actions") or []
warnings = data.get("warnings") or []
errors = data.get("errors") or []

print("Actions:")
if actions:
    for a in actions:
        print(" -", a)
else:
    print(" - (none)")

print("\\nWarnings:")
if warnings:
    for w in warnings:
        print(" -", w)
else:
    print(" - (none)")

print("\\nErrors:")
if errors:
    for e in errors:
        print(" -", e)
else:
    print(" - (none)")
PY'
