"""Fail-closed current-rules gate for Polymarket financial actions.

This module deliberately does not fetch or enable trading by itself. A caller must
supply a fresh, authoritative rules snapshot. The gate exists to prevent historical
fee/reward/order assumptions from silently authorizing financial execution.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class RulesDecision:
    allowed: bool
    reason: str
    checked_at: str
    source: Optional[str] = None


class PolymarketRulesGate:
    """Validate the minimum current-rule evidence required before financial action."""

    REQUIRED_FIELDS = (
        "market_id",
        "observed_at",
        "source",
        "fees_enabled",
        "fee_schedule",
        "order_type",
        "orderbook_depth",
        "market_constraints",
    )

    def __init__(self, freshness_seconds: int = 300):
        if freshness_seconds <= 0:
            raise ValueError("freshness_seconds must be positive")
        self.freshness_seconds = freshness_seconds

    def check(
        self,
        snapshot: Optional[Mapping[str, Any]],
        *,
        live_trading_enabled: bool,
        now: Optional[datetime] = None,
    ) -> RulesDecision:
        checked_at = (now or datetime.now(timezone.utc)).isoformat()

        if not live_trading_enabled:
            return RulesDecision(False, "live_trading_globally_disabled", checked_at)
        if not isinstance(snapshot, Mapping):
            return RulesDecision(False, "current_rules_snapshot_missing", checked_at)

        missing = [field for field in self.REQUIRED_FIELDS if field not in snapshot]
        if missing:
            return RulesDecision(False, f"rules_snapshot_missing:{','.join(missing)}", checked_at, snapshot.get("source"))

        observed_at = self._parse_time(snapshot.get("observed_at"))
        if observed_at is None:
            return RulesDecision(False, "rules_snapshot_timestamp_invalid", checked_at, snapshot.get("source"))

        current = now or datetime.now(timezone.utc)
        age = (current - observed_at).total_seconds()
        if age < 0 or age > self.freshness_seconds:
            return RulesDecision(False, "rules_snapshot_stale", checked_at, snapshot.get("source"))

        if not snapshot.get("source"):
            return RulesDecision(False, "rules_snapshot_source_missing", checked_at)
        if not isinstance(snapshot.get("fee_schedule"), Mapping):
            return RulesDecision(False, "fee_schedule_invalid", checked_at, snapshot.get("source"))
        if snapshot.get("order_type") not in {"limit", "market", "post_only"}:
            return RulesDecision(False, "order_type_unknown", checked_at, snapshot.get("source"))
        if not isinstance(snapshot.get("orderbook_depth"), Mapping):
            return RulesDecision(False, "orderbook_depth_invalid", checked_at, snapshot.get("source"))
        if not isinstance(snapshot.get("market_constraints"), Mapping):
            return RulesDecision(False, "market_constraints_invalid", checked_at, snapshot.get("source"))

        return RulesDecision(True, "current_rules_valid", checked_at, snapshot.get("source"))

    @staticmethod
    def _parse_time(value: Any) -> Optional[datetime]:
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
