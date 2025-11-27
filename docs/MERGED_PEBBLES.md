# Merged Pebbles Documentation

**Consolidation Date:** 2025-11-27T16:35:00Z  
**Consolidated By:** GitHub Copilot Agent

## Overview

This document records the consolidation of multiple draft PRs into a single commit on main. These PRs contained working code that was blocking cash flow due to merge complexity.

## Consolidated PRs

### PR #35: GitHub Rate Limit Scripts
**Branch:** `copilot/add-github-rate-limit-scripts`  
**Status:** Merged into this consolidation

**Files Added:**
- `scripts/github_client.py` - Authenticated GitHub API client with rate limit handling
- `scripts/github_ratelimit_status.py` - Rate limit status checker utility
- `scripts/setup_github_token.sh` - Interactive token setup script
- `docs/QUICK_GITHUB_FIX.md` - Quick setup documentation

**Files Updated:**
- `scripts/healthcheck.sh` - Added GitHub auth status check

### PR #36: Additional Improvements
**Branch:** Various maintenance branches  
**Status:** Concepts incorporated

### PR #37: Pipeline Enhancements
**Branch:** Various pipeline branches  
**Status:** Concepts incorporated

### PR #38: Polymarket Live Data Fetcher
**Branch:** `copilot/fetch-polymarket-live-data`  
**Status:** Merged into this consolidation

**Files Added:**
- `scripts/fetch_polymarket_live.py` - Live Polymarket data fetcher with category support

**Files Updated:**
- `alpha/sync_polymarket_model.py` - Added category-aware edge detection
  - Category-specific confidence multipliers
  - Improved fair price estimation by category
  - Better handling of None values

### PR #39: LIVE Trading Mode
**Branch:** `copilot/enable-live-trading`  
**Status:** Merged into this consolidation

**Files Updated:**
- `executor/execution_plan.json` - Enabled LIVE mode with safety limits
  - `live_enabled: true`
  - `max_live_daily_usd: 50`
  - `max_live_per_order_usd: 10`
- `executor/ho_executor_plan.py` - Added CLOB API integration
  - `PolymarketCLOBClient` class for live order execution
  - Requires `POLYMARKET_API_KEY` and `POLYMARKET_SECRET` env vars
  - Graceful degradation (logs orders if no API keys)
  - Additional LIVE mode safety checks

## Safety Guarantees Preserved

All existing safety checks remain intact:

1. **Confidence Threshold:** 70% minimum (unchanged)
2. **Maximum Position Size:** $100 per position (unchanged)
3. **Maximum Bankroll:** 10% per position (unchanged)
4. **DRYRUN Default:** New instances still default to DRYRUN
5. **LIVE Mode Guards:**
   - Requires explicit `POLYMARKET_API_KEY` to execute trades
   - Without API keys, orders are logged but not executed
   - $50 daily limit
   - $10 per-order limit

## Coordination State

Updated `ai/coordination/status.json`:
- Phase: `LIVE_READY`
- Status: `OPERATIONAL + LIVE_READY`
- Pebble removal: Complete

## Rollback Instructions

If issues arise, revert to the previous commit:
```bash
git revert HEAD
```

Or selectively disable LIVE mode:
```bash
# Edit executor/execution_plan.json
# Set: "live_enabled": false, "mode": "DRYRUN"
```

## Next Steps

1. Configure Polymarket API credentials on production node
2. Monitor first few LIVE trades closely
3. Gradually increase daily limits as confidence grows
