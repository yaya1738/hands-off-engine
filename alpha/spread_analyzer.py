#!/usr/bin/env python3
"""
Spread Analyzer: Market Inefficiency Detection for Polymarket
==============================================================

Identifies high-profit opportunities based on:
1. High Spread (bid-ask percentage) - immediate market making profit
2. High Order Flow Variance / Volume Ratio - market inefficiency signal
3. Market Newness - new markets have less efficient pricing

The core insight: Markets with HIGH SPREAD + HIGH VARIANCE/VOLUME
represent immediate profit opportunities. The higher the metrics,
the more immediate the profit potential.

Key Metrics:
- spread_pct: (ask - bid) / midpoint - higher = more profit per trade
- variance_volume_ratio: stdev(price_changes) / avg_volume - higher = more inefficiency
- market_age_hours: time since market creation - lower = less efficient
- opportunity_score: combined score prioritizing immediate profit

Usage:
    from alpha.spread_analyzer import SpreadAnalyzer

    analyzer = SpreadAnalyzer(history_path='state/market_history.json')
    analyzer.update_snapshot(markets_data)
    opportunities = analyzer.find_opportunities(min_score=0.5)
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from statistics import mean, stdev


@dataclass
class SpreadMetrics:
    """Metrics for a single market's spread and order flow."""
    market_id: str
    question: str
    category: str

    # Core pricing
    bid: float              # Best bid price
    ask: float              # Best ask price (inferred from last)
    mid: float              # Midpoint price
    last: float             # Last trade price

    # Spread metrics
    spread_absolute: float  # ask - bid
    spread_pct: float       # spread as percentage of mid
    spread_score: float     # normalized 0-1 score (higher = wider spread = more profit)

    # Order flow metrics (require historical data)
    price_variance: float          # variance of price over time
    variance_volume_ratio: float   # variance / volume (higher = more inefficiency)
    flow_score: float              # normalized 0-1 score

    # Market newness
    market_age_hours: Optional[float]  # hours since creation
    newness_score: float               # 0-1 (1 = brand new)

    # Combined opportunity metrics
    opportunity_score: float    # combined score prioritizing immediate profit
    profit_immediacy: str       # "immediate" / "high" / "medium" / "low"

    # Raw data
    volume: Optional[float]
    created_at: Optional[str]
    timestamp: str


@dataclass
class MarketSnapshot:
    """A point-in-time snapshot of market state for variance tracking."""
    market_id: str
    timestamp: str
    bid: float
    ask: float
    last: float
    volume: Optional[float]


