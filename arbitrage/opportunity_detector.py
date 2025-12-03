"""
Arbitrage Opportunity Detector
==============================

Core arbitrage detection engine that:
1. Fetches data from all platforms
2. Matches same events across platforms
3. Calculates arbitrage opportunities
4. Ranks and filters opportunities by profitability

Zero-Risk Arbitrage Math:
=========================

For binary prediction markets (YES/NO):
- Platform A: YES costs P_a, pays $1 if event happens
- Platform B: NO costs (1 - P_b), pays $1 if event doesn't happen

Arbitrage exists when:
  P_a + (1 - P_b) < 1.0

Example:
  Polymarket YES = $0.52
  Kalshi YES = $0.48 (so NO = $0.52)

  Buy YES on Kalshi: $0.48
  Buy NO on Polymarket: $0.48 (1 - 0.52)
  Total cost: $0.96

  Outcome A (event happens): Win $1 from Kalshi YES = $0.04 profit
  Outcome B (event doesn't): Win $1 from Polymarket NO = $0.04 profit

  Guaranteed profit: 4.17% (0.04/0.96)
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .types import (
    Platform,
    ArbitrageType,
    ArbitrageOpportunity,
    PredictionMarket,
    CryptoPrice,
    MatchedEvent,
)
from .event_matcher import EventMatcher
from .fetchers.polymarket import PolymarketFetcher
from .fetchers.kalshi import KalshiFetcher
from .fetchers.crypto_exchanges import CryptoFetcher

logger = logging.getLogger(__name__)


class ArbitrageDetector:
    """
    Main arbitrage detection engine.

    Coordinates fetchers, matchers, and calculators to find
    zero-risk arbitrage opportunities across platforms.
    """

    # Minimum profit threshold to report (after fees)
    MIN_PROFIT_PCT = 0.005  # 0.5% minimum net profit

    # Estimated fees by platform (as decimal)
    PLATFORM_FEES = {
        Platform.POLYMARKET: 0.02,   # ~2% effective fee
        Platform.KALSHI: 0.01,       # ~1% fee
        Platform.DRAFTKINGS: 0.05,   # ~5% vig
        Platform.FANDUEL: 0.05,      # ~5% vig
    }

    def __init__(
        self,
        polymarket_cache: Optional[Path] = None,
        kalshi_api_key: Optional[str] = None,
        manual_mappings: Optional[Path] = None,
        min_profit_pct: float = 0.005,
    ):
        """
        Initialize the arbitrage detector.

        Args:
            polymarket_cache: Path to cached Polymarket data
            kalshi_api_key: Optional Kalshi API key
            manual_mappings: Path to manual market mappings file
            min_profit_pct: Minimum profit % to report (default 0.5%)
        """
        self.min_profit_pct = min_profit_pct

        # Initialize fetchers
        self.polymarket = PolymarketFetcher(cache_path=polymarket_cache)
        self.kalshi = KalshiFetcher(api_key=kalshi_api_key)
        self.crypto = CryptoFetcher()

        # Initialize matcher
        self.matcher = EventMatcher(manual_mappings_path=manual_mappings)

    def scan_all(self) -> Dict[str, List[ArbitrageOpportunity]]:
        """
        Scan all platforms for arbitrage opportunities.

        Returns:
            Dict with keys 'prediction_markets', 'crypto' containing opportunities
        """
        results = {
            'prediction_markets': [],
            'crypto': [],
            'scan_time': datetime.now(timezone.utc).isoformat(),
        }

        # Scan prediction markets
        try:
            pm_opps = self.scan_prediction_markets()
            results['prediction_markets'] = pm_opps
            logger.info(f"Found {len(pm_opps)} prediction market arbitrage opportunities")
        except Exception as e:
            logger.error(f"Prediction market scan failed: {e}")

        # Scan crypto
        try:
            crypto_opps = self.scan_crypto()
            results['crypto'] = crypto_opps
            logger.info(f"Found {len(crypto_opps)} crypto arbitrage opportunities")
        except Exception as e:
            logger.error(f"Crypto scan failed: {e}")

        return results

    def scan_prediction_markets(self) -> List[ArbitrageOpportunity]:
        """
        Scan prediction markets (Polymarket, Kalshi) for arbitrage.

        Returns:
            List of arbitrage opportunities sorted by profit potential
        """
        opportunities = []

        # Fetch markets from both platforms
        logger.info("Fetching Polymarket markets...")
        polymarket_markets = self.polymarket.fetch_markets(active_only=True)

        logger.info("Fetching Kalshi markets...")
        kalshi_markets = self.kalshi.fetch_markets(status="open")

        if not polymarket_markets and not kalshi_markets:
            logger.warning("No markets fetched from either platform")
            return []

        # Match same events across platforms
        markets_by_platform = {
            Platform.POLYMARKET: polymarket_markets,
            Platform.KALSHI: kalshi_markets,
        }

        matched_events = self.matcher.match_markets(markets_by_platform)
        logger.info(f"Matched {len(matched_events)} events across platforms")

        # Calculate arbitrage for each matched event
        for event in matched_events:
            opp = self._calculate_binary_arb(event)
            if opp and opp.profit_pct_net >= self.min_profit_pct:
                opportunities.append(opp)

        # Also check for single-platform spread opportunities
        for market in polymarket_markets:
            opp = self._check_spread_arb(market)
            if opp and opp.profit_pct_net >= self.min_profit_pct:
                opportunities.append(opp)

        # Sort by net profit (highest first)
        opportunities.sort(key=lambda x: x.profit_pct_net, reverse=True)

        return opportunities

    def _calculate_binary_arb(
        self,
        event: MatchedEvent,
    ) -> Optional[ArbitrageOpportunity]:
        """
        Calculate arbitrage opportunity for a binary event.

        The math:
        - If we can buy YES on platform A and NO on platform B
          for less than $1 total, we have guaranteed profit.
        """
        if len(event.markets) < 2:
            return None

        # Find best YES and NO prices across platforms
        best_yes_market = None
        best_yes_price = float('inf')

        best_no_market = None
        best_no_price = float('inf')

        for market in event.markets:
            # Use ask price if available, else mid price
            yes_price = market.best_ask_yes or market.yes_price
            no_price = market.best_ask_no or market.no_price

            if yes_price < best_yes_price:
                best_yes_price = yes_price
                best_yes_market = market

            if no_price < best_no_price:
                best_no_price = no_price
                best_no_market = market

        if not best_yes_market or not best_no_market:
            return None

        # Check if same platform (no arb possible within same platform)
        if best_yes_market.platform == best_no_market.platform:
            return None

        # Calculate combined cost
        total_cost = best_yes_price + best_no_price

        # If total cost >= 1, no arbitrage
        if total_cost >= 1.0:
            return None

        # Calculate gross profit
        gross_profit_pct = (1.0 - total_cost) / total_cost

        # Estimate fees
        yes_fee = self.PLATFORM_FEES.get(best_yes_market.platform, 0.02)
        no_fee = self.PLATFORM_FEES.get(best_no_market.platform, 0.02)
        total_fees = (best_yes_price * yes_fee) + (best_no_price * no_fee)

        # Net profit after fees
        net_profit = (1.0 - total_cost) - total_fees
        net_profit_pct = net_profit / total_cost if total_cost > 0 else 0

        if net_profit_pct <= 0:
            return None

        # Build opportunity
        legs = [
            {
                'platform': best_yes_market.platform.value,
                'market_id': best_yes_market.market_id,
                'side': 'YES',
                'price': best_yes_price,
                'size_pct': best_yes_price / total_cost,
                'fees_est': best_yes_price * yes_fee,
            },
            {
                'platform': best_no_market.platform.value,
                'market_id': best_no_market.market_id,
                'side': 'NO',
                'price': best_no_price,
                'size_pct': best_no_price / total_cost,
                'fees_est': best_no_price * no_fee,
            },
        ]

        # Assess execution risk
        risk_factors = []
        if event.match_confidence < 0.95:
            risk_factors.append(f"Match confidence only {event.match_confidence:.1%}")
        if not best_yes_market.liquidity or best_yes_market.liquidity < 1000:
            risk_factors.append("Low liquidity on YES side")
        if not best_no_market.liquidity or best_no_market.liquidity < 1000:
            risk_factors.append("Low liquidity on NO side")

        execution_risk = "low"
        if len(risk_factors) > 2:
            execution_risk = "high"
        elif len(risk_factors) > 0:
            execution_risk = "medium"

        # Estimate max size based on liquidity
        min_liquidity = min(
            best_yes_market.liquidity or 1000,
            best_no_market.liquidity or 1000
        )
        max_size = min_liquidity * 0.1  # Don't take more than 10% of liquidity

        return ArbitrageOpportunity(
            opportunity_id=str(uuid.uuid4())[:8],
            arb_type=ArbitrageType.TWO_WAY_BINARY,
            profit_pct=gross_profit_pct,
            profit_pct_net=net_profit_pct,
            matched_event=event,
            legs=legs,
            execution_risk=execution_risk,
            risk_factors=risk_factors,
            max_size_usd=max_size,
            recommended_size_usd=min(max_size * 0.5, 100),  # Conservative
            detected_at=datetime.now(timezone.utc),
            expires_at=event.markets[0].closes_at,
        )

    def _check_spread_arb(
        self,
        market: PredictionMarket,
    ) -> Optional[ArbitrageOpportunity]:
        """
        Check for spread arbitrage within a single platform.

        This occurs when YES + NO < 1.0 (underround), which can happen
        during volatile market conditions.
        """
        total = market.yes_price + market.no_price

        if total >= 1.0:
            return None

        # Underround! This is rare but possible
        gross_profit = (1.0 - total) / total

        # Single platform fee (charged on both sides)
        fee_rate = self.PLATFORM_FEES.get(market.platform, 0.02)
        total_fees = total * fee_rate * 2  # Fee on buy and on payout

        net_profit = (1.0 - total) - total_fees
        net_profit_pct = net_profit / total if total > 0 else 0

        if net_profit_pct <= 0:
            return None

        legs = [
            {
                'platform': market.platform.value,
                'market_id': market.market_id,
                'side': 'YES',
                'price': market.yes_price,
                'size_pct': market.yes_price / total,
            },
            {
                'platform': market.platform.value,
                'market_id': market.market_id,
                'side': 'NO',
                'price': market.no_price,
                'size_pct': market.no_price / total,
            },
        ]

        # Create a synthetic matched event for reporting
        event = MatchedEvent(
            event_id=f"spread-{market.market_id[:8]}",
            canonical_question=market.question,
            markets=[market],
            match_confidence=1.0,
            match_method="spread",
        )

        return ArbitrageOpportunity(
            opportunity_id=str(uuid.uuid4())[:8],
            arb_type=ArbitrageType.TWO_WAY_BINARY,
            profit_pct=gross_profit,
            profit_pct_net=net_profit_pct,
            matched_event=event,
            legs=legs,
            execution_risk="low",  # Same platform = lower execution risk
            risk_factors=["Single platform spread arb (rare, may close quickly)"],
            max_size_usd=market.liquidity * 0.1 if market.liquidity else 100,
            detected_at=datetime.now(timezone.utc),
        )

    def scan_crypto(self) -> List[ArbitrageOpportunity]:
        """
        Scan crypto exchanges for price arbitrage.

        Simple spot arbitrage:
        - Buy asset on exchange with lower ask
        - Sell on exchange with higher bid
        - Profit = bid_B - ask_A - fees
        """
        opportunities = []

        # Fetch prices from all exchanges
        logger.info("Fetching crypto prices from all exchanges...")
        prices_by_pair = self.crypto.fetch_all_prices()

        for pair, prices in prices_by_pair.items():
            if len(prices) < 2:
                continue

            # Find best buy (lowest ask) and best sell (highest bid)
            best_buy = min(prices, key=lambda p: p.ask_price)
            best_sell = max(prices, key=lambda p: p.bid_price)

            # Skip if same exchange
            if best_buy.platform == best_sell.platform:
                continue

            # Calculate profit
            gross_profit_pct = (best_sell.bid_price - best_buy.ask_price) / best_buy.ask_price

            # Account for fees (taker on both sides)
            buy_fee = best_buy.taker_fee
            sell_fee = best_sell.taker_fee
            net_profit_pct = gross_profit_pct - buy_fee - sell_fee

            if net_profit_pct <= self.min_profit_pct:
                continue

            # Risk factors
            risk_factors = []

            # Transfer time risk (price might change during transfer)
            risk_factors.append("Transfer time risk: ~10-60 min for most coins")

            # Size limitations
            max_size = min(
                (best_buy.bid_size or 1) * best_buy.ask_price,
                (best_sell.ask_size or 1) * best_sell.bid_price,
            )

            legs = [
                {
                    'platform': best_buy.platform.value,
                    'action': 'BUY',
                    'pair': pair,
                    'price': best_buy.ask_price,
                    'fee_pct': buy_fee,
                },
                {
                    'platform': best_sell.platform.value,
                    'action': 'SELL',
                    'pair': pair,
                    'price': best_sell.bid_price,
                    'fee_pct': sell_fee,
                },
            ]

            opp = ArbitrageOpportunity(
                opportunity_id=str(uuid.uuid4())[:8],
                arb_type=ArbitrageType.SIMPLE_SPOT,
                profit_pct=gross_profit_pct,
                profit_pct_net=net_profit_pct,
                crypto_prices=[best_buy, best_sell],
                legs=legs,
                execution_risk="high",  # Crypto arb has transfer risk
                risk_factors=risk_factors,
                max_size_usd=max_size,
                recommended_size_usd=min(max_size * 0.2, 1000),
                detected_at=datetime.now(timezone.utc),
            )
            opportunities.append(opp)

        # Sort by net profit
        opportunities.sort(key=lambda x: x.profit_pct_net, reverse=True)

        return opportunities

    def get_report(self, opportunities: Dict[str, List]) -> str:
        """Generate human-readable report of opportunities"""
        lines = []
        lines.append("=" * 60)
        lines.append("ARBITRAGE OPPORTUNITY REPORT")
        lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("=" * 60)

        # Prediction Markets
        pm_opps = opportunities.get('prediction_markets', [])
        lines.append(f"\n📊 PREDICTION MARKETS ({len(pm_opps)} opportunities)")
        lines.append("-" * 40)

        if not pm_opps:
            lines.append("No arbitrage opportunities found.")
        else:
            for opp in pm_opps[:10]:  # Top 10
                lines.append(f"\n[{opp.profit_pct_net:+.2%} NET] {opp.arb_type.value}")
                if opp.matched_event:
                    lines.append(f"  Event: {opp.matched_event.canonical_question[:70]}...")
                for leg in opp.legs:
                    lines.append(f"  → {leg['side']} on {leg['platform']} @ ${leg['price']:.2f}")
                lines.append(f"  Risk: {opp.execution_risk} | Max: ${opp.max_size_usd:.0f}")

        # Crypto
        crypto_opps = opportunities.get('crypto', [])
        lines.append(f"\n₿ CRYPTO ({len(crypto_opps)} opportunities)")
        lines.append("-" * 40)

        if not crypto_opps:
            lines.append("No arbitrage opportunities found.")
        else:
            for opp in crypto_opps[:10]:  # Top 10
                lines.append(f"\n[{opp.profit_pct_net:+.2%} NET] {opp.arb_type.value}")
                for leg in opp.legs:
                    lines.append(f"  → {leg['action']} {leg['pair']} on {leg['platform']} @ ${leg['price']:.2f}")
                lines.append(f"  Risk: {opp.execution_risk} | Max: ${opp.max_size_usd:.0f}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def save_opportunities(
        self,
        opportunities: Dict[str, List],
        path: Path,
    ) -> None:
        """Save opportunities to JSON file"""
        output = {
            'scan_time': opportunities.get('scan_time'),
            'prediction_markets': [
                opp.to_dict() for opp in opportunities.get('prediction_markets', [])
            ],
            'crypto': [
                opp.to_dict() for opp in opportunities.get('crypto', [])
            ],
        }

        # Atomic write
        tmp_path = path.with_suffix('.tmp')
        with open(tmp_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        tmp_path.replace(path)

        logger.info(f"Saved opportunities to {path}")
