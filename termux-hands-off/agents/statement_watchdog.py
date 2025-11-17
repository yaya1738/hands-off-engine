#!/usr/bin/env python3
import json, pathlib, datetime, os

HOME = pathlib.Path.home()
CARDS = HOME/"hands-off"/"agents"/"cards.json"
LOG   = HOME/"hands-off"/"logs"/"finance_credit.log"

WARN_DAYS = 5  # ping 5 days before statement date

def notify(title, text):
    os.system(f'termux-notification --title "{title}" --content "{text}" >/dev/null 2>&1')

def load_cards():
    d = json.loads(CARDS.read_text()) if CARDS.exists() else {}
    out=[]
    for k,v in d.items():
        try:
            name=v.get("name",k); lim=float(v.get("limit",0)); bal=float(v.get("balance",0))
            stmt=int(v.get("statement_day",15))
            if lim>0: out.append({"key":k,"name":name,"limit":lim,"balance":bal,"statement_day":stmt})
        except: pass
    return out

def next_statement_date(day_of_month):
    today = datetime.date.today()
    # if today <= d, use this month; else next month
    y,m = today.year, today.month
    d = min(day_of_month, 28)  # keep safe
    date_this = datetime.date(y,m,d)
    if today <= date_this:
        return date_this
    # roll month
    if m==12: y,m = y+1,1
    else: m+=1
    return datetime.date(y,m,d)

def main():
    cards = load_cards()
    tl = sum(c["limit"] for c in cards)
    tb = sum(c["balance"] for c in cards)
    util = (tb/tl) if tl>0 else 0.0

    msgs=[]
    today = datetime.date.today()
    for c in cards:
        nxt = next_statement_date(c["statement_day"])
        days = (nxt - today).days
        if days == WARN_DAYS or days == 0:
            tag = "WARN" if days==WARN_DAYS else "DUE"
            msgs.append(f'{tag}: {c["name"]} statement {nxt.isoformat()} (in {days}d)')

    if msgs:
        body = f'Total util {round(util*100,1)}% | ' + " / ".join(msgs)
        notify("Statements", body)

    row = {
        "ts": datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z",
        "total_utilization": round(util,4),
        "statement_notes": msgs
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG,"a",encoding="utf-8") as f: f.write(json.dumps(row)+"\n")
    print(json.dumps(row, indent=2))

if __name__=="__main__":
    main()
