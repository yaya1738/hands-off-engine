"""
Execution Engine for Hands-Off Engine

This module handles the actual order execution:
- Smart order routing
- Slippage control
- Partial fill handling
- Execution timing optimization
"""

import json
import sys
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Order:
    """Represents a trading order"""
    order_id: str
    market_id: str
    market_name: str
    side: str  # "YES" or "NO"
    amount: float  # Dollar amount
    price: Optional[float]  # Limit price (None for market orders)
    status: str
    created_at: str
    filled_amount: float = 0.0
    filled_price: Optional[float] = None
    filled_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result of order execution"""
    order_id: str
    success: bool
    status: str
    filled_amount: float
    filled_price: Optional[float]
    slippage_bps: float  # Slippage in basis points
    execution_time_ms: float  # Execution time in milliseconds
    message: str


class ExecutionEngine:
    """
    Execution engine handles order placement and monitoring.
    
    In DRYRUN mode: logs orders but doesn't execute
    In LIVE mode: executes via Polymarket API
    """
    
    # Execution parameters
    MAX_SLIPPAGE_BPS = 50  # Max 0.5% slippage
    ORDER_TIMEOUT_SECONDS = 60  # Order timeout
    PARTIAL_FILL_THRESHOLD = 0.5  # Min 50% fill to accept
    
    def __init__(self, dryrun: bool = True, state_dir: Optional[Path] = None):
        """
        Initialize execution engine.
        
        Args:
            dryrun: If True, no actual trades are executed (default: True)
            state_dir: Directory for state files (defaults to ../state)
        """
        self.dryrun = dryrun
        
        if state_dir is None:
            state_dir = Path(__file__).parent.parent / "state"
        
        self.state_dir = state_dir
        self.pending_file = state_dir / "execution" / "pending.json"
        self.history_file = state_dir / "execution" / "history.jsonl"
        self.metrics_file = state_dir / "execution" / "metrics.json"
        
        self.audit = get_audit_logger(component="executor.engine")
        
        # Ensure state files exist
        self._ensure_state_files()
    
    def _ensure_state_files(self):
        """Ensure state files exist with proper structure"""
        # Ensure directory exists
        self.pending_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create pending.json if it doesn't exist
        if not self.pending_file.exists():
            self._save_pending_orders([])
        
        # Create history.jsonl if it doesn't exist
        if not self.history_file.exists():
            self.history_file.touch()
        
        # Create metrics.json if it doesn't exist
        if not self.metrics_file.exists():
            self._save_metrics({
                "total_orders": 0,
                "successful_fills": 0,
                "failed_orders": 0,
                "total_slippage_bps": 0.0,
                "avg_execution_time_ms": 0.0,
                "last_reset": datetime.now(timezone.utc).isoformat()
            })
    
    def _load_pending_orders(self) -> List[Order]:
        """Load pending orders from state file"""
        with open(self.pending_file, 'r') as f:
            data = json.load(f)
        
        return [Order(**order) for order in data.get("orders", [])]
    
    def _save_pending_orders(self, orders: List[Order]):
        """Save pending orders to state file"""
        data = {
            "orders": [asdict(order) for order in orders],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        # Atomic write
        tmp_file = self.pending_file.with_suffix('.tmp')
        with open(tmp_file, 'w') as f:
            json.dump(data, f, indent=2)
        tmp_file.replace(self.pending_file)
    
    def _append_history(self, order: Order, result: ExecutionResult):
        """Append execution to history log"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "order": asdict(order),
            "result": asdict(result)
        }
        
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def _load_metrics(self) -> Dict:
        """Load execution metrics from state file"""
        with open(self.metrics_file, 'r') as f:
            return json.load(f)
    
    def _save_metrics(self, metrics: Dict):
        """Save execution metrics to state file"""
        # Atomic write
        tmp_file = self.metrics_file.with_suffix('.tmp')
        with open(tmp_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        tmp_file.replace(self.metrics_file)
    
    def _update_metrics(self, result: ExecutionResult):
        """Update execution metrics with new result"""
        metrics = self._load_metrics()
        
        metrics["total_orders"] += 1
        
        if result.success:
            metrics["successful_fills"] += 1
        else:
            metrics["failed_orders"] += 1
        
        # Update rolling averages
        total = metrics["total_orders"]
        metrics["total_slippage_bps"] = (
            (metrics["total_slippage_bps"] * (total - 1) + result.slippage_bps) / total
        )
        metrics["avg_execution_time_ms"] = (
            (metrics["avg_execution_time_ms"] * (total - 1) + result.execution_time_ms) / total
        )
        
        self._save_metrics(metrics)
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"order_{timestamp}_{int(time.time() * 1000) % 10000}"
    
    def _calculate_slippage(self, expected_price: float, filled_price: float) -> float:
        """Calculate slippage in basis points"""
        if expected_price == 0:
            return 0.0
        return abs(filled_price - expected_price) / expected_price * 10000
    
    def _execute_dryrun(self, order: Order) -> ExecutionResult:
        """Execute order in DRYRUN mode (simulation)"""
        start_time = time.time()
        
        # Simulate execution
        time.sleep(0.1)  # Simulate network latency
        
        # Simulate fill at expected price
        filled_price = order.price if order.price else 0.5
        filled_amount = order.amount
        
        execution_time_ms = (time.time() - start_time) * 1000
        slippage_bps = 0.0  # No slippage in DRYRUN
        
        return ExecutionResult(
            order_id=order.order_id,
            success=True,
            status=OrderStatus.FILLED.value,
            filled_amount=filled_amount,
            filled_price=filled_price,
            slippage_bps=slippage_bps,
            execution_time_ms=execution_time_ms,
            message=f"DRYRUN: Filled {order.side} ${filled_amount:.2f} @ {filled_price:.4f}"
        )
    
    def _execute_live(self, order: Order) -> ExecutionResult:
        """
        Execute order in LIVE mode via Polymarket API.
        
        NOTE: This is a placeholder. Real implementation would:
        1. Connect to Polymarket API
        2. Place order
        3. Monitor fills
        4. Handle errors
        """
        start_time = time.time()
        
        # TODO: Implement actual Polymarket API integration
        # For now, return a placeholder result
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return ExecutionResult(
            order_id=order.order_id,
            success=False,
            status=OrderStatus.FAILED.value,
            filled_amount=0.0,
            filled_price=None,
            slippage_bps=0.0,
            execution_time_ms=execution_time_ms,
            message="LIVE execution not yet implemented - API integration required"
        )
    
    def submit_order(self, action) -> Order:
        """
        Submit order from planned action.
        
        Args:
            action: PlannedAction object
            
        Returns:
            Order object with pending status
        """
        order = Order(
            order_id=self._generate_order_id(),
            market_id=action.market_id,
            market_name=action.market_name,
            side=action.side,
            amount=action.amount,
            price=None,  # Market order for now
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Add to pending orders
        pending = self._load_pending_orders()
        pending.append(order)
        self._save_pending_orders(pending)
        
        # Audit order submission
        self.audit.log_order(
            order_type="market",
            market=action.market_name,
            side=action.side,
            size=action.amount,
            dryrun=self.dryrun,
            order_id=order.order_id
        )
        
        return order
    
    def execute_order(self, order: Order) -> ExecutionResult:
        """
        Execute a pending order.
        
        Args:
            order: Order object to execute
            
        Returns:
            ExecutionResult with execution details
        """
        # Execute based on mode
        if self.dryrun:
            result = self._execute_dryrun(order)
        else:
            result = self._execute_live(order)
        
        # Update order status
        order.status = result.status
        order.filled_amount = result.filled_amount
        order.filled_price = result.filled_price
        
        if result.success:
            order.filled_at = datetime.now(timezone.utc).isoformat()
        else:
            order.error = result.message
        
        # Update pending orders
        pending = self._load_pending_orders()
        pending = [o for o in pending if o.order_id != order.order_id]
        self._save_pending_orders(pending)
        
        # Append to history
        self._append_history(order, result)
        
        # Update metrics
        self._update_metrics(result)
        
        # Audit execution
        self.audit.log_action(
            action_type="order_execution",
            action_data={
                "order_id": order.order_id,
                "market_id": order.market_id,
                "side": order.side,
                "amount": order.amount,
                "filled": result.filled_amount,
                "slippage_bps": result.slippage_bps,
                "execution_time_ms": result.execution_time_ms
            },
            result="success" if result.success else "failed"
        )
        
        return result
    
    def execute_actions(self, planned_actions: List) -> List[ExecutionResult]:
        """
        Execute multiple planned actions.
        
        Args:
            planned_actions: List of PlannedAction objects
            
        Returns:
            List of ExecutionResult objects
        """
        results = []
        
        for action in planned_actions:
            # Submit order
            order = self.submit_order(action)
            
            # Execute order
            result = self.execute_order(order)
            results.append(result)
        
        return results
    
    def get_pending_orders(self) -> List[Order]:
        """Get list of pending orders"""
        return self._load_pending_orders()
    
    def get_metrics(self) -> Dict:
        """Get execution quality metrics"""
        return self._load_metrics()


# Example usage
if __name__ == "__main__":
    from decider.ho_decider import PlannedAction
    
    engine = ExecutionEngine(dryrun=True)
    
    # Test action
    action = PlannedAction(
        market_id="test_market",
        market_name="Test Market",
        side="YES",
        amount=50.0,
        confidence=0.85,
        reasoning="Test execution"
    )
    
    # Execute
    results = engine.execute_actions([action])
    
    print("\nExecution Results:")
    for result in results:
        print(f"  Order {result.order_id}: {result.status}")
        print(f"    Filled: ${result.filled_amount:.2f} @ {result.filled_price:.4f}")
        print(f"    Slippage: {result.slippage_bps:.2f} bps")
        print(f"    Time: {result.execution_time_ms:.2f} ms")
        print(f"    Message: {result.message}")
    
    # Show metrics
    metrics = engine.get_metrics()
    print("\nExecution Metrics:")
    print(f"  Total orders: {metrics['total_orders']}")
    print(f"  Successful: {metrics['successful_fills']}")
    print(f"  Failed: {metrics['failed_orders']}")
    print(f"  Avg slippage: {metrics['total_slippage_bps']:.2f} bps")
    print(f"  Avg execution time: {metrics['avg_execution_time_ms']:.2f} ms")
