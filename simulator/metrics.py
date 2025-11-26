"""
Performance Metrics for Hands-Off Engine Simulator

Calculates standard trading performance metrics:
- Sharpe ratio
- Maximum drawdown
- Win rate
- Profit factor
- Edge decay analysis
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@dataclass
class PerformanceSnapshot:
    """Single point-in-time performance snapshot"""
    timestamp: datetime
    portfolio_value: float
    cash: float
    positions_value: float
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float


@dataclass
class TradeMetrics:
    """Metrics for a single completed trade"""
    market_id: str
    entry_time: datetime
    exit_time: datetime
    side: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    return_pct: float
    hold_duration_hours: float


class PerformanceMetrics:
    """
    Calculates trading performance metrics from simulation results.
    """
    
    def __init__(self):
        """Initialize metrics calculator"""
        self.snapshots: List[PerformanceSnapshot] = []
        self.trades: List[TradeMetrics] = []
        
    def add_snapshot(
        self,
        timestamp: datetime,
        portfolio_value: float,
        cash: float,
        positions_value: float,
        total_pnl: float,
        realized_pnl: float,
        unrealized_pnl: float
    ):
        """Add a performance snapshot"""
        snapshot = PerformanceSnapshot(
            timestamp=timestamp,
            portfolio_value=portfolio_value,
            cash=cash,
            positions_value=positions_value,
            total_pnl=total_pnl,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl
        )
        self.snapshots.append(snapshot)
    
    def add_trade(
        self,
        market_id: str,
        entry_time: datetime,
        exit_time: datetime,
        side: str,
        entry_price: float,
        exit_price: float,
        size: float,
        pnl: float
    ):
        """Add a completed trade"""
        hold_duration = (exit_time - entry_time).total_seconds() / 3600.0
        return_pct = (pnl / size * 100) if size > 0 else 0.0
        
        trade = TradeMetrics(
            market_id=market_id,
            entry_time=entry_time,
            exit_time=exit_time,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            size=size,
            pnl=pnl,
            return_pct=return_pct,
            hold_duration_hours=hold_duration
        )
        self.trades.append(trade)
    
    def calculate_returns(self) -> List[float]:
        """
        Calculate period-over-period returns from snapshots.
        
        Returns:
            List of returns as decimals (e.g., 0.05 for 5%)
        """
        if len(self.snapshots) < 2:
            return []
        
        returns = []
        for i in range(1, len(self.snapshots)):
            prev_value = self.snapshots[i-1].portfolio_value
            curr_value = self.snapshots[i].portfolio_value
            
            if prev_value > 0:
                ret = (curr_value - prev_value) / prev_value
                returns.append(ret)
        
        return returns
    
    def sharpe_ratio(self, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            risk_free_rate: Annual risk-free rate as decimal
            periods_per_year: Number of periods per year (252 for daily, 52 for weekly)
            
        Returns:
            Sharpe ratio (annualized)
        """
        returns = self.calculate_returns()
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate mean and std of returns
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_return = math.sqrt(variance)
        
        if std_return == 0:
            return 0.0
        
        # Annualize
        annual_return = mean_return * periods_per_year
        annual_std = std_return * math.sqrt(periods_per_year)
        
        sharpe = (annual_return - risk_free_rate) / annual_std
        return sharpe
    
    def max_drawdown(self) -> Tuple[float, float]:
        """
        Calculate maximum drawdown.
        
        Returns:
            Tuple of (max_drawdown_pct, max_drawdown_dollars)
        """
        if not self.snapshots:
            return (0.0, 0.0)
        
        peak_value = self.snapshots[0].portfolio_value
        max_dd_pct = 0.0
        max_dd_dollars = 0.0
        
        for snapshot in self.snapshots:
            value = snapshot.portfolio_value
            
            # Update peak
            if value > peak_value:
                peak_value = value
            
            # Calculate drawdown
            dd_dollars = peak_value - value
            dd_pct = (dd_dollars / peak_value * 100) if peak_value > 0 else 0.0
            
            # Update max drawdown
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
                max_dd_dollars = dd_dollars
        
        return (max_dd_pct, max_dd_dollars)
    
    def win_rate(self) -> float:
        """
        Calculate win rate from completed trades.
        
        Returns:
            Win rate as percentage (0-100)
        """
        if not self.trades:
            return 0.0
        
        winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        return (winning_trades / len(self.trades) * 100)
    
    def profit_factor(self) -> float:
        """
        Calculate profit factor (gross profit / gross loss).
        
        Returns:
            Profit factor (>1.0 is profitable)
        """
        if not self.trades:
            return 0.0
        
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def average_win(self) -> float:
        """Calculate average winning trade P&L"""
        winning_trades = [t.pnl for t in self.trades if t.pnl > 0]
        return sum(winning_trades) / len(winning_trades) if winning_trades else 0.0
    
    def average_loss(self) -> float:
        """Calculate average losing trade P&L"""
        losing_trades = [t.pnl for t in self.trades if t.pnl < 0]
        return sum(losing_trades) / len(losing_trades) if losing_trades else 0.0
    
    def total_return(self) -> float:
        """
        Calculate total return from start to end.
        
        Returns:
            Total return as percentage
        """
        if len(self.snapshots) < 2:
            return 0.0
        
        initial_value = self.snapshots[0].portfolio_value
        final_value = self.snapshots[-1].portfolio_value
        
        if initial_value == 0:
            return 0.0
        
        return ((final_value - initial_value) / initial_value * 100)
    
    def cagr(self, years: Optional[float] = None) -> float:
        """
        Calculate Compound Annual Growth Rate.
        
        Args:
            years: Duration in years (auto-calculated if None)
            
        Returns:
            CAGR as percentage
        """
        if len(self.snapshots) < 2:
            return 0.0
        
        if years is None:
            duration = (self.snapshots[-1].timestamp - self.snapshots[0].timestamp)
            years = duration.total_seconds() / (365.25 * 24 * 3600)
        
        if years == 0:
            return 0.0
        
        initial_value = self.snapshots[0].portfolio_value
        final_value = self.snapshots[-1].portfolio_value
        
        if initial_value <= 0:
            return 0.0
        
        cagr = (pow(final_value / initial_value, 1.0 / years) - 1.0) * 100
        return cagr
    
    def edge_decay_analysis(self, window_size: int = 10) -> List[Dict]:
        """
        Analyze edge decay over time using rolling windows.
        
        Args:
            window_size: Number of trades per window
            
        Returns:
            List of dicts with window metrics
        """
        if len(self.trades) < window_size:
            return []
        
        results = []
        
        for i in range(len(self.trades) - window_size + 1):
            window_trades = self.trades[i:i + window_size]
            
            # Calculate metrics for this window
            total_pnl = sum(t.pnl for t in window_trades)
            win_rate = sum(1 for t in window_trades if t.pnl > 0) / window_size * 100
            avg_return = sum(t.return_pct for t in window_trades) / window_size
            
            results.append({
                "window_start": i,
                "window_end": i + window_size - 1,
                "start_time": window_trades[0].entry_time,
                "end_time": window_trades[-1].exit_time,
                "total_pnl": total_pnl,
                "win_rate": win_rate,
                "avg_return_pct": avg_return
            })
        
        return results
    
    def get_summary(self) -> Dict:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with all key metrics
        """
        if not self.snapshots:
            return {}
        
        initial_value = self.snapshots[0].portfolio_value
        final_value = self.snapshots[-1].portfolio_value
        
        max_dd_pct, max_dd_dollars = self.max_drawdown()
        
        summary = {
            # Portfolio metrics
            "initial_value": initial_value,
            "final_value": final_value,
            "total_return_pct": self.total_return(),
            "total_pnl": final_value - initial_value,
            
            # Risk metrics
            "sharpe_ratio": self.sharpe_ratio(),
            "max_drawdown_pct": max_dd_pct,
            "max_drawdown_dollars": max_dd_dollars,
            
            # Trade metrics
            "num_trades": len(self.trades),
            "win_rate": self.win_rate(),
            "profit_factor": self.profit_factor(),
            "average_win": self.average_win(),
            "average_loss": self.average_loss(),
            
            # Time metrics
            "start_date": self.snapshots[0].timestamp.isoformat() if self.snapshots else None,
            "end_date": self.snapshots[-1].timestamp.isoformat() if self.snapshots else None,
            "duration_days": (self.snapshots[-1].timestamp - self.snapshots[0].timestamp).days if len(self.snapshots) > 1 else 0,
            
            # Snapshot count
            "num_snapshots": len(self.snapshots)
        }
        
        return summary


if __name__ == "__main__":
    # Example usage
    print("Performance Metrics Example\n" + "=" * 50)
    
    metrics = PerformanceMetrics()
    
    # Add some sample snapshots
    from datetime import timedelta, timezone
    
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    initial_value = 1000.0
    
    for i in range(30):
        # Simulate portfolio growth with some volatility
        import random
        value = initial_value * (1.0 + 0.002 * i + random.gauss(0, 0.01))
        
        metrics.add_snapshot(
            timestamp=base_time + timedelta(days=i),
            portfolio_value=value,
            cash=value * 0.5,
            positions_value=value * 0.5,
            total_pnl=value - initial_value,
            realized_pnl=(value - initial_value) * 0.3,
            unrealized_pnl=(value - initial_value) * 0.7
        )
    
    # Add some sample trades
    for i in range(10):
        entry_time = base_time + timedelta(days=i*2)
        exit_time = entry_time + timedelta(days=1)
        pnl = random.gauss(5, 10)  # Random P&L
        
        metrics.add_trade(
            market_id=f"market_{i}",
            entry_time=entry_time,
            exit_time=exit_time,
            side="YES",
            entry_price=0.50,
            exit_price=0.55,
            size=100.0,
            pnl=pnl
        )
    
    # Get summary
    summary = metrics.get_summary()
    
    print(f"Total Return: {summary['total_return_pct']:.2f}%")
    print(f"Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {summary['max_drawdown_pct']:.2f}%")
    print(f"Win Rate: {summary['win_rate']:.2f}%")
    print(f"Profit Factor: {summary['profit_factor']:.2f}")
    print(f"Number of Trades: {summary['num_trades']}")
