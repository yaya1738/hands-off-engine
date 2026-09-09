"""Economic sustainability control for the governed autonomous system.

This module makes recurring compute and operating burn part of the same resource
optimization problem as capital.  It is intentionally decision-only: it does not
move money, buy compute, borrow, trade, or create accounts.  Authorized adapters
may consume its decisions later through the existing authority boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Any, Dict


@dataclass(frozen=True)
class EconomicSnapshot:
    """Normalized economic state for one control interval."""

    available_capital: float
    operating_burn: float
    realized_inflow: float = 0.0
    expected_inflow: float = 0.0
    reserved_capital: float = 0.0

    def validate(self) -> None:
        for name in asdict(self):
            value = float(getattr(self, name))
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.reserved_capital > self.available_capital:
            raise ValueError("reserved_capital cannot exceed available_capital")


class EconomicSustainability:
    """Optimize positive economic churn and aggressively penalize negative churn.

    Positive churn is net inflow after operating burn.  Negative churn is treated
    as a first-class failure signal: paid capacity should contract, discretionary
    allocations should be withheld, and the system should prefer free capacity or
    revenue generation until the trajectory recovers.
    """

    def __init__(self, *, minimum_runway_periods: float = 3.0, target_coverage: float = 1.25):
        if minimum_runway_periods <= 0 or target_coverage <= 0:
            raise ValueError("minimum_runway_periods and target_coverage must be positive")
        self.minimum_runway_periods = float(minimum_runway_periods)
        self.target_coverage = float(target_coverage)

    @staticmethod
    def net_churn(snapshot: EconomicSnapshot) -> float:
        snapshot.validate()
        return snapshot.realized_inflow - snapshot.operating_burn

    @staticmethod
    def expected_net_churn(snapshot: EconomicSnapshot) -> float:
        snapshot.validate()
        return snapshot.expected_inflow - snapshot.operating_burn

    def score(self, snapshot: EconomicSnapshot) -> Dict[str, Any]:
        """Return an economic health score and the corresponding control posture."""
        snapshot.validate()
        net = self.net_churn(snapshot)
        expected = self.expected_net_churn(snapshot)
        burn = snapshot.operating_burn
        coverage = ((snapshot.realized_inflow + snapshot.expected_inflow) / burn) if burn > 0 else float("inf")
        runway = ((snapshot.available_capital - snapshot.reserved_capital) / burn) if burn > 0 else float("inf")

        # Positive churn is rewarded; negative churn is penalized more strongly so
        # that the controller does not rationalize persistent losses as growth.
        if net >= 0 and expected >= 0:
            health = 1.0 + min(2.0, net / max(burn, 1e-12))
            posture = "scale"
        elif expected >= 0:
            health = max(0.0, 0.5 + expected / max(burn, 1e-12))
            posture = "stabilize"
        else:
            health = -min(3.0, abs(expected) / max(burn, 1e-12))
            posture = "contract"

        return {
            "net_churn": net,
            "expected_net_churn": expected,
            "coverage_ratio": coverage,
            "runway_periods": runway,
            "health_score": health,
            "posture": posture,
            "positive_churn": net > 0,
            "negative_churn": net < 0,
        }

    def compute_policy(self, snapshot: EconomicSnapshot) -> Dict[str, Any]:
        """Choose how aggressively the system may consume scarce resources."""
        health = self.score(snapshot)
        runway = health["runway_periods"]
        coverage = health["coverage_ratio"]

        if health["negative_churn"]:
            return {
                "action": "contract_paid_capacity",
                "capital_allocation": "preserve",
                "compute_policy": "free_first",
                "revenue_priority": "maximum",
                "reason": "negative churn must be eliminated before discretionary burn expands",
                "health": health,
            }

        if runway < self.minimum_runway_periods or coverage < self.target_coverage:
            return {
                "action": "stabilize",
                "capital_allocation": "preserve",
                "compute_policy": "cost_minimized",
                "revenue_priority": "high",
                "reason": "runway or inflow coverage is below the sustainability target",
                "health": health,
            }

        return {
            "action": "scale_productive_capacity",
            "capital_allocation": "selective",
            "compute_policy": "roi_gated",
            "revenue_priority": "high",
            "reason": "positive churn and sufficient runway support selective reinvestment",
            "health": health,
        }

    def report(self) -> Dict[str, Any]:
        return {
            "component": "EconomicSustainability",
            "mode": "decision_only",
            "optimization": "positive_churn",
            "penalty": "negative_churn",
            "minimum_runway_periods": self.minimum_runway_periods,
            "target_coverage": self.target_coverage,
            "execution": "requires_separate_authorized_adapter",
        }
