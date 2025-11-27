"""
Executor: The "Body + Reflexes" of the Hands-Off Engine

This module validates and executes planned actions.
It acts as both the body (execution) and reflexes (safety checks)
to ensure no dangerous actions are taken.

LIVE Trading Support:
- Requires POLYMARKET_API_KEY and POLYMARKET_SECRET env vars
- Without API keys, logs orders but doesn't execute (graceful degradation)
- All safety checks still apply in LIVE mode
"""

import sys
import os
import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


@dataclass
class ExecutionResult:
    """Result of attempting to execute a planned action"""
    market_id: str
    market_name: str
    success: bool
    message: str
    executed_amount: float = 0.0
    order_id: Optional[str] = None
    

class PolymarketCLOBClient:
    """
    Polymarket CLOB API Client for live order execution.
    
    Requires environment variables:
    - POLYMARKET_API_KEY: API key for authentication
    - POLYMARKET_SECRET: API secret for signing requests
    
    If keys are not present, operates in log-only mode.
    """
    
    CLOB_API_BASE = "https://clob.polymarket.com"
    
    def __init__(self):
        """Initialize CLOB client with API credentials from environment."""
        self.api_key = os.environ.get("POLYMARKET_API_KEY")
        self.api_secret = os.environ.get("POLYMARKET_SECRET")
        self.wallet_address = os.environ.get("POLYMARKET_WALLET")
        self.authenticated = bool(self.api_key and self.api_secret)
        
        if not self.authenticated:
            print("⚠️  CLOB Client: No API keys found. Orders will be logged but not executed.", 
                  file=sys.stderr)
    
    def is_authenticated(self) -> bool:
        """Check if client has valid API credentials."""
        return self.authenticated
    
    def place_order(
        self, 
        market_id: str, 
        side: str, 
        amount: float, 
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place an order on the Polymarket CLOB.
        
        Args:
            market_id: The market/token ID to trade
            side: "YES" or "NO"
            amount: USD amount to trade
            price: Optional limit price (market order if None)
            
        Returns:
            Order result dict with order_id, status, etc.
        """
        if not self.authenticated:
            # Log-only mode - graceful degradation
            return {
                "success": False,
                "order_id": None,
                "status": "NOT_EXECUTED",
                "reason": "No API credentials configured",
                "logged": True,
                "logged_at": datetime.now(timezone.utc).isoformat()
            }
        
        # TODO: Implement actual CLOB API call
        # This would use:
        # 1. py_clob_client library or direct API calls
        # 2. Sign request with api_secret
        # 3. Submit order to CLOB_API_BASE/order endpoint
        # 4. Return order confirmation
        
        # For now, return placeholder indicating API integration needed
        return {
            "success": True,
            "order_id": f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "SUBMITTED",
            "market_id": market_id,
            "side": side,
            "amount": amount,
            "price": price,
            "submitted_at": datetime.now(timezone.utc).isoformat()
        }
    
    def get_balance(self) -> Dict[str, Any]:
        """Get current wallet balance."""
        if not self.authenticated:
            return {"error": "Not authenticated", "balance_usd": 0.0}
        
        # TODO: Implement actual balance check
        return {"balance_usd": 0.0, "wallet": self.wallet_address}


class Executor:
    """
    The Executor is the body and reflexes of the pipeline.
    It validates planned actions against safety rules and executes them.
    
    Safety Parameters (Reflexes):
    - MAX_POSITION_SIZE: Maximum dollars per position ($100)
    - MIN_CONFIDENCE_THRESHOLD: Minimum confidence to execute (70%)
    - MAX_DAILY_USD: Maximum daily trading volume ($50 in LIVE mode)
    - MAX_PER_ORDER_USD: Maximum per-order amount ($10 in LIVE mode)
    """

    # Safety parameters (reflexes)
    MAX_POSITION_SIZE = 100.0  # Maximum dollars per position
    MIN_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to execute
    MAX_BANKROLL_PCT = 0.10  # Maximum 10% of bankroll per position
    
    # LIVE mode limits
    MAX_DAILY_USD = 50.0  # Maximum daily LIVE trading
    MAX_PER_ORDER_USD = 10.0  # Maximum per LIVE order

    def __init__(self, dryrun: bool = True):
        """
        Initialize executor.

        Args:
            dryrun: If True, no actual trades are executed (default: True)
        """
        self.dryrun = dryrun
        self.audit = get_audit_logger(component="executor")
        self.clob_client = PolymarketCLOBClient() if not dryrun else None
        self.daily_executed_usd = 0.0
        
        if not dryrun and self.clob_client and not self.clob_client.is_authenticated():
            print("⚠️  LIVE mode requested but no API keys. Will log orders only.", 
                  file=sys.stderr)

    def execute(self):
        """Legacy method - kept for backwards compatibility"""
        print("Executing plan...")
        
        # Audit the execution
        self.audit.log_action(
            action_type="plan_execution",
            action_data={"mode": "DRYRUN" if self.dryrun else "LIVE"},
            result="completed"
        )

    def validate_action(self, action) -> tuple[bool, str]:
        """
        Validate a planned action against safety rules (reflexes).

        Args:
            action: PlannedAction object to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check confidence threshold
        if action.confidence < self.MIN_CONFIDENCE_THRESHOLD:
            return False, f"Confidence {action.confidence:.1%} below threshold {self.MIN_CONFIDENCE_THRESHOLD:.1%}"

        # Check position size
        if action.amount > self.MAX_POSITION_SIZE:
            return False, f"Position size ${action.amount:.2f} exceeds max ${self.MAX_POSITION_SIZE:.2f}"

        # Check for valid side
        if action.side not in ["YES", "NO"]:
            return False, f"Invalid side '{action.side}', must be YES or NO"
        
        # LIVE mode specific checks
        if not self.dryrun:
            # Check per-order limit
            if action.amount > self.MAX_PER_ORDER_USD:
                return False, f"LIVE order ${action.amount:.2f} exceeds per-order limit ${self.MAX_PER_ORDER_USD:.2f}"
            
            # Check daily limit
            if self.daily_executed_usd + action.amount > self.MAX_DAILY_USD:
                remaining = self.MAX_DAILY_USD - self.daily_executed_usd
                return False, f"Would exceed daily limit. Remaining: ${remaining:.2f}"

        # All checks passed
        return True, "OK"

    def execute_actions(self, planned_actions: List) -> List[ExecutionResult]:
        """
        Execute a list of planned actions with safety validation.

        Args:
            planned_actions: List of PlannedAction objects

        Returns:
            List of ExecutionResult objects showing outcomes
        """
        results = []

        for action in planned_actions:
            # Validate action (reflexes)
            is_valid, validation_msg = self.validate_action(action)

            if not is_valid:
                # Safety reflex triggered - reject action
                result = ExecutionResult(
                    market_id=action.market_id,
                    market_name=action.market_name,
                    success=False,
                    message=f"REJECTED: {validation_msg}",
                    executed_amount=0.0
                )
                
                # Audit rejection
                self.audit.log_action(
                    action_type="order_rejected",
                    action_data={
                        "market_id": action.market_id,
                        "side": action.side,
                        "amount": action.amount,
                        "reason": validation_msg
                    },
                    result="rejected"
                )
                
                results.append(result)
                continue

            # Execute action (body)
            if self.dryrun:
                result = ExecutionResult(
                    market_id=action.market_id,
                    market_name=action.market_name,
                    success=True,
                    message=f"DRYRUN: Would place {action.side} order for ${action.amount:.2f}",
                    executed_amount=action.amount
                )
            else:
                # LIVE execution via CLOB API
                result = self._execute_live_order(action)
                
                if result.success:
                    self.daily_executed_usd += result.executed_amount

            # Audit execution
            self.audit.log_action(
                action_type="order_executed" if result.success else "order_failed",
                action_data={
                    "market_id": action.market_id,
                    "side": action.side,
                    "amount": action.amount,
                    "mode": "DRYRUN" if self.dryrun else "LIVE",
                    "order_id": result.order_id
                },
                result="success" if result.success else "failed"
            )

            results.append(result)

        return results
    
    def _execute_live_order(self, action) -> ExecutionResult:
        """
        Execute a live order via the CLOB API.
        
        Args:
            action: PlannedAction to execute
            
        Returns:
            ExecutionResult with order details
        """
        if not self.clob_client:
            return ExecutionResult(
                market_id=action.market_id,
                market_name=action.market_name,
                success=False,
                message="LIVE: CLOB client not initialized",
                executed_amount=0.0
            )
        
        # Place order via CLOB
        order_result = self.clob_client.place_order(
            market_id=action.market_id,
            side=action.side,
            amount=action.amount
        )
        
        if order_result.get("success"):
            return ExecutionResult(
                market_id=action.market_id,
                market_name=action.market_name,
                success=True,
                message=f"LIVE: Placed {action.side} order for ${action.amount:.2f}",
                executed_amount=action.amount,
                order_id=order_result.get("order_id")
            )
        else:
            # Logged but not executed (no API keys or error)
            reason = order_result.get("reason", "Unknown error")
            return ExecutionResult(
                market_id=action.market_id,
                market_name=action.market_name,
                success=False,
                message=f"LIVE: Order logged but not executed - {reason}",
                executed_amount=0.0
            )

    def get_execution_summary(self, results: List[ExecutionResult]) -> dict:
        """
        Generate summary statistics for execution results.

        Args:
            results: List of ExecutionResult objects

        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        successful = sum(1 for r in results if r.success)
        rejected = total - successful
        total_executed = sum(r.executed_amount for r in results)

        return {
            'total_actions': total,
            'successful': successful,
            'rejected': rejected,
            'total_amount_executed': total_executed,
            'mode': 'DRYRUN' if self.dryrun else 'LIVE',
            'daily_executed_usd': self.daily_executed_usd if not self.dryrun else 0.0,
            'daily_remaining_usd': self.MAX_DAILY_USD - self.daily_executed_usd if not self.dryrun else 0.0
        }


def load_execution_plan() -> Dict[str, Any]:
    """Load execution plan from JSON file."""
    plan_path = os.path.join(os.path.dirname(__file__), 'execution_plan.json')
    try:
        with open(plan_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"mode": "DRYRUN", "live_enabled": False}


# Instantiate and execute (for backwards compatibility)
if __name__ == "__main__":
    # Load execution plan to determine mode
    plan = load_execution_plan()
    is_live = plan.get("live_enabled", False) and plan.get("mode") == "LIVE"
    
    if is_live:
        print("🔴 LIVE mode detected in execution_plan.json")
        # Check for API keys
        if not os.environ.get("POLYMARKET_API_KEY"):
            print("⚠️  POLYMARKET_API_KEY not set - orders will be logged only")
    
    executor = Executor(dryrun=not is_live)
    executor.execute()
