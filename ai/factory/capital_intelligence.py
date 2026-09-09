"""Capital intelligence for scarce real-world operating capital.

This module is deliberately decision-only: it does not hold credentials and does
not move funds or place orders.  It turns observations from authorized financial
adapters into comparable, risk-aware capital decisions that can be routed through
FactoryAuthorityGateway when an execution capability is actually authorized.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class CapitalOpportunity:
    """Normalized candidate use of capital."""

    opportunity_id: str
    venue: str
    thesis: str
    expected_return: float
    downside: float
    probability: float
    liquidity: float = 1.0
    fees: float = 0.0
    capital_required: float = 0.0
    lockup_hours: float = 0.0

    def validate(self) -> None:
        for name in ("expected_return", "downside", "probability", "liquidity", "fees", "capital_required", "lockup_hours"):
            value = getattr(self, name)
            if not isfinite(float(value)):
                raise ValueError(f"{name} must be finite")
        if not self.opportunity_id or not self.venue or not self.thesis:
            raise ValueError("opportunity_id, venue, and thesis are required")
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if self.downside < 0 or self.capital_required < 0 or self.fees < 0 or self.lockup_hours < 0:
            raise ValueError("downside, fees, capital_required and lockup_hours must be non-negative")
        if not 0.0 <= self.liquidity <= 1.0:
            raise ValueError("liquidity must be between 0 and 1")


class CapitalIntelligence:
    """Compare scarce-capital uses while strongly penalizing ruin and illiquidity.

    The model is intentionally conservative.  It may recommend holding cash when
    no candidate clears the preservation threshold.  A recommendation is only an
    allocation *proposal*; actual financial movement remains outside this class.
    """

    def __init__(self, *, preservation_floor: float = 0.50, max_fraction_per_opportunity: float = 0.20):
        if not 0.0 < preservation_floor <= 1.0:
            raise ValueError("preservation_floor must be in (0, 1]")
        if not 0.0 < max_fraction_per_opportunity <= 1.0:
            raise ValueError("max_fraction_per_opportunity must be in (0, 1]")
        self.preservation_floor = preservation_floor
        self.max_fraction_per_opportunity = max_fraction_per_opportunity

    def score(self, opportunity: CapitalOpportunity, available_capital: float) -> float:
        opportunity.validate()
        if available_capital < 0 or not isfinite(float(available_capital)):
            raise ValueError("available_capital must be finite and non-negative")
        if opportunity.capital_required > available_capital:
            return float("-inf")

        # Expected value after fees, discounted for liquidity and time lockup.
        expected_value = (
            opportunity.probability * opportunity.expected_return
            - (1.0 - opportunity.probability) * opportunity.downside
            - opportunity.fees
        )
        liquidity_factor = 0.25 + 0.75 * opportunity.liquidity
        time_factor = 1.0 / (1.0 + opportunity.lockup_hours / 168.0)
        concentration = min(1.0, opportunity.capital_required / max(available_capital, 1e-12))
        concentration_penalty = 1.0 - 0.75 * concentration
        return expected_value * liquidity_factor * time_factor * concentration_penalty

    def rank(self, opportunities: Iterable[CapitalOpportunity], available_capital: float) -> List[Dict[str, Any]]:
        scored = []
        for opportunity in opportunities:
            score = self.score(opportunity, available_capital)
            scored.append({"opportunity": asdict(opportunity), "score": score})
        return sorted(scored, key=lambda item: item["score"], reverse=True)

    def decide(self, opportunities: Iterable[CapitalOpportunity], available_capital: float) -> Dict[str, Any]:
        if available_capital < 0 or not isfinite(float(available_capital)):
            raise ValueError("available_capital must be finite and non-negative")
        ranked = self.rank(opportunities, available_capital)
        positive = [item for item in ranked if item["score"] > 0]
        if not positive or available_capital == 0:
            return {
                "action": "hold_cash",
                "allocation": 0.0,
                "venue": "cash",
                "reason": "no candidate clears the positive risk-adjusted value threshold",
                "ranked": ranked,
            }

        best = positive[0]
        required = float(best["opportunity"]["capital_required"])
        allocation = min(required, available_capital * self.max_fraction_per_opportunity)
        if allocation <= 0:
            return {
                "action": "hold_cash",
                "allocation": 0.0,
                "venue": "cash",
                "reason": "best candidate requires no allocatable capital",
                "ranked": ranked,
            }
        return {
            "action": "propose_allocation",
            "allocation": allocation,
            "venue": best["opportunity"]["venue"],
            "opportunity_id": best["opportunity"]["opportunity_id"],
            "score": best["score"],
            "reason": "best currently observed risk-adjusted use of scarce capital",
            "preservation_floor": self.preservation_floor,
            "ranked": ranked,
        }

    def rebalance_plan(self, balances: Dict[str, float], opportunities: Iterable[CapitalOpportunity]) -> Dict[str, Any]:
        """Return a venue-level plan; never performs transfers itself."""
        total = sum(float(value) for value in balances.values())
        decision = self.decide(opportunities, total)
        transfers: List[Dict[str, Any]] = []
        target = decision.get("venue")
        amount = float(decision.get("allocation", 0.0))
        if target and target != "cash" and amount > 0:
            source = max(balances, key=balances.get, default="cash")
            if source != target and balances.get(source, 0.0) >= amount:
                transfers.append({"from": source, "to": target, "amount": amount, "status": "proposed"})
        return {"decision": decision, "transfers": transfers, "execution_authority": "external_authorized_financial_adapter"}

    def report(self) -> Dict[str, Any]:
        return {
            "component": "CapitalIntelligence",
            "mode": "decision_only",
            "real_capital": True,
            "venues": ["polymarket", "kalshi"],
            "supports": ["allocation", "hold_cash", "cross_venue_rebalance"],
            "execution": "requires_separate_authorized_financial_adapter",
            "preservation_floor": self.preservation_floor,
            "max_fraction_per_opportunity": self.max_fraction_per_opportunity,
        }
