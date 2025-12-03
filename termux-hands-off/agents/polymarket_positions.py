#!/usr/bin/env python3
import os, json, time, pathlib, csv, re
from typing import List, Dict, Any
import requests

HOME = pathlib.Path.home()
EXT  = HOME/"hands-off"/"agents"/"external_accounts.json"
JLOG = HOME/"hands-off"/"logs"/"polymarket_positions.jsonl"
CSVF = HOME/"hands-off"/"logs"/"polymarket_positions.csv"
PULL = HOME/"hands-off"/"logs"/"polymarket_pull.log"  # for context

def nowz():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def http_get(url, params=None, headers=None, timeout=15):
    r = requests.get(url, params=params, headers=headers or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()

def load_wallet():
    d = json.loads(EXT.read_text()) if EXT.exists() else {}
    w = (d.get("polymarket_wallet") or "").strip()
    u = (d.get("polymarket_username") or "").strip()
    if w: return w
    # fall back: try to resolve via username like the other puller
    for url in ["https://gamma-api.polymarket.com/user","https://api.polymarket.com/user"]:
        try:
            if not u: break
            j = http_get(url, {"username": u})
            for k in ("address","wallet","publicAddress","ownerAddress"):
                a = j.get(k) if isinstance(j, dict) else None
                if a and re.match(r"^0x[a-fA-F0-9]{40}$", a): return a
        except Exception:
            pass
    return None

def fetch_positions(wallet) -> List[Dict[str,Any]]:
    trials = [
        ("https://gamma-api.polymarket.com/positions", {"address": wallet, "limit": 2000}),
        ("https://api.polymarket.com/positions",       {"address": wallet, "limit": 2000}),
        ("https://gamma-api.polymarket.com/portfolio", {"address": wallet}),  # sometimes has embedded positions
    ]
    for url, params in trials:
        try:
            j = http_get(url, params=params)
            # normalize to list of dicts with price & qty
            out = []
            cand = []
            if isinstance(j, dict):
                if isinstance(j.get("positions"), list):
                    cand = j["positions"]
                elif isinstance(j.get("data"), list):
                    cand = j["data"]
            elif isinstance(j, list):
                cand = j
            for pos in cand:
                # generic fields across various versions
                market = pos.get("market") or pos.get("question") or pos.get("marketTitle") or ""
                outcome = pos.get("outcome") or pos.get("outcomeName") or pos.get("side") or ""
                qty = pos.get("quantity") or pos.get("qty") or pos.get("shares") or 0
                price = (
                    pos.get("markPrice") or pos.get("price") or pos.get("avgPrice")
                    or pos.get("valuePerShare") or pos.get("mark") or 0
                )
                # fallback: if value given but not price, derive
                value = pos.get("value") or pos.get("markValue") or pos.get("notionalValue") or pos.get("equity")
                try:
                    qty = float(qty)
                except: qty = 0.0
                try:
                    price = float(price)
                except:
                    if value is not None:
                        try:
                            price = float(value) / qty if qty else 0.0
                        except: price = 0.0
                    else:
                        price = 0.0
                if value is None:
                    value = qty * price
                else:
                    try: value = float(value)
                    except: value = qty * price

                # capture ids if present
                mid = pos.get("marketId") or pos.get("market_id") or pos.get("id") or ""
                oid = pos.get("outcomeId") or pos.get("outcome_id") or ""

                out.append({
                    "ts": nowz(),
                    "market": str(market),
                    "outcome": str(outcome),
                    "market_id": str(mid),
                    "outcome_id": str(oid),
                    "quantity": qty,
                    "price": round(price, 6),
                    "value": round(value, 2),
                })
            if out:
                return out
        except Exception:
            # try next endpoint
            pass
    return []

def write_jsonl(rows: List[Dict[str,Any]]):
    JLOG.parent.mkdir(parents=True, exist_ok=True)
    with open(JLOG, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r)+"\n")

def write_csv(rows: List[Dict[str,Any]]):
    CSVF.parent.mkdir(parents=True, exist_ok=True)
    hdr = ["ts","market","outcome","market_id","outcome_id","quantity","price","value"]
    newfile = not CSVF.exists()
    with open(CSVF, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        if newfile: w.writeheader()
        for r in rows: w.writerow({k:r.get(k) for k in hdr})

def main():
    wallet = load_wallet()
    if not wallet:
        print("[i] No wallet/username set. Aborting.")
        return
    rows = fetch_positions(wallet)
    mark_sum = round(sum(r["value"] for r in rows), 2) if rows else 0.0

    # write logs
    if rows:
        write_jsonl(rows)
        write_csv(rows)

    # update external_accounts with mark + unrealized est
    d = json.loads(EXT.read_text()) if EXT.exists() else {}
    d["polymarket_positions_mark"] = mark_sum
    cost = float(d.get("polymarket_cost_basis", 0.0) or 0.0)
    d["polymarket_unrealized_est"] = round(mark_sum - cost, 2)
    EXT.write_text(json.dumps(d, indent=2), encoding="utf-8")

    # console summary
    print(json.dumps({
        "wallet": wallet,
        "positions_found": len(rows),
        "mark_sum": mark_sum,
        "cost_basis": cost,
        "unrealized_est": round(mark_sum - cost, 2)
    }, indent=2))

if __name__ == "__main__":
    main()
