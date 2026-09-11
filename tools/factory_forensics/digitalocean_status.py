#!/usr/bin/env python3
"""Read-only DigitalOcean account/infrastructure telemetry for the Factory.

The token is supplied only through the runtime environment (DO_API_TOKEN or
DIGITALOCEAN_API_TOKEN). No credential or raw billing payload is persisted.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

BASE = "https://api.digitalocean.com/v2"


def get(path: str, token: str) -> dict[str, Any]:
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def money(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def main() -> int:
    token = os.environ.get("DO_API_TOKEN") or os.environ.get("DIGITALOCEAN_API_TOKEN")
    if not token:
        print(json.dumps({"status": "unavailable", "reason": "no protected DigitalOcean API token configured"}))
        return 0

    try:
        account = get("/account", token).get("account", {})
        droplets = get("/droplets?per_page=200").get("droplets", []) if False else get("/droplets?per_page=200", token).get("droplets", [])
        invoices = get("/invoices?per_page=200", token).get("invoices", [])
    except urllib.error.HTTPError as exc:
        # Preserve fail-closed behavior while making the reason machine-readable.
        print(json.dumps({"status": "error", "http_status": exc.code, "reason": "DigitalOcean API request failed"}))
        return 0
    except Exception:
        print(json.dumps({"status": "error", "reason": "DigitalOcean API request failed"}))
        return 0

    historical_invoice_total = sum((money(i.get("total")) for i in invoices), Decimal("0"))
    open_invoice_total = sum((money(i.get("total")) for i in invoices if str(i.get("status", "")).lower() not in {"paid", "void"}), Decimal("0"))

    report = {
        "status": "ok",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "account": {
            "status": account.get("status"),
            "droplet_limit": account.get("droplet_limit"),
            "floating_ip_limit": account.get("floating_ip_limit"),
        },
        "infrastructure": {
            "droplet_count": len(droplets),
            "droplet_ids": [d.get("id") for d in droplets],
        },
        "billing": {
            "invoice_count": len(invoices),
            "historical_invoice_total": str(historical_invoice_total),
            "open_invoice_total": str(open_invoice_total),
        },
        "safety": {
            "read_only": True,
            "credentials_persisted": False,
            "provisioning_performed": False,
        },
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
