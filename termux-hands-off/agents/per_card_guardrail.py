#!/usr/bin/env python3
import json, pathlib, datetime, math, os

HOME = pathlib.Path.home()
CARDS = HOME/"hands-off"/"agents"/"cards.json"
OUT_LOG = HOME/"hands-off"/"logs"/"cards_status.log"
OUT_JSON= HOME/"hands-off"/"logs"/"cards_status.json"

def notify(title, text):
    os.system(f'termux-notification --title "{title}" --content "{text}" >/dev/null 2>&1')

def load_cards():
    if not CARDS.exists(): return []
    try: return json.loads(CARDS.read_text())
    except: return []

def next_statement_countdown(day):
    # Using local timezone date (Termux device local time)
    today = datetime.date.today()
    # clamp day 1..28
    d = min(28, max(1, int(day or 1)))
    # candidate this month
    try:
        cand = datetime.date(today.year, today.month, d)
    except:
        cand = today
    if cand <= today:
        # next month
        year, month = (today.year + (today.month==12), 1 if today.month==12 else today.month+1)
        cand = datetime.date(year, month, d)
    return (cand - today).days

cards = load_cards()
rows = []
alerts = []
for c in cards:
    name   = c.get("name","card")
    limit  = float(c.get("limit",0) or 0)
    bal    = float(c.get("balance",0) or 0)
    apr    = float(c.get("apr_pct",0) or 0)
    sday   = int(c.get("statement_day",10) or 10)
    util   = (bal/limit) if limit>0 else 0.0
    days   = next_statement_countdown(sday)
    flags  = []
    # guardrails
    if util >= 0.50: flags.append("HARD>50%")
    elif util >= 0.45: flags.append("WARN>45%")
    if days <= 3 and util >= 0.30: flags.append("CUT SOON")
    if apr >= 25 and util >= 0.40: flags.append("APR x UTIL")

    rows.append({
        "name": name, "limit": round(limit,2), "balance": round(bal,2),
        "util": round(util,4), "apr_pct": round(apr,2),
        "statement_day": sday, "days_to_statement": days,
        "flags": flags
    })
    if flags:
        alerts.append(f"{name}: util {util*100:.1f}%, {days}d→stmt | " + ", ".join(flags))

# notify
if alerts:
    notify("Card Guardrail", " | ".join(alerts)[:250])

# persist
OUT_JSON.write_text(json.dumps({"ts": datetime.datetime.utcnow().isoformat()+"Z", "cards": rows}, indent=2), encoding="utf-8")
with OUT_LOG.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"ts": datetime.datetime.utcnow().isoformat()+"Z", "cards": rows})+"\n")

# print summary
print(json.dumps({"alerts": alerts, "cards": rows}, indent=2))
