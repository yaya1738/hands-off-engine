#!/data/data/com.termux/files/usr/bin/python
import os, sys, json, time, datetime, pathlib, traceback, re
import requests
from pytz import UTC

BASE   = os.path.expanduser("~/hands-off")
STATE  = os.path.join(BASE, "state")
OUT    = os.path.join(BASE, "out")
TG_ENV = os.path.join(STATE, "tg/bots/handsoff.env")

def now_utc_iso():
    return datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def save_json(path, data):
    tmp = path + ".tmp"
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def load_json_lenient(path, default, *, allow_comments=True):
    """
    Loads JSON, optionally stripping // and /* */ comments.
    Returns (data, warn) where warn is None or a string like 'stripped_comments' or 'json_error:...'.
    """
    try:
        raw = open(path, "r", encoding="utf-8").read()
    except Exception:
        return default, f"missing:{path}"
    warn = None
    txt = raw
    if allow_comments:
        # strip /* ... */ then // ... (but not inside "key://value")
        no_block = re.sub(r"/\*.*?\*/", "", txt, flags=re.DOTALL)
        # remove // comments only when not following a colon in the same token
        no_line  = re.sub(r"(^|[^:])//.*?$", r"\1", no_block, flags=re.MULTILINE)
        if no_line != txt:
            warn = "stripped_comments"
        txt = no_line
    try:
        return json.loads(txt), warn
    except Exception as e:
        return default, f"json_error:{path}:{e}"

