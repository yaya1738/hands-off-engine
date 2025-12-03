#!/usr/bin/env python3
import json, pathlib, os, subprocess

HOME = pathlib.Path.home()
CARDS = HOME/"hands-off/agents/cards.json"
PERFI = HOME/"hands-off/agents/perf_inputs.json"

def ask_float(prompt, default):
    try:
        v = input(f"{prompt} [{default}]: ").strip()
        return float(default) if v=="" else float(v)
    except:
        return float(default)

def quick_cards():
    d = json.loads(CARDS.read_text()) if CARDS.exists() else {}
    print("\n[Cards quick update] (press Enter to keep current)")
    for k,v in d.items():
        cur = v.get("balance",0.0)
        nb  = ask_float(f"{v.get('name',k)} balance", cur)
        v["balance"] = nb
    CARDS.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print("[ok] cards updated")

def quick_pnl():
    d = json.loads(PERFI.read_text()) if PERFI.exists() else {"polymarket_pnl":0.0,"robinhood_pnl":0.0,"notes":""}
    print("\n[Daily P&L] (Enter = keep)")
    d["polymarket_pnl"] = ask_float("Polymarket P&L", d.get("polymarket_pnl",0.0))
    d["robinhood_pnl"]  = ask_float("Robinhood P&L", d.get("robinhood_pnl",0.0))
    n = input("Notes ["+d.get("notes","")+"]: ").strip()
    if n!="": d["notes"]=n
    PERFI.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print("[ok] P&L staged")

def run(cmd):
    return subprocess.call(cmd, shell=True)

def main():
    quick_cards()
    quick_pnl()
    # run trackers
    run(f'python "{HOME}/hands-off/agents/credit_utilization.py"')
    run(f'python "{HOME}/hands-off/agents/perf_logger.py"')
    run(f'python "{HOME}/hands-off/agents/weekly_summary.py"')
    print("[done] trackers refreshed")

if __name__=="__main__":
    main()
