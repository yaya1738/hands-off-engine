"""
P&L Calculator for Hands-Off Engine

Calculates and tracks profit and loss metrics:
- Realized P&L from closed positions
- Unrealized P&L from open positions
- P&L by market, by day, by strategy
- Historical P&L tracking
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger
from portfolio.positions import Position, PositionManager


class PnLCalculator:
    """
    Calculates and tracks P&L across multiple dimensions:
    - Realized vs unrealized
    - By market
    - By day
    - By mode (DRYRUN vs LIVE)
    """
    
    def __init__(self, position_manager: Optional[PositionManager] = None,
                 state_dir: Optional[Path] = None):
        """
        Initialize P&L calculator.
        
        Args:
            position_manager: PositionManager instance (creates new if None)
            state_dir: Directory for state files (defaults to ./state/portfolio)
        """
        self.position_manager = position_manager or PositionManager()
        
        if state_dir is None:
            repo_root = Path(__file__).parent.parent
            state_dir = repo_root / "state" / "portfolio"
        
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.pnl_daily_file = self.state_dir / "pnl_daily.json"
        
        self.audit = get_audit_logger(component="pnl_calculator")
    
    def calculate_realized_pnl(self, mode: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> float:
        """
        Calculate total realized P&L from closed positions.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            
        Returns:
            Total realized P&L in dollars
        """
        closed_positions = self.position_manager.get_all_positions(status="closed", mode=mode)
        
        # Filter by date if specified
        if start_date or end_date:
            filtered_positions = []
            for pos in closed_positions:
                if pos.closed_at:
                    closed_dt = datetime.fromisoformat(pos.closed_at.replace('Z', '+00:00'))
                    if start_date and closed_dt < start_date:
                        continue
                    if end_date and closed_dt > end_date:
                        continue
                    filtered_positions.append(pos)
            closed_positions = filtered_positions
        
        return sum(pos.realized_pnl or 0 for pos in closed_positions)
    
    def calculate_unrealized_pnl(self, mode: Optional[str] = None) -> float:
        """
        Calculate total unrealized P&L from open positions.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Total unrealized P&L in dollars
        """
        open_positions = self.position_manager.get_all_positions(status="open", mode=mode)
        return sum(pos.unrealized_pnl for pos in open_positions)
    
    def calculate_total_pnl(self, mode: Optional[str] = None) -> float:
        """
        Calculate total P&L (realized + unrealized).
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Total P&L in dollars
        """
        return self.calculate_realized_pnl(mode=mode) + self.calculate_unrealized_pnl(mode=mode)
    
    def calculate_pnl_by_market(self, mode: Optional[str] = None) -> Dict[str, Dict]:
        """
        Calculate P&L breakdown by market.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Dictionary mapping market_id to P&L metrics
        """
        all_positions = self.position_manager.get_all_positions(mode=mode)
        
        pnl_by_market = defaultdict(lambda: {
            'realized_pnl': 0.0,
            'unrealized_pnl': 0.0,
            'total_pnl': 0.0,
            'open_positions': 0,
            'closed_positions': 0,
            'total_invested': 0.0,
            'current_value': 0.0
        })
        
        for pos in all_positions:
            market_data = pnl_by_market[pos.market_id]
            market_data['total_invested'] += pos.entry_amount
            
            if pos.status == "open":
                market_data['unrealized_pnl'] += pos.unrealized_pnl
                market_data['current_value'] += pos.current_value
                market_data['open_positions'] += 1
            else:
                market_data['realized_pnl'] += pos.realized_pnl or 0
                market_data['closed_positions'] += 1
            
            market_data['total_pnl'] = market_data['realized_pnl'] + market_data['unrealized_pnl']
        
        # Add market names
        for market_id, data in pnl_by_market.items():
            positions = self.position_manager.get_positions_by_market(market_id)
            if positions:
                data['market_name'] = positions[0].market_name
        
        return dict(pnl_by_market)
    
    def calculate_pnl_by_day(self, mode: Optional[str] = None,
                            days: int = 30) -> Dict[str, Dict]:
        """
        Calculate daily P&L for the last N days.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            days: Number of days to look back
            
        Returns:
            Dictionary mapping date (YYYY-MM-DD) to daily P&L metrics
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        daily_pnl = {}
        
        # Initialize all days
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_pnl[date_str] = {
                'date': date_str,
                'realized_pnl': 0.0,
                'positions_opened': 0,
                'positions_closed': 0,
                'net_invested': 0.0
            }
            current_date += timedelta(days=1)
        
        # Calculate realized P&L from closed positions
        closed_positions = self.position_manager.get_all_positions(status="closed", mode=mode)
        for pos in closed_positions:
            if pos.closed_at:
                closed_dt = datetime.fromisoformat(pos.closed_at.replace('Z', '+00:00'))
                if closed_dt >= start_date:
                    date_str = closed_dt.strftime('%Y-%m-%d')
                    if date_str in daily_pnl:
                        daily_pnl[date_str]['realized_pnl'] += pos.realized_pnl or 0
                        daily_pnl[date_str]['positions_closed'] += 1
        
        # Track positions opened
        all_positions = self.position_manager.get_all_positions(mode=mode)
        for pos in all_positions:
            opened_dt = datetime.fromisoformat(pos.opened_at.replace('Z', '+00:00'))
            if opened_dt >= start_date:
                date_str = opened_dt.strftime('%Y-%m-%d')
                if date_str in daily_pnl:
                    daily_pnl[date_str]['positions_opened'] += 1
                    daily_pnl[date_str]['net_invested'] += pos.entry_amount
        
        return daily_pnl
    
    def get_pnl_report(self, mode: Optional[str] = None) -> Dict:
        """
        Generate comprehensive P&L report.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Dictionary with comprehensive P&L metrics
        """
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mode': mode or "ALL",
            'summary': {
                'realized_pnl': self.calculate_realized_pnl(mode=mode),
                'unrealized_pnl': self.calculate_unrealized_pnl(mode=mode),
                'total_pnl': self.calculate_total_pnl(mode=mode)
            },
            'by_market': self.calculate_pnl_by_market(mode=mode),
            'recent_days': {}
        }
        
        # Add recent daily P&L (last 7 days)
        daily_pnl = self.calculate_pnl_by_day(mode=mode, days=7)
        recent_dates = sorted(daily_pnl.keys())[-7:]
        for date in recent_dates:
            report['recent_days'][date] = daily_pnl[date]
        
        # Log report generation
        self.audit.log_action(
            action_type="pnl_report_generated",
            action_data={
                'mode': mode or "ALL",
                'total_pnl': report['summary']['total_pnl'],
                'realized_pnl': report['summary']['realized_pnl'],
                'unrealized_pnl': report['summary']['unrealized_pnl']
            },
            result="success"
        )
        
        return report
    
    def save_daily_snapshot(self, mode: Optional[str] = None) -> None:
        """
        Save daily P&L snapshot to state file.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
        """
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        snapshot = {
            'date': today,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mode': mode or "ALL",
            'realized_pnl': self.calculate_realized_pnl(mode=mode),
            'unrealized_pnl': self.calculate_unrealized_pnl(mode=mode),
            'total_pnl': self.calculate_total_pnl(mode=mode),
            'by_market': self.calculate_pnl_by_market(mode=mode)
        }
        
        # Load existing snapshots
        snapshots = {}
        if self.pnl_daily_file.exists():
            try:
                with open(self.pnl_daily_file, 'r') as f:
                    data = json.load(f)
                    snapshots = data.get('snapshots', {})
            except Exception as e:
                import sys
                print(f"[PnLCalculator] Warning: Failed to load daily snapshots: {e}", file=sys.stderr)
        
        # Add today's snapshot
        snapshots[today] = snapshot
        
        # Keep only last 90 days
        sorted_dates = sorted(snapshots.keys())
        if len(sorted_dates) > 90:
            for old_date in sorted_dates[:-90]:
                del snapshots[old_date]
        
        # Save atomically
        data = {
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'snapshots': snapshots
        }
        
        tmp_file = self.pnl_daily_file.with_suffix('.json.tmp')
        try:
            with open(tmp_file, 'w') as f:
                json.dump(data, f, indent=2)
            tmp_file.replace(self.pnl_daily_file)
        except Exception as e:
            import sys
            print(f"[PnLCalculator] Error: Failed to save daily snapshot: {e}", file=sys.stderr)
            if tmp_file.exists():
                tmp_file.unlink()
            raise
        
        # Log snapshot
        self.audit.log_action(
            action_type="pnl_daily_snapshot",
            action_data={
                'date': today,
                'mode': mode or "ALL",
                'total_pnl': snapshot['total_pnl']
            },
            result="success"
        )
    
    def get_historical_snapshots(self, days: int = 30) -> List[Dict]:
        """
        Get historical daily snapshots.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of daily snapshots, sorted by date
        """
        if not self.pnl_daily_file.exists():
            return []
        
        try:
            with open(self.pnl_daily_file, 'r') as f:
                data = json.load(f)
                snapshots = data.get('snapshots', {})
            
            # Get last N days
            sorted_dates = sorted(snapshots.keys())[-days:]
            return [snapshots[date] for date in sorted_dates]
            
        except Exception as e:
            import sys
            print(f"[PnLCalculator] Warning: Failed to load historical snapshots: {e}", file=sys.stderr)
            return []
    
    def get_best_and_worst_positions(self, mode: Optional[str] = None,
                                     n: int = 5) -> Dict[str, List[Position]]:
        """
        Get best and worst performing positions.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            n: Number of positions to return for each category
            
        Returns:
            Dictionary with 'best' and 'worst' position lists
        """
        all_positions = self.position_manager.get_all_positions(mode=mode)
        
        # Calculate P&L for each position
        positions_with_pnl = []
        for pos in all_positions:
            if pos.status == "open":
                pnl = pos.unrealized_pnl
            else:
                pnl = pos.realized_pnl or 0
            positions_with_pnl.append((pos, pnl))
        
        # Sort by P&L
        positions_with_pnl.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'best': [pos for pos, _ in positions_with_pnl[:n]],
            'worst': [pos for pos, _ in positions_with_pnl[-n:][::-1]]
        }


