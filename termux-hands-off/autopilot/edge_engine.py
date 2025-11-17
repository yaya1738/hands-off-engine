import os, sys, json, datetime

BASE = os.path.expanduser("~/hands-off/autopilot")
thr = float(os.environ.get("EDGE_THRESHOLD", "0.05"))

# inputs:
#   - candidates.jsonl (each line: {"key":"btc_above_100k","p_fair":0.34,"p_mkt":0.25,"note":"BTC 100k EOY"})
#   - optional fair_priors.json (fallback if a candidate line is missing p_fair)
cand_path = os.path.join(BASE, "candidates.jsonl")
priors_path = os.path.join(BASE, "fair_priors.json")

priors = {}
try:
    with open(priors_path, "r") as f:
        priors = json.load(f)
except FileNotFoundError:
    pass

def load_candidates():
    out = []
    try:
        with open(cand_path, "r") as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try:
                    j = json.loads(line)
                    out.append(j)
                except:
                    pass
    except FileNotFoundError:
        pass
    return out

cands = load_candidates()
edges = []
for c in cands:
    key = c.get("key") or c.get("market") or "unknown"
    p_mkt = c.get("p_mkt")
    p_fair = c.get("p_fair", None)

    if p_mkt is None:
        continue
    if p_fair is None:
        # fallback to priors (keys in priors may be friendly strings)
        p_fair = priors.get(key, None)
        if p_fair is None:
            # try looser match by lowercasing
            p_fair = priors.get(str(key).lower(), None)
    if p_fair is None:
        continue

    edge = float(p_fair) - float(p_mkt)
    if abs(edge) >= thr:
        edges.append({
            "key": key,
            "p_fair": float(p_fair),
            "p_mkt": float(p_mkt),
            "edge": float(edge),
            "note": c.get("note","")
        })

# print digest
utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
print(f"[Edge Digest @ {utc}] threshold={thr}")
if not edges:
    print("No edges above threshold. Adjust watchlist/fair_priors or lower EDGE_THRESHOLD.")
    sys.exit(0)

# sort by absolute edge desc
edges.sort(key=lambda x: abs(x["edge"]), reverse=True)
for e in edges:
    sign = "BUY YES" if e["edge"]>0 else "BUY NO"
    print(f"- {e['key']}: fair={e['p_fair']:.3f}, mkt={e['p_mkt']:.3f}, edge={e['edge']:+.3f}  [{sign}] {e['note']}")
