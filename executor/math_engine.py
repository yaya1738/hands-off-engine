#!/usr/bin/env python3
"""
Mathematical Calculation Engine - Core Trading Mathematics

Robust mathematical infrastructure for:
- Position sizing (Kelly, fractional Kelly)
- Risk calculations (VaR, drawdown, exposure)
- Price/spread calculations
- Grid generation
- Statistical analysis
- HFT throughput calculations

USAGE:
    from executor.math_engine import math, kelly, grid, risk, stats

    # Kelly criterion
    size = kelly.optimal_size(win_prob=0.6, odds=2.0, bankroll=10000)

    # Grid generation
    prices = grid.generate(center=0.5, spread_bps=50, levels=10)

    # Risk metrics
    var = risk.value_at_risk(returns, confidence=0.95)

    # HFT calculations
    capacity = math.hft.throughput(wallets=100, rate_per_wallet=1000)

Serving: Yair Siegel
"""

import math as _math
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
import statistics


# ==================== CONSTANTS ====================

# Polymarket specific
POLYMARKET_MIN_PRICE = Decimal("0.001")
POLYMARKET_MAX_PRICE = Decimal("0.999")
POLYMARKET_TICK_SIZE = Decimal("0.001")
POLYMARKET_MIN_SIZE = Decimal("0.01")

# Risk defaults
DEFAULT_CONFIDENCE = 0.95
MAX_POSITION_PCT = 0.25  # Max 25% of bankroll per position


# ==================== KELLY CRITERION ====================

class KellyCalculator:
    """
    Kelly Criterion for optimal position sizing.

    The Kelly formula maximizes long-term growth rate.
    f* = (bp - q) / b

    Where:
        b = odds received on the bet (net odds)
        p = probability of winning
        q = probability of losing (1 - p)
        f* = fraction of bankroll to bet
    """

    def optimal_fraction(self, win_prob: float, odds: float) -> float:
        """
        Calculate optimal Kelly fraction.

        Args:
            win_prob: Probability of winning (0-1)
            odds: Net odds (e.g., 2.0 means win $2 for every $1 bet)

        Returns:
            Optimal fraction of bankroll to bet (can be negative = don't bet)
        """
        if not 0 < win_prob < 1:
            return 0.0
        if odds <= 0:
            return 0.0

        p = win_prob
        q = 1 - p
        b = odds

        kelly_f = (b * p - q) / b

        return max(0.0, kelly_f)

    def optimal_size(self, win_prob: float, odds: float, bankroll: float,
                     fraction: float = 1.0) -> float:
        """
        Calculate optimal position size in dollars.

        Args:
            win_prob: Probability of winning (0-1)
            odds: Net odds
            bankroll: Total capital
            fraction: Kelly fraction (0.5 = half Kelly, safer)

        Returns:
            Dollar amount to bet
        """
        kelly_f = self.optimal_fraction(win_prob, odds)
        adjusted_f = kelly_f * fraction
        return bankroll * adjusted_f

    def from_market_price(self, market_price: float, true_prob: float,
                          bankroll: float, fraction: float = 0.5) -> Dict:
        """
        Calculate Kelly size from Polymarket prices.

        Args:
            market_price: Current market price (0-1)
            true_prob: Your estimated true probability (0-1)
            bankroll: Total capital
            fraction: Kelly fraction (default 0.5 = half Kelly)

        Returns:
            {"side": "BUY"|"SELL", "size": float, "edge": float}
        """
        # Calculate edge
        if true_prob > market_price:
            # Market underprices YES - BUY
            side = "BUY"
            # Odds: if price is 0.4, odds are 1/0.4 - 1 = 1.5
            odds = (1 / market_price) - 1
            edge = true_prob - market_price
        else:
            # Market overprices YES - SELL (bet NO)
            side = "SELL"
            # For NO: price is 1 - market_price
            no_price = 1 - market_price
            no_true_prob = 1 - true_prob
            odds = (1 / no_price) - 1
            edge = no_true_prob - no_price
            true_prob = no_true_prob  # Use NO probability for Kelly

        if edge <= 0:
            return {"side": "NONE", "size": 0, "edge": 0, "kelly_f": 0}

        kelly_f = self.optimal_fraction(true_prob, odds)
        size = self.optimal_size(true_prob, odds, bankroll, fraction)

        # Cap at max position
        max_size = bankroll * MAX_POSITION_PCT
        size = min(size, max_size)

        return {
            "side": side,
            "size": round(size, 2),
            "edge": round(edge, 4),
            "kelly_f": round(kelly_f, 4),
            "adjusted_f": round(kelly_f * fraction, 4),
            "odds": round(odds, 2)
        }

    def multi_position(self, opportunities: List[Dict], bankroll: float,
                       max_total_exposure: float = 0.8) -> List[Dict]:
        """
        Calculate sizes for multiple simultaneous positions.

        Args:
            opportunities: List of {"market": str, "true_prob": float, "market_price": float}
            bankroll: Total capital
            max_total_exposure: Max fraction of bankroll to deploy

        Returns:
            List of position recommendations
        """
        # Calculate individual Kelly for each
        positions = []
        for opp in opportunities:
            result = self.from_market_price(
                opp["market_price"],
                opp["true_prob"],
                bankroll,
                fraction=0.5
            )
            if result["size"] > 0:
                result["market"] = opp.get("market", "unknown")
                positions.append(result)

        # Sort by edge (best first)
        positions.sort(key=lambda x: x["edge"], reverse=True)

        # Scale down if total exceeds max exposure
        total_size = sum(p["size"] for p in positions)
        max_size = bankroll * max_total_exposure

        if total_size > max_size:
            scale = max_size / total_size
            for p in positions:
                p["size"] = round(p["size"] * scale, 2)
                p["scaled"] = True

        return positions


