"""
Polymarket Trading Strategies
=============================

Complete trading strategy implementations for prediction markets:
- Market Making (providing liquidity)
- Arbitrage (binary, cross-market, time-based)
- Hedging (delta neutral, event hedging)
- Directional (momentum, mean reversion, news-based)
- Statistical arbitrage

STRATEGY CATEGORIES:
-------------------
1. Market Making
   - Passive liquidity provision
   - Spread capture
   - Inventory management

2. Arbitrage
   - Binary YES/NO arbitrage
   - Multi-outcome arbitrage
   - Cross-platform arbitrage
   - Resolution arbitrage

3. Hedging
   - Position hedging
   - Event hedging
   - Correlation-based hedging

4. Directional
   - Information edge trading
   - Momentum following
   - Mean reversion

USAGE:
    from executor.polymarket.strategies import strategies

    quotes = strategies.calculate_mm_quotes(0.65, 0.02, inventory=10)
    arb = strategies.binary_arbitrage_opportunity(0.60, 0.38)
    hedge = strategies.calculate_hedge(position, correlation)
"""

import math
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum


class StrategyType(Enum):
    MARKET_MAKING = "market_making"
    ARBITRAGE = "arbitrage"
    HEDGING = "hedging"
    DIRECTIONAL = "directional"
    STATISTICAL = "statistical"


@dataclass
class Quote:
    """Market maker quote"""
    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float

    @property
    def spread(self) -> float:
        return self.ask_price - self.bid_price

    @property
    def mid(self) -> float:
        return (self.bid_price + self.ask_price) / 2


