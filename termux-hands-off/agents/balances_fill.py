#!/usr/bin/env python3
import json, pathlib
EXT=pathlib.Path.home()/ "hands-off/agents/external_accounts.json"
d={}
if EXT.exists():
    try: d=json.loads(EXT.read_text())
    except: d={}
def ask(k, cur):
    try:
        v=input(f"{k} [{cur}]: ").strip()
        return float(v) if v!="" else float(cur or 0)
    except: return float(cur or 0)
fields=[
    ("paypal", d.get("paypal",0.0)),
    ("monzo", d.get("monzo",0.0)),
    ("robinhood_cash", d.get("robinhood_cash",0.0)),
    ("polymarket_cash", d.get("polymarket_cash",0.0)),
]
for k,cur in fields:
    d[k]=ask(k, cur)
EXT.write_text(json.dumps(d, indent=2), encoding="utf-8")
print("[ok] balances updated ->", EXT)
