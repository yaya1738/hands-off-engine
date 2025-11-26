# Alpha Module: Real Market Signals Pipeline

This module transforms raw Polymarket data into actionable alpha signals for the Hands-Off Engine.

## Overview

The Alpha module bridges raw market data with the Decider (brain) by:
1. Fetching live market data with retry logic and caching
2. Filtering markets by liquidity, price range, and other criteria
3. Tracking historical odds and detecting sharp movements
4. Estimating fair prices for each market
5. Calculating edge (difference between fair and market price)
6. Outputting canonical alpha signals to `state/polymarket-model.json`

## Files

### Core Pipeline
- **`enhanced_pipeline.py`** - Enhanced V2 pipeline with filtering and history tracking
- **`sync_polymarket_model.py`** - Original V1 sync script (still supported)
- **`ho_alpha_polymarket.py`** - Legacy placeholder

### Data Components
- **`data_fetcher.py`** - Data fetching with retry logic, caching, and fallback sources
- **`historical_odds.py`** - Historical odds tracking and velocity calculation
- **`market_filter.py`** - Market filtering by liquidity, price, type, and exclusions

## Usage

### Enhanced Pipeline V2 (Recommended)

```bash
# Run enhanced pipeline with filtering, caching, and history tracking
python3 alpha/enhanced_pipeline.py
```

This provides:
- Data fetching with retry logic and exponential backoff
- Market filtering by liquidity, price range, and custom criteria
- Historical odds tracking with velocity calculation
- Sharp money movement detection
- Comprehensive logging and metrics

### Original Pipeline V1

```bash
# Run original sync script (still supported for compatibility)
python3 alpha/sync_polymarket_model.py
```

Both pipelines read from `termux-hands-off/out/polymarket-compact.json` and write to `state/polymarket-model.json`.

### Enhanced V2 Model Format

Enhanced pipeline adds additional fields:

```json
{
  "generated_at": "2025-11-26T12:14:06Z",
  "source_timestamp": "2025-11-16T12:05:00Z",
  "pipeline_version": "2.0",
  "total_markets_fetched": 55,
  "total_markets_filtered": 5,
  "markets_selected": 5,
  "filter_stats": {
    "total_checked": 55,
    "passed": 5,
    "rejected_price": 26,
    "rejected_liquidity": 0
  },
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
      "liquidity": 1000.0,
      "velocity_1h": 0.02,
      "velocity_24h": 0.01,
      "is_sharp_move": false
    }
  ]
}
```

### Field Definitions

**Core Fields:**
- **`market_id`** - Unique identifier (slug from Polymarket)
- **`question`** - Market question text
- **`query_category`** - Category/query this market belongs to
- **`side`** - Recommended side ("YES" or "NO")
- **`model_edge`** - Estimated edge (0.0 to 1.0), e.g., 0.08 = 8% edge
- **`model_confidence`** - Confidence in the edge estimate (0.0 to 1.0)
- **`fair_price`** - Our estimated fair price (0.0 to 1.0)
- **`market_price`** - Current market price (0.0 to 1.0)
- **`best_bid`** - Current best bid price
- **`liquidity`** - Market liquidity indicator

**Enhanced V2 Fields:**
- **`velocity_1h`** - Odds change per hour over last hour (optional)
- **`velocity_24h`** - Odds change per hour over last 24 hours (optional)
- **`is_sharp_move`** - Whether sharp money movement detected (optional)
- **`pipeline_version`** - Pipeline version ("2.0" for enhanced)
- **`filter_stats`** - Detailed filtering statistics

## Enhanced Features

### Data Fetcher (`data_fetcher.py`)

**Retry Logic:**
- Exponential backoff (1s, 2s, 4s)
- Configurable max retries (default: 3)
- Multiple source fallback support

**Caching:**
- File-based caching with configurable TTL (default: 5 minutes)
- Automatic cache invalidation
- Cache hit/miss logging

**Rate Limiting:**
- Protects against excessive API calls
- Configurable: 60 calls per 60 seconds default
- Automatic wait when limit reached

### Historical Odds Tracker (`historical_odds.py`)

**Features:**
- Stores up to 288 snapshots per market (24h at 5-min intervals)
- Calculates odds velocity (1h, 6h, 24h windows)
- Detects sharp money movements (>10% change threshold)
- Identifies trending markets

**Storage:**
- Historical data stored in `state/historical_odds/`
- One JSON file per market
- Atomic writes for data integrity

### Market Filter (`market_filter.py`)

**Filtering Criteria:**
- **Liquidity:** Minimum $10k volume (configurable)
- **Price Range:** 0.05 to 0.95 (avoid near-certainties)
- **Time to Resolution:** Min/max days configurable
- **Market Type:** Binary only for V1
- **Keywords:** Exclude specific terms
- **Exclusion List:** Persistent blacklist in `state/market_exclusion_list.json`

**Statistics Tracking:**
- Total markets checked
- Pass/reject counts by reason
- Useful for monitoring and tuning

## State Management

### Cache Files
- **`state/cache_*.json`** - Cached data from fetcher (TTL: 5 minutes)
- **`state/market_cache.json`** - Reserved for future use

### Historical Data
- **`state/historical_odds/`** - Historical odds snapshots per market
- One JSON file per market with timestamped snapshots
- Automatic cleanup of old snapshots (keeps last 288)

### Logs
- **`state/fetch_log.jsonl`** - JSONL log of fetch attempts
  - Timestamp, success/failure, markets count
  - One line per fetch for monitoring
- **`logs/audit/audit_*.jsonl`** - Comprehensive audit logs
  - All pipeline events
  - Cache hits/misses
  - Filter decisions
  - Sharp move detections

