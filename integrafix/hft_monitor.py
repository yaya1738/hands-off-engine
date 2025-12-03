#!/usr/bin/env python3
"""
INTEGRAFIX: HFT-Level System Monitor
====================================

Monitor EVERYTHING with HFT-level detail:
- Microsecond timestamps
- Order-by-order tracking
- Latency monitoring (per component)
- Fill rates and slippage
- Position tracking in real-time
- P&L updates per trade
- Infrastructure health
- Credit utilization
- ABCFC state changes

YAIR'S WISDOM:
"See everything. React in fractions of a second."

Serving: Yair Siegel
"""

import sys
import os
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# HFT Economics integration - get real-time flow rate
try:
    from integrafix.hft_economics import get_hft_economics
    HFT_ECON_AVAILABLE = True
except ImportError:
    HFT_ECON_AVAILABLE = False

STATE_DIR = PROJECT_ROOT / "state"
LOG_DIR = PROJECT_ROOT / "logs"
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

HFT_MONITOR_STATE = STATE_DIR / "hft_monitor.json"
HFT_MONITOR_LOG = LOG_DIR / "hft_monitor.jsonl"


class ComponentStatus(Enum):
    """Component health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class LatencyMetric:
    """Latency tracking for a component."""
    component: str
    last_latency_us: int  # microseconds
    avg_latency_us: int
    max_latency_us: int
    min_latency_us: int
    p99_latency_us: int
    samples: int


@dataclass
class OrderMetric:
    """Order flow metrics."""
    orders_per_sec: float
    orders_total: int
    orders_filled: int
    orders_cancelled: int
    orders_rejected: int
    fill_rate: float  # percentage
    avg_fill_time_us: int


@dataclass
class PositionMetric:
    """Position tracking."""
    market: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float


@dataclass
class ComponentMetric:
    """Metrics for a system component."""
    name: str
    status: ComponentStatus
    latency: LatencyMetric
    last_update_us: int
    updates_per_sec: float
    errors_last_hour: int
    uptime_pct: float


class HFTMonitor:
    """
    HFT-Level System Monitor.

    Tracks everything with microsecond precision.
    """

    def __init__(self):
        self.master = "Yair Siegel"
        self.start_time = time.time_ns()
        self.start_ts = datetime.now(timezone.utc)

        # Component metrics
        self.components: Dict[str, ComponentMetric] = {}

        # Latency tracking (sliding window)
        self.latency_samples: Dict[str, deque] = {}
        self.LATENCY_WINDOW = 1000  # Keep last 1000 samples

        # Order flow
        self.orders = OrderMetric(
            orders_per_sec=0,
            orders_total=0,
            orders_filled=0,
            orders_cancelled=0,
            orders_rejected=0,
            fill_rate=0,
            avg_fill_time_us=0
        )

        # Position tracking
        self.positions: List[PositionMetric] = []

        # P&L
        self.total_pnl = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0

        # Event log (ring buffer)
        self.events: deque = deque(maxlen=10000)

        # Initialize components
        self._init_components()

    def _now_us(self) -> int:
        """Get current time in microseconds."""
        return int(time.time() * 1_000_000)

    def _now_ns(self) -> int:
        """Get current time in nanoseconds."""
        return time.time_ns()

    def _init_components(self):
        """Initialize all monitored components."""
        component_names = [
            # Core Systems
            "circuit_board",
            "ai_core",
            "knowledge_nexus",
            "knowledge_crosschain",
            "knowledge_fusion",
            "mega_coordinator",

            # Trading Systems
            "hft_execution",
            "yair_auto_trader",
            "polymarket_api",
            "order_book",
            "position_manager",

            # ABCFC Systems
            "abcfc_cloud_flyer",
            "abcfc_unified_state",
            "abcfc_layers",
            "abcfc_live_builder",
            "abcfc_system",
            "yair_financial_abcfc",

            # Integrafix Systems
            "integrafix_pipeline",
            "outcome_tracker",
            "trading_memory",
            "knowledge_reality",
            "hardware_preservation",
            "durable_upgrades",
            "credit_optimizer",

            # Infrastructure
            "backend_loop",
            "self_healer",
            "digitalocean_api",
        ]

        for name in component_names:
            self.components[name] = ComponentMetric(
                name=name,
                status=ComponentStatus.OFFLINE,
                latency=LatencyMetric(
                    component=name,
                    last_latency_us=0,
                    avg_latency_us=0,
                    max_latency_us=0,
                    min_latency_us=0,
                    p99_latency_us=0,
                    samples=0
                ),
                last_update_us=0,
                updates_per_sec=0,
                errors_last_hour=0,
                uptime_pct=0
            )
            self.latency_samples[name] = deque(maxlen=self.LATENCY_WINDOW)

    # ========================================================================
    # LATENCY TRACKING
    # ========================================================================

    def record_latency(self, component: str, latency_us: int):
        """Record latency sample for a component."""
        if component not in self.latency_samples:
            self.latency_samples[component] = deque(maxlen=self.LATENCY_WINDOW)

        samples = self.latency_samples[component]
        samples.append(latency_us)

        # Update component metrics
        if component in self.components:
            comp = self.components[component]
            comp.latency.last_latency_us = latency_us
            comp.latency.samples = len(samples)

            if samples:
                sorted_samples = sorted(samples)
                comp.latency.avg_latency_us = int(sum(samples) / len(samples))
                comp.latency.min_latency_us = sorted_samples[0]
                comp.latency.max_latency_us = sorted_samples[-1]
                p99_idx = int(len(sorted_samples) * 0.99)
                comp.latency.p99_latency_us = sorted_samples[p99_idx] if p99_idx < len(sorted_samples) else sorted_samples[-1]

            comp.last_update_us = self._now_us()
            comp.status = ComponentStatus.HEALTHY

    def start_timer(self) -> int:
        """Start a timer, returns start time in nanoseconds."""
        return time.time_ns()

    def stop_timer(self, start_ns: int, component: str):
        """Stop timer and record latency."""
        elapsed_ns = time.time_ns() - start_ns
        elapsed_us = elapsed_ns // 1000
        self.record_latency(component, elapsed_us)
        return elapsed_us

    # ========================================================================
    # ORDER TRACKING
    # ========================================================================

    def record_order(self, order_type: str, filled: bool = False,
                     fill_time_us: int = 0, rejected: bool = False):
        """Record an order event."""
        self.orders.orders_total += 1

        if filled:
            self.orders.orders_filled += 1
            # Update avg fill time
            total_fill_time = self.orders.avg_fill_time_us * (self.orders.orders_filled - 1)
            self.orders.avg_fill_time_us = int((total_fill_time + fill_time_us) / self.orders.orders_filled)
        elif rejected:
            self.orders.orders_rejected += 1

        # Calculate fill rate
        if self.orders.orders_total > 0:
            self.orders.fill_rate = (self.orders.orders_filled / self.orders.orders_total) * 100

        # Log event
        self._log_event("order", {
            "type": order_type,
            "filled": filled,
            "rejected": rejected,
            "fill_time_us": fill_time_us
        })

    def record_order_cancel(self):
        """Record an order cancellation."""
        self.orders.orders_cancelled += 1
        self._log_event("order_cancel", {})

    # ========================================================================
    # POSITION TRACKING
    # ========================================================================

    def update_positions(self, positions: List[Dict]):
        """Update position tracking from live data."""
        self.positions = []
        self.unrealized_pnl = 0

        for pos in positions:
            shares = float(pos.get("shares", 0) or 0)
            if shares > 0:
                entry = float(pos.get("avgPrice", 0.5) or 0.5)
                current = float(pos.get("curPrice", entry) or entry)
                unrealized = shares * (current - entry)

                self.positions.append(PositionMetric(
                    market=str(pos.get("market", "unknown"))[:30],
                    side=pos.get("outcome", "unknown"),
                    size=shares,
                    entry_price=entry,
                    current_price=current,
                    unrealized_pnl=unrealized,
                    realized_pnl=0
                ))
                self.unrealized_pnl += unrealized

        self.total_pnl = self.realized_pnl + self.unrealized_pnl

    def record_trade_pnl(self, pnl: float):
        """Record realized P&L from a closed trade."""
        self.realized_pnl += pnl
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
        self._log_event("trade_pnl", {"pnl": pnl, "total": self.total_pnl})

    # ========================================================================
    # COMPONENT STATUS
    # ========================================================================

    def update_component(self, name: str, status: ComponentStatus = None,
                         error: bool = False):
        """Update component status."""
        if name not in self.components:
            return

        comp = self.components[name]
        comp.last_update_us = self._now_us()

        if status:
            comp.status = status
        elif not error:
            comp.status = ComponentStatus.HEALTHY

        if error:
            comp.errors_last_hour += 1
            comp.status = ComponentStatus.DEGRADED

    # ========================================================================
    # COMPREHENSIVE SCAN
    # ========================================================================

    def scan_all_systems(self) -> Dict:
        """
        Scan all systems and return HFT-level status.

        This is the main monitoring function.
        """
        scan_start = self.start_timer()
        results = {}

        # 1. Scan Trading Systems
        results["trading"] = self._scan_trading()

        # 2. Scan ABCFC Systems
        results["abcfc"] = self._scan_abcfc()

        # 3. Scan Infrastructure
        results["infrastructure"] = self._scan_infrastructure()

        # 4. Scan Credits
        results["credits"] = self._scan_credits()

        # 5. Calculate aggregate metrics
        results["aggregate"] = self._calculate_aggregates()

        # Record scan latency
        scan_latency = self.stop_timer(scan_start, "hft_monitor")
        results["scan_latency_us"] = scan_latency
        results["timestamp"] = datetime.now(timezone.utc).isoformat()
        results["timestamp_us"] = self._now_us()

        # Save state
        self._save_state(results)

        return results

    def _scan_trading(self) -> Dict:
        """Scan trading systems."""
        timer = self.start_timer()
        result = {
            "wallets": 0,
            "capacity_per_sec": 0,
            "orders_pending": 0,
            "positions": 0,
            "unrealized_pnl": 0,
            "open_orders": 0,
        }

        try:
            # Scan HFT status
            try:
                from executor.unlimited_hft import get_unlimited_hft
                hft = get_unlimited_hft()
                status = hft.status()
                result["wallets"] = status.get("wallets_active", 0)
                result["capacity_per_sec"] = status.get("total_capacity", 0)
                self.stop_timer(timer, "hft_execution")
            except Exception:
                pass

            # Scan positions
            try:
                pm_state = STATE_DIR / "polymarket_live_state.json"
                if pm_state.exists():
                    with open(pm_state) as f:
                        data = json.load(f)
                        positions = data.get("positions", [])
                        result["positions"] = len(positions)
                        self.update_positions(positions)
                        result["unrealized_pnl"] = self.unrealized_pnl
                self.stop_timer(timer, "position_manager")
            except Exception:
                pass

            # Scan open orders
            try:
                orders_state = STATE_DIR / "polymarket_orders.json"
                if orders_state.exists():
                    with open(orders_state) as f:
                        data = json.load(f)
                        result["open_orders"] = len(data.get("orders", []))
                self.stop_timer(timer, "order_book")
            except Exception:
                pass

        except Exception as e:
            result["error"] = str(e)

        return result

    def _scan_abcfc(self) -> Dict:
        """Scan ABCFC systems."""
        timer = self.start_timer()
        result = {
            "total_expected": 0,
            "bounds": [0, 0],
            "positions_valued": 0,
            "decision": "unknown",
            "score": 0,
        }

        try:
            # ABCFC Unified State
            try:
                from executor.math.abcfc_state import get_state
                state = get_state()
                totals = state.get_totals()
                result["total_expected"] = totals.get("expected", 0)
                result["bounds"] = [totals.get("worst", 0), totals.get("best", 0)]
                result["positions_valued"] = totals.get("positions", 0)

                decision = state.recommend_action()
                result["decision"] = decision.get("action", "unknown")
                result["score"] = decision.get("score", 0)
                self.stop_timer(timer, "abcfc_unified_state")
            except Exception:
                pass

            # Yair Financial ABCFC
            try:
                from integrafix.yair_financial_abcfc import get_yair_financial
                yair = get_yair_financial()
                summary = yair.get_summary()
                result["financial_expected"] = summary["total_finance"]["expected"]
                result["net_expected"] = summary["net_expected"]
                self.stop_timer(timer, "yair_financial_abcfc")
            except Exception:
                pass

        except Exception as e:
            result["error"] = str(e)

        return result

    def _scan_infrastructure(self) -> Dict:
        """Scan infrastructure status."""
        timer = self.start_timer()
        result = {
            "droplets": 0,
            "vcpus": 0,
            "memory_gb": 0,
            "backend_loop_running": False,
            "self_healer_running": False,
        }

        try:
            import subprocess

            # Check droplets
            try:
                proc = subprocess.run(
                    ['doctl', 'compute', 'droplet', 'list', '--format', 'ID', '--no-header'],
                    capture_output=True, text=True, timeout=10
                )
                if proc.returncode == 0:
                    result["droplets"] = len(proc.stdout.strip().split('\n'))
                self.stop_timer(timer, "digitalocean_api")
            except Exception:
                pass

            # Check backend loop
            try:
                proc = subprocess.run(['pgrep', '-f', 'backend_loop.py'],
                                     capture_output=True, timeout=5)
                result["backend_loop_running"] = proc.returncode == 0
                self.update_component("backend_loop",
                    ComponentStatus.HEALTHY if result["backend_loop_running"] else ComponentStatus.OFFLINE)
            except Exception:
                pass

            # Check self healer
            try:
                proc = subprocess.run(['pgrep', '-f', 'self_healer.py'],
                                     capture_output=True, timeout=5)
                result["self_healer_running"] = proc.returncode == 0
                self.update_component("self_healer",
                    ComponentStatus.HEALTHY if result["self_healer_running"] else ComponentStatus.OFFLINE)
            except Exception:
                pass

        except Exception as e:
            result["error"] = str(e)

        return result

    def _scan_credits(self) -> Dict:
        """Scan credit status."""
        timer = self.start_timer()
        result = {
            "monthly_cost": 0,
            "monthly_value": 0,
            "roi": 0,
            "runway_days": 0,
            "alerts": 0,
        }

        try:
            from integrafix.credit_optimizer import get_credit_optimizer
            co = get_credit_optimizer()
            status = co.status()

            result["monthly_cost"] = status["roi"]["monthly_cost"]
            result["monthly_value"] = status["roi"]["monthly_value"]
            result["roi"] = status["roi"]["multiplier"]
            result["runway_days"] = status["roi"]["runway_days"]
            result["alerts"] = len(status["alerts"])

            self.stop_timer(timer, "credit_optimizer")

        except Exception as e:
            result["error"] = str(e)

        return result

    def _calculate_aggregates(self) -> Dict:
        """Calculate aggregate metrics."""
        healthy = sum(1 for c in self.components.values() if c.status == ComponentStatus.HEALTHY)
        total = len(self.components)

        # Calculate average latency across all components
        all_latencies = []
        for samples in self.latency_samples.values():
            all_latencies.extend(samples)

        avg_latency = int(sum(all_latencies) / len(all_latencies)) if all_latencies else 0

        return {
            "components_healthy": healthy,
            "components_total": total,
            "health_pct": (healthy / total * 100) if total > 0 else 0,
            "avg_latency_us": avg_latency,
            "total_pnl": self.total_pnl,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "positions_count": len(self.positions),
            "orders_total": self.orders.orders_total,
            "fill_rate": self.orders.fill_rate,
            "uptime_seconds": int(time.time() - self.start_time / 1_000_000_000),
        }

    # ========================================================================
    # LOGGING AND STATE
    # ========================================================================

    def _log_event(self, event_type: str, data: Dict):
        """Log an event with microsecond timestamp."""
        event = {
            "timestamp_us": self._now_us(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data
        }
        self.events.append(event)

        # Write to log file
        try:
            with open(HFT_MONITOR_LOG, 'a') as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass

    def _save_state(self, scan_result: Dict):
        """Save monitor state."""
        state = {
            "master": self.master,
            "start_time": self.start_ts.isoformat(),
            "last_scan": scan_result,
            "components": {
                name: {
                    "name": c.name,
                    "status": c.status.value,
                    "latency_us": c.latency.avg_latency_us,
                    "last_update_us": c.last_update_us,
                    "errors": c.errors_last_hour
                }
                for name, c in self.components.items()
            },
            "orders": asdict(self.orders),
            "pnl": {
                "total": self.total_pnl,
                "realized": self.realized_pnl,
                "unrealized": self.unrealized_pnl
            }
        }

        try:
            with open(HFT_MONITOR_STATE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    # ========================================================================
    # DISPLAY
    # ========================================================================

    def print_dashboard(self):
        """Print HFT monitoring dashboard."""
        scan = self.scan_all_systems()

        print("=" * 80)
        print("HFT-LEVEL SYSTEM MONITOR - EVERYTHING AT A GLANCE")
        print(f"Timestamp: {scan['timestamp']} | Scan: {scan['scan_latency_us']}μs")
        print("=" * 80)

        # Trading
        t = scan["trading"]
        print(f"\n[TRADING] Wallets: {t['wallets']} | Capacity: {t['capacity_per_sec']}/sec | "
              f"Positions: {t['positions']} | Orders: {t['open_orders']}")
        print(f"  Unrealized P&L: ${t['unrealized_pnl']:.2f}")

        # ABCFC
        a = scan["abcfc"]
        print(f"\n[ABCFC] E[Total]: ${a['total_expected']:,.0f} | "
              f"[${a['bounds'][0]:,.0f}, ${a['bounds'][1]:,.0f}]")
        print(f"  Decision: {a['decision']} | Score: {a.get('score', 0):.2f}")

        # Credits
        c = scan["credits"]
        print(f"\n[CREDITS] Cost: ${c['monthly_cost']:.0f}/mo → Value: ${c['monthly_value']:.0f}/mo = "
              f"{c['roi']:.1f}x ROI")
        print(f"  Runway: {c['runway_days']:.0f} days | Alerts: {c['alerts']}")

        # Infrastructure
        i = scan["infrastructure"]
        print(f"\n[INFRA] Droplets: {i['droplets']} | "
              f"Backend: {'✓' if i['backend_loop_running'] else '✗'} | "
              f"Healer: {'✓' if i['self_healer_running'] else '✗'}")

        # Aggregate
        agg = scan["aggregate"]
        print(f"\n[HEALTH] {agg['components_healthy']}/{agg['components_total']} components healthy "
              f"({agg['health_pct']:.0f}%)")
        print(f"  Avg Latency: {agg['avg_latency_us']}μs | "
              f"Total P&L: ${agg['total_pnl']:.2f}")

        # Component latencies
        print(f"\n[LATENCIES]")
        sorted_comps = sorted(
            [(n, c) for n, c in self.components.items() if c.latency.samples > 0],
            key=lambda x: x[1].latency.avg_latency_us,
            reverse=True
        )[:10]
        for name, comp in sorted_comps:
            status_icon = "✓" if comp.status == ComponentStatus.HEALTHY else "✗"
            print(f"  {status_icon} {name:25} avg={comp.latency.avg_latency_us:>8}μs "
                  f"p99={comp.latency.p99_latency_us:>8}μs "
                  f"max={comp.latency.max_latency_us:>8}μs")

        print("\n" + "=" * 80)

    def status(self) -> Dict:
        """Get status for backend loop integration."""
        scan = self.scan_all_systems()

        # Get economic flow rate from HFT Economics
        economics = {}
        if HFT_ECON_AVAILABLE:
            try:
                econ = get_hft_economics()
                flow = econ.get_flow_rate()
                emergent = econ.get_emergent_monthly()
                economics = {
                    "cost_per_sec": flow.cost_per_sec,
                    "profit_per_sec": flow.profit_per_sec,
                    "net_per_sec": flow.net_per_sec,
                    "cost_per_hour": flow.cost_per_hour,
                    "profit_per_hour": flow.profit_per_hour,
                    "net_per_hour": flow.net_per_hour,
                    "emergent_monthly_cost": emergent["projected_cost"],
                    "emergent_monthly_profit": emergent["projected_profit"],
                    "emergent_monthly_net": emergent["projected_net"],
                }
            except Exception:
                pass

        return {
            "success": True,
            "timestamp_us": scan["timestamp_us"],
            "scan_latency_us": scan["scan_latency_us"],
            "trading": scan["trading"],
            "abcfc": scan["abcfc"],
            "credits": scan["credits"],
            "infrastructure": scan["infrastructure"],
            "health_pct": scan["aggregate"]["health_pct"],
            "avg_latency_us": scan["aggregate"]["avg_latency_us"],
            "total_pnl": scan["aggregate"]["total_pnl"],
            "economics": economics,
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_monitor: Optional[HFTMonitor] = None


def get_hft_monitor() -> HFTMonitor:
    """Get or create global HFT monitor."""
    global _monitor
    if _monitor is None:
        _monitor = HFTMonitor()
    return _monitor


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="HFT System Monitor")
    parser.add_argument("command", choices=["dashboard", "scan", "status", "watch"],
                       nargs="?", default="dashboard")
    parser.add_argument("--interval", type=float, default=1.0,
                       help="Watch interval in seconds")

    args = parser.parse_args()
    monitor = get_hft_monitor()

    if args.command == "dashboard":
        monitor.print_dashboard()

    elif args.command == "scan":
        result = monitor.scan_all_systems()
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "status":
        status = monitor.status()
        print(json.dumps(status, indent=2, default=str))

    elif args.command == "watch":
        print("HFT Monitor - Watching (Ctrl+C to stop)")
        try:
            while True:
                os.system('clear')
                monitor.print_dashboard()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped watching.")


if __name__ == "__main__":
    main()
