"""Legacy trade-executor compatibility shim.

The historical implementation contained a direct Polymarket LIVE order path
controlled by environment/config state. That is incompatible with the current
Factory authority and explicit human financial approval model, so live trading
through this legacy surface is permanently unavailable.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List


class TradeExecutor:
    """Legacy compatibility surface; never places live orders."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.mode = "DENIED"
        self.live_trading_enabled = False
        self.state: Dict[str, Any] = {"mode": self.mode, "total_trades": 0}

    def get_market_data(self, limit: int = 20) -> List[Dict[str, Any]]:
        return []

    def analyze_opportunity(self, market: Dict[str, Any]) -> Any:
        return None

    def generate_signals(self) -> List[Dict[str, Any]]:
        return []

    def execute_trade(self, signal: Dict[str, Any], amount: float = 1.0) -> Dict[str, Any]:
        return {
            "status": "blocked",
            "executed": False,
            "mode": "DENIED",
            "reason": "Legacy direct trading executor is quarantined; use Factory authority and human financial approval.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def check_positions(self) -> Dict[str, Any]:
        return {"mode": "DENIED", "trading_available": False}

    def run_trading_cycle(self) -> Dict[str, Any]:
        return {
            "status": "blocked",
            "mode": "DENIED",
            "signals_generated": 0,
            "trades_executed": 0,
            "reason": "Legacy autonomous trading cycle is quarantined.",
        }


def main() -> Dict[str, Any]:
    return TradeExecutor().run_trading_cycle()


if __name__ == "__main__":
    main()