# ==================== GRID CALCULATIONS ====================

class GridCalculator:
    """
    Grid and spread calculations for market making.
    """

    def generate(self, center: float, spread_bps: int = 100,
                 levels: int = 5, size_per_level: float = 10) -> Dict:
        """
        Generate order grid around center price.

        Args:
            center: Center price (0-1)
            spread_bps: Spread in basis points between levels
            levels: Number of levels on each side
            size_per_level: Size per order

        Returns:
            {"bids": [...], "asks": [...], "total_size": float}
        """
        spread = spread_bps / 10000  # Convert bps to decimal

        bids = []
        asks = []

        for i in range(1, levels + 1):
            offset = spread * i

            # Bid (below center)
            bid_price = center - offset
            if POLYMARKET_MIN_PRICE <= Decimal(str(bid_price)) <= POLYMARKET_MAX_PRICE:
                bids.append({
                    "price": self._round_price(bid_price),
                    "size": size_per_level,
                    "side": "BUY"
                })

            # Ask (above center)
            ask_price = center + offset
            if POLYMARKET_MIN_PRICE <= Decimal(str(ask_price)) <= POLYMARKET_MAX_PRICE:
                asks.append({
                    "price": self._round_price(ask_price),
                    "size": size_per_level,
                    "side": "SELL"
                })

        return {
            "center": center,
            "spread_bps": spread_bps,
            "bids": bids,
            "asks": asks,
            "total_orders": len(bids) + len(asks),
            "total_size": (len(bids) + len(asks)) * size_per_level
        }

    def _round_price(self, price: float) -> float:
        """Round price to Polymarket tick size."""
        d = Decimal(str(price))
        return float(d.quantize(POLYMARKET_TICK_SIZE, rounding=ROUND_HALF_UP))

    def logarithmic_grid(self, center: float, spread_pct: float = 5,
                         levels: int = 10, size_curve: str = "flat") -> Dict:
        """
        Generate logarithmically-spaced grid (tighter near center).

        Args:
            center: Center price
            spread_pct: Total spread percentage
            levels: Number of levels
            size_curve: "flat", "linear", "exponential"

        Returns:
            Grid orders
        """
        import numpy as np

        # Logarithmic spacing
        log_offsets = np.logspace(-3, 0, levels) * (spread_pct / 100)

        bids = []
        asks = []

        for i, offset in enumerate(log_offsets):
            # Size based on curve
            if size_curve == "linear":
                size = 10 * (1 + i * 0.5)
            elif size_curve == "exponential":
                size = 10 * (1.5 ** i)
            else:
                size = 10

            bid_price = center * (1 - offset)
            ask_price = center * (1 + offset)

            if 0.001 <= bid_price <= 0.999:
                bids.append({"price": self._round_price(bid_price), "size": round(size, 2), "side": "BUY"})
            if 0.001 <= ask_price <= 0.999:
                asks.append({"price": self._round_price(ask_price), "size": round(size, 2), "side": "SELL"})

        return {
            "center": center,
            "type": "logarithmic",
            "bids": bids,
            "asks": asks,
            "total_orders": len(bids) + len(asks)
        }

    def optimal_spread(self, volatility: float, inventory: float,
                       risk_aversion: float = 0.1) -> float:
        """
        Calculate optimal market maker spread (Avellaneda-Stoikov style).

        Args:
            volatility: Price volatility (standard deviation)
            inventory: Current inventory position
            risk_aversion: Risk aversion parameter

        Returns:
            Optimal spread in price units
        """
        # Simplified Avellaneda-Stoikov
        # spread = gamma * sigma^2 + (2/gamma) * ln(1 + gamma/k)
        gamma = risk_aversion
        sigma = volatility

        base_spread = gamma * (sigma ** 2)
        inventory_adjustment = abs(inventory) * gamma * sigma

        return base_spread + inventory_adjustment

    def price_levels(self, start: float, end: float, count: int) -> List[float]:
        """Generate evenly-spaced price levels."""
        if count < 2:
            return [start]
        step = (end - start) / (count - 1)
        return [self._round_price(start + i * step) for i in range(count)]


