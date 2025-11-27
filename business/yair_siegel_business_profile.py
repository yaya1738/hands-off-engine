#!/usr/bin/env python3
"""
Yair Siegel Business Profile System
Unified view of personal + business financials + system business operations
"""
import json
import pathlib
import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from decimal import Decimal

HOME = pathlib.Path.home()
REPO_ROOT = pathlib.Path(__file__).parent.parent

# Data sources
EXTERNAL_ACCOUNTS = REPO_ROOT / "termux-hands-off/agents/external_accounts.json"
FINANCE_STATE = REPO_ROOT / "termux-hands-off/data/finances/state.json"
CARDS_DATA = REPO_ROOT / "termux-hands-off/agents/cards.json"

# Business profile storage
BUSINESS_PROFILE_DIR = REPO_ROOT / "business/data"
BUSINESS_STATE_FILE = BUSINESS_PROFILE_DIR / "yair_siegel_business_state.json"
BUSINESS_HISTORY_FILE = BUSINESS_PROFILE_DIR / "business_history.jsonl"
BUSINESS_METRICS_FILE = BUSINESS_PROFILE_DIR / "business_metrics.jsonl"


@dataclass
class BusinessAccounts:
    """Business-related financial accounts"""
    paypal_business: float = 0.0
    paypal_cashback_balance: float = 0.0
    total_business_liquid: float = 0.0


@dataclass
class PersonalAccounts:
    """Personal financial accounts"""
    paypal_personal: float = 0.0
    monzo: float = 0.0
    robinhood_cash: float = 0.0
    robinhood_total: float = 0.0
    polymarket_cash: float = 0.0
    polymarket_total: float = 0.0
    schwab: float = 0.0
    total_personal_liquid: float = 0.0


@dataclass
class CreditProfile:
    """Credit utilization and limits"""
    capital_one_balance: float = 0.0
    paypal_credit_balance: float = 0.0
    total_credit_balance: float = 0.0
    total_credit_limit: float = 0.0
    credit_utilization: float = 0.0
    credit_score: int = 0
    auth_user_limits: float = 0.0


@dataclass
class BusinessOperations:
    """System business operations and performance"""
    trading_system_active: bool = True
    ai_nexus_active: bool = True
    automation_uptime_pct: float = 99.0
    daily_ai_cost: float = 0.0
    monthly_ai_cost: float = 0.0
    trading_volume_monthly: float = 0.0
    net_trading_pnl: float = 0.0
    system_roi_pct: float = 0.0


@dataclass
class BusinessHealth:
    """Overall business health metrics"""
    total_net_worth: float = 0.0
    monthly_cash_flow: float = 0.0
    monthly_burn_rate: float = 0.0
    runway_months: float = 0.0
    business_score: float = 0.0  # 0-100 composite health score
    improvement_opportunities: List[str] = None


@dataclass
class YairSiegelBusinessProfile:
    """Complete unified business profile for Yair Siegel"""
    timestamp: str
    business_accounts: BusinessAccounts
    personal_accounts: PersonalAccounts
    credit_profile: CreditProfile
    business_operations: BusinessOperations
    business_health: BusinessHealth
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []
        if self.business_health.improvement_opportunities is None:
            self.business_health.improvement_opportunities = []


