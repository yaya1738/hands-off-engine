"""
Pre-Trade Checks for Hands-Off Engine Executor

This module validates trades against risk limits before execution:
- Position size limits
- Daily loss limits
- Concentration checks (portfolio exposure)
- Liquidity checks
- Circuit breaker checks (stop all trading if triggered)
"""

import json
import sys
import os
from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


@dataclass
class PreTradeCheckResult:
    """Result of a pre-trade safety check"""
    passed: bool
    check_name: str
    message: str
    severity: str = "info"  # info, warning, error


class PreTradeValidator:
    """
    Pre-trade validator enforces safety checks before execution.
    
    These are the "reflexes" that prevent dangerous trades.
    """
    
    # Safety parameters
    MAX_POSITION_SIZE = 100.0  # Max dollars per position
    MAX_DAILY_LOSS = 500.0  # Max daily loss limit
    MAX_PORTFOLIO_CONCENTRATION = 0.20  # Max 20% of portfolio in one position
    MIN_LIQUIDITY_THRESHOLD = 100.0  # Min liquidity required
    MIN_CONFIDENCE_THRESHOLD = 0.70  # Min confidence to execute
    CIRCUIT_BREAKER_LOSS_THRESHOLD = 1000.0  # Total loss that triggers circuit breaker
    
    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize pre-trade validator.
        
        Args:
            state_dir: Directory for state files (defaults to ../state)
        """
        if state_dir is None:
            state_dir = Path(__file__).parent.parent / "state"
        
        self.state_dir = state_dir
        self.audit = get_audit_logger(component="executor.pretrade")
        
        # Load circuit breaker state
        self.circuit_breaker_file = state_dir / "circuit_breaker.json"
        self._load_circuit_breaker_state()
    
    def _load_circuit_breaker_state(self) -> Dict:
        """Load circuit breaker state from file"""
        if self.circuit_breaker_file.exists():
            with open(self.circuit_breaker_file, 'r') as f:
                return json.load(f)
        return {"triggered": False, "triggered_at": None, "reason": None}
    
    def _save_circuit_breaker_state(self, state: Dict):
        """Save circuit breaker state to file"""
        with open(self.circuit_breaker_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def check_circuit_breaker(self) -> PreTradeCheckResult:
        """
        Check if circuit breaker is triggered.
        
        Returns:
            PreTradeCheckResult indicating if trading is allowed
        """
        state = self._load_circuit_breaker_state()
        
        if state.get("triggered", False):
            return PreTradeCheckResult(
                passed=False,
                check_name="circuit_breaker",
                message=f"Circuit breaker triggered: {state.get('reason', 'unknown')}",
                severity="error"
            )
        
        return PreTradeCheckResult(
            passed=True,
            check_name="circuit_breaker",
            message="Circuit breaker OK"
        )
    
    def check_position_limit(self, amount: float) -> PreTradeCheckResult:
        """
        Check if position size is within limits.
        
        Args:
            amount: Dollar amount of position
            
        Returns:
            PreTradeCheckResult
        """
        if amount > self.MAX_POSITION_SIZE:
            return PreTradeCheckResult(
                passed=False,
                check_name="position_limit",
                message=f"Position ${amount:.2f} exceeds max ${self.MAX_POSITION_SIZE:.2f}",
                severity="error"
            )
        
        return PreTradeCheckResult(
            passed=True,
            check_name="position_limit",
            message=f"Position size ${amount:.2f} within limit"
        )
    
    def check_daily_loss_limit(self) -> PreTradeCheckResult:
        """
        Check if we've hit daily loss limit.
        
        Returns:
            PreTradeCheckResult
        """
        # Load today's execution history
        history_file = self.state_dir / "execution" / "history.jsonl"
        
        if not history_file.exists():
            return PreTradeCheckResult(
                passed=True,
                check_name="daily_loss_limit",
                message="No execution history, daily loss OK"
            )
        
        # Calculate today's P&L
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        daily_pnl = 0.0
        with open(history_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                    
                    if entry_time >= today_start:
                        # Add realized P&L if available
                        daily_pnl += entry.get("realized_pnl", 0.0)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        # Check if loss exceeds limit
        if daily_pnl < -self.MAX_DAILY_LOSS:
            return PreTradeCheckResult(
                passed=False,
                check_name="daily_loss_limit",
                message=f"Daily loss ${-daily_pnl:.2f} exceeds limit ${self.MAX_DAILY_LOSS:.2f}",
                severity="error"
            )
        
        return PreTradeCheckResult(
            passed=True,
            check_name="daily_loss_limit",
            message=f"Daily P&L ${daily_pnl:.2f} within limit"
        )
    
    def check_concentration(self, market_id: str, amount: float, 
                           bankroll: float = 1000.0) -> PreTradeCheckResult:
        """
        Check if position would create excessive concentration.
        
        Args:
            market_id: Market identifier
            amount: Dollar amount of new position
            bankroll: Total bankroll
            
        Returns:
            PreTradeCheckResult
        """
        # Load current positions
        pending_file = self.state_dir / "execution" / "pending.json"
        
        current_exposure = 0.0
        if pending_file.exists():
            with open(pending_file, 'r') as f:
                pending = json.load(f)
                
                for order in pending.get("orders", []):
                    if order.get("market_id") == market_id:
                        current_exposure += order.get("amount", 0.0)
        
        # Calculate total exposure if we add this position
        total_exposure = current_exposure + amount
        concentration = total_exposure / bankroll
        
        if concentration > self.MAX_PORTFOLIO_CONCENTRATION:
            return PreTradeCheckResult(
                passed=False,
                check_name="concentration",
                message=f"Position concentration {concentration:.1%} exceeds max {self.MAX_PORTFOLIO_CONCENTRATION:.1%}",
                severity="warning"
            )
        
        return PreTradeCheckResult(
            passed=True,
            check_name="concentration",
            message=f"Concentration {concentration:.1%} within limit"
        )
    
    def check_liquidity(self, market_liquidity: float) -> PreTradeCheckResult:
        """
        Check if market has sufficient liquidity.
        
        Args:
            market_liquidity: Available liquidity in market
            
        Returns:
            PreTradeCheckResult
        """
        if market_liquidity < self.MIN_LIQUIDITY_THRESHOLD:
            return PreTradeCheckResult(
                passed=False,
                check_name="liquidity",
                message=f"Market liquidity ${market_liquidity:.2f} below min ${self.MIN_LIQUIDITY_THRESHOLD:.2f}",
                severity="warning"
            )
        
        return PreTradeCheckResult(
            passed=True,
            check_name="liquidity",
            message=f"Market liquidity ${market_liquidity:.2f} sufficient"
        )
    
    def check_confidence(self, confidence: float) -> PreTradeCheckResult:
        """
        Check if confidence meets minimum threshold.
        
        Args:
            confidence: Model confidence (0.0 to 1.0)
            
        Returns:
            PreTradeCheckResult
        """
        if confidence < self.MIN_CONFIDENCE_THRESHOLD:
            return PreTradeCheckResult(
                passed=False,
                check_name="confidence",
                message=f"Confidence {confidence:.1%} below min {self.MIN_CONFIDENCE_THRESHOLD:.1%}",
                severity="error"
            )
        
        return PreTradeCheckResult(
            passed=True,
            check_name="confidence",
            message=f"Confidence {confidence:.1%} sufficient"
        )
    
    def validate_trade(self, action, bankroll: float = 1000.0) -> tuple[bool, List[PreTradeCheckResult]]:
        """
        Run all pre-trade checks on a planned action.
        
        Args:
            action: PlannedAction object with market_id, amount, confidence, etc.
            bankroll: Total bankroll for concentration check
            
        Returns:
            Tuple of (all_passed, list_of_check_results)
        """
        results = []
        
        # Run all checks
        results.append(self.check_circuit_breaker())
        results.append(self.check_position_limit(action.amount))
        results.append(self.check_daily_loss_limit())
        results.append(self.check_concentration(action.market_id, action.amount, bankroll))
        results.append(self.check_confidence(action.confidence))
        
        # Check liquidity if available
        if hasattr(action, 'liquidity') and action.liquidity is not None:
            results.append(self.check_liquidity(action.liquidity))
        
        # All must pass
        all_passed = all(r.passed for r in results)
        
        # Audit the validation
        self.audit.log_action(
            action_type="pretrade_validation",
            action_data={
                "market_id": action.market_id,
                "amount": action.amount,
                "confidence": action.confidence,
                "checks_passed": all_passed,
                "checks": [{"name": r.check_name, "passed": r.passed, "message": r.message} 
                          for r in results]
            },
            result="passed" if all_passed else "rejected"
        )
        
        return all_passed, results
    
    def trigger_circuit_breaker(self, reason: str):
        """
        Trigger circuit breaker to stop all trading.
        
        Args:
            reason: Reason for triggering circuit breaker
        """
        state = {
            "triggered": True,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason
        }
        self._save_circuit_breaker_state(state)
        
        # Audit the circuit breaker trigger
        self.audit.log_action(
            action_type="circuit_breaker_trigger",
            action_data={"reason": reason},
            result="trading_stopped"
        )
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker to allow trading."""
        state = {
            "triggered": False,
            "triggered_at": None,
            "reason": None
        }
        self._save_circuit_breaker_state(state)
        
        # Audit the reset
        self.audit.log_action(
            action_type="circuit_breaker_reset",
            action_data={},
            result="trading_enabled"
        )


# Example usage
if __name__ == "__main__":
    from decider.ho_decider import PlannedAction
    
    validator = PreTradeValidator()
    
    # Test action
    action = PlannedAction(
        market_id="test_market",
        market_name="Test Market",
        side="YES",
        amount=50.0,
        confidence=0.85,
        reasoning="Test"
    )
    
    passed, results = validator.validate_trade(action)
    
    print(f"Validation {'PASSED' if passed else 'FAILED'}")
    for result in results:
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.check_name}: {result.message}")
