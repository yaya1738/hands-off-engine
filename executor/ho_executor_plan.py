"""
Executor: The "Body + Reflexes" of the Hands-Off Engine

This module validates and executes planned actions.
It acts as both the body (execution) and reflexes (safety checks)
to ensure no dangerous actions are taken.
"""

import sys
import os
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger

# Polymarket CLOB client import (optional - only needed for LIVE trading)
try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import OrderArgs, OrderType
    CLOB_AVAILABLE = True
except ImportError:
    CLOB_AVAILABLE = False
    ClobClient = None


# Polymarket API configuration
POLYMARKET_HOST = "https://clob.polymarket.com"
POLYGON_CHAIN_ID = 137  # Polygon mainnet


@dataclass
class ExecutionResult:
    """Result of attempting to execute a planned action"""
    market_id: str
    market_name: str
    success: bool
    message: str
    executed_amount: float = 0.0
    order_id: Optional[str] = None


def get_polymarket_credentials() -> tuple[Optional[str], Optional[str]]:
    """
    Get Polymarket API credentials from environment variables.
    
    Returns:
        Tuple of (api_key, secret) or (None, None) if not configured
    """
    api_key = os.environ.get('POLYMARKET_API_KEY')
    secret = os.environ.get('POLYMARKET_SECRET')
    return api_key, secret


