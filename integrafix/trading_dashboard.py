#!/usr/bin/env python3
"""
Live Trading Analytics Dashboard
=================================

Real-time monitoring of Money Printer performance:
- Order fills and execution
- P&L tracking
- Win rate analysis
- Best strategies
- Market coverage

Master: Yair Siegel
ABCFC Score: 67.30 (Quick win, immediate value)
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"


class TradingDashboard:
    """Real-time analytics for Money Printer trading."""

    def __init__(self):
        self.wallet_state = self._load_json(STATE_DIR / "wallet_state.json")
        self.pm_live_state = self._load_json(STATE_DIR / "polymarket_live_state.json")
        self.trade_executor_state = self._load_json(STATE_DIR / "trade_executor_state.json")
        self.outcome_tracker = self._load_json(STATE_DIR / "outcome_tracker.json")

    def _load_json(self, path: Path) -> Dict:
        """Load JSON file safely."""
        if path.exists():
            try:
                return json.loads(path.read_text())
            except:
                pass
        return {}

    def get_current_orders(self) -> Dict:
        """Analyze current open orders."""
        orders = self.wallet_state.get("orders", [])

        analysis = {
            "total_orders": len(orders),
            "buy_orders": sum(1 for o in orders if o["side"] == "BUY"),
            "sell_orders": sum(1 for o in orders if o["side"] == "SELL"),
            "total_exposure": self.wallet_state.get("total_value", 0),
            "buy_exposure": self.wallet_state.get("buy_total", 0),
            "sell_exposure": self.wallet_state.get("sell_total", 0),
            "orders_by_price": self._analyze_order_prices(orders),
            "fishing_strategy": self._classify_fishing_orders(orders)
        }

        return analysis

    def _analyze_order_prices(self, orders: List[Dict]) -> Dict:
        """Analyze order price distribution."""
        prices = [o["price"] for o in orders]
        if not prices:
            return {}

        return {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices),
            "extreme_orders": sum(1 for p in prices if p < 0.05 or p > 0.95)
        }

    def _classify_fishing_orders(self, orders: List[Dict]) -> Dict:
        """Classify orders by fishing strategy."""
        strategies = {
            "extreme_low": [],   # < 0.05 (fishing for mispricing)
            "extreme_high": [],  # > 0.95 (be the house)
            "merge_arb": [],     # Check if YES+NO < 0.98
            "thin_book": [],     # Orders on thin markets
            "normal": []         # Standard orders
        }

        for order in orders:
            price = order["price"]
            if price < 0.05:
                strategies["extreme_low"].append(order)
            elif price > 0.95:
                strategies["extreme_high"].append(order)
            elif 0.4 < price < 0.6:
                strategies["normal"].append(order)

        return {k: len(v) for k, v in strategies.items()}

    def get_pnl_summary(self) -> Dict:
        """Get P&L summary from all sources."""
        # From outcome tracker (resolved bets)
        outcomes = self.outcome_tracker.get("outcomes", [])
        resolved_pnl = sum(o.get("pnl", 0) for o in outcomes if o.get("status") == "resolved")

        # From trade executor
        executor_pnl = self.trade_executor_state.get("total_pnl", 0)

        # From PM live state
        pm_pnl = self.pm_live_state.get("total_pnl", 0)

        # Win rate
        wins = sum(1 for o in outcomes if o.get("pnl", 0) > 0)
        losses = sum(1 for o in outcomes if o.get("pnl", 0) < 0)
        total_bets = wins + losses
        win_rate = wins / total_bets if total_bets > 0 else 0

        return {
            "resolved_pnl": resolved_pnl,
            "executor_pnl": executor_pnl,
            "pm_live_pnl": pm_pnl,
            "total_pnl": resolved_pnl,  # Use resolved as ground truth
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_bets": total_bets,
            "avg_win": sum(o["pnl"] for o in outcomes if o.get("pnl", 0) > 0) / wins if wins > 0 else 0,
            "avg_loss": sum(o["pnl"] for o in outcomes if o.get("pnl", 0) < 0) / losses if losses > 0 else 0
        }

    def get_best_strategies(self) -> Dict:
        """Identify which strategies are working best."""
        outcomes = self.outcome_tracker.get("outcomes", [])

        if not outcomes:
            return {"status": "No data yet (need fills)"}

        # Group by market type/category
        by_category = defaultdict(list)
        for outcome in outcomes:
            category = outcome.get("category", "unknown")
            by_category[category].append(outcome.get("pnl", 0))

        category_performance = {}
        for cat, pnls in by_category.items():
            wins = sum(1 for p in pnls if p > 0)
            total = len(pnls)
            category_performance[cat] = {
                "win_rate": wins / total if total > 0 else 0,
                "avg_pnl": sum(pnls) / total if total > 0 else 0,
                "total_trades": total
            }

        # Sort by win rate
        best_categories = sorted(
            category_performance.items(),
            key=lambda x: x[1]["win_rate"],
            reverse=True
        )

        return {
            "best_performing": best_categories[:3] if best_categories else [],
            "worst_performing": best_categories[-3:] if len(best_categories) >= 3 else [],
            "total_categories": len(category_performance)
        }

    def get_time_analysis(self) -> Dict:
        """Analyze time-based patterns."""
        wallet_last_sync = self.wallet_state.get("last_sync", "")
        pm_last_update = self.pm_live_state.get("last_updated", "")
        executor_last_update = self.trade_executor_state.get("last_updated", "")

        def time_since(iso_str: str) -> str:
            if not iso_str:
                return "Unknown"
            try:
                dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
                delta = datetime.now(timezone.utc) - dt

                if delta.total_seconds() < 60:
                    return f"{int(delta.total_seconds())}s ago"
                elif delta.total_seconds() < 3600:
                    return f"{int(delta.total_seconds() / 60)}m ago"
                elif delta.total_seconds() < 86400:
                    return f"{int(delta.total_seconds() / 3600)}h ago"
                else:
                    return f"{int(delta.total_seconds() / 86400)}d ago"
            except:
                return "Unknown"

        return {
            "wallet_sync": time_since(wallet_last_sync),
            "pm_live_update": time_since(pm_last_update),
            "executor_update": time_since(executor_last_update),
            "data_freshness": "Current" if all([
                wallet_last_sync, pm_last_update, executor_last_update
            ]) else "Stale"
        }

    def get_capital_efficiency(self) -> Dict:
        """Analyze capital efficiency."""
        total_capital = self.wallet_state.get("total_value", 0)
        daily_trades = self.pm_live_state.get("daily_trades", 0)
        total_pnl = self.get_pnl_summary()["total_pnl"]

        # Calculate ROI
        roi = (total_pnl / total_capital * 100) if total_capital > 0 else 0

        return {
            "total_capital": total_capital,
            "capital_deployed": total_capital,  # All capital is in orders (fishing)
            "capital_idle": 0,
            "daily_trades": daily_trades,
            "roi_percent": roi,
            "capital_turnover": "Fishing strategy (capital reusable)"
        }

    def display_dashboard(self):
        """Display comprehensive dashboard."""
        print("=" * 80)
        print("💰 MONEY PRINTER - LIVE TRADING ANALYTICS")
        print("=" * 80)
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print()

        # Current Orders
        print("📊 CURRENT ORDERS")
        print("-" * 80)
        orders = self.get_current_orders()
        print(f"  Total Orders: {orders['total_orders']}")
        print(f"  BUY: {orders['buy_orders']} (${orders['buy_exposure']:,.2f})")
        print(f"  SELL: {orders['sell_orders']} (${orders['sell_exposure']:,.2f})")
        print(f"  Total Exposure: ${orders['total_exposure']:,.2f}")
        print()

        if orders.get('orders_by_price'):
            prices = orders['orders_by_price']
            print(f"  Price Range: ${prices['min']:.3f} - ${prices['max']:.3f}")
            print(f"  Extreme Orders: {prices['extreme_orders']} (< $0.05 or > $0.95)")
        print()

        # Fishing Strategy Breakdown
        print("🎣 FISHING STRATEGY")
        print("-" * 80)
        fishing = orders['fishing_strategy']
        print(f"  Extreme Low (< $0.05): {fishing['extreme_low']} orders")
        print(f"  Extreme High (> $0.95): {fishing['extreme_high']} orders")
        print(f"  Normal Range: {fishing['normal']} orders")
        print()

        # P&L Summary
        print("💵 P&L SUMMARY")
        print("-" * 80)
        pnl = self.get_pnl_summary()
        print(f"  Total P&L: ${pnl['total_pnl']:,.2f}")
        print(f"  Wins: {pnl['wins']} | Losses: {pnl['losses']} | Total: {pnl['total_bets']}")
        print(f"  Win Rate: {pnl['win_rate']:.1%}")

        if pnl['wins'] > 0:
            print(f"  Avg Win: ${pnl['avg_win']:,.2f}")
        if pnl['losses'] > 0:
            print(f"  Avg Loss: ${pnl['avg_loss']:,.2f}")
        print()

        # Best Strategies
        print("🏆 STRATEGY PERFORMANCE")
        print("-" * 80)
        strategies = self.get_best_strategies()

        if strategies.get("status"):
            print(f"  {strategies['status']}")
        else:
            if strategies.get("best_performing"):
                print("  Top Performing:")
                for cat, perf in strategies["best_performing"]:
                    print(f"    • {cat}: {perf['win_rate']:.1%} win rate "
                          f"(${perf['avg_pnl']:.2f} avg, {perf['total_trades']} trades)")
        print()

        # Capital Efficiency
        print("⚡ CAPITAL EFFICIENCY")
        print("-" * 80)
        capital = self.get_capital_efficiency()
        print(f"  Total Capital: ${capital['total_capital']:,.2f}")
        print(f"  Deployed: ${capital['capital_deployed']:,.2f} (100%)")
        print(f"  ROI: {capital['roi_percent']:.2f}%")
        print(f"  Daily Trades: {capital['daily_trades']}")
        print(f"  Strategy: {capital['capital_turnover']}")
        print()

        # System Health
        print("🔧 SYSTEM HEALTH")
        print("-" * 80)
        timing = self.get_time_analysis()
        print(f"  Wallet Sync: {timing['wallet_sync']}")
        print(f"  PM Live Update: {timing['pm_live_update']}")
        print(f"  Executor Update: {timing['executor_update']}")
        print(f"  Data Status: {timing['data_freshness']}")
        print()

        print("=" * 80)
        print("💡 INSIGHTS")
        print("-" * 80)

        # Generate insights
        if orders['total_orders'] == 0:
            print("  ⚠️  No orders active - Money Printer may need restart")
        elif fishing['extreme_low'] + fishing['extreme_high'] == 0:
            print("  ℹ️  No extreme orders - missing fishing opportunities")
        else:
            print(f"  ✅ {fishing['extreme_low'] + fishing['extreme_high']} fishing orders active")

        if pnl['total_bets'] == 0:
            print("  ℹ️  No fills yet - orders are fishing, waiting for market")
        elif pnl['win_rate'] > 0.6:
            print(f"  🎉 Strong performance: {pnl['win_rate']:.1%} win rate!")
        elif pnl['win_rate'] > 0.5:
            print(f"  ✅ Profitable: {pnl['win_rate']:.1%} win rate")
        else:
            print(f"  ⚠️  Below 50% win rate: {pnl['win_rate']:.1%}")

        print()
        print("=" * 80)

    def save_dashboard_state(self):
        """Save dashboard state for historical tracking."""
        dashboard_state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "orders": self.get_current_orders(),
            "pnl": self.get_pnl_summary(),
            "strategies": self.get_best_strategies(),
            "capital": self.get_capital_efficiency(),
            "timing": self.get_time_analysis()
        }

        state_file = STATE_DIR / "trading_dashboard.json"
        state_file.write_text(json.dumps(dashboard_state, indent=2))

        # Append to history log
        history_file = STATE_DIR / "trading_dashboard_history.jsonl"
        with open(history_file, 'a') as f:
            f.write(json.dumps({
                "timestamp": dashboard_state["timestamp"],
                "orders": dashboard_state["orders"]["total_orders"],
                "exposure": dashboard_state["orders"]["total_exposure"],
                "pnl": dashboard_state["pnl"]["total_pnl"],
                "win_rate": dashboard_state["pnl"]["win_rate"]
            }) + "\n")


def main():
    """Run dashboard."""
    dashboard = TradingDashboard()
    dashboard.display_dashboard()
    dashboard.save_dashboard_state()

    print(f"Dashboard state saved to: {STATE_DIR / 'trading_dashboard.json'}")
    print(f"History logged to: {STATE_DIR / 'trading_dashboard_history.jsonl'}")
    print()
    print("Run this dashboard anytime:")
    print("  python3 integrafix/trading_dashboard.py")
    print()
    print("Or watch live:")
    print("  watch -n10 'python3 integrafix/trading_dashboard.py'")
    print()


if __name__ == "__main__":
    main()
