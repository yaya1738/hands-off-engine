"""
Portfolio Tracker for Hands-Off Engine

Tracks all positions and calculates portfolio value in real-time.
Supports both DRYRUN and LIVE modes.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger
from portfolio.positions import Position, PositionManager


class PortfolioTracker:
    """
    Tracks portfolio value and positions across DRYRUN and LIVE modes.
    Calculates aggregate metrics and portfolio composition.
    """
    
    def __init__(self, position_manager: Optional[PositionManager] = None):
        """
        Initialize portfolio tracker.
        
        Args:
            position_manager: PositionManager instance (creates new if None)
        """
        self.position_manager = position_manager or PositionManager()
        self.audit = get_audit_logger(component="portfolio_tracker")
    
    def get_portfolio_value(self, mode: Optional[str] = None, status: str = "open") -> float:
        """
        Calculate total portfolio value.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            status: Filter by status ("open" or "closed", default "open")
            
        Returns:
            Total portfolio value in dollars
        """
        positions = self.position_manager.get_all_positions(status=status, mode=mode)
        return sum(pos.current_value for pos in positions)
    
    def get_portfolio_cost_basis(self, mode: Optional[str] = None, status: str = "open") -> float:
        """
        Calculate total cost basis (amount invested).
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            status: Filter by status ("open" or "closed", default "open")
            
        Returns:
            Total cost basis in dollars
        """
        positions = self.position_manager.get_all_positions(status=status, mode=mode)
        return sum(pos.entry_amount for pos in positions)
    
    def get_unrealized_pnl(self, mode: Optional[str] = None) -> float:
        """
        Calculate total unrealized P&L from open positions.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Total unrealized P&L in dollars
        """
        positions = self.position_manager.get_all_positions(status="open", mode=mode)
        return sum(pos.unrealized_pnl for pos in positions)
    
    def get_position_count(self, mode: Optional[str] = None, status: Optional[str] = None) -> int:
        """
        Get count of positions.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            status: Filter by status ("open" or "closed", None for all)
            
        Returns:
            Number of positions
        """
        return len(self.position_manager.get_all_positions(status=status, mode=mode))
    
    def get_portfolio_summary(self, mode: Optional[str] = None) -> Dict:
        """
        Get comprehensive portfolio summary.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Dictionary with portfolio metrics
        """
        open_positions = self.position_manager.get_all_positions(status="open", mode=mode)
        closed_positions = self.position_manager.get_all_positions(status="closed", mode=mode)
        
        # Calculate metrics
        total_value = sum(pos.current_value for pos in open_positions)
        total_cost = sum(pos.entry_amount for pos in open_positions)
        unrealized_pnl = sum(pos.unrealized_pnl for pos in open_positions)
        realized_pnl = sum(pos.realized_pnl or 0 for pos in closed_positions)
        
        # Calculate unrealized P&L percentage
        unrealized_pnl_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
        
        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mode': mode or "ALL",
            'open_positions': {
                'count': len(open_positions),
                'total_value': total_value,
                'total_cost': total_cost,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct
            },
            'closed_positions': {
                'count': len(closed_positions),
                'realized_pnl': realized_pnl
            },
            'total_pnl': unrealized_pnl + realized_pnl
        }
        
        # Log the summary to audit
        self.audit.log_action(
            action_type="portfolio_summary",
            action_data=summary,
            result="success"
        )
        
        return summary
    
    def get_positions_by_market(self, mode: Optional[str] = None) -> Dict[str, List[Position]]:
        """
        Group positions by market.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Dictionary mapping market_id to list of positions
        """
        positions = self.position_manager.get_all_positions(mode=mode)
        
        by_market: Dict[str, List[Position]] = {}
        for pos in positions:
            if pos.market_id not in by_market:
                by_market[pos.market_id] = []
            by_market[pos.market_id].append(pos)
        
        return by_market
    
    def get_exposure_by_market(self, mode: Optional[str] = None) -> Dict[str, float]:
        """
        Calculate total exposure (cost basis) by market.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Dictionary mapping market_id to total exposure
        """
        positions_by_market = self.get_positions_by_market(mode=mode)
        
        exposure = {}
        for market_id, positions in positions_by_market.items():
            # Only count open positions
            open_positions = [p for p in positions if p.status == "open"]
            exposure[market_id] = sum(p.entry_amount for p in open_positions)
        
        return exposure
    
    def check_risk_limits(self, market_id: str, proposed_amount: float,
                         max_per_position: float = 100.0,
                         max_per_market: float = 300.0,
                         max_total_exposure: float = 1000.0,
                         mode: str = "DRYRUN") -> tuple[bool, str]:
        """
        Check if proposed position would violate risk limits.
        
        Args:
            market_id: Market identifier
            proposed_amount: Proposed position size in dollars
            max_per_position: Maximum per position (default $100)
            max_per_market: Maximum total per market (default $300)
            max_total_exposure: Maximum total portfolio exposure (default $1000)
            mode: Trading mode ("DRYRUN" or "LIVE")
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check per-position limit
        if proposed_amount > max_per_position:
            return False, f"Position size ${proposed_amount:.2f} exceeds max ${max_per_position:.2f}"
        
        # Check per-market limit
        current_market_exposure = self.get_exposure_by_market(mode=mode).get(market_id, 0)
        new_market_exposure = current_market_exposure + proposed_amount
        if new_market_exposure > max_per_market:
            return False, f"Market exposure ${new_market_exposure:.2f} would exceed max ${max_per_market:.2f}"
        
        # Check total portfolio limit
        current_total_exposure = self.get_portfolio_cost_basis(mode=mode, status="open")
        new_total_exposure = current_total_exposure + proposed_amount
        if new_total_exposure > max_total_exposure:
            return False, f"Total exposure ${new_total_exposure:.2f} would exceed max ${max_total_exposure:.2f}"
        
        return True, "OK"
    
    def get_top_positions(self, n: int = 10, mode: Optional[str] = None,
                         sort_by: str = "unrealized_pnl") -> List[Position]:
        """
        Get top N positions sorted by specified metric.
        
        Args:
            n: Number of positions to return
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            sort_by: Sort metric ("unrealized_pnl", "current_value", "entry_amount")
            
        Returns:
            List of top N positions
        """
        positions = self.position_manager.get_all_positions(status="open", mode=mode)
        
        if sort_by == "unrealized_pnl":
            positions.sort(key=lambda p: p.unrealized_pnl, reverse=True)
        elif sort_by == "current_value":
            positions.sort(key=lambda p: p.current_value, reverse=True)
        elif sort_by == "entry_amount":
            positions.sort(key=lambda p: p.entry_amount, reverse=True)
        
        return positions[:n]
    
    def get_portfolio_health_check(self, mode: Optional[str] = None) -> Dict:
        """
        Perform health check on portfolio.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Dictionary with health metrics and warnings
        """
        summary = self.get_portfolio_summary(mode=mode)
        exposure_by_market = self.get_exposure_by_market(mode=mode)
        
        warnings = []
        
        # Check for concentration risk
        if exposure_by_market:
            max_market_exposure = max(exposure_by_market.values())
            total_exposure = summary['open_positions']['total_cost']
            
            if total_exposure > 0:
                concentration_pct = (max_market_exposure / total_exposure) * 100
                if concentration_pct > 30:
                    warnings.append(f"High concentration: {concentration_pct:.1f}% in single market")
        
        # Check for negative P&L
        if summary['total_pnl'] < -100:
            warnings.append(f"Large negative P&L: ${summary['total_pnl']:.2f}")
        
        # Check for stale positions (open > 7 days)
        open_positions = self.position_manager.get_all_positions(status="open", mode=mode)
        now = datetime.now(timezone.utc)
        for pos in open_positions:
            opened_dt = datetime.fromisoformat(pos.opened_at.replace('Z', '+00:00'))
            days_open = (now - opened_dt).days
            if days_open > 7:
                warnings.append(f"Stale position: {pos.position_id} open for {days_open} days")
        
        health = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mode': mode or "ALL",
            'status': 'OK' if not warnings else 'WARNING',
            'warnings': warnings,
            'metrics': {
                'position_count': summary['open_positions']['count'],
                'total_exposure': summary['open_positions']['total_cost'],
                'unrealized_pnl': summary['open_positions']['unrealized_pnl'],
                'realized_pnl': summary['closed_positions']['realized_pnl'],
                'total_pnl': summary['total_pnl']
            }
        }
        
        return health


