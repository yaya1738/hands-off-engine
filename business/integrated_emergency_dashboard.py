#!/usr/bin/env python3
"""
Integrated Emergency Dashboard
Combines financial emergency status with cash opportunities
Shows complete picture and action plan
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from business.yair_siegel_business_profile import BusinessProfileManager
from business.cash_explosion_opportunities import CashExplosionManager
import json
import datetime

REPO_ROOT = pathlib.Path(__file__).parent.parent


def main():
    print("=" * 80)
    print("🚨 INTEGRATED EMERGENCY DASHBOARD 🚨")
    print("=" * 80)
    print(f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Load profile
    profile_mgr = BusinessProfileManager()
    profile = profile_mgr.generate_current_profile()

    # Load opportunities
    opp_mgr = CashExplosionManager()
    emergency_opps = opp_mgr.get_emergency_opportunities()
    all_opps = opp_mgr.get_active_opportunities()

    # Emergency mode check
    emergency_mode_file = REPO_ROOT / "business/data/emergency_mode.json"
    emergency_active = False
    if emergency_mode_file.exists():
        config = json.loads(emergency_mode_file.read_text())
        emergency_active = config.get("enabled", False)

    # SECTION 1: CURRENT SITUATION
    print("📊 CURRENT SITUATION")
    print("-" * 80)

    personal_liquid = profile.personal_accounts.total_personal_liquid
    total_liquid = personal_liquid + profile.business_accounts.total_business_liquid
    credit_util = profile.credit_profile.credit_utilization

    print(f"Personal Cash:      ${personal_liquid:,.2f} {'🔴' if personal_liquid < 2000 else '✅'}")
    print(f"Total Liquid:       ${total_liquid:,.2f}")
    print(f"Credit Util:        {credit_util*100:.1f}% {'🔴 OVERLIMIT' if credit_util >= 1.0 else '⚠️' if credit_util >= 0.7 else '✅'}")
    print(f"Emergency Mode:     {'🔴 ACTIVE' if emergency_active else '✅ Inactive'}")
    print()

    # SECTION 2: CASH OPPORTUNITIES
    print("💰 CASH EXPLOSION OPPORTUNITIES")
    print("-" * 80)

    if emergency_opps:
        total_emergency_potential = sum(opp.expected_value() for opp in emergency_opps)

        print(f"Emergency-Ready Opportunities: {len(emergency_opps)}")
        print(f"Total Potential (< 48hr):      ${total_emergency_potential:,.2f}")
        print()

        print("TOP 3 EMERGENCY OPPORTUNITIES:")
        for i, opp in enumerate(emergency_opps[:3], 1):
            print(f"{i}. {opp.title}")
            print(f"   💵 ${opp.expected_value():.2f} in {opp.time_to_cash_hours}hrs")
            print(f"   ⚡ ${opp.hourly_rate():.2f}/hr | {opp.confidence*100:.0f}% confidence")
            print()
    else:
        print("⚠️  No emergency opportunities tracked yet")
        print("   Add opportunities: python3 business/quick_add_opportunity.py")
        print()

    # SECTION 3: IMPACT ANALYSIS
    if emergency_opps:
        print("📈 OPPORTUNITY IMPACT ANALYSIS")
        print("-" * 80)

        # Calculate impact if top 2 opportunities executed
        top_opps = emergency_opps[:2]
        impact_revenue = sum(opp.expected_value() for opp in top_opps)

        new_personal_cash = personal_liquid + impact_revenue
        overlimit_amt = max(0, profile.credit_profile.total_credit_balance - profile.credit_profile.total_credit_limit)

        print(f"If you execute top {len(top_opps)} opportunities:")
        print(f"  Expected Revenue:     ${impact_revenue:,.2f}")
        print(f"  Personal Cash After:  ${new_personal_cash:,.2f} (current: ${personal_liquid:,.2f})")

        if overlimit_amt > 0:
            remaining_overlimit = max(0, overlimit_amt - impact_revenue)
            print(f"  Credit Overlimit:     ${remaining_overlimit:,.2f} (current: ${overlimit_amt:,.2f})")

            if remaining_overlimit == 0:
                print(f"  ✅ THIS WOULD ELIMINATE OVERLIMIT!")
            elif remaining_overlimit < overlimit_amt:
                print(f"  ✅ This would reduce overlimit by ${overlimit_amt - remaining_overlimit:,.2f}")

        # Runway impact
        daily_burn = 50  # Estimated
        current_runway = personal_liquid / daily_burn
        new_runway = new_personal_cash / daily_burn

        print(f"  Personal Runway:      {new_runway:.1f} days (current: {current_runway:.1f} days)")
        print()

    # SECTION 4: PRIORITIZED ACTION PLAN
    print("🎯 PRIORITIZED ACTION PLAN")
    print("-" * 80)

    actions = []

    # Action 1: Execute emergency opportunities
    if emergency_opps:
        top_opp = emergency_opps[0]
        actions.append({
            "priority": 1,
            "action": f"Execute: {top_opp.title}",
            "impact": f"${top_opp.expected_value():.2f} in {top_opp.time_to_cash_hours} hours",
            "urgency": "START TODAY",
        })

    # Action 2: Credit paydown (if overlimit)
    if credit_util >= 1.0:
        overlimit = profile.credit_profile.total_credit_balance - profile.credit_profile.total_credit_limit
        actions.append({
            "priority": 2,
            "action": "Pay down overlimit credit",
            "impact": f"Use ${overlimit:,.2f} from PayPal Cashback to get under limit",
            "urgency": "DO TODAY",
        })

    # Action 3: Second opportunity
    if len(emergency_opps) > 1:
        second_opp = emergency_opps[1]
        actions.append({
            "priority": 3,
            "action": f"Execute: {second_opp.title}",
            "impact": f"${second_opp.expected_value():.2f} in {second_opp.time_to_cash_hours} hours",
            "urgency": "START WITHIN 24 HOURS",
        })

    # Action 4: Spending freeze
    actions.append({
        "priority": 4,
        "action": "Maintain spending freeze",
        "impact": "Reduce burn rate from $50/day to $20/day",
        "urgency": "ONGOING",
    })

    # Action 5: Add more opportunities
    if len(all_opps) < 5:
        actions.append({
            "priority": 5,
            "action": "Identify more cash opportunities",
            "impact": "Build pipeline of income sources",
            "urgency": "DAILY",
        })

    for action in actions:
        print(f"{action['priority']}. [{action['urgency']}] {action['action']}")
        print(f"   Impact: {action['impact']}")
        print()

    # SECTION 5: QUICK COMMANDS
    print("⚡ QUICK COMMANDS")
    print("-" * 80)
    print("Add new opportunity:    python3 business/quick_add_opportunity.py \"Title\" AMOUNT")
    print("View opportunities:     python3 business/cash_explosion_opportunities.py")
    print("Emergency status:       python3 business/emergency_status_monitor.py")
    print("Full emergency plan:    cat business/EMERGENCY_ACTION_PLAN.md")
    print()

    print("=" * 80)


if __name__ == "__main__":
    main()
