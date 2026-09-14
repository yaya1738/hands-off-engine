import os, sys, json, time, re, urllib.request
import json

BASE = os.path.expanduser("~/hands-off/autopilot")
WATCHLIST_FILE = os.path.join(BASE, "watchlist.txt")
CAND_FILE = os.path.join(BASE, "candidates.jsonl")

# Map keywords -> your prior keys so the engine can match priors
KEYMAP = {
    r"\bbitcoin\b": "bitcoin above",
    r"\boil\b": "oil above",
    r"\bceltics\b": "celtics win",
    r"\blakers\b": "lakers win",
    r"\belection\b|\btrump\b|\bbiden\b": "trump",  # collapse to one prior key (tweak as you like)
    r"\binflation\b": "inflation",
    r"\bfed\b.*(rate|cut|hike)": "fed rate cut",
    r"\bnba\b": "nba",  # generic fallback
}

def load_watchlist():
    try:
        with open(WATCHLIST_FILE, "r") as f:
            words = [w.strip().lower() for w in f if w.strip()]
        return words
    except FileNotFoundError:
        return ["bitcoin","oil","election","nba","inflation"]

def choose_key(title: str):
    t = title.lower()
    for pat, key in KEYMAP.items():
        if re.search(pat, t):
            return key
    # fallback: first word-ish
    return t.split()[:2] and " ".join(t.split()[:2]) or t

def get_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent":"edge-autopilot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def price_to_prob(outcomes, outcome_prices):
    if not outcome_prices:
        return None
    try:
        prices = [float(x) for x in outcome_prices]
    except Exception:
        return None

    p_yes = None
    if outcomes and isinstance(outcomes, list) and len(outcomes) == len(prices):
        for i, o in enumerate(outcomes):
            if isinstance(o, str) and o.strip().lower() in ("yes","over","team a","home","buy yes"):
                p_yes = prices[i]; break
    if p_yes is None:
        # use the max-priced side as implied favorite
        p_yes = max(prices)

    # optional renorm if it's obviously a 2-outcome market
    if len(prices) == 2:
        total = prices[0] + prices[1]
        if 0.95 <= total <= 1.05:
            # assume they're complementary and p_yes already reflects the side to act on
            pass

    return max(0.0, min(1.0, p_yes))

def main():
    watch = load_watchlist()
    # Pull events (Gamma API)
    # Docs: https://gamma-api.polymarket.com/events  (see Polymarket docs)
    # Fetches first page of events. Pagination available if needed for broader coverage.
    url = "https://gamma-api.polymarket.com/events"
    try:
        events = get_json(url)
    except Exception as e:
        print(f"[fetch] error fetching events: {e}", file=sys.stderr)
        sys.exit(0)

    # Build candidate lines
    lines = []
    wanted = [w.lower() for w in watch]
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for ev in events if isinstance(events, list) else []:
        title = ev.get("title") or ev.get("ticker") or ev.get("slug") or ""
        if not title:
            continue
        # quick keyword gate
        t_low = title.lower()
        if not any(w in t_low for w in wanted):
            # also scan tags if present
            tag_hit = False
            for tag in (ev.get("tags") or []):
                lab = (tag.get("label") or "").lower()
                if any(w in lab for w in wanted):
                    tag_hit = True
                    break
            if not tag_hit:
                continue

        markets = ev.get("markets") or []
        for m in markets:
            q = m.get("question") or title
            outcomes = m.get("outcomes")
            # Some docs show 'shortOutcomes' too; prefer 'outcomes' if present.
            outcome_prices = m.get("outcomePrices")
            p_mkt = price_to_prob(outcomes, outcome_prices)
            if p_mkt is None:
                continue

            # normalize a candidate key that maps to your priors
            key = choose_key(f"{title} {q}")
            note = f"{title} | {q}"
            lines.append({
                "key": key,
                "p_fair": None,        # engine will fallback to priors.json for fair
                "p_mkt": round(float(p_mkt), 3),
                "note": note,
                "t": now_iso,
            })

    if not lines:
        print("[fetch] no candidates found for current watchlist")
        return

    # write/append: we will refresh candidates.jsonl (overwrite to keep it clean)
    tmp = CAND_FILE + ".tmp"
    with open(tmp, 'w') as f:
        for x in dedup:
            f.write(x + "\n")
    os.replace(tmp, CAND_FILE)
    print(f"[fetch] wrote {len(lines)} candidates to {CAND_FILE}")
if __name__ == "__main__":
    if "--debug" in sys.argv:
        # lightweight debug pass
        try:
            events = get_json("https://gamma-api.polymarket.com/events")
        except Exception as e:
            print(f"[fetch] error fetching events: {e}", file=sys.stderr)
            sys.exit(0)

        watch = load_watchlist()
        wanted = [w.lower() for w in watch]
        shown = 0
        for ev in events if isinstance(events, list) else []:
            title = ev.get("title") or ev.get("ticker") or ev.get("slug") or ""
            t_low = title.lower()
            hit = any(w in t_low for w in wanted)
            if not hit:
                for tag in (ev.get("tags") or []):
                    lab = (tag.get("label") or "").lower()
                    if any(w in lab for w in wanted):
                        hit = True
                        break
            if not hit:
                continue
            for m in (ev.get("markets") or []):
                prices = m.get("outcomePrices")
                q = m.get("question") or title
                print(f"[match] {title} | {q} | prices={prices}")
                shown += 1
                if shown >= 20:
                    break
            if shown >= 20:
                break
        sys.exit(0)
