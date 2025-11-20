# Hands-Off Trading Pipeline

## Overview

The trading pipeline transforms market data into actionable orders through a multi-stage process:

```
Scanner → Enrichment → Decider → Executor
   ↓           ↓          ↓         ↓
compact.json  model.json  decision_report.json  (DRYRUN/LIVE)
```

## Pipeline Stages

### 1. Scanner → `polymarket-compact.json`

**Input**: Live market data from Polymarket API
**Output**: `$HOME/hands-off-out/state/polymarket-compact.json`

The scanner fetches current market data including:
- Market IDs and questions
- Best bid/ask prices
- Volume and liquidity
- Close dates

**Format** (dict indexed by market_id):
```json
{
  "btc-100k": {
    "id": "btc-100k",
    "question": "Bitcoin reaches $100k by EOY?",
    "best_ask": 0.51,
    "best_bid": 0.49,
    "yes_price": 0.50,
    "no_price": 0.50,
    "volume": 125000,
    "closes_at": "2024-12-31T23:59:59Z"
  }
}
```

### 2. Model Configuration → `polymarket-model.json`

**Manually curated** list of markets to track with fair value estimates.

**Format**:
```json
{
  "as_of": "2025-11-20T10:30:00Z",
  "globals": {
    "budget_usd": 30.0,
    "default_stake_usd": 5.0,
    "min_edge_to_bet_pct_points": 3.0
  },
  "events": [
    {
      "id": "btc-100k",
      "side": "YES",
      "fair_yes": 0.65,
      "price": 0.51,
      "edge_pct_points": 14.0,
      "question": "Bitcoin reaches $100k by EOY?",
      "category": "crypto",
      "alloc": {
        "max_usd": 4.29
      }
    }
  ]
}
```

**Key fields**:
- `fair_yes`: Your model's probability estimate (0-1) that the YES outcome occurs
- `price`: Current trading price (filled by enrichment)
- `edge_pct_points`: Computed edge in percentage points (filled by enrichment)
- `alloc.max_usd`: Max position size for this market

### 3. Enrichment → `pm_enrich_model.py`

**Script**: `termux-hands-off/agent/pm_enrich_model.py`
**Wrapper**: `termux-hands-off/agent/hoenrich.sh`

**What it does**:
1. Reads `polymarket-compact.json` (live prices)
2. Reads `polymarket-model.json` (your curated markets + fair values)
3. For each event:
   - Extracts trading price from compact:
     - YES side: uses `best_ask`
     - NO side: uses `1 - best_bid` or `no_price`
   - Computes edge:
     - YES: `edge = 100 * (fair_yes - price)`
     - NO: `edge = 100 * ((1 - fair_yes) - price)`
4. Writes enriched `polymarket-model.json` back

**Usage**:
```bash
# From Termux
./hoenrich.sh
```

**Output**: Updated `polymarket-model.json` with live `price` and `edge_pct_points`.

### 4. Decider → `pm_decide.py`

**Script**: `termux-hands-off/agent/pm_decide.py`
**Wrapper**: `termux-hands-off/agent/hodecide.sh`
**Output**: `$HOME/hands-off-out/state/decision_report.json`

**What it does**:
1. Reads enriched `polymarket-model.json`
2. Filters events by `min_edge_to_bet_pct_points` threshold
3. Sizes positions:
   - Uses `default_stake_usd` from globals
   - Caps at `alloc.max_usd` per market
4. Generates DRYRUN orders

**Usage**:
```bash
# From Termux
./hodecide.sh
```

**Output format**:
```json
{
  "as_of": "2025-11-20T10:35:00Z",
  "mode": "DRYRUN",
  "infra_allow_trades": false,
  "gate_blocked": false,
  "polymarket": {
    "orders": [
      {
        "market_id": "btc-100k",
        "side": "YES",
        "limit_price": 0.51,
        "stake_usd": 4.29,
        "edge_pct_points": 14.0,
        "fair_yes": 0.65,
        "question": "Bitcoin reaches $100k by EOY?",
        "reason": "YES edge of +14.0pp (fair=0.650, price=0.510)"
      }
    ],
    "total_live_usd": 4.29
  }
}
```

