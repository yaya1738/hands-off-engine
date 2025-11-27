"""
Shadow Executor Sink

Logs would-be trades when running in shadow mode.
This allows full pipeline execution (planning, risk checks, safeguards)
without sending real orders to the trading API.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SHADOW_LOG = Path(__file__).parent.parent / "state" / "shadow_trades.jsonl"


def record_shadow_order(
    market_id: str,
    market_name: str,
    side: str,
    size_usd: float,
    price: Optional[float],
    confidence: float,
    source: str,
    executor_mode: str,
    health_ok: bool,
    health_reason: str,
    risk_phase: str,
    caps_applied: List[str],
    safety_checks: List[str],
    extra: Optional[Dict[str, Any]] = None,
    log_path: Optional[Path] = None,
) -> None:
    """
    Record a shadow order to the shadow trades log.

    Args:
        market_id: Market identifier
        market_name: Human-readable market name
        side: "YES" or "NO"
        size_usd: Position size in USD
        price: Current market price (if available)
        confidence: Confidence score (0-1)
        source: Where the signal came from (e.g., "polymarket_decider_v2")
        executor_mode: Should always be "shadow" for this function
        health_ok: Whether system health check passed
        health_reason: Health check details
        risk_phase: Current risk phase (baby_mode, scale_up, full_deployment)
        caps_applied: List of caps/limits that were applied
        safety_checks: List of safety check messages
        extra: Additional context to log
        log_path: Override default log path (for testing)
    """
    if log_path is None:
        log_path = DEFAULT_SHADOW_LOG

    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": market_id,
        "market_name": market_name,
        "side": side,
        "size_usd": size_usd,
        "price": price,
        "confidence": confidence,
        "source": source,
        "executor_mode": executor_mode,
        "health_ok": health_ok,
        "health_reason": health_reason,
        "risk_phase": risk_phase,
        "caps_applied": caps_applied,
        "safety_checks": safety_checks,
    }

    if extra:
        entry["extra"] = extra

    # Append to log file
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
