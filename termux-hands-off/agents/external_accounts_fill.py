import json, pathlib
from private_state import private_path

p = private_path("agents/external_accounts.json", create_parent=True)
d = {}
if p.exists():
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: d = {}
def ask(k, default):
    cur = d.get(k, default)
    try:
        v = input(f"{k} [{cur}]: ").strip()
        if not v: return float(cur)
        return float(v)
    except: return float(cur)
keys = [
    ("paypal", 0.0),
    ("monzo", 0.0),
    ("robinhood_cash", 0.0),
    ("polymarket_cash", 0.0),
    ("credit_cards", 0.0)  # enter negative for liabilities
]
for k,defv in keys:
    d[k] = ask(k, defv)
p.write_text(json.dumps(d, indent=2), encoding="utf-8")
print("[ok] external accounts updated ->", p)
