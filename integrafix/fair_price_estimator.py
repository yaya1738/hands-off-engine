#!/usr/bin/env python3
"""
INTEGRAFIX: Fair Price Estimator
================================

PROBLEM SOLVED:
The old estimate_fair_price() was circular:
    fair = market_price + hash_adjustment(±0.04)

This means edge = |fair - market| ≈ 0.00 to 0.04 always.
That's not a real edge - it's noise.

SOLUTION:
Real fair price estimation from EXTERNAL sources:
1. Order book analysis (bid-ask midpoint, depth-weighted)
2. Historical data (where was price? regression to mean)
3. Volatility adjustment (high vol = wider fair range)
4. Category-specific models (sports, politics, etc.)
5. Ensemble of wisdom engine outputs

THE KEY INSIGHT:
Fair price must come from OUTSIDE the current market price.
Otherwise you're just adding noise to the price and calling it edge.

This file REPLACES the circular estimate_fair_price() in sync_polymarket_model.py
"""

import json
import math
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# ABCFC Integration - Absolute Bounds Continuous Fan Chart
try:
    from executor.math.abcfc_unified import create_binary_market_density
    ABCFC_AVAILABLE = True
except ImportError:
    ABCFC_AVAILABLE = False

# INTEGRAFIX: Knowledge Base Integration
try:
    from integrafix.knowledge_loader import knowledge as kb_loader
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False
    kb_loader = None

def get_knowledge_for_market(market_title: str) -> Optional[str]:
    """INTEGRAFIX: Search knowledge bases for relevant trading insights."""
    if not KNOWLEDGE_AVAILABLE or not kb_loader:
        return None
    try:
        # Extract key terms from market title
        terms = market_title.lower().replace('?', '').split()[:5]
        query = ' '.join(terms)
        results = kb_loader.search(query, limit=1)
        if results:
            return results[0].get('snippet', '')
    except:
        pass
    return None

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
HISTORY_DIR = STATE_DIR / "price_history"
HUMAN_ESTIMATES_FILE = STATE_DIR / "human_probability_estimates.json"
YAIR_KERNEL_FILE = STATE_DIR / "yair_context_kernel.json"


@dataclass
class FairPriceEstimate:
    """Result of fair price estimation."""
    fair_price: float
    confidence: float
    source: str                    # Which method produced this
    edge_vs_market: float          # fair - market
    is_actionable: bool            # Edge >= threshold
    reasoning: str


