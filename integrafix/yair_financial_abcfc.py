#!/usr/bin/env python3
"""
YAIR SIEGEL FINANCIAL ABCFC
===========================

Complete hierarchical ABCFC for Yair Siegel's finances.

HIERARCHY:
==========
Yair Siegel Total Finance
├── Income
│   ├── Employment (salary, w2)
│   ├── Consulting (retainers, projects)
│   ├── Freelance (gigs, contracts)
│   └── Passive (dividends, interest)
├── Trading
│   ├── Polymarket (active positions)
│   ├── Stocks (if any)
│   └── Crypto (if any)
├── Business
│   ├── Hands-off Revenue (subscriptions, API)
│   ├── Signal Sales
│   └── Consulting Revenue
├── Payments Received
│   ├── Wallet USDC
│   └── Bank Transfers
└── Expenses
    ├── Fixed (rent, subscriptions)
    ├── Variable (food, transport)
    └── Business (servers, tools)

NEXUS CLOUD:
============
The nexus cloud shows all possible actions and their impact on
Yair's total financial ABCFC:
- Take on consulting gig → impact on Income + time
- Execute trade → impact on Trading
- Invest in business → impact on expenses + future revenue
- Pay down debt → impact on expenses

Created by: Yair Siegel
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

# Import ABCFC components
try:
    from executor.math.abcfc_system import ABCFCSystem, ABCFCHierarchy, ABCFC, Action
    ABCFC_SYSTEM_AVAILABLE = True
except ImportError:
    ABCFC_SYSTEM_AVAILABLE = False

try:
    from executor.math.abcfc_state import get_state as get_unified_state
    UNIFIED_STATE_AVAILABLE = True
except ImportError:
    UNIFIED_STATE_AVAILABLE = False

try:
    from executor.math.abcfc_layers import get_layers, ABCFCLayers
    LAYERS_AVAILABLE = True
except ImportError:
    LAYERS_AVAILABLE = False


@dataclass
class IncomeSource:
    """A source of income for Yair."""
    name: str
    category: str  # employment, consulting, freelance, passive
    monthly_amount: float  # Expected monthly
    worst_monthly: float  # Worst case monthly
    best_monthly: float  # Best case monthly
    certainty: float = 0.8  # How certain is this income (0-1)
    active: bool = True

    def to_abcfc(self, months: int = 12) -> Dict:
        """Convert to ABCFC bounds over time horizon."""
        return {
            "name": self.name,
            "worst": self.worst_monthly * months * self.certainty,
            "best": self.best_monthly * months,
            "expected": self.monthly_amount * months * self.certainty,
        }


@dataclass
class Expense:
    """An expense category."""
    name: str
    category: str  # fixed, variable, business
    monthly_amount: float
    worst_monthly: float  # Worst case (highest)
    best_monthly: float  # Best case (lowest)
    required: bool = True  # Is this a required expense?

    def to_abcfc(self, months: int = 12) -> Dict:
        """Convert to ABCFC bounds (expenses are negative)."""
        return {
            "name": self.name,
            "worst": -self.worst_monthly * months,  # Worst = highest expense
            "best": -self.best_monthly * months,    # Best = lowest expense
            "expected": -self.monthly_amount * months,
        }


@dataclass
class Payment:
    """A payment received."""
    timestamp: str
    amount: float
    source: str  # wallet, bank, venmo, etc.
    category: str  # income, trading, refund, gift
    metadata: Dict = field(default_factory=dict)


class YairFinancialABCFC:
    """
    Complete financial ABCFC for Yair Siegel.

    Aggregates all income, trading, business, and expenses into
    a unified hierarchical view with nexus cloud decision support.
    """

    def __init__(self):
        self.income_sources: List[IncomeSource] = []
        self.expenses: List[Expense] = []
        self.payments: List[Payment] = []
        self.trading_positions: List[Dict] = []
        self.business_revenue: List[Dict] = []

        self.state = self._load_state()
        self._load_income_sources()
        self._load_expenses()
        self._load_payments()
        self._load_trading_positions()
        self._load_business_revenue()

    def _load_state(self) -> Dict:
        state_file = STATE_DIR / "yair_financial_abcfc.json"
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": None,
            "owner": "Yair Siegel",
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        state_file = STATE_DIR / "yair_financial_abcfc.json"
        with open(state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _load_income_sources(self):
        """Load Yair's income sources."""
        # Default income sources (can be configured)
        income_file = STATE_DIR / "yair_income_sources.json"
        if income_file.exists():
            with open(income_file) as f:
                data = json.load(f)
                for src in data.get("sources", []):
                    self.income_sources.append(IncomeSource(**src))
        else:
            # Initialize with realistic defaults
            self.income_sources = [
                IncomeSource(
                    name="Consulting",
                    category="consulting",
                    monthly_amount=2000,
                    worst_monthly=0,
                    best_monthly=5000,
                    certainty=0.5,
                ),
                IncomeSource(
                    name="Freelance Projects",
                    category="freelance",
                    monthly_amount=1000,
                    worst_monthly=0,
                    best_monthly=3000,
                    certainty=0.3,
                ),
                IncomeSource(
                    name="Trading Profits",
                    category="trading",
                    monthly_amount=500,
                    worst_monthly=-500,
                    best_monthly=2000,
                    certainty=0.6,
                ),
            ]
            # Save defaults
            self._save_income_sources()

    def _save_income_sources(self):
        income_file = STATE_DIR / "yair_income_sources.json"
        with open(income_file, 'w') as f:
            json.dump({
                "sources": [
                    {
                        "name": s.name,
                        "category": s.category,
                        "monthly_amount": s.monthly_amount,
                        "worst_monthly": s.worst_monthly,
                        "best_monthly": s.best_monthly,
                        "certainty": s.certainty,
                        "active": s.active,
                    }
                    for s in self.income_sources
                ]
            }, f, indent=2)

    def _load_expenses(self):
        """Load Yair's expenses."""
        expense_file = STATE_DIR / "yair_expenses.json"
        if expense_file.exists():
            with open(expense_file) as f:
                data = json.load(f)
                for exp in data.get("expenses", []):
                    self.expenses.append(Expense(**exp))
        else:
            # Initialize with realistic defaults
            self.expenses = [
                Expense(
                    name="Server Costs",
                    category="business",
                    monthly_amount=50,
                    worst_monthly=100,
                    best_monthly=30,
                    required=True,
                ),
                Expense(
                    name="API Subscriptions",
                    category="business",
                    monthly_amount=100,
                    worst_monthly=200,
                    best_monthly=50,
                    required=True,
                ),
                Expense(
                    name="Trading Fees",
                    category="variable",
                    monthly_amount=20,
                    worst_monthly=100,
                    best_monthly=5,
                    required=False,
                ),
            ]
            self._save_expenses()

    def _save_expenses(self):
        expense_file = STATE_DIR / "yair_expenses.json"
        with open(expense_file, 'w') as f:
            json.dump({
                "expenses": [
                    {
                        "name": e.name,
                        "category": e.category,
                        "monthly_amount": e.monthly_amount,
                        "worst_monthly": e.worst_monthly,
                        "best_monthly": e.best_monthly,
                        "required": e.required,
                    }
                    for e in self.expenses
                ]
            }, f, indent=2)

    def _load_payments(self):
        """Load payment history."""
        payment_file = STATE_DIR / "payment_monitor.json"
        if payment_file.exists():
            with open(payment_file) as f:
                data = json.load(f)
                for p in data.get("payments", []):
                    self.payments.append(Payment(
                        timestamp=p.get("timestamp", ""),
                        amount=p.get("amount", 0),
                        source="wallet",
                        category="income",
                        metadata=p,
                    ))

    def _load_trading_positions(self):
        """Load trading positions from ABCFC unified state."""
        # INTEGRAFIX: Use abcfc_unified_state.json (has 149+ positions!)
        unified_file = STATE_DIR / "abcfc_unified_state.json"
        if unified_file.exists():
            try:
                with open(unified_file) as f:
                    data = json.load(f)
                    # Convert ABCFC positions to trading format
                    positions = data.get("positions", [])
                    self.trading_positions = [
                        {
                            "market": p.get("name", ""),
                            "category": p.get("category", "Trading"),
                            "worst": p.get("worst", 0),
                            "best": p.get("best", 0),
                            "expected": p.get("expected", 0),
                        }
                        for p in positions
                        if p.get("category") == "Trading" or "trade" in p.get("name", "").lower()
                    ]
            except Exception:
                pass

        # Fallback to polymarket_live_state.json
        if not self.trading_positions:
            pm_file = STATE_DIR / "polymarket_live_state.json"
            if pm_file.exists():
                with open(pm_file) as f:
                    data = json.load(f)
                    self.trading_positions = data.get("positions", [])

    def _load_business_revenue(self):
        """Load business revenue tracking."""
        # Try income accelerator state
        accelerator_file = STATE_DIR / "income_accelerator.json"
        if accelerator_file.exists():
            with open(accelerator_file) as f:
                data = json.load(f)
                if data.get("income_generated", 0) > 0:
                    self.business_revenue.append({
                        "source": "income_accelerator",
                        "amount": data["income_generated"],
                        "category": "business",
                    })

        # INTEGRAFIX: Add trading system P&L as hands-off revenue
        try:
            backend_file = STATE_DIR / "backend_loop.json"
            if backend_file.exists():
                with open(backend_file) as f:
                    backend = json.load(f)

                # Get P&L from outcome tracker
                outcome = backend.get("outcome_tracker", {})
                total_pnl_str = outcome.get("total_pnl", "$0")
                # Parse "$265.73" format
                total_pnl = float(total_pnl_str.replace("$", "").replace(",", ""))

                if total_pnl > 0:
                    self.business_revenue.append({
                        "source": "trading_system",
                        "amount": total_pnl,
                        "category": "automated_trading",
                        "win_rate": outcome.get("win_rate", "0%"),
                    })

                # Also add HFT economics if profitable
                hft_econ = backend.get("hft_economics", {})
                total_net = hft_econ.get("total_net", 0)
                if total_net > 0:
                    self.business_revenue.append({
                        "source": "hft_economics",
                        "amount": total_net,
                        "category": "hft_profit",
                    })
        except Exception:
            pass

    # ==================== ABCFC CONSTRUCTION ====================

    def build_hierarchy(self) -> Optional[ABCFCHierarchy]:
        """Build complete financial ABCFC hierarchy."""
        if not ABCFC_SYSTEM_AVAILABLE:
            return None

        hierarchy = ABCFCHierarchy("Yair Siegel")

        # 1. INCOME category
        income_worst, income_best, income_exp = 0, 0, 0
        for src in self.income_sources:
            if src.active:
                abcfc = src.to_abcfc(months=12)
                income_worst += abcfc["worst"]
                income_best += abcfc["best"]
                income_exp += abcfc["expected"]

        hierarchy.add_category("Income", income_worst, income_best, income_exp)

        # Add income subcategories
        for category in ["consulting", "freelance", "trading", "passive", "employment"]:
            cat_sources = [s for s in self.income_sources if s.category == category and s.active]
            if cat_sources:
                cat_worst = sum(s.to_abcfc()["worst"] for s in cat_sources)
                cat_best = sum(s.to_abcfc()["best"] for s in cat_sources)
                cat_exp = sum(s.to_abcfc()["expected"] for s in cat_sources)
                hierarchy.add_subcategory("Income", category.title(), cat_worst, cat_best, cat_exp)

                # Add individual sources as positions
                for src in cat_sources:
                    abcfc = src.to_abcfc()
                    hierarchy.add_position(category.title(), src.name,
                                          abcfc["worst"], abcfc["best"], abcfc["expected"])

        # 2. TRADING category (from Polymarket)
        trading_worst, trading_best, trading_exp = 0, 0, 0
        for pos in self.trading_positions:
            entry = float(pos.get("avgPrice", 0.5) or 0.5)
            shares = float(pos.get("shares", 0) or 0)
            if shares > 0:
                worst = -shares * entry
                best = shares * (1 - entry)
                exp = shares * (0.5 - entry)
                trading_worst += worst
                trading_best += best
                trading_exp += exp

        hierarchy.add_category("Trading", trading_worst, trading_best, trading_exp)
        hierarchy.add_subcategory("Trading", "Polymarket", trading_worst, trading_best, trading_exp)

        # Add individual positions
        for i, pos in enumerate(self.trading_positions[:10]):
            entry = float(pos.get("avgPrice", 0.5) or 0.5)
            shares = float(pos.get("shares", 0) or 0)
            if shares > 0:
                worst = -shares * entry
                best = shares * (1 - entry)
                exp = shares * (0.5 - entry)
                name = str(pos.get("market", f"Position {i+1}"))[:20]
                hierarchy.add_position("Polymarket", name, worst, best, exp)

        # 3. BUSINESS category
        biz_worst, biz_best, biz_exp = 0, 0, 0
        for rev in self.business_revenue:
            biz_exp += rev.get("amount", 0)
            biz_worst += rev.get("amount", 0) * 0.5  # Conservative
            biz_best += rev.get("amount", 0) * 2.0   # Optimistic

        hierarchy.add_category("Business", biz_worst, biz_best, biz_exp)

        # 4. PAYMENTS category (realized cash)
        payments_total = sum(p.amount for p in self.payments)
        hierarchy.add_category("Payments", payments_total, payments_total, payments_total)

        # 5. EXPENSES category (negative values)
        exp_worst, exp_best, exp_exp = 0, 0, 0
        for exp in self.expenses:
            abcfc = exp.to_abcfc(months=12)
            exp_worst += abcfc["worst"]  # Already negative
            exp_best += abcfc["best"]
            exp_exp += abcfc["expected"]

        hierarchy.add_category("Expenses", exp_worst, exp_best, exp_exp)

        for category in ["fixed", "variable", "business"]:
            cat_exps = [e for e in self.expenses if e.category == category]
            if cat_exps:
                cat_worst = sum(e.to_abcfc()["worst"] for e in cat_exps)
                cat_best = sum(e.to_abcfc()["best"] for e in cat_exps)
                cat_exp = sum(e.to_abcfc()["expected"] for e in cat_exps)
                hierarchy.add_subcategory("Expenses", category.title(), cat_worst, cat_best, cat_exp)

        return hierarchy

    def build_system(self) -> Optional[ABCFCSystem]:
        """Build complete ABCFC System with nexus cloud."""
        if not ABCFC_SYSTEM_AVAILABLE:
            return None

        system = ABCFCSystem("Yair Siegel")
        system.risk_aversion = 0.5

        # Build same structure as hierarchy
        # Income
        for src in self.income_sources:
            if src.active:
                abcfc = src.to_abcfc()
                system.add_category("Income") if "Income" not in [c.name for c in system.hierarchy.root.children] else None
                system.add_position("Income", src.name, abcfc["worst"], abcfc["best"], abcfc["expected"])

        # Trading
        system.add_category("Trading")
        system.add_subcategory("Trading", "Polymarket")
        for i, pos in enumerate(self.trading_positions[:10]):
            entry = float(pos.get("avgPrice", 0.5) or 0.5)
            shares = float(pos.get("shares", 0) or 0)
            if shares > 0:
                worst = -shares * entry
                best = shares * (1 - entry)
                exp = shares * (0.5 - entry)
                name = str(pos.get("market", f"Pos{i+1}"))[:20]
                system.add_position("Polymarket", name, worst, best, exp)

        # Expenses
        system.add_category("Expenses")
        for exp in self.expenses:
            abcfc = exp.to_abcfc()
            system.add_position("Expenses", exp.name, abcfc["worst"], abcfc["best"], abcfc["expected"])

        return system

    def sync_to_unified_state(self):
        """Sync financial data to the unified ABCFC state."""
        if not UNIFIED_STATE_AVAILABLE:
            return

        state = get_unified_state()

        # Update with Yair's financial totals
        hierarchy = self.build_hierarchy()
        if hierarchy:
            state.update_trading([
                {
                    "name": "Yair_Total_Finance",
                    "worst": hierarchy.root.worst,
                    "best": hierarchy.root.best,
                    "expected": hierarchy.root.expected,
                }
            ])

    def sync_to_layers(self):
        """Sync financial data to ABCFC layers."""
        if not LAYERS_AVAILABLE:
            return

        layers = get_layers()

        # Add business income to Hands-off layer
        for rev in self.business_revenue:
            try:
                layers.add_handsoff_stream(
                    stream_name=rev.get("source", "unknown"),
                    monthly=rev.get("amount", 0) / 12,
                    certainty=0.7,
                    months=12,
                )
            except:
                pass

    # ==================== NEXUS CLOUD ====================

    def get_nexus_cloud_actions(self) -> List[Action]:
        """Get possible actions for nexus cloud evaluation."""
        if not ABCFC_SYSTEM_AVAILABLE:
            return []

        actions = [
            Action("Hold", "hold", {}),

            # Income actions
            Action("TakeConsultingGig", "buy", {
                "category": "income",
                "monthly_impact": 2000,
                "time_commitment": 40,  # hours/month
            }),
            Action("LaunchCourse", "buy", {
                "category": "passive",
                "upfront_cost": 100,  # hours
                "monthly_impact": 500,
            }),

            # Trading actions
            Action("DoublePolymarket", "buy", {
                "category": "trading",
                "risk_multiplier": 2.0,
            }),
            Action("HedgePositions", "hedge", {
                "ratio": 0.5,
            }),

            # Expense actions
            Action("CutExpenses", "sell", {
                "category": "expenses",
                "reduction": 0.2,
            }),
            Action("InvestInTools", "buy", {
                "category": "business",
                "monthly_cost": 100,
                "efficiency_gain": 1.2,
            }),
        ]

        return actions

    def evaluate_actions(self) -> Dict:
        """Evaluate all actions in the nexus cloud."""
        system = self.build_system()
        if not system:
            return {"error": "ABCFC System not available"}

        actions = self.get_nexus_cloud_actions()
        results = system.evaluate_all_actions("Income", actions)

        return {
            "current_state": {
                "worst": system.total_bounds()[0],
                "best": system.total_bounds()[1],
                "expected": system.total_expected(),
            },
            "best_action": results[0] if results else None,
            "all_actions": results[:5],
        }

    # ==================== FINANCIAL SUMMARY ====================

    def get_summary(self) -> Dict:
        """Get complete financial summary with ABCFC bounds."""
        hierarchy = self.build_hierarchy()

        # Calculate totals
        total_income = sum(s.to_abcfc()["expected"] for s in self.income_sources if s.active)
        total_expenses = sum(e.to_abcfc()["expected"] for e in self.expenses)
        trading_exp = sum(
            float(p.get("shares", 0) or 0) * (0.5 - float(p.get("avgPrice", 0.5) or 0.5))
            for p in self.trading_positions
        )
        payments_total = sum(p.amount for p in self.payments)

        return {
            "owner": "Yair Siegel",
            "timestamp": datetime.now(timezone.utc).isoformat(),

            # ABCFC bounds
            "total_finance": {
                "worst": hierarchy.total_bounds()[0] if hierarchy else 0,
                "best": hierarchy.total_bounds()[1] if hierarchy else 0,
                "expected": hierarchy.total_expected() if hierarchy else 0,
            },

            # Breakdown
            "income": {
                "expected_annual": total_income,
                "sources": len(self.income_sources),
                "active_sources": len([s for s in self.income_sources if s.active]),
            },
            "trading": {
                "expected": trading_exp,
                "positions": len(self.trading_positions),
            },
            "payments": {
                "total_received": payments_total,
                "count": len(self.payments),
            },
            "expenses": {
                "expected_annual": abs(total_expenses),
                "categories": len(set(e.category for e in self.expenses)),
            },

            # Net
            "net_expected": total_income + total_expenses + trading_exp + payments_total,
        }

    def status(self) -> Dict:
        """Get status for backend loop integration."""
        summary = self.get_summary()

        return {
            "success": True,
            "total_expected": summary["total_finance"]["expected"],
            "total_bounds": (summary["total_finance"]["worst"], summary["total_finance"]["best"]),
            "income_sources": summary["income"]["active_sources"],
            "trading_positions": summary["trading"]["positions"],
            "payments_received": summary["payments"]["total_received"],
            "net_expected": summary["net_expected"],
        }

    # ==================== INCOME MANAGEMENT ====================

    def add_income_source(self, name: str, category: str, monthly: float,
                          worst: float = None, best: float = None, certainty: float = 0.7):
        """Add a new income source."""
        if worst is None:
            worst = monthly * 0.5
        if best is None:
            best = monthly * 1.5

        self.income_sources.append(IncomeSource(
            name=name,
            category=category,
            monthly_amount=monthly,
            worst_monthly=worst,
            best_monthly=best,
            certainty=certainty,
            active=True,
        ))
        self._save_income_sources()

    def add_expense(self, name: str, category: str, monthly: float,
                    worst: float = None, best: float = None, required: bool = True):
        """Add a new expense."""
        if worst is None:
            worst = monthly * 1.2
        if best is None:
            best = monthly * 0.8

        self.expenses.append(Expense(
            name=name,
            category=category,
            monthly_amount=monthly,
            worst_monthly=worst,
            best_monthly=best,
            required=required,
        ))
        self._save_expenses()

    def record_payment(self, amount: float, source: str = "wallet", category: str = "income"):
        """Record a payment received."""
        self.payments.append(Payment(
            timestamp=datetime.now(timezone.utc).isoformat(),
            amount=amount,
            source=source,
            category=category,
        ))

        # Update income accelerator state
        accelerator_file = STATE_DIR / "income_accelerator.json"
        if accelerator_file.exists():
            with open(accelerator_file) as f:
                data = json.load(f)
        else:
            data = {}

        data["income_generated"] = data.get("income_generated", 0) + amount
        data["last_payment"] = datetime.now(timezone.utc).isoformat()

        with open(accelerator_file, 'w') as f:
            json.dump(data, f, indent=2)


