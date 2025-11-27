"""
Executor: The "Body + Reflexes" of the Hands-Off Engine

This module validates and executes planned actions.
It acts as both the body (execution) and reflexes (safety checks)
to ensure no dangerous actions are taken.
"""

import sys
import os
from dataclasses import dataclass
from typing import List

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


class Executor:
    """
    The Executor is the body and reflexes of the pipeline.
    It validates planned actions against safety rules and executes them.
    """

    # Safety parameters (reflexes)
    MAX_POSITION_SIZE = 100.0  # Maximum dollars per position
    MIN_CONFIDENCE_THRESHOLD = 0.55  # Minimum confidence to execute (lowered for cash explosion)

    def __init__(self, dryrun: bool = True):
        """
        Initialize executor.

        Args:
            dryrun: If True, no actual trades are executed (default: True)
        """
        self.dryrun = dryrun
        self.audit = get_audit_logger(component="executor")

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
                # In production, this would call actual trading API
                result = ExecutionResult(
                    market_id=action.market_id,
                    market_name=action.market_name,
                    success=True,
                    message=f"LIVE: Placed {action.side} order for ${action.amount:.2f}",
                    executed_amount=action.amount
                )

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

        return {
            'total_actions': total,
            'successful': successful,
            'rejected': rejected,
            'total_amount_executed': total_executed,
            'mode': 'DRYRUN' if self.dryrun else 'LIVE'
        }


# Instantiate and execute (for backwards compatibility)
if __name__ == "__main__":
    executor = Executor()
    executor.execute()
