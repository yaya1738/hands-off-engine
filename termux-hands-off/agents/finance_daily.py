import json, pathlib, statistics

HOME = pathlib.Path.home()
LOG = HOME/"hands-off"/"logs"/"finance_balances.log"
OUTCSV = HOME/"hands-off"/"logs"/"finance_daily.csv"

def rows():
    if not LOG.exists(): return []
    out=[]
    with open(LOG, "r", encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
                ts = d.get("ts")
                # prefer raw, fallback to rounded
                val = d.get("usd_total_raw", d.get("usd_total"))
                if ts and val is not None:
                    out.append((ts, float(val)))
            except: pass
    return out

data = rows()
if not data:
    print("[i] no data"); raise SystemExit(0)

# group by YYYY-MM-DD then take the LAST value of that date
by_day = {}
for ts, val in data:
    day = ts[:10]
    by_day.setdefault(day, []).append((ts, val))

daily=[]
prev=None
for day in sorted(by_day.keys()):
    # sort by timestamp string, take last-of-day
    ts_vals = sorted(by_day[day], key=lambda x: x[0])
    last_val = ts_vals[-1][1]
    chg = None if prev is None else round(last_val - prev, 2)
    daily.append((day, round(last_val,2), chg))
    prev = last_val

OUTCSV.write_text(
    "date,usd_last,delta_vs_prev\n" +
    "\n".join(f"{d},{v},{'' if c is None else c}" for d,v,c in daily),
    encoding="utf-8"
)
print(f"[ok] wrote {OUTCSV}")