### Metrics
- **`state/pipeline_metrics.json`** - Current pipeline metrics
  - Last success/failure timestamps
  - Duration, market counts
  - Filter statistics
  - Success rate tracking

### Configuration
- **`state/market_exclusion_list.json`** - Blacklisted markets
  - Persistent across runs
  - Can be manually edited or managed via API

## Filtering Logic

**V1 Pipeline:**
- Edge >= 3% (configurable minimum threshold)
- Market price between 0.05 and 0.95 (avoid near-certain markets)
- Markets are sorted by edge (highest first)
- Top N markets selected (default: 20)

**V2 Enhanced Pipeline:**
- All V1 filters plus:
- Liquidity >= $10k (configurable, currently disabled for placeholder data)
- Time to resolution filters (min/max days)
- Keyword exclusion
- Persistent exclusion list
- Market type filtering (binary only for V1)

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

**V1 Pipeline:**
```
Raw Data → sync_polymarket_model.py → Alpha Signals → Decider → Executor
```

**V2 Enhanced Pipeline:**
```
Raw Data → Data Fetcher → Market Filter → Historical Tracker → Alpha Model → Output
           (retry/cache)  (liquidity/etc)  (velocity calc)  (edge calc)  (JSON)
```

### Integration Points

1. **Input**: `termux-hands-off/out/polymarket-compact.json`
2. **Data Fetcher**: Fetch with retry logic and caching
3. **Market Filter**: Apply liquidity, price, and other filters
4. **Historical Tracker**: Update odds history, calculate velocity
5. **Alpha Model**: Calculate edge and confidence
6. **Output**: `state/polymarket-model.json`
7. **Consume**: Decider loads signals via `load_model_signals()`

### Audit Integration

All pipeline stages log to audit system:
- Data fetches (success/failure, retry attempts)
- Cache hits/misses
- Filter decisions and rejections
- Velocity calculations
- Sharp move detections
- Pipeline start/complete events

Audit logs stored in `logs/audit/audit_YYYY-MM-DD.jsonl`

## Testing

### Run All Tests

```bash
# Original V1 pipeline tests
python3 tests/test_alpha_pipeline.py

# Enhanced V2 pipeline tests
python3 tests/test_enhanced_pipeline.py
```

### Test Coverage

**V1 Tests:**
- Model generation and schema validation
- Edge calculation correctness
- Filtering logic
- File I/O and atomic writes
- End-to-end pipeline
- Executor safety reflexes

**V2 Tests:**
- Data fetcher with retry and caching
- Historical odds tracking and velocity
- Market filtering with various criteria
- Filter statistics
- Cache invalidation
- Enhanced pipeline integration

### Component Testing

```bash
# Test individual components
python3 alpha/data_fetcher.py
python3 alpha/historical_odds.py
python3 alpha/market_filter.py
python3 alpha/enhanced_pipeline.py
```

## Automation

For production use, schedule regular pipeline runs:

```bash
# V2 Enhanced Pipeline (recommended)
*/15 * * * * cd /path/to/repo && python3 alpha/enhanced_pipeline.py

# V1 Original Pipeline (legacy)
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

### Key Metrics

Monitor these files for health:
- **`state/polymarket-model.json`** - Should be recent (< 15 min old)
- **`state/fetch_log.jsonl`** - Check success rate
- **`state/pipeline_metrics.json`** - View last run statistics
- **`logs/audit/audit_*.jsonl`** - Detailed event logs

### What to Monitor

**Pipeline Health:**
- Fetch success rate (should be >95%)
- Pipeline duration (should be <30 seconds)
- Cache hit rate (useful for optimization)
- Error frequency and types

**Market Quality:**
- Number of markets analyzed vs selected
- Average edge of selected markets
- Confidence distribution
- Filter rejection reasons (tune criteria)

**Velocity Detection:**
- Sharp move frequency
- Velocity distributions (1h, 6h, 24h)
- Trending market count

### Alerting

Set up alerts for:
- Multiple consecutive fetch failures
- No markets passing filters
- Pipeline not running (check timestamp age)
- Sharp moves on high-edge markets

## Performance

### V2 Pipeline Optimizations

**Caching:**
- Default 5-minute TTL reduces API calls
- Cache hit rate typically 80%+ with 15-min scheduling
- Significant reduction in data fetch time

**Filtering:**
- Early rejection of bad markets
- Reduces processing time for alpha calculations
- Filter stats help tune criteria

**Historical Tracking:**
- Incremental updates (only new snapshots)
- Automatic cleanup of old data
- Minimal storage overhead

### Typical Performance

- Cold run (no cache): 1-2 seconds
- Warm run (cached): 0.1-0.5 seconds
- Memory usage: <50 MB
- Disk usage: ~1 MB per day of history

## Future Enhancements

### Completed (V2)
- ✅ Retry logic with exponential backoff
- ✅ Caching to reduce API calls
- ✅ Rate limiting protection
- ✅ Historical odds tracking
- ✅ Odds velocity calculation
- ✅ Sharp money movement detection
- ✅ Advanced market filtering
- ✅ State management and metrics

### Planned
1. **Real Liquidity Data** - Query Polymarket API for actual liquidity
2. **Historical Accuracy** - Track prediction accuracy over time
3. **Multi-Source Alpha** - Combine signals from multiple models
4. **Feature Engineering** - Add more market features (time to resolution, etc.)
5. **ML Models** - Train models on historical outcomes
6. **Backtesting Framework** - Validate alpha signals against historical data
7. **API Endpoint** - REST API for real-time alpha queries
8. **Dashboard** - Web UI for monitoring and analysis
