#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Siegel Master ABCFC
====================================

Properly integrates with ABCFCSystem hierarchy and Nexus Cloud.

ABCFC = Absolute Bounds Continuous Fan Chart
  - Profit (P&L) over Time
  - NOT balance sheet (assets/liabilities)

HIERARCHY (P&L based):
======================
Level 0: Yair Siegel (Total P&L)
  Level 1: Trading (P&L from trading activities)
    Level 2: Polymarket (P&L from Polymarket positions)
      Level 3: Individual positions
    Level 2: Robinhood (P&L from stock positions)
  Level 1: Business (P&L from business activities)
    Level 2: AI Services (Revenue - Costs)
  Level 1: Employment (P&L from employment)
    Level 2: Salary (if employed)

RISK ADJUSTMENTS:
=================
Risk factors MODIFY bounds of existing nodes, they are NOT separate nodes.
- Incorporation risk → Multiplies worst-case bounds
- Centralization risk → Reduces confidence
- Operational risk → Adjusts expected value

NEXUS CLOUD:
============
Uses ABCFCSystem.get_top_line_nexus_cloud() for decision making.
All actions evaluated by impact on top-line ABCFC.

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

# Import the REAL ABCFC system
try:
    from executor.math.abcfc_system import ABCFCSystem, Action, ABCFCNexus
    ABCFC_AVAILABLE = True
except ImportError:
    ABCFC_AVAILABLE = False
    ABCFCSystem = None
    Action = None
    ABCFCNexus = None


# =============================================================================
# RISK MODIFIERS (Applied to ABCFC bounds, NOT separate nodes)
# =============================================================================

@dataclass
class RiskModifier:
    """Modifies ABCFC bounds based on risk factors."""
    name: str
    description: str

    # Bound modifiers
    worst_multiplier: float = 1.0   # Multiplies worst-case (>1 = worse)
    best_multiplier: float = 1.0    # Multiplies best-case
    expected_penalty: float = 0.0   # Flat penalty to expected
    confidence: float = 1.0         # Confidence in bounds (0-1)

    # When this risk applies
    applies_to: List[str] = field(default_factory=list)  # Node names

    def apply_to_bounds(self, worst: float, best: float, expected: float) -> Tuple[float, float, float]:
        """Apply this risk modifier to ABCFC bounds."""
        new_worst = worst * self.worst_multiplier
        new_best = best * self.best_multiplier
        new_expected = (expected - self.expected_penalty) * self.confidence
        return new_worst, new_best, new_expected


# =============================================================================
# YAIR MASTER ABCFC
# =============================================================================

