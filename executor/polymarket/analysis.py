"""
Polymarket Market Analysis
==========================

Comprehensive market analysis for prediction markets:
- Probability analysis and calibration
- Liquidity assessment
- Market depth analysis
- Volume analysis
- Price discovery metrics
- Market efficiency tests

USAGE:
    from executor.polymarket.analysis import analysis

    analysis.analyze_liquidity(orderbook)
    analysis.probability_calibration(predictions, outcomes)
    analysis.market_efficiency_score(prices)
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class LiquidityMetrics:
    """Liquidity assessment metrics"""
    bid_depth: float
    ask_depth: float
    total_depth: float
    spread: float
    spread_bps: float
    depth_imbalance: float
    liquidity_score: float  # 0-100


@dataclass
class MarketQuality:
    """Market quality metrics"""
    efficiency_score: float
    information_ratio: float
    volatility: float
    volume_24h: float
    unique_traders: int


class MarketAnalysis:
    """
    Market analysis tools for Polymarket.

    Provides comprehensive analytics without external dependencies.
    """

    # ==========================================
    # PROBABILITY ANALYSIS
    # ==========================================

    def implied_probability(self, price: float) -> float:
        """Convert price to implied probability"""
        return max(0, min(1, price))

    def fair_value_estimate(self, yes_price: float, no_price: float) -> Dict:
        """
        Estimate fair value from YES/NO prices.

        In efficient market: YES + NO = 1
        Deviations indicate arbitrage or inefficiency.
        """
        total = yes_price + no_price
        overround = total - 1  # Bookmaker margin equivalent

        # Remove overround for fair probability
        fair_yes = yes_price / total if total > 0 else 0.5
        fair_no = no_price / total if total > 0 else 0.5

        return {
            'yes_price': yes_price,
            'no_price': no_price,
            'sum': total,
            'overround': overround,
            'overround_pct': overround * 100,
            'fair_yes_prob': fair_yes,
            'fair_no_prob': fair_no,
            'market_quality': 'efficient' if abs(overround) < 0.02 else 'inefficient'
        }

    def probability_calibration(self, predictions: List[float],
                                outcomes: List[int]) -> Dict:
        """
        Assess prediction calibration.

        predictions: list of predicted probabilities (0-1)
        outcomes: list of actual outcomes (0 or 1)

        A well-calibrated predictor has:
        - Predictions of 70% should be correct ~70% of the time
        """
        if len(predictions) != len(outcomes):
            return {'error': 'Length mismatch'}

        # Bin predictions
        bins = [(0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5),
                (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]

        calibration = []
        for low, high in bins:
            bin_mask = [(low <= p < high) for p in predictions]
            bin_preds = [p for p, m in zip(predictions, bin_mask) if m]
            bin_outcomes = [o for o, m in zip(outcomes, bin_mask) if m]

            if bin_preds:
                avg_pred = sum(bin_preds) / len(bin_preds)
                actual_rate = sum(bin_outcomes) / len(bin_outcomes)
                calibration.append({
                    'bin': f'{low:.1f}-{high:.1f}',
                    'count': len(bin_preds),
                    'avg_prediction': avg_pred,
                    'actual_rate': actual_rate,
                    'calibration_error': abs(avg_pred - actual_rate)
                })

        # Brier score (lower is better)
        brier = sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / len(predictions)

        # Average calibration error
        ace = sum(c['calibration_error'] * c['count'] for c in calibration) / len(predictions) if calibration else 0

        return {
            'brier_score': brier,
            'avg_calibration_error': ace,
            'calibration_bins': calibration,
            'num_predictions': len(predictions),
            'interpretation': 'well_calibrated' if ace < 0.05 else 'moderately_calibrated' if ace < 0.1 else 'poorly_calibrated'
        }

    def expected_value_analysis(self, price: float, estimated_prob: float,
                                size: float = 1.0) -> Dict:
        """Calculate expected value of a trade"""
        # EV = P(win) * payout - P(lose) * cost
        # For binary: EV = prob * (1 - price) - (1 - prob) * price
        ev_per_share = estimated_prob * (1 - price) - (1 - estimated_prob) * price
        total_ev = ev_per_share * size

        # Edge = estimated_prob - price (for YES)
        edge = estimated_prob - price

        return {
            'price': price,
            'estimated_probability': estimated_prob,
            'edge': edge,
            'edge_pct': edge * 100,
            'ev_per_share': ev_per_share,
            'total_ev': total_ev,
            'size': size,
            'recommendation': 'buy' if edge > 0.02 else 'sell' if edge < -0.02 else 'hold'
        }

    # ==========================================
    # LIQUIDITY ANALYSIS
    # ==========================================

    def analyze_liquidity(self, bids: List[Dict], asks: List[Dict]) -> LiquidityMetrics:
        """
        Comprehensive liquidity analysis.

        bids/asks: [{'price': float, 'size': float}, ...]
        """
        bid_depth = sum(b['size'] for b in bids)
        ask_depth = sum(a['size'] for a in asks)
        total_depth = bid_depth + ask_depth

        best_bid = bids[0]['price'] if bids else 0
        best_ask = asks[0]['price'] if asks else 1

        spread = best_ask - best_bid
        mid = (best_bid + best_ask) / 2 if best_bid and best_ask else 0.5
        spread_bps = (spread / mid * 10000) if mid > 0 else 0

        # Imbalance: positive = more bids (buy pressure)
        imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0

        # Liquidity score (0-100)
        depth_score = min(50, total_depth / 20)  # Max 50 points for depth > 1000
        spread_score = max(0, 50 - spread_bps / 10)  # Lower spread = higher score

        liquidity_score = depth_score + spread_score

        return LiquidityMetrics(
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            total_depth=total_depth,
            spread=spread,
            spread_bps=spread_bps,
            depth_imbalance=imbalance,
            liquidity_score=liquidity_score
        )

    def depth_profile(self, bids: List[Dict], asks: List[Dict],
                      price_levels: int = 10) -> Dict:
        """Analyze depth at various price levels"""
        profile = {'bids': [], 'asks': []}

        # Cumulative bid depth
        cumulative = 0
        for i, bid in enumerate(bids[:price_levels]):
            cumulative += bid['size']
            profile['bids'].append({
                'level': i + 1,
                'price': bid['price'],
                'size': bid['size'],
                'cumulative': cumulative
            })

        # Cumulative ask depth
        cumulative = 0
        for i, ask in enumerate(asks[:price_levels]):
            cumulative += ask['size']
            profile['asks'].append({
                'level': i + 1,
                'price': ask['price'],
                'size': ask['size'],
                'cumulative': cumulative
            })

        return profile

    def price_impact_curve(self, bids: List[Dict], asks: List[Dict],
                           order_sizes: List[float] = None) -> Dict:
        """Calculate price impact for various order sizes"""
        if order_sizes is None:
            order_sizes = [10, 50, 100, 500, 1000, 5000]

        buy_impacts = []
        sell_impacts = []

        for size in order_sizes:
            # Buy impact (eating into asks)
            remaining = size
            cost = 0
            for ask in asks:
                fill = min(remaining, ask['size'])
                cost += fill * ask['price']
                remaining -= fill
                if remaining <= 0:
                    break

            avg_price = cost / size if size > 0 else 0
            best_ask = asks[0]['price'] if asks else 0
            buy_impact = (avg_price - best_ask) / best_ask * 100 if best_ask > 0 else 0

            buy_impacts.append({
                'size': size,
                'avg_price': avg_price,
                'impact_pct': buy_impact
            })

            # Sell impact (eating into bids)
            remaining = size
            proceeds = 0
            for bid in bids:
                fill = min(remaining, bid['size'])
                proceeds += fill * bid['price']
                remaining -= fill
                if remaining <= 0:
                    break

            avg_price = proceeds / size if size > 0 else 0
            best_bid = bids[0]['price'] if bids else 0
            sell_impact = (best_bid - avg_price) / best_bid * 100 if best_bid > 0 else 0

            sell_impacts.append({
                'size': size,
                'avg_price': avg_price,
                'impact_pct': sell_impact
            })

        return {
            'buy_impacts': buy_impacts,
            'sell_impacts': sell_impacts
        }

    # ==========================================
    # VOLUME ANALYSIS
    # ==========================================

    def volume_profile(self, trades: List[Dict]) -> Dict:
        """Analyze trading volume patterns"""
        if not trades:
            return {'error': 'No trades'}

        total_volume = sum(t.get('size', 0) for t in trades)
        buy_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'BUY')
        sell_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'SELL')

        # Volume-weighted average price
        vwap = sum(t.get('size', 0) * t.get('price', 0) for t in trades) / total_volume if total_volume > 0 else 0

        return {
            'total_volume': total_volume,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'buy_sell_ratio': buy_volume / sell_volume if sell_volume > 0 else float('inf'),
            'vwap': vwap,
            'num_trades': len(trades),
            'avg_trade_size': total_volume / len(trades)
        }

    def volume_by_price(self, trades: List[Dict], num_bins: int = 10) -> List[Dict]:
        """Analyze volume at different price levels"""
        if not trades:
            return []

        prices = [t.get('price', 0) for t in trades]
        min_price = min(prices)
        max_price = max(prices)

        if min_price == max_price:
            return [{'price_range': f'{min_price:.3f}', 'volume': sum(t.get('size', 0) for t in trades)}]

        bin_size = (max_price - min_price) / num_bins
        bins = []

        for i in range(num_bins):
            low = min_price + i * bin_size
            high = min_price + (i + 1) * bin_size

            volume = sum(
                t.get('size', 0) for t in trades
                if low <= t.get('price', 0) < high
            )

            bins.append({
                'price_low': low,
                'price_high': high,
                'volume': volume
            })

        return bins

    # ==========================================
    # MARKET EFFICIENCY
    # ==========================================

    def market_efficiency_score(self, prices: List[float]) -> Dict:
        """
        Calculate market efficiency metrics.

        Efficient markets have:
        - Prices follow random walk
        - No predictable patterns
        - Quick information incorporation
        """
        if len(prices) < 10:
            return {'error': 'Insufficient data'}

        # Calculate returns
        returns = [(prices[i] - prices[i-1]) / prices[i-1]
                  for i in range(1, len(prices)) if prices[i-1] != 0]

        if not returns:
            return {'error': 'No valid returns'}

        # Autocorrelation (efficient = near 0)
        mean_ret = sum(returns) / len(returns)
        var = sum((r - mean_ret) ** 2 for r in returns)

        if var == 0:
            autocorr = 0
        else:
            autocorr = sum((returns[i] - mean_ret) * (returns[i-1] - mean_ret)
                          for i in range(1, len(returns))) / var

        # Variance ratio (efficient = near 1)
        # Compare variance of 2-period returns to 2 * 1-period variance
        one_period_var = var / (len(returns) - 1) if len(returns) > 1 else 0

        two_period_returns = [(prices[i] - prices[i-2]) / prices[i-2]
                             for i in range(2, len(prices)) if prices[i-2] != 0]
        two_period_var = sum((r - sum(two_period_returns)/len(two_period_returns)) ** 2
                            for r in two_period_returns) / (len(two_period_returns) - 1) if len(two_period_returns) > 1 else 0

        variance_ratio = two_period_var / (2 * one_period_var) if one_period_var > 0 else 1

        # Efficiency score (0-100)
        autocorr_score = max(0, 50 * (1 - abs(autocorr)))
        vr_score = max(0, 50 * (1 - abs(variance_ratio - 1)))
        efficiency_score = autocorr_score + vr_score

        return {
            'efficiency_score': efficiency_score,
            'autocorrelation': autocorr,
            'variance_ratio': variance_ratio,
            'interpretation': 'efficient' if efficiency_score > 70 else 'moderately_efficient' if efficiency_score > 40 else 'inefficient',
            'num_observations': len(prices)
        }

    def information_incorporation_speed(self, prices: List[float],
                                        event_time: int) -> Dict:
        """
        Measure how quickly prices incorporate information.

        event_time: index in prices where event occurred
        """
        if event_time >= len(prices) - 1 or event_time < 1:
            return {'error': 'Invalid event time'}

        pre_event_price = prices[event_time - 1]
        event_price = prices[event_time]
        post_prices = prices[event_time + 1:]

        # Immediate reaction
        immediate_move = (event_price - pre_event_price) / pre_event_price if pre_event_price != 0 else 0

        # Drift after event
        if post_prices:
            final_price = post_prices[-1]
            drift = (final_price - event_price) / event_price if event_price != 0 else 0

            # Check for continued drift (inefficient) vs stabilization (efficient)
            continued_drift_ratio = abs(drift) / abs(immediate_move) if immediate_move != 0 else 0
        else:
            drift = 0
            continued_drift_ratio = 0

        return {
            'immediate_move': immediate_move,
            'immediate_move_pct': immediate_move * 100,
            'subsequent_drift': drift,
            'drift_ratio': continued_drift_ratio,
            'incorporation': 'quick' if continued_drift_ratio < 0.2 else 'slow'
        }

    # ==========================================
    # VOLATILITY ANALYSIS
    # ==========================================

    def realized_volatility(self, prices: List[float],
                            annualize: bool = True) -> float:
        """Calculate realized volatility from price series"""
        if len(prices) < 2:
            return 0

        returns = [(prices[i] / prices[i-1] - 1)
                  for i in range(1, len(prices)) if prices[i-1] != 0]

        if not returns:
            return 0

        variance = sum(r ** 2 for r in returns) / len(returns)
        vol = math.sqrt(variance)

        if annualize:
            # Assuming daily data, annualize with 365 days
            vol = vol * math.sqrt(365)

        return vol

    def volatility_regime(self, prices: List[float],
                          short_window: int = 5,
                          long_window: int = 20) -> Dict:
        """Identify current volatility regime"""
        if len(prices) < long_window:
            return {'regime': 'unknown'}

        short_vol = self.realized_volatility(prices[-short_window:], annualize=False)
        long_vol = self.realized_volatility(prices[-long_window:], annualize=False)

        vol_ratio = short_vol / long_vol if long_vol > 0 else 1

        if vol_ratio > 1.5:
            regime = 'high_volatility'
        elif vol_ratio < 0.67:
            regime = 'low_volatility'
        else:
            regime = 'normal'

        return {
            'regime': regime,
            'short_volatility': short_vol,
            'long_volatility': long_vol,
            'vol_ratio': vol_ratio
        }

    # ==========================================
    # MARKET MICROSTRUCTURE
    # ==========================================

    def order_flow_imbalance(self, trades: List[Dict]) -> Dict:
        """Analyze order flow imbalance"""
        if not trades:
            return {'ofi': 0}

        buy_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'BUY')
        sell_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'SELL')
        total_volume = buy_volume + sell_volume

        ofi = (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0

        return {
            'ofi': ofi,  # -1 to 1
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'interpretation': 'buy_pressure' if ofi > 0.2 else 'sell_pressure' if ofi < -0.2 else 'balanced'
        }

    def trade_arrival_rate(self, trades: List[Dict]) -> Dict:
        """Analyze trade arrival patterns"""
        if len(trades) < 2:
            return {'avg_interval': 0}

        # Assume trades have 'timestamp' field
        timestamps = [t.get('timestamp', 0) for t in trades]
        intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]

        if not intervals:
            return {'avg_interval': 0}

        avg_interval = sum(intervals) / len(intervals)
        arrival_rate = 1 / avg_interval if avg_interval > 0 else 0

        return {
            'avg_interval_seconds': avg_interval,
            'arrival_rate_per_second': arrival_rate,
            'arrival_rate_per_minute': arrival_rate * 60,
            'num_trades': len(trades)
        }

    # ==========================================
    # COMPARATIVE ANALYSIS
    # ==========================================

    def compare_markets(self, market1: Dict, market2: Dict) -> Dict:
        """Compare two related markets"""
        # Both should have: price, volume, liquidity_score
        price_diff = abs(market1.get('price', 0.5) - market2.get('price', 0.5))
        volume_ratio = (market1.get('volume', 0) / market2.get('volume', 1)) if market2.get('volume', 0) > 0 else 0
        liquidity_diff = market1.get('liquidity_score', 0) - market2.get('liquidity_score', 0)

        return {
            'price_difference': price_diff,
            'price_diff_pct': price_diff * 100,
            'volume_ratio': volume_ratio,
            'liquidity_advantage': 'market1' if liquidity_diff > 0 else 'market2',
            'potential_arbitrage': price_diff > 0.02
        }


# Singleton instance
analysis = MarketAnalysis()
