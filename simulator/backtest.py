"""
Backtest Engine for Hands-Off Engine

Orchestrates backtesting by combining:
- Market simulation
- Strategy execution
- Performance tracking
- Results reporting
"""

import sys
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional, Callable
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger
from .market import MarketSimulator, MarketSnapshot
from .executor import ExecutionSimulator, OrderSide
from .metrics import PerformanceMetrics


@dataclass
class BacktestConfig:
    """Configuration for a backtest run"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 1000.0
    fee_rate: float = 0.02
    slippage_rate: float = 0.005
    interval_hours: int = 1
    market_ids: Optional[List[str]] = None


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    config: BacktestConfig
    metrics: PerformanceMetrics
    final_portfolio_value: float
    total_return_pct: float
    num_trades: int
    success: bool
    error_message: Optional[str] = None


# Type for strategy functions
# Strategy takes (timestamp, market_snapshots, executor) and returns list of actions
StrategyFunc = Callable[[datetime, Dict[str, MarketSnapshot], ExecutionSimulator], List[Dict]]


class BacktestEngine:
    """
    Main backtesting engine.
    
    Runs strategies over historical or synthetic data and tracks performance.
    """
    
    def __init__(
        self,
        market_simulator: Optional[MarketSimulator] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize backtest engine.
        
        Args:
            market_simulator: Market simulator (creates one if None)
            output_dir: Directory for backtest results
        """
        self.market_sim = market_simulator or MarketSimulator()
        self.output_dir = output_dir or Path("data/simulations")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audit = get_audit_logger(component="simulator.backtest")
        
    def run_backtest(
        self,
        config: BacktestConfig,
        strategy: StrategyFunc
    ) -> BacktestResult:
        """
        Run a backtest with given configuration and strategy.
        
        Args:
            config: Backtest configuration
            strategy: Strategy function to test
            
        Returns:
            BacktestResult with performance metrics
        """
        self.audit.log_action(
            action_type="backtest_start",
            action_data={
                "strategy": config.strategy_name,
                "start_date": config.start_date.isoformat(),
                "end_date": config.end_date.isoformat(),
                "initial_capital": config.initial_capital
            },
            result="started"
        )
        
        try:
            # Initialize execution simulator
            executor = ExecutionSimulator(
                initial_capital=config.initial_capital,
                fee_rate=config.fee_rate,
                slippage_rate=config.slippage_rate
            )
            
            # Initialize performance tracker
            metrics = PerformanceMetrics()
            
            # Get list of timestamps to simulate
            current_time = config.start_date
            timestamps = []
            while current_time <= config.end_date:
                timestamps.append(current_time)
                current_time += timedelta(hours=config.interval_hours)
            
            # Run simulation step by step
            for timestamp in timestamps:
                # Get market snapshots at this time
                market_snapshots = self.market_sim.get_all_markets_at_time(timestamp)
                
                if not market_snapshots:
                    continue
                
                # Run strategy to get actions
                try:
                    actions = strategy(timestamp, market_snapshots, executor)
                    
                    # Execute each action
                    for action in actions:
                        market_id = action.get('market_id')
                        side = action.get('side')
                        size = action.get('size')
                        
                        if not market_id or not side or not size:
                            continue
                        
                        if market_id not in market_snapshots:
                            continue
                        
                        snapshot = market_snapshots[market_id]
                        
                        # Execute order
                        executor.execute_order(
                            timestamp=timestamp,
                            market_id=market_id,
                            market_name=snapshot.market_name,
                            side=side,
                            size=size,
                            market_price=snapshot.yes_price,
                            limit_price=action.get('limit_price')
                        )
                    
                except Exception as e:
                    self.audit.log_error(
                        error_type="strategy_error",
                        error_message=str(e),
                        context={"timestamp": timestamp.isoformat()}
                    )
                    continue
                
                # Record performance snapshot
                current_prices = {
                    mid: snapshot.yes_price
                    for mid, snapshot in market_snapshots.items()
                }
                
                portfolio_metrics = executor.get_metrics(current_prices)
                
                metrics.add_snapshot(
                    timestamp=timestamp,
                    portfolio_value=portfolio_metrics['total_value'],
                    cash=portfolio_metrics['capital'],
                    positions_value=portfolio_metrics['positions_value'],
                    total_pnl=portfolio_metrics['total_pnl'],
                    realized_pnl=portfolio_metrics['realized_pnl'],
                    unrealized_pnl=portfolio_metrics['unrealized_pnl']
                )
            
            # Calculate final metrics
            final_prices = self.market_sim.get_all_markets_at_time(config.end_date)
            final_market_prices = {
                mid: snapshot.yes_price
                for mid, snapshot in final_prices.items()
            }
            
            final_value = executor.get_portfolio_value(final_market_prices)
            total_return = ((final_value - config.initial_capital) / config.initial_capital * 100)
            
            result = BacktestResult(
                config=config,
                metrics=metrics,
                final_portfolio_value=final_value,
                total_return_pct=total_return,
                num_trades=len(executor.orders),
                success=True
            )
            
            self.audit.log_action(
                action_type="backtest_complete",
                action_data={
                    "strategy": config.strategy_name,
                    "final_value": final_value,
                    "total_return_pct": total_return,
                    "num_trades": len(executor.orders)
                },
                result="completed"
            )
            
            return result
            
        except Exception as e:
            self.audit.log_error(
                error_type="backtest_error",
                error_message=str(e),
                context={"strategy": config.strategy_name}
            )
            
            return BacktestResult(
                config=config,
                metrics=PerformanceMetrics(),
                final_portfolio_value=0.0,
                total_return_pct=0.0,
                num_trades=0,
                success=False,
                error_message=str(e)
            )
    
    def save_results(
        self,
        result: BacktestResult,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save backtest results to file.
        
        Args:
            result: BacktestResult to save
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_{result.config.strategy_name}_{timestamp}.json"
        
        output_file = self.output_dir / filename
        
        # Prepare data for JSON serialization
        summary = result.metrics.get_summary()
        
        data = {
            "strategy": result.config.strategy_name,
            "start_date": result.config.start_date.isoformat(),
            "end_date": result.config.end_date.isoformat(),
            "initial_capital": result.config.initial_capital,
            "final_value": result.final_portfolio_value,
            "total_return_pct": result.total_return_pct,
            "num_trades": result.num_trades,
            "success": result.success,
            "error_message": result.error_message,
            "metrics": summary
        }
        
        # Atomic write
        temp_file = output_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        temp_file.replace(output_file)
        
        self.audit.log_action(
            action_type="save_results",
            action_data={
                "strategy": result.config.strategy_name,
                "output_file": str(output_file)
            },
            result="completed"
        )
        
        return output_file
    
    def compare_strategies(
        self,
        results: List[BacktestResult]
    ) -> Dict:
        """
        Compare multiple backtest results.
        
        Args:
            results: List of BacktestResult objects
            
        Returns:
            Dictionary with comparison data
        """
        if not results:
            return {}
        
        comparison = {
            "strategies": [],
            "best_return": None,
            "best_sharpe": None,
            "lowest_drawdown": None
        }
        
        best_return = float('-inf')
        best_sharpe = float('-inf')
        lowest_dd = float('inf')
        
        for result in results:
            if not result.success:
                continue
            
            summary = result.metrics.get_summary()
            
            strategy_data = {
                "name": result.config.strategy_name,
                "total_return_pct": result.total_return_pct,
                "sharpe_ratio": summary.get('sharpe_ratio', 0.0),
                "max_drawdown_pct": summary.get('max_drawdown_pct', 0.0),
                "win_rate": summary.get('win_rate', 0.0),
                "profit_factor": summary.get('profit_factor', 0.0),
                "num_trades": result.num_trades
            }
            
            comparison["strategies"].append(strategy_data)
            
            # Track best performers
            if result.total_return_pct > best_return:
                best_return = result.total_return_pct
                comparison["best_return"] = result.config.strategy_name
            
            sharpe = summary.get('sharpe_ratio', 0.0)
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                comparison["best_sharpe"] = result.config.strategy_name
            
            dd = summary.get('max_drawdown_pct', float('inf'))
            if dd < lowest_dd:
                lowest_dd = dd
                comparison["lowest_drawdown"] = result.config.strategy_name
        
        return comparison


# Example strategies for testing
def buy_and_hold_strategy(
    timestamp: datetime,
    market_snapshots: Dict[str, MarketSnapshot],
    executor: ExecutionSimulator
) -> List[Dict]:
    """
    Simple buy and hold strategy - buys YES on first timestep.
    """
    # Only execute on first call (when we have no positions)
    if len(executor.positions) > 0:
        return []
    
    actions = []
    
    # Buy YES on all markets with 10% of capital each
    capital_per_market = executor.capital * 0.1
    
    for market_id, snapshot in market_snapshots.items():
        if snapshot.yes_price < 0.8:  # Only if not too expensive
            actions.append({
                'market_id': market_id,
                'side': 'YES',
                'size': capital_per_market
            })
    
    return actions


def simple_threshold_strategy(
    timestamp: datetime,
    market_snapshots: Dict[str, MarketSnapshot],
    executor: ExecutionSimulator
) -> List[Dict]:
    """
    Simple strategy: buy YES when price < 0.3, buy NO when price > 0.7
    """
    actions = []
    
    position_size = 50.0  # Fixed position size
    
    for market_id, snapshot in market_snapshots.items():
        # Check if we already have a position
        if market_id in executor.positions:
            continue
        
        # Buy YES if underpriced
        if snapshot.yes_price < 0.3:
            actions.append({
                'market_id': market_id,
                'side': 'YES',
                'size': position_size
            })
        # Buy NO if overpriced
        elif snapshot.yes_price > 0.7:
            actions.append({
                'market_id': market_id,
                'side': 'NO',
                'size': position_size
            })
    
    return actions


if __name__ == "__main__":
    # Example usage
    print("Backtest Engine Example\n" + "=" * 50)
    
    from .market import Market
    
    # Create market simulator with synthetic data
    market_sim = MarketSimulator()
    
    market = Market(
        market_id="test_market",
        market_name="Test Market",
        initial_yes_price=0.50,
        volatility=0.05,
        drift=0.0
    )
    
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 30, tzinfo=timezone.utc)
    
    market_sim.generate_synthetic_data(market, start, end, interval_hours=1)
    
    # Create backtest engine
    engine = BacktestEngine(market_simulator=market_sim)
    
    # Run backtest with buy and hold strategy
    config = BacktestConfig(
        strategy_name="buy_and_hold",
        start_date=start,
        end_date=end,
        initial_capital=1000.0,
        interval_hours=1
    )
    
    result = engine.run_backtest(config, buy_and_hold_strategy)
    
    print(f"Strategy: {result.config.strategy_name}")
    print(f"Success: {result.success}")
    print(f"Final Value: ${result.final_portfolio_value:.2f}")
    print(f"Total Return: {result.total_return_pct:.2f}%")
    print(f"Number of Trades: {result.num_trades}")
    
    # Save results
    output_file = engine.save_results(result)
    print(f"\nResults saved to: {output_file}")
