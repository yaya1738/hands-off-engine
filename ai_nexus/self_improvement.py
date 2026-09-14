#!/usr/bin/env python3
"""
Self-improvement system for AI Nexus
Analyzes performance and makes recommendations for optimization
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from audit import AuditLogger, FinancialLedger


@dataclass
class PerformanceMetrics:
    """Performance metrics for a component or session"""
    component: str
    total_actions: int
    success_rate: float
    avg_cost_per_action: float
    total_cost: float
    total_revenue: float
    net_profit: float
    roi_percent: float
    avg_latency_ms: float
    error_count: int


@dataclass
class Recommendation:
    """Self-improvement recommendation"""
    priority: str  # "high", "medium", "low"
    category: str  # "cost_reduction", "performance", "reliability", "revenue"
    title: str
    description: str
    expected_impact: str
    action_items: List[str]


class SelfImprovementEngine:
    """
    Analyzes system performance and generates improvement recommendations

    Features:
    - Cost optimization suggestions
    - Performance improvement recommendations
    - Reliability enhancements
    - Revenue optimization strategies
    - Budget reallocation advice
    """

    def __init__(self, audit_logger: AuditLogger, ledger: FinancialLedger):
        self.audit_logger = audit_logger
        self.ledger = ledger

    def analyze_component_performance(self, component: str) -> PerformanceMetrics:
        """
        Analyze performance metrics for a specific component

        Args:
            component: Component name (e.g., "ai.claude", "trading.polymarket")

        Returns:
            PerformanceMetrics object
        """
        # Get audit events
        events = self.audit_logger.get_events(component=component)

        if not events:
            return PerformanceMetrics(
                component=component,
                total_actions=0,
                success_rate=0.0,
                avg_cost_per_action=0.0,
                total_cost=0.0,
                total_revenue=0.0,
                net_profit=0.0,
                roi_percent=0.0,
                avg_latency_ms=0.0,
                error_count=0
            )

        # Calculate metrics
        total_actions = len(events)
        errors = sum(1 for e in events if e.error)
        success_rate = ((total_actions - errors) / total_actions) * 100

        total_cost = sum(e.cost or 0 for e in events)
        total_revenue = sum(e.revenue or 0 for e in events)
        net_profit = total_revenue - total_cost
        roi_percent = (net_profit / total_cost * 100) if total_cost > 0 else 0

        avg_cost = total_cost / total_actions if total_actions > 0 else 0

        # Calculate average latency if available
        latencies = [e.metadata.get("latency_ms", 0) for e in events]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        return PerformanceMetrics(
            component=component,
            total_actions=total_actions,
            success_rate=success_rate,
            avg_cost_per_action=avg_cost,
            total_cost=total_cost,
            total_revenue=total_revenue,
            net_profit=net_profit,
            roi_percent=roi_percent,
            avg_latency_ms=avg_latency,
            error_count=errors
        )

    def generate_recommendations(
        self,
        session_id: Optional[str] = None
    ) -> List[Recommendation]:
        """
        Generate self-improvement recommendations

        Args:
            session_id: Optional session to analyze (None for all sessions)

        Returns:
            List of Recommendation objects
        """
        recommendations = []

        # Get overall metrics
        if session_id:
            events = self.audit_logger.get_events(session_id=session_id)
            balance = self.ledger.get_balance(session_id=session_id)
        else:
            events = self.audit_logger.get_events()
            balance = self.ledger.get_balance()

        # Analyze financial performance
        roi = balance["roi_percent"]

        if roi < 0:
            recommendations.append(Recommendation(
                priority="high",
                category="revenue",
                title="Negative ROI - Urgent Action Required",
                description=f"System is operating at a loss (ROI: {roi:.1f}%). "
                           "Costs exceed revenues.",
                expected_impact="Return to profitability",
                action_items=[
                    "Review and reduce AI model costs (switch to cheaper models)",
                    "Increase trading frequency or position sizes",
                    "Implement more aggressive trading strategies",
                    "Review and eliminate unprofitable components"
                ]
            ))
        elif roi < 50:
            recommendations.append(Recommendation(
                priority="medium",
                category="cost_reduction",
                title="Low ROI - Cost Optimization Recommended",
                description=f"ROI is below target (current: {roi:.1f}%, target: >50%). "
                           "There's room for cost optimization.",
                expected_impact="Increase ROI by 20-50%",
                action_items=[
                    "Use GPT-4o-mini instead of GPT-4o for non-critical tasks",
                    "Implement caching for repeated queries",
                    "Batch similar requests to reduce API calls",
                    "Use Claude Haiku for simple tasks"
                ]
            ))
        elif roi > 200:
            recommendations.append(Recommendation(
                priority="high",
                category="revenue",
                title="Excellent ROI - Scale Up Recommended",
                description=f"ROI is exceptional (current: {roi:.1f}%). "
                           "System is highly profitable and should be scaled.",
                expected_impact="Multiply profits by increasing investment",
                action_items=[
                    "Increase AI budget by 50-100%",
                    "Scale up trading positions",
                    "Deploy more AI agents for market monitoring",
                    "Explore additional revenue streams"
                ]
            ))

        # Analyze component performance
        component_perf = self.ledger.get_component_performance()

        for component, stats in component_perf.items():
            comp_roi = stats["roi_percent"]

            if comp_roi < 0:
                recommendations.append(Recommendation(
                    priority="high",
                    category="cost_reduction",
                    title=f"Unprofitable Component: {component}",
                    description=f"{component} is losing money (ROI: {comp_roi:.1f}%). "
                               f"Costs: ${stats['total_cost']:.2f}, "
                               f"Revenue: ${stats['total_revenue']:.2f}",
                    expected_impact="Eliminate losses or remove component",
                    action_items=[
                        f"Review {component} usage patterns",
                        "Reduce frequency of unprofitable operations",
                        "Consider disabling or optimizing component",
                        "Investigate alternative implementations"
                    ]
                ))

        # Analyze error rates
        component_stats = {}
        for event in events:
            if event.component not in component_stats:
                component_stats[event.component] = {"total": 0, "errors": 0}
            component_stats[event.component]["total"] += 1
            if event.error:
                component_stats[event.component]["errors"] += 1

        for component, stats in component_stats.items():
            error_rate = (stats["errors"] / stats["total"]) * 100
            if error_rate > 10:
                recommendations.append(Recommendation(
                    priority="high",
                    category="reliability",
                    title=f"High Error Rate: {component}",
                    description=f"{component} has a {error_rate:.1f}% error rate "
                               f"({stats['errors']} errors out of {stats['total']} operations)",
                    expected_impact="Improve reliability and reduce wasted costs",
                    action_items=[
                        "Review error logs for common failure patterns",
                        "Add retry logic with exponential backoff",
                        "Improve error handling and recovery",
                        "Add input validation to prevent errors"
                    ]
                ))

        # Cost efficiency recommendations
        if balance["total_costs"] > 100:
            recommendations.append(Recommendation(
                priority="medium",
                category="cost_reduction",
                title="High Overall Costs Detected",
                description=f"Total costs are ${balance['total_costs']:.2f}. "
                           "Consider implementing cost optimization strategies.",
                expected_impact="Reduce costs by 20-30%",
                action_items=[
                    "Implement request caching",
                    "Use cheaper models for non-critical tasks",
                    "Batch similar requests",
                    "Add rate limiting to prevent runaway costs",
                    "Implement cost budgets per component"
                ]
            ))

        # Sort recommendations by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order[r.priority])

        return recommendations

    def get_optimal_budget_allocation(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate optimal budget allocation based on component ROI

        Returns:
            Dictionary mapping component to budget recommendations
        """
        component_perf = self.ledger.get_component_performance()

        # Calculate total current budget
        total_budget = sum(stats["total_cost"] for stats in component_perf.values())

        if total_budget == 0:
            return {}

        # Calculate allocation based on ROI
        # Components with higher ROI should get more budget
        allocations = {}

        for component, stats in component_perf.items():
            current_budget = stats["total_cost"]
            current_roi = stats["roi_percent"]

            # Calculate recommended budget adjustment
            if current_roi > 100:
                # Highly profitable - increase budget
                adjustment = 1.5
            elif current_roi > 50:
                # Profitable - slight increase
                adjustment = 1.2
            elif current_roi > 0:
                # Marginally profitable - maintain
                adjustment = 1.0
            elif current_roi > -50:
                # Small loss - reduce
                adjustment = 0.7
            else:
                # Large loss - significantly reduce
                adjustment = 0.3

            recommended_budget = current_budget * adjustment

            allocations[component] = {
                "current_budget": current_budget,
                "current_roi": current_roi,
                "recommended_budget": recommended_budget,
                "adjustment_factor": adjustment,
                "reasoning": self._get_budget_reasoning(current_roi, adjustment)
            }

        return allocations

    def _get_budget_reasoning(self, roi: float, adjustment: float) -> str:
        """Generate reasoning for budget recommendation"""
        if adjustment > 1.3:
            return f"Excellent ROI ({roi:.1f}%) - scale up to maximize profits"
        elif adjustment > 1.0:
            return f"Good ROI ({roi:.1f}%) - increase investment moderately"
        elif adjustment == 1.0:
            return f"Adequate ROI ({roi:.1f}%) - maintain current budget"
        elif adjustment > 0.5:
            return f"Low ROI ({roi:.1f}%) - reduce spending"
        else:
            return f"Negative ROI ({roi:.1f}%) - significantly cut or eliminate"
