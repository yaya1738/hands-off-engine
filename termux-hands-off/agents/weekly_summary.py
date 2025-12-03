#!/usr/bin/env python3
import json, pathlib, datetime, os, statistics

HOME = pathlib.Path.home()
EXT  = HOME/"hands-off/agents/external_accounts.json"
CARDS= HOME/"hands-off/agents/cards.json"
BAL  = HOME/"hands-off/logs/finance_balances.log"
CRED = HOME/"hands-off/logs/finance_credit.log"

def notify(title, text):
    os.system(f'termux-notification --title "{title}" --content "{text}" >/dev/null 2>&1')

def get_total_util():
    if not CRED.exists(): return None
    last=None
    for line in CRED.read_text(encoding="utf-8").splitlines():
        try:
            d=json.loads(line); last=d
        except: pass
    return (last or {}).get("total_utilization")

def last_usd():
    if not BAL.exists(): return None
    last=None
    for line in BAL.read_text(encoding="utf-8").splitlines():
        try:
            d=json.loads(line); last=d
        except: pass
    if not last: return None
    return float(last.get("usd_total_raw", last.get("usd_total", 0.0)))

def week_delta():
    if not BAL.exists(): return None
    rows=[]
    for line in BAL.read_text(encoding="utf-8").splitlines():
        try:
            d=json.loads(line)
            ts=d.get("ts"); v=d.get("usd_total_raw", d.get("usd_total"))
            if ts and v is not None:
                rows.append((ts[:10], float(v)))
        except: pass
    if not rows: return None
    rows.sort(key=lambda x: x[0])
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=7)).isoformat()
    prev  = (today - datetime.timedelta(days=14)).isoformat()
    last7=[v for d,v in rows if d>=start]
    prev7=[v for d,v in rows if prev<=d<start]
    if not last7 or not prev7: return None
    return round(statistics.median(last7) - statistics.median(prev7), 2)

def pm_ev():
    import json
    EXT = pathlib.Path.home()/ "hands-off/agents/external_accounts.json"
    if not EXT.exists(): return None, None
    d=json.loads(EXT.read_text())
    return d.get("polymarket_positions_mark"), d.get("polymarket_unrealized_est")

def rent_info():
    if not EXT.exists(): return None, None
    d=json.loads(EXT.read_text())
    return d.get("rent_monthly_shekel"), d.get("rent_monthly_usd")

def main():
    pm_mark, pm_unr = pm_ev()
    total = last_usd()
    util  = get_total_util()
    delta = week_delta()
    rent_il, rent_usd = rent_info()
    parts=[]
    if total is not None: parts.append(f"Net ${round(total,2)}")
    if util  is not None: parts.append(f"Util {round(util*100,1)}%")
    if rent_il is not None: parts.append(f"Rent ₪{rent_il}/mo (~${rent_usd})")
    if delta is not None: parts.append(f"W/W Δ ${delta}")
    if pm_mark is not None: parts.append(f"PM EV ${round(pm_mark,2)}")
    if pm_unr is not None: parts.append(f"PM Unreal ${round(pm_unr,2)}")
    msg=" | ".join(parts) if parts else "No data yet"
    notify("Weekly Summary", msg)
    print(msg)

if __name__=="__main__":
    main()
