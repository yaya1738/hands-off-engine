#!/usr/bin/env python3
import json, os, time
from pathlib import Path

BASE = Path(os.environ["HOME"]) / "hands-off"
STATE = BASE / "state"
OUT   = BASE / "out"

LEDGER = STATE / "pnl_ledger.json"

def load(name):
    p = OUT / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except:
        return None

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)

    data = {}
    for key in ["finance.json", "decision_report.json", "fetch-latest.json"]:
        val = load(key)
        if val is not None:
            data[key] = val

    ts = int(time.time())

    if LEDGER.exists():
        try:
            hist = json.loads(LEDGER.read_text())
        except:
            hist = []
    else:
        hist = []

    hist.append({"ts": ts, "data": data})
    LEDGER.write_text(json.dumps(hist, indent=2))

    print("[ok] pnl_logger wrote entry", ts)

if __name__ == "__main__":
    main()
