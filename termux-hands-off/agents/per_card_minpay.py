#!/usr/bin/env python3
import json, pathlib, datetime, math

HOME = pathlib.Path.home()
CARDS = HOME/"hands-off"/"agents"/"cards.json"
OUT_JSON = HOME/"hands-off"/"logs"/"cards_minpay.json"
OUT_LOG  = HOME/"hands-off"/"logs"/"cards_minpay.log"

def load_cards():
    if not CARDS.exists(): return []
    try: return json.loads(CARDS.read_text())
    except: return []

# Heuristic min payment:
#   min = max($25, 3% of balance)  (conservative, adjust if issuer differs)
def min_payment(balance: float) -> float:
    b = float(balance or 0)
    return round(max(25.0, 0.03*b), 2) if b>0 else 0.0

def targets(c):
    limit=float(c.get("limit",0) or 0)
    bal =float(c.get("balance",0) or 0)
    to50 = round(max(0.0, bal - 0.50*limit),2) if limit>0 else 0.0
    to45 = round(max(0.0, bal - 0.45*limit),2) if limit>0 else 0.0
    return to50, to45

cards = load_cards()
rows = []
for c in cards:
    name=c.get("name","card")
    bal =float(c.get("balance",0) or 0)
    apr =float(c.get("apr_pct",0) or 0)
    sday=int(c.get("statement_day",10) or 10)

    mp = min_payment(bal)
    to50,to45 = targets(c)
    util = (bal/float(c.get("limit",1))) if float(c.get("limit",0))>0 else 0.0

    rows.append({
        "name":name,
        "balance":round(bal,2),
        "apr_pct":round(apr,2),
        "statement_day":sday,
        "min_payment":mp,
        "to_below_50":to50,
        "to_below_45":to45,
        "util":round(util,4),
    })

snap = {"ts": datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z", "cards": rows}
OUT_JSON.write_text(json.dumps(snap, indent=2), encoding="utf-8")
OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
OUT_LOG.open("a", encoding="utf-8").write(json.dumps(snap)+"\n")
print(json.dumps(snap, indent=2))
