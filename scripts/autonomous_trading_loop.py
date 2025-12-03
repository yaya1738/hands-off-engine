#!/usr/bin/env python3
"""
AUTONOMOUS TRADING LOOP - Self-Circulating Trading System
==========================================================
This script runs as a cron job or daemon to:
1. Fetch fresh market data
2. Generate alpha signals
3. Run through the Decider
4. Execute trades via Unified Trading Hub

The system drives itself - no manual intervention needed.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

# Setup paths
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [AUTONOMOUS] %(message)s'
)
LOG = logging.getLogger(__name__)

# State files
STATE_DIR = REPO_ROOT / "state"
LAST_RUN_FILE = STATE_DIR / "autonomous_last_run.json"


def get_current_balance() -> float:
    """Get current wallet balance"""
    try:
        from executor.trading_safeguards import TradingSafeguards
        import re
        safeguards = TradingSafeguards()
        ok, msg = safeguards.check_wallet_balance(0)
        match = re.search(r'\$(\d+\.?\d*)', msg)
        return float(match.group(1)) if match else 0
    except Exception as e:
        LOG.error(f"Balance check failed: {e}")
        return 0


def fetch_fresh_markets() -> list:
    """Fetch fresh market data from Polymarket"""
    try:
        from executor.polymarket_api import PolymarketAPI
        api = PolymarketAPI()
        markets = api.get_active_markets(limit=50)
        LOG.info(f"Fetched {len(markets)} markets")
        return markets
    except Exception as e:
        LOG.error(f"Market fetch failed: {e}")
        return []


def generate_signals(markets: list, bankroll: float) -> list:
    """Generate trading signals from markets"""
    signals = []

    for market in markets:
        try:
            # Simple edge detection based on volume/liquidity
            volume = market.get('volume', 0)
            liquidity = market.get('liquidity', 0)
            price = market.get('best_bid', 0.5) or market.get('outcomePrices', [0.5, 0.5])[0]

            # Skip low liquidity markets
            if liquidity < 1000:
                continue

            # Look for mispriced markets (simplified)
            # If price is extreme (< 0.1 or > 0.9) and high volume, might be edge
            if price and (price < 0.15 or price > 0.85):
                edge = 0.02  # Assume 2% edge on extreme prices
                side = "NO" if price > 0.5 else "YES"

                signals.append({
                    'market_id': market.get('slug') or market.get('market_id'),
                    'market_name': market.get('question', 'Unknown'),
                    'side': side,
                    'edge': edge,
                    'current_odds': price,
                    'model_confidence': 0.6
                })

        except Exception as e:
            continue

    LOG.info(f"Generated {len(signals)} signals")
    return signals


def run_decider(signals: list, bankroll: float) -> list:
    """Run signals through Decider to get planned actions"""
    try:
        from decider.ho_decider import Decider, PlannedAction
        decider = Decider(bankroll=bankroll)
        actions = decider.plan_actions(signals)
        LOG.info(f"Decider produced {len(actions)} actions")
        return actions
    except Exception as e:
        LOG.error(f"Decider failed: {e}")
        return []


def execute_via_unified_hub(actions: list) -> dict:
    """Execute actions through Unified Trading Hub"""
    try:
        from trading.unified_trading_hub import get_trading_hub, TradeRequest

        hub = get_trading_hub()
        status = hub.get_status()
        LOG.info(f"Hub status: balance=${status['balance']:.2f}, max_trades={status['max_trades']}")

        results = {
            'total': len(actions),
            'executed': 0,
            'success': 0,
            'failed': 0,
            'trades': []
        }

        for action in actions:
            request = TradeRequest(
                market_slug=action.market_id,
                side=action.side,
                amount_usd=action.amount,
                confidence=action.confidence,
                reason=action.reasoning,
                source="autonomous_loop"
            )

            result = hub.execute_trade(request)
            results['executed'] += 1

            if result.success:
                results['success'] += 1
            else:
                results['failed'] += 1

            results['trades'].append({
                'market': action.market_id,
                'side': action.side,
                'amount': action.amount,
                'success': result.success,
                'message': result.message
            })

            # Stop if trade failed due to balance
            if 'INSUFFICIENT_BALANCE' in result.message:
                LOG.warning("Stopping: Insufficient balance")
                break

        return results

    except Exception as e:
        LOG.error(f"Execution failed: {e}")
        return {'total': len(actions), 'executed': 0, 'error': str(e)}


def save_run_state(results: dict):
    """Save run state for next iteration"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    state = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'results': results
    }

    with open(LAST_RUN_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def autonomous_cycle():
    """Run one autonomous trading cycle"""
    LOG.info("=" * 60)
    LOG.info("AUTONOMOUS TRADING CYCLE START")
    LOG.info("=" * 60)

    # Step 1: Check balance
    balance = get_current_balance()
    LOG.info(f"Step 1: Balance = ${balance:.2f}")

    if balance < 1.0:
        LOG.warning("Balance too low for trading")
        save_run_state({'skipped': 'low_balance', 'balance': balance})
        return

    # Step 2: Fetch markets
    LOG.info("Step 2: Fetching markets...")
    markets = fetch_fresh_markets()

    if not markets:
        LOG.warning("No markets fetched")
        save_run_state({'skipped': 'no_markets'})
        return

    # Step 3: Generate signals
    LOG.info("Step 3: Generating signals...")
    signals = generate_signals(markets, balance)

    if not signals:
        LOG.info("No signals generated")
        save_run_state({'skipped': 'no_signals', 'markets': len(markets)})
        return

    # Step 4: Run Decider
    LOG.info("Step 4: Running Decider...")
    actions = run_decider(signals, balance)

    if not actions:
        LOG.info("No actions from Decider")
        save_run_state({'skipped': 'no_actions', 'signals': len(signals)})
        return

    # Step 5: Execute via Unified Hub
    LOG.info(f"Step 5: Executing {len(actions)} actions...")
    results = execute_via_unified_hub(actions)

    LOG.info(f"Results: {results['success']}/{results['executed']} trades succeeded")
    save_run_state(results)

    LOG.info("=" * 60)
    LOG.info("AUTONOMOUS TRADING CYCLE COMPLETE")
    LOG.info("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous Trading Loop")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds (daemon mode)")

    args = parser.parse_args()

    if args.once:
        autonomous_cycle()
    elif args.daemon:
        import time
        LOG.info(f"Starting daemon mode, interval={args.interval}s")
        while True:
            try:
                autonomous_cycle()
            except Exception as e:
                LOG.error(f"Cycle error: {e}")
            time.sleep(args.interval)
    else:
        autonomous_cycle()
