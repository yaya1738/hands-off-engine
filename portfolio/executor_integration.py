"""
Portfolio Integration for Executor

This module provides integration between the Executor and Portfolio Tracker,
automatically recording positions when trades are executed.
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from portfolio.positions import PositionManager
from portfolio.tracker import PortfolioTracker
from audit import get_audit_logger


class PortfolioExecutorIntegration:
    """
    Integration layer between Executor and Portfolio Tracker.
    Automatically creates portfolio positions when trades are executed.
    """
    
    def __init__(self, position_manager: Optional[PositionManager] = None):
        """
        Initialize the integration.
        
        Args:
            position_manager: PositionManager instance (creates new if None)
        """
        self.position_manager = position_manager or PositionManager()
        self.tracker = PortfolioTracker(position_manager=self.position_manager)
        self.audit = get_audit_logger(component="portfolio_executor_integration")
    
    def on_trade_executed(self, market_id: str, market_name: str, side: str,
                         price: float, quantity: float, mode: str = "DRYRUN") -> Optional[str]:
        """
        Called when a trade is executed. Creates a position in the portfolio.
        
        Args:
            market_id: Market identifier
            market_name: Human-readable market name
            side: "YES" or "NO"
            price: Execution price per share
            quantity: Number of shares
            mode: "DRYRUN" or "LIVE"
            
        Returns:
            Position ID or None if position wasn't created
        """
        try:
            # Check risk limits before creating position
            amount = price * quantity
            allowed, reason = self.tracker.check_risk_limits(
                market_id=market_id,
                proposed_amount=amount,
                mode=mode
            )
            
            if not allowed:
                self.audit.log_action(
                    action_type="trade_rejected_risk_limits",
                    action_data={
                        "market_id": market_id,
                        "market_name": market_name,
                        "side": side,
                        "amount": amount,
                        "reason": reason,
                        "mode": mode
                    },
                    result="rejected"
                )
                return None
            
            # Create position
            position = self.position_manager.add_position(
                market_id=market_id,
                market_name=market_name,
                side=side,
                entry_price=price,
                quantity=quantity,
                mode=mode
            )
            
            self.audit.log_action(
                action_type="position_created_from_trade",
                action_data={
                    "position_id": position.position_id,
                    "market_id": market_id,
                    "market_name": market_name,
                    "side": side,
                    "price": price,
                    "quantity": quantity,
                    "amount": amount,
                    "mode": mode
                },
                result="success"
            )
            
            return position.position_id
            
        except Exception as e:
            self.audit.log_error(
                error_type="position_creation_failed",
                error_message=str(e),
                context={
                    "market_id": market_id,
                    "side": side,
                    "price": price,
                    "quantity": quantity,
                    "mode": mode
                }
            )
            return None
    
    def on_trade_closed(self, position_id: str, exit_price: float) -> bool:
        """
        Called when a position is closed. Updates the position record.
        
        Args:
            position_id: Position identifier
            exit_price: Exit price per share
            
        Returns:
            True if position was closed successfully
        """
        try:
            closed_position = self.position_manager.close_position(position_id, exit_price)
            
            if closed_position:
                self.audit.log_action(
                    action_type="position_closed_from_trade",
                    action_data={
                        "position_id": position_id,
                        "market_id": closed_position.market_id,
                        "exit_price": exit_price,
                        "realized_pnl": closed_position.realized_pnl,
                        "entry_amount": closed_position.entry_amount,
                        "exit_value": closed_position.current_value
                    },
                    result="success"
                )
                return True
            else:
                self.audit.log_action(
                    action_type="position_close_failed",
                    action_data={"position_id": position_id, "reason": "Position not found"},
                    result="failed"
                )
                return False
                
        except Exception as e:
            self.audit.log_error(
                error_type="position_close_failed",
                error_message=str(e),
                context={"position_id": position_id, "exit_price": exit_price}
            )
            return False
    
    def update_position_prices(self, market_prices: dict) -> int:
        """
        Update current prices for all open positions based on market data.
        
        Args:
            market_prices: Dictionary mapping market_id to current price
            
        Returns:
            Number of positions updated
        """
        updated_count = 0
        
        try:
            open_positions = self.position_manager.get_all_positions(status="open")
            
            for position in open_positions:
                if position.market_id in market_prices:
                    new_price = market_prices[position.market_id]
                    
                    # Only update if price changed
                    if abs(new_price - position.current_price) > 0.0001:
                        self.position_manager.update_position_price(
                            position.position_id,
                            new_price
                        )
                        updated_count += 1
            
            if updated_count > 0:
                self.audit.log_action(
                    action_type="bulk_price_update",
                    action_data={
                        "positions_updated": updated_count,
                        "markets_provided": len(market_prices)
                    },
                    result="success"
                )
            
            return updated_count
            
        except Exception as e:
            self.audit.log_error(
                error_type="bulk_price_update_failed",
                error_message=str(e),
                context={"markets_count": len(market_prices)}
            )
            return updated_count
    
    def get_portfolio_summary(self, mode: Optional[str] = None) -> dict:
        """
        Get current portfolio summary.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Portfolio summary dictionary
        """
        return self.tracker.get_portfolio_summary(mode=mode)


# Example usage
if __name__ == "__main__":
    # Create integration
    integration = PortfolioExecutorIntegration()
    
    # Simulate trade execution
    print("Simulating trade execution...")
    position_id = integration.on_trade_executed(
        market_id="test_market_1",
        market_name="Will BTC hit $100k by EOY?",
        side="YES",
        price=0.45,
        quantity=100.0,
        mode="DRYRUN"
    )
    
    if position_id:
        print(f"✓ Position created: {position_id}")
        
        # Update prices
        market_prices = {
            "test_market_1": 0.55
        }
        updated = integration.update_position_prices(market_prices)
        print(f"✓ Updated {updated} position(s)")
        
        # Get summary
        summary = integration.get_portfolio_summary(mode="DRYRUN")
        print(f"\nPortfolio Summary:")
        print(f"  Open positions: {summary['open_positions']['count']}")
        print(f"  Total value: ${summary['open_positions']['total_value']:.2f}")
        print(f"  Unrealized P&L: ${summary['open_positions']['unrealized_pnl']:.2f}")
        
        # Close position
        success = integration.on_trade_closed(position_id, 0.60)
        if success:
            print(f"\n✓ Position closed")
            
            # Get updated summary
            summary = integration.get_portfolio_summary(mode="DRYRUN")
            print(f"  Realized P&L: ${summary['closed_positions']['realized_pnl']:.2f}")
    else:
        print("✗ Position creation failed")