class BusinessProfileManager:
    """Manages Yair Siegel's unified business profile"""

    def __init__(self):
        BUSINESS_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    def load_external_accounts(self) -> Dict[str, Any]:
        """Load external accounts data"""
        if EXTERNAL_ACCOUNTS.exists():
            return json.loads(EXTERNAL_ACCOUNTS.read_text())
        return {}

    def load_finance_state(self) -> Dict[str, Any]:
        """Load current finance state"""
        if FINANCE_STATE.exists():
            return json.loads(FINANCE_STATE.read_text())
        return {}

    def load_cards_data(self) -> Dict[str, Any]:
        """Load credit cards data"""
        if CARDS_DATA.exists():
            return json.loads(CARDS_DATA.read_text())
        return {}

    def calculate_business_health_score(self, profile: YairSiegelBusinessProfile) -> float:
        """Calculate composite business health score (0-100)"""
        score = 0.0

        # Liquidity score (30 points)
        total_liquid = profile.business_accounts.total_business_liquid + profile.personal_accounts.total_personal_liquid
        if total_liquid > 5000:
            score += 30
        elif total_liquid > 2000:
            score += 20
        elif total_liquid > 1000:
            score += 10

        # Credit health score (25 points)
        util = profile.credit_profile.credit_utilization
        if util < 0.30:
            score += 25
        elif util < 0.50:
            score += 15
        elif util < 0.70:
            score += 5

        # Credit score (20 points)
        if profile.credit_profile.credit_score >= 750:
            score += 20
        elif profile.credit_profile.credit_score >= 700:
            score += 15
        elif profile.credit_profile.credit_score >= 650:
            score += 10

        # System performance (15 points)
        if profile.business_operations.automation_uptime_pct > 95:
            score += 15
        elif profile.business_operations.automation_uptime_pct > 85:
            score += 10

        # ROI (10 points)
        if profile.business_operations.system_roi_pct > 10:
            score += 10
        elif profile.business_operations.system_roi_pct > 0:
            score += 5

        return round(score, 2)

    def identify_improvement_opportunities(self, profile: YairSiegelBusinessProfile) -> List[str]:
        """Identify business improvement opportunities"""
        opportunities = []

        # Credit utilization opportunities
        if profile.credit_profile.credit_utilization > 0.50:
            opportunities.append("HIGH_PRIORITY: Reduce credit utilization below 50% to improve credit score")
        elif profile.credit_profile.credit_utilization > 0.30:
            opportunities.append("MEDIUM: Consider reducing credit utilization below 30% for optimal score")

        # Liquidity opportunities
        total_liquid = profile.business_accounts.total_business_liquid + profile.personal_accounts.total_personal_liquid
        if total_liquid < 1000:
            opportunities.append("HIGH_PRIORITY: Increase liquid reserves - current runway is low")
        elif total_liquid < 2000:
            opportunities.append("MEDIUM: Build additional liquid reserves for safety buffer")

        # Business account optimization
        if profile.business_accounts.paypal_cashback_balance > 5000:
            opportunities.append("OPPORTUNITY: Deploy excess PayPal cashback balance for higher returns")

        # Trading system optimization
        if profile.business_operations.net_trading_pnl < 0:
            opportunities.append("CRITICAL: Trading system is negative - review alpha model and risk parameters")

        # AI cost optimization
        if profile.business_operations.monthly_ai_cost > 100 and profile.business_operations.system_roi_pct < 5:
            opportunities.append("OPTIMIZE: AI costs are high relative to returns - review cost efficiency")

        # System uptime
        if profile.business_operations.automation_uptime_pct < 95:
            opportunities.append("RELIABILITY: Automation uptime below target - investigate failure points")

        return opportunities

    def generate_current_profile(self) -> YairSiegelBusinessProfile:
        """Generate current business profile from all data sources"""
        ext_accounts = self.load_external_accounts()
        fin_state = self.load_finance_state()
        cards = self.load_cards_data()

        # Business accounts
        business_accounts = BusinessAccounts(
            paypal_business=float(ext_accounts.get("paypal_business", 0)),
            paypal_cashback_balance=float(ext_accounts.get("paypal_cashback_balance", 0)),
        )
        business_accounts.total_business_liquid = (
            business_accounts.paypal_business +
            business_accounts.paypal_cashback_balance
        )

        # Personal accounts
        personal_accounts = PersonalAccounts(
            paypal_personal=float(ext_accounts.get("paypal", 0)),
            monzo=float(ext_accounts.get("monzo", 0)),
            robinhood_cash=float(ext_accounts.get("robinhood_cash", 0)),
            robinhood_total=float(ext_accounts.get("robinhood_total", 0)),
            polymarket_cash=float(ext_accounts.get("polymarket_cash", 0)),
            polymarket_total=float(ext_accounts.get("polymarket_total", 0)),
            schwab=float(ext_accounts.get("schwab", 0)),
        )
        personal_accounts.total_personal_liquid = (
            personal_accounts.paypal_personal +
            personal_accounts.monzo +
            personal_accounts.robinhood_cash +
            personal_accounts.polymarket_cash
        )

        # Credit profile
        total_credit_limit = float(ext_accounts.get("credit_total_limit", 0))
        capital_one = abs(float(ext_accounts.get("credit_capital_one", 0)))
        paypal_credit = abs(float(ext_accounts.get("credit_paypal_credit", 0)))
        total_balance = capital_one + paypal_credit

        credit_profile = CreditProfile(
            capital_one_balance=capital_one,
            paypal_credit_balance=paypal_credit,
            total_credit_balance=total_balance,
            total_credit_limit=total_credit_limit,
            credit_utilization=total_balance / total_credit_limit if total_credit_limit > 0 else 0,
            credit_score=int(ext_accounts.get("credit_score", 0)),
            auth_user_limits=float(ext_accounts.get("auth_user_limits", 0)),
        )

        # Business operations (placeholder - to be populated from actual system metrics)
        business_operations = BusinessOperations()

        # Calculate net worth
        total_net_worth = (
            business_accounts.total_business_liquid +
            personal_accounts.total_personal_liquid +
            personal_accounts.robinhood_total +
            personal_accounts.polymarket_total -
            credit_profile.total_credit_balance
        )

        # Business health
        business_health = BusinessHealth(
            total_net_worth=total_net_worth,
        )

        # Create profile
        profile = YairSiegelBusinessProfile(
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            business_accounts=business_accounts,
            personal_accounts=personal_accounts,
            credit_profile=credit_profile,
            business_operations=business_operations,
            business_health=business_health,
        )

        # Calculate health score and opportunities
        profile.business_health.business_score = self.calculate_business_health_score(profile)
        profile.business_health.improvement_opportunities = self.identify_improvement_opportunities(profile)

        return profile

    def save_profile(self, profile: YairSiegelBusinessProfile):
        """Save current business profile to state file"""
        profile_dict = asdict(profile)
        BUSINESS_STATE_FILE.write_text(json.dumps(profile_dict, indent=2))

        # Also append to history
        with open(BUSINESS_HISTORY_FILE, "a") as f:
            f.write(json.dumps(profile_dict) + "\n")

    def load_current_profile(self) -> YairSiegelBusinessProfile:
        """Load current business profile from state file"""
        if BUSINESS_STATE_FILE.exists():
            data = json.loads(BUSINESS_STATE_FILE.read_text())
            return YairSiegelBusinessProfile(
                timestamp=data["timestamp"],
                business_accounts=BusinessAccounts(**data["business_accounts"]),
                personal_accounts=PersonalAccounts(**data["personal_accounts"]),
                credit_profile=CreditProfile(**data["credit_profile"]),
                business_operations=BusinessOperations(**data["business_operations"]),
                business_health=BusinessHealth(**data["business_health"]),
                notes=data.get("notes", []),
            )
        return self.generate_current_profile()

    def log_metric(self, metric_name: str, value: float, category: str = "general"):
        """Log a business metric"""
        metric = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "metric": metric_name,
            "value": value,
            "category": category,
        }
        with open(BUSINESS_METRICS_FILE, "a") as f:
            f.write(json.dumps(metric) + "\n")

    def get_summary(self, profile: YairSiegelBusinessProfile) -> str:
        """Generate human-readable summary"""
        lines = [
            "=" * 80,
            "YAIR SIEGEL BUSINESS PROFILE",
            "=" * 80,
            f"Timestamp: {profile.timestamp}",
            f"Business Health Score: {profile.business_health.business_score}/100",
            "",
            "BUSINESS ACCOUNTS:",
            f"  PayPal Business:        ${profile.business_accounts.paypal_business:,.2f}",
            f"  PayPal Cashback:        ${profile.business_accounts.paypal_cashback_balance:,.2f}",
            f"  Total Business Liquid:  ${profile.business_accounts.total_business_liquid:,.2f}",
            "",
            "PERSONAL ACCOUNTS:",
            f"  PayPal Personal:        ${profile.personal_accounts.paypal_personal:,.2f}",
            f"  Monzo:                  ${profile.personal_accounts.monzo:,.2f}",
            f"  Robinhood Cash:         ${profile.personal_accounts.robinhood_cash:,.2f}",
            f"  Polymarket Cash:        ${profile.personal_accounts.polymarket_cash:,.2f}",
            f"  Total Personal Liquid:  ${profile.personal_accounts.total_personal_liquid:,.2f}",
            "",
            "CREDIT PROFILE:",
            f"  Total Balance:          ${profile.credit_profile.total_credit_balance:,.2f}",
            f"  Total Limit:            ${profile.credit_profile.total_credit_limit:,.2f}",
            f"  Utilization:            {profile.credit_profile.credit_utilization*100:.1f}%",
            f"  Credit Score:           {profile.credit_profile.credit_score}",
            "",
            "BUSINESS OPERATIONS:",
            f"  Trading System:         {'Active' if profile.business_operations.trading_system_active else 'Inactive'}",
            f"  AI Nexus:               {'Active' if profile.business_operations.ai_nexus_active else 'Inactive'}",
            f"  Automation Uptime:      {profile.business_operations.automation_uptime_pct:.1f}%",
            f"  System ROI:             {profile.business_operations.system_roi_pct:.1f}%",
            "",
            "BUSINESS HEALTH:",
            f"  Total Net Worth:        ${profile.business_health.total_net_worth:,.2f}",
            "",
            "IMPROVEMENT OPPORTUNITIES:",
        ]

        if profile.business_health.improvement_opportunities:
            for opp in profile.business_health.improvement_opportunities:
                lines.append(f"  • {opp}")
        else:
            lines.append("  • No critical opportunities identified - business is healthy!")

        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    """Main entry point - generate and display current business profile"""
    manager = BusinessProfileManager()

    print("Generating Yair Siegel Business Profile...")
    profile = manager.generate_current_profile()

    print("Saving profile...")
    manager.save_profile(profile)

    print("\n" + manager.get_summary(profile))

    print(f"\nProfile saved to: {BUSINESS_STATE_FILE}")
    print(f"History appended to: {BUSINESS_HISTORY_FILE}")


if __name__ == "__main__":
    main()
