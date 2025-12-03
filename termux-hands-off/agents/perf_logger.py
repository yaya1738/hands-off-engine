#!/usr/bin/env python3
import json, pathlib, datetime, os

HOME = pathlib.Path.home()
INP  = HOME/"hands-off/agents/perf_inputs.json"
OUT  = HOME/"hands-off/logs/performance_daily.csv"

def today():
    return datetime.date.today().isoformat()

def load_inputs():
    d = json.loads(INP.read_text()) if INP.exists() else {}
    dt = d.get("date_override") or today()
    pm = float(d.get("polymarket_pnl", 0.0))
    rh = float(d.get("robinhood_pnl", 0.0))
    notes = str(d.get("notes","")).replace(",", ";")
    return dt, pm, rh, notes

def append_csv(row):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUT.exists():
        OUT.write_text("date,polymarket_pnl,robinhood_pnl,total_pnl,notes\n", encoding="utf-8")
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(row+"\n")

def main():
    dt, pm, rh, notes = load_inputs()
    tot = round(pm + rh, 2)
    row = f"{dt},{pm},{rh},{tot},{notes}"
    append_csv(row)
    os.system(f'termux-notification --title "P&L Logged" --content "{dt}: total ${tot}" >/dev/null 2>&1')
    print("[ok] performance logged:", row)

if __name__=="__main__":
    main()