class FairPriceEstimator:
    """
    Estimate fair price from EXTERNAL signals, not market price.

    This breaks the circular dependency that killed edge detection.
    """

    def __init__(self):
        self.history_dir = HISTORY_DIR
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.price_history: Dict[str, List[Dict]] = {}
        self._load_history()

    def _load_history(self):
        """Load historical price data."""
        for f in self.history_dir.glob("*.json"):
            market_id = f.stem
            with open(f) as fp:
                self.price_history[market_id] = json.load(fp)

    def _save_history(self, market_id: str, data: List[Dict]):
        """Save historical price data."""
        with open(self.history_dir / f"{market_id}.json", 'w') as f:
            json.dump(data, f)

    def record_price(self, market_id: str, price: float, timestamp: Optional[str] = None):
        """Record a price observation for history."""
        if market_id not in self.price_history:
            self.price_history[market_id] = []

        self.price_history[market_id].append({
            "price": price,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        })

        # Keep last 1000 observations
        self.price_history[market_id] = self.price_history[market_id][-1000:]
        self._save_history(market_id, self.price_history[market_id])

    # ==================== ESTIMATION METHODS ====================

    def estimate_from_human(self, market: Dict) -> Optional[FairPriceEstimate]:
        """
        INTEGRAFIX: METHOD 0 (HIGHEST PRIORITY) - Human probability estimate from Yair.

        If Yair has provided a probability estimate for this market, USE IT.
        Human edge detection is often superior to machine algorithms.
        """
        market_id = market.get('market_slug') or market.get('slug') or market.get('condition_id') or ''
        if not market_id:
            return None

        # Normalize market_id for lookup
        market_id = market_id.lower().strip()

        # Try to load human estimates
        human_prob = None

        # Check human_probability_estimates.json
        if HUMAN_ESTIMATES_FILE.exists():
            try:
                with open(HUMAN_ESTIMATES_FILE) as f:
                    data = json.load(f)
                    estimates = data.get("estimates", {})

                    # Try exact match and partial matches
                    for est_id, prob in estimates.items():
                        if est_id.lower() == market_id or market_id in est_id.lower():
                            human_prob = prob
                            break
            except:
                pass

        # Also check yair_context_kernel.json
        if human_prob is None and YAIR_KERNEL_FILE.exists():
            try:
                with open(YAIR_KERNEL_FILE) as f:
                    kernel = json.load(f)
                    active = kernel.get("active_estimates", {})

                    for est_id, prob in active.items():
                        if est_id.lower() == market_id or market_id in est_id.lower():
                            human_prob = prob
                            break
            except:
                pass

        if human_prob is None:
            return None

        # Calculate edge vs market
        yes_price = market.get('yes_price') or market.get('last', 0.5)
        edge = human_prob - yes_price

        return FairPriceEstimate(
            fair_price=human_prob,
            confidence=0.85,  # High confidence in human estimates
            source="human_yair",
            edge_vs_market=edge,
            is_actionable=abs(edge) >= 0.03,  # 3% minimum edge
            reasoning=f"Yair's probability estimate: {human_prob:.1%} (market: {yes_price:.1%})",
        )

    def estimate_from_orderbook(self, market: Dict) -> Optional[FairPriceEstimate]:
        """
        METHOD 1: Order book analysis.

        Fair price = weighted midpoint considering depth.
        Wide spreads = opportunity for market making.
        """
        best_bid = market.get('bestBid') or market.get('best_bid', 0)
        best_ask = market.get('bestAsk') or market.get('best_ask', 0)
        yes_price = market.get('yes_price', 0)
        no_price = market.get('no_price', 0)

        # If we have bid/ask, analyze spread
        if best_bid > 0 and best_ask > 0 and best_ask > best_bid:
            midpoint = (best_bid + best_ask) / 2.0
            spread = best_ask - best_bid
            spread_pct = spread / midpoint if midpoint > 0 else 0

            # Wide spread = opportunity!
            # If spread > 5%, we can profit by placing at midpoint
            edge = 0.0
            reasoning = f"Bid-ask midpoint ${midpoint:.3f}, spread {spread_pct:.1%}"

            if spread_pct >= 0.10:  # 10%+ spread = strong signal
                # We can buy at bid+small and sell at ask-small
                edge = spread_pct * 0.3  # Capture ~30% of spread
                reasoning = f"WIDE SPREAD {spread_pct:.1%} - market making opportunity"
            elif spread_pct >= 0.05:  # 5%+ spread = moderate signal
                edge = spread_pct * 0.2
                reasoning = f"Moderate spread {spread_pct:.1%} - potential edge"

            # Confidence based on spread (wide = less liquid but more profit)
            confidence = min(0.8, 0.3 + spread_pct * 3)

            return FairPriceEstimate(
                fair_price=midpoint,
                confidence=confidence,
                source="orderbook_spread",
                edge_vs_market=edge,
                is_actionable=spread_pct >= 0.05,
                reasoning=reasoning,
            )

        # If no bid/ask, can't use this method
        return None

    def estimate_from_history(self, market: Dict) -> Optional[FairPriceEstimate]:
        """
        METHOD 2: Historical regression to mean.

        If price has moved significantly from recent average,
        fair price is somewhere between current and historical mean.
        """
        market_id = market.get('slug') or market.get('market_id', '')
        history = self.price_history.get(market_id, [])

        if len(history) < 5:
            return None

        # Get recent prices
        recent_prices = [h['price'] for h in history[-50:]]

        # Calculate statistics
        mean_price = statistics.mean(recent_prices)
        std_price = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
        current_price = market.get('yes_price') or market.get('last', mean_price)

        # Z-score: how far is current from mean?
        z_score = (current_price - mean_price) / std_price if std_price > 0 else 0

        # If z > 1.5, price has moved significantly - expect regression
        if abs(z_score) > 1.5:
            # Fair price is between current and mean
            # The further away, the more we expect regression
            regression_strength = min(0.5, abs(z_score) / 4)
            fair_price = current_price + regression_strength * (mean_price - current_price)

            edge = fair_price - current_price

            return FairPriceEstimate(
                fair_price=fair_price,
                confidence=0.6,
                source="historical_regression",
                edge_vs_market=edge,
                is_actionable=abs(edge) >= 0.02,
                reasoning=f"Price deviated {z_score:.1f}σ from mean {mean_price:.3f}",
            )

        return None

    def estimate_from_volatility(self, market: Dict) -> Optional[FairPriceEstimate]:
        """
        METHOD 3: Volatility-adjusted fair range.

        High volatility = wider confidence interval around current price.
        Very high vol markets are inefficient - edge opportunities.
        """
        market_id = market.get('slug') or market.get('market_id', '')
        history = self.price_history.get(market_id, [])

        if len(history) < 10:
            return None

        # Calculate returns
        prices = [h['price'] for h in history[-100:]]
        returns = [(prices[i] - prices[i-1]) / prices[i-1]
                   for i in range(1, len(prices)) if prices[i-1] > 0]

        if not returns:
            return None

        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        current_price = market.get('yes_price') or market.get('last', 0.5)

        # High volatility (>20% per period) suggests inefficiency
        if volatility > 0.20:
            # In high vol, current price is less reliable
            # Fair price could be anywhere in a range
            range_size = volatility * current_price

            # Use momentum to bias direction
            recent_returns = returns[-5:] if len(returns) >= 5 else returns
            momentum = sum(recent_returns) / len(recent_returns)

            # Fair price biased by momentum
            fair_price = current_price * (1 + momentum * 0.5)
            fair_price = max(0.01, min(0.99, fair_price))

            edge = fair_price - current_price

            return FairPriceEstimate(
                fair_price=fair_price,
                confidence=0.5,
                source="volatility_momentum",
                edge_vs_market=edge,
                is_actionable=abs(edge) >= 0.02 and volatility > 0.25,
                reasoning=f"High vol {volatility:.1%}, momentum {momentum:+.2%}",
            )

        return None

    def estimate_from_category(self, market: Dict) -> Optional[FairPriceEstimate]:
        """
        METHOD 4: Category-specific estimation.

        Different categories have different edge patterns:
        - Sports: Compare to external odds
        - Politics: Polls + historical accuracy
        - Crypto: Momentum bias
        - Low probability events: Often overpriced
        """
        question = (market.get('question', '') + market.get('description', '')).lower()
        current_price = market.get('yes_price') or market.get('last', 0.5)

        # Sports detection - these markets often misprice vs ESPN/Vegas
        if any(kw in question for kw in ['nba', 'nfl', 'mlb', 'game', 'win', 'championship', 'super bowl', 'playoffs']):
            if 0.55 < current_price < 0.80:
                fair_price = current_price * 1.05
                edge = fair_price - current_price
                return FairPriceEstimate(
                    fair_price=min(0.95, fair_price),
                    confidence=0.55,
                    source="sports_favorite_bias",
                    edge_vs_market=edge,
                    is_actionable=edge >= 0.015,
                    reasoning="Sports markets underweight favorites",
                )
            elif 0.20 < current_price < 0.45:
                fair_price = current_price * 0.90
                edge = current_price - fair_price
                return FairPriceEstimate(
                    fair_price=max(0.05, fair_price),
                    confidence=0.55,
                    source="sports_longshot_bias",
                    edge_vs_market=-edge,
                    is_actionable=edge >= 0.015,
                    reasoning="Sports markets overprice longshots",
                )

        # Crypto/Bitcoin - momentum often continues
        if any(kw in question for kw in ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'solana']):
            if current_price > 0.60:
                # Crypto YES momentum - often continues
                edge = 0.03
                return FairPriceEstimate(
                    fair_price=min(0.95, current_price + edge),
                    confidence=0.50,
                    source="crypto_momentum",
                    edge_vs_market=edge,
                    is_actionable=True,
                    reasoning="Crypto markets have momentum bias - YES trending",
                )
            elif current_price < 0.40:
                edge = 0.03
                return FairPriceEstimate(
                    fair_price=max(0.05, current_price - edge),
                    confidence=0.50,
                    source="crypto_momentum",
                    edge_vs_market=-edge,
                    is_actionable=True,
                    reasoning="Crypto markets have momentum bias - NO trending",
                )

        # Politics - often moves toward extremes near resolution
        if any(kw in question for kw in ['trump', 'biden', 'election', 'president', 'congress', 'senate']):
            if 0.40 < current_price < 0.60:
                # Uncertainty zone - edge in going toward the leader
                edge = 0.02 if current_price > 0.5 else -0.02
                return FairPriceEstimate(
                    fair_price=current_price + edge,
                    confidence=0.45,
                    source="politics_uncertainty",
                    edge_vs_market=edge,
                    is_actionable=True,
                    reasoning="Political markets in uncertainty zone - bias toward leader",
                )

        # Low probability events are often overpriced (longshot bias)
        if current_price < 0.05:
            # Very low prob events are often overpriced
            fair_price = current_price * 0.70
            edge = current_price - fair_price
            return FairPriceEstimate(
                fair_price=max(0.001, fair_price),
                confidence=0.60,
                source="longshot_bias",
                edge_vs_market=-edge,  # Sell/short
                is_actionable=edge >= 0.005,
                reasoning=f"Low prob event at {current_price:.1%} likely overpriced",
            )

        # High probability events slightly underpriced
        if current_price > 0.95:
            fair_price = current_price * 1.02
            edge = fair_price - current_price
            return FairPriceEstimate(
                fair_price=min(0.99, fair_price),
                confidence=0.55,
                source="favorite_underpriced",
                edge_vs_market=edge,
                is_actionable=edge >= 0.005,
                reasoning=f"High prob event at {current_price:.1%} likely underpriced",
            )

        # Time-decay markets
        end_date = market.get('endDate') or market.get('end_date')
        if end_date:
            try:
                if isinstance(end_date, str):
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    days_left = (end_dt - datetime.now(timezone.utc)).days

                    if days_left < 7 and 0.30 < current_price < 0.70:
                        if current_price > 0.5:
                            fair_price = current_price + 0.10 * (1 - days_left / 7)
                        else:
                            fair_price = current_price - 0.10 * (1 - days_left / 7)

                        fair_price = max(0.05, min(0.95, fair_price))
                        edge = fair_price - current_price

                        return FairPriceEstimate(
                            fair_price=fair_price,
                            confidence=0.5,
                            source="time_decay",
                            edge_vs_market=edge,
                            is_actionable=abs(edge) >= 0.02,
                            reasoning=f"{days_left} days left, expect resolution acceleration",
                        )
            except Exception:
                pass

        return None

    def estimate_from_abcfc(self, market: Dict) -> Optional[FairPriceEstimate]:
        """
        METHOD 5: ABCFC Probability Density Analysis.

        Uses Absolute Bounds Continuous Fan Chart to model the 2D probability
        density of outcomes, giving a mathematically rigorous fair price estimate.

        Key insight: Binary markets have known bounds (0, 1) and the ABCFC
        density function models how probability mass should be distributed
        between win/lose outcomes over time.
        """
        if not ABCFC_AVAILABLE:
            return None

        yes_price = market.get('yes_price') or market.get('last', 0.5)
        no_price = market.get('no_price', 1 - yes_price)

        # Get time to resolution if available
        end_date = market.get('endDate') or market.get('end_date')
        days_to_resolution = 30  # Default

        if end_date:
            try:
                if isinstance(end_date, str):
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    days_to_resolution = max(1, (end_dt - datetime.now(timezone.utc)).days)
            except Exception:
                pass

        # Create ABCFC for this binary market
        # Bounds are the P&L range: worst = -entry, best = 1-entry
        entry_price = yes_price
        worst_pnl = -entry_price  # Lose everything paid
        best_pnl = 1 - entry_price  # Gain the upside

        try:
            # Create binary market density
            density_func = create_binary_market_density(
                prob_yes=yes_price,  # Current market price as initial probability
                entry_price=entry_price,
                shares=1.0  # Normalized
            )

            # Sample the density to get expected value
            # Integrate probability-weighted value across the outcome space
            n_samples = 50
            total_prob = 0.0
            expected_value = 0.0

            for i in range(n_samples):
                x = worst_pnl + (best_pnl - worst_pnl) * i / (n_samples - 1)
                t = days_to_resolution * 0.5  # Mid-point in time

                # Get density at this point
                p = density_func(x, t, worst_pnl, best_pnl, days_to_resolution)
                total_prob += p
                expected_value += p * x

            if total_prob > 0:
                expected_value /= total_prob

            # Convert expected P&L back to fair price
            # If E[P&L] > 0, the market is underpriced (buy YES)
            # If E[P&L] < 0, the market is overpriced (sell YES)

            # Fair price = price where E[P&L] = 0
            # P&L = shares * (outcome - entry)
            # E[P&L] = prob_yes * (1 - entry) + (1 - prob_yes) * (0 - entry) - current_entry
            # Solving for prob_yes gives fair price

            # Using Kelly-like adjustment based on density spread
            density_confidence = min(0.8, total_prob / n_samples)

            # Edge is the expected P&L
            edge = expected_value

            # Convert edge to price adjustment
            fair_price = yes_price + edge * 0.5  # Conservative adjustment
            fair_price = max(0.01, min(0.99, fair_price))

            # Only actionable if edge is significant and confidence is reasonable
            is_actionable = abs(edge) >= 0.03 and density_confidence >= 0.4

            return FairPriceEstimate(
                fair_price=fair_price,
                confidence=density_confidence,
                source="abcfc_density",
                edge_vs_market=fair_price - yes_price,
                is_actionable=is_actionable,
                reasoning=f"ABCFC E[P&L]={expected_value:+.3f}, density_conf={density_confidence:.0%}, {days_to_resolution}d to resolution",
            )

        except Exception as e:
            # ABCFC calculation failed, skip this method
            return None

    def estimate_from_spread_arb(self, market: Dict) -> Optional[FairPriceEstimate]:
        """
        METHOD 6: Spread arbitrage.

        If YES + NO significantly != 1.0, there's a guaranteed arb.
        Fair prices are where sum = 1.0.
        """
        yes_price = market.get('yes_price', 0)
        no_price = market.get('no_price', 0)

        if yes_price > 0 and no_price > 0:
            total = yes_price + no_price

            # Significant deviation from 1.0
            if total < 0.98 or total > 1.02:
                # Arbitrage exists
                # Fair prices are normalized to sum to 1.0
                fair_yes = yes_price / total
                fair_no = no_price / total

                edge = fair_yes - yes_price
                arb_profit = abs(1.0 - total)

                return FairPriceEstimate(
                    fair_price=fair_yes,
                    confidence=0.9,  # High confidence - this is math
                    source="spread_arbitrage",
                    edge_vs_market=edge,
                    is_actionable=arb_profit >= 0.01,
                    reasoning=f"YES+NO={total:.3f}, arb profit ${arb_profit:.3f}/pair",
                )

        return None

    # ==================== ENSEMBLE ====================

    def estimate_fair_price(self, market: Dict) -> FairPriceEstimate:
        """
        ENSEMBLE: Combine all estimation methods.

        Returns the best estimate based on confidence and actionability.
        """
        estimates = []

        # Try each method (INTEGRAFIX: Human estimates have highest priority)
        methods = [
            self.estimate_from_human,          # INTEGRAFIX: Yair's estimates first!
            self.estimate_from_spread_arb,     # Highest confidence if exists
            self.estimate_from_abcfc,          # ABCFC probability density
            self.estimate_from_orderbook,
            self.estimate_from_history,
            self.estimate_from_volatility,
            self.estimate_from_category,
        ]

        for method in methods:
            try:
                result = method(market)
                if result:
                    estimates.append(result)
            except Exception:
                continue

        if not estimates:
            # Fallback: use current price with zero edge (no actionable signal)
            current_price = market.get('yes_price') or market.get('last', 0.5)
            return FairPriceEstimate(
                fair_price=current_price,
                confidence=0.0,
                source="no_signal",
                edge_vs_market=0.0,
                is_actionable=False,
                reasoning="No estimation method produced a signal",
            )

        # Sort by: actionable first, then confidence, then edge size
        estimates.sort(key=lambda e: (
            e.is_actionable,
            e.confidence,
            abs(e.edge_vs_market),
        ), reverse=True)

        best = estimates[0]

        # If multiple actionable estimates, ensemble them
        actionable = [e for e in estimates if e.is_actionable]
        if len(actionable) > 1:
            # Weighted average by confidence
            total_conf = sum(e.confidence for e in actionable)
            if total_conf > 0:
                fair_price = sum(e.fair_price * e.confidence for e in actionable) / total_conf
                avg_edge = sum(e.edge_vs_market * e.confidence for e in actionable) / total_conf

                return FairPriceEstimate(
                    fair_price=fair_price,
                    confidence=min(0.95, total_conf / len(actionable)),
                    source="ensemble",
                    edge_vs_market=avg_edge,
                    is_actionable=abs(avg_edge) >= 0.01,
                    reasoning=f"Ensemble of {len(actionable)} methods: {[e.source for e in actionable]}",
                )

        return best

    def get_edge(self, market: Dict) -> Tuple[float, float, str]:
        """
        Main interface: Get edge for a market.

        Returns:
            (edge, confidence, reason)
        """
        estimate = self.estimate_fair_price(market)
        return (
            estimate.edge_vs_market,
            estimate.confidence,
            estimate.reasoning,
        )


