#!/usr/bin/env python3
"""
Polymarket Order Convenience Methods

Simple interface for all order types on YES and NO tokens.

USAGE:
    from executor.polymarket_orders import orders

    # Limit orders
    orders.limit_buy_yes(market_slug, price=0.40, size=10)
    orders.limit_sell_yes(market_slug, price=0.60, size=10)
    orders.limit_buy_no(market_slug, price=0.30, size=10)
    orders.limit_sell_no(market_slug, price=0.70, size=10)

    # Market orders (take best available)
    orders.market_buy_yes(market_slug, size=10)
    orders.market_sell_yes(market_slug, size=10)
    orders.market_buy_no(market_slug, size=10)
    orders.market_sell_no(market_slug, size=10)

    # Split/Merge (on-chain)
    orders.split(market, amount)   # $1 USDC -> 1 YES + 1 NO
    orders.merge(market, amount)   # 1 YES + 1 NO -> $1 USDC

Serving: Yair Siegel
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class Market:
    """Market info with YES and NO token IDs."""
    condition_id: str
    question: str
    yes_token_id: str
    no_token_id: str
    yes_price: float
    no_price: float


class PolymarketOrders:
    """
    Convenience methods for all Polymarket order types.

    All 8 combinations supported:
    - LIMIT BUY YES
    - LIMIT SELL YES
    - LIMIT BUY NO
    - LIMIT SELL NO
    - MARKET BUY YES
    - MARKET SELL YES
    - MARKET BUY NO
    - MARKET SELL NO
    """

    def __init__(self):
        self._client = None
        self._market_cache = {}

    @property
    def client(self):
        """Get or create CLOB client."""
        if self._client is None:
            from py_clob_client.client import ClobClient

            private_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
            funder = os.environ.get("POLYMARKET_FUNDER_ADDRESS")

            if not private_key:
                raise ValueError("POLYMARKET_PRIVATE_KEY not set")

            self._client = ClobClient(
                "https://clob.polymarket.com",
                key=private_key,
                chain_id=137,
                funder=funder
            )
            creds = self._client.create_or_derive_api_creds()
            self._client.set_api_creds(creds)

        return self._client

    # ==================== MARKET LOOKUP ====================

    def get_market(self, identifier: str) -> Market:
        """
        Get market info by slug, condition_id, or token_id.

        Args:
            identifier: Market slug, condition_id, or token_id

        Returns:
            Market object with YES/NO token IDs
        """
        if identifier in self._market_cache:
            return self._market_cache[identifier]

        # Helper to parse market response
        def parse_market(m):
            # clobTokenIds and outcomePrices may be JSON strings or lists
            tokens = m.get("clobTokenIds", [])
            prices = m.get("outcomePrices", [])

            # Parse if they are strings
            if isinstance(tokens, str):
                tokens = json.loads(tokens) if tokens else []
            if isinstance(prices, str):
                prices = json.loads(prices) if prices else []

            return Market(
                condition_id=m.get("conditionId", ""),
                question=m.get("question", identifier),
                yes_token_id=tokens[0] if len(tokens) > 0 else "",
                no_token_id=tokens[1] if len(tokens) > 1 else "",
                yes_price=float(prices[0]) if len(prices) > 0 else 0.5,
                no_price=float(prices[1]) if len(prices) > 1 else 0.5
            )

        # Try gamma API with slug parameter
        try:
            response = requests.get(
                f"https://gamma-api.polymarket.com/markets?slug={identifier}",
                timeout=10
            )
            if response.status_code == 200:
                markets = response.json()
                if markets:
                    market = parse_market(markets[0])
                    self._market_cache[identifier] = market
                    return market
        except Exception as e:
            pass  # Silently try next method

        # Try fetching all markets and searching by slug
        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets?closed=false&limit=100",
                timeout=10
            )
            if response.status_code == 200:
                markets = response.json()
                for m in markets:
                    if m.get("slug") == identifier:
                        market = parse_market(m)
                        self._market_cache[identifier] = market
                        return market
        except:
            pass

        # Try searching by condition_id
        try:
            response = requests.get(
                f"https://gamma-api.polymarket.com/markets?conditionId={identifier}",
                timeout=10
            )
            if response.status_code == 200:
                markets = response.json()
                if markets:
                    market = parse_market(markets[0])
                    self._market_cache[identifier] = market
                    return market
        except:
            pass

        # If identifier looks like a token_id, use it directly
        if len(identifier) > 20 and identifier.isdigit():
            return Market(
                condition_id="",
                question="Direct token",
                yes_token_id=identifier,
                no_token_id="",
                yes_price=0.5,
                no_price=0.5
            )

        raise ValueError(f"Could not find market: {identifier}")

    def get_token_ids(self, market: str) -> Tuple[str, str]:
        """Get (yes_token_id, no_token_id) for a market."""
        m = self.get_market(market)
        return m.yes_token_id, m.no_token_id

    # ==================== LIMIT ORDERS ====================

    def limit_buy_yes(self, market: str, price: float, size: float) -> Dict:
        """
        Place limit order to BUY YES tokens.

        Args:
            market: Market slug or token_id
            price: Price per YES token (0.001 - 0.999)
            size: Number of tokens to buy

        Returns:
            Order result
        """
        yes_token, _ = self.get_token_ids(market)
        return self._place_limit_order(yes_token, price, size, "BUY")

    def limit_sell_yes(self, market: str, price: float, size: float) -> Dict:
        """Place limit order to SELL YES tokens."""
        yes_token, _ = self.get_token_ids(market)
        return self._place_limit_order(yes_token, price, size, "SELL")

    def limit_buy_no(self, market: str, price: float, size: float) -> Dict:
        """Place limit order to BUY NO tokens."""
        _, no_token = self.get_token_ids(market)
        return self._place_limit_order(no_token, price, size, "BUY")

    def limit_sell_no(self, market: str, price: float, size: float) -> Dict:
        """Place limit order to SELL NO tokens."""
        _, no_token = self.get_token_ids(market)
        return self._place_limit_order(no_token, price, size, "SELL")

    # ==================== MARKET ORDERS ====================

    def market_buy_yes(self, market: str, size: float) -> Dict:
        """
        Market order to BUY YES tokens (take best ask).

        Args:
            market: Market slug or token_id
            size: Number of tokens to buy

        Returns:
            Order result
        """
        yes_token, _ = self.get_token_ids(market)
        # Get best ask price and add small buffer
        book = self.client.get_order_book(yes_token)
        if book.asks:
            price = float(book.asks[0].price) + 0.01
        else:
            price = 0.99
        return self._place_market_order(yes_token, price, size, "BUY")

    def market_sell_yes(self, market: str, size: float) -> Dict:
        """Market order to SELL YES tokens (hit best bid)."""
        yes_token, _ = self.get_token_ids(market)
        book = self.client.get_order_book(yes_token)
        if book.bids:
            price = float(book.bids[0].price) - 0.01
        else:
            price = 0.01
        return self._place_market_order(yes_token, price, size, "SELL")

    def market_buy_no(self, market: str, size: float) -> Dict:
        """Market order to BUY NO tokens (take best ask)."""
        _, no_token = self.get_token_ids(market)
        book = self.client.get_order_book(no_token)
        if book.asks:
            price = float(book.asks[0].price) + 0.01
        else:
            price = 0.99
        return self._place_market_order(no_token, price, size, "BUY")

    def market_sell_no(self, market: str, size: float) -> Dict:
        """Market order to SELL NO tokens (hit best bid)."""
        _, no_token = self.get_token_ids(market)
        book = self.client.get_order_book(no_token)
        if book.bids:
            price = float(book.bids[0].price) - 0.01
        else:
            price = 0.01
        return self._place_market_order(no_token, price, size, "SELL")

    # ==================== INTERNAL ====================

    def _place_limit_order(self, token_id: str, price: float, size: float, side: str) -> Dict:
        """Place a limit order (GTC)."""
        from py_clob_client.order_builder.constants import BUY, SELL

        order_side = BUY if side == "BUY" else SELL

        try:
            order = self.client.create_order({
                "token_id": token_id,
                "price": price,
                "size": size,
                "side": order_side
            })
            result = self.client.post_order(order)
            return {
                "success": True,
                "type": "LIMIT",
                "side": side,
                "price": price,
                "size": size,
                "order": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _place_market_order(self, token_id: str, price: float, size: float, side: str) -> Dict:
        """Place a market order (FOK - Fill or Kill)."""
        from py_clob_client.order_builder.constants import BUY, SELL
        from py_clob_client.clob_types import OrderType

        order_side = BUY if side == "BUY" else SELL

        try:
            order = self.client.create_order({
                "token_id": token_id,
                "price": price,
                "size": size,
                "side": order_side,
                "order_type": OrderType.FOK  # Fill or Kill = market order
            })
            result = self.client.post_order(order)
            return {
                "success": True,
                "type": "MARKET",
                "side": side,
                "size": size,
                "order": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== UTILITIES ====================

    def cancel_all(self) -> Dict:
        """Cancel all open orders."""
        try:
            result = self.client.cancel_all()
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_open_orders(self) -> List[Dict]:
        """Get all open orders."""
        return self.client.get_orders()

    def get_book(self, market: str, side: str = "YES") -> Dict:
        """Get order book for a market."""
        yes_token, no_token = self.get_token_ids(market)
        token = yes_token if side.upper() == "YES" else no_token

        book = self.client.get_order_book(token)
        return {
            "bids": [(float(b.price), float(b.size)) for b in book.bids[:5]],
            "asks": [(float(a.price), float(a.size)) for a in book.asks[:5]]
        }

    def status(self) -> Dict:
        """Get current status."""
        orders = self.get_open_orders()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "open_orders": len(orders),
            "cached_markets": len(self._market_cache),
            "connected": self._client is not None
        }

    # ==================== REWARDS ====================

    def get_reward_config(self, market: str) -> Dict:
        """
        Get reward configuration for a market.

        Returns:
            {
                "rewards_enabled": bool,
                "min_size": float,      # Minimum order size for rewards
                "max_spread": float,    # Max distance from midpoint (cents)
                "midpoint": float,      # Current midpoint price
                "reward_range": (low, high)  # Price range for rewards
            }
        """
        try:
            # Fetch market with reward fields
            response = requests.get(
                f"https://gamma-api.polymarket.com/markets?slug={market}",
                timeout=10
            )
            if response.status_code == 200:
                markets = response.json()
                if markets:
                    m = markets[0]

                    # Parse prices
                    prices = m.get("outcomePrices", [])
                    if isinstance(prices, str):
                        prices = json.loads(prices) if prices else []

                    yes_price = float(prices[0]) if len(prices) > 0 else 0.5
                    no_price = float(prices[1]) if len(prices) > 1 else 0.5

                    # Get reward params
                    min_size = m.get("rewardsMinSize", 100)
                    max_spread = m.get("rewardsMaxSpread", 3.5)  # cents
                    max_spread_decimal = max_spread / 100  # convert to decimal

                    # Calculate midpoint
                    best_bid = float(m.get("bestBid", yes_price - 0.01))
                    best_ask = float(m.get("bestAsk", yes_price + 0.01))
                    midpoint = (best_bid + best_ask) / 2

                    # Reward-eligible price range
                    low = max(0.001, midpoint - max_spread_decimal)
                    high = min(0.999, midpoint + max_spread_decimal)

                    return {
                        "rewards_enabled": True,
                        "min_size": min_size,
                        "max_spread": max_spread,
                        "max_spread_decimal": max_spread_decimal,
                        "midpoint": midpoint,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "reward_range": (low, high),
                        "two_sided_required": midpoint < 0.10,
                        "holding_rewards": m.get("holdingRewardsEnabled", False)
                    }
        except:
            pass

        return {"rewards_enabled": False, "error": "Could not fetch reward config"}

    def is_reward_eligible(self, market: str, price: float, size: float) -> Dict:
        """
        Check if an order would be eligible for rewards.

        Args:
            market: Market slug
            price: Order price
            size: Order size

        Returns:
            {"eligible": bool, "reason": str}
        """
        config = self.get_reward_config(market)

        if not config.get("rewards_enabled"):
            return {"eligible": False, "reason": "Rewards not enabled for this market"}

        # Check size
        if size < config["min_size"]:
            return {
                "eligible": False,
                "reason": f"Size ${size} below minimum ${config['min_size']}"
            }

        # Check spread
        low, high = config["reward_range"]
        if price < low or price > high:
            return {
                "eligible": False,
                "reason": f"Price {price:.3f} outside reward range [{low:.3f}, {high:.3f}]"
            }

        # Check two-sided requirement
        if config.get("two_sided_required"):
            return {
                "eligible": True,
                "reason": "Eligible but requires two-sided orders (midpoint < $0.10)",
                "requires_two_sided": True
            }

        return {"eligible": True, "reason": "Order qualifies for rewards"}

    def place_reward_order(self, market: str, size: float, side: str = "BOTH") -> Dict:
        """
        Place reward-optimized order(s) close to midpoint.

        Args:
            market: Market slug
            size: Order size (must meet minimum)
            side: "YES", "NO", or "BOTH" (recommended for max rewards)

        Returns:
            Order results with reward eligibility
        """
        config = self.get_reward_config(market)

        if not config.get("rewards_enabled"):
            return {"success": False, "error": "Rewards not enabled"}

        if size < config["min_size"]:
            return {
                "success": False,
                "error": f"Size ${size} below reward minimum ${config['min_size']}"
            }

        results = {"success": True, "orders": [], "config": config}
        midpoint = config["midpoint"]

        # Place slightly inside the spread for better reward scoring
        offset = config["max_spread_decimal"] * 0.5  # 50% into reward zone

        yes_token, no_token = self.get_token_ids(market)

        if side in ["YES", "BOTH"]:
            # Buy YES below midpoint
            yes_price = round(midpoint - offset, 3)
            yes_price = max(0.001, min(0.999, yes_price))

            result = self._place_limit_order(yes_token, yes_price, size, "BUY")
            result["reward_eligible"] = True
            result["distance_from_mid"] = abs(midpoint - yes_price)
            results["orders"].append({"side": "YES", "result": result})

        if side in ["NO", "BOTH"]:
            # Buy NO (complement) - price should be 1 - yes_price area
            no_midpoint = 1 - midpoint
            no_price = round(no_midpoint - offset, 3)
            no_price = max(0.001, min(0.999, no_price))

            result = self._place_limit_order(no_token, no_price, size, "BUY")
            result["reward_eligible"] = True
            result["distance_from_mid"] = abs(no_midpoint - no_price)
            results["orders"].append({"side": "NO", "result": result})

        results["two_sided"] = side == "BOTH"
        results["reward_multiplier"] = "~3x" if side == "BOTH" else "1x"

        return results

    def estimate_rewards(self, market: str, size: float, hours: float = 24) -> Dict:
        """
        Estimate potential rewards for providing liquidity.

        Based on historical data: ~$1 reward per $846 volume (July data)
        During high incentive periods: ~$1 per $73 liquidity

        Args:
            market: Market slug
            size: Order size
            hours: Hours of liquidity provision

        Returns:
            Reward estimate
        """
        config = self.get_reward_config(market)

        if not config.get("rewards_enabled"):
            return {"estimate": 0, "error": "Rewards not enabled"}

        # Conservative estimate based on historical ratios
        # Normal: $1 per $846 volume
        # High incentive: $1 per $73 liquidity

        # Assume normal conditions, two-sided bonus
        base_rate = size / 846  # $ per day at normal rate
        two_sided_multiplier = 2.5  # ~3x for two-sided

        daily_estimate = base_rate * two_sided_multiplier
        hourly_estimate = daily_estimate / 24

        return {
            "size": size,
            "hours": hours,
            "daily_estimate": round(daily_estimate, 4),
            "period_estimate": round(hourly_estimate * hours, 4),
            "assumptions": "Normal reward rate, two-sided orders",
            "note": "Actual rewards depend on competition and market activity"
        }

    def project_profit(self, market: str, size: float, days: int = 30,
                       n_simulations: int = 10000) -> Dict:
        """
        Monte Carlo profit projection with probability distribution.

        Returns best case, worst case, expected value, and probability
        distribution across possible outcomes.

        Args:
            market: Market slug
            size: Position size in USDC
            days: Projection period
            n_simulations: Number of Monte Carlo trials

        Returns:
            {
                "expected": float,
                "best_case": float (95th percentile),
                "worst_case": float (5th percentile),
                "std_dev": float,
                "distribution": {p5, p25, p50, p75, p95},
                "probability_profitable": float,
                "var_95": float (Value at Risk)
            }
        """
        import random

        config = self.get_reward_config(market)
        m = self.get_market(market)

        # Parameters for simulation
        yes_price = m.yes_price
        no_price = m.no_price

        # Volatility estimate (higher for prices near 0.5, lower near extremes)
        base_volatility = 0.02  # 2% daily base volatility
        price_factor = 4 * yes_price * (1 - yes_price)  # peaks at 0.5
        daily_volatility = base_volatility * (0.5 + price_factor)

        # Reward rate uncertainty
        reward_base = size / 846 * 2.5  # Base daily reward (two-sided)
        reward_volatility = 0.5  # 50% uncertainty in rewards

        # Fill rate uncertainty (how often orders get filled)
        fill_rate_mean = 0.3  # 30% of orders fill on average
        fill_rate_std = 0.15

        results = []

        for _ in range(n_simulations):
            total_pnl = 0
            price = yes_price

            for day in range(days):
                # Price movement (random walk)
                price_change = random.gauss(0, daily_volatility)
                new_price = max(0.01, min(0.99, price + price_change))

                # Trading PnL from price movement (if holding position)
                position_pnl = size * (new_price - price) * random.choice([-1, 1])

                # Reward income (with uncertainty)
                daily_reward = reward_base * (1 + random.gauss(0, reward_volatility))
                daily_reward = max(0, daily_reward)

                # Fill-based trading profit
                fill_rate = max(0, min(1, random.gauss(fill_rate_mean, fill_rate_std)))
                spread_capture = size * 0.01 * fill_rate  # 1% spread capture

                total_pnl += daily_reward + spread_capture + position_pnl * 0.1
                price = new_price

            results.append(total_pnl)

        # Sort for percentile calculation
        results.sort()

        def percentile(data, p):
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]

        mean = sum(results) / len(results)
        variance = sum((x - mean) ** 2 for x in results) / len(results)
        std_dev = variance ** 0.5

        profitable_count = sum(1 for r in results if r > 0)

        return {
            "market": market,
            "size": size,
            "days": days,
            "simulations": n_simulations,

            # Core projections
            "expected": round(mean, 2),
            "std_dev": round(std_dev, 2),

            # Distribution
            "worst_case": round(percentile(results, 5), 2),   # 5th percentile
            "pessimistic": round(percentile(results, 25), 2), # 25th percentile
            "median": round(percentile(results, 50), 2),      # 50th percentile
            "optimistic": round(percentile(results, 75), 2),  # 75th percentile
            "best_case": round(percentile(results, 95), 2),   # 95th percentile

            # Risk metrics
            "probability_profitable": round(profitable_count / n_simulations * 100, 1),
            "var_95": round(-percentile(results, 5), 2),  # 95% VaR (positive = loss)

            # Annualized
            "annualized_return": round(mean / size * (365 / days) * 100, 1) if size > 0 else 0,
            "sharpe_estimate": round(mean / std_dev * (365 / days) ** 0.5, 2) if std_dev > 0 else 0
        }

    def plot_profit_projection(self, market: str, size: float, days: int = 30,
                                entry_price: float = None, save_path: str = None) -> Dict:
        """
        Generate profit projection chart with probability distribution.

        Creates visualization with:
        - Expected profit line
        - Absolute best case line (position wins)
        - Absolute worst case line (position loses)
        - Gradient fill showing probability distribution

        Args:
            market: Market slug
            size: Position size in USDC
            days: Projection period
            entry_price: Entry price (default: current market price)
            save_path: Path to save chart

        Returns:
            Chart path and projection data
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib.colors import LinearSegmentedColormap
            import numpy as np
        except ImportError:
            return {"success": False, "error": "matplotlib not installed"}

        m = self.get_market(market)
        config = self.get_reward_config(market)

        # Use current price if not specified
        if entry_price is None:
            entry_price = m.yes_price

        # Calculate outcomes
        # Best case: market resolves YES (price goes to 1.0)
        best_payout = size * (1.0 - entry_price) / entry_price  # profit if YES wins

        # Worst case: market resolves NO (price goes to 0)
        worst_payout = -size  # lose entire position

        # Expected value based on current probability
        prob_yes = m.yes_price  # market-implied probability
        expected_payout = (prob_yes * best_payout) + ((1 - prob_yes) * worst_payout)

        # Build daily projection lines
        days_range = np.linspace(0, days, days + 1)

        # Linear interpolation to final outcomes
        best_line = (days_range / days) * best_payout
        worst_line = (days_range / days) * worst_payout
        expected_line = (days_range / days) * expected_payout

        fig, ax = plt.subplots(figsize=(12, 7))

        # Create truly continuous gradient using meshgrid
        # Higher resolution for smoother gradient
        n_x = 200  # horizontal resolution
        n_y = 400  # vertical resolution

        y_min = worst_payout * 1.05
        y_max = best_payout * 1.05

        # Create meshgrid
        x = np.linspace(0, days, n_x)
        y = np.linspace(y_min, y_max, n_y)
        X, Y = np.meshgrid(x, y)

        # For each point, calculate the "probability density"
        # Based on distance from expected value, bounded by best/worst
        density = np.zeros_like(X)

        for i in range(n_x):
            day = x[i]
            if day == 0:
                continue

            # Current day's bounds
            day_best = (day / days) * best_payout
            day_worst = (day / days) * worst_payout
            day_expected = (day / days) * expected_payout
            day_range = day_best - day_worst

            for j in range(n_y):
                y_val = y[j]

                # Only shade within the possible outcome region
                if day_worst <= y_val <= day_best and day_range > 0:
                    # Normalize position: 0 = worst, 1 = best
                    t = (y_val - day_worst) / day_range

                    # Expected position normalized
                    exp_t = (day_expected - day_worst) / day_range if day_range > 0 else 0.5

                    # Smooth Gaussian-like density centered on expected
                    # Use wider sigma for smoother gradient
                    sigma = 0.35
                    dist = abs(t - exp_t)
                    density[j, i] = np.exp(-(dist ** 2) / (2 * sigma ** 2))

        # Apply Gaussian smoothing for extra smoothness
        from scipy.ndimage import gaussian_filter
        density = gaussian_filter(density, sigma=3)

        # Normalize
        if density.max() > 0:
            density = density / density.max()

        # Plot using pcolormesh for smooth gradient (better than imshow for this)
        pcm = ax.pcolormesh(X, Y, density, cmap='Blues', shading='gouraud', alpha=0.85)

        # Plot the three main lines
        ax.plot(days_range, best_line, 'g-', linewidth=2, label=f'Best case: +${best_payout:.2f}')
        ax.plot(days_range, expected_line, 'b-', linewidth=2.5, label=f'Expected: ${expected_payout:+.2f}')
        ax.plot(days_range, worst_line, 'r-', linewidth=2, label=f'Worst case: -${size:.2f}')

        # Zero line
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.7)

        # Labels
        ax.set_xlabel('Days', fontsize=12)
        ax.set_ylabel('Profit/Loss ($)', fontsize=12)
        ax.set_title(f'Profit Projection: {market}\n${size} @ {entry_price:.2f} (P(YES)={prob_yes:.1%})', fontsize=14)
        ax.legend(loc='upper left' if expected_payout > 0 else 'lower left', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Shade profit/loss regions
        ax.axhspan(0, ax.get_ylim()[1], alpha=0.05, color='green')
        ax.axhspan(ax.get_ylim()[0], 0, alpha=0.05, color='red')

        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/profit_projection.png'

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "market": market,
            "size": size,
            "entry_price": entry_price,
            "prob_yes": round(prob_yes, 4),
            "best_case": round(best_payout, 2),
            "expected": round(expected_payout, 2),
            "worst_case": round(worst_payout, 2),
            "days": days
        }

    def plot_profit_projection_old(self, market: str, size: float, days: int = 30,
                                n_simulations: int = 1000, save_path: str = None) -> Dict:
        """
        Generate profit projection chart with probability distribution.

        Creates visualization with:
        - Expected profit line (median)
        - Best/worst case bounds (5th/95th percentile)
        - Gradient fill showing probability distribution

        Args:
            market: Market slug
            size: Position size in USDC
            days: Projection period
            n_simulations: Number of Monte Carlo paths
            save_path: Optional path to save chart (default: /tmp/profit_projection.png)

        Returns:
            Path to saved chart and projection data
        """
        import random

        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors
        except ImportError:
            return {"success": False, "error": "matplotlib not installed. Run: pip install matplotlib"}

        config = self.get_reward_config(market)
        m = self.get_market(market)

        # Simulation parameters
        yes_price = m.yes_price
        base_volatility = 0.02
        price_factor = 4 * yes_price * (1 - yes_price)
        daily_volatility = base_volatility * (0.5 + price_factor)
        reward_base = size / 846 * 2.5
        reward_volatility = 0.5
        fill_rate_mean = 0.3
        fill_rate_std = 0.15

        # Run simulations and track daily values
        all_paths = []

        for _ in range(n_simulations):
            path = [0]  # Start at 0 profit
            price = yes_price
            cumulative = 0

            for day in range(days):
                price_change = random.gauss(0, daily_volatility)
                new_price = max(0.01, min(0.99, price + price_change))
                position_pnl = size * (new_price - price) * random.choice([-1, 1])
                daily_reward = max(0, reward_base * (1 + random.gauss(0, reward_volatility)))
                fill_rate = max(0, min(1, random.gauss(fill_rate_mean, fill_rate_std)))
                spread_capture = size * 0.01 * fill_rate

                cumulative += daily_reward + spread_capture + position_pnl * 0.1
                path.append(cumulative)
                price = new_price

            all_paths.append(path)

        # Calculate percentiles for each day
        days_range = list(range(days + 1))
        p5 = []
        p25 = []
        p50 = []
        p75 = []
        p95 = []

        for day_idx in range(days + 1):
            day_values = sorted([path[day_idx] for path in all_paths])
            n = len(day_values)
            p5.append(day_values[int(n * 0.05)])
            p25.append(day_values[int(n * 0.25)])
            p50.append(day_values[int(n * 0.50)])
            p75.append(day_values[int(n * 0.75)])
            p95.append(day_values[int(n * 0.95)])

        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 7))

        # Gradient fill for probability distribution
        # Outer band (5-95%)
        ax.fill_between(days_range, p5, p95, alpha=0.2, color='blue', label='90% probability range')
        # Middle band (25-75%)
        ax.fill_between(days_range, p25, p75, alpha=0.3, color='blue', label='50% probability range')

        # Lines
        ax.plot(days_range, p50, 'b-', linewidth=2.5, label='Expected (median)')
        ax.plot(days_range, p95, 'g--', linewidth=1.5, label=f'Best case (95%): ${p95[-1]:.2f}')
        ax.plot(days_range, p5, 'r--', linewidth=1.5, label=f'Worst case (5%): ${p5[-1]:.2f}')

        # Zero line
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)

        # Labels and title
        ax.set_xlabel('Days', fontsize=12)
        ax.set_ylabel('Profit ($)', fontsize=12)
        ax.set_title(f'Profit Projection: {market}\n${size} position over {days} days ({n_simulations:,} simulations)',
                     fontsize=14)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Add annotation for final expected value
        ax.annotate(f'Expected: ${p50[-1]:.2f}',
                    xy=(days, p50[-1]),
                    xytext=(days - 5, p50[-1] + (p95[-1] - p5[-1]) * 0.2),
                    fontsize=11, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='blue'))

        plt.tight_layout()

        # Save
        if save_path is None:
            save_path = '/tmp/profit_projection.png'

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "market": market,
            "size": size,
            "days": days,
            "final_expected": round(p50[-1], 2),
            "final_best": round(p95[-1], 2),
            "final_worst": round(p5[-1], 2),
            "probability_profitable": round(sum(1 for p in all_paths if p[-1] > 0) / n_simulations * 100, 1)
        }

    # ==================== SPLIT / MERGE (ON-CHAIN) ====================

    def _get_web3(self):
        """Get or create Web3 instance for Polygon."""
        if not hasattr(self, '_web3') or self._web3 is None:
            from web3 import Web3
            # Polygon RPC
            rpc_url = os.environ.get("POLYGON_RPC_URL", "https://polygon-rpc.com")
            self._web3 = Web3(Web3.HTTPProvider(rpc_url))
        return self._web3

    def _get_ctf_exchange(self):
        """Get CTF Exchange contract instance."""
        if not hasattr(self, '_ctf_exchange') or self._ctf_exchange is None:
            w3 = self._get_web3()

            # CTF Exchange address on Polygon
            CTF_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"

            # Minimal ABI for split/merge operations
            CTF_ABI = [
                {
                    "inputs": [
                        {"name": "collateralToken", "type": "address"},
                        {"name": "parentCollectionId", "type": "bytes32"},
                        {"name": "conditionId", "type": "bytes32"},
                        {"name": "partition", "type": "uint256[]"},
                        {"name": "amount", "type": "uint256"}
                    ],
                    "name": "splitPosition",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"name": "collateralToken", "type": "address"},
                        {"name": "parentCollectionId", "type": "bytes32"},
                        {"name": "conditionId", "type": "bytes32"},
                        {"name": "partition", "type": "uint256[]"},
                        {"name": "amount", "type": "uint256"}
                    ],
                    "name": "mergePositions",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]

            self._ctf_exchange = w3.eth.contract(
                address=w3.to_checksum_address(CTF_EXCHANGE),
                abi=CTF_ABI
            )
        return self._ctf_exchange

    def split(self, market: str, amount: float) -> Dict:
        """
        Split USDC into YES and NO tokens.

        $1 USDC -> 1 YES token + 1 NO token
        MINIMUM: $1 USDC

        Args:
            market: Market slug or condition_id
            amount: Amount of USDC to split (minimum $1)

        Returns:
            Transaction result
        """
        # Minimum $1 for split
        if amount < 1.0:
            return {"success": False, "error": f"Minimum split is $1 USDC (got ${amount})"}

        try:
            w3 = self._get_web3()
            ctf = self._get_ctf_exchange()

            # Get market info
            m = self.get_market(market)
            condition_id = m.condition_id

            if not condition_id:
                return {"success": False, "error": "Could not find condition_id for market"}

            # USDC on Polygon (6 decimals)
            USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

            # Convert amount to USDC wei (6 decimals)
            amount_wei = int(amount * 1_000_000)

            # Parent collection ID (0x0 for root)
            parent_collection = bytes(32)

            # Partition for binary outcome: [1, 2] = [YES, NO]
            partition = [1, 2]

            # Get private key
            private_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
            if not private_key:
                return {"success": False, "error": "POLYMARKET_PRIVATE_KEY not set"}

            # Get account
            account = w3.eth.account.from_key(private_key)

            # Build transaction
            tx = ctf.functions.splitPosition(
                w3.to_checksum_address(USDC),
                parent_collection,
                bytes.fromhex(condition_id[2:] if condition_id.startswith("0x") else condition_id),
                partition,
                amount_wei
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'chainId': 137  # Polygon
            })

            # Sign and send
            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            return {
                "success": receipt.status == 1,
                "type": "SPLIT",
                "amount": amount,
                "tx_hash": tx_hash.hex(),
                "gas_used": receipt.gasUsed,
                "result": f"Split ${amount} USDC -> {amount} YES + {amount} NO"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def merge(self, market: str, amount: float) -> Dict:
        """
        Merge YES and NO tokens back into USDC.

        1 YES token + 1 NO token -> $1 USDC

        Args:
            market: Market slug or condition_id
            amount: Amount of token pairs to merge (e.g., 100 = 100 YES + 100 NO -> $100)

        Returns:
            Transaction result
        """
        try:
            w3 = self._get_web3()
            ctf = self._get_ctf_exchange()

            # Get market info
            m = self.get_market(market)
            condition_id = m.condition_id

            if not condition_id:
                return {"success": False, "error": "Could not find condition_id for market"}

            # USDC on Polygon (6 decimals)
            USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

            # Convert amount to USDC wei (6 decimals)
            amount_wei = int(amount * 1_000_000)

            # Parent collection ID (0x0 for root)
            parent_collection = bytes(32)

            # Partition for binary outcome: [1, 2] = [YES, NO]
            partition = [1, 2]

            # Get private key
            private_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
            if not private_key:
                return {"success": False, "error": "POLYMARKET_PRIVATE_KEY not set"}

            # Get account
            account = w3.eth.account.from_key(private_key)

            # Build transaction
            tx = ctf.functions.mergePositions(
                w3.to_checksum_address(USDC),
                parent_collection,
                bytes.fromhex(condition_id[2:] if condition_id.startswith("0x") else condition_id),
                partition,
                amount_wei
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'chainId': 137  # Polygon
            })

            # Sign and send
            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            return {
                "success": receipt.status == 1,
                "type": "MERGE",
                "amount": amount,
                "tx_hash": tx_hash.hex(),
                "gas_used": receipt.gasUsed,
                "result": f"Merged {amount} YES + {amount} NO -> ${amount} USDC"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def merge_arbitrage(self, market: str, max_amount: float = 100) -> Dict:
        """
        Execute merge arbitrage if profitable.

        Checks if YES + NO < $1, then:
        1. Buy YES at ask
        2. Buy NO at ask
        3. Merge for $1

        Profit = $1 - (YES price + NO price) - gas

        Args:
            market: Market slug
            max_amount: Maximum USDC to deploy

        Returns:
            Arbitrage result
        """
        try:
            m = self.get_market(market)

            total_cost = m.yes_price + m.no_price

            if total_cost >= 0.99:  # No arb opportunity (need some margin for gas)
                return {
                    "success": False,
                    "reason": f"No arb: YES({m.yes_price:.3f}) + NO({m.no_price:.3f}) = {total_cost:.3f} >= $0.99"
                }

            profit_per_share = 1.0 - total_cost

            # Calculate optimal size (limited by max_amount and available liquidity)
            size = min(max_amount / total_cost, 1000)  # Cap at 1000 shares

            # Execute: Buy YES
            yes_result = self.market_buy_yes(market, size)
            if not yes_result.get("success"):
                return {"success": False, "error": f"Failed to buy YES: {yes_result.get('error')}"}

            # Execute: Buy NO
            no_result = self.market_buy_no(market, size)
            if not no_result.get("success"):
                return {"success": False, "error": f"Failed to buy NO: {no_result.get('error')}", "partial": "YES bought"}

            # Execute: Merge
            merge_result = self.merge(market, size)
            if not merge_result.get("success"):
                return {"success": False, "error": f"Failed to merge: {merge_result.get('error')}", "partial": "YES+NO bought"}

            gross_profit = size * profit_per_share

            return {
                "success": True,
                "type": "MERGE_ARB",
                "size": size,
                "yes_cost": size * m.yes_price,
                "no_cost": size * m.no_price,
                "total_cost": size * total_cost,
                "gross_profit": gross_profit,
                "profit_per_share": profit_per_share,
                "tx_hash": merge_result.get("tx_hash")
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton
_orders = None

def get_orders() -> PolymarketOrders:
    """Get or create orders singleton."""
    global _orders
    if _orders is None:
        _orders = PolymarketOrders()
    return _orders


# Convenience alias
orders = get_orders()


# ==================== CLI ====================

if __name__ == "__main__":
    print("=" * 60)
    print("POLYMARKET ORDERS - COMPLETE TRADING INTERFACE")
    print("=" * 60)
    print("""
LIMIT ORDERS (specify price, wait for fill):
  orders.limit_buy_yes(market, price, size)
  orders.limit_sell_yes(market, price, size)
  orders.limit_buy_no(market, price, size)
  orders.limit_sell_no(market, price, size)

MARKET ORDERS (take/hit best available):
  orders.market_buy_yes(market, size)
  orders.market_sell_yes(market, size)
  orders.market_buy_no(market, size)
  orders.market_sell_no(market, size)

SPLIT / MERGE (on-chain operations):
  orders.split(market, amount)         # $100 USDC -> 100 YES + 100 NO
  orders.merge(market, amount)         # 100 YES + 100 NO -> $100 USDC
  orders.merge_arbitrage(market, max)  # Auto arb if YES + NO < $1

UTILITIES:
  orders.get_book(market, side="YES")
  orders.get_open_orders()
  orders.cancel_all()

EXAMPLES:
  # Buy YES at 40 cents
  orders.limit_buy_yes("btc-100k-2024", price=0.40, size=100)

  # Sell NO at 70 cents
  orders.limit_sell_no("btc-100k-2024", price=0.70, size=50)

  # Market buy YES (take best ask)
  orders.market_buy_yes("btc-100k-2024", size=25)

  # Split $50 into YES + NO tokens
  orders.split("btc-100k-2024", amount=50)

  # Merge arbitrage (buy YES + NO cheap, merge for $1)
  orders.merge_arbitrage("btc-100k-2024", max_amount=100)
""")

    # Quick test
    o = get_orders()
    print(f"\nStatus: {o.status()}")