# Singleton
_yair_financial = None

def get_yair_financial() -> YairFinancialABCFC:
    """Get or create the Yair Financial ABCFC singleton."""
    global _yair_financial
    if _yair_financial is None:
        _yair_financial = YairFinancialABCFC()
    return _yair_financial


def run_yair_financial_check() -> Dict:
    """Run Yair financial check for backend loop."""
    yair = get_yair_financial()

    # Sync to unified state and layers
    yair.sync_to_unified_state()
    yair.sync_to_layers()

    return yair.status()


if __name__ == "__main__":
    print("=" * 70)
    print("YAIR SIEGEL FINANCIAL ABCFC")
    print("=" * 70)

    yair = get_yair_financial()

    # Get summary
    summary = yair.get_summary()

    print(f"\nOwner: {summary['owner']}")
    print(f"\n[TOTAL FINANCE ABCFC]")
    tf = summary["total_finance"]
    print(f"  Worst:    ${tf['worst']:,.0f}")
    print(f"  Expected: ${tf['expected']:,.0f}")
    print(f"  Best:     ${tf['best']:,.0f}")

    print(f"\n[INCOME]")
    print(f"  Expected Annual: ${summary['income']['expected_annual']:,.0f}")
    print(f"  Active Sources: {summary['income']['active_sources']}")

    print(f"\n[TRADING]")
    print(f"  Expected: ${summary['trading']['expected']:.2f}")
    print(f"  Positions: {summary['trading']['positions']}")

    print(f"\n[PAYMENTS RECEIVED]")
    print(f"  Total: ${summary['payments']['total_received']:.2f}")
    print(f"  Count: {summary['payments']['count']}")

    print(f"\n[EXPENSES]")
    print(f"  Expected Annual: ${summary['expenses']['expected_annual']:,.0f}")

    print(f"\n[NET EXPECTED]")
    print(f"  ${summary['net_expected']:,.0f}")

    # Evaluate actions
    print(f"\n[NEXUS CLOUD - BEST ACTIONS]")
    eval_result = yair.evaluate_actions()
    if "best_action" in eval_result and eval_result["best_action"]:
        best = eval_result["best_action"]
        print(f"  Best: {best.get('action')} (score={best.get('score', 0):.2f})")

    print("\n" + "=" * 70)
