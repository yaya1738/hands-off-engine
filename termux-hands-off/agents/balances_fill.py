#!/usr/bin/env python3
import json, pathlib, math
from private_state import private_path

EXT = private_path("agents/external_accounts.json", create_parent=True)
d={}
if EXT.exists():
    try: d=json.loads(EXT.read_text())
    except: d={}
def ask(k, cur):
    try:
        shown = cur if cur is not None else "unknown"
        value = input(f"{k} [{shown}]: ").strip()
        if value == "":
            return float(cur) if cur is not None else None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return float(cur) if cur is not None else None
fields=[
    ("paypal", d.get("paypal")),
    ("monzo", d.get("monzo")),
    ("robinhood_cash", d.get("robinhood_cash")),
    ("polymarket_cash", d.get("polymarket_cash")),
]
for k,cur in fields:
    d[k]=ask(k, cur)
EXT.write_text(json.dumps(d, indent=2), encoding="utf-8")
print("[ok] balances updated ->", EXT)
