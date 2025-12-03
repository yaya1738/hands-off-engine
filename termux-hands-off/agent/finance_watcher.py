#!/data/data/com.termux/files/usr/bin/python
import os, json, time, math, requests, traceback

BASE   = os.path.expanduser("~/hands-off")
STATE  = f"{BASE}/state"
AGENT  = f"{BASE}/agent"
LOGDIR = os.path.expanduser("~/.cron-logs")

TG_ENV   = f"{STATE}/tg/bots/handsoff.env"          # expects TOKEN=… and CHAT_ID=…
IFTTTENV = f"{STATE}/auto_sources.env"              # expects IFTTT_WEBHOOK=…
PREV     = f"{STATE}/finance_prev.json"

# Try multiple locations for polymarket compact file
PM_CANDIDATES = [
    f"{STATE}/polymarket-compact.json",
    f"{AGENT}/polymarket-compact.json",
    f"{STATE}/polymarket_compact.json"
]

WC_PATH  = f"{STATE}/watchlist_coins.json"          # optional (ids to watch)
CH_PATH  = f"{STATE}/crypto_holdings.json"          # optional (id->amount)
FA_PATH  = f"{STATE}/fiat_accounts.json"            # optional (name->usd)

def load_env(path):
    d={}
    if os.path.exists(path):
        for line in open(path, 'r', encoding='utf-8'):
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            k,v = line.split('=',1)
            d[k.strip()] = v.strip()
    return d

def load_json(path):
    try:
        if os.path.exists(path):
            return json.load(open(path, 'r', encoding='utf-8'))
    except Exception:
        pass
    return None

def find_pm_compact():
    for p in PM_CANDIDATES:
        if os.path.exists(p): return p
    return None

def get_coingecko_prices(ids):
    if not ids: return {}
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(ids), "vs_currencies": "usd"}
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

def money(x):
    try:
        return f"${x:,.2f}"
    except Exception:
        return "-"

def calc_snapshot():
    snap = {
        "ts": int(time.time()),
        "components": {},
        "notes": []
    }

    # --- Polymarket (cash + mark) ---
    pm_file = find_pm_compact()
    if pm_file:
        try:
            pm = load_json(pm_file) or {}
            # Try common keys; fall back to zero if not present
            cash = pm.get("cash_usd") or pm.get("cashUSD") or 0.0
            mark = pm.get("mark_value_usd") or pm.get("markUSD") or 0.0
            snap["components"]["polymarket_cash_usd"] = float(cash)
            snap["components"]["polymarket_mark_usd"] = float(mark)
        except Exception:
            snap["notes"].append("Polymarket file present but parse failed")
    else:
        snap["notes"].append("Polymarket compact not found")

    # --- Fiat accounts (static json you can edit any time) ---
    fiat = load_json(FA_PATH) or {}
    for k,v in fiat.items():
        try:
            snap["components"][k] = float(v)
        except Exception:
            pass

    # --- Crypto holdings (id->amount) + prices ---
    holdings = load_json(CH_PATH) or {}
    if holdings:
        ids = sorted(set(holdings.keys()))
        prices = get_coingecko_prices(ids)
        crypto_total = 0.0
        for cid, amt in holdings.items():
            try:
                amt = float(amt)
                px  = float(prices.get(cid, {}).get("usd", 0.0))
                val = amt * px
                snap["components"][f"crypto_{cid}_usd"] = val
                crypto_total += val
            except Exception:
                continue
        snap["components"]["crypto_total_usd"] = crypto_total
    else:
        snap["notes"].append("crypto_holdings.json missing or empty")

    # --- Sum up ---
    net = sum([v for v in snap["components"].values() if isinstance(v,(int,float)) and not math.isnan(v)])
    snap["net_usd"] = net
    return snap

def diff(prev, curr):
    if not prev: 
        return {"net_delta": None, "components": {}}
    dd = {"net_delta": (curr.get("net_usd") or 0) - (prev.get("net_usd") or 0), "components": {}}
    pc = prev.get("components", {})
    cc = curr.get("components", {})
    keys = set(pc.keys()) | set(cc.keys())
    for k in keys:
        dd["components"][k] = (cc.get(k,0.0) or 0.0) - (pc.get(k,0.0) or 0.0)
    return dd

def send_telegram(text, env):
    tok = env.get("TOKEN"); chat = env.get("CHAT_ID")
    if not tok or not chat: return
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat, "text": text}, timeout=10)
    except Exception:
        pass

def send_ifttt(text, env):
    hook = env.get("IFTTT_WEBHOOK")
    if not hook: return
    payload = {"value1": "finance_watcher", "value2": text, "value3": ""}
    try:
        requests.post(hook, json=payload, timeout=10)
    except Exception:
        pass

def build_summary(curr, delta):
    lines = []
    lines.append("💹 Finance watcher — " + time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(curr["ts"])))
    lines.append(f"Net: {money(curr.get('net_usd') or 0.0)}" + ("" if delta["net_delta"] is None else f"  (Δ {money(delta['net_delta'])})"))
    # Top components (sorted by absolute size, show up to 6)
    comps = curr.get("components", {})
    top = sorted(comps.items(), key=lambda kv: abs(kv[1]), reverse=True)[:6]
    for k,v in top:
        d = delta["components"].get(k)
        delta_str = "" if d is None else f" (Δ {money(d)})"
        lines.append(f"- {k}: {money(v)}{delta_str}")
    if curr.get("notes"):
        lines.append("")
        for n in curr["notes"]:
            lines.append(f"note: {n}")
    return "\n".join(lines)

def main():
    os.makedirs(LOGDIR, exist_ok=True)
    prev = load_json(PREV)

    curr = calc_snapshot()
    delta = diff(prev, curr)
    text  = build_summary(curr, delta)

    # Save snapshot before push (so we never double-count if push fails)
    with open(PREV, "w", encoding="utf-8") as f:
        json.dump(curr, f, indent=2)

    # Send to Telegram + IFTTT
    tgenv = load_env(TG_ENV)
    ifttt = load_env(IFTTTENV)
    send_telegram(text, tgenv)
    send_ifttt(text, ifttt)

    # Also append a local log
    with open(f"{LOGDIR}/finance.log", "a", encoding="utf-8") as f:
        f.write(text + "\n\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open(f"{LOGDIR}/finance.log", "a", encoding="utf-8") as f:
            f.write("[error] " + repr(e) + "\n" + traceback.format_exc() + "\n")
        raise
