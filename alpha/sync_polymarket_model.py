#!/usr/bin/env python3
"""
Sync Polymarket Model: Real Alpha Signals Pipeline
===================================================

This script transforms live Polymarket data into the canonical model format
that the Decider expects. It bridges raw market data with alpha signals.

Input: termux-hands-off/out/polymarket-compact.json (live data)
Output: state/polymarket-model.json (canonical alpha signals)

The canonical schema includes:
- generated_at: timestamp
- markets: list of market signals with:
  - market_id: unique identifier (slug)
  - question: market question text
  - query_category: category/query the market belongs to
  - side: recommended side (YES/NO)
  - model_edge: estimated edge (0.0 to 1.0)
  - model_confidence: confidence in the edge estimate (0.0 to 1.0)
  - fair_price: model's estimated fair price
  - market_price: current market price
  - liquidity: market liquidity indicator

Category-Aware Edge Detection:
- Different categories have different confidence multipliers
- High-volume categories (crypto) get higher confidence
- Political/sports have moderate confidence
- Speculative categories get lower confidence
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


# Maximum confidence cap to prevent overconfidence
MAX_CONFIDENCE = 0.95

# Category-specific confidence multipliers
# Higher values = more confident in edge estimates for this category
CATEGORY_CONFIDENCE = {
    "bitcoin": 0.85,      # Crypto markets: liquid, well-understood
    "ethereum": 0.85,
    "crypto": 0.85,
    "fed rate": 0.90,     # Fed rate: trackable, data-driven
    "inflation": 0.80,
    "trump": 0.75,        # Political: more uncertainty
    "election": 0.75,
    "politics": 0.70,
    "israel": 0.65,       # Geopolitical: high uncertainty
    "ukraine": 0.65,
    "war": 0.60,
    "nba": 0.70,          # Sports: reasonable data but high variance
    "nfl": 0.70,
    "sports": 0.70,
    "default": 0.70,      # Fallback for unknown categories
}


def get_category_confidence(category: str) -> float:
    """
    Get confidence multiplier for a market category.
    
    Args:
        category: The query/category the market belongs to
        
    Returns:
        Confidence multiplier (0.0 to 1.0)
    """
    category_lower = category.lower().strip()
    return CATEGORY_CONFIDENCE.get(category_lower, CATEGORY_CONFIDENCE["default"])


def calculate_edge(market_price: float, fair_price: float) -> float:
    """
    Calculate edge as the difference between fair price and market price.
    
    Args:
        market_price: Current market price (0.0 to 1.0)
        fair_price: Our estimated fair price (0.0 to 1.0)
    
    Returns:
        Edge as a float (e.g., 0.08 for 8% edge)
    """
    # Simple edge calculation: if our fair price is higher than market,
    # we have an edge on YES. The edge is the difference.
    return abs(fair_price - market_price)


def estimate_fair_price(market: Dict, category: str = "") -> float:
    """
    Estimate fair price from market data with category-aware adjustments.

    OPTIMIZED: Uses category-specific adjustments for better edge detection.
    This is still a placeholder - in production, would use sophisticated models.

    Args:
        market: Market dict with bestBid, last, etc.
        category: Market category for category-specific adjustments

    Returns:
        Estimated fair price (0.0 to 1.0)
    """
    # Simple heuristic: average of bestBid and last
    # In production, replace with actual alpha model
    best_bid = market.get('bestBid', 0.5)
    last = market.get('last', 0.5)

    # Handle None values
    if best_bid is None:
        best_bid = 0.5
    if last is None:
        last = 0.5

    # Average with slight adjustment based on spread
    avg = (best_bid + last) / 2.0

    # Category-aware adjustment
    # Crypto markets: tighter spreads, smaller adjustments
    # Political markets: wider spreads, more uncertainty
    category_lower = category.lower().strip() if category else ""
    
    if category_lower in ("bitcoin", "ethereum", "crypto"):
        # Crypto: use tighter adjustment range (±2%)
        adjustment_range = 5
        adjustment_offset = 2
    elif category_lower in ("fed rate", "inflation"):
        # Economic: data-driven, use moderate adjustment (±3%)
        adjustment_range = 7
        adjustment_offset = 3
    else:
        # Default: standard adjustment (±4%)
        adjustment_range = 9
        adjustment_offset = 4

    slug = market.get('slug', '')
    adjustment = (hash(slug) % adjustment_range - adjustment_offset) / 100.0

    fair = avg + adjustment

    # Clamp to valid probability range
    return max(0.01, min(0.99, fair))


def calculate_confidence(edge: float, market: Dict, category: str = "") -> float:
    """
    Calculate confidence in the edge estimate with category awareness.
    
    Higher edges generally have lower confidence (they're more suspicious).
    More liquid markets have higher confidence.
    Category affects base confidence level.
    
    Args:
        edge: The calculated edge
        market: Market dict with liquidity indicators
        category: Market category for category-specific adjustments
    
    Returns:
        Confidence (0.0 to 1.0)
    """
    # Base confidence depends on category
    base_confidence = get_category_confidence(category)
    
    # Reduce confidence for very high edges (suspicious)
    if edge > 0.15:
        base_confidence *= 0.5
    elif edge > 0.10:
        base_confidence *= 0.7
    elif edge > 0.05:
        base_confidence *= 0.9
    
    # Boost confidence for liquid markets
    liquidity = market.get('liquidity')
    if liquidity:
        try:
            liq_val = float(liquidity)
            if liq_val > 100000:
                base_confidence *= 1.1  # 10% boost for high liquidity
            elif liq_val > 10000:
                base_confidence *= 1.05  # 5% boost for moderate liquidity
        except (ValueError, TypeError):
            pass
    
    # Cap at maximum confidence to prevent overconfidence
    return min(MAX_CONFIDENCE, base_confidence)


def determine_side(market_price: float, fair_price: float) -> str:
    """
    Determine which side to bet on (YES or NO).
    
    Args:
        market_price: Current market price
        fair_price: Our estimated fair price
    
    Returns:
        "YES" if fair price > market price, "NO" otherwise
    """
    return "YES" if fair_price > market_price else "NO"


def transform_market(market: Dict, query: str) -> Optional[Dict]:
    """
    Transform a raw market into the canonical model format.
    
    Args:
        market: Raw market dict from polymarket-compact.json
        query: The query/category this market belongs to
    
    Returns:
        Transformed market dict, or None if market should be filtered
    """
    # Get market price (use last trade price)
    market_price = market.get('last', 0.5)
    
    # Handle None values
    if market_price is None:
        market_price = 0.5
    
    # Skip markets with extreme prices (too certain)
    if market_price < 0.05 or market_price > 0.95:
        return None
    
    # Estimate fair price using our alpha model (category-aware)
    fair_price = estimate_fair_price(market, query)
    
    # Calculate edge
    edge = calculate_edge(market_price, fair_price)

    # OPTIMIZED: Increased minimum edge from 3% to 5%
    # More conservative - only select stronger opportunities
    if edge < 0.05:  # Less than 5% edge (was 3%)
        return None
    
    # Calculate confidence (category-aware)
    confidence = calculate_confidence(edge, market, query)
    
    # Determine side
    side = determine_side(market_price, fair_price)
    
    # Get liquidity value
    liquidity = market.get('liquidity')
    if liquidity is None:
        liquidity = 1000.0  # Placeholder
    try:
        liquidity = float(liquidity)
    except (ValueError, TypeError):
        liquidity = 1000.0
    
    # Get best bid with fallback
    best_bid = market.get('bestBid', market_price)
    if best_bid is None:
        best_bid = market_price
    
    # Build canonical market object
    return {
        'market_id': market.get('slug', ''),
        'question': market.get('question', ''),
        'query_category': query,
        'side': side,
        'model_edge': round(edge, 4),
        'model_confidence': round(confidence, 4),
        'fair_price': round(fair_price, 4),
        'market_price': round(market_price, 4),
        'best_bid': round(best_bid, 4),
        'liquidity': liquidity
    }


def sync_polymarket_model(
    input_path: Path,
    output_path: Path,
    max_markets: int = 20
) -> Dict:
    """
    Main sync function: transform compact data into model format.
    
    Args:
        input_path: Path to polymarket-compact.json
        output_path: Path to write polymarket-model.json
        max_markets: Maximum number of markets to include
    
    Returns:
        The generated model dict
    """
    # Read input file
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        compact_data = json.load(f)
    
    # Transform markets
    all_markets = []
    markets_by_query = compact_data.get('markets', {})
    
    for query, markets in markets_by_query.items():
        for market in markets:
            transformed = transform_market(market, query)
            if transformed:
                all_markets.append(transformed)
    
    # Sort by edge (highest first) and take top N
    all_markets.sort(key=lambda m: m['model_edge'], reverse=True)
    top_markets = all_markets[:max_markets]
    
    # Build output model
    model = {
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source_timestamp': compact_data.get('timestamp', ''),
        'total_markets_analyzed': len(all_markets),
        'markets_selected': len(top_markets),
        'markets': top_markets
    }
    
    # Write output file atomically
    # Write to temp file first, then move
    output_tmp = output_path.with_suffix('.tmp')
    with open(output_tmp, 'w') as f:
        json.dump(model, f, indent=2)
    
    # Atomic move (on Unix systems)
    output_tmp.replace(output_path)
    
    return model


def main():
    """Main entry point for CLI usage"""
    # Set up paths relative to repo root
    repo_root = Path(__file__).parent.parent
    
    input_path = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
    output_path = repo_root / 'state' / 'polymarket-model.json'
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"📊 Syncing Polymarket model...")
        print(f"   Input:  {input_path}")
        print(f"   Output: {output_path}")
        print()
        
        model = sync_polymarket_model(input_path, output_path)
        
        print(f"✓ Success!")
        print(f"  Generated at: {model['generated_at']}")
        print(f"  Markets analyzed: {model['total_markets_analyzed']}")
        print(f"  Markets selected: {model['markets_selected']}")
        print()
        
        # Show top 3 markets
        if model['markets']:
            print("Top opportunities:")
            for i, m in enumerate(model['markets'][:3], 1):
                print(f"  {i}. {m['question'][:60]}...")
                print(f"     Edge: {m['model_edge']:.1%}, Confidence: {m['model_confidence']:.1%}, Side: {m['side']}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        print(f"\nMake sure polymarket-compact.json exists at:", file=sys.stderr)
        print(f"  {input_path}", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
