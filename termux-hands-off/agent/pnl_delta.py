#!/usr/bin/env python3
import json, os, time, math
from pathlib import Path

HOME = os.environ.get("HOME","")
ST = Path(HOME)/"hands-off/state"
FIN = ST/"finance.json"
STATE = ST/"pnl_state.json"
HIST = ST/"pnl_history.json"
SUMM = ST/"pnl_summary.json"

def load_json(p, default):
    try:
        with open(p,"r",encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def numeric(x):
    try:
        if isinstance(x,(int,float)): return float(x)
        if isinstance(x,str): return float(x.strip())
    except Exception: pass
    return None

def get_total_usd(fin):
    # accept either explicit net_usd or sum of balances
    if isinstance(fin,dict):
        if "net_usd" in fin and numeric(fin["net_usd"]) is not None:
            return float(fin["net_usd"])
        if "balances" in fin and isinstance(fin["balances"],dict):
            s = 0.0; found=False
            for v in fin["balances"].values():
                n = numeric(v)
                if n is not None:
                    s += n; found=True
            if found: return s
    raise RuntimeError("Unable to derive total USD from finance.json")

now = time.time()

fin = load_json(FIN, {})
total = get_total_usd(fin)
ts = fin.get("ts", now)

state = load_json(STATE, {})
last_total = state.get("last_total")
last_ts = state.get("last_ts")

# load/initialize history
hist = load_json(HIST, [])
if not isinstance(hist, list): hist = []

# append current point
hist.append({"ts": ts, "total": total})
# prune to ~60 days to keep file small
cutoff = now - 60*24*3600
hist = [r for r in hist if isinstance(r,dict) and r.get("ts",0)>=cutoff]

def window_delta(hist, horizon_sec):
    """delta and pct over the given horizon using earliest record >= now-horizon"""
    if not hist: return None
    ref_ts = now - horizon_sec
    # find earliest record with ts >= ref_ts; if none, use earliest available
    hist_sorted = sorted(hist, key=lambda r: r.get("ts",0))
    base = None
    for r in hist_sorted:
        if r.get("ts",0) >= ref_ts:
            base = r; break
    if base is None: base = hist_sorted[0]
    base_total = base.get("total")
    if base_total is None: return None
    d = total - base_total
    pct = (d/base_total)*100.0 if base_total>0 else None
    return {"since_ts": base.get("ts"), "delta": d, "pct": pct}

delta_since_last = None
if isinstance(last_total,(int,float)):
    d = total - float(last_total)
    pct = (d/last_total*100.0) if last_total>0 else None
    delta_since_last = {"delta": d, "pct": pct, "since_ts": last_ts}

d24 = window_delta(hist, 24*3600)
d7d = window_delta(hist, 7*24*3600)

summary = {
    "ts": now,
    "total_usd": total,
    "delta_since_last": delta_since_last,
    "delta_24h": d24,
    "delta_7d": d7d,
}

# persist
with open(HIST,"w",encoding="utf-8") as f: json.dump(hist, f, indent=2)
with open(SUMM,"w",encoding="utf-8") as f: json.dump(summary, f, indent=2)
with open(STATE,"w",encoding="utf-8") as f: json.dump({"last_total": total, "last_ts": now}, f, indent=2)