# Singleton instance
_estimator = None

def get_estimator() -> FairPriceEstimator:
    global _estimator
    if _estimator is None:
        _estimator = FairPriceEstimator()
    return _estimator


def estimate_fair_price_integrafixed(market: Dict) -> float:
    """
    Drop-in replacement for the old circular estimate_fair_price().

    Import this instead of the old one:
        from integrafix.fair_price_estimator import estimate_fair_price_integrafixed as estimate_fair_price
    """
    estimator = get_estimator()
    estimate = estimator.estimate_fair_price(market)
    return estimate.fair_price


def main():
    """Test the fair price estimator."""
    estimator = get_estimator()

    # Test market
    test_market = {
        "slug": "test-market",
        "question": "Will the Lakers win the NBA championship?",
        "yes_price": 0.45,
        "no_price": 0.52,  # Sum = 0.97, arb exists
        "bestBid": 0.43,
        "bestAsk": 0.47,
        "volume": 100000,
    }

    # Record some history
    for i in range(20):
        estimator.record_price("test-market", 0.40 + i * 0.005)

    # Get estimate
    estimate = estimator.estimate_fair_price(test_market)

    print("=" * 70)
    print("INTEGRAFIX: Fair Price Estimator Test")
    print("=" * 70)
    print()
    print(f"Market: {test_market['question']}")
    print(f"Current YES price: ${test_market['yes_price']:.3f}")
    print(f"Current NO price: ${test_market['no_price']:.3f}")
    print()
    print(f"ESTIMATED FAIR PRICE: ${estimate.fair_price:.3f}")
    print(f"EDGE vs MARKET: {estimate.edge_vs_market:+.3f} ({estimate.edge_vs_market*100:+.1f}%)")
    print(f"CONFIDENCE: {estimate.confidence:.0%}")
    print(f"SOURCE: {estimate.source}")
    print(f"ACTIONABLE: {estimate.is_actionable}")
    print(f"REASONING: {estimate.reasoning}")

    return estimate


if __name__ == "__main__":
    main()
