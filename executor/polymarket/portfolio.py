"""
Polymarket Portfolio & Position Management
==========================================

Complete position and portfolio tracking:
- Position tracking (entry, exit, P&L)
- Portfolio aggregation
- Mark-to-market valuation
- Performance metrics
- Trade history analysis

USAGE:
    from executor.polymarket.portfolio import portfolio

    portfolio.add_position(token_id, 100, 0.65)
    portfolio.update_prices({token_id: 0.70})
    portfolio.get_summary()
"""

import math
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class PositionSide(Enum):
    LONG = "LONG"    # Own YES tokens or bought NO
    SHORT = "SHORT"  # Sold YES tokens (if possible)
    FLAT = "FLAT"


@dataclass
class Position:
    """Individual position in a market"""
    token_id: str
    market_name: str
    side: PositionSide
    size: float
    entry_price: float
    current_price: float
    entry_time: datetime
    outcome: str  # YES or NO

    @property
    def cost_basis(self) -> float:
        return self.size * self.entry_price

    @property
    def market_value(self) -> float:
        return self.size * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_percent(self) -> float:
        if self.cost_basis == 0:
            return 0
        return self.unrealized_pnl / self.cost_basis * 100

    @property
    def max_profit(self) -> float:
        """Max profit if outcome wins (price goes to 1)"""
        return self.size * (1.0 - self.entry_price)

    @property
    def max_loss(self) -> float:
        """Max loss if outcome loses (price goes to 0)"""
        return self.cost_basis


@dataclass
class Trade:
    """Completed trade record"""
    trade_id: str
    token_id: str
    side: str  # BUY or SELL
    price: float
    size: float
    timestamp: datetime
    fee: float = 0.0

    @property
    def value(self) -> float:
        return self.size * self.price


@dataclass
class PortfolioSnapshot:
    """Point-in-time portfolio snapshot"""
    timestamp: datetime
    total_value: float
    cash_balance: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    position_count: int


