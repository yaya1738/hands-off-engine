# New Market Thin Book Edge - Research Summary

## The Edge
New markets have thin order books. Limit orders at book edges fill more easily because:
- Limited competition (few market makers initially)
- Wide spreads during price discovery
- Eager traders accept sub-optimal pricing

## Detection
```
NEW_MARKET = (age < 24 hours) AND (liquidity < $10k) AND (spread > 200 bps)
```

## Strategy
1. Post limits inside the spread (aggressive) or at edges (conservative)
2. Size small ($10-25 per order, max 5% of market liquidity)
3. Exit fast (4h max hold, 5% stop loss)

## Economics
- Standalone: ~breakeven to slightly negative
- With LLM edge filtering: $2-10/day possible
- This is a satellite strategy, not primary alpha

## Implementation Priority
1. Add `createdAt` to Market dataclass
2. Implement NewMarketDetector (poll every 30s)
3. Combine with intelligent alpha for market selection

## Key Insight
Works best when we have domain knowledge about the market topic.
Don't trade new markets blindly - use AI to filter.

---
Research completed: 2025-11-30
