#!/usr/bin/env python3
import os, json, time, hmac, hashlib, base64, datetime, sys
from pathlib import Path
from urllib.parse import urlencode
import requests

HOME = Path.home()
LOG_DIR = HOME / "hands-off" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
RULES = json.load(open(HOME/"hands-off"/"agents"/"finance_rules.json"))
EXTERNAL_FILE = HOME/"hands-off"/"agents"/"external_accounts.json"
VAULT_CANDIDATES = [
    HOME/"hands-off"/"vault.json",
    HOME/".config"/"hands-off"/"vault.json"
]
VAULT = next((p for p in VAULT_CANDIDATES if p.exists()), None)

def now_utc_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

def termux_notify(title, text):
    # Local phone notification if Termux:API is installed; otherwise no-op
    try:
        os.system(f'termux-notification --title "{title}" --content "{text}" >/dev/null 2>&1')
    except Exception:
        pass

def log_line(fname, data):
    with open(LOG_DIR/fname, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_utc_iso(), **data})+"\n")

def okx_headers(method, path, body, api_key, secret, passphrase):
    ts = datetime.datetime.utcnow().isoformat(timespec='milliseconds')+'Z'
    prehash = f"{ts}{method}{path}{(body or '')}"
    sign = base64.b64encode(hmac.new(secret.encode(), prehash.encode(), hashlib.sha256).digest()).decode()
    return {
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json"
    }

def get_okx_ticker(symbol):
    # symbol like BTC-USDT
    url = "https://www.okx.com/api/v5/market/ticker"
    r = requests.get(url, params={"instId": symbol}, timeout=10)
    r.raise_for_status()
    d = r.json()
    if d.get("code") == "0" and d.get("data"):
        px = float(d["data"][0]["last"])
        return px
    raise RuntimeError(f"OKX ticker error: {d}")

def get_okx_balances(vault):
    if not vault: return {}
    ak = vault.get("OKX_API_KEY")
    sk = vault.get("OKX_API_SECRET")
    pp = vault.get("OKX_API_PASSPHRASE")
    if not (ak and sk and pp): return {}
    p = "/api/v5/account/balance"
    url = "https://www.okx.com"+p
    h = okx_headers("GET", p, "", ak, sk, pp)
    r = requests.get(url, headers=h, timeout=15)
    if r.status_code == 401: return {"_auth_error":"OKX unauthorized"}
    r.raise_for_status()
    d = r.json()
    out = {}
    for data in d.get("data", []):
        for d2 in data.get("details", []):
            ccy = d2["ccy"]
            tot = float(d2.get("cashBal", d2.get("eq","0")))
            if tot: out[ccy] = out.get(ccy, 0.0) + tot
    return out

def kraken_sign(path, data, secret):
    postdata = urlencode(data)
    encoded = (str(data.get('nonce')) + postdata).encode()
    message = path.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest())

def get_kraken_balances(vault):
    if not vault: return {}
    ak = vault.get("KRAKEN_API_KEY")
    sk = vault.get("KRAKEN_API_SECRET")
    if not (ak and sk): return {}
    url = "https://api.kraken.com/0/private/Balance"
    nonce = int(time.time()*1000)
    data = {"nonce": nonce}
    headers = {
        "API-Key": ak,
        "API-Sign": kraken_sign("/0/private/Balance", data, sk)
    }
    r = requests.post(url, headers=headers, data=data, timeout=15)
    if r.status_code == 401: return {"_auth_error":"Kraken unauthorized"}
    r.raise_for_status()
    d = r.json()
    if d.get("error"):
        return {"_auth_error": ";".join(d["error"])}
    # returns dict of assets and balances (strings)
    out = {}
    for k,v in d.get("result", {}).items():
        try:
            fv = float(v)
            if fv: out[k] = out.get(k,0.0)+fv
        except: pass
    return out

def load_external_accounts():
    try:
        import json
        p = EXTERNAL_FILE
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            # normalize keys; liabilities are negative
            out = {}
            for k,v in d.items():
                try:
                    out[k] = float(v)
                except:
                    pass
            return out
    except Exception:
        pass
    return {}

def load_vault():
    if not VAULT: return {}
    try:
        with open(VAULT, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {}

def portfolio_snapshot(vault):
    snap = {"by_asset": {}, "prices": {}}
    # normalize symbols to pull prices
    for sym in RULES["symbols"]:
        try:
            px = get_okx_ticker(sym)
            snap["prices"][sym] = px
        except Exception as e:
            log_line("finance_errors.log", {"source":"okx_ticker", "symbol": sym, "error": str(e)})

    okx = get_okx_balances(vault)
    krk = get_kraken_balances(vault)

    def add(ccy, amt):
        if amt:
            snap["by_asset"][ccy] = snap["by_asset"].get(ccy, 0.0) + float(amt)

    for ccy, amt in okx.items(): add(ccy, amt)
    for ccy, amt in krk.items(): add(ccy, amt)

    # rough USD valuation using USDT prices from OKX
    usd_total = 0.0
    for ccy, amt in snap["by_asset"].items():
        if ccy.upper() in ("USD","USDT","USDC","ZUSD"): usd_total += amt
        else:
            pair = f"{ccy.upper()}-USDT"
            px = snap["prices"].get(pair)
            if px: usd_total += amt * px
    # External accounts support (manual balances, liabilities negative)
    ext = load_external_accounts()
    ext_total = sum(ext.values()) if isinstance(ext, dict) else 0.0
    snap["external"] = ext

    usd_total_raw = usd_total + ext_total
    snap["usd_total_raw"] = usd_total_raw
    snap["usd_total"] = round(usd_total_raw, 2)
    return snap

def check_alerts(prices):
    hits = []
    for rule in RULES.get("alerts", []):
        sym = rule["symbol"]
        px = prices.get(sym)
        if px is None: continue
        if "above" in rule and px >= rule["above"]:
            hits.append(f"{sym} ≥ {rule['above']}, now {px}")
        if "below" in rule and px <= rule["below"]:
            hits.append(f"{sym} ≤ {rule['below']}, now {px}")
    return hits

def main():
    vault = load_vault()
    if not vault:
        log_line("finance_events.log", {"event":"vault_missing"})
    last_usd = None
    while True:
        try:
            snap = portfolio_snapshot(vault)
            log_line("finance_balances.log", snap)
            hits = check_alerts(snap.get("prices", {}))
            if hits:
                msg = " / ".join(hits)
                termux_notify("Price Alert", msg)
                log_line("finance_alerts.log", {"alerts": hits})
            if last_usd is not None and snap.get("usd_total") is not None:
                delta = round(snap["usd_total"] - last_usd, 2)
                if abs(delta) >= 50:  # only log noticeable moves
                    log_line("finance_pnl.log", {"usd_total": snap["usd_total"], "delta": delta})
            last_usd = snap.get("usd_total", last_usd)
        except Exception as e:
            log_line("finance_errors.log", {"error": str(e)})
        time.sleep(max(15, int(RULES.get("poll_seconds", 45))))

if __name__ == "__main__":
    main()
