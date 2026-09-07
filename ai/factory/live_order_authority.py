"""Authoritative boundary for live order mutation.

This module is deliberately deny-by-default. Strategy code may submit an order
intent here, but this layer will not mutate an exchange until the repository has
an explicit, auditable activation contract. Keeping the boundary centralized
prevents strategy modules from silently acquiring live-trading authority.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


@dataclass(frozen=True)
class OrderIntent:
    token_id: str
    price: float
    size: float
    side: str
    source: str = "unknown"


class LiveOrderAuthority:
    """Fail-closed order authority; no exchange client is created here yet."""

    def __init__(self, *, enabled: bool = False):
        self.enabled = bool(enabled)

    def authorize(self, intent: OrderIntent | Mapping[str, Any]) -> dict[str, Any]:
        if isinstance(intent, Mapping):
            intent = OrderIntent(**intent)

        if not intent.token_id:
            return {"authorized": False, "reason": "missing_token_id"}
        if intent.side.upper() not in {"BUY", "SELL"}:
            return {"authorized": False, "reason": "invalid_side"}
        if intent.price <= 0 or intent.price > 1:
            return {"authorized": False, "reason": "invalid_price"}
        if intent.size <= 0:
            return {"authorized": False, "reason": "invalid_size"}
        if not self.enabled:
            return {
                "authorized": False,
                "reason": "live_order_authority_disabled",
                "intent": asdict(intent),
            }

        # Deliberately fail closed until the full activation/risk/capital/
        # provenance contract is wired into this single authority boundary.
        return {
            "authorized": False,
            "reason": "activation_contract_not_implemented",
            "intent": asdict(intent),
        }

    def submit(self, intent: OrderIntent | Mapping[str, Any]) -> dict[str, Any]:
        """Compatibility ingress. Authorization failure is never bypassed."""
        decision = self.authorize(intent)
        if not decision["authorized"]:
            return {"executed": False, **decision}
        raise RuntimeError("live submission backend is intentionally not enabled")


def submit_legacy_order(order: Any, *, source: str = "legacy") -> dict[str, Any]:
    """Route legacy signed-order objects through the same fail-closed boundary.

    The migration helper intentionally does not submit, inspect credentials, or
    create an exchange client. It accepts the legacy object only so existing
    executor call sites can be migrated mechanically without preserving a live
    mutation capability outside this authority module.
    """
    return LiveOrderAuthority().submit(
        {
            "token_id": "",
            "price": 0.0,
            "size": 0.0,
            "side": "",
            "source": source,
        }
    )
