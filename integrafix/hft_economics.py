#!/usr/bin/env python3
"""
INTEGRAFIX: HFT Economics - Real-Time Cost/Profit at System Speed
=================================================================

YAIR'S INSIGHT:
"Monthly costs are emergent. Everything happens at HFT frequency.
There are no fixed costs - every cost can be changed, every profit
happens in microseconds. Track at system speed."

PHILOSOPHY:
- Every API call has a cost (measured in μs and $)
- Every trade has a profit/loss (measured in μs and $)
- Every compute cycle has a cost
- Monthly = sum of all micro-events
- Nothing is fixed - everything is real-time

TRACKING:
- Cost per API call (tokens × price)
- Cost per compute second
- Profit per trade execution
- Net flow rate ($/second)

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

STATE_DIR = PROJECT_ROOT / "state"
LOG_DIR = PROJECT_ROOT / "logs"
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

HFT_ECON_STATE = STATE_DIR / "hft_economics.json"
HFT_ECON_LOG = LOG_DIR / "hft_economics.jsonl"


class EventType(Enum):
    """Types of economic events."""
    API_CALL = "api_call"
    TRADE_OPEN = "trade_open"
    TRADE_CLOSE = "trade_close"
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    VALUE_GENERATED = "value_generated"


@dataclass
class EconomicEvent:
    """A single economic event at HFT frequency."""
    timestamp_us: int  # Microsecond timestamp
    event_type: EventType
    provider: str  # anthropic, openai, digitalocean, polymarket, etc.
    cost_usd: float  # Negative = cost, Positive = profit
    tokens: int = 0  # For API calls
    latency_us: int = 0  # How long it took
    metadata: Dict = field(default_factory=dict)


@dataclass
class ABCFC:
    """ABCFC bounds for any value - worst/best/expected."""
    worst: float
    best: float
    expected: float

    def __repr__(self):
        return f"ABCFC(W:{self.worst:.4f}, E:{self.expected:.4f}, B:{self.best:.4f})"


@dataclass
class FlowRateABCFC:
    """Economic flow rate with ABCFC bounds ($/second)."""
    cost_per_sec: ABCFC
    profit_per_sec: ABCFC
    net_per_sec: ABCFC
    cost_per_hour: ABCFC
    profit_per_hour: ABCFC
    net_per_hour: ABCFC


@dataclass
class FlowRate:
    """Economic flow rate ($/second) - legacy, use FlowRateABCFC for bounds."""
    cost_per_sec: float
    profit_per_sec: float
    net_per_sec: float
    cost_per_hour: float
    profit_per_hour: float
    net_per_hour: float


# Provider costs at HFT granularity
PROVIDER_COSTS = {
    # AI Providers ($ per 1M tokens)
    "anthropic": {
        "claude-opus-4-5": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4": {"input": 3.0, "output": 15.0},
        "claude-haiku-3-5": {"input": 0.25, "output": 1.25},
    },
    "openai": {
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4o": {"input": 5.0, "output": 15.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    },
    "groq": {
        "llama-3.1-70b": {"input": 0.0, "output": 0.0},
        "mixtral-8x7b": {"input": 0.0, "output": 0.0},
    },
    "google": {
        "gemini-pro": {"input": 0.0, "output": 0.0},
    },

    # Compute ($ per second)
    "digitalocean": {
        "s-1vcpu-1gb": 0.00744 / 3600,  # $0.00744/hr → $/sec
        "s-2vcpu-4gb": 0.02976 / 3600,
        "s-4vcpu-8gb": 0.05952 / 3600,
        "s-8vcpu-16gb": 0.11905 / 3600,
    },

    # Trading ($ per trade)
    "polymarket": {
        "maker_fee": 0.0,  # 0% maker
        "taker_fee": 0.01,  # 1% taker (on profit)
    },
}


class HFTEconomics:
    """
    HFT-Frequency Economic Tracking.

    Every cost and profit measured at microsecond granularity.
    Monthly costs are emergent from the sum of all events.
    """

    def __init__(self):
        self.master = "Yair Siegel"
        self.start_time_us = int(time.time() * 1_000_000)
        self.start_time_ns = time.time_ns()

        # Event log (ring buffer for memory efficiency)
        self.events: deque = deque(maxlen=100000)  # Last 100K events

        # Running totals
        self.total_cost = 0.0
        self.total_profit = 0.0
        self.total_events = 0

        # Per-provider totals
        self.provider_costs: Dict[str, float] = {}
        self.provider_profits: Dict[str, float] = {}
        self.provider_events: Dict[str, int] = {}

        # Per-second tracking (sliding window)
        self.second_window: deque = deque(maxlen=3600)  # Last hour of seconds
        self.current_second_cost = 0.0
        self.current_second_profit = 0.0
        self.current_second = int(time.time())

        # Load state
        self._load_state()

        # Lock for thread safety
        self._lock = threading.Lock()

    def _now_us(self) -> int:
        """Current time in microseconds."""
        return int(time.time() * 1_000_000)

    def _load_state(self):
        """Load persisted state."""
        if HFT_ECON_STATE.exists():
            try:
                with open(HFT_ECON_STATE) as f:
                    data = json.load(f)
                    self.total_cost = data.get("total_cost", 0)
                    self.total_profit = data.get("total_profit", 0)
                    self.total_events = data.get("total_events", 0)
                    self.provider_costs = data.get("provider_costs", {})
                    self.provider_profits = data.get("provider_profits", {})
                    self.provider_events = data.get("provider_events", {})
            except Exception:
                pass

    def _save_state(self):
        """Persist state."""
        state = {
            "master": self.master,
            "timestamp_us": self._now_us(),
            "total_cost": self.total_cost,
            "total_profit": self.total_profit,
            "total_events": self.total_events,
            "net": self.total_profit - self.total_cost,
            "provider_costs": self.provider_costs,
            "provider_profits": self.provider_profits,
            "provider_events": self.provider_events,
            "flow_rate": asdict(self.get_flow_rate()),
        }
        try:
            with open(HFT_ECON_STATE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def _log_event(self, event: EconomicEvent):
        """Log event to file."""
        try:
            entry = {
                "ts_us": event.timestamp_us,
                "type": event.event_type.value,
                "provider": event.provider,
                "cost": event.cost_usd,
                "tokens": event.tokens,
                "latency_us": event.latency_us,
            }
            with open(HFT_ECON_LOG, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ========================================================================
    # COST RECORDING (HFT FREQUENCY)
    # ========================================================================

    def record_api_call(self, provider: str, model: str,
                        input_tokens: int, output_tokens: int,
                        latency_us: int = 0) -> float:
        """
        Record an API call cost at HFT frequency.

        Returns: cost in USD
        """
        # Calculate cost
        costs = PROVIDER_COSTS.get(provider, {}).get(model, {"input": 0, "output": 0})
        cost = (input_tokens / 1_000_000 * costs["input"] +
                output_tokens / 1_000_000 * costs["output"])

        event = EconomicEvent(
            timestamp_us=self._now_us(),
            event_type=EventType.API_CALL,
            provider=provider,
            cost_usd=-cost,  # Negative = expense
            tokens=input_tokens + output_tokens,
            latency_us=latency_us,
            metadata={"model": model, "input": input_tokens, "output": output_tokens}
        )

        self._record_event(event)
        return cost

    def record_compute_cost(self, provider: str, instance_type: str,
                           duration_sec: float) -> float:
        """
        Record compute cost at HFT frequency.

        Returns: cost in USD
        """
        cost_per_sec = PROVIDER_COSTS.get(provider, {}).get(instance_type, 0)
        cost = cost_per_sec * duration_sec

        event = EconomicEvent(
            timestamp_us=self._now_us(),
            event_type=EventType.COMPUTE,
            provider=provider,
            cost_usd=-cost,
            latency_us=int(duration_sec * 1_000_000),
            metadata={"instance": instance_type, "duration_sec": duration_sec}
        )

        self._record_event(event)
        return cost

    def record_trade_open(self, market: str, side: str, size: float,
                          price: float) -> float:
        """
        Record trade opening (no immediate cost, tracks position).

        Returns: 0 (cost happens at close)
        """
        event = EconomicEvent(
            timestamp_us=self._now_us(),
            event_type=EventType.TRADE_OPEN,
            provider="polymarket",
            cost_usd=0,  # No cost at open
            metadata={"market": market, "side": side, "size": size, "price": price}
        )

        self._record_event(event)
        return 0

    def record_trade_close(self, market: str, side: str, size: float,
                           entry_price: float, exit_price: float) -> float:
        """
        Record trade closing - this is where profit/loss happens.

        Returns: profit (positive) or loss (negative)
        """
        # Calculate P&L
        if side.upper() == "YES":
            pnl = size * (exit_price - entry_price)
        else:
            pnl = size * (entry_price - exit_price)

        # Apply taker fee on profit (if any)
        fee = 0
        if pnl > 0:
            fee = pnl * PROVIDER_COSTS["polymarket"]["taker_fee"]
            pnl -= fee

        event = EconomicEvent(
            timestamp_us=self._now_us(),
            event_type=EventType.TRADE_CLOSE,
            provider="polymarket",
            cost_usd=pnl,  # Positive = profit, Negative = loss
            metadata={
                "market": market, "side": side, "size": size,
                "entry": entry_price, "exit": exit_price,
                "gross_pnl": pnl + fee, "fee": fee
            }
        )

        self._record_event(event)
        return pnl

    def record_value_generated(self, source: str, value: float,
                               description: str = "") -> float:
        """
        Record value generated (insights, signals, decisions).

        This is the "output" side of the ROI equation.
        """
        event = EconomicEvent(
            timestamp_us=self._now_us(),
            event_type=EventType.VALUE_GENERATED,
            provider=source,
            cost_usd=value,  # Positive = value
            metadata={"description": description}
        )

        self._record_event(event)
        return value

    def _record_event(self, event: EconomicEvent):
        """Record an economic event."""
        with self._lock:
            self.events.append(event)
            self.total_events += 1

            # Update totals
            if event.cost_usd < 0:
                self.total_cost += abs(event.cost_usd)
                self.provider_costs[event.provider] = (
                    self.provider_costs.get(event.provider, 0) + abs(event.cost_usd)
                )
            else:
                self.total_profit += event.cost_usd
                self.provider_profits[event.provider] = (
                    self.provider_profits.get(event.provider, 0) + event.cost_usd
                )

            self.provider_events[event.provider] = (
                self.provider_events.get(event.provider, 0) + 1
            )

            # Update per-second tracking
            current_sec = int(time.time())
            if current_sec != self.current_second:
                # New second - save previous and reset
                self.second_window.append({
                    "second": self.current_second,
                    "cost": self.current_second_cost,
                    "profit": self.current_second_profit,
                })
                self.current_second = current_sec
                self.current_second_cost = 0
                self.current_second_profit = 0

            if event.cost_usd < 0:
                self.current_second_cost += abs(event.cost_usd)
            else:
                self.current_second_profit += event.cost_usd

        # Log event
        self._log_event(event)

    # ========================================================================
    # FLOW RATE CALCULATION
    # ========================================================================

    def get_flow_rate(self) -> FlowRate:
        """
        Calculate current economic flow rate ($/second).

        This is the real-time cost/profit velocity.
        """
        with self._lock:
            if not self.second_window:
                # Use overall average
                elapsed_sec = max(1, (self._now_us() - self.start_time_us) / 1_000_000)
                cost_per_sec = self.total_cost / elapsed_sec
                profit_per_sec = self.total_profit / elapsed_sec
            else:
                # Use recent window (last 60 seconds)
                recent = list(self.second_window)[-60:]
                if recent:
                    total_cost = sum(s["cost"] for s in recent)
                    total_profit = sum(s["profit"] for s in recent)
                    seconds = len(recent)
                    cost_per_sec = total_cost / seconds if seconds > 0 else 0
                    profit_per_sec = total_profit / seconds if seconds > 0 else 0
                else:
                    cost_per_sec = 0
                    profit_per_sec = 0

        return FlowRate(
            cost_per_sec=cost_per_sec,
            profit_per_sec=profit_per_sec,
            net_per_sec=profit_per_sec - cost_per_sec,
            cost_per_hour=cost_per_sec * 3600,
            profit_per_hour=profit_per_sec * 3600,
            net_per_hour=(profit_per_sec - cost_per_sec) * 3600,
        )

    def get_flow_rate_abcfc(self) -> FlowRateABCFC:
        """
        Calculate flow rate with ABCFC bounds (worst/best/expected).

        The bounds come from the variance in recent observations:
        - worst: highest cost observed, lowest profit observed
        - best: lowest cost observed, highest profit observed
        - expected: average (midline)
        """
        # Get flow rate first (outside lock to avoid deadlock)
        flow = self.get_flow_rate()

        with self._lock:
            if not self.second_window or len(self.second_window) < 2:
                # Not enough data - use point estimates with uncertainty
                # Default uncertainty: ±50% for costs, ±100% for profits
                return FlowRateABCFC(
                    cost_per_sec=ABCFC(
                        worst=flow.cost_per_sec * 1.5,
                        expected=flow.cost_per_sec,
                        best=flow.cost_per_sec * 0.5
                    ),
                    profit_per_sec=ABCFC(
                        worst=0,  # Could make nothing
                        expected=flow.profit_per_sec,
                        best=flow.profit_per_sec * 2  # Could double
                    ),
                    net_per_sec=ABCFC(
                        worst=-flow.cost_per_sec * 1.5,
                        expected=flow.net_per_sec,
                        best=flow.profit_per_sec * 2 - flow.cost_per_sec * 0.5
                    ),
                    cost_per_hour=ABCFC(
                        worst=flow.cost_per_hour * 1.5,
                        expected=flow.cost_per_hour,
                        best=flow.cost_per_hour * 0.5
                    ),
                    profit_per_hour=ABCFC(
                        worst=0,
                        expected=flow.profit_per_hour,
                        best=flow.profit_per_hour * 2
                    ),
                    net_per_hour=ABCFC(
                        worst=-flow.cost_per_hour * 1.5,
                        expected=flow.net_per_hour,
                        best=flow.profit_per_hour * 2 - flow.cost_per_hour * 0.5
                    ),
                )

            # Calculate bounds from observed variance
            # EXPECTED stays the same as flow rate - ABCFC just adds worst/best bounds
            recent = list(self.second_window)[-60:]
            costs = [s["cost"] for s in recent]
            profits = [s["profit"] for s in recent]

            # Worst/best from observations, expected from flow rate (unchanged!)
            cost_worst = max(costs) if costs else flow.cost_per_sec * 1.5
            cost_best = min(costs) if costs else flow.cost_per_sec * 0.5

            profit_worst = min(profits) if profits else 0
            profit_best = max(profits) if profits else flow.profit_per_sec * 2

        # EXPECTED = original flow rate values (unchanged!)
        # ABCFC just adds worst/best bounds around them
        return FlowRateABCFC(
            cost_per_sec=ABCFC(worst=cost_worst, expected=flow.cost_per_sec, best=cost_best),
            profit_per_sec=ABCFC(worst=profit_worst, expected=flow.profit_per_sec, best=profit_best),
            net_per_sec=ABCFC(
                worst=profit_worst - cost_worst,
                expected=flow.net_per_sec,  # UNCHANGED!
                best=profit_best - cost_best
            ),
            cost_per_hour=ABCFC(worst=cost_worst*3600, expected=flow.cost_per_hour, best=cost_best*3600),
            profit_per_hour=ABCFC(worst=profit_worst*3600, expected=flow.profit_per_hour, best=profit_best*3600),
            net_per_hour=ABCFC(
                worst=(profit_worst - cost_worst)*3600,
                expected=flow.net_per_hour,  # UNCHANGED!
                best=(profit_best - cost_best)*3600
            ),
        )

    def get_instantaneous_rate(self) -> Dict:
        """
        Get instantaneous rate from last second.
        """
        with self._lock:
            return {
                "cost_per_sec": self.current_second_cost,
                "profit_per_sec": self.current_second_profit,
                "net_per_sec": self.current_second_profit - self.current_second_cost,
            }

    # ========================================================================
    # EMERGENT METRICS (derived from HFT data)
    # ========================================================================

    def get_emergent_monthly(self) -> Dict:
        """
        Calculate emergent monthly costs from HFT data.

        Monthly = flow_rate × seconds_in_month
        NOT a fixed value - changes in real-time based on actual usage.
        """
        flow = self.get_flow_rate()
        seconds_per_month = 30 * 24 * 3600

        return {
            "projected_cost": flow.cost_per_sec * seconds_per_month,
            "projected_profit": flow.profit_per_sec * seconds_per_month,
            "projected_net": flow.net_per_sec * seconds_per_month,
            "note": "Emergent from HFT frequency - changes in real-time",
            "based_on_rate": {
                "cost_per_sec": flow.cost_per_sec,
                "profit_per_sec": flow.profit_per_sec,
            }
        }

    def get_emergent_monthly_abcfc(self) -> Dict:
        """
        Calculate emergent monthly with ABCFC bounds.

        Monthly = flow_rate × seconds_in_month
        Returns worst/best/expected for each metric.
        """
        flow_abcfc = self.get_flow_rate_abcfc()
        seconds_per_month = 30 * 24 * 3600

        return {
            "projected_cost": {
                "worst": flow_abcfc.cost_per_sec.worst * seconds_per_month,
                "expected": flow_abcfc.cost_per_sec.expected * seconds_per_month,
                "best": flow_abcfc.cost_per_sec.best * seconds_per_month,
            },
            "projected_profit": {
                "worst": flow_abcfc.profit_per_sec.worst * seconds_per_month,
                "expected": flow_abcfc.profit_per_sec.expected * seconds_per_month,
                "best": flow_abcfc.profit_per_sec.best * seconds_per_month,
            },
            "projected_net": {
                "worst": flow_abcfc.net_per_sec.worst * seconds_per_month,
                "expected": flow_abcfc.net_per_sec.expected * seconds_per_month,
                "best": flow_abcfc.net_per_sec.best * seconds_per_month,
            },
            "note": "ABCFC bounds from observed HFT variance",
            "flow_rate_abcfc": {
                "cost_per_sec": asdict(flow_abcfc.cost_per_sec),
                "profit_per_sec": asdict(flow_abcfc.profit_per_sec),
                "net_per_sec": asdict(flow_abcfc.net_per_sec),
            }
        }

    def get_runway_seconds(self, available_credits: float) -> float:
        """
        Calculate runway in SECONDS (not days).

        At HFT frequency, we think in seconds, not months.
        """
        flow = self.get_flow_rate()
        if flow.cost_per_sec <= 0:
            return float('inf')
        return available_credits / flow.cost_per_sec

    # ========================================================================
    # STATUS
    # ========================================================================

    def status(self) -> Dict:
        """Get HFT economics status."""
        flow = self.get_flow_rate()
        flow_abcfc = self.get_flow_rate_abcfc()
        instant = self.get_instantaneous_rate()
        emergent = self.get_emergent_monthly()
        emergent_abcfc = self.get_emergent_monthly_abcfc()

        elapsed_us = self._now_us() - self.start_time_us
        elapsed_sec = elapsed_us / 1_000_000

        self._save_state()

        return {
            "timestamp_us": self._now_us(),
            "elapsed_sec": elapsed_sec,

            # Totals
            "total_cost": self.total_cost,
            "total_profit": self.total_profit,
            "total_net": self.total_profit - self.total_cost,
            "total_events": self.total_events,

            # Flow rates ($/second) - midline expected
            "flow": {
                "cost_per_sec": flow.cost_per_sec,
                "profit_per_sec": flow.profit_per_sec,
                "net_per_sec": flow.net_per_sec,
                "cost_per_hour": flow.cost_per_hour,
                "profit_per_hour": flow.profit_per_hour,
                "net_per_hour": flow.net_per_hour,
            },

            # Flow rates with ABCFC bounds (worst/best/expected)
            "flow_abcfc": {
                "cost_per_sec": asdict(flow_abcfc.cost_per_sec),
                "profit_per_sec": asdict(flow_abcfc.profit_per_sec),
                "net_per_sec": asdict(flow_abcfc.net_per_sec),
                "cost_per_hour": asdict(flow_abcfc.cost_per_hour),
                "profit_per_hour": asdict(flow_abcfc.profit_per_hour),
                "net_per_hour": asdict(flow_abcfc.net_per_hour),
            },

            # Instantaneous (last second)
            "instant": instant,

            # Emergent monthly (NOT fixed) - midline
            "emergent_monthly": emergent,

            # Emergent monthly with ABCFC bounds
            "emergent_monthly_abcfc": emergent_abcfc,

            # Per provider
            "providers": {
                p: {
                    "cost": self.provider_costs.get(p, 0),
                    "profit": self.provider_profits.get(p, 0),
                    "events": self.provider_events.get(p, 0),
                }
                for p in set(list(self.provider_costs.keys()) +
                           list(self.provider_profits.keys()))
            },

            # ROI at HFT frequency
            "roi": {
                "multiplier": (self.total_profit / self.total_cost) if self.total_cost > 0 else float('inf'),
                "net_per_event": ((self.total_profit - self.total_cost) / self.total_events) if self.total_events > 0 else 0,
            }
        }

    def print_dashboard(self):
        """Print HFT economics dashboard."""
        status = self.status()

        print("=" * 80)
        print("HFT ECONOMICS - REAL-TIME COST/PROFIT AT SYSTEM SPEED")
        print(f"Timestamp: {status['timestamp_us']}μs | Elapsed: {status['elapsed_sec']:.1f}s")
        print("=" * 80)

        # Flow rates
        f = status["flow"]
        print(f"\n[FLOW RATE - $/second]")
        print(f"  Cost:   ${f['cost_per_sec']:.6f}/sec = ${f['cost_per_hour']:.2f}/hr")
        print(f"  Profit: ${f['profit_per_sec']:.6f}/sec = ${f['profit_per_hour']:.2f}/hr")
        print(f"  Net:    ${f['net_per_sec']:.6f}/sec = ${f['net_per_hour']:.2f}/hr")

        # Instantaneous
        i = status["instant"]
        print(f"\n[INSTANTANEOUS - last second]")
        print(f"  Cost: ${i['cost_per_sec']:.6f} | Profit: ${i['profit_per_sec']:.6f} | "
              f"Net: ${i['net_per_sec']:.6f}")

        # Totals
        print(f"\n[TOTALS - cumulative]")
        print(f"  Cost:   ${status['total_cost']:.4f}")
        print(f"  Profit: ${status['total_profit']:.4f}")
        print(f"  Net:    ${status['total_net']:.4f}")
        print(f"  Events: {status['total_events']}")

        # Emergent monthly
        e = status["emergent_monthly"]
        print(f"\n[EMERGENT MONTHLY - derived from HFT rate]")
        print(f"  Projected Cost:   ${e['projected_cost']:.2f}")
        print(f"  Projected Profit: ${e['projected_profit']:.2f}")
        print(f"  Projected Net:    ${e['projected_net']:.2f}")
        print(f"  (Changes in real-time based on actual usage)")

        # ROI
        r = status["roi"]
        print(f"\n[ROI]")
        print(f"  Multiplier: {r['multiplier']:.2f}x")
        print(f"  Net/Event:  ${r['net_per_event']:.6f}")

        # Per provider
        if status["providers"]:
            print(f"\n[PER PROVIDER]")
            for provider, data in sorted(status["providers"].items(),
                                        key=lambda x: x[1]["cost"], reverse=True):
                print(f"  {provider:15} cost=${data['cost']:.4f} "
                      f"profit=${data['profit']:.4f} events={data['events']}")

        print("\n" + "=" * 80)


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_economics: Optional[HFTEconomics] = None


def get_hft_economics() -> HFTEconomics:
    """Get or create global HFT economics tracker."""
    global _economics
    if _economics is None:
        _economics = HFTEconomics()
    return _economics


# ============================================================================
# CONVENIENCE FUNCTIONS (for use throughout codebase)
# ============================================================================

def track_api_call(provider: str, model: str, input_tokens: int,
                   output_tokens: int, latency_us: int = 0) -> float:
    """Track an API call cost. Returns cost in USD."""
    return get_hft_economics().record_api_call(
        provider, model, input_tokens, output_tokens, latency_us
    )


def track_trade_pnl(market: str, side: str, size: float,
                    entry: float, exit: float) -> float:
    """Track a trade P&L. Returns profit/loss in USD."""
    return get_hft_economics().record_trade_close(
        market, side, size, entry, exit
    )


def track_value(source: str, value: float, description: str = "") -> float:
    """Track value generated. Returns value in USD."""
    return get_hft_economics().record_value_generated(source, value, description)


def get_cost_rate() -> float:
    """Get current cost rate in $/second."""
    return get_hft_economics().get_flow_rate().cost_per_sec


def get_profit_rate() -> float:
    """Get current profit rate in $/second."""
    return get_hft_economics().get_flow_rate().profit_per_sec


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="HFT Economics Tracker")
    parser.add_argument("command", choices=["dashboard", "status", "watch", "simulate"],
                       nargs="?", default="dashboard")
    parser.add_argument("--interval", type=float, default=1.0)

    args = parser.parse_args()
    econ = get_hft_economics()

    if args.command == "dashboard":
        econ.print_dashboard()

    elif args.command == "status":
        print(json.dumps(econ.status(), indent=2, default=str))

    elif args.command == "watch":
        print("HFT Economics - Watching (Ctrl+C to stop)")
        try:
            while True:
                os.system('clear')
                econ.print_dashboard()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")

    elif args.command == "simulate":
        # Simulate some activity to show the system works
        print("Simulating HFT economic activity...")

        for i in range(10):
            # Simulate API calls
            econ.record_api_call("anthropic", "claude-haiku-3-5",
                                1000, 500, latency_us=50000)

            # Simulate a trade
            if i % 3 == 0:
                econ.record_trade_close("test_market", "YES",
                                       10.0, 0.50, 0.55)

            # Simulate value generated
            econ.record_value_generated("system", 0.01, "insight")

            time.sleep(0.1)

        econ.print_dashboard()


if __name__ == "__main__":
    main()