### 5. Executor → (Future)

**Script**: `executor/ho_executor_plan.py` (TODO)
**Mode**: DRYRUN (no actual trades yet)

**What it will do**:
- Read `decision_report.json`
- Submit orders to Polymarket API (when LIVE mode enabled)
- Track order status and fills

## Typical Workflow

### Initial Setup

1. **Add markets to track**:
   ```bash
   # Add a market with your fair value estimate
   # Usage: hoaddmodel <market_id> <edge_pp> <max_usd>
   ./hoaddmodel.sh btc-100k 0 4.29
   ```

2. **Manually set fair_yes values**:
   Edit `polymarket-model.json` on the droplet:
   ```bash
   ssh do138
   nano /root/hands-off-out/state/polymarket-model.json
   ```

   Update `fair_yes` for each event (your probability estimate).

### Running the Pipeline

```bash
# 1. Enrich model with live prices
./hoenrich.sh

# 2. Generate orders
./hodecide.sh

# 3. View orders
./hoorders.sh

# 4. Get full snapshot
./hosnapshot.sh
```

### Viewing Results

```bash
# Quick status summary
./ho-state-summary.sh

# Detailed insight report
./hoinsight.sh

# View specific orders
./hoorders.sh
```

## Configuration

### Global Parameters

Edit `polymarket-model.json` globals:

```json
{
  "globals": {
    "budget_usd": 30.0,              // Total budget across all markets
    "default_stake_usd": 5.0,         // Default position size
    "min_edge_to_bet_pct_points": 3.0 // Minimum edge (3pp = 3%)
  }
}
```

### Per-Market Parameters

Edit individual events in `polymarket-model.json`:

```json
{
  "id": "btc-100k",
  "side": "YES",               // YES or NO
  "fair_yes": 0.65,            // Your probability estimate
  "alloc": {
    "max_usd": 10.0            // Max position size for this market
  }
}
```

## Edge Calculation

### YES Positions
- Trading price = `best_ask` (price to buy YES)
- Edge = `(fair_yes - best_ask) × 100` percentage points

**Example**:
- Fair: 0.65 (you think 65% chance)
- Ask: 0.51 (market price)
- Edge: (0.65 - 0.51) × 100 = **+14pp**

### NO Positions
- Trading price = `1 - best_bid` or `no_price`
- Edge = `((1 - fair_yes) - price_to_buy_no) × 100`

**Example**:
- Fair_yes: 0.20 (you think only 20% chance YES)
- Effective fair NO: 0.80
- NO price: 0.36
- Edge: (0.80 - 0.36) × 100 = **+44pp** (NO bet)

## Troubleshooting

### Missing price or edge_pct_points?

Run the enrichment:
```bash
./hoenrich.sh
```

### No orders generated?

Check:
1. Are `edge_pct_points` above `min_edge_to_bet_pct_points`? (default 3pp)
2. Is `alloc.max_usd` set and > 0?
3. Run `./hoinsight.sh` to see details

### Market not in compact?

The scanner might not be tracking it. Check scanner configuration.

## Safety Notes

⚠️ **Current Mode: DRYRUN ONLY**

No actual trades are being executed. The pipeline generates order plans but does not submit them to Polymarket.

Before enabling LIVE mode:
1. Verify DRYRUN orders make sense
2. Test with small position sizes
3. Enable `infra_allow_trades` flag
4. Monitor closely for the first few trades

## Files Reference

| File | Purpose | Format |
|------|---------|--------|
| `polymarket-compact.json` | Live market data | Dict of markets |
| `polymarket-model.json` | Curated markets + fair values | Model config |
| `decision_report.json` | Generated orders | Order list |

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `pm_enrich_model.py` | Enrich model with live prices |
| `pm_decide.py` | Generate DRYRUN orders |
| `hoenrich.sh` | Wrapper for enrichment |
| `hodecide.sh` | Wrapper for decider |
| `hoaddmodel.sh` | Add/update market in model |
| `hoinsight.sh` | Detailed report |
| `hoorders.sh` | View current orders |
| `hosnapshot.sh` | Full system snapshot |