# Example usage
if __name__ == "__main__":
    from portfolio.tracker import PortfolioTracker
    
    # Create calculator
    calc = PnLCalculator()
    tracker = PortfolioTracker(position_manager=calc.position_manager)
    pm = calc.position_manager
    
    # Add and close some test positions
    pos1 = pm.add_position(
        market_id="market_1",
        market_name="Test Market 1",
        side="YES",
        entry_price=0.50,
        quantity=100.0,
        mode="DRYRUN"
    )
    pm.update_position_price(pos1.position_id, 0.60)
    pm.close_position(pos1.position_id, 0.65)
    
    pos2 = pm.add_position(
        market_id="market_2",
        market_name="Test Market 2",
        side="NO",
        entry_price=0.70,
        quantity=50.0,
        mode="DRYRUN"
    )
    pm.update_position_price(pos2.position_id, 0.75)
    
    # Generate P&L report
    report = calc.get_pnl_report(mode="DRYRUN")
    
    print("\nP&L Report:")
    print(f"Realized P&L: ${report['summary']['realized_pnl']:.2f}")
    print(f"Unrealized P&L: ${report['summary']['unrealized_pnl']:.2f}")
    print(f"Total P&L: ${report['summary']['total_pnl']:.2f}")
    
    print("\nP&L by Market:")
    for market_id, data in report['by_market'].items():
        print(f"  {market_id}: ${data['total_pnl']:.2f} (realized: ${data['realized_pnl']:.2f}, unrealized: ${data['unrealized_pnl']:.2f})")
    
    # Save daily snapshot
    calc.save_daily_snapshot(mode="DRYRUN")
    print(f"\nDaily snapshot saved to: {calc.pnl_daily_file}")
    
    # Get best/worst positions
    best_worst = calc.get_best_and_worst_positions(mode="DRYRUN", n=3)
    print(f"\nBest performing positions: {len(best_worst['best'])}")
    print(f"Worst performing positions: {len(best_worst['worst'])}")
