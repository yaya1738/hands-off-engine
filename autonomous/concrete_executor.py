"""Legacy trading executor compatibility shim.

The historical ConcreteExecutor contained a direct Polymarket order-placement
path that bypassed the current Factory authority and financial approval gates.
That path is intentionally unavailable. Current autonomous work must use the
Factory authority/runtime and its fail-closed financial gates.
"""

from datetime import datetime, timezone
from typing import Any, Dict


class ConcreteExecutor:
    """Compatibility surface for legacy callers; never places live orders."""

    def __init__(self, dry_run: bool = True, *args: Any, **kwargs: Any) -> None:
        self.dry_run = True
        self.trading_available = False

    def evaluate_opportunity(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "recommendation": "BLOCKED_LEGACY_EXECUTOR",
            "concrete_action": {"action": "NO_TRADE"},
            "reason": "Legacy direct trading executor is quarantined; use Factory authority.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute_trade(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "executed": False,
            "status": "blocked",
            "reason": "Legacy direct trading executor is permanently unavailable.",
        }

    def record_outcome(self, trade_id: str, outcome: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "trade_id": trade_id,
            "recorded": False,
            "status": "shadow_only",
            "reason": "Legacy executor is quarantined; no live trade exists to record.",
            "outcome": outcome,
        }

    def run_pipeline(self, limit: int = 10) -> Dict[str, Any]:
        return {
            "status": "blocked",
            "markets_evaluated": 0,
            "trades_recommended": 0,
            "trades_executed": 0,
            "trades_skipped": 0,
            "trades_blocked": 0,
            "opportunities": [],
            "reason": "Legacy direct trading pipeline is quarantined; use Factory authority.",
        }
