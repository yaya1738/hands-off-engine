# Fetchers - Live Data Ingestion (Batch 12)

This module provides read-only data fetchers for the Hands-Off Engine.

## Polymarket Fetcher

The `ho_fetch_polymarket.py` module fetches live market data from Polymarket's public API.

### Features

- **Read-only public API access** - No authentication required
- **DRYRUN safe** - No trading or order execution
- **Robust error handling** - Gracefully handles network errors
- **Atomic writes** - Uses temp files to prevent corruption
- **Compatible format** - Produces data compatible with Alpha pipeline

### CLI Usage

```bash
# Fetch markets and write to state/polymarket-compact.json
python3 fetchers/ho_fetch_polymarket.py state/

# Debug mode - print raw API response
python3 fetchers/ho_fetch_polymarket.py --debug
```

### Python API

```python
from fetchers import ho_fetch_polymarket

# High-level: fetch and write in one call
output_path = ho_fetch_polymarket.fetch_and_write("state")

# Or step by step:
raw = ho_fetch_polymarket.fetch_markets_raw()
compact = ho_fetch_polymarket.build_compact_from_raw(raw)
path = ho_fetch_polymarket.write_compact("state", compact)
```

### Output Format

The fetcher produces `polymarket-compact.json` with this structure:

```json
{
  "timestamp": "2025-11-18T15:00:00Z",
  "markets": {
    "crypto": [...],
    "sports": [...],
    "politics": [...],
    "economy": [...],
    "other": [...]
  }
}
```

Each market entry contains:
- `id`: Market identifier
- `slug`: URL-friendly identifier
- `question`: Market question
- `title`: Event title
- `bestBid`: Best bid price (0-1)
- `last`: Last traded price (0-1)
- `endDate`: Market end date (ISO8601)
- `outcomes`: List of outcome names
- `outcomePrices`: List of outcome prices

### Integration with Autoloop

The fetcher is integrated into `ho_autoloop.py`:

```python
# In ho_autoloop.py
ENABLE_LIVE_POLYMARKET_FETCH = True  # Enable live data

# When run_all() is called, it will:
# 1. Fetch live Polymarket data
# 2. Run Alpha -> Decider -> Executor pipeline
# 3. Generate reports and summary
```

### Testing

```bash
# Run all integration tests
python3 -m unittest tests.integration.test_fetch_polymarket -v

# Tests use mocked network calls - no real API requests
```

### Safety

- ✓ Read-only public data access
- ✓ No authentication or API keys
- ✓ No trading or order execution
- ✓ Network-only for market data
- ✓ All downstream operations remain DRYRUN

### API Details

- **Endpoint**: `https://gamma-api.polymarket.com/events`
- **Method**: GET
- **Auth**: None (public endpoint)
- **Rate limits**: Unknown (handle 429 errors gracefully)

### Troubleshooting

If you encounter HTTP 403 errors:
1. The API may require different headers or have rate limiting
2. Check Polymarket API documentation for changes
3. Tests use mocked data and will pass regardless
4. DRYRUN pipeline works with existing/cached data
