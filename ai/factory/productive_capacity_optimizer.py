"""Unified productive-capacity economics for the autonomous Factory.

Money, compute, hardware, and software output are treated as one resource loop.
The optimizer is decision-only: it ranks resource strategies but never moves
money, purchases infrastructure, or performs external mutations itself.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class CapacityOpportunity:
    """One candidate way to increase sustainable autonomous capacity."""

    opportunity_id: str
    resource: str  # software, compute, hardware, capital, or revenue
    expected_value: float
    incremental_cost: float
    probability: float = 1.0
    time_to_value_hours: float = 1.0
    risk: float = 0.0
    capacity_gain: float = 0.0
    recurring_burn: float = 0.0
    free_resource: bool = False

    def validate(self) -> None:
        if not self.opportunity_id.strip():
            raise ValueError("opportunity_id must not be empty")
        if self.resource not in {"software", "compute", "hardware", "capital", "revenue"}:
            raise ValueError("unsupported resource type")
        for name in asdict(self):
            if name in {"opportunity_id", "resource", "free_resource"}:
                continue
            value = float(getattr(self, name))
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.probability > 1:
            raise ValueError("probability must be <= 1")


class ProductiveCapacityOptimizer:
    """Optimize the conversion of scarce resources into sustainable capacity."""

    def __init__(self, *, capital_floor_fraction: float = 0.50):
        if not 0 <= capital_floor_fraction <= 1:
            raise ValueError("capital_floor_fraction must be between 0 and 1")
        self.capital_floor_fraction = float(capital_floor_fraction)

    @staticmethod
    def score(opportunity: CapacityOpportunity) -> float:
        opportunity.validate()
        expected_value = opportunity.expected_value * opportunity.probability
        net_value = expected_value - opportunity.incremental_cost - opportunity.recurring_burn
        risk_penalty = opportunity.risk * max(expected_value, 1.0)
        time_penalty = max(opportunity.time_to_value_hours, 0.0) / 168.0
        return (net_value - risk_penalty) / (1.0 + time_penalty)

    def rank(self, opportunities: Iterable[CapacityOpportunity]) -> List[Dict[str, Any]]:
        ranked = []
        for opportunity in opportunities:
            score = self.score(opportunity)
            ranked.append({"opportunity": opportunity.opportunity_id,
                           "resource": opportunity.resource,
                           "score": score,
                           "positive_churn": score > 0,
                           "capacity_gain": opportunity.capacity_gain,
                           "free_resource": opportunity.free_resource})
        return sorted(ranked, key=lambda item: (item["score"], item["capacity_gain"]), reverse=True)

    def decide(self, *, available_capital: float,
               protected_capital: float,
               opportunities: Iterable[CapacityOpportunity]) -> Dict[str, Any]:
        if not isfinite(available_capital) or available_capital < 0:
            raise ValueError("available_capital must be finite and non-negative")
        if not isfinite(protected_capital) or protected_capital < 0:
            raise ValueError("protected_capital must be finite and non-negative")
        if protected_capital > available_capital:
            raise ValueError("protected_capital cannot exceed available_capital")

        ranked = self.rank(opportunities)
        positive = [item for item in ranked if item["positive_churn"]]
        free_positive = [item for item in positive if item["free_resource"]]
        deployable = available_capital - protected_capital

        if free_positive:
            return {"action": "use_free_capacity_first", "allocation_budget": 0.0,
                    "selected": free_positive[0], "ranked": ranked}
        if positive and deployable > 0:
            return {"action": "reinvest_in_positive_churn", "allocation_budget": deployable,
                    "selected": positive[0], "ranked": ranked}
        return {"action": "preserve_resources_and_generate_revenue", "allocation_budget": 0.0,
                "selected": None, "ranked": ranked}

    def report(self) -> Dict[str, Any]:
        return {
            "component": "ProductiveCapacityOptimizer",
            "objective": "maximize_sustainable_productive_capacity",
            "unified_resources": ["money", "compute", "hardware", "software", "revenue"],
            "positive_churn": "optimize_and_reinvest",
            "negative_churn": "penalize_and_contract",
            "free_capacity": "preferred",
            "execution": "requires_existing_authorized_adapters",
            "capital_floor_fraction": self.capital_floor_fraction,
        }
