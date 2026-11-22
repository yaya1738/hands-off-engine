import json, pathlib, math
from private_state import private_path

p = private_path("agents/external_accounts.json", create_parent=True)
d = {}
if p.exists():
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: d = {}
def ask(k, default=None):
    cur = d.get(k, default)
    try:
        shown = cur if cur is not None else "unknown"
        value = input(f"{k} [{shown}]: ").strip()
        if not value:
            return float(cur) if cur is not None else None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return float(cur) if cur is not None else None
keys = [
    ("paypal", None),
    ("monzo", None),
    ("robinhood_cash", None),
    ("polymarket_cash", None),
    ("credit_cards", None)  # enter negative for liabilities
]
for k,defv in keys:
    d[k] = ask(k, defv)
p.write_text(json.dumps(d, indent=2), encoding="utf-8")
print("[ok] external accounts updated ->", p)
