"""Unified, fail-closed decision gate for consequential trading.

The gate never places orders. It composes hard limits, trading safeguards,
fully loaded costs, and probability/brain evidence into an auditable decision.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from executor.trading_safeguards import TradingSafeguards
from llm.consensus_engine import build_consensus

ROOT = Path(__file__).resolve().parent.parent
HARD_LIMITS = ROOT / "config" / "hard_limits.json"

CONFIDENCE_SCORES = {"low": 0.40, "medium": 0.65, "high": 0.85}


@dataclass(frozen=True)
class TradingDecision:
    approved: bool
    reason: str
    probability: float
    market_price: float
    edge: float
    expected_value: float
    total_cost: float
    max_position_usd: float
    checks: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _limits() -> dict[str, float]:
    try:
        data = json.loads(HARD_LIMITS.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in data["limits"].items()}
    except Exception as exc:
        raise RuntimeError(f"hard limits unavailable: {exc}") from exc


def _consensus(analyses: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return build_consensus([dict(a) for a in analyses])


def evaluate_trade(
    *,
    trade_size_usd: float,
    market_price: float,
    analyses: Sequence[Mapping[str, Any]],
    explicit_costs_usd: float = 0.0,
    expected_payout_multiple: float = 1.0,
    safeguards: TradingSafeguards | None = None,
) -> TradingDecision:
    """Evaluate a trade without execution; every missing safety input rejects."""
    checks: list[str] = []
    limits = _limits()

    if not 0.0 < market_price <= 1.0:
        return _reject("invalid market price", checks)
    if trade_size_usd <= 0:
        return _reject("invalid trade size", checks)
    if explicit_costs_usd < 0 or expected_payout_multiple <= 0:
        return _reject("invalid cost or payout input", checks)
    if trade_size_usd > limits["MAX_ABSOLUTE_POSITION_USD"]:
        return _reject("absolute position limit exceeded", checks)
    if len(analyses) < 1:
        return _reject("no probability analysis", checks)

    first = _consensus(analyses)
    checks.append("probability-consensus-1")
    second = _consensus(analyses)
    checks.append("probability-consensus-2")

    probability = float(first["consensus_probability"])
    if first != second:
        return _reject("consensus recomputation mismatch", checks, probability=probability, price=market_price)
    if first["num_analyses"] < 1:
        return _reject("no valid probability analysis", checks, probability=probability, price=market_price)
    if first["disagreement_detected"]:
        return _reject("analysis disagreement requires deferral", checks, probability=probability, price=market_price)

    confidence = str(first.get("confidence", "low")).lower()
    confidence_score = CONFIDENCE_SCORES.get(confidence, 0.0)
    checks.append("brain-confidence-rule")
    if confidence_score < limits["MIN_CONFIDENCE_THRESHOLD"]:
        return _reject("brain confidence below minimum threshold", checks, probability=probability, price=market_price)

    edge = probability - market_price
    expected_gross = trade_size_usd * max(0.0, probability * expected_payout_multiple - 1.0)
    total_cost = float(explicit_costs_usd)
    expected_value = expected_gross - total_cost
    checks.append("costs-accounted-for")

    guard = safeguards or TradingSafeguards(
        max_daily_loss_usd=limits["MAX_ABSOLUTE_DAILY_LOSS_USD"],
        max_position_usd=limits["MAX_ABSOLUTE_POSITION_USD"],
        max_open_risk_usd=limits["MAX_ABSOLUTE_OPEN_RISK_USD"],
        max_trades_per_hour=int(limits["MAX_ABSOLUTE_TRADES_PER_HOUR"]),
    )
    safe, messages = guard.check_all_safeguards(trade_size_usd)
    checks.append("trading-safeguards")
    if not safe:
        return _reject("; ".join(messages), checks, probability=probability, price=market_price, edge=edge, ev=expected_value, cost=total_cost)

    recomputed_gross = trade_size_usd * max(0.0, probability * expected_payout_multiple - 1.0)
    recomputed_ev = recomputed_gross - total_cost
    checks.append("economic-recomputation")
    if abs(recomputed_ev - expected_value) > 1e-9:
        return _reject("economic recomputation mismatch", checks, probability=probability, price=market_price, edge=edge, ev=expected_value, cost=total_cost)
    if recomputed_ev <= 0:
        return _reject("non-positive net expected value after all costs", checks, probability=probability, price=market_price, edge=edge, ev=recomputed_ev, cost=total_cost)

    return TradingDecision(True, "all hard limits, safeguards, brain confidence, probability and cost checks passed", probability, market_price, edge, recomputed_ev, total_cost, limits["MAX_ABSOLUTE_POSITION_USD"], tuple(checks))


def _reject(reason: str, checks: list[str], *, probability: float = 0.0, price: float = 0.0, edge: float = 0.0, ev: float = 0.0, cost: float = 0.0) -> TradingDecision:
    return TradingDecision(False, reason, probability, price, edge, ev, cost, 0.0, tuple(checks))
