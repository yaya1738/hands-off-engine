"""
Command-line interface for running backtests.

Usage:
    python -m simulator.backtest --start 2024-01-01 --end 2024-12-31 --strategy alpha_v1
"""

import sys
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import simulator components - these need to be imported after path is set
from simulator.market import MarketSimulator, Market
from simulator.backtest import BacktestEngine, BacktestConfig, buy_and_hold_strategy, simple_threshold_strategy
from simulator.reports import ReportGenerator


# Strategy registry
STRATEGIES = {
    'buy_and_hold': buy_and_hold_strategy,
    'threshold': simple_threshold_strategy,
}


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Run backtests for Hands-Off Engine strategies'
    )
    
    parser.add_argument(
        '--start',
        type=str,
        required=True,
        help='Start date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end',
        type=str,
        required=True,
        help='End date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        required=True,
        choices=list(STRATEGIES.keys()),
        help='Strategy to test'
    )
    
    parser.add_argument(
        '--capital',
        type=float,
        default=1000.0,
        help='Initial capital (default: 1000.0)'
    )
    
    parser.add_argument(
        '--fee-rate',
        type=float,
        default=0.02,
        help='Fee rate as decimal (default: 0.02 for 2%%)'
    )
    
    parser.add_argument(
        '--slippage-rate',
        type=float,
        default=0.005,
        help='Slippage rate (default: 0.005)'
    )
    
    parser.add_argument(
        '--interval-hours',
        type=int,
        default=1,
        help='Hours between simulation steps (default: 1)'
    )
    
    parser.add_argument(
        '--synthetic',
        action='store_true',
        help='Generate synthetic market data for testing'
    )
    
    parser.add_argument(
        '--report-format',
        type=str,
        choices=['markdown', 'html', 'both'],
        default='both',
        help='Report format (default: both)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for results (default: data/simulations)'
    )
    
    return parser.parse_args()


def generate_synthetic_markets(
    market_sim: MarketSimulator,
    start_date: datetime,
    end_date: datetime,
    interval_hours: int
):
    """Generate synthetic market data for testing"""
    print("Generating synthetic market data...")
    
    # Create a few test markets with different characteristics
    markets = [
        Market(
            market_id="test_market_1",
            market_name="Bullish Market (upward drift)",
            initial_yes_price=0.30,
            volatility=0.03,
            drift=0.01  # Positive drift
        ),
        Market(
            market_id="test_market_2",
            market_name="Bearish Market (downward drift)",
            initial_yes_price=0.70,
            volatility=0.03,
            drift=-0.01  # Negative drift
        ),
        Market(
            market_id="test_market_3",
            market_name="Volatile Market",
            initial_yes_price=0.50,
            volatility=0.08,
            drift=0.0
        ),
        Market(
            market_id="test_market_4",
            market_name="Stable Market",
            initial_yes_price=0.50,
            volatility=0.01,
            drift=0.0
        ),
    ]
    
    for market in markets:
        snapshots = market_sim.generate_synthetic_data(
            market,
            start_date,
            end_date,
            interval_hours
        )
        print(f"  Generated {len(snapshots)} snapshots for {market.market_name}")
    
    print()


def main():
    """Main entry point"""
    args = parse_args()
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(args.end, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        print("Please use YYYY-MM-DD format")
        return 1
    
    if end_date <= start_date:
        print("Error: End date must be after start date")
        return 1
    
    # Set up directories
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path("data/simulations")
    
    print("=" * 70)
    print(f"Backtest Configuration")
    print("=" * 70)
    print(f"Strategy: {args.strategy}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print(f"Fee Rate: {args.fee_rate * 100:.2f}%")
    print(f"Slippage Rate: {args.slippage_rate * 100:.3f}%")
    print(f"Interval: {args.interval_hours} hour(s)")
    print(f"Output Directory: {output_dir}")
    print()
    
    # Create market simulator
    market_sim = MarketSimulator()
    
    # Generate or load market data
    if args.synthetic:
        generate_synthetic_markets(
            market_sim,
            start_date,
            end_date,
            args.interval_hours
        )
    else:
        print("Loading historical market data...")
        # In a real scenario, you would load actual historical data here
        print("Warning: No historical data available, generating synthetic data instead")
        generate_synthetic_markets(
            market_sim,
            start_date,
            end_date,
            args.interval_hours
        )
    
    # Create backtest configuration
    config = BacktestConfig(
        strategy_name=args.strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=args.capital,
        fee_rate=args.fee_rate,
        slippage_rate=args.slippage_rate,
        interval_hours=args.interval_hours
    )
    
    # Get strategy function
    strategy_func = STRATEGIES[args.strategy]
    
    # Run backtest
    print("Running backtest...")
    engine = BacktestEngine(market_simulator=market_sim, output_dir=output_dir)
    result = engine.run_backtest(config, strategy_func)
    
    # Display results
    print()
    print("=" * 70)
    print("Backtest Results")
    print("=" * 70)
    
    if result.success:
        print(f"✅ Backtest completed successfully")
        print()
        print(f"Final Portfolio Value: ${result.final_portfolio_value:,.2f}")
        print(f"Total Return: {result.total_return_pct:+.2f}%")
        print(f"Number of Trades: {result.num_trades}")
        
        summary = result.metrics.get_summary()
        print()
        print("Performance Metrics:")
        print(f"  Sharpe Ratio: {summary.get('sharpe_ratio', 0):.3f}")
        print(f"  Max Drawdown: {summary.get('max_drawdown_pct', 0):.2f}%")
        print(f"  Win Rate: {summary.get('win_rate', 0):.2f}%")
        print(f"  Profit Factor: {summary.get('profit_factor', 0):.2f}")
    else:
        print(f"❌ Backtest failed: {result.error_message}")
        return 1
    
    # Save results
    print()
    print("Saving results...")
    results_file = engine.save_results(result)
    print(f"  JSON results: {results_file}")
    
    # Generate reports
    report_gen = ReportGenerator(output_dir=output_dir / "reports")
    
    if args.report_format in ['markdown', 'both']:
        md_report = report_gen.generate_markdown_report(result)
        print(f"  Markdown report: {md_report}")
    
    if args.report_format in ['html', 'both']:
        html_report = report_gen.generate_html_report(result)
        print(f"  HTML report: {html_report}")
    
    print()
    print("=" * 70)
    print("Backtest complete!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
