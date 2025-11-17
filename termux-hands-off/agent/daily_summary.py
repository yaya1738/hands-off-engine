#!/usr/bin/env python3
import os, json, glob, subprocess

REG = os.path.expanduser("~/hands-off/state/balances.d")
NOTIFY = os.path.expanduser("~/hands-off/agent/notify.py")

def load():
    parts, total = [], 0.0
    for p in sorted(glob.glob(os.path.join(REG,"*.json"))):
        try:
            d=json.load(open(p))
            name=d.get("name") or os.path.splitext(os.path.basename(p))[0]
            amt=float(d.get("balance_usd",0.0))
            parts.append((name,amt)); total+=amt
        except: pass
    return parts, total

if __name__=="__main__":
    parts, total = load()
    if not parts:
        msg = "📊 Daily Summary: (no sources yet)"
    else:
        lines = "\n".join([f"• {n}: ${a:,.2f}" for n,a in parts])
        msg = f"📊 Daily Summary\nTotal: ${total:,.2f}\n\n{lines}"
    subprocess.run(["python", NOTIFY, msg], check=False)
