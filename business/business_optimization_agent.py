#!/usr/bin/env python3
"""
Business Optimization Agent
Uses AI Nexus to continuously improve Yair Siegel's business operations
Analyzes business profile, identifies opportunities, and implements improvements
"""
import json
import pathlib
import datetime
import sys
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from business.yair_siegel_business_profile import BusinessProfileManager, YairSiegelBusinessProfile

REPO_ROOT = pathlib.Path(__file__).parent.parent
OPTIMIZATION_LOG = REPO_ROOT / "business/data/optimization_log.jsonl"
OPTIMIZATION_STATE = REPO_ROOT / "business/data/optimization_state.json"
ACTIONS_TAKEN = REPO_ROOT / "business/data/optimization_actions.jsonl"


class BusinessOptimizationAgent:
    """AI-driven agent for business optimization"""

    def __init__(self):
        self.profile_manager = BusinessProfileManager()
        self.optimization_log_path = OPTIMIZATION_LOG
        self.optimization_state_path = OPTIMIZATION_STATE
        self.actions_taken_path = ACTIONS_TAKEN
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure required directories exist"""
        self.optimization_log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log an optimization event"""
        event = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "details": details,
        }
        with open(self.optimization_log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def log_action(self, action_type: str, description: str, expected_impact: str, status: str = "proposed"):
        """Log an optimization action"""
        action = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "action_type": action_type,
            "description": description,
            "expected_impact": expected_impact,
            "status": status,
        }
        with open(self.actions_taken_path, "a") as f:
            f.write(json.dumps(action) + "\n")
        return action

    def analyze_credit_optimization(self, profile: YairSiegelBusinessProfile) -> List[Dict[str, Any]]:
        """Analyze credit utilization and suggest optimizations"""
        suggestions = []

        util = profile.credit_profile.credit_utilization
        total_balance = profile.credit_profile.total_credit_balance
        total_liquid = profile.business_accounts.total_business_liquid + profile.personal_accounts.total_personal_liquid

        # High utilization - suggest paydown
        if util > 0.50:
            paydown_target = profile.credit_profile.total_credit_limit * 0.30
            paydown_amount = total_balance - paydown_target
            if paydown_amount > 0 and total_liquid >= paydown_amount:
                suggestions.append({
                    "priority": "HIGH",
                    "category": "credit_optimization",
                    "action": "pay_down_credit",
                    "description": f"Pay down ${paydown_amount:.2f} to reduce utilization to 30%",
                    "expected_impact": f"Credit score improvement (+10-30 points), utilization reduction to 30%",
                    "required_capital": paydown_amount,
                    "feasible": True,
                })
            elif paydown_amount > 0:
                suggestions.append({
                    "priority": "HIGH",
                    "category": "credit_optimization",
                    "action": "pay_down_credit_partial",
                    "description": f"Pay down ${total_liquid:.2f} from available liquid (need ${paydown_amount:.2f})",
                    "expected_impact": f"Partial utilization reduction, some credit score improvement",
                    "required_capital": total_liquid,
                    "feasible": True,
                })

        # Cashback optimization
        cashback_balance = profile.business_accounts.paypal_cashback_balance
        if cashback_balance > 3000 and util > 0.10:
            # Use cashback to pay down credit
            suggestions.append({
                "priority": "MEDIUM",
                "category": "cash_flow_optimization",
                "action": "deploy_cashback_to_credit",
                "description": f"Use ${cashback_balance:.2f} cashback to pay down credit",
                "expected_impact": f"Reduce credit balance, improve utilization by {(cashback_balance/profile.credit_profile.total_credit_limit)*100:.1f}%",
                "required_capital": 0,
                "feasible": True,
            })

        return suggestions

    def analyze_cash_flow_optimization(self, profile: YairSiegelBusinessProfile) -> List[Dict[str, Any]]:
        """Analyze cash flow and suggest optimizations"""
        suggestions = []

        business_liquid = profile.business_accounts.total_business_liquid
        personal_liquid = profile.personal_accounts.total_personal_liquid

        # Excess business liquid - suggest rebalancing
        if business_liquid > 5000 and personal_liquid < 1000:
            transfer_amount = min(business_liquid - 3000, 2000)
            suggestions.append({
                "priority": "MEDIUM",
                "category": "cash_flow_optimization",
                "action": "rebalance_liquidity",
                "description": f"Transfer ${transfer_amount:.2f} from business to personal for better balance",
                "expected_impact": "Improved personal safety buffer, maintains business operations",
                "required_capital": 0,
                "feasible": True,
            })

        # Low overall liquid - suggest income focus
        total_liquid = business_liquid + personal_liquid
        if total_liquid < 1000:
            suggestions.append({
                "priority": "CRITICAL",
                "category": "cash_flow_optimization",
                "action": "increase_income_focus",
                "description": "Focus on income generation - liquid reserves critically low",
                "expected_impact": "Improve financial stability, increase runway",
                "required_capital": 0,
                "feasible": True,
            })

        return suggestions

    def analyze_trading_system_optimization(self, profile: YairSiegelBusinessProfile) -> List[Dict[str, Any]]:
        """Analyze trading system and suggest optimizations"""
        suggestions = []

        # If trading system is negative, suggest review
        if profile.business_operations.net_trading_pnl < 0:
            suggestions.append({
                "priority": "HIGH",
                "category": "trading_optimization",
                "action": "review_alpha_model",
                "description": "Review and improve alpha model - current PnL is negative",
                "expected_impact": "Improve trading edge, reduce losses",
                "required_capital": 0,
                "feasible": True,
            })

        # If ROI is low but AI costs are high
        if profile.business_operations.monthly_ai_cost > 50 and profile.business_operations.system_roi_pct < 5:
            suggestions.append({
                "priority": "MEDIUM",
                "category": "cost_optimization",
                "action": "optimize_ai_costs",
                "description": f"Reduce AI costs (${profile.business_operations.monthly_ai_cost:.2f}/month) - ROI is low",
                "expected_impact": "Improve profitability, better cost efficiency",
                "required_capital": 0,
                "feasible": True,
            })

        # If system uptime is low
        if profile.business_operations.automation_uptime_pct < 95:
            suggestions.append({
                "priority": "HIGH",
                "category": "reliability_optimization",
                "action": "improve_automation_reliability",
                "description": f"Fix automation issues - uptime is {profile.business_operations.automation_uptime_pct:.1f}%",
                "expected_impact": "Increased reliability, reduced manual intervention",
                "required_capital": 0,
                "feasible": True,
            })

        return suggestions

    def analyze_business_growth(self, profile: YairSiegelBusinessProfile) -> List[Dict[str, Any]]:
        """Analyze business growth opportunities"""
        suggestions = []

        # Strong health score - suggest growth investments
        if profile.business_health.business_score > 75:
            suggestions.append({
                "priority": "LOW",
                "category": "growth_opportunity",
                "action": "consider_growth_investments",
                "description": "Business health is strong - consider strategic growth investments",
                "expected_impact": "Accelerated growth, increased returns",
                "required_capital": 1000,
                "feasible": profile.business_health.total_net_worth > 2000,
            })

        # Good credit score - suggest credit limit increases
        if profile.credit_profile.credit_score >= 720 and profile.credit_profile.credit_utilization < 0.30:
            suggestions.append({
                "priority": "LOW",
                "category": "credit_expansion",
                "action": "request_credit_limit_increases",
                "description": "Strong credit profile - request credit limit increases for better flexibility",
                "expected_impact": "Increased financial flexibility, lower utilization ratio",
                "required_capital": 0,
                "feasible": True,
            })

        return suggestions

    def generate_optimization_recommendations(self, profile: YairSiegelBusinessProfile) -> Dict[str, Any]:
        """Generate comprehensive optimization recommendations"""
        recommendations = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "profile_health_score": profile.business_health.business_score,
            "suggestions": [],
        }

        # Analyze different areas
        credit_suggestions = self.analyze_credit_optimization(profile)
        cashflow_suggestions = self.analyze_cash_flow_optimization(profile)
        trading_suggestions = self.analyze_trading_system_optimization(profile)
        growth_suggestions = self.analyze_business_growth(profile)

        # Combine all suggestions
        all_suggestions = credit_suggestions + cashflow_suggestions + trading_suggestions + growth_suggestions

        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        all_suggestions.sort(key=lambda x: priority_order.get(x["priority"], 4))

        recommendations["suggestions"] = all_suggestions

        return recommendations

    def run_optimization_cycle(self) -> Dict[str, Any]:
        """Run a complete optimization cycle"""
        self.log_event("optimization_cycle_start", {})

        # Load current profile
        profile = self.profile_manager.generate_current_profile()

        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(profile)

        # Log recommendations
        self.log_event("recommendations_generated", {
            "count": len(recommendations["suggestions"]),
            "health_score": recommendations["profile_health_score"],
        })

        # Log each recommendation as a potential action
        for suggestion in recommendations["suggestions"]:
            self.log_action(
                action_type=suggestion["category"],
                description=suggestion["description"],
                expected_impact=suggestion["expected_impact"],
                status="proposed",
            )

        result = {
            "timestamp": recommendations["timestamp"],
            "profile": {
                "net_worth": profile.business_health.total_net_worth,
                "health_score": profile.business_health.business_score,
                "credit_utilization": profile.credit_profile.credit_utilization,
            },
            "recommendations_count": len(recommendations["suggestions"]),
            "recommendations": recommendations["suggestions"],
        }

        self.log_event("optimization_cycle_complete", result)

        return result

    def get_optimization_report(self) -> str:
        """Generate human-readable optimization report"""
        result = self.run_optimization_cycle()

        lines = [
            "=" * 80,
            "YAIR SIEGEL BUSINESS OPTIMIZATION REPORT",
            "=" * 80,
            f"Timestamp: {result['timestamp']}",
            f"Business Health Score: {result['profile']['health_score']}/100",
            f"Net Worth: ${result['profile']['net_worth']:,.2f}",
            f"Credit Utilization: {result['profile']['credit_utilization']*100:.1f}%",
            "",
            f"OPTIMIZATION RECOMMENDATIONS ({result['recommendations_count']}):",
            "",
        ]

        if result["recommendations"]:
            for i, rec in enumerate(result["recommendations"], 1):
                lines.append(f"{i}. [{rec['priority']}] {rec['category'].upper()}")
                lines.append(f"   Action: {rec['description']}")
                lines.append(f"   Impact: {rec['expected_impact']}")
                lines.append(f"   Feasible: {'Yes' if rec['feasible'] else 'No'}")
                if rec.get("required_capital", 0) > 0:
                    lines.append(f"   Capital Required: ${rec['required_capital']:.2f}")
                lines.append("")
        else:
            lines.append("No optimization opportunities identified - business is operating optimally!")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    """Main entry point"""
    agent = BusinessOptimizationAgent()

    print("Running Business Optimization Analysis...\n")
    report = agent.get_optimization_report()
    print(report)

    print(f"\nOptimization log saved to: {agent.optimization_log_path}")
    print(f"Actions logged to: {agent.actions_taken_path}")


if __name__ == "__main__":
    main()
