#!/usr/bin/env python3
"""Read-only daily summary compatibility facade."""
import glob
import json
import os
from datetime import datetime, timezone

REG = os.path.expanduser("~/hands-off/state/balances.d")


def load():
    parts, total = [], 0.0
    for p in sorted(glob.glob(os.path.join(REG, "*.json"))):
        try:
            with open(p) as f:
                d = json.load(f)
            name = d.get("name") or os.path.splitext(os.path.basename(p))[0]
            amount = float(d.get("balance_usd", 0.0))
            parts.append((name, amount))
            total += amount
        except Exception:
            pass
    return parts, total


def build_message():
    parts, total = load()
    if not parts:
        return "Daily Summary: no sources yet"
    lines = "\n".join(f"- {name}: ${amount:,.2f}" for name, amount in parts)
    return f"Daily Summary\nTotal: ${total:,.2f}\n\n{lines}"


def notify(message):
    return {
        "success": False,
        "authority_required": "FactoryAuthorityGateway",
        "message": message,
    }


if __name__ == "__main__":
    print(json.dumps(notify(build_message()), ensure_ascii=False, indent=2))