def load_tg():
    token, chat_id = None, None
    if os.path.isfile(TG_ENV):
        for line in open(TG_ENV, "r", encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#"): continue
            if "=" not in line: continue
            k,v = line.split("=",1)
            if k=="TOKEN": token=v.strip()
            if k=="CHAT_ID": chat_id=v.strip()
    return token, chat_id

def tg_send(token, chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
    except Exception:
        pass

# ---------- Providers ----------
def coingecko_prices(coins):
    if not coins: return {}
    ids = ",".join(coins)
    url = "https://api.coingecko.com/api/v3/simple/price"
    try:
        r = requests.get(url, params={"ids": ids, "vs_currencies":"usd"}, timeout=15)
        if r.ok: return r.json()
    except Exception as e:
        return {"error": str(e)}
    return {}

def fx_rate(base="USD", quote="ILS"):
    try:
        r = requests.get("https://api.exchangerate.host/latest", params={"base": base, "symbols": quote}, timeout=15)
        if r.ok:
            j = r.json()
            return j.get("rates", {}).get(quote)
    except Exception:
        return None
    return None

def polymarket_fetch(queries):
    """
    Robust public Polymarket fetcher using endpoints that work unauthenticated:
      - /public-search?q=term (prefer)
      - /markets/slug/{slug} (if string looks like a market slug)
      - fallback: /markets?slug=<slug>
    Returns a flat list of markets plus writes ~/hands-off/out/pm-debug.json
    """
    BASE = "https://gamma-api.polymarket.com"
    sess = requests.Session()
    sess.headers.update({
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 15; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129 Mobile Safari/537.36",
        "Origin": "https://polymarket.com",
        "Referer": "https://polymarket.com/"
    })

    def GET(url, params=None, timeout=20):
        rec = {"url": url, "params": params, "status": None, "err": None}
        try:
            r = sess.get(url, params=params, timeout=timeout)
            rec["status"] = r.status_code
            if r.ok:
                try:
                    return r.json(), rec
                except Exception as e:
                    rec["err"] = f"json:{e}"
                    return None, rec
            else:
                return None, rec
        except Exception as e:
            rec["err"] = str(e)
            return None, rec

    tried = []
    out = []

    for q in (queries or []):
        q = (q or "").strip()
        if not q: continue
        looks_slug = (" " not in q) and ("-" in q) and (len(q) > 8)

        markets = []

        # First try search (best coverage)
        js, rec = GET(f"{BASE}/public-search", params={"q": q, "limit_per_type": 3, "optimized": True})
        tried.append(rec)
        if isinstance(js, dict):
            evs = js.get("events") or []
            if evs:
                # take first event; many payloads include markets directly
                ev = evs[0]
                mk = ev.get("markets") or []
                if isinstance(mk, list) and mk:
                    markets = mk

        # If no markets yet and it looks like a slug, try market-by-slug then markets?slug=
        if not markets and looks_slug:
            js2, rec2 = GET(f"{BASE}/markets/slug/{q}")
            tried.append(rec2)
            if isinstance(js2, dict) and js2.get("id"):
                markets = [js2]
            if not markets:
                js3, rec3 = GET(f"{BASE}/markets", params={"slug": q, "closed": False})
                tried.append(rec3)
                if isinstance(js3, list) and js3:
                    markets = js3

        if not markets:
            out.append({"query": q, "error": "no_results"})
            continue

        for m in markets:
            out.append({
                "query": q,
                "id": m.get("id"),
                "slug": m.get("slug"),
                "question": m.get("question") or m.get("title") or m.get("name"),
                "bestBid": m.get("bestBid"),
                "bestAsk": m.get("bestAsk"),
                "lastTradePrice": m.get("lastTradePrice") or m.get("lastPrice"),
                "closed": m.get("closed"),
                "active": m.get("active"),
                "endDate": m.get("endDate") or m.get("closeTime") or m.get("close_time")
            })

    # persist debug
    debug = {"tried": tried, "hits": len([x for x in out if "error" not in x])}
    try:
        save_json(os.path.join(OUT, "pm-debug.json"), debug)
    except Exception:
        pass

    return out, debug

def summarize_pm(markets):
    if not markets:
        return "• Polymarket: no results"
    lines=[]
    for m in markets[:8]:
        if "error" in m:
            lines.append(f"• {m.get('query')}: error {m['error']}")
            continue
        q = (m.get("question") or m.get("slug") or m.get("query") or "")[:84]
        price = m.get("bestBid")
        if price is None: price = m.get("lastTradePrice")
        if isinstance(price, (int,float)):
            lines.append(f"• {q} → ~ {price:.2f}")
        else:
            lines.append(f"• {q} → price n/a")
    return "\n".join(lines)

# ---------- Main ----------
def main():
    t0 = time.time()
    ts = now_utc_iso()

    wl_pm, warn_pm     = load_json_lenient(os.path.join(STATE,"watchlist_polymarket.json"), {"markets":[]})
    wl_coin, warn_coin = load_json_lenient(os.path.join(STATE,"watchlist_coins.json"), {"coins":[]})

    result = {
        "timestamp": ts,
        "providers": {},
        "meta": {"runtime_sec": None, "warnings": []}
    }

    # Polymarket
    try:
        pm_markets, pm_debug = polymarket_fetch(wl_pm.get("markets", []))
        result["providers"]["polymarket"] = {
            "ok": True, "count": len(pm_markets), "data": pm_markets, "debug": pm_debug
        }
    except Exception:
        result["providers"]["polymarket"] = {"ok": False, "error": traceback.format_exc()}

    # CoinGecko
    try:
        cg = coingecko_prices(wl_coin.get("coins", []))
        result["providers"]["coingecko"] = {"ok": True, "data": cg}
    except Exception:
        result["providers"]["coingecko"] = {"ok": False, "error": traceback.format_exc()}

    # FX
    try:
        usdils = fx_rate("USD","ILS")
        result["providers"]["fx"] = {"ok": usdils is not None, "USDILS": usdils}
    except Exception:
        result["providers"]["fx"] = {"ok": False, "error": traceback.format_exc()}

    # meta
    result["meta"]["runtime_sec"] = round(time.time()-t0, 3)
    if warn_pm:   result["meta"]["warnings"].append({"watchlist_polymarket.json": warn_pm})
    if warn_coin: result["meta"]["warnings"].append({"watchlist_coins.json": warn_coin})

    # write outputs
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%MZ")
    save_json(os.path.join(OUT, f"fetch-{stamp}.json"), result)
    save_json(os.path.join(OUT, "fetch-latest.json"), result)

    # Telegram summary (optional)
    tok, cid = load_tg()
    if tok and cid:
        lines = [f"Fetch @ {ts}"]
        if result["meta"]["warnings"]:
            issues = ", ".join([list(w.keys())[0]+":"+list(w.values())[0] for w in result["meta"]["warnings"]])
            lines.append(f"⚠️ watchlist issues: {issues}")
        pm = result.get("providers",{}).get("polymarket",{})
        if pm.get("count"):
            lines.append(summarize_pm(pm.get("data",[])))
        cg = result.get("providers",{}).get("coingecko",{}).get("data",{})
        if isinstance(cg, dict) and cg:
            flat = ", ".join([f"{k}: ${v.get('usd')}" for k,v in cg.items() if isinstance(v, dict) and 'usd' in v])
            if flat: lines.append(f"Spot: {flat}")
        fx = result.get("providers",{}).get("fx",{}).get("USDILS")
        if fx is not None:
            lines.append(f"USD/ILS: {fx}")
        tg_send(tok, cid, "\n".join(lines))

if __name__ == "__main__":
    main()
