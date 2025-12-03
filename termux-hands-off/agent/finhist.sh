#!/data/data/com.termux/files/usr/bin/bash
set -e
HIS="$HOME/hands-off/state/pnl_history.json"
[ -s "$HIS" ] || { echo "(no pnl_history.json yet)"; exit 0; }
RANGE="${1:-30d}"
DAILY=0; [ "${2:-}" = "--daily" ] && DAILY=1 || true

python - <<'PY'
import json, os, sys, time, math
from datetime import datetime, timezone

HOME = os.environ.get("HOME","")
HIS = os.path.join(HOME,"hands-off","state","pnl_history.json")

def load_hist(path):
    try:
        with open(path,"r",encoding="utf-8") as f: h = json.load(f)
        if not isinstance(h,list): return []
        out=[]
        for r in h:
            try:
                ts=float(r.get("ts")); tot=float(r.get("total"))
                out.append((ts,tot))
            except: pass
        return sorted(out, key=lambda x:x[0])
    except: return []

def parse_range(arg):
    if arg is None: return ("days", 30)
    arg = arg.strip().lower()
    if arg == "all": return ("all", None)
    if arg.endswith("d"):
        try: return ("days", int(arg[:-1]))
        except: return ("days", 30)
    try:
        return ("points", max(2, int(arg)))
    except:
        return ("days", 30)

def filter_hist(hist, mode):
    if not hist: return []
    if mode[0]=="all": return hist
    if mode[0]=="days":
        now = time.time()
        cutoff = now - mode[1]*24*3600
        return [p for p in hist if p[0]>=cutoff]
    # points
    return hist[-mode[1]:]

def daily_close(hist):
    """Return last point per UTC date."""
    from collections import OrderedDict
    if not hist: return []
    by_day = OrderedDict()
    for ts, tot in hist:
        d = datetime.utcfromtimestamp(ts).date().isoformat()
        by_day[d] = (ts, tot)  # override => last of day
    return [by_day[k] for k in by_day]

def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

# argv: RANGE, "--daily" flag is passed via env var ARGV2
rng = os.environ.get("RANGE","30d")
daily = os.environ.get("DAILY","0")=="1"

hist = load_hist(HIS)
mode = parse_range(rng)
seg = filter_hist(hist, mode)
if daily:
    seg = daily_close(seg)

# emit TSV
out = []
for ts, tot in seg:
    out.append(f"{iso(ts)}\t{tot:.2f}")
sys.stdout.write("\n".join(out) + ("\n" if out else ""))
PY
