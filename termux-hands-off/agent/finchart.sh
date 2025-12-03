#!/data/data/com.termux/files/usr/bin/bash
# Usage: finchart [range]
#   range examples: 7d | 30d | 90d | 200 (points)
set -e
HIS="$HOME/hands-off/state/pnl_history.json"
[ -s "$HIS" ] || { echo "(no pnl_history.json yet)"; exit 0; }
RANGE="${1:-30d}"

python - <<'PY'
import json, os, sys, time, math
from datetime import datetime

HOME = os.environ.get("HOME","")
HIS = os.path.join(HOME,"hands-off","state","pnl_history.json")

def load_hist(path):
    try:
        with open(path,"r",encoding="utf-8") as f: h = json.load(f)
        if not isinstance(h,list): return []
        # keep only items with ts & total
        out=[]
        for r in h:
            try:
                ts=float(r.get("ts"))
                tot=float(r.get("total"))
                out.append((ts,tot))
            except: pass
        return sorted(out, key=lambda x:x[0])
    except:
        return []

def parse_range(arg, n_default=200):
    if not arg: return ("points", n_default)
    arg = arg.strip().lower()
    if arg.endswith("d"):
        try:
            days = int(arg[:-1])
            return ("days", days)
        except: pass
    try:
        pts = int(arg)
        return ("points", pts)
    except:
        return ("days", 30)

def filter_hist(hist, mode):
    now = time.time()
    if mode[0]=="days":
        cutoff = now - mode[1]*24*3600
        return [p for p in hist if p[0]>=cutoff]
    else:
        # last N points
        n = max(2, mode[1])
        return hist[-n:]

def spark(values, width=64):
    # unicode sparkline blocks
    blocks = "▁▂▃▄▅▆▇█"
    if not values: return ""
    vmin, vmax = min(values), max(values)
    if vmax==vmin:
        return blocks[0]*min(len(values), width)
    # compress to width if too many points
    pts = values
    if len(values)>width:
        step = len(values)/width
        idxs = [int(i*step) for i in range(width)]
        pts = [values[i] for i in idxs]
    out=[]
    for v in pts:
        # normalize 0..1
        x=(v-vmin)/(vmax-vmin)
        k=min(len(blocks)-1, int(round(x*(len(blocks)-1))))
        out.append(blocks[k])
    return "".join(out)

def fmt(v):
    try:
        return f"{v:,.2f}"
    except:
        return str(v)

hist = load_hist(HIS)
mode = parse_range(sys.argv[1] if len(sys.argv)>1 else "30d")
seg = filter_hist(hist, mode)
if len(seg)<2:
    print("(not enough points yet)")
    sys.exit(0)

ts0, v0 = seg[0]
ts1, v1 = seg[-1]
vals = [v for _,v in seg]
line = spark(vals, width=64)

delta = v1 - v0
pct = (delta/v0*100.0) if v0>0 else None

# simple dailyized rate over segment (not annualized—keeps it honest on small windows)
days = max(1e-9,(ts1-ts0)/86400.0)
daily = ((v1/v0)**(1.0/days)-1.0)*100.0 if v0>0 else None
# conservative annualized (if window >= 7d)
ann = ( (1+daily/100.0)**365 - 1 )*100.0 if (daily is not None and days>=7) else None

rng = f"{mode[1]}{'d' if mode[0]=='days' else 'pts'}"
print(f"Range: {rng}   Points: {len(seg)}   First: {datetime.utcfromtimestamp(ts0).isoformat(timespec='seconds')}Z   Last: {datetime.utcfromtimestamp(ts1).isoformat(timespec='seconds')}Z")
print(f"Net USD: {fmt(v1)}   Δ: {fmt(delta)}   {(f'({pct:+.2f}% )' if pct is not None else '')}")
if daily is not None:
    s = f"Daily: {daily:+.2f}%"
    if ann is not None:
        s += f"   Annualized (approx): {ann:+.1f}%"
    print(s)
print(line)
PY