class PortfolioManager:
    """
    Portfolio management for Polymarket positions.

    Tracks positions, calculates P&L, and provides portfolio analytics.
    """

    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.cash_balance: float = 0
        self.realized_pnl: float = 0
        self.snapshots: List[PortfolioSnapshot] = []

    # ==========================================
    # POSITION MANAGEMENT
    # ==========================================

    def add_position(self, token_id: str, size: float, price: float,
                     market_name: str = "", outcome: str = "YES") -> Position:
        """Add or increase a position"""
        if token_id in self.positions:
            # Average into existing position
            existing = self.positions[token_id]
            total_cost = existing.cost_basis + (size * price)
            total_size = existing.size + size
            avg_price = total_cost / total_size if total_size > 0 else price

            existing.size = total_size
            existing.entry_price = avg_price
            return existing
        else:
            position = Position(
                token_id=token_id,
                market_name=market_name or token_id[:8],
                side=PositionSide.LONG,
                size=size,
                entry_price=price,
                current_price=price,
                entry_time=datetime.now(),
                outcome=outcome
            )
            self.positions[token_id] = position
            return position

    def reduce_position(self, token_id: str, size: float,
                        price: float) -> Dict:
        """Reduce a position (partial or full exit)"""
        if token_id not in self.positions:
            return {'error': 'Position not found'}

        position = self.positions[token_id]
        if size > position.size:
            size = position.size  # Can't reduce more than held

        # Calculate realized P&L
        realized = size * (price - position.entry_price)
        self.realized_pnl += realized

        # Update position
        position.size -= size
        if position.size <= 0.001:  # Close position if near zero
            del self.positions[token_id]

        return {
            'reduced_size': size,
            'exit_price': price,
            'realized_pnl': realized,
            'remaining_size': position.size if token_id in self.positions else 0
        }

    def close_position(self, token_id: str, price: float) -> Dict:
        """Fully close a position"""
        if token_id not in self.positions:
            return {'error': 'Position not found'}

        position = self.positions[token_id]
        return self.reduce_position(token_id, position.size, price)

    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update current prices for positions"""
        for token_id, price in prices.items():
            if token_id in self.positions:
                self.positions[token_id].current_price = price

    # ==========================================
    # PORTFOLIO VALUATION
    # ==========================================

    def total_value(self) -> float:
        """Total portfolio value (cash + positions)"""
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash_balance + positions_value

    def positions_value(self) -> float:
        """Total value of open positions"""
        return sum(p.market_value for p in self.positions.values())

    def cost_basis_total(self) -> float:
        """Total cost basis of positions"""
        return sum(p.cost_basis for p in self.positions.values())

    def unrealized_pnl_total(self) -> float:
        """Total unrealized P&L"""
        return sum(p.unrealized_pnl for p in self.positions.values())

    def total_pnl(self) -> float:
        """Total P&L (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl_total()

    def max_potential_value(self) -> Dict:
        """
        Calculate max portfolio value based on outcomes.

        Returns best and worst case scenarios.
        """
        best_case = self.cash_balance
        worst_case = self.cash_balance

        for position in self.positions.values():
            # Best case: all positions win (go to 1)
            best_case += position.size * 1.0
            # Worst case: all positions lose (go to 0)
            # worst_case += 0

        return {
            'best_case': best_case,
            'worst_case': worst_case,
            'current_value': self.total_value(),
            'upside': best_case - self.total_value(),
            'downside': self.total_value() - worst_case
        }

    # ==========================================
    # PORTFOLIO ANALYTICS
    # ==========================================

    def get_summary(self) -> Dict:
        """Get portfolio summary"""
        positions_list = list(self.positions.values())

        return {
            'total_value': self.total_value(),
            'cash_balance': self.cash_balance,
            'positions_value': self.positions_value(),
            'cost_basis': self.cost_basis_total(),
            'unrealized_pnl': self.unrealized_pnl_total(),
            'realized_pnl': self.realized_pnl,
            'total_pnl': self.total_pnl(),
            'position_count': len(positions_list),
            'winning_positions': sum(1 for p in positions_list if p.unrealized_pnl > 0),
            'losing_positions': sum(1 for p in positions_list if p.unrealized_pnl < 0)
        }

    def exposure_by_outcome(self) -> Dict:
        """Calculate exposure by YES/NO outcomes"""
        yes_exposure = sum(p.market_value for p in self.positions.values()
                         if p.outcome == 'YES')
        no_exposure = sum(p.market_value for p in self.positions.values()
                        if p.outcome == 'NO')

        return {
            'yes_exposure': yes_exposure,
            'no_exposure': no_exposure,
            'net_directional': yes_exposure - no_exposure,
            'total_exposure': yes_exposure + no_exposure
        }

    def concentration_analysis(self) -> Dict:
        """Analyze position concentration"""
        if not self.positions:
            return {'concentration': 0, 'max_position': 0}

        total = self.positions_value()
        if total == 0:
            return {'concentration': 0, 'max_position': 0}

        sizes = sorted([p.market_value / total for p in self.positions.values()],
                      reverse=True)

        # Herfindahl-Hirschman Index (concentration measure)
        hhi = sum(s ** 2 for s in sizes)

        return {
            'hhi': hhi,  # 0 = diversified, 1 = concentrated
            'concentration': 'high' if hhi > 0.5 else 'medium' if hhi > 0.25 else 'low',
            'largest_position_pct': sizes[0] * 100 if sizes else 0,
            'top3_positions_pct': sum(sizes[:3]) * 100 if len(sizes) >= 3 else sum(sizes) * 100
        }

    def risk_contribution(self) -> List[Dict]:
        """Calculate each position's risk contribution"""
        contributions = []
        total_exposure = self.positions_value()

        for token_id, position in self.positions.items():
            weight = position.market_value / total_exposure if total_exposure > 0 else 0

            # Risk = max potential loss
            max_loss = position.cost_basis
            risk_contribution = max_loss / total_exposure if total_exposure > 0 else 0

            contributions.append({
                'token_id': token_id,
                'market_name': position.market_name,
                'weight': weight,
                'max_loss': max_loss,
                'risk_contribution': risk_contribution,
                'current_pnl': position.unrealized_pnl
            })

        contributions.sort(key=lambda x: x['risk_contribution'], reverse=True)
        return contributions

    # ==========================================
    # TRADE TRACKING
    # ==========================================

    def record_trade(self, trade: Trade) -> None:
        """Record a completed trade"""
        self.trades.append(trade)

        # Update cash balance
        if trade.side == 'BUY':
            self.cash_balance -= trade.value + trade.fee
        else:
            self.cash_balance += trade.value - trade.fee

    def trade_history(self, token_id: str = None,
                     limit: int = 100) -> List[Trade]:
        """Get trade history, optionally filtered by token"""
        trades = self.trades
        if token_id:
            trades = [t for t in trades if t.token_id == token_id]
        return sorted(trades, key=lambda t: t.timestamp, reverse=True)[:limit]

    def trade_statistics(self, days: int = None) -> Dict:
        """Calculate trade statistics"""
        trades = self.trades
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            trades = [t for t in trades if t.timestamp >= cutoff]

        if not trades:
            return {'num_trades': 0}

        buys = [t for t in trades if t.side == 'BUY']
        sells = [t for t in trades if t.side == 'SELL']

        return {
            'num_trades': len(trades),
            'num_buys': len(buys),
            'num_sells': len(sells),
            'total_volume': sum(t.value for t in trades),
            'buy_volume': sum(t.value for t in buys),
            'sell_volume': sum(t.value for t in sells),
            'total_fees': sum(t.fee for t in trades),
            'avg_trade_size': sum(t.size for t in trades) / len(trades)
        }

    # ==========================================
    # PERFORMANCE METRICS
    # ==========================================

    def returns_analysis(self) -> Dict:
        """Calculate return metrics"""
        total_invested = self.cost_basis_total() + self.realized_pnl
        if total_invested <= 0:
            return {'return_pct': 0}

        total_return = self.total_pnl()
        return_pct = total_return / total_invested * 100

        return {
            'total_return': total_return,
            'return_percent': return_pct,
            'total_invested': total_invested,
            'current_value': self.total_value()
        }

    def win_rate(self) -> Dict:
        """Calculate win rate from closed positions"""
        # Would need historical closed position data
        # For now, analyze current positions
        positions = list(self.positions.values())
        if not positions:
            return {'win_rate': 0, 'avg_win': 0, 'avg_loss': 0}

        winners = [p for p in positions if p.unrealized_pnl > 0]
        losers = [p for p in positions if p.unrealized_pnl < 0]

        avg_win = sum(p.unrealized_pnl for p in winners) / len(winners) if winners else 0
        avg_loss = sum(p.unrealized_pnl for p in losers) / len(losers) if losers else 0

        return {
            'win_rate': len(winners) / len(positions) * 100,
            'num_winners': len(winners),
            'num_losers': len(losers),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(sum(p.unrealized_pnl for p in winners) /
                                sum(p.unrealized_pnl for p in losers))
                           if losers and sum(p.unrealized_pnl for p in losers) != 0 else float('inf')
        }

    def take_snapshot(self) -> PortfolioSnapshot:
        """Take a portfolio snapshot for time-series tracking"""
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(),
            total_value=self.total_value(),
            cash_balance=self.cash_balance,
            positions_value=self.positions_value(),
            unrealized_pnl=self.unrealized_pnl_total(),
            realized_pnl=self.realized_pnl,
            position_count=len(self.positions)
        )
        self.snapshots.append(snapshot)
        return snapshot

    def equity_curve(self) -> List[Dict]:
        """Get equity curve from snapshots"""
        return [
            {
                'timestamp': s.timestamp.isoformat(),
                'value': s.total_value,
                'pnl': s.unrealized_pnl + s.realized_pnl
            }
            for s in self.snapshots
        ]

    # ==========================================
    # POSITION QUERIES
    # ==========================================

    def get_position(self, token_id: str) -> Optional[Position]:
        """Get specific position"""
        return self.positions.get(token_id)

    def get_all_positions(self) -> List[Position]:
        """Get all positions sorted by value"""
        return sorted(self.positions.values(),
                     key=lambda p: p.market_value, reverse=True)

    def get_profitable_positions(self) -> List[Position]:
        """Get positions with positive P&L"""
        return [p for p in self.positions.values() if p.unrealized_pnl > 0]

    def get_losing_positions(self) -> List[Position]:
        """Get positions with negative P&L"""
        return [p for p in self.positions.values() if p.unrealized_pnl < 0]

    def positions_by_market(self) -> Dict[str, List[Position]]:
        """Group positions by market"""
        by_market = {}
        for position in self.positions.values():
            market = position.market_name
            if market not in by_market:
                by_market[market] = []
            by_market[market].append(position)
        return by_market


# Singleton instance
portfolio = PortfolioManager()
