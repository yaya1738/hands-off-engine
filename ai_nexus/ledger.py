"""
Action Ledger - Financial and operational tracking for AI Nexus

Maintains an immutable ledger of all AI operations, costs, and outcomes
for accountability, budgeting, and self-financing capabilities.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Import audit logger
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from audit import get_audit_logger
    audit = get_audit_logger(component="ai_nexus.ledger")
except ImportError:
    audit = None


@dataclass
class LedgerEntry:
    """Single entry in the action ledger"""
    timestamp: str
    entry_type: str  # ai_task, trade, decision, etc.
    action: str
    cost: float = 0.0
    revenue: float = 0.0
    profit: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        self.profit = self.revenue - self.cost
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class ActionLedger:
    """
    Immutable ledger tracking all operations and their financial impact.
    
    Enables:
    - Complete accountability for all actions
    - Cost tracking and budget enforcement
    - Revenue attribution
    - ROI calculation for self-financing
    - Audit trail for financial operations
    """
    
    def __init__(self, ledger_dir: Optional[str] = None):
        """
        Initialize Action Ledger
        
        Args:
            ledger_dir: Directory for ledger files
        """
        if ledger_dir is None:
            # Try ~/hands-off/ledger first, fall back to local
            home_ledger = Path.home() / "hands-off" / "ledger"
            if Path.home() / "hands-off" in [p for p in Path.home().iterdir() if p.is_dir()]:
                ledger_dir = str(home_ledger)
            else:
                ledger_dir = str(Path(__file__).parent.parent / "logs" / "ledger")
        
        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        
        # Current date for daily ledger files
        self._current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._ledger_file = self._get_ledger_file()
        
        # Audit ledger initialization
        if audit:
            audit.log_action(
                action_type="ledger_initialized",
                action_data={
                    "ledger_dir": str(self.ledger_dir),
                    "current_date": self._current_date
                },
                result="success"
            )
    
    def _get_ledger_file(self) -> Path:
        """Get the current ledger file path based on date"""
        return self.ledger_dir / f"ledger_{self._current_date}.jsonl"
    
    def _ensure_ledger_file(self):
        """Ensure ledger file exists and check for date rotation"""
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if current_date != self._current_date:
            self._current_date = current_date
            self._ledger_file = self._get_ledger_file()
    
    def record(self, entry: LedgerEntry) -> bool:
        """
        Record an entry to the ledger
        
        Args:
            entry: LedgerEntry to record
            
        Returns:
            bool: True if successful
        """
        self._ensure_ledger_file()
        
        try:
            with open(self._ledger_file, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
            
            # Audit ledger write
            if audit:
                audit.log_action(
                    action_type="ledger_entry_recorded",
                    action_data={
                        "entry_type": entry.entry_type,
                        "action": entry.action,
                        "cost": entry.cost,
                        "revenue": entry.revenue,
                        "profit": entry.profit
                    },
                    result="success"
                )
            
            return True
            
        except Exception as e:
            if audit:
                audit.log_error(
                    error_type="LedgerWriteError",
                    error_message=str(e),
                    context={"file": str(self._ledger_file)}
                )
            return False
    
    def record_ai_task(self, task_id: str, provider: str, cost: float, 
                      tokens: int, success: bool, metadata: Optional[Dict] = None):
        """Record an AI task execution"""
        entry = LedgerEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry_type="ai_task",
            action=f"AI task via {provider}",
            cost=cost,
            revenue=0.0,
            metadata={
                "task_id": task_id,
                "provider": provider,
                "tokens": tokens,
                "success": success,
                **(metadata or {})
            }
        )
        return self.record(entry)
    
    def record_trade(self, market: str, side: str, size: float, 
                    price: float, profit: float, metadata: Optional[Dict] = None):
        """Record a trading operation"""
        entry = LedgerEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry_type="trade",
            action=f"Trade: {side} {size} {market} @ {price}",
            cost=size * price if side == "BUY" else 0.0,
            revenue=size * price if side == "SELL" else 0.0,
            profit=profit,
            metadata={
                "market": market,
                "side": side,
                "size": size,
                "price": price,
                **(metadata or {})
            }
        )
        return self.record(entry)
    
    def record_decision(self, decision_type: str, cost: float = 0.0, 
                       expected_value: float = 0.0, metadata: Optional[Dict] = None):
        """Record a decision-making operation"""
        entry = LedgerEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry_type="decision",
            action=f"Decision: {decision_type}",
            cost=cost,
            revenue=0.0,
            metadata={
                "decision_type": decision_type,
                "expected_value": expected_value,
                **(metadata or {})
            }
        )
        return self.record(entry)
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get financial summary for a specific day
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Dictionary with cost, revenue, profit by category
        """
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        ledger_file = self.ledger_dir / f"ledger_{date}.jsonl"
        
        summary = {
            "date": date,
            "total_cost": 0.0,
            "total_revenue": 0.0,
            "total_profit": 0.0,
            "by_type": {},
            "entry_count": 0
        }
        
        if not ledger_file.exists():
            return summary
        
        try:
            with open(ledger_file, 'r') as f:
                for line in f:
                    entry_dict = json.loads(line.strip())
                    entry_type = entry_dict.get('entry_type', 'unknown')
                    cost = entry_dict.get('cost', 0.0)
                    revenue = entry_dict.get('revenue', 0.0)
                    profit = entry_dict.get('profit', 0.0)
                    
                    # Update totals
                    summary['total_cost'] += cost
                    summary['total_revenue'] += revenue
                    summary['total_profit'] += profit
                    summary['entry_count'] += 1
                    
                    # Update by type
                    if entry_type not in summary['by_type']:
                        summary['by_type'][entry_type] = {
                            'cost': 0.0,
                            'revenue': 0.0,
                            'profit': 0.0,
                            'count': 0
                        }
                    
                    summary['by_type'][entry_type]['cost'] += cost
                    summary['by_type'][entry_type]['revenue'] += revenue
                    summary['by_type'][entry_type]['profit'] += profit
                    summary['by_type'][entry_type]['count'] += 1
        
        except Exception as e:
            if audit:
                audit.log_error(
                    error_type="LedgerReadError",
                    error_message=str(e),
                    context={"file": str(ledger_file)}
                )
        
        return summary
    
    def get_period_summary(self, start_date: str, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get financial summary for a date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today
            
        Returns:
            Aggregated summary across date range
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Get all ledger files in range
        from datetime import timedelta
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        period_summary = {
            "start_date": start_date,
            "end_date": end_date,
            "total_cost": 0.0,
            "total_revenue": 0.0,
            "total_profit": 0.0,
            "by_type": {},
            "entry_count": 0,
            "daily_summaries": []
        }
        
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            daily = self.get_daily_summary(date_str)
            
            if daily['entry_count'] > 0:
                period_summary['daily_summaries'].append(daily)
                period_summary['total_cost'] += daily['total_cost']
                period_summary['total_revenue'] += daily['total_revenue']
                period_summary['total_profit'] += daily['total_profit']
                period_summary['entry_count'] += daily['entry_count']
                
                # Merge by_type
                for entry_type, stats in daily['by_type'].items():
                    if entry_type not in period_summary['by_type']:
                        period_summary['by_type'][entry_type] = {
                            'cost': 0.0,
                            'revenue': 0.0,
                            'profit': 0.0,
                            'count': 0
                        }
                    period_summary['by_type'][entry_type]['cost'] += stats['cost']
                    period_summary['by_type'][entry_type]['revenue'] += stats['revenue']
                    period_summary['by_type'][entry_type]['profit'] += stats['profit']
                    period_summary['by_type'][entry_type]['count'] += stats['count']
            
            current += timedelta(days=1)
        
        return period_summary
    
    def calculate_roi(self, start_date: str, end_date: Optional[str] = None) -> float:
        """
        Calculate ROI for a period
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today
            
        Returns:
            ROI as percentage
        """
        summary = self.get_period_summary(start_date, end_date)
        
        if summary['total_cost'] == 0:
            return 0.0
        
        roi = (summary['total_profit'] / summary['total_cost']) * 100
        return roi


# Example usage
if __name__ == "__main__":
    print("Action Ledger - Financial Tracking System")
    print("=" * 70)
    
    # Initialize ledger
    ledger = ActionLedger()
    print(f"✓ Ledger initialized")
    print(f"  Directory: {ledger.ledger_dir}")
    print()
    
    # Record some example entries
    print("Recording example entries...")
    
    # AI task cost
    ledger.record_ai_task(
        task_id="task123",
        provider="copilot",
        cost=2.50,
        tokens=5000,
        success=True
    )
    print("✓ AI task recorded: $2.50 cost")
    
    # Simulated trade profit
    ledger.record_trade(
        market="btc_100k_eoy",
        side="SELL",
        size=100.0,
        price=0.35,
        profit=15.0,
        metadata={"strategy": "edge_based"}
    )
    print("✓ Trade recorded: $15.00 profit")
    
    # Decision cost
    ledger.record_decision(
        decision_type="bet_sizing",
        cost=0.10,
        expected_value=50.0
    )
    print("✓ Decision recorded: $0.10 cost, $50.00 EV")
    print()
    
    # Get daily summary
    summary = ledger.get_daily_summary()
    print("Daily Summary:")
    print(f"  Entries: {summary['entry_count']}")
    print(f"  Total Cost: ${summary['total_cost']:.2f}")
    print(f"  Total Revenue: ${summary['total_revenue']:.2f}")
    print(f"  Total Profit: ${summary['total_profit']:.2f}")
    print()
    
    print("By Type:")
    for entry_type, stats in summary['by_type'].items():
        print(f"  {entry_type}:")
        print(f"    Count: {stats['count']}")
        print(f"    Cost: ${stats['cost']:.2f}")
        print(f"    Revenue: ${stats['revenue']:.2f}")
        print(f"    Profit: ${stats['profit']:.2f}")
    print()
    
    print(f"Ledger file: {ledger._ledger_file}")
