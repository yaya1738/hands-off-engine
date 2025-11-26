"""
Post-Trade Processing for Hands-Off Engine

This module handles post-execution tasks:
- Confirm fills
- Update positions
- Log to audit
- Send notifications
"""

import json
import sys
import os
from typing import Optional, Dict, List
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


class PostTradeProcessor:
    """
    Post-trade processor handles tasks after order execution.
    """
    
    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize post-trade processor.
        
        Args:
            state_dir: Directory for state files (defaults to ../state)
        """
        if state_dir is None:
            state_dir = Path(__file__).parent.parent / "state"
        
        self.state_dir = state_dir
        self.positions_file = state_dir / "positions.json"
        self.audit = get_audit_logger(component="executor.posttrade")
    
    def _load_positions(self) -> Dict:
        """Load current positions from state file"""
        if not self.positions_file.exists():
            return {"positions": {}, "last_updated": None}
        
        with open(self.positions_file, 'r') as f:
            return json.load(f)
    
    def _save_positions(self, positions: Dict):
        """Save positions to state file"""
        positions["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # Atomic write
        tmp_file = self.positions_file.with_suffix('.tmp')
        with open(tmp_file, 'w') as f:
            json.dump(positions, f, indent=2)
        tmp_file.replace(self.positions_file)
    
    def confirm_fill(self, order, result) -> bool:
        """
        Confirm that order was filled successfully.
        
        Args:
            order: Order object
            result: ExecutionResult object
            
        Returns:
            True if fill confirmed, False otherwise
        """
        if not result.success:
            self.audit.log_action(
                action_type="fill_confirmation",
                action_data={
                    "order_id": order.order_id,
                    "market_id": order.market_id,
                    "confirmed": False,
                    "reason": result.message
                },
                result="failed"
            )
            return False
        
        # Verify fill details
        if result.filled_amount <= 0:
            self.audit.log_action(
                action_type="fill_confirmation",
                action_data={
                    "order_id": order.order_id,
                    "market_id": order.market_id,
                    "confirmed": False,
                    "reason": "No fill amount"
                },
                result="failed"
            )
            return False
        
        # Fill confirmed
        self.audit.log_action(
            action_type="fill_confirmation",
            action_data={
                "order_id": order.order_id,
                "market_id": order.market_id,
                "confirmed": True,
                "filled_amount": result.filled_amount,
                "filled_price": result.filled_price
            },
            result="success"
        )
        
        return True
    
    def update_positions(self, order, result):
        """
        Update position tracking after fill.
        
        Args:
            order: Order object
            result: ExecutionResult object
        """
        if not result.success:
            return
        
        # Load current positions
        positions_data = self._load_positions()
        positions = positions_data.get("positions", {})
        
        market_id = order.market_id
        
        # Initialize position if doesn't exist
        if market_id not in positions:
            positions[market_id] = {
                "market_id": market_id,
                "market_name": order.market_name,
                "side": order.side,
                "quantity": 0.0,
                "total_cost": 0.0,
                "avg_price": 0.0,
                "realized_pnl": 0.0,
                "trades": []
            }
        
        position = positions[market_id]
        
        # Update position
        trade_record = {
            "order_id": order.order_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "side": order.side,
            "quantity": result.filled_amount,
            "price": result.filled_price,
            "cost": result.filled_amount * result.filled_price if result.filled_price else result.filled_amount
        }
        
        position["trades"].append(trade_record)
        
        # Update totals
        if order.side == position["side"]:
            # Adding to position
            position["total_cost"] += trade_record["cost"]
            position["quantity"] += result.filled_amount
            if position["quantity"] > 0:
                position["avg_price"] = position["total_cost"] / position["quantity"]
        else:
            # Reducing/reversing position
            # For now, simple tracking - could be enhanced with FIFO/LIFO
            position["quantity"] -= result.filled_amount
            position["realized_pnl"] += (result.filled_price - position["avg_price"]) * result.filled_amount
        
        # Save updated positions
        positions_data["positions"] = positions
        self._save_positions(positions_data)
        
        # Audit position update
        self.audit.log_action(
            action_type="position_update",
            action_data={
                "market_id": market_id,
                "side": order.side,
                "filled_amount": result.filled_amount,
                "filled_price": result.filled_price,
                "new_quantity": position["quantity"],
                "avg_price": position["avg_price"]
            },
            result="success"
        )
    
    def log_execution(self, order, result):
        """
        Log execution details to audit trail.
        
        Args:
            order: Order object
            result: ExecutionResult object
        """
        self.audit.log_action(
            action_type="execution_complete",
            action_data={
                "order_id": order.order_id,
                "market_id": order.market_id,
                "market_name": order.market_name,
                "side": order.side,
                "amount": order.amount,
                "filled_amount": result.filled_amount,
                "filled_price": result.filled_price,
                "slippage_bps": result.slippage_bps,
                "execution_time_ms": result.execution_time_ms,
                "success": result.success,
                "message": result.message
            },
            result="success" if result.success else "failed"
        )
    
    def send_notification(self, order, result, notification_type: str = "telegram"):
        """
        Send notification about execution.
        
        Args:
            order: Order object
            result: ExecutionResult object
            notification_type: Type of notification (telegram, slack, etc.)
        """
        # Format notification message
        if result.success:
            message = (
                f"✅ Order Filled\n"
                f"Market: {order.market_name}\n"
                f"Side: {order.side}\n"
                f"Amount: ${result.filled_amount:.2f}\n"
                f"Price: {result.filled_price:.4f}\n"
                f"Slippage: {result.slippage_bps:.2f} bps\n"
                f"Time: {result.execution_time_ms:.0f} ms"
            )
        else:
            message = (
                f"❌ Order Failed\n"
                f"Market: {order.market_name}\n"
                f"Side: {order.side}\n"
                f"Amount: ${order.amount:.2f}\n"
                f"Reason: {result.message}"
            )
        
        # Log notification (actual sending would happen here)
        self.audit.log_action(
            action_type="notification",
            action_data={
                "notification_type": notification_type,
                "order_id": order.order_id,
                "market_id": order.market_id,
                "success": result.success,
                "message": message
            },
            result="sent"
        )
        
        # TODO: Implement actual notification sending
        # For Telegram: would use telegram bot API
        # For Slack: would use slack webhook
        # For now, just print to console
        print(f"\n[NOTIFICATION - {notification_type.upper()}]")
        print(message)
    
    def process_execution(self, order, result):
        """
        Process completed execution through all post-trade steps.
        
        Args:
            order: Order object
            result: ExecutionResult object
        """
        # Confirm fill
        fill_confirmed = self.confirm_fill(order, result)
        
        # Update positions if filled
        if fill_confirmed:
            self.update_positions(order, result)
        
        # Log to audit trail
        self.log_execution(order, result)
        
        # Send notification
        self.send_notification(order, result)
    
    def get_positions(self) -> Dict:
        """Get current positions"""
        return self._load_positions()
    
    def get_position_summary(self) -> Dict:
        """Get summary of all positions"""
        positions_data = self._load_positions()
        positions = positions_data.get("positions", {})
        
        summary = {
            "total_positions": len(positions),
            "total_exposure": 0.0,
            "total_realized_pnl": 0.0,
            "positions_by_side": {"YES": 0, "NO": 0},
            "markets": []
        }
        
        for market_id, position in positions.items():
            if position["quantity"] != 0:
                summary["total_exposure"] += abs(position["quantity"] * position["avg_price"])
                summary["total_realized_pnl"] += position["realized_pnl"]
                summary["positions_by_side"][position["side"]] += 1
                
                summary["markets"].append({
                    "market_id": market_id,
                    "market_name": position["market_name"],
                    "side": position["side"],
                    "quantity": position["quantity"],
                    "avg_price": position["avg_price"],
                    "exposure": position["quantity"] * position["avg_price"]
                })
        
        return summary


# Example usage
if __name__ == "__main__":
    from executor.engine import Order, ExecutionResult, OrderStatus
    
    processor = PostTradeProcessor()
    
    # Test order
    order = Order(
        order_id="test_order_123",
        market_id="test_market",
        market_name="Test Market",
        side="YES",
        amount=50.0,
        price=0.6,
        status=OrderStatus.FILLED.value,
        created_at=datetime.now(timezone.utc).isoformat(),
        filled_amount=50.0,
        filled_price=0.6,
        filled_at=datetime.now(timezone.utc).isoformat()
    )
    
    result = ExecutionResult(
        order_id="test_order_123",
        success=True,
        status=OrderStatus.FILLED.value,
        filled_amount=50.0,
        filled_price=0.6,
        slippage_bps=5.0,
        execution_time_ms=150.0,
        message="Filled successfully"
    )
    
    # Process execution
    processor.process_execution(order, result)
    
    # Show position summary
    summary = processor.get_position_summary()
    print("\nPosition Summary:")
    print(f"  Total positions: {summary['total_positions']}")
    print(f"  Total exposure: ${summary['total_exposure']:.2f}")
    print(f"  Total realized P&L: ${summary['total_realized_pnl']:.2f}")
