"""Canonical autonomous convergence lifecycle.

All consequential work should enter here: cognition supplies evidence,
the decision kernel validates it, and the caller supplies the governed executor.
This module never performs external side effects itself.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from ai.decision.action_kernel import ActionDecision, decide


class ConvergenceController:
    """Single reusable decision-to-action lifecycle with verification closure."""

    def __init__(self, *, decision_fn: Callable[..., ActionDecision] = decide):
        self._decision_fn = decision_fn

    def evaluate(self, *, action: str, confidence: float, risk_score: float,
                 costs: Mapping[str, Any], evidence: Mapping[str, Any],
                 max_risk: float = 1.0, min_confidence: float = 0.4,
                 risk_check: Callable[[], bool] | None = None) -> ActionDecision:
        return self._decision_fn(
            action=action,
            confidence=confidence,
            risk_score=risk_score,
            costs=costs,
            evidence=evidence,
            max_risk=max_risk,
            min_confidence=min_confidence,
            risk_check=risk_check,
        )

    def execute(self, *, decision: ActionDecision,
                executor: Callable[[ActionDecision], Any],
                verifier: Callable[[Any, ActionDecision], bool] | None = None) -> dict[str, Any]:
        """Execute only an approved decision, then close the loop by verification."""
        if not decision.approved:
            return {"status": "blocked", "decision": decision.as_dict()}
        if not callable(executor):
            return {"status": "blocked", "reason": "missing governed executor", "decision": decision.as_dict()}
        try:
            result = executor(decision)
        except Exception as exc:
            return {"status": "failed", "reason": "execution_error", "error": str(exc), "decision": decision.as_dict()}

        if verifier is None:
            return {"status": "executed_unverified", "result": result, "decision": decision.as_dict()}
        try:
            verified = bool(verifier(result, decision))
        except Exception as exc:
            return {"status": "verification_failed", "reason": "verification_error", "error": str(exc), "result": result, "decision": decision.as_dict()}
        return {
            "status": "verified" if verified else "verification_failed",
            "verified": verified,
            "result": result,
            "decision": decision.as_dict(),
        }
