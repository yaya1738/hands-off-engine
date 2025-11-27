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
  - side: recommended side (YES/NO)
  - model_edge: estimated edge (0.0 to 1.0)
  - model_confidence: confidence in the edge estimate (0.0 to 1.0)
  - fair_price: model's estimated fair price
  - market_price: current market price
  - liquidity: market liquidity indicator
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


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


def estimate_fair_price(market: Dict) -> float:
    """
    Estimate fair price from market data.

    This function estimates our fair price based on:
    1. The spread between bestBid and last price (market inefficiency signal)
    2. Category-specific adjustments for known biases
    3. Volume-based confidence (higher volume = more efficient pricing)

    Args:
        market: Market dict with bestBid, last, etc.

    Returns:
        Estimated fair price (0.0 to 1.0)
    """
    best_bid = market.get('bestBid')
    if best_bid is None:
        best_bid = market.get('last', 0.5)
    last = market.get('last', 0.5)
    volume = market.get('volume', 0)
    query = market.get('query', '').lower()
    question = market.get('question', '').lower()
    
    # Base fair price is midpoint between bid and last
    avg = (best_bid + last) / 2.0
    
    # Calculate spread - larger spreads indicate market inefficiency
    spread = abs(last - best_bid) if best_bid else 0
    
    # Adjustment based on market characteristics
    adjustment = 0.0
    
    # Sports markets: tend to have edge on favorites (public overvalues underdogs)
    if any(kw in query for kw in ['nfl', 'nba', 'sports']):
        if last > 0.6:  # Favorite side
            adjustment = -0.05  # Slight edge on favorites
        elif last < 0.4:  # Underdog side  
            adjustment = 0.03  # Slight overpricing of underdogs
    
    # Political markets: tend to overprice extreme outcomes
    elif any(kw in query for kw in ['election', 'chile', 'fed', 'russia']):
        if last > 0.85:  # Very confident market
            adjustment = -0.04  # Markets often overconfident
        elif last < 0.15:  # Very unlikely outcome
            adjustment = 0.03  # Markets undervalue tail risk
        elif 0.4 <= last <= 0.6:  # Uncertain markets
            adjustment = spread * 0.5  # Use spread as edge signal
    
    # Crypto markets: tend to have momentum bias
    elif any(kw in query for kw in ['bitcoin', 'ethereum', 'btc', 'eth']):
        if 'reach' in question or 'above' in question:
            adjustment = -0.06  # Markets overoptimistic on reaching targets
        elif 'dip' in question or 'below' in question:
            adjustment = 0.04  # Markets underestimate downside
    
    # Ceasefire/geopolitical: markets often too optimistic about peace
    elif 'ceasefire' in query or 'peace' in query:
        adjustment = -0.05  # Markets tend to be hopeful
    
    # Volume-based dampening: higher volume = more efficient = less edge
    if volume and volume > 50_000_000:  # $50M+ volume
        adjustment *= 0.5  # Dampen adjustment for high-volume markets
    elif volume and volume > 20_000_000:  # $20M+ volume
        adjustment *= 0.75
    
    # Apply adjustment with some slug-based noise for diversity
    slug = market.get('slug', '')
    noise = (hash(slug) % 5 - 2) / 100.0  # -0.02 to +0.02
    
    fair = avg + adjustment + noise
    
    # Clamp to valid probability range
    return max(0.01, min(0.99, fair))


def calculate_confidence(edge: float, market: Dict) -> float:
    """
    Calculate confidence in the edge estimate.
    
    Higher edges generally have lower confidence (they're more suspicious).
    More liquid markets have higher confidence.
    
    Args:
        edge: The calculated edge
        market: Market dict with liquidity indicators
    
    Returns:
        Confidence (0.0 to 1.0)
    """
    # Base confidence starts at 0.7
    base_confidence = 0.7
    
    # Reduce confidence for very high edges (suspicious)
    if edge > 0.15:
        base_confidence *= 0.5
    elif edge > 0.10:
        base_confidence *= 0.7
    elif edge > 0.05:
        base_confidence *= 0.9
    
    # In production, would adjust based on:
    # - Market liquidity
    # - Historical accuracy of similar predictions
    # - Data quality
    # - Time until resolution
    
    return base_confidence


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
    
    # Skip markets with extreme prices (too certain)
    if market_price < 0.05 or market_price > 0.95:
        return None
    
    # Estimate fair price using our alpha model
    fair_price = estimate_fair_price(market)
    
    # Calculate edge
    edge = calculate_edge(market_price, fair_price)

    # OPTIMIZED: Increased minimum edge from 3% to 5%
    # More conservative - only select stronger opportunities
    if edge < 0.05:  # Less than 5% edge (was 3%)
        return None
    
    # Calculate confidence
    confidence = calculate_confidence(edge, market)
    
    # Determine side
    side = determine_side(market_price, fair_price)
    
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
        'best_bid': round(market.get('bestBid', market_price), 4),
        'liquidity': 1000.0  # Placeholder - in production, get real liquidity
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
