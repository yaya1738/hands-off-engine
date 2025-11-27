# Alpha Scoring System

## Overview

The alpha scoring system implements a multi-factor approach to rank and filter trading candidates from Polymarket markets.

## Scoring Formula

### Composite Score
```
score = |edge| × (1 + vol_factor) × spread_factor × time_factor × (1 + confidence)
```

### Components

1. **Edge (Base Signal)**
   - `edge = p_fair - p_mkt`
   - Positive edge = YES underpriced (BUY YES opportunity)
   - Negative edge = YES overpriced (BUY NO opportunity)

2. **Volume Factor (Liquidity Bonus)**
   - `vol_factor = log(1 + volume) / 10`
   - Higher volume markets get higher scores
   - Easier to execute larger positions

3. **Spread Factor (Execution Cost)**
   - `spread_factor = max(0.1, 1 - spread × 5)`
   - Tight spreads = lower execution cost = higher score
   - Wide spreads penalized

4. **Time Factor (Urgency)**
   - `time_factor = exp(-days_to_close / 30)`
   - Near-term events prioritized
   - Reduces uncertainty from distant events

5. **Confidence Factor (Signal Strength)**
   - `confidence = 1 - 2 × |p_fair - 0.5|`
   - Extreme priors (0.1, 0.9) = stronger signal
   - Neutral priors (0.5) = weaker signal

## Score Interpretation

| Score Range | Signal Quality | Recommended Action |
|-------------|----------------|-------------------|
| 0.00 - 0.02 | Weak | Hold/Skip |
| 0.02 - 0.05 | Moderate | Small position |
| 0.05 - 0.10 | Strong | Standard position |
| 0.10+ | Exceptional | Large position |

## Ranking & Filtering

### Multi-Level Sort
1. **Primary:** Score (descending)
2. **Secondary:** Category priority (configurable)
3. **Tertiary:** Volume (descending)

### Caps & Limits
- **Global cap:** 50 candidates (configurable)
- **Per-category cap:** 15 candidates default (configurable per category)
- **Minimum score threshold:** 0.02 (configurable)

### Category Caps (Default)
- Crypto: 20 candidates
- Politics: 15 candidates
- Macro: 10 candidates
- Sports: 10 candidates
- Other: 5 candidates

## Configuration

Edit `alpha/alpha_config.json`:
```json
{
  "min_score_threshold": 0.02,
  "max_candidates_global": 50,
  "max_candidates_per_category": 15,
  "edge_threshold": 0.05,
  "category_caps": {
    "crypto": 20,
    "sports": 10,
    "politics": 15,
    "macro": 10,
    "other": 5
  }
}
```

## Summary Statistics

The system outputs aggregate metrics:

- **best_score:** Highest scoring candidate
- **avg_score:** Mean score across all candidates
- **median_score:** Median score
- **top_10_avg:** Average of top 10 candidates
- **total_candidates:** Total candidates evaluated
- **filtered_candidates:** Candidates above threshold
- **category_breakdown:** Per-category stats (count, avg, top_score, top_edge)
- **percentiles:** Distribution metrics (p25, p50, p75, p90, p95)

## Usage

### Scoring Candidates
```python
from alpha_scorer import score_candidate, ScoringConfig, rank_and_cap_candidates

# Score a single candidate
candidate = {
    'key': 'btc_100k',
    'p_fair': 0.65,
    'p_mkt': 0.50,
    'volume': 1000000,
    'category': 'crypto'
}
scored = score_candidate(candidate)

# Rank and cap multiple candidates
config = ScoringConfig()
final_candidates = rank_and_cap_candidates(all_candidates, config)
```

### Generating Stats
```python
from alpha_stats import write_summary_stats, print_summary_stats

# Write stats to file
write_summary_stats(candidates, threshold=0.02, output_path=Path('stats.json'))

# Print to console
stats = calculate_summary_stats(candidates, threshold=0.02)
print_summary_stats(stats)
```

## Testing

Run unit tests:
```bash
cd alpha/tests
python test_alpha_scorer.py
```

## Integration Points

1. **Input:** Candidates from `fetch_polymarket.py` or `candidates.jsonl`
2. **Scoring:** `alpha_scorer.py` enriches candidates with scores
3. **Filtering:** Apply thresholds and caps
4. **Output:** Ranked candidates to `alpha_candidates_scored.json`
5. **Stats:** Summary to `alpha_stats.json`
