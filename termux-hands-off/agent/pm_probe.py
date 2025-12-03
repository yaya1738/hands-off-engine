#!/data/data/com.termux/files/usr/bin/python
import os, json, requests, time

BASE = "https://gamma-api.polymarket.com"
OUT  = os.path.expanduser("~/hands-off/out")
WL   = os.path.expanduser("~/hands-off/state/watchlist_polymarket.json")

def load_watchlist():
    try:
        with open(WL, "r", encoding="utf-8") as f:
            j = json.load(f)
            return j.get("markets", [])
    except Exception:
        return []

def try_get(sess, url, params=None, timeout=20):
    rec = {"url": url, "params": params, "status": None, "body_head": None, "err": None}
    try:
        r = sess.get(url, params=params, timeout=timeout)
        rec["status"] = r.status_code
        head = r.text[:600] if isinstance(r.text, str) else str(r.content)[:600]
        rec["body_head"] = head
    except Exception as e:
        rec["err"] = str(e)
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    queries = load_watchlist() or ["bitcoin","ethereum","trump","israel","nba"]

    sess = requests.Session()
    sess.headers.update({
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 15; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129 Mobile Safari/537.36",
        "Origin": "https://polymarket.com",
        "Referer": "https://polymarket.com/"
    })

    tried = []
    for q in queries:
        q = (q or "").strip()
        if not q: 
            continue
        looks_slug = (" " not in q) and ("-" in q) and (len(q) > 8)

        if looks_slug:
            # market-by-slug
            tried.append(try_get(sess, f"{BASE}/markets/slug/{q}"))
            # event-by-slug
            tried.append(try_get(sess, f"{BASE}/events/slug/{q}"))
            # markets?slug=
            tried.append(try_get(sess, f"{BASE}/markets", params={"slug": q, "closed": False}))
        else:
            # public-search
            tried.append(try_get(sess, f"{BASE}/public-search", params={"q": q, "limit_per_type": 3, "optimized": True}))
            # legacy search fallback
            tried.append(try_get(sess, f"{BASE}/search", params={"q": q, "limit_per_type": 3, "optimized": True}))

    out = {
        "ts": int(time.time()),
        "queries": queries,
        "tried": tried
    }
    with open(os.path.join(OUT,"pm-probe.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