class SpreadAnalyzer:
    """
    Analyzes market spreads and order flow to identify profit opportunities.

    Tracks historical snapshots to calculate order flow variance over time.
    Higher spread + higher variance/volume = more immediate profit.
    """

    # Thresholds for opportunity classification
    SPREAD_HIGH = 0.10      # 10% spread is considered high
    SPREAD_MEDIUM = 0.05    # 5% spread is medium

    # Weights for opportunity score calculation
    WEIGHT_SPREAD = 0.4     # Spread is primary profit driver
    WEIGHT_VARIANCE = 0.35  # High variance = market hasn't found equilibrium
    WEIGHT_NEWNESS = 0.25   # New markets are inherently inefficient

    def __init__(self, history_path: Optional[Path] = None, max_history_hours: int = 24):
        """
        Initialize the spread analyzer.

        Args:
            history_path: Path to store historical snapshots for variance calc
            max_history_hours: How many hours of history to retain
        """
        self.history_path = Path(history_path) if history_path else None
        self.max_history_hours = max_history_hours
        self.history: Dict[str, List[MarketSnapshot]] = {}

        if self.history_path and self.history_path.exists():
            self._load_history()

    def _load_history(self) -> None:
        """Load historical snapshots from disk."""
        try:
            with open(self.history_path, 'r') as f:
                data = json.load(f)
                for market_id, snapshots in data.get('markets', {}).items():
                    self.history[market_id] = [
                        MarketSnapshot(**s) for s in snapshots
                    ]
        except Exception:
            self.history = {}

    def _save_history(self) -> None:
        """Save historical snapshots to disk."""
        if not self.history_path:
            return

        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'markets': {
                market_id: [asdict(s) for s in snapshots]
                for market_id, snapshots in self.history.items()
            }
        }

        tmp_path = self.history_path.with_suffix('.tmp')
        with open(tmp_path, 'w') as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(self.history_path)

    def _prune_old_history(self) -> None:
        """Remove snapshots older than max_history_hours."""
        cutoff = datetime.now(timezone.utc).timestamp() - (self.max_history_hours * 3600)

        for market_id in list(self.history.keys()):
            self.history[market_id] = [
                s for s in self.history[market_id]
                if datetime.fromisoformat(s.timestamp.replace('Z', '+00:00')).timestamp() > cutoff
            ]
            if not self.history[market_id]:
                del self.history[market_id]

    def calculate_spread(self, bid: float, ask: float) -> Tuple[float, float, float]:
        """
        Calculate spread metrics from bid/ask.

        Returns:
            (spread_absolute, spread_pct, spread_score)
        """
        if bid <= 0 or ask <= 0:
            return (0.0, 0.0, 0.0)

        mid = (bid + ask) / 2.0
        spread_abs = ask - bid
        spread_pct = spread_abs / mid if mid > 0 else 0.0

        # Normalize to 0-1 score (10%+ spread = 1.0)
        spread_score = min(1.0, spread_pct / self.SPREAD_HIGH)

        return (spread_abs, spread_pct, spread_score)

    def calculate_variance_metrics(self, market_id: str, current_price: float,
                                    volume: Optional[float]) -> Tuple[float, float, float]:
        """
        Calculate order flow variance metrics from historical data.

        Higher variance relative to volume indicates market inefficiency
        and price discovery in progress = profit opportunity.

        Returns:
            (price_variance, variance_volume_ratio, flow_score)
        """
        snapshots = self.history.get(market_id, [])

        if len(snapshots) < 2:
            # Not enough history - assume high variance (new market)
            return (0.0, 0.0, 0.5)  # Middle score when unknown

        # Calculate price changes over time
        prices = [s.last for s in snapshots] + [current_price]

        try:
            price_var = stdev(prices) if len(prices) > 1 else 0.0
        except Exception:
            price_var = 0.0

        # Calculate average volume (if available)
        volumes = [s.volume for s in snapshots if s.volume is not None]
        avg_volume = mean(volumes) if volumes else 1.0  # Default to 1 to avoid div by 0

        # Variance / Volume ratio (higher = more inefficiency per unit of trading)
        # Normalize volume to reasonable scale
        normalized_volume = max(avg_volume, 1.0) / 10000.0  # Assume $10k is baseline
        variance_ratio = price_var / max(normalized_volume, 0.001)

        # Score: high variance with low volume = high inefficiency
        # Cap at 1.0 for extreme values
        flow_score = min(1.0, variance_ratio * 10)

        return (price_var, variance_ratio, flow_score)

    def calculate_newness_score(self, created_at: Optional[str]) -> Tuple[Optional[float], float]:
        """
        Calculate market newness score.

        New markets (< 24 hours) are inherently less efficient.
        Brand new (< 2 hours) = maximum score.

        Returns:
            (age_hours, newness_score)
        """
        if not created_at:
            return (None, 0.3)  # Unknown age = assume moderate

        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age_hours = (now - created).total_seconds() / 3600

            # Scoring: exponential decay
            # 0 hours = 1.0, 2 hours = ~0.5, 24 hours = ~0.05
            newness_score = math.exp(-age_hours / 8)  # 8-hour half-life

            return (age_hours, min(1.0, newness_score))
        except Exception:
            return (None, 0.3)

    def calculate_opportunity_score(self, spread_score: float, flow_score: float,
                                     newness_score: float) -> Tuple[float, str]:
        """
        Calculate combined opportunity score.

        Higher score = more immediate profit potential.

        Returns:
            (opportunity_score, profit_immediacy)
        """
        # Weighted combination
        score = (
            self.WEIGHT_SPREAD * spread_score +
            self.WEIGHT_VARIANCE * flow_score +
            self.WEIGHT_NEWNESS * newness_score
        )

        # Classify immediacy
        if score >= 0.7:
            immediacy = "immediate"
        elif score >= 0.5:
            immediacy = "high"
        elif score >= 0.3:
            immediacy = "medium"
        else:
            immediacy = "low"

        return (score, immediacy)

    def analyze_market(self, market: Dict, category: str = "") -> SpreadMetrics:
        """
        Analyze a single market for spread and order flow opportunities.

        Args:
            market: Market dict with bid, ask/last, volume, created_at fields
            category: Market category/query for grouping

        Returns:
            SpreadMetrics with all calculated values
        """
        market_id = market.get('slug', market.get('market_id', ''))

        # Extract prices - handle various data formats
        bid = market.get('bestBid') or market.get('bid') or 0.0
        last = market.get('last') or market.get('ask') or market.get('yes_price') or 0.5

        # Infer ask from last trade (conservative estimate)
        # In prediction markets, last trade is often close to ask
        ask = last
        mid = (bid + ask) / 2.0 if bid > 0 else last

        # Calculate spread metrics
        spread_abs, spread_pct, spread_score = self.calculate_spread(bid, ask)

        # Get volume and creation date if available
        volume = market.get('volume')
        created_at = market.get('createdAt') or market.get('created_at')

        # Calculate variance metrics from history
        price_var, var_ratio, flow_score = self.calculate_variance_metrics(
            market_id, last, volume
        )

        # Calculate newness score
        age_hours, newness_score = self.calculate_newness_score(created_at)

        # Calculate combined opportunity score
        opp_score, immediacy = self.calculate_opportunity_score(
            spread_score, flow_score, newness_score
        )

        return SpreadMetrics(
            market_id=market_id,
            question=market.get('question', ''),
            category=category,
            bid=bid,
            ask=ask,
            mid=mid,
            last=last,
            spread_absolute=round(spread_abs, 4),
            spread_pct=round(spread_pct, 4),
            spread_score=round(spread_score, 4),
            price_variance=round(price_var, 6),
            variance_volume_ratio=round(var_ratio, 4),
            flow_score=round(flow_score, 4),
            market_age_hours=round(age_hours, 2) if age_hours else None,
            newness_score=round(newness_score, 4),
            opportunity_score=round(opp_score, 4),
            profit_immediacy=immediacy,
            volume=volume,
            created_at=created_at,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def update_snapshot(self, markets: List[Dict], category: str = "") -> None:
        """
        Record current market state as a snapshot for variance tracking.

        Should be called periodically to build up history for variance calculation.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        for market in markets:
            market_id = market.get('slug', market.get('market_id', ''))
            if not market_id:
                continue

            bid = market.get('bestBid') or market.get('bid') or 0.0
            last = market.get('last') or market.get('ask') or 0.5
            volume = market.get('volume')

            snapshot = MarketSnapshot(
                market_id=market_id,
                timestamp=timestamp,
                bid=bid,
                ask=last,
                last=last,
                volume=volume
            )

            if market_id not in self.history:
                self.history[market_id] = []
            self.history[market_id].append(snapshot)

        self._prune_old_history()
        self._save_history()

    def analyze_all(self, markets_by_category: Dict[str, List[Dict]]) -> List[SpreadMetrics]:
        """
        Analyze all markets and return sorted by opportunity score.

        Args:
            markets_by_category: Dict mapping category to list of markets

        Returns:
            List of SpreadMetrics sorted by opportunity_score (highest first)
        """
        all_metrics = []

        for category, markets in markets_by_category.items():
            # Update snapshots for variance tracking
            self.update_snapshot(markets, category)

            for market in markets:
                metrics = self.analyze_market(market, category)
                all_metrics.append(metrics)

        # Sort by opportunity score (highest = most immediate profit)
        all_metrics.sort(key=lambda m: m.opportunity_score, reverse=True)

        return all_metrics

    def find_opportunities(self, markets_by_category: Dict[str, List[Dict]],
                           min_score: float = 0.3,
                           min_spread_pct: float = 0.02) -> List[SpreadMetrics]:
        """
        Find high-profit opportunities based on spread and order flow.

        Args:
            markets_by_category: Dict mapping category to list of markets
            min_score: Minimum opportunity score to include
            min_spread_pct: Minimum spread percentage to consider

        Returns:
            List of opportunities sorted by immediacy of profit
        """
        all_metrics = self.analyze_all(markets_by_category)

        opportunities = [
            m for m in all_metrics
            if m.opportunity_score >= min_score and m.spread_pct >= min_spread_pct
        ]

        return opportunities

    def get_immediate_opportunities(self, markets_by_category: Dict[str, List[Dict]],
                                     top_n: int = 10) -> List[SpreadMetrics]:
        """
        Get the top N most immediate profit opportunities.

        These are markets where profit can be captured NOW due to:
        - Wide spreads (easy market making)
        - High variance (market hasn't found equilibrium)
        - Newness (inefficient pricing)
        """
        all_metrics = self.analyze_all(markets_by_category)

        # Filter for immediate/high priority only
        immediate = [
            m for m in all_metrics
            if m.profit_immediacy in ("immediate", "high")
        ]

        return immediate[:top_n]


def main():
    """CLI entry point for testing."""
    import sys

    repo_root = Path(__file__).parent.parent
    input_path = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
    history_path = repo_root / 'state' / 'market_history.json'

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    with open(input_path) as f:
        data = json.load(f)

    analyzer = SpreadAnalyzer(history_path=history_path)
    markets = data.get('markets', {})

    print("=" * 70)
    print("SPREAD & ORDER FLOW ANALYSIS - IMMEDIATE PROFIT OPPORTUNITIES")
    print("=" * 70)
    print()

    opportunities = analyzer.find_opportunities(markets, min_score=0.2, min_spread_pct=0.01)

    if not opportunities:
        print("No high-profit opportunities found.")
        return 0

    print(f"Found {len(opportunities)} opportunities:\n")

    for i, m in enumerate(opportunities[:15], 1):
        print(f"{i:2d}. [{m.profit_immediacy.upper():9s}] Score: {m.opportunity_score:.2f}")
        print(f"    {m.question[:60]}...")
        print(f"    Spread: {m.spread_pct:.1%} | Variance: {m.flow_score:.2f} | New: {m.newness_score:.2f}")
        print(f"    Bid: {m.bid:.3f} | Ask: {m.ask:.3f} | Mid: {m.mid:.3f}")
        print()

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
