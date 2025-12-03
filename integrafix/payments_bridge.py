#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Siegel Payments & Subscriptions Bridge
========================================================

Complete management of payment methods and subscriptions:

PAYMENT METHODS:
- Credit Cards (cycling strategy)
- PayPal Business
- Crypto Wallets (Polygon USDC)
- Bank Accounts

SUBSCRIPTIONS:
- AI Services (Claude, ChatGPT, Copilot)
- API Services (Anthropic, OpenAI)
- Tools & Infrastructure
- ROI tracking per subscription

OPTIMIZATIONS:
- Credit cycling opportunities
- Subscription ROI analysis
- Cost reduction recommendations
- Billing cycle management

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import calendar

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
FINANCE_DIR = PROJECT_ROOT / "finance"


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class PaymentMethodType(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    CRYPTO_WALLET = "crypto_wallet"
    BANK_ACCOUNT = "bank_account"
    CASH = "cash"


class SubscriptionCategory(Enum):
    AI_SERVICES = "ai_services"
    API_USAGE = "api_usage"
    INFRASTRUCTURE = "infrastructure"
    TOOLS = "tools"
    ENTERTAINMENT = "entertainment"
    ESSENTIAL = "essential"


class BillingCycle(Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"
    USAGE_BASED = "usage_based"
    ONE_TIME = "one_time"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PaymentMethod:
    """A payment method available to Yair."""
    id: str
    name: str
    type: PaymentMethodType

    # Balances
    balance: float = 0.0
    available: float = 0.0
    limit: float = 0.0

    # Status
    active: bool = True
    primary: bool = False

    # Details
    last_4: str = ""
    network: str = ""  # Visa, Mastercard, Polygon, etc.
    address: str = ""  # For crypto

    # Credit-specific
    utilization: float = 0.0
    apr: float = 0.0
    min_payment: float = 0.0
    due_date: int = 0  # Day of month

    # Metadata
    notes: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "balance": self.balance,
            "available": self.available,
            "limit": self.limit,
            "active": self.active,
            "primary": self.primary,
            "last_4": self.last_4,
            "network": self.network,
            "utilization": self.utilization,
            "apr": self.apr,
            "notes": self.notes,
        }


@dataclass
class Subscription:
    """A subscription service."""
    id: str
    name: str
    provider: str
    category: SubscriptionCategory

    # Cost
    amount: float = 0.0
    currency: str = "USD"
    billing_cycle: BillingCycle = BillingCycle.MONTHLY

    # Dates
    billing_day: int = 1  # Day of month
    next_billing: str = ""
    started_at: str = ""

    # Payment
    payment_method_id: str = ""

    # ROI tracking
    generates_revenue: bool = False
    estimated_monthly_value: float = 0.0
    actual_monthly_value: float = 0.0
    roi: float = 0.0  # value / cost

    # Status
    active: bool = True
    essential: bool = False
    can_cancel: bool = True

    # Notes
    notes: str = ""

    def calculate_roi(self):
        """Calculate ROI for this subscription."""
        if self.amount > 0:
            value = self.actual_monthly_value or self.estimated_monthly_value
            self.roi = value / self.amount
        else:
            self.roi = float('inf') if self.estimated_monthly_value > 0 else 0

    def monthly_cost(self) -> float:
        """Get normalized monthly cost."""
        if self.billing_cycle == BillingCycle.ANNUAL:
            return self.amount / 12
        elif self.billing_cycle == BillingCycle.MONTHLY:
            return self.amount
        else:
            return self.amount  # Approximate for usage-based

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "category": self.category.value,
            "amount": self.amount,
            "billing_cycle": self.billing_cycle.value,
            "billing_day": self.billing_day,
            "next_billing": self.next_billing,
            "payment_method_id": self.payment_method_id,
            "monthly_cost": self.monthly_cost(),
            "estimated_value": self.estimated_monthly_value,
            "actual_value": self.actual_monthly_value,
            "roi": self.roi,
            "active": self.active,
            "essential": self.essential,
            "notes": self.notes,
        }


@dataclass
class CreditCycleOpportunity:
    """A credit cycling opportunity."""
    from_card: str
    to_card: str
    amount: float
    fee_pct: float
    fee_amount: float
    savings_vs_apr: float
    recommended: bool
    notes: str