# Example usage
if __name__ == "__main__":
    # Create tracker
    tracker = PortfolioTracker()
    
    # Add some test positions
    pm = tracker.position_manager
    
    pos1 = pm.add_position(
        market_id="market_1",
        market_name="Will BTC hit $100k by EOY?",
        side="YES",
        entry_price=0.45,
        quantity=100.0,
        mode="DRYRUN"
    )
    
    pos2 = pm.add_position(
        market_id="market_2",
        market_name="Will S&P 500 reach 5000?",
        side="NO",
        entry_price=0.70,
        quantity=50.0,
        mode="DRYRUN"
    )
    
    # Update prices
    pm.update_position_price(pos1.position_id, 0.55)
    pm.update_position_price(pos2.position_id, 0.65)
    
    # Get portfolio summary
    summary = tracker.get_portfolio_summary(mode="DRYRUN")
    print("\nPortfolio Summary:")
    print(f"Open positions: {summary['open_positions']['count']}")
    print(f"Total value: ${summary['open_positions']['total_value']:.2f}")
    print(f"Total cost: ${summary['open_positions']['total_cost']:.2f}")
    print(f"Unrealized P&L: ${summary['open_positions']['unrealized_pnl']:.2f} ({summary['open_positions']['unrealized_pnl_pct']:.2f}%)")
    
    # Check risk limits
    allowed, reason = tracker.check_risk_limits("market_1", 50.0, mode="DRYRUN")
    print(f"\nRisk check for $50 position in market_1: {reason}")
    
    # Health check
    health = tracker.get_portfolio_health_check(mode="DRYRUN")
    print(f"\nPortfolio health: {health['status']}")
    if health['warnings']:
        print("Warnings:")
        for warning in health['warnings']:
            print(f"  - {warning}")
