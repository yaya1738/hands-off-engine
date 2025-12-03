"""
Polymarket Risk Management
==========================

Complete risk management for prediction market trading:
- Position limits and sizing
- Drawdown monitoring
- Correlation risk
- Concentration limits
- Value at Risk (VaR)
- Stop-loss management

USAGE:
    from executor.polymarket.risk import risk

    risk.check_position_limit(size, max_position)
    risk.calculate_var(returns, confidence=0.95)
    risk.max_drawdown(equity_curve)
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskLimits:
    """Risk limit configuration"""
    max_position_size: float = 1000
    max_portfolio_exposure: float = 10000
    max_single_market_pct: float = 0.25  # 25% max in one market
    max_drawdown_pct: float = 0.20  # 20% max drawdown
    max_daily_loss: float = 500
    max_correlation: float = 0.7
    min_liquidity_ratio: float = 2.0  # 2x position must be available


@dataclass
class RiskMetrics:
    """Current risk metrics"""
    portfolio_exposure: float
    max_single_position: float
    concentration_hhi: float
    current_drawdown: float
    daily_pnl: float
    var_95: float
    positions_at_risk: int


class RiskManager:
    """
    Risk management for Polymarket trading.

    Monitors and enforces risk limits across the portfolio.
    """

    def __init__(self, limits: RiskLimits = None):
        self.limits = limits or RiskLimits()
        self.peak_value: float = 0
        self.daily_start_value: float = 0
        self.daily_start_time: datetime = datetime.now()

    # ==========================================
    # POSITION SIZING
    # ==========================================

    def check_position_limit(self, proposed_size: float,
                             current_position: float = 0) -> Dict:
        """Check if proposed position is within limits"""
        new_position = current_position + proposed_size
        within_limit = abs(new_position) <= self.limits.max_position_size

        return {
            'approved': within_limit,
            'proposed_size': proposed_size,
            'current_position': current_position,
            'new_position': new_position,
            'limit': self.limits.max_position_size,
            'headroom': self.limits.max_position_size - abs(new_position)
        }

    def optimal_position_size(self, edge: float, win_prob: float,
                              bankroll: float, max_position: float = None) -> Dict:
        """
        Calculate optimal position size using Kelly criterion.

        f* = (p*b - q) / b
        where: p = win prob, q = lose prob, b = odds - 1
        """
        if win_prob <= 0 or win_prob >= 1:
            return {'size': 0, 'error': 'Invalid probability'}

        odds = 1 / (1 - win_prob) if edge > 0 else 1 / win_prob
        b = odds - 1
        p = win_prob
        q = 1 - win_prob

        kelly_fraction = (p * b - q) / b if b > 0 else 0
        kelly_fraction = max(0, kelly_fraction)

        # Half-Kelly for safety
        conservative_fraction = kelly_fraction / 2

        # Apply limits
        kelly_size = bankroll * kelly_fraction
        conservative_size = bankroll * conservative_fraction

        if max_position:
            kelly_size = min(kelly_size, max_position)
            conservative_size = min(conservative_size, max_position)

        return {
            'kelly_fraction': kelly_fraction,
            'kelly_size': kelly_size,
            'half_kelly_fraction': conservative_fraction,
            'half_kelly_size': conservative_size,
            'edge': edge,
            'win_probability': win_prob,
            'bankroll': bankroll
        }

    def position_scaling(self, confidence: float, base_size: float,
                         volatility: float = 0.1) -> float:
        """Scale position size based on confidence and volatility"""
        # Higher confidence = larger position
        # Higher volatility = smaller position
        confidence_factor = max(0.1, min(2.0, confidence))
        volatility_factor = 1 / (1 + volatility * 10)

        scaled_size = base_size * confidence_factor * volatility_factor
        return min(scaled_size, self.limits.max_position_size)

    # ==========================================
    # PORTFOLIO RISK
    # ==========================================

    def check_portfolio_exposure(self, current_exposure: float,
                                 proposed_addition: float) -> Dict:
        """Check total portfolio exposure"""
        new_exposure = current_exposure + proposed_addition
        within_limit = new_exposure <= self.limits.max_portfolio_exposure

        return {
            'approved': within_limit,
            'current_exposure': current_exposure,
            'proposed_addition': proposed_addition,
            'new_exposure': new_exposure,
            'limit': self.limits.max_portfolio_exposure,
            'utilization': new_exposure / self.limits.max_portfolio_exposure
        }

    def concentration_check(self, position_sizes: Dict[str, float]) -> Dict:
        """Check position concentration"""
        total = sum(position_sizes.values())
        if total == 0:
            return {'passed': True, 'hhi': 0}

        weights = {k: v / total for k, v in position_sizes.items()}
        max_weight = max(weights.values())

        # Herfindahl-Hirschman Index
        hhi = sum(w ** 2 for w in weights.values())

        violations = []
        for market, weight in weights.items():
            if weight > self.limits.max_single_market_pct:
                violations.append({
                    'market': market,
                    'weight': weight,
                    'limit': self.limits.max_single_market_pct
                })

        return {
            'passed': len(violations) == 0,
            'hhi': hhi,
            'max_weight': max_weight,
            'violations': violations,
            'risk_level': 'high' if hhi > 0.5 else 'medium' if hhi > 0.25 else 'low'
        }

    def correlation_risk(self, positions: List[Dict],
                         correlation_matrix: List[List[float]]) -> Dict:
        """Assess correlation-based portfolio risk"""
        n = len(positions)
        if n < 2:
            return {'correlation_risk': 0}

        # Find highly correlated pairs
        high_correlation_pairs = []
        portfolio_correlation = 0

        for i in range(n):
            for j in range(i + 1, n):
                corr = correlation_matrix[i][j]
                weight_product = (positions[i]['weight'] * positions[j]['weight'])
                portfolio_correlation += 2 * weight_product * corr

                if abs(corr) > self.limits.max_correlation:
                    high_correlation_pairs.append({
                        'pair': (positions[i]['id'], positions[j]['id']),
                        'correlation': corr,
                        'combined_weight': positions[i]['weight'] + positions[j]['weight']
                    })

        return {
            'portfolio_correlation': portfolio_correlation,
            'high_correlation_pairs': high_correlation_pairs,
            'diversification_score': 1 - abs(portfolio_correlation),
            'warning': len(high_correlation_pairs) > 0
        }

    # ==========================================
    # DRAWDOWN MANAGEMENT
    # ==========================================

    def update_peak(self, current_value: float) -> None:
        """Update peak value for drawdown tracking"""
        if current_value > self.peak_value:
            self.peak_value = current_value

    def current_drawdown(self, current_value: float) -> Dict:
        """Calculate current drawdown from peak"""
        self.update_peak(current_value)

        if self.peak_value == 0:
            drawdown = 0
        else:
            drawdown = (self.peak_value - current_value) / self.peak_value

        return {
            'current_value': current_value,
            'peak_value': self.peak_value,
            'drawdown': drawdown,
            'drawdown_pct': drawdown * 100,
            'within_limit': drawdown <= self.limits.max_drawdown_pct,
            'limit': self.limits.max_drawdown_pct
        }

    def max_drawdown(self, equity_curve: List[float]) -> Dict:
        """Calculate maximum drawdown from equity curve"""
        if not equity_curve:
            return {'max_drawdown': 0}

        peak = equity_curve[0]
        max_dd = 0
        max_dd_start = 0
        max_dd_end = 0
        current_dd_start = 0

        for i, value in enumerate(equity_curve):
            if value > peak:
                peak = value
                current_dd_start = i

            dd = (peak - value) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
                max_dd_start = current_dd_start
                max_dd_end = i

        return {
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd * 100,
            'drawdown_start_idx': max_dd_start,
            'drawdown_end_idx': max_dd_end,
            'exceeded_limit': max_dd > self.limits.max_drawdown_pct
        }

    def drawdown_recovery_time(self, equity_curve: List[float]) -> Dict:
        """Analyze drawdown recovery characteristics"""
        if len(equity_curve) < 2:
            return {'avg_recovery': 0}

        in_drawdown = False
        drawdown_start = 0
        recovery_times = []
        peak = equity_curve[0]

        for i, value in enumerate(equity_curve):
            if value > peak:
                if in_drawdown:
                    recovery_times.append(i - drawdown_start)
                    in_drawdown = False
                peak = value
            elif value < peak * 0.98 and not in_drawdown:  # 2% threshold
                in_drawdown = True
                drawdown_start = i

        return {
            'num_drawdowns': len(recovery_times),
            'avg_recovery_periods': sum(recovery_times) / len(recovery_times) if recovery_times else 0,
            'max_recovery_periods': max(recovery_times) if recovery_times else 0,
            'currently_in_drawdown': in_drawdown
        }

    # ==========================================
    # VALUE AT RISK
    # ==========================================

    def calculate_var(self, returns: List[float], confidence: float = 0.95) -> Dict:
        """
        Calculate Value at Risk using historical method.

        VaR = potential loss at given confidence level
        """
        if not returns:
            return {'var': 0}

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        var = -sorted_returns[index] if index < len(sorted_returns) else 0

        # CVaR (Expected Shortfall)
        tail_returns = sorted_returns[:index + 1]
        cvar = -sum(tail_returns) / len(tail_returns) if tail_returns else 0

        return {
            'var': var,
            'var_pct': var * 100,
            'cvar': cvar,  # Expected loss beyond VaR
            'cvar_pct': cvar * 100,
            'confidence': confidence,
            'sample_size': len(returns)
        }

    def parametric_var(self, mean_return: float, std_return: float,
                       confidence: float = 0.95,
                       position_value: float = 1.0) -> Dict:
        """Calculate VaR using parametric (normal) method"""
        # Z-score for confidence level
        z_scores = {0.90: 1.28, 0.95: 1.645, 0.99: 2.33}
        z = z_scores.get(confidence, 1.645)

        var = (mean_return - z * std_return) * position_value
        if var > 0:
            var = 0  # VaR is a loss

        return {
            'var': abs(var),
            'var_pct': abs(var) / position_value * 100 if position_value > 0 else 0,
            'confidence': confidence,
            'z_score': z,
            'mean_return': mean_return,
            'std_return': std_return
        }

    def portfolio_var(self, positions: List[Dict],
                      correlations: List[List[float]],
                      confidence: float = 0.95) -> Dict:
        """Calculate portfolio VaR considering correlations"""
        n = len(positions)
        if n == 0:
            return {'portfolio_var': 0}

        # Portfolio variance = sum of weighted covariances
        portfolio_variance = 0
        for i in range(n):
            for j in range(n):
                cov = (correlations[i][j] *
                       positions[i]['volatility'] *
                       positions[j]['volatility'] *
                       positions[i]['value'] *
                       positions[j]['value'])
                portfolio_variance += cov

        portfolio_std = math.sqrt(portfolio_variance) if portfolio_variance > 0 else 0
        z = 1.645 if confidence == 0.95 else 2.33 if confidence == 0.99 else 1.28

        portfolio_var = z * portfolio_std

        # Undiversified VaR (sum of individual VaRs)
        undiversified_var = sum(
            z * p['volatility'] * p['value'] for p in positions
        )

        return {
            'portfolio_var': portfolio_var,
            'undiversified_var': undiversified_var,
            'diversification_benefit': undiversified_var - portfolio_var,
            'portfolio_volatility': portfolio_std,
            'confidence': confidence
        }

    # ==========================================
    # STOP LOSS MANAGEMENT
    # ==========================================

    def calculate_stop_loss(self, entry_price: float, risk_pct: float,
                            side: str) -> float:
        """Calculate stop loss price"""
        if side.upper() == 'BUY':
            return entry_price * (1 - risk_pct)
        else:
            return entry_price * (1 + risk_pct)

    def trailing_stop(self, entry_price: float, current_price: float,
                      trail_pct: float, side: str) -> Dict:
        """Calculate trailing stop level"""
        if side.upper() == 'BUY':
            # Long position: trail below highest price
            highest = max(entry_price, current_price)
            stop = highest * (1 - trail_pct)
            triggered = current_price <= stop
        else:
            # Short position: trail above lowest price
            lowest = min(entry_price, current_price)
            stop = lowest * (1 + trail_pct)
            triggered = current_price >= stop

        return {
            'stop_level': stop,
            'current_price': current_price,
            'triggered': triggered,
            'distance_to_stop': abs(current_price - stop),
            'distance_pct': abs(current_price - stop) / current_price * 100
        }

    def dynamic_stop(self, volatility: float, atr_multiple: float = 2.0,
                     current_price: float = 1.0) -> float:
        """Calculate dynamic stop based on volatility"""
        stop_distance = volatility * atr_multiple
        return current_price * (1 - stop_distance)

    # ==========================================
    # DAILY LIMITS
    # ==========================================

    def check_daily_loss(self, current_pnl: float) -> Dict:
        """Check if daily loss limit is breached"""
        # Reset at start of new day
        if datetime.now().date() > self.daily_start_time.date():
            self.daily_start_time = datetime.now()
            self.daily_start_value = 0

        within_limit = abs(current_pnl) <= self.limits.max_daily_loss

        return {
            'daily_pnl': current_pnl,
            'limit': self.limits.max_daily_loss,
            'within_limit': within_limit,
            'remaining': self.limits.max_daily_loss - abs(current_pnl) if current_pnl < 0 else self.limits.max_daily_loss,
            'action': 'stop_trading' if not within_limit else 'continue'
        }

    # ==========================================
    # RISK ASSESSMENT
    # ==========================================

    def overall_risk_level(self, metrics: RiskMetrics) -> RiskLevel:
        """Determine overall portfolio risk level"""
        risk_score = 0

        # Exposure check
        if metrics.portfolio_exposure > self.limits.max_portfolio_exposure * 0.9:
            risk_score += 3
        elif metrics.portfolio_exposure > self.limits.max_portfolio_exposure * 0.7:
            risk_score += 2

        # Concentration check
        if metrics.concentration_hhi > 0.5:
            risk_score += 3
        elif metrics.concentration_hhi > 0.25:
            risk_score += 1

        # Drawdown check
        if metrics.current_drawdown > self.limits.max_drawdown_pct:
            risk_score += 4
        elif metrics.current_drawdown > self.limits.max_drawdown_pct * 0.7:
            risk_score += 2

        # Daily P&L check
        if abs(metrics.daily_pnl) > self.limits.max_daily_loss * 0.8:
            risk_score += 2

        if risk_score >= 8:
            return RiskLevel.CRITICAL
        elif risk_score >= 5:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def risk_report(self, portfolio_value: float, positions: Dict,
                    daily_pnl: float) -> Dict:
        """Generate comprehensive risk report"""
        exposure = sum(positions.values())
        dd = self.current_drawdown(portfolio_value)

        metrics = RiskMetrics(
            portfolio_exposure=exposure,
            max_single_position=max(positions.values()) if positions else 0,
            concentration_hhi=sum((v/exposure)**2 for v in positions.values()) if exposure > 0 else 0,
            current_drawdown=dd['drawdown'],
            daily_pnl=daily_pnl,
            var_95=0,  # Would need historical returns
            positions_at_risk=sum(1 for v in positions.values() if v > self.limits.max_position_size * 0.8)
        )

        return {
            'risk_level': self.overall_risk_level(metrics).value,
            'metrics': {
                'portfolio_exposure': metrics.portfolio_exposure,
                'exposure_utilization': metrics.portfolio_exposure / self.limits.max_portfolio_exposure,
                'concentration_hhi': metrics.concentration_hhi,
                'current_drawdown_pct': metrics.current_drawdown * 100,
                'daily_pnl': metrics.daily_pnl,
                'positions_at_risk': metrics.positions_at_risk
            },
            'limits': {
                'max_position': self.limits.max_position_size,
                'max_exposure': self.limits.max_portfolio_exposure,
                'max_drawdown': self.limits.max_drawdown_pct,
                'max_daily_loss': self.limits.max_daily_loss
            },
            'recommendations': self._generate_recommendations(metrics)
        }

    def _generate_recommendations(self, metrics: RiskMetrics) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []

        if metrics.portfolio_exposure > self.limits.max_portfolio_exposure * 0.8:
            recommendations.append("Consider reducing overall exposure")

        if metrics.concentration_hhi > 0.3:
            recommendations.append("Portfolio is concentrated - diversify positions")

        if metrics.current_drawdown > self.limits.max_drawdown_pct * 0.5:
            recommendations.append("Drawdown elevated - consider reducing risk")

        if metrics.daily_pnl < -self.limits.max_daily_loss * 0.5:
            recommendations.append("Significant daily loss - review position sizes")

        return recommendations


# Singleton instance
risk = RiskManager()
