from typing import Any, Dict, List


class FactoryRiskManager:
    """Advisory risk adapter that cannot grant execution authority."""

    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def assess(self, action: Dict[str, Any]):
        """Return only explicitly supplied risk data; never invent a safe score."""
        risk_score = action.get("risk_score") if isinstance(action, dict) else None
        result = {"risk_score": risk_score, "assessed": risk_score is not None, "action": action}
        self._history.append(result)
        return result

    def check_constraints(self, action: Dict[str, Any]):
        """Do not infer that constraints pass when no policy evidence exists."""
        if not isinstance(action, dict) or "within_constraints" not in action:
            result = {"within_constraints": False, "reason": "missing_constraint_evidence", "action": action}
        else:
            result = {"within_constraints": bool(action["within_constraints"]), "action": action}
        self._history.append(result)
        return result

    def approve(self, action: Dict[str, Any]):
        """Never grant execution approval; the canonical decision kernel owns approval."""
        result = {
            "approved": False,
            "reason": "execution_approval_owned_by_canonical_decision_kernel",
            "action": action,
        }
        self._history.append(result)
        return result

    def mitigate(self, risk: Dict[str, Any]):
        """Record mitigation intent without claiming the risk was actually mitigated."""
        result = {"mitigated": False, "reason": "mitigation_requires_verified_policy_action", "risk": risk}
        self._history.append(result)
        return result

    def history(self):
        return self._history