class YairMasterABCFC:
    """
    Complete Yair Siegel ABCFC hierarchy with proper Nexus Cloud integration.

    Uses ABCFCSystem for hierarchy and get_top_line_nexus_cloud() for decisions.
    """

    def __init__(self, risk_aversion: float = 0.6):
        if not ABCFC_AVAILABLE:
            raise ImportError("ABCFCSystem not available")

        self.system = ABCFCSystem("Yair Siegel")
        self.system.risk_aversion = risk_aversion
        self.risk_modifiers: List[RiskModifier] = []

        # State
        self.state_path = STATE_DIR / "yair_master_abcfc.json"
        self.built = False

    # =========================================================================
    # DATA LOADING
    # =========================================================================

    def _load_financial_data(self) -> Dict:
        """Load current financial state."""
        data = {
            "deployable": 241,
            "monthly_burn": 3280,
            "runway_months": 0.8,
            "polymarket_balance": 8.99,
            "robinhood_balance": 1500,
            "paypal_balance": 1000,
            "credit_balance": -18000,
        }

        # Try to load from finance hub
        finance_path = PROJECT_ROOT / "finance" / "yair_finance_hub.json"
        if finance_path.exists():
            try:
                with open(finance_path) as f:
                    hub = json.load(f)
                accounts = hub.get("accounts", {})
                data["polymarket_balance"] = accounts.get("polymarket", {}).get("balance_usdc", 8.99)
                data["robinhood_balance"] = accounts.get("robinhood", {}).get("balance_usd", 1500)
                data["paypal_balance"] = accounts.get("paypal_business", {}).get("balance_usd", 1000)
                credit = hub.get("credit", {})
                data["credit_balance"] = -credit.get("total_balance", 18000)
            except:
                pass

        # Try to load from reality bridge
        try:
            from integrafix.reality_bridge import RealityBridge
            bridge = RealityBridge()
            snapshot = bridge.snapshot_reality()
            data["deployable"] = snapshot.deployable
            data["monthly_burn"] = snapshot.monthly_burn
            data["runway_months"] = snapshot.runway_months
        except:
            pass

        return data

    def _load_trading_history(self) -> Dict:
        """Load trading performance."""
        data = {
            "win_rate": 0.655,
            "total_pnl": 215.83,
            "total_trades": 110,
        }

        # Try polymarket state
        poly_state = STATE_DIR / "polymarket_live_state.json"
        if poly_state.exists():
            try:
                with open(poly_state) as f:
                    state = json.load(f)
                data["win_rate"] = state.get("win_rate", 0.655)
                data["total_pnl"] = state.get("total_pnl", 215.83)
                data["total_trades"] = state.get("total_resolved", 110)
            except:
                pass

        return data

    def _load_risk_data(self) -> Dict:
        """Load risk management data."""
        data = {
            "has_llc": False,
            "centralization_score": 0.75,  # High = more centralized
            "credit_utilization": 0.9,
        }

        try:
            from integrafix.risk_management_bridge import RiskManagementBridge
            bridge = RiskManagementBridge()
            inc = bridge.get_incorporation_analysis()
            cent = bridge.get_centralization_analysis()
            data["has_llc"] = "LLC" in inc.get("current_status", "")
            data["centralization_score"] = cent.get("score", 0.75)
        except:
            pass

        return data

    # =========================================================================
    # BUILD RISK MODIFIERS
    # =========================================================================

    def _build_risk_modifiers(self, risk_data: Dict) -> List[RiskModifier]:
        """Build risk modifiers from risk data."""
        modifiers = []

        # 1. No LLC → Personal liability exposure
        if not risk_data.get("has_llc", False):
            modifiers.append(RiskModifier(
                name="No LLC Protection",
                description="Personal assets exposed to business liabilities",
                worst_multiplier=1.3,  # Worst case 30% worse
                confidence=0.9,
                applies_to=["Trading", "Business"]
            ))

        # 2. High centralization → Increased operational risk
        cent_score = risk_data.get("centralization_score", 0.5)
        if cent_score > 0.5:
            modifiers.append(RiskModifier(
                name="Centralization Risk",
                description="Single points of failure in infrastructure",
                expected_penalty=cent_score * 100,  # Penalty proportional to score
                confidence=1 - (cent_score * 0.2),  # Lower confidence
                applies_to=["Trading", "Polymarket"]
            ))

        # 3. Critical runway → Forced liquidation risk
        fin_data = self._load_financial_data()
        runway = fin_data.get("runway_months", 1)
        if runway < 1:
            modifiers.append(RiskModifier(
                name="Critical Runway",
                description="Less than 1 month runway - forced liquidation risk",
                worst_multiplier=1.5,  # Worst case 50% worse
                expected_penalty=200,  # Lost opportunities
                confidence=0.7,
                applies_to=["Yair Siegel"]
            ))

        # 4. High credit utilization
        if risk_data.get("credit_utilization", 0) > 0.8:
            modifiers.append(RiskModifier(
                name="High Credit Utilization",
                description="Credit cards near limit - interest drag",
                expected_penalty=150,  # Monthly interest cost
                applies_to=["Yair Siegel"]
            ))

        return modifiers

    # =========================================================================
    # BUILD HIERARCHY
    # =========================================================================

    def build(self) -> 'YairMasterABCFC':
        """
        Build the ABCFC hierarchy with proper structure.

        Hierarchy is P&L based:
        - Yair Siegel (root)
          - Trading (P&L from trades)
            - Polymarket
            - Robinhood
          - Business (P&L from business)
            - AI Services
          - Employment
        """

        fin_data = self._load_financial_data()
        trading_data = self._load_trading_history()
        risk_data = self._load_risk_data()

        deployable = fin_data["deployable"]
        monthly_burn = fin_data["monthly_burn"]
        win_rate = trading_data["win_rate"]

        # Build risk modifiers
        self.risk_modifiers = self._build_risk_modifiers(risk_data)

        # =====================================================================
        # Level 1: TRADING (P&L)
        # =====================================================================

        # Trading P&L bounds based on deployable capital
        # Worst: lose all deployable
        # Best: 10x return (aggressive but bounded)
        # Expected: based on historical win rate
        trading_worst = -deployable
        trading_best = deployable * 10
        trading_expected = deployable * (win_rate - 0.5) * 4  # Edge * leverage

        self.system.add_category(
            "Trading",
            worst=trading_worst,
            best=trading_best,
            expected=trading_expected
        )

        # Polymarket subcategory
        poly_worst = trading_worst * 0.6
        poly_best = trading_best * 0.6
        poly_expected = trading_expected * 0.6

        self.system.add_subcategory(
            "Trading", "Polymarket",
            worst=poly_worst,
            best=poly_best,
            expected=poly_expected
        )

        # Robinhood subcategory
        rh_balance = fin_data["robinhood_balance"]
        self.system.add_subcategory(
            "Trading", "Robinhood",
            worst=-rh_balance * 0.3,  # 30% max drawdown
            best=rh_balance * 0.5,    # 50% return
            expected=rh_balance * 0.1  # 10% expected
        )

        # =====================================================================
        # Level 1: BUSINESS (P&L)
        # =====================================================================

        # AI Services: $255/mo cost, potential $840/mo value
        ai_cost = 255
        ai_value = 840

        self.system.add_category(
            "Business",
            worst=-ai_cost * 3,        # 3 months cost with no revenue
            best=ai_value * 3,          # 3 months full value realization
            expected=(ai_value - ai_cost)  # Net monthly value
        )

        self.system.add_subcategory(
            "Business", "AI_Services",
            worst=-ai_cost,
            best=ai_value,
            expected=ai_value - ai_cost
        )

        # =====================================================================
        # Level 1: EMPLOYMENT (P&L)
        # =====================================================================

        # Currently unemployed
        self.system.add_category(
            "Employment",
            worst=0,
            best=8000,  # Potential monthly salary
            expected=0  # Currently $0
        )

        # =====================================================================
        # APPLY RISK MODIFIERS (to bounds, not as separate nodes)
        # =====================================================================

        # Risk modifiers adjust the root node bounds
        root_node = self.system.hierarchy.root

        total_worst_mult = 1.0
        total_expected_penalty = 0.0
        total_confidence = 1.0

        for mod in self.risk_modifiers:
            if "Yair Siegel" in mod.applies_to or not mod.applies_to:
                total_worst_mult *= mod.worst_multiplier
                total_expected_penalty += mod.expected_penalty
                total_confidence *= mod.confidence

        # Store risk adjustments for reporting
        self._risk_summary = {
            "worst_multiplier": total_worst_mult,
            "expected_penalty": total_expected_penalty,
            "confidence": total_confidence,
            "modifiers": [m.name for m in self.risk_modifiers]
        }

        self.built = True
        self._save_state()

        return self

    def _save_state(self):
        """Save state to disk."""
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "built": self.built,
            "hierarchy": self.system.hierarchy.to_dict() if self.built else None,
            "risk_modifiers": [m.name for m in self.risk_modifiers],
            "summary": self.get_summary() if self.built else None
        }
        with open(self.state_path, 'w') as f:
            json.dump(state, f, indent=2)

    # =========================================================================
    # NEXUS CLOUD (Decision Making)
    # =========================================================================

    def get_nexus_cloud(self, actions: List[Action] = None) -> Dict:
        """
        Get the top-line nexus cloud using ABCFCSystem.

        This is THE integration point - evaluates how actions across
        the hierarchy affect Yair Siegel's total ABCFC.
        """
        if not self.built:
            self.build()

        if actions is None:
            actions = self._default_actions()

        return self.system.get_top_line_nexus_cloud(actions)

    def _default_actions(self) -> List[Action]:
        """Generate default action set for nexus evaluation."""
        return [
            Action("hold", "hold", {}),
            Action("deploy_capital", "buy", {"size": 50, "price": 0.45}),
            Action("reduce_exposure", "sell", {"size": 25, "price": 0.55}),
            Action("hedge_50pct", "hedge", {"ratio": 0.5}),
            Action("hedge_25pct", "hedge", {"ratio": 0.25}),
        ]

    def get_best_action(self, risk_aversion: float = None) -> Dict:
        """Get the best action from nexus cloud."""
        if risk_aversion is not None:
            self.system.risk_aversion = risk_aversion

        cloud = self.get_nexus_cloud()

        if not cloud.get("futures"):
            return {"action": "hold", "reason": "No actionable futures"}

        best = cloud["futures"][0]  # Already sorted by score

        return {
            "action": best["action"],
            "target_node": best["node"],
            "score": best["score"],
            "top_line_after": best["top_line"],
            "delta": best["delta"],
            "all_futures": len(cloud["futures"])
        }

    # =========================================================================
    # ANALYSIS
    # =========================================================================

    def get_summary(self) -> Dict:
        """Get summary of master ABCFC."""
        if not self.built:
            return {"error": "Not built yet"}

        bounds = self.system.total_bounds()
        expected = self.system.total_expected()

        # Apply risk adjustments to summary
        risk = self._risk_summary
        adjusted_worst = bounds[0] * risk["worst_multiplier"]
        adjusted_expected = (expected - risk["expected_penalty"]) * risk["confidence"]

        return {
            "bounds": {
                "worst": bounds[0],
                "best": bounds[1],
                "expected": expected
            },
            "risk_adjusted": {
                "worst": adjusted_worst,
                "expected": adjusted_expected,
                "worst_multiplier": risk["worst_multiplier"],
                "confidence": risk["confidence"]
            },
            "risk_modifiers": risk["modifiers"],
            "hierarchy_nodes": len(self.system.hierarchy.all_nodes)
        }

    def get_optimal_path(self) -> Dict:
        """Calculate optimal path using nexus cloud."""
        best = self.get_best_action()

        # Get alternative paths
        cloud = self.get_nexus_cloud()
        alternatives = cloud.get("futures", [])[1:4]  # Top 3 alternatives

        return {
            "recommended": best,
            "alternatives": [
                {"action": f["action"], "node": f["node"], "score": f["score"]}
                for f in alternatives
            ],
            "cloud_bounds": cloud.get("cloud_bounds", {})
        }

    # =========================================================================
    # VISUALIZATION
    # =========================================================================

    def print_hierarchy(self):
        """Print the ABCFC hierarchy."""
        if not self.built:
            self.build()
        self.system.print_hierarchy()

    def print_report(self):
        """Print comprehensive report."""
        if not self.built:
            self.build()

        print("=" * 70)
        print("YAIR SIEGEL MASTER ABCFC")
        print(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)

        # Summary
        summary = self.get_summary()
        bounds = summary["bounds"]
        risk_adj = summary["risk_adjusted"]

        print(f"\n>>> TOP-LINE ABCFC")
        print(f"    Raw Bounds:      [{bounds['worst']:+,.0f}, {bounds['best']:+,.0f}]")
        print(f"    Raw Expected:    {bounds['expected']:+,.0f}")
        print(f"    Risk-Adj Worst:  {risk_adj['worst']:+,.0f} ({risk_adj['worst_multiplier']:.1f}x)")
        print(f"    Risk-Adj Exp:    {risk_adj['expected']:+,.0f} ({risk_adj['confidence']:.0%} conf)")

        # Hierarchy
        print(f"\n>>> HIERARCHY")
        self.print_hierarchy()

        # Risk Modifiers
        print(f"\n>>> RISK MODIFIERS (Applied to bounds)")
        for mod in self.risk_modifiers:
            print(f"    - {mod.name}: worst×{mod.worst_multiplier:.1f}, penalty=${mod.expected_penalty:.0f}")

        # Nexus Cloud
        print(f"\n>>> NEXUS CLOUD (Decision Space)")
        cloud = self.get_nexus_cloud()
        print(f"    Futures evaluated: {len(cloud.get('futures', []))}")

        if cloud.get("cloud_bounds"):
            cb = cloud["cloud_bounds"]
            print(f"    Worst possible:  {cb['worst_possible']:+,.0f}")
            print(f"    Best possible:   {cb['best_possible']:+,.0f}")
            print(f"    Expected range:  [{cb['worst_expected']:+,.0f}, {cb['best_expected']:+,.0f}]")

        # Best Action
        print(f"\n>>> RECOMMENDED ACTION")
        best = self.get_best_action()
        print(f"    Action: {best['action']} on {best.get('target_node', 'root')}")
        print(f"    Score:  {best.get('score', 0):.2f}")
        if best.get("delta"):
            delta = best["delta"]
            print(f"    Delta:  E={delta.get('expected', 0):+,.0f}, W={delta.get('worst', 0):+,.0f}")

        print("\n" + "=" * 70)

    def plot_nexus_cloud(self, save_path: str = None) -> Dict:
        """Plot the nexus cloud visualization."""
        if not self.built:
            self.build()

        actions = self._default_actions()
        return self.system.plot_top_line_nexus(actions, save_path=save_path)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Yair Siegel Master ABCFC")
    parser.add_argument("command", choices=["build", "summary", "nexus", "path", "report", "plot"],
                       default="report", nargs="?")
    parser.add_argument("--risk", type=float, default=0.6, help="Risk aversion (0-1)")
    args = parser.parse_args()

    try:
        master = YairMasterABCFC(risk_aversion=args.risk)
        master.build()

        if args.command == "build":
            print(json.dumps(master.get_summary(), indent=2))

        elif args.command == "summary":
            print(json.dumps(master.get_summary(), indent=2))

        elif args.command == "nexus":
            cloud = master.get_nexus_cloud()
            print(json.dumps({
                "current": cloud.get("current"),
                "cloud_bounds": cloud.get("cloud_bounds"),
                "top_futures": cloud.get("futures", [])[:5]
            }, indent=2))

        elif args.command == "path":
            print(json.dumps(master.get_optimal_path(), indent=2))

        elif args.command == "plot":
            result = master.plot_nexus_cloud()
            print(json.dumps(result, indent=2))

        elif args.command == "report":
            master.print_report()

    except ImportError as e:
        print(f"Error: {e}")
        print("ABCFCSystem not available. Check executor/math/abcfc_system.py")


if __name__ == "__main__":
    main()
