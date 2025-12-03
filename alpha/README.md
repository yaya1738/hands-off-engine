# Alpha Module: Real Market Signals Pipeline

This module transforms raw Polymarket data into actionable alpha signals for the Hands-Off Engine.

## Overview

The Alpha module bridges raw market data with the Decider (brain) by:
1. Loading live market data from `termux-hands-off/out/polymarket-compact.json`
2. Estimating fair prices for each market
3. Calculating edge (difference between fair and market price)
4. Filtering markets by minimum edge and price thresholds
5. Outputting canonical alpha signals to `state/polymarket-model.json`

## Files

- **`sync_polymarket_model.py`** - Main sync script that generates alpha signals
- **`ho_alpha_polymarket.py`** - Legacy placeholder (to be updated)

## Usage

### Generate Alpha Signals

```bash
# Run sync script to generate state/polymarket-model.json
python3 alpha/sync_polymarket_model.py
```

This reads from `termux-hands-off/out/polymarket-compact.json` and writes to `state/polymarket-model.json`.

### Canonical Model Format

The output `state/polymarket-model.json` has this structure:

```json
{
  "generated_at": "2025-11-20T19:53:39Z",
  "source_timestamp": "2025-11-16T12:05:00Z",
  "total_markets_analyzed": 20,
  "markets_selected": 20,
  "markets": [
    {
      "market_id": "will-trump-talk-to-keir-starmer-in-november",
      "question": "Will Trump talk to Keir Starmer in November?",
      "query_category": "trump",
      "side": "YES",
      "model_edge": 0.165,
      "model_confidence": 0.35,
      "fair_price": 0.79,
      "market_price": 0.95,
      "best_bid": 0.80,
      "liquidity": 1000.0
    }
  ]
}
```

### Field Definitions

- **`market_id`** - Unique identifier (slug from Polymarket)
- **`question`** - Market question text
- **`query_category`** - Category/query this market belongs to
- **`side`** - Recommended side ("YES" or "NO")
- **`model_edge`** - Estimated edge (0.0 to 1.0), e.g., 0.08 = 8% edge
- **`model_confidence`** - Confidence in the edge estimate (0.0 to 1.0)
- **`fair_price`** - Our estimated fair price (0.0 to 1.0)
- **`market_price`** - Current market price (0.0 to 1.0)
- **`best_bid`** - Current best bid price
- **`liquidity`** - Market liquidity indicator (placeholder currently)

## Filtering Logic

Markets are filtered to include only:
- Edge >= 3% (configurable minimum threshold)
- Market price between 0.05 and 0.95 (avoid near-certain markets)
- Markets are sorted by edge (highest first)
- Top N markets selected (default: 20)

## Alpha Model (Fair Price Estimation)

⚠️ **Current Implementation**: Placeholder/demo model

The current fair price estimation uses a simple heuristic:
```python
fair_price = (best_bid + last_price) / 2 + adjustment
```

This is intentionally simple for demonstration purposes.

### Production Implementation TODO

For production use, replace with:
- Sophisticated statistical models
- Historical data analysis
- Fundamental analysis of event likelihood
- External data sources and signals
- Machine learning models
- Ensemble methods combining multiple approaches

The placeholder model is designed to be easily swapped out without changing the rest of the pipeline.

## Integration with Pipeline

The Alpha module integrates with the broader pipeline:

```
Raw Data → sync_polymarket_model.py → Alpha Signals → Decider → Executor
```

1. **Input**: `termux-hands-off/out/polymarket-compact.json`
2. **Transform**: `sync_polymarket_model.py`
3. **Output**: `state/polymarket-model.json`
4. **Consume**: Decider loads signals via `load_model_signals()`

## Testing

Run tests:
```bash
python3 tests/test_alpha_pipeline.py
```

Tests cover:
- Model generation and schema validation
- Edge calculation correctness
- Filtering logic
- File I/O and atomic writes

## Automation

For production use, schedule regular sync runs:

```bash
# Example cron (every 15 minutes)
*/15 * * * * cd /path/to/repo && python3 alpha/sync_polymarket_model.py
```

This keeps `state/polymarket-model.json` up-to-date with live market data.

## Safety & Risk Management

The Alpha module includes several safety features:

1. **Atomic Writes** - Output written to `.tmp` file first, then moved
2. **Edge Threshold** - Only markets with meaningful edge (>3%)
3. **Price Boundaries** - Avoids extreme/certain markets
4. **Confidence Scoring** - Reduces confidence for suspicious high edges
5. **Validation** - Schema and value range checks

All signals are INPUTS to the Decider. Final execution decisions include additional safety checks in the Executor (body reflexes).

## Monitoring

When running in production, monitor:
- Number of markets analyzed vs selected
- Average edge of selected markets
- Confidence distribution
- Age of `state/polymarket-model.json` (should be recent)
- Sync script failures/errors

## Future Enhancements

1. **Real Liquidity Data** - Query Polymarket API for actual liquidity
2. **Historical Accuracy** - Track prediction accuracy over time
3. **Multi-Source Alpha** - Combine signals from multiple models
4. **Feature Engineering** - Add more market features (time to resolution, etc.)
5. **ML Models** - Train models on historical outcomes
6. **Backtesting Framework** - Validate alpha signals against historical data
