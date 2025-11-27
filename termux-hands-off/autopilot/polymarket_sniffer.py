import json, os, sys
from datetime import datetime, timezone
from dateutil import tz
from pathlib import Path
import requests

# Add alpha module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'alpha'))
from alpha_scorer import score_candidate, calculate_summary_stats

TZ = tz.gettz('Asia/Jerusalem')
BASE = os.path.dirname(__file__)

EDGE_THRESHOLD = float(os.environ.get('EDGE_THRESHOLD', '0.05'))
MAX_RESULTS    = int(os.environ.get('MAX_RESULTS', '40'))
POLY_URL       = "https://gamma-api.polymarket.com/markets?limit=200&active=true"

WATCH_PATH = os.path.join(BASE, 'watchlist.txt')
PRIORS_PATH= os.path.join(BASE, 'fair_priors.json')

def load_watch():
    try:
        with open(WATCH_PATH, 'r', encoding='utf-8') as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.startswith('#')]
    except Exception:
        return []

def load_priors():
    try:
        with open(PRIORS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

WATCH_TERMS = load_watch()
REFERENCE_FAIR = load_priors()

def keep(title):
    if not WATCH_TERMS:
        return True
    t = title.lower()
    return any(w.lower() in t for w in WATCH_TERMS)

def fetch_markets():
    r = requests.get(POLY_URL, timeout=20)
    r.raise_for_status()
    return r.json()

def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

def get_yes_price(m):
    """
    Try multiple shapes:
    - outcomes: ["Yes","No"] + outcomePrices: ["0.45","0.55"]
    - outcomes: [{"name":"Yes","price":0.45}, ...]
    - contracts: [{"name":"Yes","price":0.45} or {"outcome":"Yes","bestBuyYesCost":0.45}, ...]
    - orderBooks/orderBook: nested best bids (rare here)
    Return a probability 0..1 or None.
    """
    # 1) outcomes + outcomePrices aligned lists
    outcomes = m.get('outcomes')
    outcome_prices = m.get('outcomePrices') or m.get('prices')
    if isinstance(outcomes, list) and isinstance(outcome_prices, list) and len(outcomes) == len(outcome_prices):
        for name, price in zip(outcomes, outcome_prices):
            if isinstance(name, str) and name.lower() == 'yes':
                pf = safe_float(price)
                if pf is not None:
                    return pf

    # 2) outcomes as list of dicts
    if isinstance(outcomes, list):
        for o in outcomes:
            if isinstance(o, dict):
                name = (o.get('name') or o.get('outcome') or '').lower()
                if name == 'yes':
                    for key in ('price','bestBuyYesCost','lastPrice','mid'):
                        pf = safe_float(o.get(key))
                        if pf is not None:
                            return pf

    # 3) contracts array
    contracts = m.get('contracts') or m.get('markets')  # sometimes nested
    if isinstance(contracts, list):
        for c in contracts:
            if isinstance(c, dict):
                name = (c.get('name') or c.get('outcome') or '').lower()
                if name == 'yes':
                    for key in ('price','bestBuyYesCost','lastPrice','mid'):
                        pf = safe_float(c.get(key))
                        if pf is not None:
                            return pf

    # 4) generic best price fields on root (rare)
    for key in ('bestBuyYesCost','yesPrice','price'):
        pf = safe_float(m.get(key))
        if pf is not None:
            return pf

    return None

def guess_fair(title: str, default=0.5):
    for k, v in REFERENCE_FAIR.items():
        if k.lower() in title.lower():
            try:
                return float(v)
            except Exception:
                return default
    return default

def main():
    data = fetch_markets()
    now  = datetime.now(timezone.utc).astimezone(TZ)
    rows = []

    for m in data:
        title = (m.get('question') or m.get('title') or '').strip()
        if not title or not keep(title):
            continue
        yes_price = get_yes_price(m)
        if yes_price is None:
            continue

        p_mkt = yes_price
        p_fair= guess_fair(title)
        edge  = p_fair - p_mkt  # FIXED: was p_mkt - p_fair (wrong sign)

        url = m.get('url') or m.get('slug') or ''
        # Make slug a proper URL if needed
        if url and not url.startswith('http'):
            url = f"https://polymarket.com/event/{url.strip('/')}"

        candidate = {
            'key': title[:100],
            'p_fair': p_fair,
            'p_mkt': p_mkt,
            'volume': m.get('volume'),
            'best_bid': m.get('bestBid'),
            'best_ask': m.get('bestAsk'),
            'closes_at': m.get('endDate') or m.get('end_date_iso'),
            'note': title,
            'url': url,
            'category': 'other'  # Could enhance with category inference
        }

        scored = score_candidate(candidate)

        if scored['score'] >= EDGE_THRESHOLD:
            rows.append({
                'title': title[:200],
                'p_market': round(p_mkt, 3),
                'p_fair': round(p_fair, 3),
                'edge': round(scored['edge_raw'], 3),
                'score': scored['score'],
                'side': 'BUY YES' if scored['edge_raw'] > 0 else 'BUY NO',
                'url': url
            })

    rows.sort(key=lambda r: r['score'], reverse=True)
    rows = rows[:MAX_RESULTS]

    # Calculate stats for summary
    stats = calculate_summary_stats(
        [{'score': r['score'], 'edge_raw': r['edge'], 'category': 'unknown'} for r in rows],
        EDGE_THRESHOLD
    )

    print(f"[Edge Digest @ {now.strftime('%Y-%m-%d %H:%M')}] threshold={EDGE_THRESHOLD}")
    print(f"Total: {stats['total_candidates']} | Filtered: {stats['filtered_candidates']} | Best: {stats['best_score']:.4f}")
    if not rows:
        print("No edges above threshold. Adjust watchlist/fair_priors or lower EDGE_THRESHOLD.")
        return
    for i, r in enumerate(rows, 1):
        print(f"{i:02d}. {r['side']:8s} | score={r['score']:.4f} edge={r['edge']:+.3f} | "
              f"mkt={r['p_market']:.3f} vs fair={r['p_fair']:.3f}\n    {r['title']}\n    {r['url']}")
if __name__ == '__main__':
    main()