@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity details"""
    type: str
    profit: float
    capital_required: float
    return_percent: float
    actions: List[Dict]
    risk_free: bool


class TradingStrategies:
    """
    Polymarket trading strategy implementations.

    Provides strategy calculations without external dependencies.
    """

    # ==========================================
    # MARKET MAKING
    # ==========================================

    def calculate_mm_quotes(self, fair_value: float, half_spread: float,
                            inventory: float = 0,
                            inventory_skew: float = 0.1,
                            size: float = 100) -> Quote:
        """
        Calculate market maker bid/ask quotes.

        Args:
            fair_value: Estimated true probability/price
            half_spread: Half of desired spread
            inventory: Current position (+ve = long, -ve = short)
            inventory_skew: How much to skew prices based on inventory
            size: Quote size

        Returns:
            Quote with bid/ask prices adjusted for inventory
        """
        # Base quotes around fair value
        base_bid = fair_value - half_spread
        base_ask = fair_value + half_spread

        # Skew based on inventory (long = lower prices, short = higher prices)
        skew = -inventory * inventory_skew * half_spread
        bid_price = max(0.001, min(0.999, base_bid + skew))
        ask_price = max(0.001, min(0.999, base_ask + skew))

        # Adjust sizes based on inventory
        if inventory > 0:
            # Long: want to sell more
            bid_size = size * 0.8
            ask_size = size * 1.2
        elif inventory < 0:
            # Short: want to buy more
            bid_size = size * 1.2
            ask_size = size * 0.8
        else:
            bid_size = size
            ask_size = size

        return Quote(bid_price, bid_size, ask_price, ask_size)

    def optimal_spread(self, volatility: float, inventory_risk: float,
                       competition: float = 1.0) -> float:
        """
        Calculate optimal spread based on market conditions.

        Args:
            volatility: Price volatility (0-1 scale)
            inventory_risk: Risk per unit of inventory
            competition: Competitive factor (lower = more competition)

        Based on Avellaneda-Stoikov market making model.
        """
        # Higher volatility = wider spread
        # More competition = tighter spread
        base_spread = 2 * volatility * inventory_risk
        competitive_spread = base_spread * competition
        return max(0.002, competitive_spread)  # Min 0.2% spread

    def inventory_management(self, current_inventory: float,
                             max_inventory: float,
                             target_inventory: float = 0) -> Dict:
        """
        Calculate inventory management signals.

        Returns recommended actions to bring inventory toward target.
        """
        deviation = current_inventory - target_inventory
        utilization = abs(current_inventory) / max_inventory if max_inventory > 0 else 0

        if utilization > 0.9:
            urgency = "critical"
            action = "reduce_immediately"
        elif utilization > 0.7:
            urgency = "high"
            action = "skew_aggressively"
        elif utilization > 0.5:
            urgency = "medium"
            action = "skew_moderately"
        else:
            urgency = "low"
            action = "maintain_neutral"

        return {
            'current_inventory': current_inventory,
            'target_inventory': target_inventory,
            'deviation': deviation,
            'utilization': utilization,
            'urgency': urgency,
            'action': action,
            'recommended_skew': deviation / max_inventory if max_inventory > 0 else 0
        }

    def mm_pnl_analysis(self, trades: List[Dict], current_mid: float) -> Dict:
        """
        Analyze market making P&L.

        Separates inventory P&L from spread capture.
        """
        buy_volume = sum(t['size'] for t in trades if t['side'] == 'BUY')
        sell_volume = sum(t['size'] for t in trades if t['side'] == 'SELL')
        buy_value = sum(t['size'] * t['price'] for t in trades if t['side'] == 'BUY')
        sell_value = sum(t['size'] * t['price'] for t in trades if t['side'] == 'SELL')

        net_inventory = buy_volume - sell_volume
        inventory_cost = buy_value - sell_value

        # Spread capture = profit if flat
        avg_buy = buy_value / buy_volume if buy_volume > 0 else 0
        avg_sell = sell_value / sell_volume if sell_volume > 0 else 0
        matched_volume = min(buy_volume, sell_volume)
        spread_capture = matched_volume * (avg_sell - avg_buy) if matched_volume > 0 else 0

        # Inventory mark-to-market
        inventory_mtm = net_inventory * current_mid - inventory_cost if net_inventory != 0 else 0

        return {
            'total_pnl': spread_capture + inventory_mtm,
            'spread_capture': spread_capture,
            'inventory_pnl': inventory_mtm,
            'net_inventory': net_inventory,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'avg_buy_price': avg_buy,
            'avg_sell_price': avg_sell
        }

    # ==========================================
    # ARBITRAGE
    # ==========================================

    def binary_arbitrage_opportunity(self, yes_price: float,
                                     no_price: float) -> Optional[ArbitrageOpportunity]:
        """
        Check for arbitrage in binary market.

        Arbitrage exists when YES + NO != 1
        """
        total = yes_price + no_price

        if total < 0.99:  # Underpriced - buy both
            profit_per_dollar = 1.0 - total
            return ArbitrageOpportunity(
                type="binary_underpriced",
                profit=profit_per_dollar,
                capital_required=total,
                return_percent=profit_per_dollar / total * 100,
                actions=[
                    {'action': 'buy', 'asset': 'YES', 'price': yes_price},
                    {'action': 'buy', 'asset': 'NO', 'price': no_price}
                ],
                risk_free=True
            )
        elif total > 1.01:  # Overpriced - sell both (if you hold)
            profit_per_dollar = total - 1.0
            return ArbitrageOpportunity(
                type="binary_overpriced",
                profit=profit_per_dollar,
                capital_required=0,  # Only if already holding
                return_percent=profit_per_dollar / total * 100,
                actions=[
                    {'action': 'sell', 'asset': 'YES', 'price': yes_price},
                    {'action': 'sell', 'asset': 'NO', 'price': no_price}
                ],
                risk_free=True
            )
        return None

    def multi_outcome_arbitrage(self, prices: List[float],
                                outcome_names: List[str] = None) -> Optional[ArbitrageOpportunity]:
        """
        Check for arbitrage in multi-outcome market.

        Sum of all outcomes should equal 1.
        """
        total = sum(prices)
        n = len(prices)
        if outcome_names is None:
            outcome_names = [f"Outcome_{i}" for i in range(n)]

        if total < 0.98:  # Buy all outcomes
            profit = 1.0 - total
            return ArbitrageOpportunity(
                type="multi_underpriced",
                profit=profit,
                capital_required=total,
                return_percent=profit / total * 100,
                actions=[
                    {'action': 'buy', 'asset': name, 'price': price}
                    for name, price in zip(outcome_names, prices)
                ],
                risk_free=True
            )
        return None

    def cross_market_arbitrage(self, market1_yes: float, market2_yes: float,
                               correlation: float = 1.0) -> Dict:
        """
        Identify cross-market arbitrage (same/correlated events).

        For perfectly correlated events (correlation=1), prices should be equal.
        """
        price_diff = abs(market1_yes - market2_yes)
        expected_diff = (1 - correlation) * 0.5  # Expected spread for given correlation

        if price_diff > expected_diff + 0.02:
            # Arbitrage opportunity
            if market1_yes > market2_yes:
                return {
                    'arbitrage': True,
                    'action': 'sell_market1_buy_market2',
                    'edge': price_diff - expected_diff,
                    'risk': 'correlation_breakdown'
                }
            else:
                return {
                    'arbitrage': True,
                    'action': 'buy_market1_sell_market2',
                    'edge': price_diff - expected_diff,
                    'risk': 'correlation_breakdown'
                }
        return {'arbitrage': False}

    def resolution_arbitrage(self, price: float, estimated_prob: float,
                             days_to_resolution: float) -> Dict:
        """
        Identify resolution arbitrage (price vs. probability gap).

        When market price differs significantly from estimated probability.
        """
        edge = estimated_prob - price
        abs_edge = abs(edge)

        # Annualized edge
        if days_to_resolution > 0:
            annualized = abs_edge * (365 / days_to_resolution)
        else:
            annualized = abs_edge

        if abs_edge > 0.03:  # 3% edge threshold
            return {
                'opportunity': True,
                'direction': 'buy' if edge > 0 else 'sell',
                'edge': edge,
                'edge_percent': edge * 100,
                'annualized_return': annualized * 100,
                'days_to_resolution': days_to_resolution,
                'risk': 'estimation_error'
            }
        return {'opportunity': False}

    # ==========================================
    # HEDGING
    # ==========================================

    def calculate_hedge(self, position_size: float, position_delta: float,
                        hedge_instrument_delta: float) -> Dict:
        """
        Calculate hedge size for delta neutrality.

        Args:
            position_size: Size of position to hedge
            position_delta: Delta of position (exposure per unit)
            hedge_instrument_delta: Delta of hedging instrument
        """
        total_exposure = position_size * position_delta
        hedge_size = -total_exposure / hedge_instrument_delta if hedge_instrument_delta != 0 else 0

        return {
            'position_exposure': total_exposure,
            'hedge_size': hedge_size,
            'hedge_direction': 'buy' if hedge_size > 0 else 'sell',
            'residual_delta': 0  # Perfectly hedged
        }

    def binary_hedge(self, yes_position: float, yes_price: float) -> Dict:
        """
        Hedge a binary position using the opposite outcome.

        For position in YES, hedge with NO position.
        """
        no_price = 1 - yes_price

        # To perfectly hedge: buy NO such that outcome is same either way
        # If YES wins: yes_position * 1 - cost
        # If NO wins: no_position * 1 - cost
        # Set equal: yes_position - yes_cost = no_position - no_cost

        hedge_size = yes_position * yes_price / no_price
        cost = hedge_size * no_price

        return {
            'hedge_instrument': 'NO',
            'hedge_size': hedge_size,
            'hedge_cost': cost,
            'guaranteed_value': yes_position - (yes_position * yes_price),
            'strategy': f'Buy {hedge_size:.2f} NO @ {no_price:.3f}'
        }

    def correlated_hedge(self, position: float, position_price: float,
                         hedge_price: float, correlation: float) -> Dict:
        """
        Hedge using correlated market.

        Less than perfect correlation = imperfect hedge.
        """
        # Optimal hedge ratio = correlation * (position_vol / hedge_vol)
        # Simplified: assume equal volatility
        hedge_ratio = correlation
        hedge_size = position * hedge_ratio

        # Expected hedge effectiveness
        variance_reduction = correlation ** 2

        return {
            'hedge_size': hedge_size,
            'hedge_ratio': hedge_ratio,
            'correlation': correlation,
            'variance_reduction': variance_reduction,
            'residual_risk': 1 - variance_reduction,
            'warning': 'Imperfect hedge' if correlation < 0.9 else None
        }

    def event_hedge(self, exposures: Dict[str, float]) -> Dict:
        """
        Calculate hedge for multiple correlated exposures.

        exposures: {market_id: position_delta}
        """
        total_exposure = sum(exposures.values())

        # Simple netting
        long_exposure = sum(v for v in exposures.values() if v > 0)
        short_exposure = sum(v for v in exposures.values() if v < 0)

        natural_hedge = min(long_exposure, abs(short_exposure))
        net_exposure = total_exposure

        return {
            'total_exposure': total_exposure,
            'long_exposure': long_exposure,
            'short_exposure': short_exposure,
            'natural_hedge': natural_hedge,
            'net_exposure': net_exposure,
            'hedge_needed': abs(net_exposure)
        }

    # ==========================================
    # DIRECTIONAL STRATEGIES
    # ==========================================

    def momentum_signal(self, prices: List[float], lookback: int = 10) -> Dict:
        """
        Calculate momentum signal from price history.

        Positive momentum = buy signal
        Negative momentum = sell signal
        """
        if len(prices) < lookback:
            return {'signal': 0, 'error': 'Insufficient data'}

        recent = prices[-lookback:]
        momentum = recent[-1] - recent[0]
        avg_return = momentum / lookback

        # Normalize by volatility
        returns = [recent[i] - recent[i-1] for i in range(1, len(recent))]
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.01

        signal = momentum / volatility if volatility > 0 else 0

        return {
            'signal': signal,
            'direction': 'long' if signal > 0.5 else 'short' if signal < -0.5 else 'neutral',
            'strength': abs(signal),
            'momentum': momentum,
            'volatility': volatility
        }

    def mean_reversion_signal(self, current_price: float, fair_value: float,
                              threshold: float = 0.05) -> Dict:
        """
        Calculate mean reversion signal.

        Trade toward fair value when price deviates.
        """
        deviation = current_price - fair_value
        deviation_percent = deviation / fair_value if fair_value > 0 else 0

        if deviation_percent > threshold:
            signal = 'sell'
            strength = deviation_percent / threshold
        elif deviation_percent < -threshold:
            signal = 'buy'
            strength = abs(deviation_percent) / threshold
        else:
            signal = 'neutral'
            strength = 0

        return {
            'signal': signal,
            'strength': strength,
            'current_price': current_price,
            'fair_value': fair_value,
            'deviation': deviation,
            'deviation_percent': deviation_percent * 100
        }

    def news_edge_sizing(self, estimated_impact: float, confidence: float,
                         max_position: float) -> Dict:
        """
        Calculate position size based on news/information edge.

        Args:
            estimated_impact: Expected price move (0-1)
            confidence: Confidence in estimate (0-1)
            max_position: Maximum position size
        """
        # Kelly-style sizing with confidence adjustment
        edge = estimated_impact * confidence
        kelly_fraction = edge / (estimated_impact * (1 - estimated_impact)) if 0 < estimated_impact < 1 else 0
        kelly_fraction = max(0, min(1, kelly_fraction))

        # Conservative sizing
        position_size = min(max_position, max_position * kelly_fraction * 0.5)

        return {
            'edge': edge,
            'kelly_fraction': kelly_fraction,
            'recommended_size': position_size,
            'risk_adjusted': position_size * confidence,
            'expected_profit': position_size * estimated_impact * confidence
        }

    # ==========================================
    # STATISTICAL STRATEGIES
    # ==========================================

    def probability_weighted_portfolio(self, opportunities: List[Dict]) -> Dict:
        """
        Build probability-weighted portfolio across opportunities.

        Each opportunity: {id, price, estimated_prob, max_size}
        """
        total_ev = 0
        positions = []

        for opp in opportunities:
            edge = opp['estimated_prob'] - opp['price']
            if edge > 0:
                # Kelly sizing
                kelly = edge / (1 - opp['price']) if opp['price'] < 1 else 0
                size = min(opp.get('max_size', 100), 100 * kelly)
                ev = size * edge

                positions.append({
                    'id': opp['id'],
                    'size': size,
                    'edge': edge,
                    'expected_value': ev
                })
                total_ev += ev

        return {
            'positions': positions,
            'total_expected_value': total_ev,
            'num_positions': len(positions),
            'avg_edge': sum(p['edge'] for p in positions) / len(positions) if positions else 0
        }

    def correlation_matrix_strategy(self, positions: List[Dict],
                                    correlations: List[List[float]]) -> Dict:
        """
        Optimize positions considering correlations.

        Reduces positions in highly correlated markets.
        """
        n = len(positions)

        # Calculate portfolio variance
        total_variance = 0
        for i in range(n):
            for j in range(n):
                cov = correlations[i][j] * positions[i]['size'] * positions[j]['size']
                total_variance += cov

        # Identify highly correlated pairs
        correlated_pairs = []
        for i in range(n):
            for j in range(i+1, n):
                if correlations[i][j] > 0.7:
                    correlated_pairs.append({
                        'pair': (positions[i]['id'], positions[j]['id']),
                        'correlation': correlations[i][j],
                        'action': 'reduce_one'
                    })

        return {
            'portfolio_variance': total_variance,
            'portfolio_vol': total_variance ** 0.5,
            'correlated_pairs': correlated_pairs,
            'diversification_score': 1 - (len(correlated_pairs) / max(1, n * (n-1) / 2))
        }

    # ==========================================
    # STRATEGY SELECTION
    # ==========================================

    def recommend_strategy(self, market_conditions: Dict) -> Dict:
        """
        Recommend strategy based on market conditions.

        market_conditions: {
            spread, volatility, volume, time_to_resolution,
            has_edge, inventory
        }
        """
        spread = market_conditions.get('spread', 0.02)
        volatility = market_conditions.get('volatility', 0.1)
        volume = market_conditions.get('volume', 1000)
        time_to_res = market_conditions.get('time_to_resolution', 30)
        has_edge = market_conditions.get('has_edge', False)
        inventory = market_conditions.get('inventory', 0)

        recommendations = []

        # Market making if spread is wide and volume is decent
        if spread > 0.02 and volume > 500:
            recommendations.append({
                'strategy': 'market_making',
                'confidence': 0.7 if spread > 0.04 else 0.5,
                'reason': f'Wide spread ({spread*100:.1f}%) with volume'
            })

        # Arbitrage always if exists
        if market_conditions.get('arbitrage_exists', False):
            recommendations.append({
                'strategy': 'arbitrage',
                'confidence': 1.0,
                'reason': 'Risk-free profit available'
            })

        # Directional if has edge
        if has_edge:
            recommendations.append({
                'strategy': 'directional',
                'confidence': 0.6,
                'reason': 'Information edge detected'
            })

        # Hedging if large inventory
        if abs(inventory) > 100:
            recommendations.append({
                'strategy': 'hedging',
                'confidence': 0.8,
                'reason': f'Large inventory ({inventory}) needs hedging'
            })

        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)

        return {
            'recommendations': recommendations,
            'primary': recommendations[0] if recommendations else None,
            'market_conditions': market_conditions
        }

    def backtest_strategy(self, strategy: str, prices: List[float],
                          params: Dict = None) -> Dict:
        """
        Simple strategy backtest on price series.

        Returns performance metrics.
        """
        if len(prices) < 10:
            return {'error': 'Insufficient data'}

        params = params or {}
        trades = []
        position = 0
        pnl = 0
        capital = 1000

        for i in range(10, len(prices)):
            price = prices[i]
            hist = prices[i-10:i]

            if strategy == 'momentum':
                signal = self.momentum_signal(hist)
                if signal['direction'] == 'long' and position <= 0:
                    trades.append({'type': 'buy', 'price': price})
                    position = capital / price
                elif signal['direction'] == 'short' and position >= 0:
                    if position > 0:
                        pnl += position * price - capital
                    trades.append({'type': 'sell', 'price': price})
                    position = 0

            elif strategy == 'mean_reversion':
                fair = sum(hist) / len(hist)
                signal = self.mean_reversion_signal(price, fair)
                # Similar logic...

        # Final P&L
        if position > 0:
            pnl += position * prices[-1] - capital

        return {
            'total_pnl': pnl,
            'return_percent': pnl / capital * 100,
            'num_trades': len(trades),
            'trades': trades[:10],  # First 10 trades
            'final_position': position
        }


# Singleton instance
strategies = TradingStrategies()
