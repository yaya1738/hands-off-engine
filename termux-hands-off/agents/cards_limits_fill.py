#!/usr/bin/env python3
import json, pathlib, datetime

HOME = pathlib.Path.home()
CARDS = HOME/"hands-off"/"agents"/"cards.json"

# Default template if file missing
default_cards = [
  {"name":"Capital One",       "limit": 10000.0, "balance": 6234.0, "apr_pct": 24.99, "statement_day": 14},
  {"name":"PayPal Cashback",   "limit":  8000.0, "balance": 7853.0, "apr_pct": 25.99, "statement_day": 12},
  {"name":"PayPal Credit",     "limit":  5000.0, "balance": 4879.0, "apr_pct": 28.99, "statement_day": 10},
  {"name":"Avant",             "limit":  2000.0, "balance":    0.0, "apr_pct": 29.99, "statement_day": 18}
]

def load_cards():
    if CARDS.exists():
        try: return json.loads(CARDS.read_text())
        except: pass
    return default_cards

def ask(prompt, cur, cast=float):
    s = input(f"{prompt} [{cur}]: ").strip()
    if s=="":
        return cur
    try:
        return cast(s)
    except:
        return cur

cards = load_cards()
print("\n[Cards quick editor] (Enter keeps current)\n")
for c in cards:
    print(f"--- {c.get('name','(card)')} ---")
    c["limit"]   = ask("Limit",   c.get("limit",0.0))
    c["balance"] = ask("Balance", c.get("balance",0.0))
    c["apr_pct"] = ask("APR %",   c.get("apr_pct",0.0))
    c["statement_day"] = int(ask("Statement day (1-28)", c.get("statement_day",10), int))

CARDS.write_text(json.dumps(cards, indent=2), encoding="utf-8")
print(f"[ok] wrote {CARDS}")
