#!/usr/bin/env python3
"""
Script to download or generate historical market data for backtesting.

Usage:
    # Generate synthetic data for testing
    python scripts/download_historical_data.py --synthetic --days 30
    
    # In future: Download actual Polymarket data
    python scripts/download_historical_data.py --source polymarket --market-ids btc_100k,eth_5k
"""

import sys
import os
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulator.market import MarketSimulator, Market


def generate_synthetic_data(args):
    """Generate synthetic market data for testing"""
    print("Generating synthetic market data...")
    print(f"  Days: {args.days}")
    print(f"  Interval: {args.interval_hours} hour(s)")
    print()
    
    market_sim = MarketSimulator()
    
    # Define test markets
    markets = [
        Market(
            market_id="btc_100k_eoy",
            market_name="Will BTC reach $100k by end of year?",
            initial_yes_price=0.40,
            volatility=0.05,
            drift=0.01
        ),
        Market(
            market_id="eth_5k_eoy",
            market_name="Will ETH reach $5k by end of year?",
            initial_yes_price=0.35,
            volatility=0.06,
            drift=0.005
        ),
        Market(
            market_id="trump_wins_2024",
            market_name="Will Trump win 2024 election?",
            initial_yes_price=0.55,
            volatility=0.03,
            drift=-0.002
        ),
        Market(
            market_id="ai_breakthrough",
            market_name="Major AI breakthrough in 2024?",
            initial_yes_price=0.60,
            volatility=0.04,
            drift=0.0
        ),
    ]
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=args.days)
    
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print()
    
    # Generate data for each market
    for market in markets:
        print(f"Generating: {market.market_name}")
        snapshots = market_sim.generate_synthetic_data(
            market,
            start_date,
            end_date,
            interval_hours=args.interval_hours
        )
        
        # Save to file
        market_sim.save_synthetic_data(market.market_id)
        print(f"  ✓ Generated {len(snapshots)} snapshots")
        print(f"  ✓ Saved to: data/historical/{market.market_id}.json")
        print()
    
    print(f"✅ Generated data for {len(markets)} markets")


def download_polymarket_data(args):
    """Download actual Polymarket historical data (future implementation)"""
    print("⚠️  Polymarket data download not yet implemented")
    print()
    print("To implement:")
    print("1. Use Polymarket API to fetch historical price data")
    print("2. Transform to MarketSnapshot format")
    print("3. Save to data/historical/")
    print()
    print("For now, use --synthetic flag to generate test data")
    return False


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Download or generate historical market data'
    )
    
    parser.add_argument(
        '--synthetic',
        action='store_true',
        help='Generate synthetic data for testing'
    )
    
    parser.add_argument(
        '--source',
        type=str,
        choices=['polymarket'],
        help='Data source (future: polymarket, etc.)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days of data to generate (default: 30)'
    )
    
    parser.add_argument(
        '--interval-hours',
        type=int,
        default=1,
        help='Hours between data points (default: 1)'
    )
    
    parser.add_argument(
        '--market-ids',
        type=str,
        help='Comma-separated list of market IDs (for real data sources)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    
    # Ensure data directory exists
    data_dir = Path("data/historical")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("Historical Data Download/Generation Tool")
    print("=" * 70)
    print()
    
    if args.synthetic:
        generate_synthetic_data(args)
        return 0
    elif args.source == 'polymarket':
        success = download_polymarket_data(args)
        return 0 if success else 1
    else:
        print("Error: Must specify --synthetic or --source")
        print()
        print("Examples:")
        print("  # Generate 30 days of synthetic data")
        print("  python scripts/download_historical_data.py --synthetic --days 30")
        print()
        print("  # Future: Download from Polymarket")
        print("  python scripts/download_historical_data.py --source polymarket")
        return 1


if __name__ == "__main__":
    sys.exit(main())
