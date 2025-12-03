"""
Polymarket Execution Module
===========================

Smart order execution algorithms:
- TWAP (Time-Weighted Average Price)
- VWAP (Volume-Weighted Average Price)
- Iceberg orders
- Smart order routing
- Execution quality analysis
- Slippage minimization

USAGE:
    from executor.polymarket.execution import execution

    plan = execution.twap_schedule(total_size=1000, duration_minutes=60)
    slices = execution.iceberg_slices(total_size=5000, max_visible=100)
    analysis = execution.execution_quality(fills, orderbook)
"""

import math
import time
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class ExecutionStrategy(Enum):
    AGGRESSIVE = "aggressive"    # Take liquidity immediately
    PASSIVE = "passive"          # Post and wait
    BALANCED = "balanced"        # Mix of both
    TWAP = "twap"               # Time-weighted
    VWAP = "vwap"               # Volume-weighted
    ICEBERG = "iceberg"         # Hidden size


@dataclass
class ExecutionSlice:
    """Single execution slice"""
    index: int
    size: float
    target_time: datetime
    price_limit: Optional[float] = None
    status: str = "pending"
    filled_size: float = 0
    filled_price: float = 0


@dataclass
class ExecutionPlan:
    """Complete execution plan"""
    strategy: ExecutionStrategy
    total_size: float
    slices: List[ExecutionSlice]
    start_time: datetime
    end_time: datetime
    constraints: Dict


@dataclass
class ExecutionReport:
    """Execution quality report"""
    total_size: float
    avg_price: float
    vwap_benchmark: float
    twap_benchmark: float
    slippage_bps: float
    execution_time_seconds: float
    fill_rate: float