def validate_live_trading_prerequisites() -> tuple[bool, str]:
    """
    Validate that all prerequisites for live trading are met.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not CLOB_AVAILABLE:
        return False, "py-clob-client not installed. Run: pip install py-clob-client"
    
    api_key, secret = get_polymarket_credentials()
    if not api_key:
        return False, "POLYMARKET_API_KEY environment variable not set"
    if not secret:
        return False, "POLYMARKET_SECRET environment variable not set"
    
    return True, "OK"


class Executor:
    """
    The Executor is the body and reflexes of the pipeline.
    It validates planned actions against safety rules and executes them.
    """

    # Safety parameters (reflexes)
    MAX_POSITION_SIZE = 100.0  # Maximum dollars per position
    MIN_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to execute
    MAX_DAILY_USD = 50.0  # Maximum USD to trade per day (LIVE mode)
    MAX_PER_ORDER_USD = 10.0  # Maximum USD per single order (LIVE mode)

    def __init__(self, dryrun: bool = True):
        """
        Initialize executor.

        Args:
            dryrun: If True, no actual trades are executed (default: True)
        """
        self.dryrun = dryrun
        self.audit = get_audit_logger(component="executor")
        self._clob_client: Optional[ClobClient] = None
        self._daily_spent_usd = 0.0
        self._last_reset_date: Optional[str] = None
    
    def _get_clob_client(self) -> Optional[ClobClient]:
        """
        Get or create the CLOB client for Polymarket API.
        
        Returns:
            ClobClient instance or None if not configured
        """
        if self._clob_client is not None:
            return self._clob_client
        
        if not CLOB_AVAILABLE:
            return None
        
        api_key, secret = get_polymarket_credentials()
        if not api_key or not secret:
            return None
        
        try:
            # Initialize CLOB client with Level 1 auth (private key)
            # The POLYMARKET_SECRET is the private key for signing
            self._clob_client = ClobClient(
                host=POLYMARKET_HOST,
                chain_id=POLYGON_CHAIN_ID,
                key=secret
            )
            return self._clob_client
        except Exception as e:
            self.audit.log_error(
                error_type="clob_client_init",
                error_message=f"Failed to initialize CLOB client: {e}"
            )
            return None
    
    def _reset_daily_limit_if_needed(self):
        """Reset daily spending limit if it's a new day."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._last_reset_date != today:
            self._daily_spent_usd = 0.0
            self._last_reset_date = today

    def execute(self):
        """Legacy method - kept for backwards compatibility"""
        print("Executing plan...")
        
        # Audit the execution
        self.audit.log_action(
            action_type="plan_execution",
            action_data={"mode": "DRYRUN" if self.dryrun else "LIVE"},
            result="completed"
        )

    def validate_action(self, action, for_live: bool = False) -> tuple[bool, str]:
        """
        Validate a planned action against safety rules (reflexes).

        Args:
            action: PlannedAction object to validate
            for_live: If True, apply additional LIVE trading constraints

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
        
        # Additional safety checks for LIVE trading
        if for_live:
            # Check per-order limit
            if action.amount > self.MAX_PER_ORDER_USD:
                return False, f"LIVE: Order size ${action.amount:.2f} exceeds max per order ${self.MAX_PER_ORDER_USD:.2f}"
            
            # Check daily limit
            self._reset_daily_limit_if_needed()
            if self._daily_spent_usd + action.amount > self.MAX_DAILY_USD:
                remaining = self.MAX_DAILY_USD - self._daily_spent_usd
                return False, f"LIVE: Would exceed daily limit. Spent: ${self._daily_spent_usd:.2f}, Limit: ${self.MAX_DAILY_USD:.2f}, Remaining: ${remaining:.2f}"

        # All checks passed
        return True, "OK"
    
    def _execute_live_order(self, action) -> ExecutionResult:
        """
        Execute a single order on Polymarket CLOB.
        
        Args:
            action: PlannedAction object
            
        Returns:
            ExecutionResult with outcome
        """
        # Validate prerequisites
        is_ready, prereq_msg = validate_live_trading_prerequisites()
        if not is_ready:
            return ExecutionResult(
                market_id=action.market_id,
                market_name=action.market_name,
                success=False,
                message=f"LIVE: Prerequisites not met - {prereq_msg}",
                executed_amount=0.0
            )
        
        client = self._get_clob_client()
        if not client:
            return ExecutionResult(
                market_id=action.market_id,
                market_name=action.market_name,
                success=False,
                message="LIVE: Failed to initialize Polymarket CLOB client",
                executed_amount=0.0
            )
        
        try:
            # Convert side to CLOB format (BUY for YES, SELL for NO)
            clob_side = "BUY" if action.side == "YES" else "SELL"
            
            # Get the token ID for the specific side (YES or NO token)
            # The action should have the correct token_id for the YES/NO outcome
            # If market_id is a condition_id, we need to get the specific token
            token_id = getattr(action, 'token_id', None) or action.market_id
            
            # Use current market price with a small spread for better execution
            # For BUY: use slightly above market (avoid aggressive 0.99)
            # For SELL: use slightly below market (avoid aggressive 0.01)
            # Default to 0.50 if no fair price available
            fair_price = getattr(action, 'fair_price', None) or 0.50
            spread = 0.02  # 2% spread for quick execution
            if clob_side == "BUY":
                price = min(0.99, fair_price + spread)
            else:
                price = max(0.01, fair_price - spread)
            
            # Create order arguments
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=action.amount,
                side=clob_side
            )
            
            # Log pre-execution audit
            self.audit.log_order(
                order_type="market",
                market=action.market_id,
                side=action.side,
                size=action.amount,
                price=price,
                dryrun=False
            )
            
            # Execute the order
            result = client.create_and_post_order(order_args)
            
            # Update daily spending tracker
            self._daily_spent_usd += action.amount
            
            # Log successful execution - only log safe fields
            order_id = 'unknown'
            if isinstance(result, dict):
                order_id = result.get('orderID') or result.get('id') or 'unknown'
            
            # Filter response to only safe, non-sensitive fields
            safe_response = {}
            if isinstance(result, dict):
                safe_fields = ['orderID', 'id', 'status', 'createdAt', 'size', 'price', 'side']
                safe_response = {k: v for k, v in result.items() if k in safe_fields}
            
            self.audit.log_action(
                action_type="live_order_executed",
                action_data={
                    "market_id": action.market_id,
                    "market_name": action.market_name,
                    "side": action.side,
                    "amount": action.amount,
                    "order_id": order_id,
                    "response": safe_response
                },
                result="success"
            )
            
            return ExecutionResult(
                market_id=action.market_id,
                market_name=action.market_name,
                success=True,
                message=f"LIVE: Placed {action.side} order for ${action.amount:.2f}",
                executed_amount=action.amount,
                order_id=order_id
            )
            
        except Exception as e:
            error_msg = str(e)
            self.audit.log_error(
                error_type="live_order_failed",
                error_message=error_msg,
                context={
                    "market_id": action.market_id,
                    "side": action.side,
                    "amount": action.amount
                }
            )
            return ExecutionResult(
                market_id=action.market_id,
                market_name=action.market_name,
                success=False,
                message=f"LIVE: Order failed - {error_msg}",
                executed_amount=0.0
            )

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
            # Validate action (reflexes) - apply LIVE constraints if not in dryrun
            is_valid, validation_msg = self.validate_action(action, for_live=not self.dryrun)

            if not is_valid:
                # Safety reflex triggered - reject action
                result = ExecutionResult(
                    market_id=action.market_id,
                    market_name=action.market_name,
                    success=False,
                    message=f"REJECTED: {validation_msg}",
                    executed_amount=0.0
                )
                results.append(result)
                continue

            # Execute action (body)
            if self.dryrun:
                # Log the dryrun order for audit trail
                self.audit.log_order(
                    order_type="market",
                    market=action.market_id,
                    side=action.side,
                    size=action.amount,
                    dryrun=True
                )
                result = ExecutionResult(
                    market_id=action.market_id,
                    market_name=action.market_name,
                    success=True,
                    message=f"DRYRUN: Would place {action.side} order for ${action.amount:.2f}",
                    executed_amount=action.amount
                )
            else:
                # LIVE MODE: Execute on Polymarket CLOB API
                result = self._execute_live_order(action)

            results.append(result)

        return results

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

        summary = {
            'total_actions': total,
            'successful': successful,
            'rejected': rejected,
            'total_amount_executed': total_executed,
            'mode': 'DRYRUN' if self.dryrun else 'LIVE'
        }
        
        # Add LIVE mode specific info
        if not self.dryrun:
            self._reset_daily_limit_if_needed()
            summary['daily_spent_usd'] = self._daily_spent_usd
            summary['daily_remaining_usd'] = max(0, self.MAX_DAILY_USD - self._daily_spent_usd)
            summary['max_per_order_usd'] = self.MAX_PER_ORDER_USD
            summary['max_daily_usd'] = self.MAX_DAILY_USD
        
        return summary


def load_execution_plan(plan_path: Optional[Path] = None) -> dict:
    """
    Load the execution plan configuration from JSON file.
    
    Args:
        plan_path: Path to execution_plan.json (default: executor/execution_plan.json)
        
    Returns:
        Execution plan configuration dict
    """
    if plan_path is None:
        plan_path = Path(__file__).parent / "execution_plan.json"
    
    with open(plan_path, 'r') as f:
        return json.load(f)


def create_executor_from_plan(plan_path: Optional[Path] = None) -> Executor:
    """
    Create an Executor instance based on the execution plan configuration.
    
    Args:
        plan_path: Path to execution_plan.json (default: executor/execution_plan.json)
        
    Returns:
        Configured Executor instance
    """
    plan = load_execution_plan(plan_path)
    
    # Determine mode from plan
    mode = plan.get('mode', 'DRYRUN')
    live_enabled = plan.get('live_enabled', False)
    
    # DRYRUN unless explicitly set to LIVE and live_enabled is True
    dryrun = not (mode == 'LIVE' and live_enabled)
    
    executor = Executor(dryrun=dryrun)
    
    # Override safety limits from plan if specified
    if 'max_live_per_order_usd' in plan:
        executor.MAX_PER_ORDER_USD = plan['max_live_per_order_usd']
    if 'max_live_daily_usd' in plan:
        executor.MAX_DAILY_USD = plan['max_live_daily_usd']
    
    return executor


# Instantiate and execute (for backwards compatibility)
if __name__ == "__main__":
    executor = Executor()
    executor.execute()
