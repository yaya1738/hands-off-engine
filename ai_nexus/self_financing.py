#!/usr/bin/env python3
"""
Self-financing system for AI Nexus
Automatically adjusts budgets and scales operations based on profitability
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

from audit import AuditLogger, FinancialLedger


@dataclass
class FinancingDecision:
    """Decision made by the self-financing system"""
    component: str
    action: str  # "scale_up", "scale_down", "maintain", "pause"
    current_budget: float
    recommended_budget: float
    reasoning: str
    expected_roi: float


class SelfFinancingEngine:
    """
    Autonomous self-financing system

    Features:
    - Monitors profitability in real-time
    - Automatically adjusts budgets based on ROI
    - Scales profitable operations
    - Reduces or pauses unprofitable operations
    - Reinvests profits into high-ROI activities
    """

    # ROI thresholds for decision making
    SCALE_UP_THRESHOLD = 100.0  # ROI > 100%
    MAINTAIN_THRESHOLD = 20.0   # ROI > 20%
    SCALE_DOWN_THRESHOLD = 0.0  # ROI > 0%
    PAUSE_THRESHOLD = -50.0     # ROI < -50%

    def __init__(self, audit_logger: AuditLogger, ledger: FinancialLedger):
        self.audit_logger = audit_logger
        self.ledger = ledger

    def analyze_and_decide(
        self,
        session_id: Optional[str] = None
    ) -> List[FinancingDecision]:
        """
        Analyze financial performance and make financing decisions

        Args:
            session_id: Optional session to analyze

        Returns:
            List of FinancingDecision objects
        """
        decisions = []

        # Get component performance
        component_perf = self.ledger.get_component_performance()

        for component, stats in component_perf.items():
            current_cost = stats["total_cost"]
            roi = stats["roi_percent"]

            # Make decision based on ROI
            if roi > self.SCALE_UP_THRESHOLD:
                # Highly profitable - scale up aggressively
                new_budget = current_cost * 2.0
                action = "scale_up"
                reasoning = (
                    f"Exceptional ROI of {roi:.1f}% justifies doubling budget. "
                    f"Current net profit: ${stats['net_profit']:.2f}. "
                    f"Scaling up could double profits to ${stats['net_profit'] * 2:.2f}."
                )
                expected_roi = roi * 0.9  # Assume slight decrease due to scaling

            elif roi > self.MAINTAIN_THRESHOLD:
                # Profitable - maintain with modest increase
                new_budget = current_cost * 1.2
                action = "maintain"
                reasoning = (
                    f"Good ROI of {roi:.1f}% justifies modest 20% budget increase. "
                    f"Current net profit: ${stats['net_profit']:.2f}."
                )
                expected_roi = roi * 0.95

            elif roi > self.SCALE_DOWN_THRESHOLD:
                # Marginally profitable - maintain current level
                new_budget = current_cost
                action = "maintain"
                reasoning = (
                    f"Marginal ROI of {roi:.1f}% suggests maintaining current budget. "
                    f"Monitor closely for improvements."
                )
                expected_roi = roi

            elif roi > self.PAUSE_THRESHOLD:
                # Unprofitable but not terrible - reduce
                new_budget = current_cost * 0.5
                action = "scale_down"
                reasoning = (
                    f"Negative ROI of {roi:.1f}% requires 50% budget cut. "
                    f"Current loss: ${abs(stats['net_profit']):.2f}. "
                    f"Reducing budget may improve efficiency."
                )
                expected_roi = roi * 1.2  # Hope for improvement with efficiency

            else:
                # Severely unprofitable - pause
                new_budget = 0.0
                action = "pause"
                reasoning = (
                    f"Severe loss with ROI of {roi:.1f}% requires pausing component. "
                    f"Current loss: ${abs(stats['net_profit']):.2f}. "
                    f"Resume only after addressing fundamental issues."
                )
                expected_roi = 0.0

            decisions.append(FinancingDecision(
                component=component,
                action=action,
                current_budget=current_cost,
                recommended_budget=new_budget,
                reasoning=reasoning,
                expected_roi=expected_roi
            ))

        # Log financing decisions
        for decision in decisions:
            self.audit_logger.log_event(
                component="ai_nexus.self_financing",
                action="budget_decision",
                metadata={
                    "target_component": decision.component,
                    "decision": decision.action,
                    "current_budget": decision.current_budget,
                    "recommended_budget": decision.recommended_budget,
                    "reasoning": decision.reasoning
                },
                session_id=session_id
            )

        return decisions

    def calculate_profit_reinvestment(self) -> Dict[str, float]:
        """
        Calculate how profits should be reinvested

        Returns:
            Dictionary mapping component to additional budget allocation
        """
        # Get overall balance
        balance = self.ledger.get_balance()
        net_profit = balance["net_profit"]

        if net_profit <= 0:
            return {}  # No profits to reinvest

        # Get component performance
        component_perf = self.ledger.get_component_performance()

        # Filter to profitable components
        profitable = {
            comp: stats for comp, stats in component_perf.items()
            if stats["roi_percent"] > self.MAINTAIN_THRESHOLD
        }

        if not profitable:
            return {}

        # Allocate profits proportional to ROI
        total_weighted_roi = sum(
            stats["roi_percent"] for stats in profitable.values()
        )

        allocations = {}
        for component, stats in profitable.items():
            # Weight by ROI
            weight = stats["roi_percent"] / total_weighted_roi
            allocation = net_profit * weight

            allocations[component] = allocation

        # Log reinvestment plan
        self.audit_logger.log_event(
            component="ai_nexus.self_financing",
            action="profit_reinvestment",
            metadata={
                "total_profit": net_profit,
                "allocations": allocations
            }
        )

        return allocations

    def get_sustainability_report(self) -> Dict[str, any]:
        """
        Generate a sustainability report showing if system is self-financing

        Returns:
            Dictionary with sustainability metrics
        """
        balance = self.ledger.get_balance()
        component_perf = self.ledger.get_component_performance()

        # Calculate runway (how long can system operate at current loss rate)
        net_profit = balance["net_profit"]
        total_costs = balance["total_costs"]

        # Assume we have a reserve fund (would need to be tracked separately in production)
        assumed_reserve = 1000.0  # $1000 reserve

        if net_profit < 0:
            # Calculate burn rate (loss per time period)
            # This is simplified - in production, calculate based on time
            burn_rate = abs(net_profit)
            runway_periods = assumed_reserve / burn_rate if burn_rate > 0 else float('inf')
            is_sustainable = False
            sustainability_status = "unsustainable"
        elif net_profit > total_costs * 0.2:  # 20% profit margin
            runway_periods = float('inf')
            is_sustainable = True
            sustainability_status = "highly_sustainable"
        else:
            runway_periods = float('inf')
            is_sustainable = True
            sustainability_status = "marginally_sustainable"

        # Identify most and least efficient components
        if component_perf:
            best_component = max(
                component_perf.items(),
                key=lambda x: x[1]["roi_percent"]
            )
            worst_component = min(
                component_perf.items(),
                key=lambda x: x[1]["roi_percent"]
            )
        else:
            best_component = None
            worst_component = None

        return {
            "is_sustainable": is_sustainable,
            "sustainability_status": sustainability_status,
            "net_profit": net_profit,
            "total_costs": total_costs,
            "total_revenue": balance["total_revenue"],
            "roi_percent": balance["roi_percent"],
            "runway_periods": runway_periods,
            "reserve_fund": assumed_reserve,
            "best_component": {
                "name": best_component[0],
                "roi": best_component[1]["roi_percent"],
                "profit": best_component[1]["net_profit"]
            } if best_component else None,
            "worst_component": {
                "name": worst_component[0],
                "roi": worst_component[1]["roi_percent"],
                "profit": worst_component[1]["net_profit"]
            } if worst_component else None,
            "recommendations": self._generate_sustainability_recommendations(
                is_sustainable,
                net_profit,
                balance["roi_percent"]
            )
        }

    def _generate_sustainability_recommendations(
        self,
        is_sustainable: bool,
        net_profit: float,
        roi: float
    ) -> List[str]:
        """Generate sustainability recommendations"""
        recommendations = []

        if not is_sustainable:
            recommendations.append(
                "⚠️  URGENT: System is not self-financing. "
                "Immediate action required to achieve profitability."
            )
            recommendations.append(
                "Cut costs by pausing low-performing components"
            )
            recommendations.append(
                "Increase revenue by scaling up trading operations"
            )
        elif roi < 50:
            recommendations.append(
                "💡 System is marginally self-financing. "
                "Optimize to improve ROI above 50%."
            )
            recommendations.append(
                "Focus on cost reduction through model optimization"
            )
        else:
            recommendations.append(
                "✅ System is highly self-financing and profitable!"
            )
            recommendations.append(
                "Consider scaling up successful strategies"
            )
            recommendations.append(
                f"Reinvest profits (${net_profit:.2f}) into high-ROI components"
            )

        return recommendations
