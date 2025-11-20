# Changelog - 2025-11-20: Edge-Based Trading Pipeline

## Summary

Implemented complete edge-based decision pipeline to fix `price: 0.0` and `edgepctpoints: None` issues in the engine snapshot. The trading brain now computes actual edges from live market data and generates interpretable DRYRUN orders.

## What Was Added

### Core Pipeline Scripts

1. **`pm_enrich_model.py`** - Model Enrichment Layer
   - Reads live market data from `polymarket-compact.json`
   - Updates `polymarket-model.json` with actual trading prices
   - Computes `edge_pct_points = 100 × (fair_yes - price)`
   - Handles both YES and NO positions correctly
   - Location: `termux-hands-off/agent/pm_enrich_model.py`

2. **`pm_decide.py`** - Decision Layer
   - Reads enriched model with prices and edges
   - Filters by `min_edge_to_bet_pct_points` threshold
   - Sizes positions using `default_stake_usd` capped by `alloc.max_usd`
   - Generates DRYRUN orders in `decision_report.json`
   - Location: `termux-hands-off/agent/pm_decide.py`

### Shell Wrappers

3. **`hoenrich.sh`** - Enrichment wrapper for Termux → Droplet
4. **`hodecide.sh`** - Decider wrapper for Termux → Droplet

### Documentation

5. **`docs/TRADING_PIPELINE.md`** - Complete pipeline documentation
   - Scanner → Enrichment → Decider → Executor flow
   - File formats and data contracts
   - Configuration guide
   - Usage examples and troubleshooting

6. **`docs/DEPLOYMENT.md`** - Deployment instructions
   - Step-by-step deployment to droplet
   - Verification and testing procedures
   - Rollback and monitoring guides
   - Cron/systemd integration examples

## What Was Fixed

### Path Compatibility

- Updated `hogitpull` to auto-detect repo path on droplet
- Supports both `/root/hands-off` (legacy) and `/root/hands-off-engine` (new)
- Maintains backward compatibility

## Before vs After

### Before (from user's snapshot):
```json
{
  "model": {
    "events": [
      {
        "id": "btc-100k",
        "price": 0.0,              // ❌ No actual price
        "edgepctpoints": null,     // ❌ No computed edge
        "alloc": {"maxusd": 4.29}
      }
    ]
  }
}
```

### After (with new pipeline):
```json
{
  "model": {
    "events": [
      {
        "id": "btc-100k",
        "side": "YES",
        "price": 0.51,             // ✅ Live market price
        "fair_yes": 0.65,
        "edge_pct_points": 14.0,   // ✅ Computed edge
        "alloc": {"max_usd": 4.29}
      }
    ]
  },
  "polymarket": {
    "orders": [                    // ✅ Meaningful DRYRUN orders
      {
        "market_id": "btc-100k",
        "side": "YES",
        "limit_price": 0.51,
        "stake_usd": 4.29,
        "edge_pct_points": 14.0,
        "reason": "YES edge of +14.0pp (fair=0.650, price=0.510)"
      }
    ]
  }
}
```

## Usage Quick Start

### Deploy to Droplet
```bash
cd ~/hands-off-engine/termux-hands-off/bin
./hogitpull
```

### Run Pipeline
```bash
cd ~/hands-off-engine/termux-hands-off/agent

# 1. Enrich with live prices
./hoenrich.sh

# 2. Generate DRYRUN orders
./hodecide.sh

# 3. View results
./hoorders.sh
./hosnapshot.sh
```

### Configure
```bash
# Set your fair_yes values
ssh do138
nano /root/hands-off-out/state/polymarket-model.json

# Edit events[].fair_yes to your probability estimates
```

## Technical Details

### Edge Calculation

**YES positions:**
- Trading price = `best_ask` (price to buy YES)
- Edge = `(fair_yes - best_ask) × 100` pp

**NO positions:**
- Trading price = `1 - best_bid` (price to buy NO)
- Edge = `((1 - fair_yes) - price_to_buy_no) × 100` pp

### Position Sizing

```python
stake_usd = min(
    globals.default_stake_usd,     # e.g., $5
    event.alloc.max_usd            # e.g., $4.29
)
```

### Filtering

Only generates orders when:
- `edge_pct_points >= min_edge_to_bet_pct_points` (default: 3pp)
- `alloc.max_usd > 0`
- `stake_usd >= 0.01`

## Safety Notes

⚠️ **DRYRUN Mode**: No actual trades are executed. The pipeline generates order plans only.

⚠️ **Before LIVE**:
1. Review DRYRUN output carefully
2. Verify fair_yes values are reasonable
3. Test with small position sizes
4. Enable `infra_allow_trades` flag explicitly

## File Locations

### On Droplet
- Code: `/root/hands-off/` or `/root/hands-off-engine/`
- State: `/root/hands-off-out/state/`
- Input: `polymarket-compact.json` (from scanner)
- Model: `polymarket-model.json` (curated + enriched)
- Output: `decision_report.json` (DRYRUN orders)

### On Termux
- Code: `~/hands-off-engine/`
- Scripts: `~/hands-off-engine/termux-hands-off/agent/`
- Wrappers: `~/hands-off-engine/termux-hands-off/bin/`

## Git Info

**Branch**: `claude/engine-snapshot-budget-014TEzB7fsTQE1bv6kSgKm4V`

**Commits**:
1. `499a731` - feat: add model enrichment and decider for edge-based DRYRUN orders
2. `a05f8b1` - fix: update droplet paths to support both hands-off and hands-off-engine
3. `2c93874` - docs: add deployment guide for trading pipeline updates

**PR**: https://github.com/yaya1738/hands-off-engine/pull/new/claude/engine-snapshot-budget-014TEzB7fsTQE1bv6kSgKm4V

## Next Steps

1. **Deploy**: Run `./hogitpull` to sync to droplet
2. **Test**: Run enrichment and decider manually
3. **Configure**: Set fair_yes values for your markets
4. **Verify**: Check DRYRUN output makes sense
5. **Automate**: Add to cron or systemd timer (see DEPLOYMENT.md)
6. **Fix hoviewer**: Address the service health issue (separate from trading logic)

## Related Docs

- [TRADING_PIPELINE.md](./docs/TRADING_PIPELINE.md) - Complete pipeline documentation
- [DEPLOYMENT.md](./docs/DEPLOYMENT.md) - Deployment and configuration guide
- [README.md](./README.md) - Main project README (if exists)

## Support

For questions or issues:
- Check documentation in `docs/`
- Review logs: `./hoinsight.sh`, `./hoorders.sh`
- Verify paths match your deployment
- Test with DRYRUN before going LIVE

---

**Status**: ✅ Committed and pushed to remote
**Mode**: 🧪 DRYRUN only - safe to deploy and test
**Action Required**: Deploy to droplet, configure fair_yes values, verify output