# ==================== RISK CALCULATIONS ====================

class RiskCalculator:
    """
    Risk metrics and calculations.
    """

    def value_at_risk(self, returns: List[float], confidence: float = 0.95,
                      position_size: float = 1.0) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: Historical returns (as decimals, e.g., 0.05 = 5%)
            confidence: Confidence level (0.95 = 95%)
            position_size: Position size in dollars

        Returns:
            VaR in dollars (maximum expected loss)
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        var_return = sorted_returns[max(0, index)]

        return abs(var_return * position_size)

    def expected_shortfall(self, returns: List[float],
                           confidence: float = 0.95) -> float:
        """
        Calculate Expected Shortfall (CVaR).

        Average loss in the worst (1-confidence)% of cases.
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        cutoff = int((1 - confidence) * len(sorted_returns))
        tail_returns = sorted_returns[:max(1, cutoff)]

        return abs(statistics.mean(tail_returns))

    def max_drawdown(self, equity_curve: List[float]) -> Dict:
        """
        Calculate maximum drawdown.

        Args:
            equity_curve: List of equity values over time

        Returns:
            {"max_drawdown": float, "peak_idx": int, "trough_idx": int}
        """
        if len(equity_curve) < 2:
            return {"max_drawdown": 0, "peak_idx": 0, "trough_idx": 0}

        peak = equity_curve[0]
        peak_idx = 0
        max_dd = 0
        max_dd_peak_idx = 0
        max_dd_trough_idx = 0

        for i, value in enumerate(equity_curve):
            if value > peak:
                peak = value
                peak_idx = i
            else:
                dd = (peak - value) / peak if peak > 0 else 0
                if dd > max_dd:
                    max_dd = dd
                    max_dd_peak_idx = peak_idx
                    max_dd_trough_idx = i

        return {
            "max_drawdown": round(max_dd, 4),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "peak_idx": max_dd_peak_idx,
            "trough_idx": max_dd_trough_idx
        }

    def position_risk(self, entry_price: float, current_price: float,
                      size: float, side: str) -> Dict:
        """
        Calculate current position risk metrics.

        Args:
            entry_price: Entry price
            current_price: Current market price
            size: Position size in shares
            side: "BUY" or "SELL"

        Returns:
            {"pnl": float, "pnl_pct": float, "max_loss": float}
        """
        if side == "BUY":
            pnl = (current_price - entry_price) * size
            max_loss = entry_price * size  # Price goes to 0
        else:
            pnl = (entry_price - current_price) * size
            max_loss = (1 - entry_price) * size  # Price goes to 1

        cost = entry_price * size if side == "BUY" else (1 - entry_price) * size
        pnl_pct = pnl / cost if cost > 0 else 0

        return {
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct * 100, 2),
            "max_loss": round(max_loss, 2),
            "current_value": round(current_price * size if side == "BUY" else (1 - current_price) * size, 2)
        }

    def portfolio_exposure(self, positions: List[Dict]) -> Dict:
        """
        Calculate total portfolio exposure.

        Args:
            positions: List of {"side": str, "size": float, "price": float}

        Returns:
            {"long_exposure": float, "short_exposure": float, "net": float, "gross": float}
        """
        long_exp = sum(p["size"] * p["price"] for p in positions if p["side"] == "BUY")
        short_exp = sum(p["size"] * (1 - p["price"]) for p in positions if p["side"] == "SELL")

        return {
            "long_exposure": round(long_exp, 2),
            "short_exposure": round(short_exp, 2),
            "net_exposure": round(long_exp - short_exp, 2),
            "gross_exposure": round(long_exp + short_exp, 2)
        }

    def sharpe_ratio(self, returns: List[float], risk_free: float = 0) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            returns: List of returns
            risk_free: Risk-free rate

        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0

        excess_returns = [r - risk_free for r in returns]
        avg = statistics.mean(excess_returns)
        std = statistics.stdev(excess_returns)

        return avg / std if std > 0 else 0


# ==================== STATISTICAL UTILITIES ====================

class StatisticalCalculator:
    """
    Statistical analysis utilities.
    """

    def volatility(self, prices: List[float], window: int = 20) -> float:
        """
        Calculate price volatility (rolling standard deviation of returns).

        Args:
            prices: Price series
            window: Rolling window size

        Returns:
            Annualized volatility
        """
        if len(prices) < 2:
            return 0.0

        returns = [(prices[i] - prices[i-1]) / prices[i-1]
                   for i in range(1, len(prices)) if prices[i-1] != 0]

        if len(returns) < window:
            return statistics.stdev(returns) if len(returns) > 1 else 0

        # Rolling volatility
        recent_returns = returns[-window:]
        daily_vol = statistics.stdev(recent_returns)

        # Annualize (assuming ~365 days for prediction markets)
        return daily_vol * _math.sqrt(365)

    def ewma_volatility(self, returns: List[float], decay: float = 0.94) -> float:
        """
        Exponentially weighted moving average volatility.

        Args:
            returns: Return series
            decay: Decay factor (0.94 is RiskMetrics standard)

        Returns:
            EWMA volatility
        """
        if not returns:
            return 0.0

        variance = returns[0] ** 2
        for r in returns[1:]:
            variance = decay * variance + (1 - decay) * (r ** 2)

        return _math.sqrt(variance)

    def correlation(self, series1: List[float], series2: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(series1) != len(series2) or len(series1) < 2:
            return 0.0

        n = len(series1)
        mean1 = sum(series1) / n
        mean2 = sum(series2) / n

        cov = sum((x - mean1) * (y - mean2) for x, y in zip(series1, series2)) / n
        std1 = _math.sqrt(sum((x - mean1) ** 2 for x in series1) / n)
        std2 = _math.sqrt(sum((y - mean2) ** 2 for y in series2) / n)

        if std1 == 0 or std2 == 0:
            return 0.0

        return cov / (std1 * std2)

    def mean_reversion_half_life(self, prices: List[float]) -> Optional[float]:
        """
        Calculate mean reversion half-life using Ornstein-Uhlenbeck.

        Returns None if no mean reversion detected.
        """
        if len(prices) < 10:
            return None

        # Simple AR(1) regression
        y = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        x = prices[:-1]

        n = len(y)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denom = sum((xi - mean_x) ** 2 for xi in x)

        if denom == 0:
            return None

        theta = -num / denom

        if theta <= 0:
            return None  # No mean reversion

        return _math.log(2) / theta

    def zscore(self, value: float, mean: float, std: float) -> float:
        """Calculate z-score."""
        if std == 0:
            return 0.0
        return (value - mean) / std

    def percentile(self, values: List[float], pct: float) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(pct * len(sorted_vals))
        return sorted_vals[min(idx, len(sorted_vals) - 1)]


# ==================== HFT CALCULATIONS ====================

class HFTCalculator:
    """
    High-frequency trading specific calculations.
    """

    def throughput(self, wallets: int, rate_per_wallet: int = 1000,
                   processes: int = 1, efficiency: float = 0.8) -> Dict:
        """
        Calculate theoretical throughput capacity.

        Args:
            wallets: Number of trading wallets
            rate_per_wallet: Orders/sec per wallet
            processes: Number of parallel processes
            efficiency: Efficiency factor (accounts for overhead)

        Returns:
            Throughput metrics
        """
        single_process = wallets * rate_per_wallet
        multi_process = single_process * processes * efficiency

        return {
            "wallets": wallets,
            "rate_per_wallet": rate_per_wallet,
            "single_process_max": single_process,
            "multi_process_max": int(multi_process),
            "processes": processes,
            "efficiency": efficiency,
            "wallets_for_1m": _math.ceil(1_000_000 / (rate_per_wallet * efficiency))
        }

    def latency_percentiles(self, latencies: List[float]) -> Dict:
        """
        Calculate latency percentiles.

        Args:
            latencies: List of latency measurements (ms)

        Returns:
            Percentile breakdown
        """
        if not latencies:
            return {}

        sorted_lat = sorted(latencies)
        n = len(sorted_lat)

        return {
            "min": sorted_lat[0],
            "p50": sorted_lat[int(n * 0.5)],
            "p90": sorted_lat[int(n * 0.9)],
            "p95": sorted_lat[int(n * 0.95)],
            "p99": sorted_lat[min(int(n * 0.99), n - 1)],
            "max": sorted_lat[-1],
            "mean": sum(latencies) / n
        }

    def optimal_batch_size(self, network_latency_ms: float,
                           processing_time_per_order_ms: float,
                           max_latency_ms: float = 100) -> int:
        """
        Calculate optimal batch size for order submission.

        Args:
            network_latency_ms: Network round-trip time
            processing_time_per_order_ms: Time to process each order
            max_latency_ms: Maximum acceptable latency

        Returns:
            Optimal batch size
        """
        available_time = max_latency_ms - network_latency_ms
        if available_time <= 0:
            return 1

        return max(1, int(available_time / processing_time_per_order_ms))

    def orders_per_dollar(self, capital: float, avg_order_size: float,
                          turnover_rate: float = 10) -> int:
        """
        Calculate expected orders per dollar of capital.

        Args:
            capital: Total capital
            avg_order_size: Average order size
            turnover_rate: Expected turnover multiplier

        Returns:
            Expected number of orders
        """
        return int((capital * turnover_rate) / avg_order_size)

    def capital_efficiency(self, working_capital: float, total_capital: float,
                           orders_per_sec: int) -> Dict:
        """
        Calculate capital efficiency metrics.

        Args:
            working_capital: Capital currently in orders
            total_capital: Total available capital
            orders_per_sec: Current order rate

        Returns:
            Efficiency metrics
        """
        utilization = working_capital / total_capital if total_capital > 0 else 0
        capital_velocity = (orders_per_sec * 10) / working_capital if working_capital > 0 else 0

        return {
            "utilization": round(utilization * 100, 2),
            "capital_velocity": round(capital_velocity, 2),
            "working_capital": round(working_capital, 2),
            "idle_capital": round(total_capital - working_capital, 2),
            "efficiency_score": round(utilization * capital_velocity, 2)
        }


# ==================== PRICE UTILITIES ====================

class PriceCalculator:
    """
    Price manipulation utilities for Polymarket.
    """

    def implied_probability(self, price: float) -> float:
        """Convert price to implied probability."""
        return price

    def price_from_probability(self, prob: float) -> float:
        """Convert probability to price."""
        return max(0.001, min(0.999, prob))

    def mid_price(self, bid: float, ask: float) -> float:
        """Calculate mid price."""
        return (bid + ask) / 2

    def spread(self, bid: float, ask: float) -> Dict:
        """Calculate spread metrics."""
        absolute = ask - bid
        mid = self.mid_price(bid, ask)
        relative = absolute / mid if mid > 0 else 0
        bps = relative * 10000

        return {
            "absolute": round(absolute, 4),
            "relative": round(relative, 4),
            "bps": round(bps, 1),
            "mid": round(mid, 4)
        }

    def round_to_tick(self, price: float, tick_size: float = 0.001) -> float:
        """Round price to tick size."""
        d = Decimal(str(price))
        tick = Decimal(str(tick_size))
        return float(d.quantize(tick, rounding=ROUND_HALF_UP))

    def clamp_price(self, price: float) -> float:
        """Clamp price to valid Polymarket range."""
        return max(0.001, min(0.999, price))

    def binary_ev(self, price: float, true_prob: float, side: str) -> float:
        """
        Calculate expected value for binary outcome.

        Args:
            price: Market price
            true_prob: Your estimated probability
            side: "BUY" (YES) or "SELL" (NO)

        Returns:
            Expected value per dollar risked
        """
        if side == "BUY":
            # Buying YES: pay price, get 1 if win
            win_payout = 1 - price  # Net profit if YES
            lose_payout = -price    # Loss if NO
            ev = true_prob * win_payout + (1 - true_prob) * lose_payout
        else:
            # Selling (buying NO): pay (1-price), get 1 if NO
            win_payout = price       # Net profit if NO
            lose_payout = -(1-price) # Loss if YES
            ev = (1 - true_prob) * win_payout + true_prob * lose_payout

        return ev


# ==================== SINGLETON INSTANCES ====================

kelly = KellyCalculator()
grid = GridCalculator()
risk = RiskCalculator()
stats = StatisticalCalculator()
hft = HFTCalculator()
price = PriceCalculator()


# ==================== UNIFIED MATH INTERFACE ====================

class MathEngine:
    """Unified access to all mathematical tools."""

    kelly = kelly
    grid = grid
    risk = risk
    stats = stats
    hft = hft
    price = price

    # Quick access methods
    @staticmethod
    def optimal_size(win_prob: float, odds: float, bankroll: float,
                     fraction: float = 0.5) -> float:
        """Quick Kelly sizing."""
        return kelly.optimal_size(win_prob, odds, bankroll, fraction)

    @staticmethod
    def generate_grid(center: float, spread_bps: int = 100,
                      levels: int = 5) -> Dict:
        """Quick grid generation."""
        return grid.generate(center, spread_bps, levels)

    @staticmethod
    def calculate_var(returns: List[float], confidence: float = 0.95,
                      position_size: float = 1.0) -> float:
        """Quick VaR calculation."""
        return risk.value_at_risk(returns, confidence, position_size)

    @staticmethod
    def throughput_capacity(wallets: int) -> int:
        """Quick throughput calculation."""
        return hft.throughput(wallets)["multi_process_max"]


# Main instance
math = MathEngine()


# ==================== CLI ====================

def main():
    import sys
    import json

    if len(sys.argv) < 2:
        print("""
Math Engine - Trading Mathematics
=================================

COMMANDS:
  kelly PROB ODDS BANKROLL    Calculate Kelly position size
  grid CENTER SPREAD LEVELS   Generate order grid
  var RETURNS CONFIDENCE      Calculate Value at Risk
  throughput WALLETS          Calculate HFT throughput

EXAMPLES:
  python math_engine.py kelly 0.6 2.0 10000
  python math_engine.py grid 0.5 100 5
  python math_engine.py throughput 100
""")
        return

    cmd = sys.argv[1]

    if cmd == "kelly":
        prob = float(sys.argv[2])
        odds = float(sys.argv[3])
        bankroll = float(sys.argv[4])
        result = kelly.optimal_size(prob, odds, bankroll, 0.5)
        print(f"Optimal size (half Kelly): ${result:.2f}")

    elif cmd == "grid":
        center = float(sys.argv[2])
        spread = int(sys.argv[3])
        levels = int(sys.argv[4])
        result = grid.generate(center, spread, levels)
        print(json.dumps(result, indent=2))

    elif cmd == "throughput":
        wallets = int(sys.argv[2])
        result = hft.throughput(wallets)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
