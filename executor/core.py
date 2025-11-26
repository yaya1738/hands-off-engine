"""
Executor Core for Hands-Off Engine

This module coordinates the complete execution pipeline:
- Receive signals from Decider
- Validate against Risk Model (via PreTradeValidator)
- Execute via Polymarket API (via ExecutionEngine)
- Confirm execution (via PostTradeProcessor)
- Monitor execution (via ExecutionMonitor)

This is the main entry point for order execution.
"""

import json
import sys
import os
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger
from executor.pretrade import PreTradeValidator
from executor.engine import ExecutionEngine
from executor.posttrade import PostTradeProcessor
from executor.monitor import ExecutionMonitor


class ExecutorCore:
    """
    Core executor coordinates the complete execution pipeline.
    
    Pipeline:
    1. Receive PlannedActions from Decider
    2. Pre-trade validation (safety checks)
    3. Order submission and execution
    4. Post-trade processing (position updates, notifications)
    5. Ongoing monitoring
    """
    
    def __init__(self, dryrun: bool = True, state_dir: Optional[Path] = None,
                 bankroll: float = 1000.0, enable_live: bool = False):
        """
        Initialize executor core.
        
        Args:
            dryrun: If True, no actual trades executed (default: True)
            state_dir: Directory for state files (defaults to ../state)
            bankroll: Total bankroll for risk checks
            enable_live: Explicit flag to enable live trading (default: False)
        """
        # SAFETY: Force dryrun unless explicitly enabled
        if not enable_live:
            dryrun = True
        
        if state_dir is None:
            state_dir = Path(__file__).parent.parent / "state"
        
        self.dryrun = dryrun
        self.state_dir = state_dir
        self.bankroll = bankroll
        
        # Initialize components
        self.validator = PreTradeValidator(state_dir=state_dir)
        self.engine = ExecutionEngine(dryrun=dryrun, state_dir=state_dir)
        self.posttrade = PostTradeProcessor(state_dir=state_dir)
        self.monitor = ExecutionMonitor(state_dir=state_dir)
        
        self.audit = get_audit_logger(component="executor.core")
        
        # Load kill switch state
        self.kill_switch_file = state_dir / "kill_switch.json"
        self._ensure_kill_switch_file()
    
    def _ensure_kill_switch_file(self):
        """Ensure kill switch file exists"""
        if not self.kill_switch_file.exists():
            self._save_kill_switch_state({"enabled": False, "reason": None, "timestamp": None})
    
    def _load_kill_switch_state(self) -> Dict:
        """Load kill switch state from file"""
        with open(self.kill_switch_file, 'r') as f:
            return json.load(f)
    
    def _save_kill_switch_state(self, state: Dict):
        """Save kill switch state to file"""
        with open(self.kill_switch_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def check_kill_switch(self) -> bool:
        """
        Check if kill switch is enabled.
        
        Returns:
            True if trading is stopped, False if allowed
        """
        state = self._load_kill_switch_state()
        return state.get("enabled", False)
    
    def enable_kill_switch(self, reason: str):
        """
        Enable kill switch to stop all trading.
        
        Args:
            reason: Reason for stopping trading
        """
        state = {
            "enabled": True,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._save_kill_switch_state(state)
        
        # Also trigger circuit breaker
        self.validator.trigger_circuit_breaker(reason)
        
        # Audit kill switch activation
        self.audit.log_action(
            action_type="kill_switch_enabled",
            action_data={"reason": reason},
            result="all_trading_stopped"
        )
    
    def disable_kill_switch(self):
        """Disable kill switch to allow trading."""
        state = {
            "enabled": False,
            "reason": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._save_kill_switch_state(state)
        
        # Also reset circuit breaker
        self.validator.reset_circuit_breaker()
        
        # Audit kill switch deactivation
        self.audit.log_action(
            action_type="kill_switch_disabled",
            action_data={},
            result="trading_enabled"
        )
    
    def execute_signals(self, planned_actions: List) -> Dict:
        """
        Execute planned actions through the complete pipeline.
        
        Args:
            planned_actions: List of PlannedAction objects from Decider
            
        Returns:
            Dict with execution summary
        """
        # Check kill switch
        if self.check_kill_switch():
            kill_switch_state = self._load_kill_switch_state()
            self.audit.log_action(
                action_type="execution_blocked",
                action_data={
                    "reason": "kill_switch",
                    "kill_switch_reason": kill_switch_state.get("reason")
                },
                result="rejected"
            )
            return {
                "status": "blocked",
                "reason": "kill_switch",
                "message": f"Trading stopped: {kill_switch_state.get('reason')}",
                "executed": [],
                "rejected": planned_actions
            }
        
        executed = []
        rejected = []
        
        # Log start of execution
        self.audit.log_action(
            action_type="execution_pipeline_start",
            action_data={
                "total_actions": len(planned_actions),
                "mode": "DRYRUN" if self.dryrun else "LIVE",
                "bankroll": self.bankroll
            },
            result="started"
        )
        
        for action in planned_actions:
            try:
                # Step 1: Pre-trade validation
                is_valid, check_results = self.validator.validate_trade(action, self.bankroll)
                
                if not is_valid:
                    # Validation failed
                    failed_checks = [r for r in check_results if not r.passed]
                    rejection_reasons = [r.message for r in failed_checks]
                    
                    rejected.append({
                        "action": action,
                        "reason": "validation_failed",
                        "details": rejection_reasons
                    })
                    
                    self.audit.log_action(
                        action_type="action_rejected",
                        action_data={
                            "market_id": action.market_id,
                            "amount": action.amount,
                            "rejection_reasons": rejection_reasons
                        },
                        result="rejected"
                    )
                    continue
                
                # Step 2: Submit and execute order
                order = self.engine.submit_order(action)
                result = self.engine.execute_order(order)
                
                # Step 3: Post-trade processing
                self.posttrade.process_execution(order, result)
                
                # Track result
                executed.append({
                    "action": action,
                    "order": order,
                    "result": result
                })
                
            except Exception as e:
                # Handle unexpected errors
                self.audit.log_error(
                    error_type="execution_error",
                    error_message=str(e),
                    context={
                        "market_id": action.market_id,
                        "amount": action.amount
                    }
                )
                
                rejected.append({
                    "action": action,
                    "reason": "exception",
                    "details": str(e)
                })
        
        # Step 4: Monitor execution quality
        quality = self.monitor.check_execution_quality()
        
        # Build summary
        summary = {
            "status": "complete",
            "mode": "DRYRUN" if self.dryrun else "LIVE",
            "total_actions": len(planned_actions),
            "executed_count": len(executed),
            "rejected_count": len(rejected),
            "executed": executed,
            "rejected": rejected,
            "quality_alerts": quality.get("alerts", []),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Log completion
        self.audit.log_action(
            action_type="execution_pipeline_complete",
            action_data={
                "total_actions": len(planned_actions),
                "executed": len(executed),
                "rejected": len(rejected),
                "mode": "DRYRUN" if self.dryrun else "LIVE"
            },
            result="complete"
        )
        
        return summary
    
    def get_status(self) -> Dict:
        """
        Get current executor status.
        
        Returns:
            Dict with status information
        """
        # Get component statuses
        pending = self.monitor.get_pending_summary()
        quality = self.monitor.check_execution_quality()
        positions = self.posttrade.get_position_summary()
        kill_switch = self._load_kill_switch_state()
        circuit_breaker = self.validator.check_circuit_breaker()
        
        status = {
            "mode": "DRYRUN" if self.dryrun else "LIVE",
            "kill_switch": kill_switch,
            "circuit_breaker": {
                "triggered": not circuit_breaker.passed,
                "message": circuit_breaker.message
            },
            "pending_orders": pending,
            "execution_quality": quality,
            "positions": positions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return status


# Example usage
if __name__ == "__main__":
    from decider.ho_decider import PlannedAction
    
    # Initialize executor (DRYRUN by default)
    executor = ExecutorCore(dryrun=True, bankroll=1000.0)
    
    # Check status
    status = executor.get_status()
    print(f"\nExecutor Status:")
    print(f"  Mode: {status['mode']}")
    print(f"  Kill Switch: {'ENABLED' if status['kill_switch']['enabled'] else 'disabled'}")
    print(f"  Circuit Breaker: {'TRIGGERED' if status['circuit_breaker']['triggered'] else 'ok'}")
    print(f"  Pending Orders: {status['pending_orders']['total_pending']}")
    
    # Create test actions
    actions = [
        PlannedAction(
            market_id="test_market_1",
            market_name="Test Market 1",
            side="YES",
            amount=50.0,
            confidence=0.85,
            reasoning="Test action 1"
        ),
        PlannedAction(
            market_id="test_market_2",
            market_name="Test Market 2",
            side="NO",
            amount=30.0,
            confidence=0.75,
            reasoning="Test action 2"
        ),
    ]
    
    # Execute signals
    print("\nExecuting signals...")
    summary = executor.execute_signals(actions)
    
    print(f"\nExecution Summary:")
    print(f"  Status: {summary['status']}")
    print(f"  Mode: {summary['mode']}")
    print(f"  Total Actions: {summary['total_actions']}")
    print(f"  Executed: {summary['executed_count']}")
    print(f"  Rejected: {summary['rejected_count']}")
    
    if summary['quality_alerts']:
        print(f"\nQuality Alerts:")
        for alert in summary['quality_alerts']:
            print(f"  - {alert['type']}: {alert['message']}")