class ExecutionEngine:
    """
    Execution algorithms for Polymarket.

    Provides smart execution to minimize market impact and slippage.
    """

    # ==========================================
    # TWAP (TIME-WEIGHTED AVERAGE PRICE)
    # ==========================================

    def twap_schedule(self, total_size: float, duration_minutes: int,
                      num_slices: int = None, randomize: bool = True) -> ExecutionPlan:
        """
        Create TWAP execution schedule.

        Spreads order evenly across time to minimize impact.
        """
        if num_slices is None:
            # Default: one slice per minute, min 5, max 60
            num_slices = max(5, min(60, duration_minutes))

        slice_size = total_size / num_slices
        interval_seconds = (duration_minutes * 60) / num_slices

        start_time = datetime.now()
        slices = []

        for i in range(num_slices):
            # Add randomization to avoid predictable patterns
            if randomize:
                jitter = (hash(str(i)) % 10 - 5) / 100  # ±5% jitter
                actual_size = slice_size * (1 + jitter)
            else:
                actual_size = slice_size

            target_time = start_time + timedelta(seconds=i * interval_seconds)

            slices.append(ExecutionSlice(
                index=i,
                size=actual_size,
                target_time=target_time
            ))

        return ExecutionPlan(
            strategy=ExecutionStrategy.TWAP,
            total_size=total_size,
            slices=slices,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration_minutes),
            constraints={
                'duration_minutes': duration_minutes,
                'num_slices': num_slices,
                'avg_slice_size': slice_size
            }
        )

    def adaptive_twap(self, total_size: float, duration_minutes: int,
                      volatility: float) -> ExecutionPlan:
        """
        Adaptive TWAP that adjusts based on volatility.

        Higher volatility = more slices, smaller sizes
        """
        # More slices in high volatility
        base_slices = max(5, duration_minutes)
        vol_factor = 1 + volatility * 10  # Higher vol = more slices
        num_slices = int(base_slices * vol_factor)

        return self.twap_schedule(total_size, duration_minutes, num_slices)

    # ==========================================
    # VWAP (VOLUME-WEIGHTED AVERAGE PRICE)
    # ==========================================

    def vwap_schedule(self, total_size: float, historical_volume_profile: List[float],
                      duration_minutes: int) -> ExecutionPlan:
        """
        Create VWAP execution schedule.

        Matches execution to historical volume patterns.
        """
        # Normalize volume profile
        total_hist_vol = sum(historical_volume_profile)
        if total_hist_vol == 0:
            # Fall back to TWAP if no volume data
            return self.twap_schedule(total_size, duration_minutes)

        volume_weights = [v / total_hist_vol for v in historical_volume_profile]
        num_slices = len(volume_weights)
        interval_seconds = (duration_minutes * 60) / num_slices

        start_time = datetime.now()
        slices = []

        for i, weight in enumerate(volume_weights):
            slice_size = total_size * weight
            target_time = start_time + timedelta(seconds=i * interval_seconds)

            slices.append(ExecutionSlice(
                index=i,
                size=slice_size,
                target_time=target_time
            ))

        return ExecutionPlan(
            strategy=ExecutionStrategy.VWAP,
            total_size=total_size,
            slices=slices,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration_minutes),
            constraints={
                'duration_minutes': duration_minutes,
                'volume_profile': volume_weights
            }
        )

    def calculate_vwap_benchmark(self, trades: List[Dict]) -> float:
        """Calculate VWAP benchmark from trade data"""
        total_volume = sum(t.get('size', 0) for t in trades)
        if total_volume == 0:
            return 0

        volume_price = sum(t.get('size', 0) * t.get('price', 0) for t in trades)
        return volume_price / total_volume

    # ==========================================
    # ICEBERG ORDERS
    # ==========================================

    def iceberg_slices(self, total_size: float, max_visible: float,
                       randomize_size: bool = True) -> List[Dict]:
        """
        Create iceberg order slices.

        Shows only max_visible at a time, replenishes as filled.
        """
        slices = []
        remaining = total_size
        index = 0

        while remaining > 0:
            if randomize_size:
                # Vary visible size by ±20%
                variation = 0.8 + (hash(str(index)) % 40) / 100
                visible = min(remaining, max_visible * variation)
            else:
                visible = min(remaining, max_visible)

            slices.append({
                'index': index,
                'size': visible,
                'visible': True,
                'remaining_hidden': remaining - visible
            })

            remaining -= visible
            index += 1

        return slices

    def iceberg_refresh_logic(self, current_slice: Dict, fill_threshold: float = 0.8) -> Dict:
        """Determine when to show next iceberg slice"""
        filled_pct = current_slice.get('filled', 0) / current_slice.get('size', 1)

        return {
            'should_refresh': filled_pct >= fill_threshold,
            'filled_percent': filled_pct,
            'remaining_in_slice': current_slice['size'] * (1 - filled_pct)
        }

    # ==========================================
    # SMART ORDER ROUTING
    # ==========================================

    def optimal_execution_strategy(self, order_size: float, market_depth: float,
                                   urgency: str = "medium",
                                   volatility: float = 0.1) -> Dict:
        """
        Recommend optimal execution strategy based on market conditions.
        """
        size_to_depth_ratio = order_size / market_depth if market_depth > 0 else float('inf')

        if urgency == "high":
            # Execute immediately
            if size_to_depth_ratio < 0.1:
                strategy = "market_order"
                recommendation = "Order is small relative to depth, take immediately"
            else:
                strategy = "aggressive_twap"
                recommendation = "Large order, use short TWAP to minimize impact"
                duration = max(5, int(size_to_depth_ratio * 30))

        elif urgency == "low":
            # Patient execution
            strategy = "passive"
            recommendation = "Post limit orders and wait for fills"
            duration = None

        else:  # medium urgency
            if size_to_depth_ratio < 0.05:
                strategy = "limit_order"
                recommendation = "Post limit order at competitive price"
            elif size_to_depth_ratio < 0.2:
                strategy = "twap"
                duration = max(10, int(size_to_depth_ratio * 60))
                recommendation = f"Use {duration} minute TWAP"
            else:
                strategy = "iceberg"
                recommendation = "Use iceberg to hide true size"

        return {
            'strategy': strategy,
            'recommendation': recommendation,
            'size_to_depth_ratio': size_to_depth_ratio,
            'estimated_impact': self.estimate_impact(order_size, market_depth),
            'duration': duration if 'duration' in dir() else None
        }

    def estimate_impact(self, order_size: float, market_depth: float,
                        impact_coefficient: float = 0.1) -> float:
        """Estimate price impact of order"""
        if market_depth == 0:
            return 1.0  # 100% impact

        # Simple square-root impact model
        impact = impact_coefficient * math.sqrt(order_size / market_depth)
        return min(impact, 1.0)

    # ==========================================
    # EXECUTION ANALYSIS
    # ==========================================

    def execution_quality(self, fills: List[Dict], benchmark_price: float) -> ExecutionReport:
        """Analyze execution quality"""
        if not fills:
            return ExecutionReport(0, 0, 0, 0, 0, 0, 0)

        total_size = sum(f.get('size', 0) for f in fills)
        total_cost = sum(f.get('size', 0) * f.get('price', 0) for f in fills)
        avg_price = total_cost / total_size if total_size > 0 else 0

        # Slippage from benchmark
        slippage = (avg_price - benchmark_price) / benchmark_price if benchmark_price > 0 else 0
        slippage_bps = slippage * 10000

        # Execution time
        if fills[0].get('timestamp') and fills[-1].get('timestamp'):
            exec_time = fills[-1]['timestamp'] - fills[0]['timestamp']
        else:
            exec_time = 0

        return ExecutionReport(
            total_size=total_size,
            avg_price=avg_price,
            vwap_benchmark=benchmark_price,
            twap_benchmark=benchmark_price,  # Would need actual TWAP
            slippage_bps=slippage_bps,
            execution_time_seconds=exec_time,
            fill_rate=1.0  # Assuming all filled
        )

    def implementation_shortfall(self, decision_price: float, fills: List[Dict]) -> Dict:
        """
        Calculate implementation shortfall.

        IS = (Avg Execution Price - Decision Price) / Decision Price
        """
        if not fills:
            return {'is': 0, 'error': 'No fills'}

        total_size = sum(f.get('size', 0) for f in fills)
        total_cost = sum(f.get('size', 0) * f.get('price', 0) for f in fills)
        avg_exec_price = total_cost / total_size if total_size > 0 else 0

        is_value = (avg_exec_price - decision_price) / decision_price if decision_price > 0 else 0

        return {
            'implementation_shortfall': is_value,
            'is_bps': is_value * 10000,
            'decision_price': decision_price,
            'avg_execution_price': avg_exec_price,
            'interpretation': 'favorable' if is_value < 0 else 'unfavorable'
        }

    def fill_rate_analysis(self, orders: List[Dict], time_window_minutes: int = 60) -> Dict:
        """Analyze fill rates"""
        total_ordered = sum(o.get('size', 0) for o in orders)
        total_filled = sum(o.get('filled_size', 0) for o in orders)

        fill_rate = total_filled / total_ordered if total_ordered > 0 else 0

        # Analyze by price level
        at_best = sum(o.get('filled_size', 0) for o in orders if o.get('at_best_price', False))
        improved = sum(o.get('filled_size', 0) for o in orders if o.get('price_improved', False))

        return {
            'fill_rate': fill_rate,
            'fill_rate_pct': fill_rate * 100,
            'total_ordered': total_ordered,
            'total_filled': total_filled,
            'unfilled': total_ordered - total_filled,
            'filled_at_best': at_best,
            'price_improved': improved
        }

    # ==========================================
    # EXECUTION TACTICS
    # ==========================================

    def peg_to_mid(self, mid_price: float, offset_bps: float = 0,
                   side: str = "BUY") -> float:
        """Calculate price pegged to mid"""
        offset = mid_price * offset_bps / 10000
        if side.upper() == "BUY":
            return mid_price - offset  # Slightly below mid
        else:
            return mid_price + offset  # Slightly above mid

    def peg_to_primary(self, best_bid: float, best_ask: float,
                       side: str, improve_by: float = 0.001) -> float:
        """Peg to best bid/ask with optional improvement"""
        if side.upper() == "BUY":
            return best_bid + improve_by  # Improve bid
        else:
            return best_ask - improve_by  # Improve ask

    def layered_orders(self, base_price: float, total_size: float,
                       num_layers: int = 5, layer_spread_bps: float = 50,
                       side: str = "BUY") -> List[Dict]:
        """Create layered orders at multiple price levels"""
        layers = []
        layer_size = total_size / num_layers
        spread_per_layer = base_price * layer_spread_bps / 10000

        for i in range(num_layers):
            if side.upper() == "BUY":
                price = base_price - (i * spread_per_layer)
            else:
                price = base_price + (i * spread_per_layer)

            layers.append({
                'layer': i + 1,
                'price': round(price, 3),
                'size': layer_size,
                'distance_from_base_bps': i * layer_spread_bps
            })

        return layers

    def cancel_and_replace_logic(self, current_order: Dict, new_fair_value: float,
                                 threshold_bps: float = 20) -> Dict:
        """Determine if order should be cancelled and replaced"""
        current_price = current_order.get('price', 0)
        distance_bps = abs(current_price - new_fair_value) / new_fair_value * 10000 if new_fair_value > 0 else 0

        should_replace = distance_bps > threshold_bps

        return {
            'should_replace': should_replace,
            'current_price': current_price,
            'new_fair_value': new_fair_value,
            'distance_bps': distance_bps,
            'threshold_bps': threshold_bps,
            'suggested_new_price': new_fair_value if should_replace else current_price
        }

    # ==========================================
    # EXECUTION MONITORING
    # ==========================================

    def execution_progress(self, plan: ExecutionPlan, current_time: datetime = None) -> Dict:
        """Monitor execution progress"""
        if current_time is None:
            current_time = datetime.now()

        total_size = plan.total_size
        filled_size = sum(s.filled_size for s in plan.slices)
        pending_size = sum(s.size - s.filled_size for s in plan.slices if s.status == "pending")

        completed_slices = sum(1 for s in plan.slices if s.status == "completed")
        total_slices = len(plan.slices)

        # Time progress
        total_duration = (plan.end_time - plan.start_time).total_seconds()
        elapsed = (current_time - plan.start_time).total_seconds()
        time_progress = min(1.0, elapsed / total_duration) if total_duration > 0 else 1.0

        # Compare fill progress to time progress
        fill_progress = filled_size / total_size if total_size > 0 else 0
        pace = fill_progress / time_progress if time_progress > 0 else 0

        return {
            'fill_progress': fill_progress,
            'fill_progress_pct': fill_progress * 100,
            'time_progress': time_progress,
            'time_progress_pct': time_progress * 100,
            'pace': pace,  # >1 = ahead of schedule
            'filled_size': filled_size,
            'pending_size': pending_size,
            'remaining_size': total_size - filled_size,
            'completed_slices': completed_slices,
            'total_slices': total_slices,
            'on_track': 0.8 <= pace <= 1.2
        }


# Singleton instance
execution = ExecutionEngine()
