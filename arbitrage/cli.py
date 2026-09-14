#!/usr/bin/env python3
"""
Arbitrage Detection CLI
=======================

Command-line interface for scanning and reporting arbitrage opportunities.

Usage:
    python -m arbitrage.cli scan          # Scan all platforms
    python -m arbitrage.cli scan --pm     # Prediction markets only
    python -m arbitrage.cli scan --crypto # Crypto only
    python -m arbitrage.cli report        # Show latest opportunities
    python -m arbitrage.cli watch         # Continuous monitoring
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from arbitrage.opportunity_detector import ArbitrageDetector
from arbitrage.types import ArbitrageOpportunity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('arbitrage.cli')


def get_default_paths() -> dict:
    """Get default paths relative to repo root"""
    repo_root = Path(__file__).parent.parent

    return {
        'polymarket_cache': repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json',
        'output_dir': repo_root / 'state' / 'arbitrage',
        'mappings': repo_root / 'state' / 'arbitrage' / 'market_mappings.json',
    }


def cmd_scan(args):
    """Scan for arbitrage opportunities"""
    paths = get_default_paths()

    # Ensure output directory exists
    paths['output_dir'].mkdir(parents=True, exist_ok=True)

    # Initialize detector
    detector = ArbitrageDetector(
        polymarket_cache=paths['polymarket_cache'] if paths['polymarket_cache'].exists() else None,
        manual_mappings=paths['mappings'] if paths['mappings'].exists() else None,
        min_profit_pct=args.min_profit / 100,  # Convert from percentage
    )

    print(f"\n🔍 Scanning for arbitrage opportunities...")
    print(f"   Minimum profit threshold: {args.min_profit}%\n")

    results = {'prediction_markets': [], 'crypto': [], 'scan_time': None}

    # Scan based on flags
    if args.pm or args.all:
        print("📊 Scanning prediction markets (Polymarket, Kalshi)...")
        try:
            pm_opps = detector.scan_prediction_markets()
            results['prediction_markets'] = pm_opps
            print(f"   Found {len(pm_opps)} opportunities\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")

    if args.crypto or args.all:
        print("₿ Scanning crypto exchanges...")
        try:
            crypto_opps = detector.scan_crypto()
            results['crypto'] = crypto_opps
            print(f"   Found {len(crypto_opps)} opportunities\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")

    results['scan_time'] = datetime.now(timezone.utc).isoformat()

    # Generate and print report
    print(detector.get_report(results))

    # Save results
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = paths['output_dir'] / 'opportunities.json'

    detector.save_opportunities(results, output_path)
    print(f"\n💾 Results saved to: {output_path}")

    # Return count for exit code
    total = len(results['prediction_markets']) + len(results['crypto'])
    return 0 if total > 0 else 1


def cmd_report(args):
    """Show latest opportunities from saved file"""
    paths = get_default_paths()

    if args.file:
        report_path = Path(args.file)
    else:
        report_path = paths['output_dir'] / 'opportunities.json'

    if not report_path.exists():
        print(f"❌ No report found at {report_path}")
        print("   Run 'python -m arbitrage.cli scan' first")
        return 1

    with open(report_path, 'r') as f:
        data = json.load(f)

    print(f"\n📋 Arbitrage Report")
    print(f"   Scan time: {data.get('scan_time', 'unknown')}")
    print("=" * 60)

    # Prediction markets
    pm_opps = data.get('prediction_markets', [])
    print(f"\n📊 PREDICTION MARKETS ({len(pm_opps)} opportunities)")
    print("-" * 40)

    if not pm_opps:
        print("No opportunities found.")
    else:
        for opp in pm_opps[:args.limit]:
            profit = opp.get('profit_pct_net', 0)
            print(f"\n[{profit:+.2%} NET] {opp.get('arb_type', 'unknown')}")

            event = opp.get('matched_event', {})
            if event:
                question = event.get('canonical_question', '')[:70]
                print(f"  Event: {question}...")

            for leg in opp.get('legs', []):
                print(f"  → {leg.get('side', '?')} on {leg.get('platform', '?')} @ ${leg.get('price', 0):.2f}")

            print(f"  Risk: {opp.get('execution_risk', '?')} | Max: ${opp.get('max_size_usd', 0):.0f}")

    # Crypto
    crypto_opps = data.get('crypto', [])
    print(f"\n₿ CRYPTO ({len(crypto_opps)} opportunities)")
    print("-" * 40)

    if not crypto_opps:
        print("No opportunities found.")
    else:
        for opp in crypto_opps[:args.limit]:
            profit = opp.get('profit_pct_net', 0)
            print(f"\n[{profit:+.2%} NET] {opp.get('arb_type', 'unknown')}")

            for leg in opp.get('legs', []):
                action = leg.get('action', '?')
                pair = leg.get('pair', '?')
                platform = leg.get('platform', '?')
                price = leg.get('price', 0)
                print(f"  → {action} {pair} on {platform} @ ${price:.2f}")

            print(f"  Risk: {opp.get('execution_risk', '?')} | Max: ${opp.get('max_size_usd', 0):.0f}")

    print("\n" + "=" * 60)
    return 0


def cmd_watch(args):
    """Continuous monitoring mode"""
    print(f"\n👁️  Starting continuous arbitrage monitoring...")
    print(f"   Scan interval: {args.interval} seconds")
    print(f"   Minimum profit: {args.min_profit}%")
    print(f"   Press Ctrl+C to stop\n")

    paths = get_default_paths()
    paths['output_dir'].mkdir(parents=True, exist_ok=True)

    detector = ArbitrageDetector(
        polymarket_cache=paths['polymarket_cache'] if paths['polymarket_cache'].exists() else None,
        manual_mappings=paths['mappings'] if paths['mappings'].exists() else None,
        min_profit_pct=args.min_profit / 100,
    )

    scan_count = 0

    try:
        while True:
            scan_count += 1
            print(f"\n[Scan #{scan_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            results = detector.scan_all()

            pm_count = len(results.get('prediction_markets', []))
            crypto_count = len(results.get('crypto', []))

            print(f"   📊 Prediction Markets: {pm_count} opportunities")
            print(f"   ₿  Crypto: {crypto_count} opportunities")

            # Show top opportunity if any
            all_opps = results.get('prediction_markets', []) + results.get('crypto', [])
            if all_opps:
                best = max(all_opps, key=lambda x: x.profit_pct_net)
                print(f"   🏆 Best: {best.profit_pct_net:+.2%} net profit")

            # Save results
            output_path = paths['output_dir'] / 'opportunities.json'
            detector.save_opportunities(results, output_path)

            # Wait for next scan
            print(f"   Next scan in {args.interval}s...")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped.")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Arbitrage Detection CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m arbitrage.cli scan              # Scan all platforms
    python -m arbitrage.cli scan --pm         # Prediction markets only
    python -m arbitrage.cli scan --crypto     # Crypto only
    python -m arbitrage.cli scan --min 1.0    # Min 1% profit
    python -m arbitrage.cli report            # Show latest results
    python -m arbitrage.cli watch             # Continuous monitoring
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan for arbitrage opportunities')
    scan_parser.add_argument('--pm', action='store_true', help='Scan prediction markets only')
    scan_parser.add_argument('--crypto', action='store_true', help='Scan crypto only')
    scan_parser.add_argument('--all', action='store_true', default=True, help='Scan all (default)')
    scan_parser.add_argument('--min-profit', type=float, default=0.5, help='Minimum profit %% (default: 0.5)')
    scan_parser.add_argument('--output', '-o', help='Output file path')

    # Report command
    report_parser = subparsers.add_parser('report', help='Show latest opportunities')
    report_parser.add_argument('--file', '-f', help='Report file to read')
    report_parser.add_argument('--limit', '-n', type=int, default=10, help='Max opportunities to show')

    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Continuous monitoring')
    watch_parser.add_argument('--interval', '-i', type=int, default=300, help='Scan interval in seconds (default: 300)')
    watch_parser.add_argument('--min-profit', type=float, default=0.5, help='Minimum profit %% (default: 0.5)')

    args = parser.parse_args()

    if args.command == 'scan':
        # If neither --pm nor --crypto specified, scan both
        if not args.pm and not args.crypto:
            args.all = True
        return cmd_scan(args)
    elif args.command == 'report':
        return cmd_report(args)
    elif args.command == 'watch':
        return cmd_watch(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
