#!/usr/bin/env python3

import json
import subprocess
import sys

data = json.loads(
    subprocess.check_output(
        [sys.executable, "-m", "autonomous.integrations.supervisor"],
        text=True
    )
)

if "--json" in sys.argv:
    print(json.dumps(data, indent=2))
    raise SystemExit(0)

warnings = []

for name, info in data.get("integrations", {}).items():
    if not info.get("connected", True):
        warnings.append(f"{name}: not connected")

for action in data.get("credential_sync", {}).get("actions", []):
    if action.get("action") != "none":
        warnings.append(
            f"{action.get('identity')}: {action.get('action')}"
        )

print("=== HANDS-OFF ENGINE STATUS ===")
print()

print("Overall:")
if warnings:
    print("  STATUS: ACTION REQUIRED")
else:
    print("  STATUS: HEALTHY")

print()

print("Health:")
print(f"  Supervisor: {'ONLINE' if data.get('healthy') else 'DEGRADED'}")
print(f"  Timestamp: {data.get('timestamp')}")

print()

print("Integrations:")
for name, info in data.get("integrations", {}).items():
    print(f"  {name}:")
    print(f"    Connected: {'YES' if info.get('connected') else 'NO'}")
    print(f"    Token: {'PRESENT' if info.get('token_present') else 'MISSING'}")

print()

print("Warnings:")
if warnings:
    for w in warnings:
        print(f"  ⚠ {w}")
else:
    print("  None")

print()

print("Pending Actions:")
for action in data.get("credential_sync", {}).get("actions", []):
    print(
        f"  {action.get('identity')}: "
        f"{action.get('action')}"
    )
