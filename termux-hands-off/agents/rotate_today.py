#!/usr/bin/env python3
import json, pathlib, datetime

HOME = pathlib.Path.home()
EXT          = HOME/"hands-off"/"agents"/"external_accounts.json"
CARDS_MINPAY = HOME/"hands-off"/"logs"/"cards_minpay.json"
CARDS_STATUS = HOME/"hands-off"/"logs"/"cards_status.json"   # from per_card_guardrail.py
OUT_JSON     = HOME/"hands-off"/"logs"/"rotate_today.json"

def jload(p, default=None):
    if not p.exists(): return default
    try: return json.loads(p.read_text())
    except: return default

ext = jload(EXT, {})
minp = jload(CARDS_MINPAY, {"cards":[]})
stat = jload(CARDS_STATUS, {"cards":[]})

cash = float(ext.get("paypal",0) or 0) + float(ext.get("monzo",0) or 0)
cards_mp = {c["name"]:c for c in minp.get("cards",[])}
cards_st = {c["name"]:c for c in stat.get("cards",[])}

# Build working rows merging both sources
rows=[]
for name, cm in cards_mp.items():
    st = cards_st.get(name, {})
    rows.append({
        "name": name,
        "balance": float(cm.get("balance",0) or 0),
        "apr": float(cm.get("apr_pct",0) or 0),
        "minpay": float(cm.get("min_payment",0) or 0),
        "to50": float(cm.get("to_below_50",0) or 0),
        "to45": float(cm.get("to_below_45",0) or 0),
        "util": float(cm.get("util",0) or 0),
        "days_to_stmt": int(st.get("days_to_statement",14) or 14)
    })

# Priority rules:
#  A) Cards ≤3 days to statement: cover min pay first.
#  B) Any card >50% util: push to 50% if cash remains (highest APR first).
#  C) Then reduce 50→45 on highest APR if cash remains.
plan=[]
left=cash

# A) imminent statements
for r in sorted([x for x in rows if x["days_to_stmt"]<=3 and x["minpay"]>0], key=lambda x:(x["days_to_stmt"], -x["apr"])):
    pay=min(left, r["minpay"])
    if pay>0:
        plan.append({"card":r["name"], "reason":"minpay (stmt soon)", "amount":round(pay,2)})
        left -= pay

# B) >50% util
for r in sorted([x for x in rows if x["to50"]>0], key=lambda x:(-x["apr"], -x["util"])):
    if left<=0: break
    pay=min(left, r["to50"])
    if pay>0:
        plan.append({"card":r["name"], "reason":"drop to 50%", "amount":round(pay,2)})
        left -= pay

# C) 50→45 for high APR
for r in sorted([x for x in rows if x["to45"]>0], key=lambda x:(-x["apr"], -x["util"])):
    if left<=0: break
    amt = r["to45"]
    pay=min(left, amt)
    if pay>0:
        plan.append({"card":r["name"], "reason":"tighten to 45%", "amount":round(pay,2)})
        left -= pay

summary = {
  "ts": datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z",
  "cash_available": round(cash,2),
  "cash_remaining": round(left,2),
  "actions": plan
}

OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
