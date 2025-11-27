#!/usr/bin/env python3
"""
Quick Add Cash Opportunity
Fast CLI for adding today's opportunity
"""
import sys
import json
import datetime

sys.path.insert(0, str(__file__).replace('/business/quick_add_opportunity.py', ''))

from business.cash_explosion_opportunities import CashOpportunity, CashExplosionManager


def quick_add(title, revenue, hours_to_cash=24, effort=1, confidence=0.7, priority="high", category="other"):
    """Quick add opportunity with minimal inputs"""

    opp = CashOpportunity({
        "title": title,
        "description": f"Opportunity added on {datetime.datetime.utcnow().strftime('%Y-%m-%d')}",
        "category": category,
        "potential_revenue": revenue,
        "time_to_cash_hours": hours_to_cash,
        "effort_hours": effort,
        "required_capital": 0,
        "confidence": confidence,
        "risk_level": "medium",
        "priority": priority,
        "action_steps": ["Execute opportunity", "Receive payment"],
        "notes": "Added via quick_add",
    })

    manager = CashExplosionManager()
    opp_id = manager.add_opportunity(opp)

    print(f"✅ Added: {title}")
    print(f"   Expected: ${opp.expected_value():.2f}")
    print(f"   Hourly Rate: ${opp.hourly_rate():.2f}/hr")
    print(f"   ID: {opp_id}")

    return opp_id


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Quick add cash opportunity")
    parser.add_argument("title", help="Opportunity title")
    parser.add_argument("revenue", type=float, help="Potential revenue ($)")
    parser.add_argument("--hours", type=float, default=24, help="Hours to cash (default: 24)")
    parser.add_argument("--effort", type=float, default=1, help="Effort hours (default: 1)")
    parser.add_argument("--confidence", type=float, default=0.7, help="Confidence 0-1 (default: 0.7)")
    parser.add_argument("--priority", choices=["critical", "high", "medium", "low"], default="high")
    parser.add_argument("--category", choices=["trading", "gig", "contract", "sale", "investment", "other"], default="other")

    args = parser.parse_args()

    quick_add(
        title=args.title,
        revenue=args.revenue,
        hours_to_cash=args.hours,
        effort=args.effort,
        confidence=args.confidence,
        priority=args.priority,
        category=args.category,
    )

    print("\nRun dashboard: python3 business/cash_explosion_opportunities.py")
