#!/usr/bin/env python3
"""
Emergency Status Monitor
Quick daily check on financial emergency status
"""
import json
import pathlib
import datetime
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from business.yair_siegel_business_profile import BusinessProfileManager

REPO_ROOT = pathlib.Path(__file__).parent.parent


def get_status_emoji(value, threshold_good, threshold_bad, lower_is_better=False):
    """Get status emoji based on value"""
    if lower_is_better:
        if value <= threshold_good:
            return "✅"
        elif value <= threshold_bad:
            return "⚠️"
        else:
            return "🔴"
    else:
        if value >= threshold_good:
            return "✅"
        elif value >= threshold_bad:
            return "⚠️"
        else:
            return "🔴"


def main():
    print("=" * 80)
    print("🚨 EMERGENCY FINANCIAL STATUS - DAILY CHECK 🚨")
    print("=" * 80)
    print(f"Date: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Load profile
    manager = BusinessProfileManager()
    profile = manager.generate_current_profile()

    # Check emergency mode
    emergency_mode_file = REPO_ROOT / "business/data/emergency_mode.json"
    emergency_active = False
    if emergency_mode_file.exists():
        config = json.loads(emergency_mode_file.read_text())
        emergency_active = config.get("enabled", False)

    print(f"Emergency Mode: {'🔴 ACTIVE' if emergency_active else '✅ Inactive'}")
    print()

    # Key metrics
    personal_liquid = profile.personal_accounts.total_personal_liquid
    total_liquid = personal_liquid + profile.business_accounts.total_business_liquid
    credit_util = profile.credit_profile.credit_utilization
    net_worth = profile.business_health.total_net_worth

    # Calculate estimated burn and runway
    daily_burn = 50  # Conservative estimate
    personal_runway = personal_liquid / daily_burn if daily_burn > 0 else 999
    total_runway = total_liquid / daily_burn if daily_burn > 0 else 999

    print("CRITICAL METRICS:")
    print()

    # Personal Liquid
    emoji = get_status_emoji(personal_liquid, 4000, 2000, lower_is_better=False)
    print(f"{emoji} Personal Liquid:    ${personal_liquid:,.2f}")
    if personal_liquid < 2000:
        print(f"    ⚠️  BELOW SAFETY THRESHOLD - Need $4,000+ for safety")

    # Total Liquid
    emoji = get_status_emoji(total_liquid, 10000, 5000, lower_is_better=False)
    print(f"{emoji} Total Liquid:       ${total_liquid:,.2f}")

    # Credit Utilization
    emoji = get_status_emoji(credit_util, 0.5, 1.0, lower_is_better=True)
    print(f"{emoji} Credit Utilization: {credit_util*100:.1f}%")
    if credit_util >= 1.0:
        overlimit = profile.credit_profile.total_credit_balance - profile.credit_profile.total_credit_limit
        print(f"    🔴 OVERLIMIT BY ${overlimit:,.2f} - URGENT: Pay down immediately!")
    elif credit_util >= 0.7:
        print(f"    ⚠️  High utilization - Target: <50%")

    # Net Worth
    emoji = get_status_emoji(net_worth, 10000, 5000, lower_is_better=False)
    print(f"{emoji} Net Worth:          ${net_worth:,.2f}")

    print()
    print("RUNWAY:")
    emoji = get_status_emoji(personal_runway, 60, 30, lower_is_better=False)
    print(f"{emoji} Personal Runway:    {personal_runway:.1f} days (at ${daily_burn}/day burn)")
    emoji = get_status_emoji(total_runway, 180, 90, lower_is_better=False)
    print(f"{emoji} Total Runway:       {total_runway:.1f} days")

    print()
    print("ACTION ITEMS:")
    print()

    # Generate action items based on current state
    actions = []

    if credit_util >= 1.0:
        overlimit = profile.credit_profile.total_credit_balance - profile.credit_profile.total_credit_limit
        actions.append(f"🔴 URGENT: Pay ${overlimit:,.2f} to get below credit limit")

    if personal_liquid < 2000:
        actions.append(f"⚠️  Build personal cash to $4,000+ (currently ${personal_liquid:,.2f})")

    if credit_util >= 0.7:
        target = profile.credit_profile.total_credit_limit * 0.5
        paydown = profile.credit_profile.total_credit_balance - target
        actions.append(f"⚠️  Pay down ${paydown:,.2f} to reach 50% utilization")

    if personal_runway < 30:
        actions.append(f"🔴 CRITICAL: Less than 30 days personal runway - increase income NOW")

    # Check for available cashback
    cashback = profile.business_accounts.paypal_cashback_balance
    if cashback > 3000 and credit_util > 0.7:
        actions.append(f"💡 Consider using ${cashback:,.2f} PayPal Cashback to pay down credit")

    if not actions:
        actions.append("✅ No critical actions - maintain current discipline")

    for i, action in enumerate(actions, 1):
        print(f"{i}. {action}")

    print()
    print("=" * 80)
    print()

    # Check if improvement from last time
    emergency_state_file = REPO_ROOT / "business/data/emergency_state.json"
    if emergency_state_file.exists():
        state = json.loads(emergency_state_file.read_text())
        last_metrics = state.get("assessment", {}).get("metrics", {})

        if last_metrics:
            last_util = last_metrics.get("credit_utilization", 0)
            last_liquid = last_metrics.get("total_liquid", 0)

            util_change = credit_util - last_util
            liquid_change = total_liquid - last_liquid

            print("PROGRESS SINCE LAST CHECK:")
            if util_change < 0:
                print(f"  ✅ Credit utilization IMPROVED by {abs(util_change)*100:.1f}%")
            elif util_change > 0:
                print(f"  🔴 Credit utilization WORSENED by {util_change*100:.1f}%")
            else:
                print(f"  ➖ Credit utilization unchanged at {credit_util*100:.1f}%")

            if liquid_change > 0:
                print(f"  ✅ Liquid cash INCREASED by ${liquid_change:,.2f}")
            elif liquid_change < 0:
                print(f"  🔴 Liquid cash DECREASED by ${abs(liquid_change):,.2f}")
            else:
                print(f"  ➖ Liquid cash unchanged at ${total_liquid:,.2f}")
            print()

    print("Run this check daily to track progress!")
    print()
    print("For full emergency plan: cat business/EMERGENCY_ACTION_PLAN.md")
    print("For detailed status: python3 business/emergency_financial_response.py")
    print()


if __name__ == "__main__":
    main()
