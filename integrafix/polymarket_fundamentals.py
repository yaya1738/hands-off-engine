#!/usr/bin/env python3
"""
INTEGRAFIX: Polymarket Fundamentals
====================================

All Yair's Polymarket-specific knowledge encoded for ABCFC-HFT system.

From POLYMARKET_SPECIFIC.md + MARKET_FUNDAMENTALS.md:

PLATFORM ADVANTAGES:
- Zero trading fees (capture smaller edges)
- Wallet transparency (track smart money)
- Reusable collateral (infinite patience)
- UMA resolution (decentralized oracle)

MARKET FUNDAMENTALS:
- Maker vs Taker distinction (be the house)
- L2 order book depth (the REAL data)
- Self-impact awareness (you ARE the market)
- Position holder analysis (know your counterparty)

KEY PRINCIPLES:
- "Be the house, not the gambler"
- "The price is a LIE" - there's a BOOK of prices
- "Patient liquidity provider wins"
- "Zero sum: one man's pitfall = another's luck"

Created by: Yair Siegel
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


class OrderType(Enum):
    """Order type determines maker/taker."""
    LIMIT = "limit"    # MAKING - patient, rebates
    MARKET = "market"  # TAKING - urgent, pays spread


class TraderType(Enum):
    """Trader classification for flow analysis."""
    SMART_MONEY = "smart_money"    # Profitable history
    DUMB_MONEY = "dumb_money"      # Losing history
    WHALE = "whale"                # Large positions
    RETAIL = "retail"              # Small positions
    UNKNOWN = "unknown"


@dataclass
class WalletProfile:
    """Profile of a Polymarket wallet/trader."""
    address: str
    username: Optional[str] = None
    win_rate: float = 0.5
    total_pnl: float = 0.0
    trade_count: int = 0
    avg_position_size: float = 0.0
    trader_type: TraderType = TraderType.UNKNOWN
    categories_active: List[str] = field(default_factory=list)
    last_seen: Optional[str] = None


@dataclass
class CollateralPosition:
    """
    Reusable collateral position tracker.

    From POLYMARKET_SPECIFIC.md:
    - Same cash can collateralize MULTIPLE open limit orders
    - Only locked when order actually executes
    """
    total_collateral: float = 0.0
    allocated_to_orders: float = 0.0  # Sum of all limit order sizes
    actually_locked: float = 0.0       # Actually filled/committed

    @property
    def available(self) -> float:
        """Available for new orders (can exceed total due to reuse)."""
        return self.total_collateral - self.actually_locked

    @property
    def utilization(self) -> float:
        """How much of collateral is at risk if all orders fill."""
        if self.total_collateral <= 0:
            return 0
        return self.allocated_to_orders / self.total_collateral

    @property
    def overcommitted(self) -> bool:
        """True if allocated > total (risky but valid)."""
        return self.allocated_to_orders > self.total_collateral


class PolymarketFundamentals:
    """
    Polymarket-specific knowledge for ABCFC-HFT.

    Implements all concepts from Yair's knowledge bases.
    """

    def __init__(self):
        self._wallet_profiles: Dict[str, WalletProfile] = {}
        self._collateral = CollateralPosition()
        self._order_matrix: Dict[str, Dict] = {}  # market_id -> orders
        self._load_state()

    # ==================== MAKER VS TAKER ====================

    def should_make_or_take(self, edge_pct: float, urgency: float,
                           book_depth: float, position_size: float) -> Dict:
        """
        INTEGRAFIX: Decide maker vs taker strategy.

        From MARKET_FUNDAMENTALS.md:
        - "Most edge comes from being the maker, not the taker"
        - "Be the house, not the gambler"
        - Makers get rebates, takers pay spread

        Args:
            edge_pct: Our edge as percentage (e.g., 15 for 15%)
            urgency: How urgent (0-1, 1 = must execute now)
            book_depth: Available liquidity in the book
            position_size: How much we want to trade

        Returns:
            Recommendation with reasoning
        """
        # Default to maker (professional traders make more than they take)
        recommendation = "maker"
        reasons = []

        # High urgency = take
        if urgency > 0.8:
            recommendation = "taker"
            reasons.append(f"High urgency ({urgency:.2f}) - need execution")

        # Edge too small for spread = make
        if edge_pct < 2:
            recommendation = "maker"
            reasons.append(f"Small edge ({edge_pct:.2f}%) - can't afford spread")

        # Large position vs thin book = make (or split)
        if book_depth > 0 and position_size > book_depth * 0.3:
            recommendation = "maker"
            reasons.append(f"Large size ({position_size}) vs depth ({book_depth}) - would move market")

        # Very high edge + decent book = take (capture opportunity)
        if edge_pct > 10 and book_depth > position_size * 2:
            recommendation = "taker"
            reasons.append(f"High edge ({edge_pct:.2f}%) with good depth - capture now")

        # Calculate cost difference
        spread_cost = position_size * 0.01  # Estimate 1% spread
        maker_rebate = position_size * 0.001  # Estimate 0.1% rebate (Polymarket has 0)

        return {
            "recommendation": recommendation,
            "reasons": reasons,
            "spread_cost_if_take": round(spread_cost, 4),
            "rebate_if_make": round(maker_rebate, 4),
            "cost_difference": round(spread_cost + maker_rebate, 4),
            "rule": "Be the house, not the gambler",
        }

    # ==================== REUSABLE COLLATERAL ====================

    def update_collateral(self, total: float):
        """Update total available collateral."""
        self._collateral.total_collateral = total

    def allocate_order(self, market_id: str, price: float, size: float) -> Dict:
        """
        INTEGRAFIX: Allocate collateral for a new limit order.

        From POLYMARKET_SPECIFIC.md:
        - "Same cash can collateralize MULTIPLE open limit orders"
        - "Only locked when order actually executes"
        - "Infinite patience enabled"

        Returns:
            Allocation status and warnings
        """
        order_value = price * size

        # Track in order matrix
        if market_id not in self._order_matrix:
            self._order_matrix[market_id] = {"orders": [], "total_allocated": 0}

        self._order_matrix[market_id]["orders"].append({
            "price": price,
            "size": size,
            "value": order_value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._order_matrix[market_id]["total_allocated"] += order_value

        # Update global allocation
        self._collateral.allocated_to_orders += order_value

        return {
            "success": True,
            "order_value": round(order_value, 2),
            "total_allocated": round(self._collateral.allocated_to_orders, 2),
            "available": round(self._collateral.available, 2),
            "utilization": round(self._collateral.utilization * 100, 1),
            "overcommitted": self._collateral.overcommitted,
            "warning": "Overcommitted - risk if multiple orders fill" if self._collateral.overcommitted else None,
            "rule": "Reusable collateral - fish everywhere with same capital",
        }

    def order_filled(self, market_id: str, price: float, size: float) -> Dict:
        """
        Mark an order as filled - now collateral is LOCKED.

        This is when the cash actually gets committed.
        """
        fill_value = price * size

        # Move from allocated to locked
        self._collateral.actually_locked += fill_value

        # Reduce allocated (order is done)
        if market_id in self._order_matrix:
            self._order_matrix[market_id]["total_allocated"] -= fill_value
        self._collateral.allocated_to_orders -= fill_value

        return {
            "success": True,
            "filled_value": round(fill_value, 2),
            "now_locked": round(self._collateral.actually_locked, 2),
            "still_available": round(self._collateral.available, 2),
            "rule": "Cash locked on fill, not on order",
        }

    def get_optimal_order_distribution(self, markets: List[Dict],
                                       total_capital: float) -> List[Dict]:
        """
        INTEGRAFIX: Distribute orders across markets optimally.

        From POLYMARKET_SPECIFIC.md:
        - "Every market has fill probability per price level"
        - "Your capital = distributed across this entire matrix"
        - Calculate EV per order placement

        Args:
            markets: List of {market_id, best_bid, best_ask, edge, fill_prob}
            total_capital: Total capital to distribute

        Returns:
            Optimal order allocation across markets
        """
        # Calculate EV for each market
        for m in markets:
            edge = m.get("edge", 0)
            fill_prob = m.get("fill_prob", 0.5)
            m["ev_per_dollar"] = edge * fill_prob

        # Sort by EV per dollar
        markets_sorted = sorted(markets, key=lambda x: x["ev_per_dollar"], reverse=True)

        # Allocate capital (all to top since collateral is reusable)
        allocations = []
        for m in markets_sorted:
            if m["ev_per_dollar"] > 0:
                allocations.append({
                    "market_id": m.get("market_id"),
                    "allocated": total_capital,  # Full capital (reusable!)
                    "ev_per_dollar": round(m["ev_per_dollar"], 4),
                    "fill_prob": m.get("fill_prob", 0.5),
                    "price_level": m.get("best_bid", 0),
                })

        return allocations

    # ==================== WALLET / SMART MONEY TRACKING ====================

    def classify_wallet(self, address: str, trade_history: List[Dict]) -> WalletProfile:
        """
        INTEGRAFIX: Classify a wallet as smart/dumb money.

        From POLYMARKET_SPECIFIC.md:
        - "Every wallet's full history visible on-chain"
        - "Build database of sharp vs dumb wallets"
        - "Follow wallets with proven edge"

        Args:
            address: Wallet address
            trade_history: List of past trades with outcomes

        Returns:
            WalletProfile with classification
        """
        profile = WalletProfile(address=address)

        if not trade_history:
            return profile

        # Calculate win rate and PnL
        wins = 0
        total_pnl = 0.0
        total_size = 0.0

        for trade in trade_history:
            pnl = trade.get("pnl", 0)
            size = trade.get("size", 0)
            total_pnl += pnl
            total_size += size
            if pnl > 0:
                wins += 1

        profile.trade_count = len(trade_history)
        profile.win_rate = wins / len(trade_history) if trade_history else 0.5
        profile.total_pnl = total_pnl
        profile.avg_position_size = total_size / len(trade_history) if trade_history else 0

        # Classify trader type
        # Lower thresholds to detect patterns earlier
        if profile.win_rate > 0.55 and profile.total_pnl > 100:
            profile.trader_type = TraderType.SMART_MONEY
        elif profile.win_rate < 0.45 and profile.total_pnl < -100:
            profile.trader_type = TraderType.DUMB_MONEY
        elif profile.avg_position_size > 10000:
            profile.trader_type = TraderType.WHALE
        elif profile.avg_position_size < 100:
            profile.trader_type = TraderType.RETAIL

        # Cache profile
        self._wallet_profiles[address] = profile

        return profile

    def should_follow_or_fade(self, wallet_address: str) -> Dict:
        """
        INTEGRAFIX: Should we follow or fade this wallet's trades?

        From POLYMARKET_SPECIFIC.md:
        - "Follow wallets with proven edge"
        - "Fade wallets that consistently lose"
        """
        profile = self._wallet_profiles.get(wallet_address)

        if not profile:
            return {
                "action": "ignore",
                "reason": "Unknown wallet - no history",
                "confidence": 0,
            }

        if profile.trader_type == TraderType.SMART_MONEY:
            return {
                "action": "follow",
                "reason": f"Smart money: {profile.win_rate:.1%} win rate, ${profile.total_pnl:,.2f} PnL",
                "confidence": 0.7,
                "rule": "Follow wallets with proven edge",
            }
        elif profile.trader_type == TraderType.DUMB_MONEY:
            return {
                "action": "fade",
                "reason": f"Dumb money: {profile.win_rate:.1%} win rate, ${profile.total_pnl:,.2f} PnL",
                "confidence": 0.6,
                "rule": "Fade wallets that consistently lose",
            }
        elif profile.trader_type == TraderType.WHALE:
            return {
                "action": "watch",
                "reason": f"Whale: avg ${profile.avg_position_size:,.2f} position",
                "confidence": 0.5,
                "rule": "Watch whales but verify conviction",
            }
        else:
            return {
                "action": "ignore",
                "reason": "Insufficient signal from this wallet",
                "confidence": 0,
            }

    # ==================== ZERO-SUM / LIQUIDITY PROVIDER ====================

    def calculate_counterparty_mistake(self, our_entry: float, our_fair_value: float,
                                       side: str) -> Dict:
        """
        INTEGRAFIX: Calculate how much counterparty is "gifting" us.

        From POLYMARKET_SPECIFIC.md:
        - "Zero Sum: One Man's Pitfall = Another's Luck"
        - "Your bad fill = someone's good fill"
        - "Their mistake = your edge"

        Args:
            our_entry: Price we're getting
            our_fair_value: Our estimate of true probability
            side: "BUY" or "SELL"

        Returns:
            Analysis of counterparty's mistake
        """
        if side == "BUY":
            # We're buying - counterparty is selling
            # Their mistake if selling below fair value
            counterparty_loss = our_fair_value - our_entry
        else:
            # We're selling - counterparty is buying
            # Their mistake if buying above fair value
            counterparty_loss = our_entry - our_fair_value

        is_gift = counterparty_loss > 0

        return {
            "counterparty_loss_per_share": round(counterparty_loss, 4),
            "is_gift": is_gift,
            "gift_pct": round(counterparty_loss * 100, 2),
            "analysis": "Patient liquidity provider wins" if is_gift else "We may be the fish",
            "rule": "One man's pitfall = another's luck",
        }

    def rate_liquidity_provision_opportunity(self, spread_pct: float, book_depth: float,
                                            avg_daily_volume: float) -> Dict:
        """
        INTEGRAFIX: Rate opportunity to be liquidity provider.

        From POLYMARKET_SPECIFIC.md:
        - "Be the patient liquidity provider"
        - "Post at 'ridiculous' levels and wait"
        - "Let desperate/dumb money come to you"

        Returns:
            Rating and strategy for LP in this market
        """
        score = 0
        reasons = []

        # Wide spread = more room to provide liquidity
        if spread_pct > 5:
            score += 3
            reasons.append(f"Wide spread ({spread_pct:.1f}%) - room to make market")
        elif spread_pct > 2:
            score += 1
            reasons.append(f"Moderate spread ({spread_pct:.1f}%)")

        # Thin book = can be the depth
        if book_depth < avg_daily_volume * 0.1:
            score += 2
            reasons.append("Thin book - can provide needed depth")

        # Active market = more opportunities
        if avg_daily_volume > 10000:
            score += 2
            reasons.append(f"Active market (${avg_daily_volume:,.0f}/day)")

        # Rating
        if score >= 5:
            rating = "excellent"
            strategy = "Deploy full LP strategy - wide spreads, patience"
        elif score >= 3:
            rating = "good"
            strategy = "Selective LP - focus on extreme levels"
        else:
            rating = "poor"
            strategy = "Tight competition - minimal LP opportunity"

        return {
            "rating": rating,
            "score": score,
            "reasons": reasons,
            "strategy": strategy,
            "rule": "Be the one with limits at 'ridiculous' levels",
        }

    # ==================== POSITION HOLDER ANALYSIS ====================

    def analyze_position_holders(self, yes_holders: List[Dict],
                                no_holders: List[Dict]) -> Dict:
        """
        INTEGRAFIX: Analyze who's on each side of the bet.

        From MARKET_FUNDAMENTALS.md:
        - "Who holds what NOW (position snapshot)"
        - "Know your counterparty"
        - "Are sharp bettors with me or against me?"

        Args:
            yes_holders: List of {address, size, cost_basis}
            no_holders: List of {address, size, cost_basis}

        Returns:
            Analysis of both sides
        """
        def analyze_side(holders: List[Dict], side_name: str) -> Dict:
            if not holders:
                return {"side": side_name, "count": 0, "total_size": 0}

            total_size = sum(h.get("size", 0) for h in holders)
            whale_count = sum(1 for h in holders if h.get("size", 0) > 10000)

            # Check for smart money
            smart_money_size = 0
            for h in holders:
                addr = h.get("address", "")
                profile = self._wallet_profiles.get(addr)
                if profile and profile.trader_type == TraderType.SMART_MONEY:
                    smart_money_size += h.get("size", 0)

            return {
                "side": side_name,
                "count": len(holders),
                "total_size": round(total_size, 2),
                "whale_count": whale_count,
                "smart_money_size": round(smart_money_size, 2),
                "smart_money_pct": round(smart_money_size / total_size * 100, 1) if total_size > 0 else 0,
                "concentration": round(max(h.get("size", 0) for h in holders) / total_size * 100, 1) if total_size > 0 else 0,
            }

        yes_analysis = analyze_side(yes_holders, "YES")
        no_analysis = analyze_side(no_holders, "NO")

        # Determine which side has smart money
        smart_money_favors = "YES" if yes_analysis["smart_money_pct"] > no_analysis["smart_money_pct"] else "NO"
        if yes_analysis["smart_money_pct"] == no_analysis["smart_money_pct"]:
            smart_money_favors = "neutral"

        return {
            "yes": yes_analysis,
            "no": no_analysis,
            "smart_money_favors": smart_money_favors,
            "our_side_check": "Check if smart bettors are with you or against you",
            "rule": "Know your counterparty",
        }

    # ==================== UMA RESOLUTION AWARENESS ====================

    def assess_resolution_risk(self, market_rules: str, time_to_resolution: int,
                               ambiguity_score: float) -> Dict:
        """
        INTEGRAFIX: Assess UMA resolution risk.

        From POLYMARKET_SPECIFIC.md:
        - "Rules Can Change - NOT always immutable"
        - "Ambiguous rules = higher risk"
        - "Popular/obvious outcomes resolve fast"

        Args:
            market_rules: Resolution criteria text
            time_to_resolution: Days until expected resolution
            ambiguity_score: 0-1 (1 = very ambiguous)

        Returns:
            Risk assessment and recommendations
        """
        risk_score = 0
        warnings = []

        # Ambiguity is major risk
        if ambiguity_score > 0.7:
            risk_score += 3
            warnings.append("HIGH AMBIGUITY - dispute likely")
        elif ambiguity_score > 0.4:
            risk_score += 1
            warnings.append("Moderate ambiguity - could see dispute")

        # Long time = more rule change risk
        if time_to_resolution > 30:
            risk_score += 2
            warnings.append(f"Long duration ({time_to_resolution} days) - monitor for rule changes")

        # Check for risky keywords in rules
        risky_keywords = ["may", "could", "discretion", "reasonable", "judgment"]
        found_risky = [kw for kw in risky_keywords if kw.lower() in market_rules.lower()]
        if found_risky:
            risk_score += len(found_risky)
            warnings.append(f"Subjective language in rules: {found_risky}")

        # Risk level
        if risk_score >= 4:
            risk_level = "HIGH"
            recommendation = "Reduce position size or avoid"
        elif risk_score >= 2:
            risk_level = "MEDIUM"
            recommendation = "Monitor closely, consider hedging"
        else:
            risk_level = "LOW"
            recommendation = "Normal position sizing appropriate"

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "warnings": warnings,
            "recommendation": recommendation,
            "position_size_adjustment": 1.0 - (risk_score * 0.15),  # Reduce by 15% per risk point
            "rule": "Ambiguous rules = higher risk, factor into sizing",
        }

    # ==================== SELF-IMPACT AWARENESS ====================

    def estimate_self_impact(self, order_size: float, book_depth: float,
                            avg_daily_volume: float = 0) -> Dict:
        """
        INTEGRAFIX: Estimate how much YOUR order moves the market.

        From MARKET_FUNDAMENTALS.md:
        - "You ARE the market" at scale
        - Self-impact eats into edge
        - Need to factor your own footprint

        Args:
            order_size: Size you want to trade
            book_depth: Available liquidity at your price level
            avg_daily_volume: Market's typical daily volume

        Returns:
            Impact analysis and sizing recommendation
        """
        if book_depth <= 0:
            return {
                "impact_pct": 100.0,
                "warning": "No liquidity - infinite impact",
                "size_recommendation": 0,
                "rule": "You ARE the market when book is empty",
            }

        # Impact as percentage of book you consume
        book_impact = (order_size / book_depth) * 100

        # Impact as percentage of daily volume
        volume_impact = 0
        if avg_daily_volume > 0:
            volume_impact = (order_size / avg_daily_volume) * 100

        # Estimate price impact (rough: 0.1% per 10% of book)
        price_impact = book_impact * 0.01

        # Sizing recommendation
        if book_impact > 50:
            recommendation = order_size * 0.2  # Only 20% of intended
            warning = "MASSIVE impact - split order across time"
        elif book_impact > 20:
            recommendation = order_size * 0.5
            warning = "Significant impact - consider splitting"
        elif book_impact > 5:
            recommendation = order_size * 0.8
            warning = "Moderate impact - acceptable"
        else:
            recommendation = order_size
            warning = None

        return {
            "impact_pct": round(book_impact, 2),
            "price_impact_estimate": round(price_impact, 4),
            "volume_pct": round(volume_impact, 2),
            "size_recommendation": round(recommendation, 2),
            "warning": warning,
            "rule": "You ARE the market - factor your own footprint",
        }

    # ==================== ORDER FLOW ANALYSIS ====================

    def analyze_order_flow(self, recent_trades: List[Dict]) -> Dict:
        """
        INTEGRAFIX: Analyze order flow to detect pressure.

        From MARKET_FUNDAMENTALS.md:
        - Direction of pressure (more buys vs sells)
        - Urgency (market orders = urgent, limits = patient)
        - Size of participants (retail vs whale)

        Args:
            recent_trades: List of {side, size, is_taker, timestamp}

        Returns:
            Flow analysis with directional signal
        """
        if not recent_trades:
            return {"signal": "neutral", "confidence": 0}

        buy_volume = 0
        sell_volume = 0
        taker_buys = 0
        taker_sells = 0
        whale_buys = 0
        whale_sells = 0

        for trade in recent_trades:
            size = trade.get("size", 0)
            side = trade.get("side", "").upper()
            is_taker = trade.get("is_taker", True)

            if side == "BUY":
                buy_volume += size
                if is_taker:
                    taker_buys += size
                if size > 1000:  # Whale threshold
                    whale_buys += size
            elif side == "SELL":
                sell_volume += size
                if is_taker:
                    taker_sells += size
                if size > 1000:
                    whale_sells += size

        total_volume = buy_volume + sell_volume
        if total_volume == 0:
            return {"signal": "neutral", "confidence": 0}

        # Net pressure
        net_pressure = (buy_volume - sell_volume) / total_volume

        # Taker imbalance (more informative - shows urgency)
        taker_total = taker_buys + taker_sells
        taker_imbalance = 0
        if taker_total > 0:
            taker_imbalance = (taker_buys - taker_sells) / taker_total

        # Whale direction
        whale_total = whale_buys + whale_sells
        whale_direction = 0
        if whale_total > 0:
            whale_direction = (whale_buys - whale_sells) / whale_total

        # Combined signal (weight taker flow more - shows conviction)
        combined = net_pressure * 0.3 + taker_imbalance * 0.5 + whale_direction * 0.2

        if combined > 0.3:
            signal = "bullish"
        elif combined < -0.3:
            signal = "bearish"
        else:
            signal = "neutral"

        return {
            "signal": signal,
            "net_pressure": round(net_pressure, 3),
            "taker_imbalance": round(taker_imbalance, 3),
            "whale_direction": round(whale_direction, 3),
            "combined_score": round(combined, 3),
            "buy_volume": round(buy_volume, 2),
            "sell_volume": round(sell_volume, 2),
            "confidence": round(abs(combined), 2),
            "rule": "Flow reveals intent - watch what traders DO",
        }

    # ==================== UMA CROSS-PLATFORM ARBITRAGE ====================

    def uma_arbitrage_opportunity(self, market_id: str, your_position: str,
                                  uma_vote_leaning: str,
                                  dispute_active: bool = False) -> Dict:
        """
        INTEGRAFIX: Identify UMA arbitrage opportunities.

        From MARKET_FUNDAMENTALS.md:
        - "Double-dipping possible" - hold position + vote
        - Cross-platform awareness: UMA ↔ Polymarket info loop
        - Watch disputes forming before they hit price

        Args:
            market_id: The Polymarket market
            your_position: Your side ("YES" or "NO")
            uma_vote_leaning: Current UMA vote direction
            dispute_active: Whether a dispute is ongoing

        Returns:
            Arbitrage analysis
        """
        opportunities = []
        warnings = []

        # 1. Vote alignment
        if your_position == uma_vote_leaning:
            opportunities.append("Vote aligned with position - can vote AND hold")
        else:
            warnings.append(f"Vote ({uma_vote_leaning}) opposes your position ({your_position})")

        # 2. Dispute arbitrage
        if dispute_active:
            opportunities.append("Active dispute - price may not reflect resolution")
            opportunities.append("Your research = voting edge")

        # 3. Double-dip strategy
        double_dip = {
            "hold_position": True,
            "participate_in_vote": True,
            "edge": "Get paid both ways",
        }

        return {
            "market_id": market_id,
            "opportunities": opportunities,
            "warnings": warnings,
            "double_dip_strategy": double_dip,
            "cross_platform_edge": "Most traders only watch one platform = your edge",
            "rule": "Info flows both directions - UMA ↔ Polymarket",
        }

    # ==================== MARKET RULES MONITORING ====================

    def monitor_rule_changes(self, market_id: str, original_rules: str,
                            current_rules: str) -> Dict:
        """
        INTEGRAFIX: Monitor for market rule changes.

        From MARKET_FUNDAMENTALS.md:
        - "Rules Are Important AND Can Change"
        - "NOT always immutable"
        - "What you bet on might not be what gets resolved"

        Args:
            market_id: Market identifier
            original_rules: Rules when you entered
            current_rules: Rules now

        Returns:
            Change analysis and recommendations
        """
        if original_rules == current_rules:
            return {
                "changed": False,
                "market_id": market_id,
                "action": "continue",
                "rule": "Rules unchanged - position thesis intact",
            }

        # Rules changed - analyze
        import difflib
        diff = list(difflib.unified_diff(
            original_rules.split(),
            current_rules.split(),
            lineterm=''
        ))

        additions = [d[1:] for d in diff if d.startswith('+') and not d.startswith('+++')]
        removals = [d[1:] for d in diff if d.startswith('-') and not d.startswith('---')]

        # Check for dangerous keywords in changes
        dangerous = ["void", "cancel", "invalid", "ambiguous", "discretion"]
        danger_found = [kw for kw in dangerous if kw in ' '.join(additions).lower()]

        if danger_found:
            severity = "HIGH"
            action = "EXIT - rules materially changed"
        elif len(additions) > 10 or len(removals) > 10:
            severity = "MEDIUM"
            action = "REVIEW - significant rule changes"
        else:
            severity = "LOW"
            action = "MONITOR - minor rule updates"

        return {
            "changed": True,
            "market_id": market_id,
            "severity": severity,
            "action": action,
            "additions": additions[:5],  # First 5
            "removals": removals[:5],
            "danger_keywords": danger_found,
            "rule": "Rule changes can flip your edge - stay on the ball",
        }

    # ==================== STATE PERSISTENCE ====================

    def _load_state(self):
        """Load state from disk."""
        try:
            state_file = STATE_DIR / "polymarket_fundamentals.json"
            if state_file.exists():
                with open(state_file) as f:
                    data = json.load(f)
                self._collateral.total_collateral = data.get("total_collateral", 0)
                self._collateral.actually_locked = data.get("actually_locked", 0)
        except:
            pass

    def _save_state(self):
        """Save state to disk."""
        try:
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_collateral": self._collateral.total_collateral,
                "actually_locked": self._collateral.actually_locked,
                "allocated_to_orders": self._collateral.allocated_to_orders,
                "wallet_profiles_count": len(self._wallet_profiles),
            }
            state_file = STATE_DIR / "polymarket_fundamentals.json"
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def status(self) -> Dict:
        """Get current status."""
        return {
            "success": True,
            "collateral": {
                "total": self._collateral.total_collateral,
                "locked": self._collateral.actually_locked,
                "allocated": self._collateral.allocated_to_orders,
                "available": self._collateral.available,
                "utilization": round(self._collateral.utilization * 100, 1),
            },
            "wallets_tracked": len(self._wallet_profiles),
            "markets_with_orders": len(self._order_matrix),
        }


# Singleton
_fundamentals = None

def get_polymarket_fundamentals() -> PolymarketFundamentals:
    """Get or create the Polymarket fundamentals singleton."""
    global _fundamentals
    if _fundamentals is None:
        _fundamentals = PolymarketFundamentals()
    return _fundamentals


if __name__ == "__main__":
    print("=" * 70)
    print("POLYMARKET FUNDAMENTALS - Yair's Knowledge Encoded")
    print("=" * 70)

    pf = get_polymarket_fundamentals()

    # Test maker vs taker
    print("\n[MAKER VS TAKER TEST]")
    result = pf.should_make_or_take(edge_pct=8, urgency=0.3, book_depth=5000, position_size=1000)
    print(f"  Recommendation: {result['recommendation']}")
    print(f"  Reasons: {result['reasons']}")
    print(f"  Rule: {result['rule']}")

    # Test reusable collateral
    print("\n[REUSABLE COLLATERAL TEST]")
    pf.update_collateral(1000)
    for i in range(3):
        result = pf.allocate_order(f"market_{i}", price=0.5, size=500)
    print(f"  Total Allocated: ${result['total_allocated']:.2f}")
    print(f"  Utilization: {result['utilization']:.1f}%")
    print(f"  Overcommitted: {result['overcommitted']}")
    print(f"  Rule: {result['rule']}")

    # Test counterparty mistake
    print("\n[ZERO-SUM ANALYSIS]")
    result = pf.calculate_counterparty_mistake(our_entry=0.45, our_fair_value=0.60, side="BUY")
    print(f"  Counterparty loss/share: ${result['counterparty_loss_per_share']:.4f}")
    print(f"  Is gift: {result['is_gift']}")
    print(f"  Rule: {result['rule']}")

    # Test resolution risk
    print("\n[UMA RESOLUTION RISK]")
    result = pf.assess_resolution_risk(
        market_rules="Will candidate win, as determined by reasonable interpretation",
        time_to_resolution=45,
        ambiguity_score=0.6
    )
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Warnings: {result['warnings']}")
    print(f"  Position Adjustment: {result['position_size_adjustment']:.2f}x")

    print("\n[STATUS]")
    status = pf.status()
    print(f"  Collateral: ${status['collateral']['total']:.2f}")
    print(f"  Utilization: {status['collateral']['utilization']:.1f}%")
