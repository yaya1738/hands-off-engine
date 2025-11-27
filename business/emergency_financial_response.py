#!/usr/bin/env python3
"""
EMERGENCY FINANCIAL RESPONSE SYSTEM
Critical cash position and burn rate management for Yair Siegel

CURRENT SITUATION:
- Personal liquid: ~$2,220 (CRITICALLY LOW)
- Business liquid: ~$12,000 (but may be needed for operations)
- Credit balance: $11,270 EXCEEDING limit of $7,600 (148% utilization!)
- Net worth: $4,880 (DANGEROUSLY LOW)
- Burn rate: NON-NEGLIGIBLE

THIS IS A FINANCIAL EMERGENCY
"""
import json
import pathlib
import datetime
import sys
from typing import Dict, Any, List, Optional
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from business.yair_siegel_business_profile import BusinessProfileManager

REPO_ROOT = pathlib.Path(__file__).parent.parent
EMERGENCY_LOG = REPO_ROOT / "business/data/emergency_actions.jsonl"
EMERGENCY_STATE = REPO_ROOT / "business/data/emergency_state.json"
BURN_RATE_LOG = REPO_ROOT / "business/data/burn_rate_tracking.jsonl"


class FinancialEmergencyManager:
    """Manages critical financial emergencies"""

    # Emergency thresholds
    CRITICAL_PERSONAL_LIQUID = 1000  # Below this = CRITICAL
    CRITICAL_TOTAL_LIQUID = 2000
    CRITICAL_CREDIT_UTIL = 1.0  # 100% = CRITICAL (we're at 148%!)
    DANGER_CREDIT_UTIL = 0.70  # 70% = DANGER
    MINIMUM_RUNWAY_DAYS = 30

    def __init__(self):
        self.profile_manager = BusinessProfileManager()
        self.emergency_log_path = EMERGENCY_LOG
        self.emergency_state_path = EMERGENCY_STATE
        self.burn_rate_log_path = BURN_RATE_LOG
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure required directories exist"""
        self.emergency_log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_emergency(self, severity: str, category: str, description: str, actions: List[Dict[str, Any]]):
        """Log emergency event"""
        event = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "severity": severity,  # CRITICAL, URGENT, WARNING
            "category": category,
            "description": description,
            "actions": actions,
        }
        with open(self.emergency_log_path, "a") as f:
            f.write(json.dumps(event) + "\n")
        return event

    def calculate_burn_rate(self) -> Dict[str, Any]:
        """Calculate current burn rate from history"""
        # Read last 30 days of history if available
        history_file = REPO_ROOT / "business/data/business_history.jsonl"

        if not history_file.exists():
            return {
                "daily_burn": 0,
                "monthly_burn": 0,
                "estimated": True,
                "data_points": 0,
            }

        # Read history
        history = []
        with open(history_file, "r") as f:
            for line in f:
                history.append(json.loads(line))

        if len(history) < 2:
            # Not enough data - estimate based on known costs
            estimated_daily = 50  # Conservative estimate: AI costs, misc
            return {
                "daily_burn": estimated_daily,
                "monthly_burn": estimated_daily * 30,
                "estimated": True,
                "data_points": 0,
            }

        # Calculate from actual data
        first = history[0]
        last = history[-1]

        first_nw = first["business_health"]["total_net_worth"]
        last_nw = last["business_health"]["total_net_worth"]

        first_time = datetime.datetime.fromisoformat(first["timestamp"].replace("Z", "+00:00"))
        last_time = datetime.datetime.fromisoformat(last["timestamp"].replace("Z", "+00:00"))

        days_elapsed = (last_time - first_time).total_seconds() / 86400

        if days_elapsed > 0:
            total_change = last_nw - first_nw
            daily_burn = -total_change / days_elapsed if total_change < 0 else 0

            return {
                "daily_burn": round(daily_burn, 2),
                "monthly_burn": round(daily_burn * 30, 2),
                "estimated": False,
                "data_points": len(history),
                "net_worth_change": round(total_change, 2),
                "days_tracked": round(days_elapsed, 2),
            }

        return {
            "daily_burn": 0,
            "monthly_burn": 0,
            "estimated": True,
            "data_points": len(history),
        }

    def calculate_runway(self, liquid_cash: float, daily_burn: float) -> float:
        """Calculate runway in days"""
        if daily_burn <= 0:
            return 999  # Infinite runway if no burn
        return liquid_cash / daily_burn

    def assess_emergency_level(self, profile) -> Dict[str, Any]:
        """Assess current emergency level"""
        personal_liquid = profile.personal_accounts.total_personal_liquid
        total_liquid = personal_liquid + profile.business_accounts.total_business_liquid
        credit_util = profile.credit_profile.credit_utilization
        net_worth = profile.business_health.total_net_worth

        burn_rate = self.calculate_burn_rate()
        daily_burn = burn_rate["daily_burn"]

        # Calculate runway
        personal_runway = self.calculate_runway(personal_liquid, daily_burn)
        total_runway = self.calculate_runway(total_liquid, daily_burn)

        emergencies = []
        severity = "NORMAL"

        # Check personal liquidity
        if personal_liquid < self.CRITICAL_PERSONAL_LIQUID:
            emergencies.append({
                "type": "critical_personal_liquidity",
                "severity": "CRITICAL",
                "message": f"Personal liquid ${personal_liquid:.2f} below critical threshold ${self.CRITICAL_PERSONAL_LIQUID}",
                "runway_days": round(personal_runway, 1),
            })
            severity = "CRITICAL"

        # Check total liquidity
        if total_liquid < self.CRITICAL_TOTAL_LIQUID:
            emergencies.append({
                "type": "critical_total_liquidity",
                "severity": "CRITICAL",
                "message": f"Total liquid ${total_liquid:.2f} below critical threshold ${self.CRITICAL_TOTAL_LIQUID}",
                "runway_days": round(total_runway, 1),
            })
            severity = "CRITICAL"

        # Check credit utilization
        if credit_util >= self.CRITICAL_CREDIT_UTIL:
            emergencies.append({
                "type": "credit_overlimit",
                "severity": "CRITICAL",
                "message": f"Credit utilization {credit_util*100:.1f}% - OVER LIMIT! Credit score damage imminent",
                "amount_overlimit": round(profile.credit_profile.total_credit_balance - profile.credit_profile.total_credit_limit, 2),
            })
            severity = "CRITICAL"
        elif credit_util >= self.DANGER_CREDIT_UTIL:
            emergencies.append({
                "type": "credit_danger",
                "severity": "URGENT",
                "message": f"Credit utilization {credit_util*100:.1f}% in danger zone (>70%)",
            })
            if severity == "NORMAL":
                severity = "URGENT"

        # Check runway
        if total_runway < self.MINIMUM_RUNWAY_DAYS:
            emergencies.append({
                "type": "insufficient_runway",
                "severity": "CRITICAL",
                "message": f"Runway only {total_runway:.1f} days at current burn rate ${daily_burn:.2f}/day",
                "burn_rate": burn_rate,
            })
            severity = "CRITICAL"

        return {
            "severity": severity,
            "emergencies": emergencies,
            "metrics": {
                "personal_liquid": personal_liquid,
                "total_liquid": total_liquid,
                "credit_utilization": credit_util,
                "net_worth": net_worth,
                "daily_burn": daily_burn,
                "monthly_burn": burn_rate["monthly_burn"],
                "personal_runway_days": round(personal_runway, 1),
                "total_runway_days": round(total_runway, 1),
            },
        }

    def generate_emergency_actions(self, profile, assessment) -> List[Dict[str, Any]]:
        """Generate immediate emergency actions"""
        actions = []

        # IMMEDIATE ACTION 1: Use PayPal cashback to pay down overlimit credit
        cashback = profile.business_accounts.paypal_cashback_balance
        overlimit = profile.credit_profile.total_credit_balance - profile.credit_profile.total_credit_limit

        if overlimit > 0 and cashback > 0:
            payment_amount = min(cashback, overlimit)
            actions.append({
                "priority": 1,
                "action": "IMMEDIATE_CREDIT_PAYDOWN",
                "description": f"Transfer ${payment_amount:.2f} from PayPal Cashback to pay down overlimit credit",
                "impact": f"Reduce credit balance by ${payment_amount:.2f}, bring utilization under 100%",
                "required_amount": payment_amount,
                "steps": [
                    "1. Transfer funds from PayPal Cashback to PayPal main account",
                    "2. Use PayPal to pay Capital One and/or PayPal Credit",
                    "3. Prioritize whichever card is most overlimit",
                ],
                "urgency": "DO THIS NOW - WITHIN 24 HOURS",
            })

        # IMMEDIATE ACTION 2: Stop all non-essential spending
        actions.append({
            "priority": 2,
            "action": "EMERGENCY_SPENDING_FREEZE",
            "description": "Implement immediate spending freeze on all non-essential items",
            "impact": "Reduce burn rate, preserve remaining cash",
            "steps": [
                "1. Review all recurring subscriptions - cancel non-essential",
                "2. Defer all discretionary purchases",
                "3. Minimize trading activity to only high-confidence opportunities",
                "4. Reduce AI API costs - use cheaper models, reduce frequency",
            ],
            "urgency": "IMPLEMENT IMMEDIATELY",
        })

        # IMMEDIATE ACTION 3: Income acceleration
        actions.append({
            "priority": 3,
            "action": "INCOME_ACCELERATION",
            "description": "Focus 100% available time on income generation",
            "impact": "Increase cash inflow, reduce burn rate impact",
            "steps": [
                "1. Identify highest $ per hour income opportunities",
                "2. Defer all non-income activities",
                "3. Leverage existing skills/platforms for quick cash",
                "4. Consider gig work for immediate liquidity",
            ],
            "urgency": "START WITHIN 24 HOURS",
        })

        # ACTION 4: Credit limit increase requests (if score allows)
        if profile.credit_profile.credit_score >= 680:
            actions.append({
                "priority": 4,
                "action": "REQUEST_CREDIT_INCREASES",
                "description": "Request credit limit increases to reduce utilization ratio",
                "impact": "Immediate utilization reduction without paying down balance",
                "steps": [
                    "1. Call Capital One - request limit increase",
                    "2. Call PayPal Credit - request limit increase",
                    "3. Emphasize payment history if good",
                ],
                "urgency": "DO WITHIN 48 HOURS",
                "note": "Soft pull may be approved instantly, hard pull worth it given emergency",
            })

        # ACTION 5: Business to personal cash transfer for immediate needs
        personal_liquid = profile.personal_accounts.total_personal_liquid
        if personal_liquid < 500:
            transfer_amount = min(1000, profile.business_accounts.paypal_business)
            actions.append({
                "priority": 5,
                "action": "EMERGENCY_CASH_TRANSFER",
                "description": f"Transfer ${transfer_amount:.2f} from PayPal Business to personal for immediate needs",
                "impact": f"Ensure personal survival needs covered for ~{transfer_amount/50:.0f} days",
                "required_amount": transfer_amount,
                "steps": [
                    "1. Transfer from PayPal Business to PayPal Personal",
                    "2. Then to Monzo for daily expenses",
                    "3. Strictly for essentials only: food, rent, utilities",
                ],
                "urgency": "DO WITHIN 24 HOURS IF PERSONAL CASH < $500",
            })

        # ACTION 6: Reduce system costs
        actions.append({
            "priority": 6,
            "action": "REDUCE_SYSTEM_COSTS",
            "description": "Immediately reduce AI and automation costs",
            "impact": "Lower monthly burn rate by $50-200",
            "steps": [
                "1. Switch to cheaper AI models (GPT-3.5 instead of GPT-4)",
                "2. Reduce automation frequency (hourly → every 4 hours)",
                "3. Pause non-critical monitoring and analysis",
                "4. Use cached results where possible",
            ],
            "urgency": "IMPLEMENT WITHIN 48 HOURS",
        })

        # ACTION 7: Rent payment strategy
        rent_monthly_usd = profile.business_accounts.__dict__.get("rent_monthly_usd", 0)
        if "rent_monthly_usd" in str(profile):
            actions.append({
                "priority": 7,
                "action": "RENT_PAYMENT_OPTIMIZATION",
                "description": "Ensure rent payment strategy leverages existing prepayment",
                "impact": "Preserve cash flow, avoid using liquid cash for rent if already paid",
                "steps": [
                    "1. Verify rent is paid 2 months ahead",
                    "2. Do NOT make additional rent payments",
                    "3. Use this buffer to focus on income generation",
                ],
                "urgency": "VERIFY NOW",
            })

        return actions

    def execute_emergency_response(self) -> Dict[str, Any]:
        """Execute complete emergency response"""
        print("=" * 80)
        print("🚨 FINANCIAL EMERGENCY RESPONSE SYSTEM 🚨")
        print("=" * 80)
        print()

        # Load profile
        profile = self.profile_manager.generate_current_profile()

        # Assess emergency
        assessment = self.assess_emergency_level(profile)

        print(f"EMERGENCY LEVEL: {assessment['severity']}")
        print()

        print("CURRENT SITUATION:")
        metrics = assessment['metrics']
        print(f"  Personal Liquid:    ${metrics['personal_liquid']:,.2f} {'🔴 CRITICAL' if metrics['personal_liquid'] < self.CRITICAL_PERSONAL_LIQUID else '⚠️'}")
        print(f"  Total Liquid:       ${metrics['total_liquid']:,.2f} {'🔴 CRITICAL' if metrics['total_liquid'] < self.CRITICAL_TOTAL_LIQUID else '⚠️'}")
        print(f"  Credit Util:        {metrics['credit_utilization']*100:.1f}% {'🔴 OVERLIMIT!' if metrics['credit_utilization'] >= 1.0 else '⚠️'}")
        print(f"  Net Worth:          ${metrics['net_worth']:,.2f}")
        print(f"  Daily Burn:         ${metrics['daily_burn']:.2f}")
        print(f"  Monthly Burn:       ${metrics['monthly_burn']:.2f}")
        print(f"  Personal Runway:    {metrics['personal_runway_days']:.1f} days {'🔴 CRITICAL' if metrics['personal_runway_days'] < 30 else '⚠️'}")
        print(f"  Total Runway:       {metrics['total_runway_days']:.1f} days")
        print()

        if assessment['emergencies']:
            print(f"EMERGENCIES DETECTED ({len(assessment['emergencies'])}):")
            for i, emergency in enumerate(assessment['emergencies'], 1):
                print(f"{i}. [{emergency['severity']}] {emergency['message']}")
            print()

        # Generate actions
        actions = self.generate_emergency_actions(profile, assessment)

        print(f"IMMEDIATE ACTIONS REQUIRED ({len(actions)}):")
        print()
        for action in actions:
            print(f"{'=' * 80}")
            print(f"PRIORITY {action['priority']}: {action['action']}")
            print(f"{'=' * 80}")
            print(f"Description: {action['description']}")
            print(f"Impact: {action['impact']}")
            print(f"Urgency: {action['urgency']}")
            if 'required_amount' in action:
                print(f"Amount: ${action['required_amount']:.2f}")
            print()
            print("Steps:")
            for step in action['steps']:
                print(f"  {step}")
            if 'note' in action:
                print(f"\nNote: {action['note']}")
            print()

        # Log emergency
        self.log_emergency(
            severity=assessment['severity'],
            category="cash_crisis",
            description=f"Critical cash position detected: ${metrics['total_liquid']:.2f} liquid, {metrics['total_runway_days']:.1f} days runway",
            actions=actions,
        )

        # Save emergency state
        emergency_state = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "severity": assessment['severity'],
            "assessment": assessment,
            "actions": actions,
            "status": "ACTIVE",
        }
        self.emergency_state_path.write_text(json.dumps(emergency_state, indent=2))

        print("=" * 80)
        print("🚨 EMERGENCY RESPONSE PLAN GENERATED 🚨")
        print("=" * 80)
        print()
        print(f"Emergency state saved to: {self.emergency_state_path}")
        print(f"Emergency log saved to: {self.emergency_log_path}")
        print()
        print("⚠️  THIS REQUIRES IMMEDIATE HUMAN ACTION ⚠️")
        print("The system has identified critical issues that need YOUR action within 24-48 hours.")
        print()

        return {
            "severity": assessment['severity'],
            "emergencies_count": len(assessment['emergencies']),
            "actions_count": len(actions),
            "metrics": metrics,
            "actions": actions,
        }


def main():
    """Main entry point"""
    manager = FinancialEmergencyManager()
    result = manager.execute_emergency_response()


if __name__ == "__main__":
    main()
