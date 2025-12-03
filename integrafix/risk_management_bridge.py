#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Siegel Risk Management Bridge
===============================================

Comprehensive risk analysis covering:

1. FINANCIAL ACCOUNTS
   - Complete inventory
   - Account health
   - Concentration risk

2. INCORPORATION STATUS
   - Current: Operating as individual
   - Risks: Liability, taxes, asset protection
   - Recommendations: LLC, Corp options

3. CENTRALIZATION RISKS
   - Single points of failure
   - Concentration of assets
   - System dependencies

4. DECENTRALIZATION OPPORTUNITIES
   - Multi-wallet strategy
   - Multi-provider redundancy
   - Geographic distribution

5. RISK SCORES & MITIGATION
   - Overall risk score
   - Priority mitigations
   - Action plan

Philosophy:
"Resilience comes from redundancy.
 Single points of failure are future catastrophes.
 Plan for what can go wrong, not just what should go right."

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
FINANCE_DIR = PROJECT_ROOT / "finance"


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class RiskLevel(Enum):
    CRITICAL = "critical"   # Immediate action required
    HIGH = "high"           # Address within days
    MEDIUM = "medium"       # Address within weeks
    LOW = "low"             # Monitor
    MINIMAL = "minimal"     # Acceptable


class RiskCategory(Enum):
    FINANCIAL = "financial"
    LEGAL = "legal"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    CONCENTRATION = "concentration"
    REGULATORY = "regulatory"


class AccountType(Enum):
    BANK = "bank"
    BROKERAGE = "brokerage"
    CRYPTO_WALLET = "crypto_wallet"
    PAYMENT_PROCESSOR = "payment_processor"
    CREDIT = "credit"
    EXCHANGE = "exchange"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FinancialAccount:
    """A financial account."""
    id: str
    name: str
    account_type: AccountType

    # Balances
    balance: float = 0.0
    available: float = 0.0

    # Details
    institution: str = ""
    account_number_last4: str = ""
    currency: str = "USD"

    # Ownership
    ownership: str = "individual"  # individual, joint, business
    entity_name: str = ""  # If business-owned

    # Risk factors
    insured: bool = False
    insurance_limit: float = 0.0
    custodial: bool = True  # True = they hold your money

    # Access
    has_api: bool = False
    mfa_enabled: bool = False

    # Status
    active: bool = True
    frozen: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.account_type.value,
            "balance": self.balance,
            "available": self.available,
            "institution": self.institution,
            "ownership": self.ownership,
            "insured": self.insured,
            "custodial": self.custodial,
            "active": self.active,
        }


@dataclass
class Risk:
    """A identified risk."""
    id: str
    name: str
    description: str
    category: RiskCategory
    level: RiskLevel

    # Impact
    potential_loss: float = 0.0
    probability: float = 0.5  # 0-1

    # Mitigation
    mitigations: List[str] = field(default_factory=list)
    mitigation_cost: float = 0.0
    mitigation_time: str = ""  # "immediate", "days", "weeks", "months"

    # Status
    acknowledged: bool = False
    mitigated: bool = False

    def risk_score(self) -> float:
        """Calculate risk score (0-100)."""
        level_weights = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.75,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.LOW: 0.25,
            RiskLevel.MINIMAL: 0.1,
        }
        return level_weights[self.level] * self.probability * 100

    def expected_loss(self) -> float:
        """Calculate expected loss."""
        return self.potential_loss * self.probability

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "level": self.level.value,
            "potential_loss": self.potential_loss,
            "probability": self.probability,
            "risk_score": self.risk_score(),
            "expected_loss": self.expected_loss(),
            "mitigations": self.mitigations,
            "mitigated": self.mitigated,
        }


# =============================================================================
# RISK MANAGEMENT BRIDGE
# =============================================================================