# =============================================================================
# PAYMENTS BRIDGE
# =============================================================================

class PaymentsBridge:
    """
    Bridge for managing payments and subscriptions.
    """

    def __init__(self):
        self.state_path = STATE_DIR / "payments_bridge.json"
        self.payment_methods: Dict[str, PaymentMethod] = {}
        self.subscriptions: Dict[str, Subscription] = {}

        self.state = self._load_state()
        self._load_from_system()

    def _load_state(self) -> Dict:
        if self.state_path.exists():
            with open(self.state_path) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_monthly_subscriptions": 0,
            "total_subscription_value": 0,
            "credit_cycles_executed": 0,
            "savings_from_optimization": 0,
        }

    def _save_state(self):
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.state["payment_methods"] = [pm.to_dict() for pm in self.payment_methods.values()]
        self.state["subscriptions"] = [sub.to_dict() for sub in self.subscriptions.values()]

        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _load_from_system(self):
        """Load payment data from existing system files."""

        # Load from finance hub
        hub_path = FINANCE_DIR / "yair_finance_hub.json"
        if hub_path.exists():
            with open(hub_path) as f:
                hub = json.load(f)

            # Payment methods from accounts
            accounts = hub.get("accounts", {})

            # Polymarket wallet
            if "polymarket" in accounts:
                pm = accounts["polymarket"]
                self.payment_methods["polymarket_wallet"] = PaymentMethod(
                    id="polymarket_wallet",
                    name="Polymarket Wallet",
                    type=PaymentMethodType.CRYPTO_WALLET,
                    balance=pm.get("balance_usdc", 0),
                    available=pm.get("balance_usdc", 0),
                    network="Polygon",
                    address=pm.get("wallet_address", ""),
                    active=True,
                    notes="Primary trading wallet"
                )

            # PayPal Business
            if "paypal_business" in accounts:
                pp = accounts["paypal_business"]
                self.payment_methods["paypal_business"] = PaymentMethod(
                    id="paypal_business",
                    name="PayPal Business",
                    type=PaymentMethodType.PAYPAL,
                    balance=pp.get("balance_usd", 0),
                    available=pp.get("balance_usd", 0),
                    active=True,
                    notes=pp.get("notes", "Credit cycling hub")
                )

            # Credit Cards (aggregate)
            if "credit_cards" in accounts:
                cc = accounts["credit_cards"]
                credit = hub.get("credit", {})
                self.payment_methods["credit_cards"] = PaymentMethod(
                    id="credit_cards",
                    name="Credit Cards (Combined)",
                    type=PaymentMethodType.CREDIT_CARD,
                    balance=cc.get("total_debt", 0),
                    available=cc.get("total_available", 0),
                    limit=cc.get("total_limit", 0),
                    utilization=credit.get("utilization_pct", 0) / 100,
                    active=True,
                    notes=credit.get("strategy", "")
                )

            # Robinhood
            if "robinhood" in accounts:
                rh = accounts["robinhood"]
                self.payment_methods["robinhood"] = PaymentMethod(
                    id="robinhood",
                    name="Robinhood",
                    type=PaymentMethodType.BANK_ACCOUNT,
                    balance=rh.get("balance_usd", 0),
                    available=rh.get("balance_usd", 0),
                    active=True,
                    notes="Brokerage - positions"
                )

            # Subscriptions from monthly burn
            burn = hub.get("monthly_burn", {})
            ai_services = burn.get("ai_services", {})
            breakdown = ai_services.get("breakdown", {})

            # Claude Max
            if "claude_max" in breakdown:
                self.subscriptions["claude_max"] = Subscription(
                    id="claude_max",
                    name="Claude Max",
                    provider="Anthropic",
                    category=SubscriptionCategory.AI_SERVICES,
                    amount=20,
                    billing_cycle=BillingCycle.MONTHLY,
                    generates_revenue=True,
                    estimated_monthly_value=100,  # Code assistance value
                    essential=True,
                    notes="Primary AI assistant"
                )

            # ChatGPT Plus
            if "chatgpt_plus" in breakdown:
                self.subscriptions["chatgpt_plus"] = Subscription(
                    id="chatgpt_plus",
                    name="ChatGPT Plus",
                    provider="OpenAI",
                    category=SubscriptionCategory.AI_SERVICES,
                    amount=20,
                    billing_cycle=BillingCycle.MONTHLY,
                    generates_revenue=True,
                    estimated_monthly_value=50,
                    essential=False,
                    can_cancel=True,
                    notes="Secondary AI - consider canceling"
                )

            # Copilot Pro
            if "copilot_pro" in breakdown:
                self.subscriptions["copilot_pro"] = Subscription(
                    id="copilot_pro",
                    name="GitHub Copilot Pro",
                    provider="GitHub/Microsoft",
                    category=SubscriptionCategory.AI_SERVICES,
                    amount=10,
                    billing_cycle=BillingCycle.MONTHLY,
                    generates_revenue=True,
                    estimated_monthly_value=30,
                    essential=False,
                    notes="IDE assistance"
                )

            # Anthropic API
            if "anthropic_api" in breakdown:
                self.subscriptions["anthropic_api"] = Subscription(
                    id="anthropic_api",
                    name="Anthropic API",
                    provider="Anthropic",
                    category=SubscriptionCategory.API_USAGE,
                    amount=50,  # Variable
                    billing_cycle=BillingCycle.USAGE_BASED,
                    generates_revenue=True,
                    estimated_monthly_value=200,
                    essential=True,
                    notes="Powers autonomous system"
                )

            # IFTTT
            if "ifttt" in breakdown:
                self.subscriptions["ifttt"] = Subscription(
                    id="ifttt",
                    name="IFTTT Pro",
                    provider="IFTTT",
                    category=SubscriptionCategory.TOOLS,
                    amount=5,
                    billing_cycle=BillingCycle.MONTHLY,
                    generates_revenue=False,
                    estimated_monthly_value=10,
                    essential=False,
                    can_cancel=True,
                    notes="Automation - may be replaceable"
                )

        # Load from expenses
        expenses_path = STATE_DIR / "yair_expenses.json"
        if expenses_path.exists():
            with open(expenses_path) as f:
                expenses = json.load(f)

            for exp in expenses.get("expenses", []):
                if exp["name"] == "Server Costs":
                    self.subscriptions["server_costs"] = Subscription(
                        id="server_costs",
                        name="Server/Infrastructure",
                        provider="Various",
                        category=SubscriptionCategory.INFRASTRUCTURE,
                        amount=exp["monthly_amount"],
                        billing_cycle=BillingCycle.MONTHLY,
                        generates_revenue=True,
                        estimated_monthly_value=exp["monthly_amount"] * 5,
                        essential=True,
                        notes="Powers the system"
                    )
                elif exp["name"] == "API Subscriptions":
                    self.subscriptions["api_general"] = Subscription(
                        id="api_general",
                        name="API Services (Other)",
                        provider="Various",
                        category=SubscriptionCategory.API_USAGE,
                        amount=exp["monthly_amount"],
                        billing_cycle=BillingCycle.MONTHLY,
                        generates_revenue=True,
                        estimated_monthly_value=exp["monthly_amount"] * 2,
                        essential=False,
                    )

        # Calculate ROI for all subscriptions
        for sub in self.subscriptions.values():
            sub.calculate_roi()

        self._save_state()

    # =========================================================================
    # PAYMENT METHODS
    # =========================================================================

    def add_payment_method(
        self,
        name: str,
        method_type: PaymentMethodType,
        balance: float = 0,
        available: float = 0,
        limit: float = 0,
        **kwargs
    ) -> PaymentMethod:
        """Add a new payment method."""
        pm_id = name.lower().replace(" ", "_")

        pm = PaymentMethod(
            id=pm_id,
            name=name,
            type=method_type,
            balance=balance,
            available=available,
            limit=limit,
            **kwargs
        )

        self.payment_methods[pm_id] = pm
        self._save_state()
        return pm

    def get_total_available(self) -> Dict:
        """Get total available across all payment methods."""
        totals = {
            "cash": 0,
            "credit": 0,
            "crypto": 0,
            "total": 0,
        }

        for pm in self.payment_methods.values():
            if not pm.active:
                continue

            if pm.type == PaymentMethodType.CREDIT_CARD:
                totals["credit"] += pm.available
            elif pm.type == PaymentMethodType.CRYPTO_WALLET:
                totals["crypto"] += pm.available
            else:
                totals["cash"] += pm.available

            totals["total"] += pm.available

        return totals

    def get_credit_utilization(self) -> Dict:
        """Get credit card utilization details."""
        total_limit = 0
        total_balance = 0

        for pm in self.payment_methods.values():
            if pm.type == PaymentMethodType.CREDIT_CARD:
                total_limit += pm.limit
                total_balance += pm.balance

        utilization = total_balance / total_limit if total_limit > 0 else 0

        return {
            "total_limit": total_limit,
            "total_balance": total_balance,
            "total_available": total_limit - total_balance,
            "utilization": utilization,
            "utilization_pct": utilization * 100,
            "health": "good" if utilization < 0.3 else "warning" if utilization < 0.5 else "high" if utilization < 0.8 else "critical",
        }

    # =========================================================================
    # SUBSCRIPTIONS
    # =========================================================================

    def add_subscription(
        self,
        name: str,
        provider: str,
        category: SubscriptionCategory,
        amount: float,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        **kwargs
    ) -> Subscription:
        """Add a new subscription."""
        sub_id = name.lower().replace(" ", "_")

        sub = Subscription(
            id=sub_id,
            name=name,
            provider=provider,
            category=category,
            amount=amount,
            billing_cycle=billing_cycle,
            **kwargs
        )
        sub.calculate_roi()

        self.subscriptions[sub_id] = sub
        self._save_state()
        return sub

    def update_subscription_value(self, sub_id: str, actual_value: float):
        """Update actual value generated by subscription."""
        if sub_id in self.subscriptions:
            self.subscriptions[sub_id].actual_monthly_value = actual_value
            self.subscriptions[sub_id].calculate_roi()
            self._save_state()

    def get_subscription_summary(self) -> Dict:
        """Get summary of all subscriptions."""
        total_cost = 0
        total_value = 0
        by_category = {}

        for sub in self.subscriptions.values():
            if not sub.active:
                continue

            monthly = sub.monthly_cost()
            total_cost += monthly
            total_value += sub.estimated_monthly_value

            cat = sub.category.value
            if cat not in by_category:
                by_category[cat] = {"cost": 0, "value": 0, "count": 0}
            by_category[cat]["cost"] += monthly
            by_category[cat]["value"] += sub.estimated_monthly_value
            by_category[cat]["count"] += 1

        return {
            "total_monthly_cost": total_cost,
            "total_monthly_value": total_value,
            "overall_roi": total_value / total_cost if total_cost > 0 else 0,
            "subscription_count": len([s for s in self.subscriptions.values() if s.active]),
            "by_category": by_category,
        }

    def get_upcoming_bills(self, days: int = 30) -> List[Dict]:
        """Get upcoming subscription bills."""
        upcoming = []
        today = datetime.now(timezone.utc)

        for sub in self.subscriptions.values():
            if not sub.active:
                continue

            if sub.billing_cycle == BillingCycle.MONTHLY:
                # Calculate next billing date
                billing_day = sub.billing_day or 1

                if today.day <= billing_day:
                    next_bill = today.replace(day=billing_day)
                else:
                    # Next month
                    if today.month == 12:
                        next_bill = today.replace(year=today.year + 1, month=1, day=billing_day)
                    else:
                        next_bill = today.replace(month=today.month + 1, day=billing_day)

                days_until = (next_bill - today).days

                if days_until <= days:
                    upcoming.append({
                        "subscription": sub.name,
                        "amount": sub.amount,
                        "date": next_bill.isoformat(),
                        "days_until": days_until,
                    })

        return sorted(upcoming, key=lambda x: x["days_until"])

    # =========================================================================
    # OPTIMIZATIONS
    # =========================================================================

    def get_cancel_recommendations(self) -> List[Dict]:
        """Get recommendations for subscriptions to cancel."""
        recommendations = []

        for sub in self.subscriptions.values():
            if not sub.active or not sub.can_cancel:
                continue

            # Low ROI subscriptions
            if sub.roi < 1.0 and not sub.essential:
                recommendations.append({
                    "subscription": sub.name,
                    "monthly_cost": sub.monthly_cost(),
                    "estimated_value": sub.estimated_monthly_value,
                    "roi": sub.roi,
                    "reason": f"Low ROI ({sub.roi:.1f}x) - costs more than it generates",
                    "savings_annual": sub.monthly_cost() * 12,
                    "priority": "high" if sub.roi < 0.5 else "medium",
                })

            # Duplicate services
            # (would need more logic to detect duplicates)

        return sorted(recommendations, key=lambda x: x["monthly_cost"], reverse=True)

    def get_credit_cycle_opportunities(self) -> List[Dict]:
        """Find credit cycling opportunities."""
        opportunities = []

        # Get credit card info
        cc = self.payment_methods.get("credit_cards")
        paypal = self.payment_methods.get("paypal_business")

        if cc and paypal and cc.balance > 0:
            # PayPal Business cycling opportunity
            # Typical fee: 2.9% + $0.30 per transaction
            amount = min(cc.balance, paypal.available, 5000)  # Max $5k at a time
            fee_pct = 0.029
            fee_fixed = 0.30
            fee_total = amount * fee_pct + fee_fixed

            # Compare to credit card APR
            apr = cc.apr or 0.24  # Default 24% APR
            monthly_interest = cc.balance * (apr / 12)

            if fee_total < monthly_interest:
                opportunities.append({
                    "type": "paypal_cycle",
                    "from": "Credit Cards",
                    "to": "PayPal Business",
                    "amount": amount,
                    "fee": fee_total,
                    "fee_pct": fee_pct * 100,
                    "vs_interest": monthly_interest,
                    "savings": monthly_interest - fee_total,
                    "recommended": True,
                    "notes": "Pay CC with PayPal, pay PayPal with CC (cycle)",
                })

        return opportunities

    def get_optimization_report(self) -> Dict:
        """Get full optimization report."""
        summary = self.get_subscription_summary()
        cancel_recs = self.get_cancel_recommendations()
        cycle_opps = self.get_credit_cycle_opportunities()
        credit = self.get_credit_utilization()

        potential_savings = sum(r["monthly_cost"] for r in cancel_recs)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_state": {
                "monthly_subscription_cost": summary["total_monthly_cost"],
                "monthly_subscription_value": summary["total_monthly_value"],
                "overall_roi": summary["overall_roi"],
                "credit_utilization": credit["utilization_pct"],
            },
            "optimizations": {
                "cancel_recommendations": cancel_recs,
                "potential_monthly_savings": potential_savings,
                "potential_annual_savings": potential_savings * 12,
                "credit_cycle_opportunities": cycle_opps,
            },
            "actions": self._generate_actions(cancel_recs, cycle_opps, credit),
        }

    def _generate_actions(self, cancel_recs, cycle_opps, credit) -> List[str]:
        """Generate prioritized action list."""
        actions = []

        # Credit utilization warning
        if credit["utilization_pct"] > 70:
            actions.append(f"HIGH: Credit utilization at {credit['utilization_pct']:.0f}% - pay down to under 30%")

        # Cycle opportunities
        for opp in cycle_opps:
            if opp["recommended"]:
                actions.append(f"MEDIUM: Credit cycle opportunity - save ${opp['savings']:.2f}/mo via {opp['type']}")

        # Cancel recommendations
        for rec in cancel_recs[:3]:
            actions.append(f"CONSIDER: Cancel {rec['subscription']} - save ${rec['monthly_cost']:.0f}/mo (ROI: {rec['roi']:.1f}x)")

        return actions

    # =========================================================================
    # STATUS & REPORTS
    # =========================================================================

    def get_status(self) -> Dict:
        """Get bridge status."""
        summary = self.get_subscription_summary()
        credit = self.get_credit_utilization()
        available = self.get_total_available()

        return {
            "bridge": "payments",
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payment_methods": len(self.payment_methods),
            "subscriptions": len(self.subscriptions),
            "monthly_cost": summary["total_monthly_cost"],
            "monthly_value": summary["total_monthly_value"],
            "roi": summary["overall_roi"],
            "credit_utilization": credit["utilization_pct"],
            "total_available": available["total"],
        }

    def print_report(self):
        """Print comprehensive report."""
        summary = self.get_subscription_summary()
        credit = self.get_credit_utilization()
        available = self.get_total_available()
        optimization = self.get_optimization_report()
        upcoming = self.get_upcoming_bills(14)

        print("=" * 70)
        print("INTEGRAFIX: Yair Siegel Payments & Subscriptions")
        print(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)

        # Payment Methods
        print("\n>>> PAYMENT METHODS")
        for pm in self.payment_methods.values():
            status = "ACTIVE" if pm.active else "INACTIVE"
            print(f"    [{pm.type.value}] {pm.name}")
            print(f"      Balance: ${pm.balance:,.2f} | Available: ${pm.available:,.2f}")
            if pm.type == PaymentMethodType.CREDIT_CARD:
                print(f"      Limit: ${pm.limit:,.0f} | Utilization: {pm.utilization:.0%}")

        print(f"\n    TOTAL AVAILABLE: ${available['total']:,.2f}")
        print(f"      Cash: ${available['cash']:,.2f} | Credit: ${available['credit']:,.2f} | Crypto: ${available['crypto']:,.2f}")

        # Credit Health
        print(f"\n>>> CREDIT HEALTH")
        print(f"    Utilization: {credit['utilization_pct']:.0f}% [{credit['health'].upper()}]")
        print(f"    Balance: ${credit['total_balance']:,.0f} / ${credit['total_limit']:,.0f}")

        # Subscriptions
        print(f"\n>>> SUBSCRIPTIONS ({len(self.subscriptions)} active)")
        print(f"    Monthly Cost:  ${summary['total_monthly_cost']:,.0f}")
        print(f"    Monthly Value: ${summary['total_monthly_value']:,.0f}")
        print(f"    Overall ROI:   {summary['overall_roi']:.1f}x")

        print("\n    BY CATEGORY:")
        for cat, data in summary["by_category"].items():
            roi = data["value"] / data["cost"] if data["cost"] > 0 else 0
            print(f"      {cat}: ${data['cost']:.0f}/mo → ${data['value']:.0f} value ({roi:.1f}x ROI)")

        print("\n    DETAILS:")
        for sub in sorted(self.subscriptions.values(), key=lambda s: s.monthly_cost(), reverse=True):
            if sub.active:
                roi_str = f"{sub.roi:.1f}x" if sub.roi < 100 else "∞"
                essential = "★" if sub.essential else " "
                print(f"    {essential} {sub.name}: ${sub.monthly_cost():.0f}/mo → {roi_str} ROI")

        # Upcoming Bills
        if upcoming:
            print(f"\n>>> UPCOMING BILLS (next 14 days)")
            for bill in upcoming:
                print(f"    • {bill['subscription']}: ${bill['amount']:.0f} in {bill['days_until']} days")

        # Optimizations
        print(f"\n>>> OPTIMIZATION OPPORTUNITIES")
        for action in optimization["actions"][:5]:
            print(f"    → {action}")

        if optimization["optimizations"]["potential_monthly_savings"] > 0:
            print(f"\n    POTENTIAL SAVINGS: ${optimization['optimizations']['potential_monthly_savings']:.0f}/mo (${optimization['optimizations']['potential_annual_savings']:.0f}/yr)")

        print("\n" + "=" * 70)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_bridge: Optional[PaymentsBridge] = None


def get_payments_bridge() -> PaymentsBridge:
    """Get or create payments bridge."""
    global _bridge
    if _bridge is None:
        _bridge = PaymentsBridge()
    return _bridge


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="INTEGRAFIX: Payments Bridge")
    parser.add_argument("command", choices=[
        "status", "payments", "subscriptions", "optimize", "upcoming", "report"
    ], default="status", nargs="?")
    args = parser.parse_args()

    bridge = get_payments_bridge()

    if args.command == "status":
        print(json.dumps(bridge.get_status(), indent=2))

    elif args.command == "payments":
        for pm in bridge.payment_methods.values():
            print(json.dumps(pm.to_dict(), indent=2))
            print()

    elif args.command == "subscriptions":
        for sub in bridge.subscriptions.values():
            print(json.dumps(sub.to_dict(), indent=2))
            print()

    elif args.command == "optimize":
        print(json.dumps(bridge.get_optimization_report(), indent=2))

    elif args.command == "upcoming":
        print(json.dumps(bridge.get_upcoming_bills(), indent=2))

    elif args.command == "report":
        bridge.print_report()


if __name__ == "__main__":
    main()
