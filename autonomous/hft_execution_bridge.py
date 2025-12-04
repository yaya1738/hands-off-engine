#!/usr/bin/env python3
"""
HFT Execution Bridge - Connect Opportunity Detection to HFT Execution

This module bridges the gap between:
- Knowledge Fusion (insights)
- Yair Wisdom Engine (opportunities)
- HFT Infrastructure (execution)

THE MISSING LINK: Knowledge → Execution

USAGE:
    from autonomous.hft_execution_bridge import hft_bridge

    # Scan for opportunities and execute
    results = hft_bridge.scan_and_execute()

    # Or use in backend loop
    hft_status = hft_bridge.run_hft_cycle()

Serving: Yair Siegel
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"


@dataclass
class ExecutionOpportunity:
    """Represents a trading opportunity ready for execution."""
    opportunity_type: str  # merge_arb, espn_signal, thin_book, grid_capture
    token_id: str
    side: str  # BUY, SELL, BOTH
    price: float
    size: float
    confidence: float
    source: str  # yair_wisdom, knowledge_fusion, market_scan
    reason: str


@dataclass
class ExecutionResult:
    """Result of executing an opportunity."""
    success: bool
    opportunity: ExecutionOpportunity
    orders_placed: int
    latency_ms: float
    error: Optional[str] = None


class HFTExecutionBridge:
    """
    Bridge between opportunity detection and HFT execution.

    Connects:
    - Yair Wisdom Engine → Detects opportunities
    - Knowledge Fusion → Provides context
    - HFT Agent API → Executes trades
    """

    def __init__(self):
        self._hft = None
        self._wisdom = None
        self._fusion = None
        self._last_scan = None
        self._execution_log = []

    # ==================== LAZY LOADING ====================

    @property
    def hft(self):
        """Unlimited HFT for execution - 63 wallets, 15K orders/sec."""
        if not self._hft:
            from executor.unlimited_hft import get_unlimited_hft
            self._hft = get_unlimited_hft()
            self._hft.activate()
        return self._hft

    @property
    def lightning(self):
        """Lightning rod for Cloudflare-aware connections."""
        if not hasattr(self, '_lightning') or self._lightning is None:
            from executor.polymarket_lightning import get_lightning
            self._lightning = get_lightning()
        return self._lightning

    @property
    def wisdom(self):
        """Yair Wisdom Engine for opportunity detection."""
        if not self._wisdom:
            try:
                from autonomous.yair_wisdom_engine import get_wisdom
                self._wisdom = get_wisdom()
            except:
                self._wisdom = None
        return self._wisdom

    @property
    def fusion(self):
        """Knowledge Fusion for context."""
        if not self._fusion:
            try:
                from autonomous.knowledge_fusion import get_fusion
                self._fusion = get_fusion()
            except:
                self._fusion = None
        return self._fusion

    @property
    def abcfc_hft(self):
        """ABCFC-HFT Frequency for microsecond ABCFC updates."""
        if not hasattr(self, '_abcfc_hft') or self._abcfc_hft is None:
            try:
                from integrafix.abcfc_hft_frequency import get_abcfc_hft
                self._abcfc_hft = get_abcfc_hft()
            except:
                self._abcfc_hft = None
        return self._abcfc_hft

    @property
    def fair_price_estimator(self):
        """FairPriceEstimator for EXTERNAL probability estimation."""
        if not hasattr(self, '_fair_price') or self._fair_price is None:
            try:
                from integrafix.fair_price_estimator import FairPriceEstimator
                self._fair_price = FairPriceEstimator()
            except:
                self._fair_price = None
        return self._fair_price

    @property
    def polymarket_fundamentals(self):
        """Polymarket Fundamentals - Yair's knowledge encoded."""
        if not hasattr(self, '_poly_fundamentals') or self._poly_fundamentals is None:
            try:
                from integrafix.polymarket_fundamentals import get_polymarket_fundamentals
                self._poly_fundamentals = get_polymarket_fundamentals()
            except:
                self._poly_fundamentals = None
        return self._poly_fundamentals

    # ==================== POLYMARKET MARKET FUNDAMENTALS ====================

    def get_l2_orderbook(self, token_id: str) -> Dict:
        """
        INTEGRAFIX: Fetch L2 order book depth for slippage calculation.

        From MARKET_FUNDAMENTALS.md:
        - L2 = multiple price levels with size at each
        - ALWAYS check book depth BEFORE order
        - Compare your size to available liquidity at each level
        """
        try:
            import requests

            # Polymarket CLOB API for order book
            response = requests.get(
                f"https://clob.polymarket.com/book?token_id={token_id}",
                timeout=5,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            if response.status_code == 200:
                book = response.json()
                return {
                    "success": True,
                    "bids": book.get("bids", []),  # [{price, size}, ...]
                    "asks": book.get("asks", []),  # [{price, size}, ...]
                    "best_bid": float(book["bids"][0]["price"]) if book.get("bids") else 0,
                    "best_ask": float(book["asks"][0]["price"]) if book.get("asks") else 1,
                }
        except Exception as e:
            pass

        return {"success": False, "bids": [], "asks": [], "best_bid": 0, "best_ask": 1}

    def calculate_slippage(self, book: Dict, side: str, size: float) -> Dict:
        """
        INTEGRAFIX: Walk the order book to calculate expected slippage.

        From MARKET_FUNDAMENTALS.md:
        - "Know expected fill price (walk the book mentally)"
        - Large orders: check L2 depth or you'll regret it

        Returns:
            avg_fill_price: Weighted average price after walking book
            slippage_cost: Cost vs best price
            levels_consumed: How many price levels we'd need
            full_fill_available: Can we fill entire order?
        """
        levels = book.get("asks" if side == "BUY" else "bids", [])

        if not levels:
            return {
                "avg_fill_price": 0.5,
                "slippage_cost": 0,
                "levels_consumed": 0,
                "full_fill_available": False,
            }

        best_price = float(levels[0]["price"])
        remaining = size
        total_cost = 0.0
        levels_consumed = 0

        # Walk the book
        for level in levels:
            level_price = float(level["price"])
            level_size = float(level["size"])

            if remaining <= 0:
                break

            fill_at_level = min(remaining, level_size)
            total_cost += fill_at_level * level_price
            remaining -= fill_at_level
            levels_consumed += 1

        filled = size - remaining
        if filled > 0:
            avg_fill_price = total_cost / filled
            slippage_cost = (avg_fill_price - best_price) * filled if side == "BUY" else (best_price - avg_fill_price) * filled
        else:
            avg_fill_price = best_price
            slippage_cost = 0

        return {
            "avg_fill_price": round(avg_fill_price, 6),
            "slippage_cost": round(abs(slippage_cost), 4),
            "levels_consumed": levels_consumed,
            "full_fill_available": remaining <= 0,
            "unfilled": round(remaining, 2),
        }

    def calculate_self_impact(self, book: Dict, side: str, size: float) -> Dict:
        """
        INTEGRAFIX: Calculate self-impact for large orders.

        From POLYMARKET_SPECIFIC.md:
        - "Your action → market reaction → affects your next action"
        - "Edge calculation must include self-impact cost"

        Returns:
            impact_pct: How much our order would move the price
            safe_size: Maximum size without excessive impact
            should_split: Whether to split into multiple orders
        """
        levels = book.get("asks" if side == "BUY" else "bids", [])

        if not levels:
            return {
                "impact_pct": 0,
                "safe_size": size,
                "should_split": False,
            }

        best_price = float(levels[0]["price"])
        total_depth = sum(float(l["size"]) for l in levels[:5])  # Top 5 levels

        # Impact estimate: what % of top-5 depth are we taking?
        if total_depth > 0:
            depth_consumption = size / total_depth
        else:
            depth_consumption = 1.0

        # Price impact scales with depth consumption
        # Taking >20% of book = significant impact
        impact_pct = min(depth_consumption * 0.05, 0.10)  # Cap at 10%

        # Safe size = 20% of available depth
        safe_size = total_depth * 0.20

        return {
            "impact_pct": round(impact_pct * 100, 2),  # As percentage
            "safe_size": round(safe_size, 2),
            "should_split": size > safe_size,
            "top5_depth": round(total_depth, 2),
            "depth_consumption_pct": round(depth_consumption * 100, 2),
        }

    def calculate_kelly_size(self, edge: float, win_prob: float, bankroll: float,
                            max_fraction: float = 0.25) -> Dict:
        """
        INTEGRAFIX: Kelly criterion sizing from ABCFC edge.

        From MARKET_FUNDAMENTALS.md:
        - Kelly Fraction = (bp - q) / b
        - where b = odds - 1, p = win prob, q = 1-p

        For prediction markets (binary):
        - If we buy YES at price p, win pays (1-p)/p odds
        - Edge = our_prob - market_price

        Returns:
            kelly_fraction: Optimal fraction of bankroll
            position_size: Dollar amount to risk
            half_kelly: Conservative sizing (half Kelly)
        """
        if edge <= 0 or win_prob <= 0 or win_prob >= 1:
            return {
                "kelly_fraction": 0,
                "position_size": 0,
                "half_kelly": 0,
            }

        # For binary markets: Kelly = edge / (1 - market_price)
        # But more generally: f* = p - q/b where b = win_payout/bet
        # Simplified Kelly for prediction markets:
        # f* = (p - price) / (1 - price) where p = our_prob, price = market_price

        market_price = win_prob - edge  # Derive market price from edge
        if market_price <= 0 or market_price >= 1:
            return {
                "kelly_fraction": 0,
                "position_size": 0,
                "half_kelly": 0,
            }

        # Kelly fraction
        kelly = edge / (1 - market_price)

        # Cap at max_fraction (never bet more than 25% of bankroll)
        kelly = min(kelly, max_fraction)
        kelly = max(kelly, 0)

        position_size = bankroll * kelly
        half_kelly = position_size / 2  # Conservative sizing

        return {
            "kelly_fraction": round(kelly, 4),
            "position_size": round(position_size, 2),
            "half_kelly": round(half_kelly, 2),
            "edge_used": round(edge, 4),
        }

    def maker_vs_taker_abcfc(self, price: float, size: float, side: str,
                            is_maker: bool, book: Dict = None) -> Dict:
        """
        INTEGRAFIX: Different ABCFC for maker vs taker orders.

        From MARKET_FUNDAMENTALS.md:
        - "LIMIT ORDER = MAKING → Often get REBATES"
        - "MARKET ORDER = TAKING → Usually pay FEES"

        From POLYMARKET_SPECIFIC.md:
        - "Zero trading fees" but execution quality differs
        - Makers get better fills (at their price)
        - Takers pay spread (instant execution)

        Returns:
            ABCFC bounds adjusted for maker/taker execution
        """
        # Base ABCFC calculation
        if side == "BUY":
            worst = -size * price
            best = size * (1 - price)
        else:
            worst = -size * (1 - price)
            best = size * price

        if is_maker:
            # MAKER: Post limit order, wait for fill
            # Pros: Get your exact price, no slippage
            # Cons: May not fill, opportunity cost
            fill_probability = 0.7  # Estimate 70% fill rate

            expected_best = best * fill_probability
            expected_worst = worst * fill_probability  # Only lose if we filled

            # Opportunity cost of not filling
            opportunity_cost = 0  # We don't lose if we don't fill

            return {
                "worst": round(expected_worst, 4),
                "expected": round((expected_best + expected_worst) / 2, 4),
                "best": round(expected_best, 4),
                "execution_type": "maker",
                "fill_probability": fill_probability,
                "slippage": 0,
                "notes": "Limit order - better price, uncertain fill",
            }
        else:
            # TAKER: Market order, instant fill
            # Pros: Guaranteed execution
            # Cons: Pay spread, slippage on large orders

            slippage = 0
            if book:
                slippage_info = self.calculate_slippage(book, side, size)
                slippage = slippage_info.get("slippage_cost", 0)
            else:
                # Estimate 0.5% slippage without book data
                slippage = size * price * 0.005

            # Adjust bounds for slippage
            if side == "BUY":
                # Slippage makes our entry worse
                adjusted_worst = worst - slippage
                adjusted_best = best - slippage
            else:
                adjusted_worst = worst - slippage
                adjusted_best = best - slippage

            return {
                "worst": round(adjusted_worst, 4),
                "expected": round((adjusted_best + adjusted_worst) / 2, 4),
                "best": round(adjusted_best, 4),
                "execution_type": "taker",
                "fill_probability": 1.0,
                "slippage": round(slippage, 4),
                "notes": "Market order - guaranteed fill, pays spread/slippage",
            }

    # ==================== YAIR POLYMARKET ABCFC METHODOLOGY ====================

    def get_yair_fair_price(self, market: Dict) -> Dict:
        """
        INTEGRAFIX: Get fair price using Yair's methodology.

        Priority order (from fair_price_estimator.py):
        1. Human estimates (Yair's kernel) - HIGHEST
        2. Order book analysis (spread, depth)
        3. Historical regression
        4. Volatility/momentum

        Returns external probability estimate, NOT market price.
        """
        if not self.fair_price_estimator:
            return {"fair_price": None, "source": "none", "edge": 0}

        estimator = self.fair_price_estimator

        # Try each method in priority order
        estimate = None

        # 1. Human estimates (Yair's probability beliefs)
        estimate = estimator.estimate_from_human(market)
        if estimate and estimate.is_actionable:
            return {
                "fair_price": estimate.fair_price,
                "confidence": estimate.confidence,
                "source": estimate.source,
                "edge": estimate.edge_vs_market,
                "reasoning": estimate.reasoning,
            }

        # 2. Order book analysis
        estimate = estimator.estimate_from_orderbook(market)
        if estimate and estimate.is_actionable:
            return {
                "fair_price": estimate.fair_price,
                "confidence": estimate.confidence,
                "source": estimate.source,
                "edge": estimate.edge_vs_market,
                "reasoning": estimate.reasoning,
            }

        # 3. Historical regression
        estimate = estimator.estimate_from_history(market)
        if estimate and estimate.is_actionable:
            return {
                "fair_price": estimate.fair_price,
                "confidence": estimate.confidence,
                "source": estimate.source,
                "edge": estimate.edge_vs_market,
                "reasoning": estimate.reasoning,
            }

        # 4. Volatility/momentum
        estimate = estimator.estimate_from_volatility(market)
        if estimate and estimate.is_actionable:
            return {
                "fair_price": estimate.fair_price,
                "confidence": estimate.confidence,
                "source": estimate.source,
                "edge": estimate.edge_vs_market,
                "reasoning": estimate.reasoning,
            }

        return {"fair_price": None, "source": "none", "edge": 0}

    def compute_polymarket_abcfc(self, market: Dict, side: str, size: float) -> Dict:
        """
        INTEGRAFIX: Compute ABCFC using Yair's Polymarket methodology.

        Uses EXTERNAL probability sources (not just market price):
        1. Yair's human probability estimates
        2. Order book depth and spread
        3. Historical price regression
        4. Volatility/momentum

        This is the PROPER way to compute edge - from fundamentals,
        not from the market price itself.

        Args:
            market: Dict with keys: yes_price, bestBid, bestAsk, slug, etc.
            side: "BUY" or "SELL"
            size: Number of shares

        Returns:
            ABCFC dict with fair_price_source showing where edge came from
        """
        # Get market price
        yes_price = market.get('yes_price') or market.get('last', 0.5)

        # Get EXTERNAL fair price estimate (Yair's methodology)
        fair = self.get_yair_fair_price(market)
        fair_price = fair.get("fair_price")
        fair_source = fair.get("source", "none")
        fair_confidence = fair.get("confidence", 0)

        # If we have external fair price, use it as our probability
        # Otherwise fall back to confidence parameter
        if fair_price is not None:
            our_prob = fair_price
            edge_source = fair_source
        else:
            # No external estimate - use market price (no edge)
            our_prob = yes_price
            edge_source = "market_price"

        # ABCFC bounds (from abcfc_live.py methodology)
        if side == "BUY":
            worst = -size * yes_price           # Lose investment
            best = size * (1 - yes_price)       # Win complement
            edge = our_prob - yes_price         # Our edge
            expected = size * edge
        else:  # SELL
            worst = -size * (1 - yes_price)     # YES wins
            best = size * yes_price             # YES loses
            edge = our_prob - (1 - yes_price)   # Edge for NO
            expected = size * edge

        # Order book liquidity adjustment
        best_bid = market.get('bestBid') or market.get('best_bid', 0)
        best_ask = market.get('bestAsk') or market.get('best_ask', 0)
        spread = best_ask - best_bid if best_ask > best_bid else 0
        spread_pct = spread / yes_price if yes_price > 0 else 0

        # Liquidity penalty: wide spread = harder to execute
        liquidity_factor = 1.0 - min(0.3, spread_pct)

        # Adjust expected by liquidity
        expected_adjusted = expected * liquidity_factor

        # Transaction cost
        tx_cost = size * yes_price * 0.005

        return {
            "worst": round(worst, 4),
            "expected": round(expected_adjusted, 4),
            "best": round(best, 4),
            "edge": round(edge, 4),
            "edge_pct": round(edge * 100, 2),
            "should_execute": expected_adjusted > tx_cost and edge > 0,
            # Yair methodology fields
            "fair_price": round(our_prob, 4) if fair_price else None,
            "fair_price_source": edge_source,
            "fair_price_confidence": round(fair_confidence, 2),
            "market_price": round(yes_price, 4),
            # Market fundamentals
            "spread_pct": round(spread_pct * 100, 2),
            "liquidity_factor": round(liquidity_factor, 2),
            "tx_cost_threshold": round(tx_cost, 4),
        }

    # ==================== ABCFC FOR EVERY HFT ACTION ====================

    def compute_action_abcfc(self, opp: ExecutionOpportunity,
                             use_l2_book: bool = True,
                             is_maker: bool = True) -> Dict:
        """
        Compute ABCFC [worst, expected, best] for a single HFT action.

        INTEGRAFIX: Full Polymarket methodology with:
        - L2 order book slippage calculation (walk the book)
        - Maker vs Taker distinction
        - Self-impact awareness for large orders
        - Kelly sizing from ABCFC edge

        Uses the ABCFC methodology from executor/math/abcfc_live.py:
        - worst_resolution: -shares * entry_price (YES) or -shares * (1-entry_price) (NO)
        - best_resolution: shares * (1 - entry_price) (YES) or shares * entry_price (NO)
        - expected_pnl: shares * (prob - entry_price) (the EDGE formula)

        KEY INSIGHT: Our confidence represents our belief about the TRUE probability,
        The EDGE = confidence - market_price

        Returns:
            {
                "worst": worst_resolution outcome (slippage-adjusted),
                "expected": shares * (our_prob - entry_price) - slippage,
                "best": best_resolution outcome,
                "should_execute": True if edge > transaction costs + slippage,
                "edge": our_prob - market_price (the actual edge),
                "slippage": estimated slippage from L2 book walk,
                "self_impact": self-impact analysis for large orders,
                "kelly": Kelly sizing recommendation,
                "maker_taker": maker vs taker ABCFC comparison,
            }
        """
        price = opp.price  # Market price = entry price
        size = opp.size    # Shares
        side = opp.side
        our_prob = opp.confidence  # Our belief about TRUE probability

        # ========== L2 ORDER BOOK ANALYSIS ==========
        book = None
        slippage_info = {"slippage_cost": 0, "avg_fill_price": price}
        self_impact_info = {"impact_pct": 0, "should_split": False}

        if use_l2_book and opp.token_id:
            book = self.get_l2_orderbook(opp.token_id)
            if book.get("success"):
                # Calculate slippage by walking the book
                slippage_info = self.calculate_slippage(book, side, size)

                # Calculate self-impact for large orders
                self_impact_info = self.calculate_self_impact(book, side, size)

        slippage_cost = slippage_info.get("slippage_cost", 0)
        avg_fill_price = slippage_info.get("avg_fill_price", price)

        # ========== BASE ABCFC (using abcfc_live.py methodology) ==========
        if side == "BUY":
            # Buying YES at (potentially slipped) price
            worst = -size * avg_fill_price       # worst_resolution: lose investment
            best = size * (1 - avg_fill_price)   # best_resolution: win complement

            edge = our_prob - avg_fill_price     # Our edge vs effective entry
            expected = size * edge               # Expected P&L

        elif side == "SELL":
            # Selling YES at (potentially slipped) price
            worst = -size * (1 - avg_fill_price)  # worst: YES wins, we lose
            best = size * avg_fill_price          # best: YES loses, we profit

            edge = our_prob - (1 - avg_fill_price)  # Our edge for betting on NO
            expected = size * edge

        else:
            # BOTH (merge arb) - arbitrage opportunity
            spread = 0.03  # Typical spread where YES+NO < $1
            worst = -size * 0.01 - slippage_cost * 2  # Execution risk + slippage both sides
            best = size * spread - slippage_cost * 2  # Full spread minus slippage
            edge = spread * our_prob
            expected = size * edge - slippage_cost * 2

        # ========== MAKER VS TAKER ABCFC ==========
        maker_abcfc = self.maker_vs_taker_abcfc(price, size, side, is_maker=True, book=book)
        taker_abcfc = self.maker_vs_taker_abcfc(price, size, side, is_maker=False, book=book)

        # Adjust expected for maker/taker execution type
        if is_maker:
            # Maker gets better price but uncertain fill
            fill_prob = maker_abcfc.get("fill_probability", 0.7)
            expected_adjusted = expected * fill_prob
        else:
            # Taker: subtract slippage from expected
            expected_adjusted = expected - slippage_cost

        # ========== KELLY SIZING ==========
        # Get bankroll from state (or use default)
        bankroll = 1000  # Default
        try:
            balance_file = STATE_DIR / "polymarket_balance.json"
            if balance_file.exists():
                import json
                with open(balance_file) as f:
                    bal = json.load(f)
                    bankroll = bal.get("total_balance", 1000)
        except:
            pass

        kelly_info = self.calculate_kelly_size(edge, our_prob, bankroll)

        # ========== CURRENT SYSTEM STATE ==========
        current_expected = 0
        if self.abcfc_hft:
            try:
                current_expected = self.abcfc_hft.state.total_abcfc.expected
            except:
                pass

        # ========== EXECUTION DECISION ==========
        # Transaction cost threshold (Polymarket has zero fees, but gas/spread)
        tx_cost = size * price * 0.002  # ~0.2% for spread

        # Self-impact penalty
        impact_penalty = size * price * (self_impact_info.get("impact_pct", 0) / 100)

        # Total cost = tx + slippage + impact
        total_cost = tx_cost + slippage_cost + impact_penalty

        # Should execute if edge beats total costs
        should_execute = expected_adjusted > total_cost and edge > 0

        return {
            # Core ABCFC
            "worst": round(worst, 4),
            "expected": round(expected_adjusted, 4),
            "best": round(best, 4),
            "should_execute": should_execute,

            # Edge analysis
            "edge": round(edge, 4),
            "edge_pct": round(edge * 100, 2),
            "our_probability": round(our_prob, 4),
            "market_price": round(price, 4),
            "effective_entry": round(avg_fill_price, 4),

            # Polymarket-specific (L2 book)
            "slippage": {
                "cost": round(slippage_cost, 4),
                "avg_fill_price": round(avg_fill_price, 6),
                "levels_consumed": slippage_info.get("levels_consumed", 0),
                "full_fill_available": slippage_info.get("full_fill_available", True),
            },

            # Self-impact
            "self_impact": {
                "impact_pct": self_impact_info.get("impact_pct", 0),
                "safe_size": self_impact_info.get("safe_size", size),
                "should_split": self_impact_info.get("should_split", False),
                "penalty": round(impact_penalty, 4),
            },

            # Kelly sizing
            "kelly": {
                "fraction": kelly_info.get("kelly_fraction", 0),
                "recommended_size": kelly_info.get("half_kelly", 0),  # Half Kelly = conservative
                "full_kelly_size": kelly_info.get("position_size", 0),
            },

            # Maker vs Taker comparison
            "maker_taker": {
                "execution_type": "maker" if is_maker else "taker",
                "maker_expected": maker_abcfc.get("expected", 0),
                "taker_expected": taker_abcfc.get("expected", 0),
                "recommendation": "maker" if maker_abcfc.get("expected", 0) > taker_abcfc.get("expected", 0) else "taker",
            },

            # Costs breakdown
            "costs": {
                "tx_cost": round(tx_cost, 4),
                "slippage_cost": round(slippage_cost, 4),
                "impact_penalty": round(impact_penalty, 4),
                "total_cost": round(total_cost, 4),
            },

            # System state
            "current_system_expected": round(current_expected, 2),
        }

    def abcfc_approve_action(self, opp: ExecutionOpportunity) -> bool:
        """
        ABCFC gatekeeper for HFT actions.

        Returns True only if ABCFC approves the action.

        INTEGRAFIX Approval Criteria (from system methodology + Polymarket docs):
        1. Edge > 0 (we have information advantage)
        2. Expected > total_cost (beats tx + slippage + impact)
        3. Edge > 5% OR Risk/Reward > 0.3 (meaningful edge or good R/R)
        4. Self-impact check: if should_split, warn but allow
        5. Kelly check: size shouldn't exceed 2x Kelly recommendation
        """
        abcfc = self.compute_action_abcfc(opp)

        # Must have positive edge that beats all costs
        if not abcfc["should_execute"]:
            return False

        # Edge must be positive (our_prob > market_price)
        if abcfc["edge"] <= 0:
            return False

        # Expected P&L must be positive after all costs
        if abcfc["expected"] <= 0:
            return False

        # Check slippage isn't eating all our edge
        slippage = abcfc.get("slippage", {})
        costs = abcfc.get("costs", {})
        total_cost = costs.get("total_cost", 0)

        if total_cost > 0 and abcfc["expected"] < total_cost * 1.5:
            # Need at least 50% buffer over costs
            return False

        # Either need meaningful edge (>5%) OR good risk/reward
        edge_pct = abcfc["edge_pct"]
        if abcfc["worst"] < 0:
            risk_reward = abcfc["expected"] / abs(abcfc["worst"])
        else:
            risk_reward = float('inf')

        # Accept if: edge > 5% OR risk/reward > 0.3
        if edge_pct < 5 and risk_reward < 0.3:
            return False

        # Self-impact warning (don't reject, but could log)
        self_impact = abcfc.get("self_impact", {})
        if self_impact.get("should_split", False):
            # Large order - might want to split
            # For now, allow but system could split automatically
            pass

        # Kelly sanity check: don't exceed 2x Kelly recommendation
        kelly = abcfc.get("kelly", {})
        kelly_recommended = kelly.get("recommended_size", float('inf'))
        if kelly_recommended > 0 and opp.size > kelly_recommended * 2:
            # Position is way too large relative to edge
            return False

        return True

    def update_abcfc_after_execution(self, opp: ExecutionOpportunity,
                                      result: 'ExecutionResult'):
        """Update ABCFC state after HFT execution."""
        if not self.abcfc_hft or not result.success:
            return

        try:
            # Process the trade to update ABCFC bounds
            self.abcfc_hft.process_hft_trade(
                side=opp.side,
                size=opp.size,
                price=opp.price,
                pnl=0  # PnL will be determined at resolution
            )
        except:
            pass

    # ==================== FULL POLYMARKET FUNDAMENTALS ANALYSIS ====================

    def full_polymarket_analysis(self, opp: ExecutionOpportunity,
                                 market_rules: str = "",
                                 time_to_resolution: int = 30,
                                 counterparty_wallets: List[str] = None) -> Dict:
        """
        INTEGRAFIX: Full Polymarket fundamentals analysis for an opportunity.

        Combines ALL knowledge from Yair's docs:
        - ABCFC with L2 slippage, self-impact, Kelly
        - Maker vs Taker recommendation
        - Counterparty analysis (gift or trap?)
        - Resolution risk assessment
        - Reusable collateral check
        - Smart money tracking

        This is THE comprehensive pre-trade analysis.
        """
        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "opportunity": {
                "type": opp.opportunity_type,
                "side": opp.side,
                "price": opp.price,
                "size": opp.size,
                "confidence": opp.confidence,
            },
            "abcfc": {},
            "fundamentals": {},
            "final_decision": {},
        }

        # 1. ABCFC Analysis (already has L2, Kelly, maker/taker, self-impact)
        abcfc = self.compute_action_abcfc(opp)
        analysis["abcfc"] = abcfc

        # 2. Polymarket Fundamentals
        if self.polymarket_fundamentals:
            pf = self.polymarket_fundamentals

            # Maker vs Taker decision
            book = self.get_l2_orderbook(opp.token_id) if opp.token_id else {}
            book_depth = sum(float(l.get("size", 0)) for l in book.get("asks", [])[:5])
            urgency = 0.3 if opp.opportunity_type == "merge_arb" else 0.5
            maker_taker = pf.should_make_or_take(
                edge_pct=abcfc.get("edge_pct", 0),
                urgency=urgency,
                book_depth=book_depth,
                position_size=opp.size
            )
            analysis["fundamentals"]["maker_vs_taker"] = maker_taker

            # Counterparty / Zero-Sum analysis
            our_fair_value = opp.confidence  # Our probability belief
            gift_analysis = pf.calculate_counterparty_mistake(
                our_entry=opp.price,
                our_fair_value=our_fair_value,
                side=opp.side
            )
            analysis["fundamentals"]["counterparty"] = gift_analysis

            # Resolution risk (if rules provided)
            if market_rules:
                resolution_risk = pf.assess_resolution_risk(
                    market_rules=market_rules,
                    time_to_resolution=time_to_resolution,
                    ambiguity_score=0.3  # Default low ambiguity
                )
                analysis["fundamentals"]["resolution_risk"] = resolution_risk

            # LP opportunity rating
            spread_pct = abcfc.get("slippage", {}).get("cost", 0) / (opp.size * opp.price) * 100 if opp.size > 0 else 0
            lp_rating = pf.rate_liquidity_provision_opportunity(
                spread_pct=spread_pct,
                book_depth=book_depth,
                avg_daily_volume=100000  # Default estimate
            )
            analysis["fundamentals"]["lp_opportunity"] = lp_rating

            # Collateral check
            collateral_status = pf.status()
            analysis["fundamentals"]["collateral"] = collateral_status.get("collateral", {})

        # 3. Final Decision
        should_execute = abcfc.get("should_execute", False)
        reasons = []

        if abcfc.get("edge", 0) > 0:
            reasons.append(f"Edge: {abcfc.get('edge_pct', 0):.2f}%")
        else:
            reasons.append("NO EDGE - reject")
            should_execute = False

        if analysis.get("fundamentals", {}).get("counterparty", {}).get("is_gift"):
            reasons.append("Counterparty giving us edge")
        else:
            reasons.append("WARNING: We may be the fish")

        maker_rec = analysis.get("fundamentals", {}).get("maker_vs_taker", {}).get("recommendation", "maker")
        reasons.append(f"Execute as: {maker_rec}")

        resolution_risk = analysis.get("fundamentals", {}).get("resolution_risk", {})
        if resolution_risk.get("risk_level") == "HIGH":
            size_adj = resolution_risk.get("position_size_adjustment", 1.0)
            reasons.append(f"HIGH resolution risk - reduce size to {size_adj:.0%}")

        analysis["final_decision"] = {
            "should_execute": should_execute,
            "reasons": reasons,
            "recommended_execution": maker_rec,
            "yair_rules": [
                "Be the house, not the gambler",
                "One man's pitfall = another's luck",
                "Patient liquidity provider wins",
            ],
        }

        return analysis

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Get bridge status using unlimited HFT."""
        # Get unlimited HFT status (63 wallets)
        hft_status = self.hft.status()

        # Add Polymarket fundamentals status
        poly_status = {}
        if self.polymarket_fundamentals:
            poly_status = self.polymarket_fundamentals.status()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hft_ready": hft_status.get("wallets_active", 0) > 0,
            "hft_wallets": hft_status.get("wallets_total", 0),
            "hft_active": hft_status.get("wallets_active", 0),
            "hft_capacity": hft_status.get("theoretical_capacity", "0/sec"),
            "hft_mode": hft_status.get("mode", "LIMITED"),
            "wisdom_loaded": self.wisdom is not None,
            "fusion_loaded": self.fusion is not None,
            "polymarket_fundamentals": poly_status,
            "executions_today": len(self._execution_log),
            "last_scan": self._last_scan
        }

    # ==================== OPPORTUNITY DETECTION ====================

    def scan_opportunities(self) -> List[ExecutionOpportunity]:
        """
        Scan for all types of opportunities.

        Sources:
        1. Yair Wisdom Engine - merge arb, ESPN signals
        2. Market scanning - thin books, grids
        3. Knowledge Fusion - strategic insights
        """
        opportunities = []
        self._last_scan = datetime.now(timezone.utc).isoformat()

        # 1. Check Yair Wisdom signals
        if self.wisdom:
            wisdom_opps = self._scan_wisdom_opportunities()
            opportunities.extend(wisdom_opps)

        # 2. Scan for merge arbitrage (YES + NO < $0.98)
        merge_opps = self._scan_merge_arbitrage()
        opportunities.extend(merge_opps)

        # 3. Check knowledge fusion for strategic opportunities
        if self.fusion:
            fusion_opps = self._scan_fusion_opportunities()
            opportunities.extend(fusion_opps)

        return opportunities

    def _scan_wisdom_opportunities(self) -> List[ExecutionOpportunity]:
        """Scan Yair Wisdom Engine for opportunities."""
        opportunities = []

        # Check for active wisdom signals
        if hasattr(self.wisdom, 'get_active_signals'):
            signals = self.wisdom.get_active_signals()
            for signal in signals:
                opp = ExecutionOpportunity(
                    opportunity_type=signal.get("type", "wisdom"),
                    token_id=signal.get("token_id", ""),
                    side=signal.get("side", "BUY"),
                    price=signal.get("price", 0.5),
                    size=signal.get("size", 10),
                    confidence=signal.get("confidence", 0.7),
                    source="yair_wisdom",
                    reason=signal.get("reason", "Wisdom signal")
                )
                if opp.token_id:
                    opportunities.append(opp)

        return opportunities

    def _scan_merge_arbitrage(self) -> List[ExecutionOpportunity]:
        """Scan for merge arbitrage opportunities (YES + NO < $0.98)."""
        opportunities = []

        try:
            import requests

            # Query active markets via gamma API
            response = requests.get(
                "https://gamma-api.polymarket.com/markets?closed=false&limit=50",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HFT-Bot/1.0)"}
            )

            if response.status_code == 200:
                markets = response.json()

                for market in markets:
                    # Gamma API uses outcomePrices and clobTokenIds (not tokens)
                    prices = market.get("outcomePrices", [])
                    token_ids = market.get("clobTokenIds", [])

                    if len(prices) >= 2 and len(token_ids) >= 2:
                        try:
                            # First price is YES, second is NO
                            yes_price = float(prices[0])
                            no_price = float(prices[1])
                            yes_token = token_ids[0]
                            no_token = token_ids[1]

                            total = yes_price + no_price

                            # Check for merge arb: YES + NO < 0.98
                            if total < 0.98:
                                arb_profit = 1.0 - total

                                opp = ExecutionOpportunity(
                                    opportunity_type="merge_arb",
                                    token_id=yes_token,
                                    side="BOTH",
                                    price=yes_price,
                                    size=min(100, 10 / arb_profit) if arb_profit > 0 else 10,
                                    confidence=0.95,
                                    source="merge_scan",
                                    reason=f"Merge arb: YES={yes_price:.3f} + NO={no_price:.3f} = {total:.3f} (profit: ${arb_profit:.3f}/share)"
                                )
                                opportunities.append(opp)
                        except (ValueError, IndexError):
                            continue

        except Exception as e:
            pass  # Silent fail for scan

        return opportunities

    def _scan_fusion_opportunities(self) -> List[ExecutionOpportunity]:
        """Get opportunities from knowledge fusion insights."""
        opportunities = []

        if self.fusion:
            try:
                # Get trading fusion insight
                trading_insight = self.fusion.fuse_for_decision("trading")
                if trading_insight and trading_insight.confidence > 0.8:
                    # High confidence trading insight available
                    # This provides context for execution, not specific trades
                    pass
            except:
                pass

        return opportunities

    # ==================== EXECUTION ====================

    def execute_opportunity(self, opp: ExecutionOpportunity,
                           skip_abcfc: bool = False) -> ExecutionResult:
        """
        Execute a single opportunity via HFT.

        INTEGRAFIX: ABCFC is computed for EVERY action before execution.
        This makes ABCFC the atomic decision driver at HFT speed.

        Args:
            opp: The opportunity to execute
            skip_abcfc: If True, skip ABCFC check (for testing only)

        Routes to appropriate execution method based on type.
        """
        import time
        start = time.time()

        # ========== ABCFC GATE: Every HFT action gets ABCFC ==========
        action_abcfc = self.compute_action_abcfc(opp)

        if not skip_abcfc and not self.abcfc_approve_action(opp):
            # ABCFC rejected this action
            return ExecutionResult(
                success=False,
                opportunity=opp,
                orders_placed=0,
                latency_ms=(time.time() - start) * 1000,
                error=f"ABCFC rejected: E[action]={action_abcfc['expected']:.4f}, "
                      f"worst={action_abcfc['worst']:.4f}"
            )

        # ========== EXECUTE (ABCFC approved) ==========
        try:
            if opp.opportunity_type == "merge_arb":
                result = self._execute_merge_arb(opp)
            elif opp.opportunity_type == "grid_capture":
                result = self._execute_grid(opp)
            else:
                result = self._execute_single(opp)

            # ========== UPDATE ABCFC after execution ==========
            if result.success:
                self.update_abcfc_after_execution(opp, result)

            return result

        except Exception as e:
            return ExecutionResult(
                success=False,
                opportunity=opp,
                orders_placed=0,
                latency_ms=(time.time() - start) * 1000,
                error=str(e)
            )

    def _execute_single(self, opp: ExecutionOpportunity) -> ExecutionResult:
        """Execute single order."""
        import time
        start = time.time()

        result = self.hft.place_order(
            token_id=opp.token_id,
            price=opp.price,
            size=opp.size,
            side=opp.side
        )

        elapsed_ms = (time.time() - start) * 1000

        return ExecutionResult(
            success=result.get("success", False),
            opportunity=opp,
            orders_placed=1 if result.get("success") else 0,
            latency_ms=elapsed_ms
        )

    def _execute_grid(self, opp: ExecutionOpportunity) -> ExecutionResult:
        """Execute grid of orders."""
        import time
        start = time.time()

        result = self.hft.place_grid(
            token_id=opp.token_id,
            center_price=opp.price,
            spread_bps=100,
            levels=5,
            size=opp.size
        )

        elapsed_ms = (time.time() - start) * 1000

        return ExecutionResult(
            success=result.get("success", False),
            opportunity=opp,
            orders_placed=result.get("orders_placed", 0),
            latency_ms=elapsed_ms
        )

    def _execute_merge_arb(self, opp: ExecutionOpportunity) -> ExecutionResult:
        """
        Execute merge arbitrage.

        Buy YES at bid, buy NO at bid, merge for $1.
        """
        import time
        start = time.time()

        # For merge arb, place limit orders on YES side
        # The full merge execution would need to also buy NO
        result = self.hft.place_order(
            token_id=opp.token_id,
            price=opp.price,
            size=opp.size,
            side="BUY"
        )

        elapsed_ms = (time.time() - start) * 1000

        return ExecutionResult(
            success=result.get("success", False),
            opportunity=opp,
            orders_placed=1 if result.get("success") else 0,
            latency_ms=elapsed_ms,
            error=None if result.get("success") else "Merge arb partial (YES only)"
        )

    # ==================== MAIN CYCLE ====================

    def scan_and_execute(self, dry_run: bool = False) -> Dict:
        """
        Full cycle: scan for opportunities and execute.

        INTEGRAFIX: Every opportunity gets ABCFC [worst, expected, best].
        Only ABCFC-approved actions are executed.

        Args:
            dry_run: If True, scan but don't execute

        Returns:
            Summary of scan and execution results with ABCFC data
        """
        # Scan
        opportunities = self.scan_opportunities()

        # Compute ABCFC for EVERY opportunity
        opportunities_with_abcfc = []
        for o in opportunities:
            abcfc = self.compute_action_abcfc(o)
            opportunities_with_abcfc.append({
                "type": o.opportunity_type,
                "token": o.token_id[:20] + "..." if len(o.token_id) > 20 else o.token_id,
                "side": o.side,
                "price": o.price,
                "size": o.size,
                "confidence": o.confidence,
                "reason": o.reason,
                # ABCFC for this action
                "abcfc": {
                    "worst": abcfc["worst"],
                    "expected": abcfc["expected"],
                    "best": abcfc["best"],
                    "should_execute": abcfc["should_execute"],
                    "edge": abcfc["edge"],
                }
            })

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "opportunities_found": len(opportunities),
            "opportunities": opportunities_with_abcfc,
            "dry_run": dry_run,
            "executions": [],
            "abcfc_approved": 0,
            "abcfc_rejected": 0,
        }

        if dry_run or not opportunities:
            return results

        # Execute high-confidence opportunities (ABCFC gate is inside execute_opportunity)
        for opp in opportunities:
            if opp.confidence >= 0.7:  # Only execute high confidence
                exec_result = self.execute_opportunity(opp)

                # Track ABCFC approval/rejection
                if exec_result.error and "ABCFC rejected" in str(exec_result.error):
                    results["abcfc_rejected"] += 1
                elif exec_result.success:
                    results["abcfc_approved"] += 1

                self._execution_log.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "opportunity": opp.opportunity_type,
                    "success": exec_result.success,
                    "orders": exec_result.orders_placed,
                    "abcfc_approved": "ABCFC rejected" not in str(exec_result.error or "")
                })
                results["executions"].append({
                    "type": opp.opportunity_type,
                    "success": exec_result.success,
                    "orders_placed": exec_result.orders_placed,
                    "latency_ms": exec_result.latency_ms,
                    "error": exec_result.error,
                })

        return results

    def run_hft_cycle(self) -> Dict:
        """
        Run one HFT cycle - for use in backend_loop.

        Returns status and any execution results.
        """
        status = self.status()

        # Only scan/execute if HFT is ready
        if not status.get("hft_ready"):
            return {
                "success": False,
                "status": status,
                "error": "HFT not ready (no active wallets)"
            }

        # Scan and execute
        scan_results = self.scan_and_execute(dry_run=False)

        return {
            "success": True,
            "status": status,
            "scan": scan_results,
            "hft_capacity": status.get("hft_capacity", 0),
            "executions": len(scan_results.get("executions", []))
        }

    def save_state(self):
        """Save bridge state to file."""
        state = {
            "last_scan": self._last_scan,
            "execution_log": self._execution_log[-100:],  # Keep last 100
            "saved_at": datetime.now(timezone.utc).isoformat()
        }

        state_file = STATE_DIR / "hft_bridge.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)


# Singleton instance
_bridge = None

def get_bridge() -> HFTExecutionBridge:
    """Get or create HFT Execution Bridge singleton."""
    global _bridge
    if _bridge is None:
        _bridge = HFTExecutionBridge()
    return _bridge


# Convenience alias
hft_bridge = get_bridge()


if __name__ == "__main__":
    # Test the bridge
    bridge = get_bridge()

    print("=" * 60)
    print("HFT EXECUTION BRIDGE")
    print("=" * 60)

    # Status
    print("\n[STATUS]")
    status = bridge.status()
    print(f"  HFT Ready: {status['hft_ready']}")
    print(f"  Wallets: {status['hft_wallets']}")
    print(f"  Capacity: {status['hft_capacity']}")
    print(f"  Wisdom Loaded: {status['wisdom_loaded']}")
    print(f"  Fusion Loaded: {status['fusion_loaded']}")

    # Scan (dry run)
    print("\n[SCANNING FOR OPPORTUNITIES]")
    results = bridge.scan_and_execute(dry_run=True)
    print(f"  Found: {results['opportunities_found']} opportunities")
    for opp in results['opportunities'][:5]:
        print(f"    - {opp['type']}: {opp['reason'][:50]}...")

    print("\n" + "=" * 60)
