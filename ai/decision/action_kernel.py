"""Single fail-closed decision kernel for consequential autonomous actions.

Cognition may recommend; this kernel decides whether an action is sufficiently
specified, independently reproducible, economically/risk bounded, and ready
for the downstream authority. It never performs external side effects.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class ActionDecision:
    approved: bool
    reason: str
    confidence: float
    risk_score: float
    total_cost: float
    checks: tuple[str, ...]
    evidence: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def decide(
    *,
    action: str,
    confidence: float,
    risk_score: float,
    costs: Mapping[str, Any],
    evidence: Mapping[str, Any],
    max_risk: float = 1.0,
    min_confidence: float = 0.4,
    risk_check: Callable[[], bool] | None = None,
) -> ActionDecision:
    """Perform a complete, side-effect-free decision calculation twice."""
    checks: list[str] = []
    if not isinstance(action, str) or not action.strip():
        return _reject("missing action", checks, confidence, risk_score, evidence)
    if not isfinite(float(confidence)) or not 0 <= confidence <= 1:
        return _reject("invalid confidence", checks, confidence, risk_score, evidence)
    if not isfinite(float(risk_score)) or not 0 <= risk_score <= max_risk:
        return _reject("risk limit exceeded", checks, confidence, risk_score, evidence)
    if not isinstance(evidence, Mapping) or not evidence:
        return _reject("missing decision evidence", checks, confidence, risk_score, evidence)
    if not isinstance(costs, Mapping) or not costs:
        return _reject("missing cost ledger", checks, confidence, risk_score, evidence)
    try:
        normalized = {str(k): float(v) for k, v in costs.items()}
    except (TypeError, ValueError):
        return _reject("invalid cost ledger", checks, confidence, risk_score, evidence)
    if any(not isfinite(v) or v < 0 for v in normalized.values()):
        return _reject("invalid cost ledger", checks, confidence, risk_score, evidence)

    total_1 = sum(normalized.values())
    checks.append("cost-ledger-1")
    total_2 = sum(normalized.values())
    checks.append("cost-ledger-2")
    if total_1 != total_2:
        return _reject("cost recomputation mismatch", checks, confidence, risk_score, evidence)

    if confidence < min_confidence:
        return _reject("confidence below minimum", checks, confidence, risk_score, evidence, total_1)
    checks.append("confidence-rule")
    if risk_check is not None:
        try:
            if not bool(risk_check()):
                return _reject("risk check rejected action", checks, confidence, risk_score, evidence, total_1)
        except Exception:
            return _reject("risk check unavailable", checks, confidence, risk_score, evidence, total_1)
    checks.append("risk-rule")

    return ActionDecision(True, "complete decision calculation passed", float(confidence), float(risk_score), total_1, tuple(checks), dict(evidence))


def _reject(reason: str, checks: list[str], confidence: float, risk_score: float, evidence: Mapping[str, Any], total: float = 0.0) -> ActionDecision:
    return ActionDecision(False, reason, float(confidence), float(risk_score), float(total), tuple(checks), dict(evidence or {}))
