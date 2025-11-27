# Arbitrage Detection Module

Cross-platform arbitrage detection for zero-risk profit opportunities.

## Overview

This module identifies arbitrage opportunities across:

1. **Prediction Markets**: Polymarket ↔ Kalshi
2. **Sports Betting**: Prediction markets vs. traditional sportsbooks
3. **Crypto Exchanges**: CEX ↔ CEX and CEX ↔ DEX price discrepancies

## Zero-Risk Arbitrage Explained

### Binary Prediction Market Arbitrage

When the same event trades on multiple platforms at different prices, you can lock in guaranteed profit.

**Example:**
- Polymarket: "Will Trump win 2024?" YES = $0.52
- Kalshi: Same event YES = $0.48 (so NO = $0.52)

**Strategy:**
1. Buy YES on Kalshi: $0.48
2. Buy NO on Polymarket: $0.48 (which is 1 - 0.52)
3. Total cost: $0.96

**Outcome A (Trump wins):** Win $1 from Kalshi YES → $0.04 profit
**Outcome B (Trump loses):** Win $1 from Polymarket NO → $0.04 profit

**Guaranteed profit: 4.17%** (0.04 / 0.96)

### Crypto Arbitrage

Price discrepancies between exchanges allow buying low and selling high.

**Example:**
- Binance: BTC/USDT ask = $67,000
- Kraken: BTC/USDT bid = $67,200

Buy on Binance, sell on Kraken → 0.3% profit minus fees

## Quick Start

```bash
# Scan all platforms
python -m arbitrage.cli scan

# Prediction markets only
python -m arbitrage.cli scan --pm

# Crypto only
python -m arbitrage.cli scan --crypto

# Set minimum profit threshold (default 0.5%)
python -m arbitrage.cli scan --min-profit 1.0

# View latest results
python -m arbitrage.cli report

# Continuous monitoring (5-minute intervals)
python -m arbitrage.cli watch --interval 300
```

## Architecture

```
arbitrage/
├── __init__.py              # Module exports
├── types.py                 # Data types (Platform, ArbitrageOpportunity, etc.)
├── event_matcher.py         # Cross-platform event matching
├── opportunity_detector.py  # Main arbitrage detection engine
├── audit.py                 # Audit logging integration
├── cli.py                   # Command-line interface
├── fetchers/
│   ├── polymarket.py        # Polymarket API fetcher
│   ├── kalshi.py            # Kalshi API fetcher
│   └── crypto_exchanges.py  # Multi-exchange crypto fetcher
└── README.md
```

## Data Flow

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Polymarket  │  │    Kalshi    │  │   Binance    │
│    Fetcher   │  │   Fetcher    │  │   Kraken...  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────┬────────┘                 │
                │                          │
         ┌──────▼──────┐            ┌──────▼──────┐
         │   Event     │            │    Crypto   │
         │   Matcher   │            │   Pricer    │
         └──────┬──────┘            └──────┬──────┘
                │                          │
                └─────────┬────────────────┘
                          │
                   ┌──────▼──────┐
                   │  Arbitrage  │
                   │  Calculator │
                   └──────┬──────┘
                          │
              ┌───────────┴───────────┐
              │                       │
       ┌──────▼──────┐         ┌──────▼──────┐
       │   Report    │         │   Audit     │
       │   Output    │         │   Logger    │
       └─────────────┘         └─────────────┘
```

## Configuration

### Environment Variables

```bash
# Optional: Kalshi API key for authenticated endpoints
export KALSHI_API_KEY="your-api-key"

# Minimum profit threshold (default: 0.5%)
export ARB_MIN_PROFIT=0.5
```

### Manual Market Mappings

For events that don't auto-match, add manual mappings in `state/arbitrage/market_mappings.json`:

```json
{
  "polymarket:trump-2024-winner": "kalshi:PRES-2024-TRUMP",
  "kalshi:PRES-2024-TRUMP": "polymarket:trump-2024-winner"
}
```

## Key Types

### ArbitrageOpportunity

```python
@dataclass
class ArbitrageOpportunity:
    opportunity_id: str
    arb_type: ArbitrageType      # TWO_WAY_BINARY, SIMPLE_SPOT, etc.
    profit_pct: float            # Gross profit percentage
    profit_pct_net: float        # After estimated fees
    matched_event: MatchedEvent  # For prediction market arb
    legs: List[Dict]             # What to buy/sell on each platform
    execution_risk: str          # low, medium, high
    risk_factors: List[str]
    max_size_usd: float          # Limited by liquidity
```

### MatchedEvent

```python
@dataclass
class MatchedEvent:
    event_id: str
    canonical_question: str
    markets: List[PredictionMarket]  # Same event on different platforms
    match_confidence: float          # 0-1, how sure we are it's the same event
    match_method: str                # exact, fuzzy, entity, manual
```

## Risk Factors

### Execution Risk Levels

- **Low**: High liquidity, exact match, same-platform spread arb
- **Medium**: Some match uncertainty, moderate liquidity
- **High**: Low liquidity, fuzzy match, crypto transfer time risk

### Common Risks

1. **Match uncertainty**: Different wording might mean different events
2. **Liquidity**: Large orders may not fill at quoted prices
3. **Timing**: Prices change; execution must be fast
4. **Transfer delays**: Crypto arb requires moving funds between exchanges
5. **Resolution differences**: Platforms may resolve events differently

## Integration with Hands-Off Engine

The arbitrage module integrates with existing infrastructure:

- **Audit logging**: All opportunities logged via `audit/audit_logger.py`
- **State management**: Results saved to `state/arbitrage/opportunities.json`
- **Polymarket data**: Can use cached `polymarket-compact.json` from existing fetchers

## Safety Features

- **DRYRUN by default**: Execution requires explicit confirmation
- **Audit trail**: Every scan and opportunity logged
- **Risk assessment**: Each opportunity rated for execution risk
- **Size limits**: Recommended sizes account for liquidity
- **Fee estimation**: Net profit accounts for platform fees

## Output Format

```json
{
  "scan_time": "2025-11-27T12:00:00Z",
  "prediction_markets": [
    {
      "opportunity_id": "a1b2c3d4",
      "arb_type": "two_way_binary",
      "profit_pct": 0.0417,
      "profit_pct_net": 0.0217,
      "execution_risk": "medium",
      "legs": [
        {"platform": "kalshi", "side": "YES", "price": 0.48},
        {"platform": "polymarket", "side": "NO", "price": 0.48}
      ],
      "matched_event": {
        "canonical_question": "Will Trump win the 2024 presidential election?",
        "match_confidence": 0.95
      }
    }
  ],
  "crypto": []
}
```

## Future Enhancements

- [ ] Real-time WebSocket price feeds
- [ ] Automated execution with confirmation
- [ ] Telegram/Discord alerts for high-profit opportunities
- [ ] Sportsbook integration (DraftKings, FanDuel)
- [ ] Historical opportunity tracking for ML models
- [ ] Multi-leg arbitrage (3+ platform)
