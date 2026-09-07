"""Unified action/calculation boundary for consequential trading decisions.

This layer turns the repository's cognitive outputs into a single auditable
pre-action calculation. It deliberately separates *decision* from *execution*:
no exchange or payment mutation happens here.

Every cost category is explicit. Missing cost evidence is fail-closed, and the
underlying trading decision gate remains the final hard-limit authority.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping, Sequence

from trading.decision_gate import TradingDecision, evaluate_trade


REQUIRED_COST_FIELDS = (
    "exchange_fees_usd",
    "slippage_usd",
    "spread_cost_usd",
    "network_fees_usd",
    "funding_or_financing_usd",
    "other_known_costs_usd",
)


@dataclass(frozen=True)
class ActionCalculation:
    approved: bool
    reason: str
    decision: TradingDecision | None
    costs: dict[str, float]
    total_cost: float
    brain_evidence: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        if self.decision is not None:
            value["decision"] = self.decision.as_dict()
        return value


def _costs(costs: Mapping[str, Any]) -> dict[str, float]:
    if not isinstance(costs, Mapping):
        raise ValueError("cost evidence is required")
    missing = [key for key in REQUIRED_COST_FIELDS if key not in costs]
    if missing:
        raise ValueError("missing cost evidence: " + ", ".join(missing))
    normalized = {key: float(costs[key]) for key in REQUIRED_COST_FIELDS}
    if any(value < 0 for value in normalized.values()):
        raise ValueError("costs cannot be negative")
    return normalized


def evaluate_action(
    *,
    trade_size_usd: float,
    market_price: float,
    analyses: Sequence[Mapping[str, Any]],
    costs: Mapping[str, Any],
    expected_payout_multiple: float = 1.0,
    safeguards=None,
    brain_evidence: Mapping[str, Any] | None = None,
) -> ActionCalculation:
    """Perform the complete pre-action calculation without executing it.

    ``analyses`` is the cognitive/probability evidence supplied by the brain
    pipeline. ``costs`` is an explicit ledger of all known expense categories.
    The final action can only be approved when the existing hard-limit and
    probability/cost gate approves the fully loaded economics.
    """
    try:
        normalized_costs = _costs(costs)
    except (TypeError, ValueError) as exc:
        return ActionCalculation(False, str(exc), None, {}, 0.0, dict(brain_evidence or {}))

    total = sum(normalized_costs.values())
    decision = evaluate_trade(
        trade_size_usd=trade_size_usd,
        market_price=market_price,
        analyses=analyses,
        explicit_costs_usd=total,
        expected_payout_multiple=expected_payout_multiple,
        safeguards=safeguards,
    )
    if not decision.approved:
        return ActionCalculation(False, decision.reason, decision, normalized_costs, total, dict(brain_evidence or {}))

    return ActionCalculation(True, "brain evidence and fully loaded economics passed", decision, normalized_costs, total, dict(brain_evidence or {}))
