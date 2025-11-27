import os, sys, json, datetime
from pathlib import Path

# Add alpha module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'alpha'))
from alpha_scorer import score_candidate, calculate_summary_stats, rank_and_cap_candidates, ScoringConfig

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
scored_candidates = []

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

    # Update candidate with p_fair
    c['p_fair'] = p_fair

    # Score using multi-factor algorithm
    scored = score_candidate(c)
    scored_candidates.append(scored)

# Calculate summary stats
stats = calculate_summary_stats(scored_candidates, thr)

# Rank and cap
config = ScoringConfig(
    min_score_threshold=thr,
    max_candidates_global=50,
    max_candidates_per_category=15
)
final_candidates = rank_and_cap_candidates(scored_candidates, config)

# Print digest
utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
print(f"[Edge Digest @ {utc}] threshold={thr}")
print(f"Total candidates: {stats['total_candidates']}")
print(f"Filtered (above threshold): {stats['filtered_candidates']}")
print(f"Best score: {stats['best_score']:.4f}")
print(f"Avg score: {stats['avg_score']:.4f}\n")

if not final_candidates:
    print("No edges above threshold. Adjust watchlist/fair_priors or lower EDGE_THRESHOLD.")
    sys.exit(0)

for i, e in enumerate(final_candidates, 1):
    sign = "BUY YES" if e["edge_raw"] > 0 else "BUY NO"
    cat = e.get('category', 'other').upper()
    print(f"{i:02d}. [{cat:8s}] score={e['score']:.4f} edge={e['edge_raw']:+.3f} | "
          f"fair={e['p_fair']:.3f} mkt={e['p_mkt']:.3f} | {sign:7s} | {e['note']}")