class RiskManagementBridge:
    """
    Comprehensive risk management for Yair Siegel.
    """

    def __init__(self):
        self.state_path = STATE_DIR / "risk_management.json"
        self.accounts: Dict[str, FinancialAccount] = {}
        self.risks: Dict[str, Risk] = {}

        self.state = self._load_state()
        self._load_accounts()
        self._identify_risks()

    def _load_state(self) -> Dict:
        if self.state_path.exists():
            with open(self.state_path) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_assessment": None,
            "overall_risk_score": 0,
            "risks_identified": 0,
            "risks_mitigated": 0,
        }

    def _save_state(self):
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.state["accounts"] = [a.to_dict() for a in self.accounts.values()]
        self.state["risks"] = [r.to_dict() for r in self.risks.values()]

        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _load_accounts(self):
        """Load all financial accounts."""

        # From finance hub
        hub_path = FINANCE_DIR / "yair_finance_hub.json"
        if hub_path.exists():
            with open(hub_path) as f:
                hub = json.load(f)

            accounts = hub.get("accounts", {})

            # Polymarket
            if "polymarket" in accounts:
                pm = accounts["polymarket"]
                self.accounts["polymarket"] = FinancialAccount(
                    id="polymarket",
                    name="Polymarket Trading Wallet",
                    account_type=AccountType.CRYPTO_WALLET,
                    balance=pm.get("balance_usdc", 0),
                    available=pm.get("balance_usdc", 0),
                    institution="Polymarket (Polygon)",
                    ownership="individual",
                    insured=False,
                    custodial=False,  # Non-custodial
                    has_api=True,
                )

            # Robinhood
            if "robinhood" in accounts:
                rh = accounts["robinhood"]
                self.accounts["robinhood"] = FinancialAccount(
                    id="robinhood",
                    name="Robinhood Brokerage",
                    account_type=AccountType.BROKERAGE,
                    balance=rh.get("balance_usd", 0),
                    available=rh.get("balance_usd", 0),
                    institution="Robinhood",
                    ownership="individual",
                    insured=True,
                    insurance_limit=500000,  # SIPC
                    custodial=True,
                    has_api=False,
                )

            # PayPal
            if "paypal_business" in accounts:
                pp = accounts["paypal_business"]
                self.accounts["paypal"] = FinancialAccount(
                    id="paypal",
                    name="PayPal Business",
                    account_type=AccountType.PAYMENT_PROCESSOR,
                    balance=pp.get("balance_usd", 0),
                    available=pp.get("balance_usd", 0),
                    institution="PayPal",
                    ownership="individual",  # Not properly incorporated
                    insured=False,  # PayPal can freeze
                    custodial=True,
                    has_api=False,  # Not configured
                )

            # Credit Cards
            if "credit_cards" in accounts:
                cc = accounts["credit_cards"]
                credit = hub.get("credit", {})
                self.accounts["credit_cards"] = FinancialAccount(
                    id="credit_cards",
                    name="Credit Cards (Combined)",
                    account_type=AccountType.CREDIT,
                    balance=-cc.get("total_debt", 0),  # Negative = debt
                    available=cc.get("total_available", 0),
                    ownership="individual",
                    insured=False,
                    custodial=False,
                )

        # Add any bank accounts we know about
        self.accounts["bank_primary"] = FinancialAccount(
            id="bank_primary",
            name="Primary Bank Account",
            account_type=AccountType.BANK,
            balance=0,  # Unknown
            institution="Unknown",
            ownership="individual",
            insured=True,
            insurance_limit=250000,  # FDIC
            custodial=True,
        )

    def _identify_risks(self):
        """Identify all risks."""

        # =================================================================
        # INCORPORATION RISKS
        # =================================================================

        self.risks["no_incorporation"] = Risk(
            id="no_incorporation",
            name="No Business Entity",
            description="Operating as individual without LLC/Corp protection. Personal assets at risk from business liabilities.",
            category=RiskCategory.LEGAL,
            level=RiskLevel.HIGH,
            potential_loss=50000,  # Potential lawsuit/liability
            probability=0.15,
            mitigations=[
                "Form LLC in Wyoming or Delaware ($100-500)",
                "Open business bank account",
                "Separate business and personal finances",
                "Get business insurance (E&O, General Liability)",
            ],
            mitigation_cost=500,
            mitigation_time="weeks",
        )

        self.risks["mixed_finances"] = Risk(
            id="mixed_finances",
            name="Commingled Finances",
            description="Business and personal finances mixed. Pierces corporate veil if ever incorporated. Tax complexity.",
            category=RiskCategory.LEGAL,
            level=RiskLevel.MEDIUM,
            potential_loss=10000,  # Tax penalties, accounting costs
            probability=0.3,
            mitigations=[
                "Open dedicated business account",
                "Use business card for business expenses",
                "Track all business transactions separately",
            ],
            mitigation_cost=0,
            mitigation_time="days",
        )

        self.risks["no_liability_insurance"] = Risk(
            id="no_liability_insurance",
            name="No Liability Insurance",
            description="No E&O or general liability insurance. One lawsuit could be catastrophic.",
            category=RiskCategory.LEGAL,
            level=RiskLevel.MEDIUM,
            potential_loss=100000,
            probability=0.05,
            mitigations=[
                "Get E&O insurance ($500-1500/yr)",
                "Get general liability insurance ($400-600/yr)",
                "Consider umbrella policy",
            ],
            mitigation_cost=1000,
            mitigation_time="days",
        )

        self.risks["tax_complexity"] = Risk(
            id="tax_complexity",
            name="Individual Tax Complexity",
            description="Crypto trading + income as individual creates complex tax situation. Self-employment tax at full rate.",
            category=RiskCategory.REGULATORY,
            level=RiskLevel.MEDIUM,
            potential_loss=5000,  # Tax inefficiency
            probability=0.8,
            mitigations=[
                "Form S-Corp for tax efficiency (save 15.3% SE tax)",
                "Use crypto tax software (Koinly, CoinTracker)",
                "Work with crypto-aware CPA",
            ],
            mitigation_cost=2000,
            mitigation_time="months",
        )

        # =================================================================
        # CENTRALIZATION RISKS
        # =================================================================

        self.risks["single_wallet"] = Risk(
            id="single_wallet",
            name="Single Crypto Wallet",
            description="All crypto in one wallet. If compromised, everything lost.",
            category=RiskCategory.CONCENTRATION,
            level=RiskLevel.HIGH,
            potential_loss=self.accounts.get("polymarket", FinancialAccount("", "", AccountType.CRYPTO_WALLET)).balance + 100,  # Current + positions
            probability=0.05,
            mitigations=[
                "Create multiple wallets (hot/cold split)",
                "Use hardware wallet for cold storage",
                "Never keep >$1000 in hot wallet",
                "Use multisig for large amounts",
            ],
            mitigation_cost=100,
            mitigation_time="days",
        )

        self.risks["single_exchange"] = Risk(
            id="single_exchange",
            name="Single Exchange Dependency",
            description="All trading on Polymarket. Platform risk (regulatory, hack, shutdown).",
            category=RiskCategory.CONCENTRATION,
            level=RiskLevel.MEDIUM,
            potential_loss=1000,
            probability=0.1,
            mitigations=[
                "Diversify to other prediction markets (Kalshi)",
                "Keep minimal balance on exchange",
                "Withdraw profits regularly",
            ],
            mitigation_cost=0,
            mitigation_time="immediate",
        )

        self.risks["single_server"] = Risk(
            id="single_server",
            name="Single Server Infrastructure",
            description="All systems on one server. Hardware failure = total system failure.",
            category=RiskCategory.TECHNICAL,
            level=RiskLevel.HIGH,
            potential_loss=5000,  # Lost trading opportunities, recovery time
            probability=0.1,
            mitigations=[
                "Set up backup server (standby)",
                "Use cloud provider with redundancy",
                "Implement automated backups to multiple locations",
                "Document recovery procedures",
            ],
            mitigation_cost=50,  # Monthly backup cost
            mitigation_time="weeks",
        )

        self.risks["single_api_key"] = Risk(
            id="single_api_key",
            name="Single API Key Exposure",
            description="API keys in environment. If server compromised, all keys exposed.",
            category=RiskCategory.TECHNICAL,
            level=RiskLevel.MEDIUM,
            potential_loss=2000,
            probability=0.1,
            mitigations=[
                "Use secrets manager (AWS Secrets, HashiCorp Vault)",
                "Implement key rotation",
                "Use minimal-permission API keys",
                "Set up IP whitelisting where possible",
            ],
            mitigation_cost=0,
            mitigation_time="days",
        )

        self.risks["no_backup"] = Risk(
            id="no_backup",
            name="Inadequate Backup Strategy",
            description="State files and code not properly backed up. Data loss risk.",
            category=RiskCategory.TECHNICAL,
            level=RiskLevel.MEDIUM,
            potential_loss=10000,  # Lost state, trading history, learnings
            probability=0.15,
            mitigations=[
                "Automate daily backups to cloud storage",
                "Backup to multiple providers (S3 + GCS)",
                "Test restore procedures monthly",
                "Version control all code (GitHub)",
            ],
            mitigation_cost=10,  # Monthly storage
            mitigation_time="days",
        )

        # =================================================================
        # FINANCIAL CONCENTRATION RISKS
        # =================================================================

        total_assets = sum(max(0, a.balance) for a in self.accounts.values())

        # Check for concentration
        for acc in self.accounts.values():
            if acc.balance > 0:
                concentration = acc.balance / total_assets if total_assets > 0 else 0
                if concentration > 0.5:
                    self.risks[f"concentration_{acc.id}"] = Risk(
                        id=f"concentration_{acc.id}",
                        name=f"Asset Concentration: {acc.name}",
                        description=f"{concentration:.0%} of assets in {acc.name}. Institution failure = major loss.",
                        category=RiskCategory.CONCENTRATION,
                        level=RiskLevel.MEDIUM if concentration < 0.7 else RiskLevel.HIGH,
                        potential_loss=acc.balance,
                        probability=0.02,
                        mitigations=[
                            "Diversify across multiple institutions",
                            "Keep emergency fund in separate bank",
                            f"Reduce {acc.name} concentration to <30%",
                        ],
                        mitigation_cost=0,
                        mitigation_time="weeks",
                    )

        # =================================================================
        # OPERATIONAL RISKS
        # =================================================================

        self.risks["credit_utilization"] = Risk(
            id="credit_utilization",
            name="High Credit Utilization",
            description="75% credit utilization damages credit score. Limits future borrowing capacity.",
            category=RiskCategory.FINANCIAL,
            level=RiskLevel.HIGH,
            potential_loss=5000,  # Higher interest rates, denied credit
            probability=0.8,  # Already happening
            mitigations=[
                "Pay down to <30% utilization",
                "Request credit limit increases",
                "Consider balance transfer offers",
            ],
            mitigation_cost=0,
            mitigation_time="months",
        )

        self.risks["runway_critical"] = Risk(
            id="runway_critical",
            name="Critical Runway",
            description="<1 month runway. Existential risk to operations.",
            category=RiskCategory.FINANCIAL,
            level=RiskLevel.CRITICAL,
            potential_loss=50000,  # System shutdown, opportunity cost
            probability=0.7,
            mitigations=[
                "Generate immediate income",
                "Reduce non-essential expenses",
                "Liquidate if necessary",
                "Seek bridge funding/loan",
            ],
            mitigation_cost=0,
            mitigation_time="immediate",
        )

        self.risks["no_emergency_fund"] = Risk(
            id="no_emergency_fund",
            name="No Emergency Fund",
            description="No separate emergency fund. One emergency = financial crisis.",
            category=RiskCategory.FINANCIAL,
            level=RiskLevel.HIGH,
            potential_loss=3000,  # One emergency
            probability=0.5,
            mitigations=[
                "Build 3-month emergency fund ($10k target)",
                "Keep in high-yield savings account",
                "Do not touch for trading",
            ],
            mitigation_cost=0,
            mitigation_time="months",
        )

        self.risks["paypal_freeze"] = Risk(
            id="paypal_freeze",
            name="PayPal Freeze Risk",
            description="PayPal can freeze accounts without notice. $1000 at risk.",
            category=RiskCategory.OPERATIONAL,
            level=RiskLevel.MEDIUM,
            potential_loss=1000,
            probability=0.1,
            mitigations=[
                "Keep minimal balance in PayPal",
                "Transfer to bank regularly",
                "Diversify payment processors",
                "Set up Stripe as backup",
            ],
            mitigation_cost=0,
            mitigation_time="immediate",
        )

        # Calculate overall risk score
        total_score = sum(r.risk_score() for r in self.risks.values())
        self.state["overall_risk_score"] = total_score / len(self.risks) if self.risks else 0
        self.state["risks_identified"] = len(self.risks)

        self._save_state()

    # =========================================================================
    # ANALYSIS
    # =========================================================================

    def get_account_summary(self) -> Dict:
        """Get financial accounts summary."""
        total_assets = 0
        total_liabilities = 0
        by_type = {}

        for acc in self.accounts.values():
            if acc.balance >= 0:
                total_assets += acc.balance
            else:
                total_liabilities += abs(acc.balance)

            t = acc.account_type.value
            if t not in by_type:
                by_type[t] = {"count": 0, "total": 0}
            by_type[t]["count"] += 1
            by_type[t]["total"] += acc.balance

        return {
            "total_accounts": len(self.accounts),
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "net_worth": total_assets - total_liabilities,
            "by_type": by_type,
            "accounts": [a.to_dict() for a in self.accounts.values()],
        }

    def get_incorporation_analysis(self) -> Dict:
        """Analyze incorporation status and recommendations."""
        return {
            "current_status": "Individual / Sole Proprietor",
            "entity_name": None,
            "jurisdiction": None,
            "risks": [
                {
                    "risk": "Personal Liability",
                    "description": "All business liabilities are personal liabilities",
                    "severity": "HIGH",
                },
                {
                    "risk": "Tax Inefficiency",
                    "description": "Full self-employment tax (15.3%) on all income",
                    "severity": "MEDIUM",
                },
                {
                    "risk": "Asset Protection",
                    "description": "Personal assets (home, savings) exposed to business lawsuits",
                    "severity": "HIGH",
                },
                {
                    "risk": "Credibility",
                    "description": "No formal business entity may limit opportunities",
                    "severity": "LOW",
                },
            ],
            "recommendations": [
                {
                    "option": "Wyoming LLC",
                    "cost": "$100 filing + $52/yr",
                    "time": "1-2 days online",
                    "benefits": [
                        "Limited liability protection",
                        "Privacy (no public disclosure)",
                        "No state income tax",
                        "Asset protection",
                    ],
                    "drawbacks": [
                        "Still subject to self-employment tax",
                        "Need to maintain separation",
                    ],
                    "priority": "HIGH",
                },
                {
                    "option": "Delaware LLC",
                    "cost": "$90 filing + $300/yr",
                    "time": "Same day possible",
                    "benefits": [
                        "Business-friendly courts",
                        "Well-established law",
                        "Privacy options",
                    ],
                    "drawbacks": [
                        "Higher annual fee",
                        "Need registered agent",
                    ],
                    "priority": "MEDIUM",
                },
                {
                    "option": "S-Corporation Election",
                    "cost": "$500-2000 (accountant setup)",
                    "time": "Weeks to set up properly",
                    "benefits": [
                        "Save 15.3% SE tax on distributions",
                        "More credible for clients",
                        "Better retirement options",
                    ],
                    "drawbacks": [
                        "Must pay reasonable salary",
                        "More complex bookkeeping",
                        "Annual filings required",
                    ],
                    "priority": "MEDIUM (after revenue > $50k)",
                },
            ],
            "immediate_action": "Form Wyoming LLC - Best cost/benefit ratio for current situation",
        }

    def get_centralization_analysis(self) -> Dict:
        """Analyze centralization vs decentralization."""
        centralization_points = []
        decentralization_opportunities = []

        # Check each dimension
        dimensions = {
            "Crypto Storage": {
                "current": "1 hot wallet (Polymarket)",
                "ideal": "Multiple wallets (hot/warm/cold)",
                "risk": "Single point of failure for all crypto",
                "fix": "Create hardware wallet for cold storage",
            },
            "Trading Venue": {
                "current": "1 platform (Polymarket)",
                "ideal": "2-3 platforms (Polymarket, Kalshi, Manifold)",
                "risk": "Platform shutdown = no trading",
                "fix": "Set up accounts on alternative platforms",
            },
            "Infrastructure": {
                "current": "1 server",
                "ideal": "Primary + standby + cloud backup",
                "risk": "Hardware failure = total outage",
                "fix": "Set up cloud standby (DigitalOcean, AWS)",
            },
            "Banking": {
                "current": "1-2 banks + PayPal",
                "ideal": "2+ banks in different institutions",
                "risk": "Bank freeze = no access to funds",
                "fix": "Open account at second bank",
            },
            "Income Sources": {
                "current": "Trading only",
                "ideal": "Trading + consulting + passive income",
                "risk": "Trading losses = no income",
                "fix": "Develop additional income streams",
            },
            "API Providers": {
                "current": "Anthropic primary",
                "ideal": "Multiple AI providers",
                "risk": "Provider outage = system down",
                "fix": "Implement fallback to OpenAI/local models",
            },
        }

        for name, dim in dimensions.items():
            centralization_points.append({
                "dimension": name,
                "current_state": dim["current"],
                "risk": dim["risk"],
            })
            decentralization_opportunities.append({
                "dimension": name,
                "target_state": dim["ideal"],
                "action": dim["fix"],
            })

        # Calculate centralization score (higher = more centralized = more risk)
        centralization_score = 0.75  # High - mostly single points of failure

        return {
            "centralization_score": centralization_score,
            "interpretation": "HIGH - Many single points of failure",
            "centralization_points": centralization_points,
            "decentralization_opportunities": decentralization_opportunities,
            "priority_actions": [
                "1. Hardware wallet for crypto cold storage",
                "2. Cloud backup for state files",
                "3. Secondary bank account",
                "4. Alternative trading platform account",
            ],
        }

    def get_risk_summary(self) -> Dict:
        """Get overall risk summary."""
        by_level = {level.value: [] for level in RiskLevel}
        by_category = {cat.value: [] for cat in RiskCategory}

        total_expected_loss = 0

        for risk in self.risks.values():
            by_level[risk.level.value].append(risk.name)
            by_category[risk.category.value].append(risk.name)
            total_expected_loss += risk.expected_loss()

        return {
            "total_risks": len(self.risks),
            "overall_score": self.state.get("overall_risk_score", 0),
            "total_expected_loss": total_expected_loss,
            "by_level": {k: len(v) for k, v in by_level.items()},
            "by_category": {k: len(v) for k, v in by_category.items()},
            "critical_risks": by_level.get("critical", []),
            "high_risks": by_level.get("high", []),
        }

    def get_priority_mitigations(self, limit: int = 10) -> List[Dict]:
        """Get priority mitigations sorted by impact."""
        mitigations = []

        for risk in self.risks.values():
            if risk.mitigated:
                continue

            for mitigation in risk.mitigations:
                mitigations.append({
                    "risk": risk.name,
                    "risk_level": risk.level.value,
                    "mitigation": mitigation,
                    "expected_loss_reduction": risk.expected_loss(),
                    "cost": risk.mitigation_cost / len(risk.mitigations) if risk.mitigations else 0,
                    "time": risk.mitigation_time,
                })

        # Sort by expected loss reduction (highest first)
        mitigations.sort(key=lambda x: x["expected_loss_reduction"], reverse=True)

        return mitigations[:limit]

    # =========================================================================
    # STATUS & REPORTS
    # =========================================================================

    def get_status(self) -> Dict:
        """Get bridge status."""
        summary = self.get_risk_summary()

        return {
            "bridge": "risk_management",
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "accounts": len(self.accounts),
            "risks_identified": summary["total_risks"],
            "critical_risks": len(summary["critical_risks"]),
            "high_risks": len(summary["high_risks"]),
            "overall_score": summary["overall_score"],
            "total_expected_loss": summary["total_expected_loss"],
        }

    def print_report(self):
        """Print comprehensive risk report."""
        account_summary = self.get_account_summary()
        incorporation = self.get_incorporation_analysis()
        centralization = self.get_centralization_analysis()
        risk_summary = self.get_risk_summary()
        priority_mitigations = self.get_priority_mitigations(10)

        print("=" * 70)
        print("INTEGRAFIX: Yair Siegel Risk Management Report")
        print(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)

        # Financial Accounts
        print("\n>>> FINANCIAL ACCOUNTS")
        print(f"    Total Accounts: {account_summary['total_accounts']}")
        print(f"    Total Assets:      ${account_summary['total_assets']:,.2f}")
        print(f"    Total Liabilities: ${account_summary['total_liabilities']:,.2f}")
        print(f"    Net Worth:         ${account_summary['net_worth']:,.2f}")

        print("\n    ACCOUNTS:")
        for acc in self.accounts.values():
            insured = "INSURED" if acc.insured else "UNINSURED"
            custody = "Custodial" if acc.custodial else "Self-custody"
            print(f"    [{acc.account_type.value}] {acc.name}")
            print(f"      Balance: ${acc.balance:,.2f} | {insured} | {custody}")

        # Incorporation Status
        print("\n>>> INCORPORATION STATUS")
        print(f"    Current: {incorporation['current_status']}")
        print("\n    RISKS:")
        for risk in incorporation["risks"]:
            print(f"    • [{risk['severity']}] {risk['risk']}: {risk['description']}")

        print("\n    RECOMMENDATIONS:")
        for rec in incorporation["recommendations"][:2]:
            print(f"    → {rec['option']} ({rec['cost']}) - {rec['priority']}")
            for benefit in rec["benefits"][:2]:
                print(f"        + {benefit}")

        print(f"\n    IMMEDIATE ACTION: {incorporation['immediate_action']}")

        # Centralization Analysis
        print("\n>>> CENTRALIZATION RISK")
        print(f"    Score: {centralization['centralization_score']:.0%} [{centralization['interpretation']}]")

        print("\n    SINGLE POINTS OF FAILURE:")
        for point in centralization["centralization_points"][:5]:
            print(f"    • {point['dimension']}: {point['current_state']}")

        print("\n    DECENTRALIZATION ACTIONS:")
        for action in centralization["priority_actions"]:
            print(f"    → {action}")

        # Risk Summary
        print("\n>>> RISK SUMMARY")
        print(f"    Total Risks: {risk_summary['total_risks']}")
        print(f"    Overall Score: {risk_summary['overall_score']:.1f}/100")
        print(f"    Total Expected Loss: ${risk_summary['total_expected_loss']:,.0f}")

        print("\n    BY LEVEL:")
        for level, count in risk_summary["by_level"].items():
            if count > 0:
                print(f"      {level.upper()}: {count}")

        # Critical & High Risks
        if risk_summary["critical_risks"]:
            print("\n    CRITICAL RISKS:")
            for risk_name in risk_summary["critical_risks"]:
                print(f"    🔴 {risk_name}")

        if risk_summary["high_risks"]:
            print("\n    HIGH RISKS:")
            for risk_name in risk_summary["high_risks"]:
                print(f"    🟠 {risk_name}")

        # Priority Mitigations
        print("\n>>> PRIORITY MITIGATIONS")
        for i, mit in enumerate(priority_mitigations[:7], 1):
            print(f"    {i}. [{mit['risk_level'].upper()}] {mit['mitigation']}")
            print(f"       Risk: {mit['risk']} | Saves: ${mit['expected_loss_reduction']:,.0f}")

        # Overall Assessment
        overall = "CRITICAL" if risk_summary["overall_score"] > 50 else "HIGH" if risk_summary["overall_score"] > 30 else "MODERATE"
        print(f"\n>>> OVERALL ASSESSMENT: {overall}")
        print("    Key concerns:")
        print("    1. Operating without liability protection (form LLC)")
        print("    2. High centralization (single points of failure)")
        print("    3. Critical runway situation")
        print("    4. High credit utilization")

        print("\n" + "=" * 70)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_bridge: Optional[RiskManagementBridge] = None


def get_risk_bridge() -> RiskManagementBridge:
    """Get or create risk management bridge."""
    global _bridge
    if _bridge is None:
        _bridge = RiskManagementBridge()
    return _bridge


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="INTEGRAFIX: Risk Management Bridge")
    parser.add_argument("command", choices=[
        "status", "accounts", "incorporation", "centralization", "risks", "mitigations", "report"
    ], default="status", nargs="?")
    args = parser.parse_args()

    bridge = get_risk_bridge()

    if args.command == "status":
        print(json.dumps(bridge.get_status(), indent=2))

    elif args.command == "accounts":
        print(json.dumps(bridge.get_account_summary(), indent=2))

    elif args.command == "incorporation":
        print(json.dumps(bridge.get_incorporation_analysis(), indent=2))

    elif args.command == "centralization":
        print(json.dumps(bridge.get_centralization_analysis(), indent=2))

    elif args.command == "risks":
        for risk in bridge.risks.values():
            print(json.dumps(risk.to_dict(), indent=2))
            print()

    elif args.command == "mitigations":
        print(json.dumps(bridge.get_priority_mitigations(), indent=2))

    elif args.command == "report":
        bridge.print_report()


if __name__ == "__main__":
    main()
