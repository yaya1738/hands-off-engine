"""
Execution Simulator for Hands-Off Engine

Simulates order execution for backtesting:
- Simulate order fills
- Model slippage and fees
- Track simulated positions
- Calculate simulated P&L
"""

import sys
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


class OrderSide(Enum):
    """Order side enumeration"""
    YES = "YES"
    NO = "NO"


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    REJECTED = "rejected"


@dataclass
class SimulatedOrder:
    """Represents a simulated order"""
    order_id: str
    timestamp: datetime
    market_id: str
    market_name: str
    side: OrderSide
    size: float  # Dollar amount
    limit_price: Optional[float] = None  # Limit price (None for market order)
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_amount: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0


@dataclass
class Position:
    """Represents a position in a market"""
    market_id: str
    market_name: str
    side: OrderSide
    shares: float  # Number of shares (contracts)
    cost_basis: float  # Total cost including fees
    avg_entry_price: float  # Average entry price
    realized_pnl: float = 0.0  # Realized P&L from closed portion
    
    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L at current price"""
        if self.shares == 0:
            return 0.0
        
        # For YES positions: profit if price increases
        # For NO positions: profit if price decreases
        if self.side == OrderSide.YES:
            market_value = self.shares * current_price
        else:
            market_value = self.shares * (1.0 - current_price)
            
        return market_value - self.cost_basis
    
    def total_pnl(self, current_price: float) -> float:
        """Calculate total P&L (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl(current_price)


class ExecutionSimulator:
    """
    Simulates order execution for backtesting.
    
    Models realistic trading including:
    - Slippage (price impact)
    - Trading fees
    - Position tracking
    - P&L calculation
    """
    
    # Default trading parameters
    DEFAULT_FEE_RATE = 0.02  # 2% fee rate (typical for prediction markets)
    DEFAULT_SLIPPAGE_RATE = 0.005  # 0.5% slippage per $100 traded
    
    def __init__(
        self,
        initial_capital: float = 1000.0,
        fee_rate: float = DEFAULT_FEE_RATE,
        slippage_rate: float = DEFAULT_SLIPPAGE_RATE
    ):
        """
        Initialize execution simulator.
        
        Args:
            initial_capital: Starting capital in dollars
            fee_rate: Fee rate as decimal (e.g., 0.02 for 2%)
            slippage_rate: Slippage rate per $100 traded
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        
        self.positions: Dict[str, Position] = {}
        self.orders: List[SimulatedOrder] = []
        self.audit = get_audit_logger(component="simulator.executor")
        
    def calculate_slippage(self, size: float, side: OrderSide) -> float:
        """
        Calculate slippage for an order.
        
        Args:
            size: Order size in dollars
            side: Order side
            
        Returns:
            Slippage in price points (e.g., 0.005 means 0.5%)
        """
        # Slippage increases with order size
        # For YES: slippage pushes price up (worse fill)
        # For NO: slippage pushes price down (worse fill for NO = higher YES price)
        base_slippage = self.slippage_rate * (size / 100.0)
        
        # Add some randomness (±25%)
        import random
        noise = random.uniform(0.75, 1.25)
        
        return base_slippage * noise
    
    def execute_order(
        self,
        timestamp: datetime,
        market_id: str,
        market_name: str,
        side: str,
        size: float,
        market_price: float,
        limit_price: Optional[float] = None
    ) -> SimulatedOrder:
        """
        Execute a simulated order.
        
        Args:
            timestamp: Order timestamp
            market_id: Market identifier
            market_name: Market name
            side: Order side ("YES" or "NO")
            size: Order size in dollars
            market_price: Current market price (YES price)
            limit_price: Optional limit price
            
        Returns:
            SimulatedOrder object with execution details
        """
        order_side = OrderSide(side)
        order_id = f"sim_{market_id}_{timestamp.timestamp():.0f}"
        
        # Create order
        order = SimulatedOrder(
            order_id=order_id,
            timestamp=timestamp,
            market_id=market_id,
            market_name=market_name,
            side=order_side,
            size=size,
            limit_price=limit_price
        )
        
        # Check if we have enough capital
        if size > self.capital:
            order.status = OrderStatus.REJECTED
            self.audit.log_action(
                action_type="order_rejected",
                action_data={
                    "order_id": order_id,
                    "reason": "insufficient_capital",
                    "required": size,
                    "available": self.capital
                },
                result="rejected"
            )
            self.orders.append(order)
            return order
        
        # Calculate slippage
        slippage = self.calculate_slippage(size, order_side)
        order.slippage = slippage
        
        # Calculate execution price
        if order_side == OrderSide.YES:
            execution_price = market_price + slippage
        else:
            # For NO side, we're buying at (1 - YES_price) but slippage makes it worse
            execution_price = market_price + slippage
        
        # Check limit price
        if limit_price is not None:
            if order_side == OrderSide.YES and execution_price > limit_price:
                order.status = OrderStatus.REJECTED
                self.orders.append(order)
                return order
            elif order_side == OrderSide.NO and execution_price < limit_price:
                order.status = OrderStatus.REJECTED
                self.orders.append(order)
                return order
        
        # Calculate shares and fees
        shares = size / execution_price
        fees = size * self.fee_rate
        total_cost = size + fees
        
        order.status = OrderStatus.FILLED
        order.filled_price = execution_price
        order.filled_amount = size
        order.fees = fees
        
        # Update capital
        self.capital -= total_cost
        
        # Update or create position
        position_key = market_id
        if position_key in self.positions:
            position = self.positions[position_key]
            # Add to existing position (same side assumed)
            old_shares = position.shares
            old_cost = position.cost_basis
            new_shares = old_shares + shares
            new_cost = old_cost + total_cost
            
            position.shares = new_shares
            position.cost_basis = new_cost
            position.avg_entry_price = new_cost / new_shares if new_shares > 0 else 0.0
        else:
            # Create new position
            position = Position(
                market_id=market_id,
                market_name=market_name,
                side=order_side,
                shares=shares,
                cost_basis=total_cost,
                avg_entry_price=execution_price
            )
            self.positions[position_key] = position
        
        self.orders.append(order)
        
        self.audit.log_action(
            action_type="order_executed",
            action_data={
                "order_id": order_id,
                "market_id": market_id,
                "side": side,
                "size": size,
                "execution_price": execution_price,
                "shares": shares,
                "fees": fees,
                "slippage": slippage
            },
            result="filled"
        )
        
        return order
    
    def close_position(
        self,
        timestamp: datetime,
        market_id: str,
        market_price: float,
        fraction: float = 1.0
    ) -> Optional[float]:
        """
        Close a position (or portion of it).
        
        Args:
            timestamp: Close timestamp
            market_id: Market identifier
            market_price: Current market price
            fraction: Fraction of position to close (0.0 to 1.0)
            
        Returns:
            Realized P&L from closing, or None if position not found
        """
        if market_id not in self.positions:
            return None
        
        position = self.positions[market_id]
        
        if position.shares == 0:
            return None
        
        # Calculate shares to close
        shares_to_close = position.shares * fraction
        
        # Calculate proceeds (before fees)
        if position.side == OrderSide.YES:
            proceeds = shares_to_close * market_price
        else:
            proceeds = shares_to_close * (1.0 - market_price)
        
        # Calculate fees on close
        close_fees = proceeds * self.fee_rate
        net_proceeds = proceeds - close_fees
        
        # Calculate cost basis of closed portion
        cost_of_closed = position.cost_basis * fraction
        
        # Calculate realized P&L
        realized_pnl = net_proceeds - cost_of_closed
        
        # Update position
        position.shares *= (1.0 - fraction)
        position.cost_basis *= (1.0 - fraction)
        position.realized_pnl += realized_pnl
        
        # Update capital
        self.capital += net_proceeds
        
        # Remove position if fully closed
        if position.shares < 1e-6:
            del self.positions[market_id]
        
        self.audit.log_action(
            action_type="position_closed",
            action_data={
                "market_id": market_id,
                "shares_closed": shares_to_close,
                "proceeds": proceeds,
                "fees": close_fees,
                "realized_pnl": realized_pnl,
                "fraction": fraction
            },
            result="completed"
        )
        
        return realized_pnl
    
    def get_portfolio_value(self, market_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value.
        
        Args:
            market_prices: Dict mapping market_id to current YES price
            
        Returns:
            Total portfolio value (capital + positions)
        """
        total = self.capital
        
        for market_id, position in self.positions.items():
            if market_id in market_prices:
                price = market_prices[market_id]
                if position.side == OrderSide.YES:
                    total += position.shares * price
                else:
                    total += position.shares * (1.0 - price)
        
        return total
    
    def get_total_pnl(self, market_prices: Dict[str, float]) -> float:
        """
        Calculate total P&L (realized + unrealized).
        
        Args:
            market_prices: Dict mapping market_id to current YES price
            
        Returns:
            Total P&L in dollars
        """
        portfolio_value = self.get_portfolio_value(market_prices)
        return portfolio_value - self.initial_capital
    
    def get_metrics(self, market_prices: Dict[str, float]) -> Dict:
        """
        Get current portfolio metrics.
        
        Args:
            market_prices: Dict mapping market_id to current YES price
            
        Returns:
            Dictionary of portfolio metrics
        """
        total_value = self.get_portfolio_value(market_prices)
        total_pnl = total_value - self.initial_capital
        
        # Calculate position-level metrics
        positions_value = 0.0
        realized_pnl = 0.0
        unrealized_pnl = 0.0
        
        for market_id, position in self.positions.items():
            realized_pnl += position.realized_pnl
            if market_id in market_prices:
                price = market_prices[market_id]
                position_unrealized = position.unrealized_pnl(price)
                unrealized_pnl += position_unrealized
                
                if position.side == OrderSide.YES:
                    positions_value += position.shares * price
                else:
                    positions_value += position.shares * (1.0 - price)
        
        return {
            "total_value": total_value,
            "capital": self.capital,
            "positions_value": positions_value,
            "total_pnl": total_pnl,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "return_pct": (total_pnl / self.initial_capital * 100) if self.initial_capital > 0 else 0.0,
            "num_positions": len(self.positions),
            "num_orders": len(self.orders)
        }


if __name__ == "__main__":
    # Example usage
    print("Execution Simulator Example\n" + "=" * 50)
    
    simulator = ExecutionSimulator(initial_capital=1000.0)
    
    # Execute some orders
    timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    order1 = simulator.execute_order(
        timestamp=timestamp,
        market_id="btc_100k",
        market_name="BTC $100k by EOY?",
        side="YES",
        size=100.0,
        market_price=0.40
    )
    
    print(f"Order 1: {order1.status.value}")
    print(f"  Filled at: {order1.filled_price:.4f}")
    print(f"  Shares: {order1.filled_amount / order1.filled_price:.2f}")
    print(f"  Fees: ${order1.fees:.2f}")
    print(f"  Slippage: {order1.slippage:.4f}")
    
    # Check portfolio
    market_prices = {"btc_100k": 0.45}
    metrics = simulator.get_metrics(market_prices)
    
    print(f"\nPortfolio Metrics:")
    print(f"  Total Value: ${metrics['total_value']:.2f}")
    print(f"  Total P&L: ${metrics['total_pnl']:.2f}")
    print(f"  Return: {metrics['return_pct']:.2f}%")
    print(f"  Positions: {metrics['num_positions']}")
