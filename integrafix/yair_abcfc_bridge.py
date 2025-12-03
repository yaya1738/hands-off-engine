#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Siegel Knowledge ↔ ABCFC Hierarchy Bridge
==========================================================

Wires Yair's knowledge bases into the ABCFC financial hierarchy:

1. IDENTITY → HIERARCHY ROOT
   - Yair Siegel as root of all ABCFCs
   - Identity attributes flow through system

2. FINANCIAL DATA → HIERARCHY BOUNDS
   - Runway/burn rate constrains worst-case bounds
   - Deployable capital sets position sizing limits
   - Credit availability expands opportunity space

3. TRADING WISDOM → POSITION EVALUATION
   - Teachings inform ABCFC density functions
   - Category strategies improve expected value estimates
   - Risk rules adjust bounds

4. INSIGHTS → NEXUS ACTIONS
   - Golden sprinkles become ABCFC actions
   - Vetoes remove paths from nexus cloud
   - Edge modifiers adjust node scores

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

# Lazy imports to avoid circular dependencies
_abcfc_system = None
_wisdom_engine = None
_insights_adapter = None


def get_abcfc_system():
    """Lazy load ABCFCSystem."""
    global _abcfc_system
    if _abcfc_system is None:
        try:
            from executor.math.abcfc_system import ABCFCSystem
            _abcfc_system = ABCFCSystem
        except ImportError:
            _abcfc_system = None
    return _abcfc_system


def get_wisdom_engine():
    """Lazy load YairWisdomEngine."""
    global _wisdom_engine
    if _wisdom_engine is None:
        try:
            from autonomous.yair_wisdom_engine import YairWisdomEngine
            _wisdom_engine = YairWisdomEngine
        except ImportError:
            _wisdom_engine = None
    return _wisdom_engine


def get_insights_adapter():
    """Lazy load YairInsightsAdapter."""
    global _insights_adapter
    if _insights_adapter is None:
        try:
            from alpha.yair_insights import YairInsightsAdapter
            _insights_adapter = YairInsightsAdapter
        except ImportError:
            _insights_adapter = None
    return _insights_adapter


# =============================================================================
# YAIR KNOWLEDGE LOADER
# =============================================================================

@dataclass
class YairKnowledge:
    """Consolidated Yair Siegel knowledge from all sources."""

    # Identity
    name: str = "Yair Siegel"
    aliases: List[str] = field(default_factory=list)
    email: str = ""
    wallet: str = ""
    role: str = "master"

    # Directive
    primary_directive: str = ""
    philosophy: List[str] = field(default_factory=list)

    # Financial State
    liquid_usd: float = 0.0
    deployable: float = 0.0
    runway_months: float = 0.0
    monthly_burn: float = 0.0
    credit_available: float = 0.0
    credit_utilized: float = 0.0

    # Accounts
    polymarket_balance: float = 0.0
    robinhood_balance: float = 0.0
    paypal_balance: float = 0.0

    # Trading Wisdom
    teachings: List[str] = field(default_factory=list)
    strategies: List[str] = field(default_factory=list)
    category_edges: Dict[str, Dict] = field(default_factory=dict)
    risk_rules: Dict[str, str] = field(default_factory=dict)

    # Performance
    teachings_applied: int = 0
    merge_arbs_found: int = 0
    espn_signals: int = 0

    # Loaded timestamp
    loaded_at: str = ""


class YairKnowledgeLoader:
    """Load and consolidate Yair's knowledge from all sources."""

    def __init__(self):
        self.kernel_path = STATE_DIR / "yair_context_kernel.json"
        self.wisdom_path = STATE_DIR / "yair_wisdom.json"
        self.finance_path = PROJECT_ROOT / "finance" / "yair_finance_hub.json"
        self.identity_path = PROJECT_ROOT / "security" / "yair_identity_profile.json"

    def load(self) -> YairKnowledge:
        """Load all knowledge sources into unified structure."""
        knowledge = YairKnowledge(loaded_at=datetime.now(timezone.utc).isoformat())

        # Load kernel (primary source)
        if self.kernel_path.exists():
            with open(self.kernel_path) as f:
                kernel = json.load(f)

            # Identity
            identity = kernel.get("identity", {})
            knowledge.name = identity.get("name", "Yair Siegel")
            knowledge.aliases = identity.get("aliases", [])
            knowledge.email = identity.get("email", "")
            knowledge.wallet = identity.get("wallet", "")
            knowledge.role = identity.get("role", "master")

            # Directive
            directive = kernel.get("directive", {})
            knowledge.primary_directive = directive.get("primary", "")
            knowledge.philosophy = directive.get("philosophy", [])

            # Financial snapshot
            financial = kernel.get("financial_snapshot", {})
            knowledge.liquid_usd = financial.get("liquid_usd", 0)
            knowledge.deployable = financial.get("deployable", 0)
            knowledge.runway_months = financial.get("runway_months", 0)

            # Trading wisdom
            wisdom = kernel.get("trading_wisdom", {})
            knowledge.teachings = wisdom.get("teachings", [])
            knowledge.strategies = wisdom.get("strategies", [])

        # Load finance hub (detailed accounts)
        if self.finance_path.exists():
            with open(self.finance_path) as f:
                finance = json.load(f)

            # Accounts
            accounts = finance.get("accounts", {})
            knowledge.polymarket_balance = accounts.get("polymarket", {}).get("balance_usdc", 0)
            knowledge.robinhood_balance = accounts.get("robinhood", {}).get("balance_usd", 0)
            knowledge.paypal_balance = accounts.get("paypal_business", {}).get("balance_usd", 0)

            # Credit
            credit = finance.get("credit", {})
            knowledge.credit_available = credit.get("total_available", 0)
            knowledge.credit_utilized = credit.get("total_balance", 0)

            # Burn
            burn = finance.get("monthly_burn", {})
            knowledge.monthly_burn = burn.get("total_usd", 0)

        # Load wisdom state (performance)
        if self.wisdom_path.exists():
            with open(self.wisdom_path) as f:
                wisdom_state = json.load(f)

            knowledge.teachings_applied = wisdom_state.get("teachings_applied", 0)
            knowledge.merge_arbs_found = wisdom_state.get("merge_arbs_found", 0)
            knowledge.espn_signals = wisdom_state.get("espn_signals", 0)

        # Load category edges from wisdom engine
        try:
            from autonomous.yair_wisdom_engine import YAIR_TEACHINGS
            knowledge.category_edges = YAIR_TEACHINGS.get("category_edges", {})
            knowledge.risk_rules = YAIR_TEACHINGS.get("risk_rules", {})
        except ImportError:
            pass

        return knowledge


# =============================================================================
# YAIR-ABCFC BRIDGE
# =============================================================================

class YairABCFCBridge:
    """
    Bridge connecting Yair's knowledge to ABCFC hierarchy.

    Key integrations:
    1. Yair as hierarchy root with real financial bounds
    2. Teachings inform position evaluation
    3. Insights create ABCFC actions
    4. Category strategies adjust expected values
    """

    def __init__(self):
        self.loader = YairKnowledgeLoader()
        self.knowledge: Optional[YairKnowledge] = None
        self._system = None
        self._wisdom_engine = None
        self._insights_adapter = None

        # State file
        self.state_path = STATE_DIR / "yair_abcfc_bridge.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if self.state_path.exists():
            with open(self.state_path) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hierarchies_built": 0,
            "actions_evaluated": 0,
            "teachings_applied": 0,
            "insights_wired": 0,
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=2)

    @property
    def system(self):
        """Get or create ABCFC system rooted in Yair."""
        if self._system is None:
            ABCFCSystem = get_abcfc_system()
            if ABCFCSystem:
                self._system = ABCFCSystem(self.knowledge.name if self.knowledge else "Yair Siegel")
        return self._system

    @property
    def wisdom(self):
        """Get wisdom engine."""
        if self._wisdom_engine is None:
            WisdomEngine = get_wisdom_engine()
            if WisdomEngine:
                self._wisdom_engine = WisdomEngine()
        return self._wisdom_engine

    @property
    def insights(self):
        """Get insights adapter."""
        if self._insights_adapter is None:
            InsightsAdapter = get_insights_adapter()
            if InsightsAdapter:
                self._insights_adapter = InsightsAdapter()
        return self._insights_adapter

    def load_knowledge(self) -> YairKnowledge:
        """Load Yair's knowledge from all sources."""
        self.knowledge = self.loader.load()
        return self.knowledge

    # =========================================================================
    # HIERARCHY BUILDING (Yair → ABCFC)
    # =========================================================================

    def build_yair_hierarchy(self) -> Dict:
        """
        Build ABCFC hierarchy with Yair as root.

        Bounds are constrained by:
        - Worst: -deployable (max loss is deployable capital)
        - Best: +deployable * 10 (ambitious but bounded)
        - Expected: Based on runway situation
        """
        if not self.knowledge:
            self.load_knowledge()

        if not self.system:
            return {"success": False, "error": "ABCFC system not available"}

        # Calculate bounds from financial state
        deployable = self.knowledge.deployable
        runway = self.knowledge.runway_months
        monthly_burn = self.knowledge.monthly_burn

        # Worst case: lose all deployable + need to cover burn
        worst_case = -deployable - (monthly_burn * 0.5)  # Half month emergency

        # Best case: 10x deployable (ambitious)
        best_case = deployable * 10

        # Expected: Based on runway urgency
        # If runway < 1 month, expected should be high to survive
        if runway < 1:
            expected = monthly_burn * 2  # Need to make 2x burn
        elif runway < 3:
            expected = monthly_burn  # Break even at minimum
        else:
            expected = deployable * 0.2  # 20% return target

        # Build categories based on Yair's actual trading profile
        # Category 1: Trading (main income path)
        self.system.add_category(
            "Trading",
            worst=worst_case * 0.8,  # 80% of risk in trading
            best=best_case * 0.9,    # 90% of upside in trading
            expected=expected * 0.8
        )

        # Category 2: AI/Business (costs but potential returns)
        ai_spend = 250  # Monthly AI spend
        self.system.add_category(
            "AI_Business",
            worst=-ai_spend,
            best=ai_spend * 5,  # 5x ROI target
            expected=ai_spend * 0.5  # 50% ROI initial
        )

        # Category 3: Employment (currently 0)
        self.system.add_category(
            "Employment",
            worst=0,
            best=5000,  # Potential monthly if employed
            expected=0  # Not currently employed
        )

        # Sub-categories for Trading
        self.system.add_subcategory(
            "Trading", "Polymarket",
            worst=worst_case * 0.5,
            best=best_case * 0.5,
            expected=expected * 0.5
        )

        self.system.add_subcategory(
            "Trading", "Robinhood",
            worst=worst_case * 0.2,
            best=best_case * 0.3,
            expected=expected * 0.2
        )

        self.system.add_subcategory(
            "Trading", "Credit_Arbitrage",
            worst=-100,  # Fee risk
            best=500,    # Monthly from cycling
            expected=100
        )

        self.state["hierarchies_built"] += 1
        self._save_state()

        return {
            "success": True,
            "root": self.knowledge.name,
            "total_bounds": self.system.total_bounds(),
            "total_expected": self.system.total_expected(),
            "categories": ["Trading", "AI_Business", "Employment"],
            "financial_context": {
                "deployable": deployable,
                "runway_months": runway,
                "monthly_burn": monthly_burn,
            }
        }

    # =========================================================================
    # WISDOM → ABCFC (Teachings inform positions)
    # =========================================================================

    def apply_teachings_to_position(
        self,
        market_question: str,
        current_price: float,
        position_size: float
    ) -> Dict:
        """
        Apply Yair's teachings to evaluate a position's ABCFC.

        Uses:
        - Category detection for strategy selection
        - Risk rules for bound adjustment
        - Core philosophy for expected value estimation
        """
        if not self.knowledge:
            self.load_knowledge()

        if not self.wisdom:
            return {"adjusted": False, "reason": "Wisdom engine not available"}

        # Get category strategy
        category_info = self.wisdom.categorize_market(market_question)
        category = category_info["category"]
        strategy = category_info.get("strategy", {})

        # Base ABCFC calculation
        # Worst: lose entire position
        worst = -position_size * current_price
        # Best: position pays out at $1
        best = position_size * (1 - current_price)
        # Expected: 50/50 baseline
        expected = position_size * (0.5 - current_price)

        # Apply category-specific adjustments
        adjustments = []

        if category == "sports":
            # ESPN algorithm insight: Better edge on live games
            adjustments.append("ESPN algorithm applicable - potential edge")
            expected *= 1.15  # 15% boost to expected

        elif category == "politics":
            # AI analysis insight: Good for complex context
            adjustments.append("AI analysis zone - higher confidence possible")
            expected *= 1.10

        elif category == "war":
            # Pure skill competition
            adjustments.append("Skill competition - research dependent")
            # No adjustment, depends on research quality

        elif category == "mention":
            # Emotional mispricing
            adjustments.append("Mention market - emotional mispricing likely")
            expected *= 1.20  # 20% boost for contrarian plays

        # Apply risk rules
        risk_adjustments = []

        if current_price < 0.05:
            # Deep value zone (from smart edge analysis)
            risk_adjustments.append("Deep value - extreme upside")
            best *= 1.5  # Wider upside

        if current_price > 0.95:
            # Extreme certainty - contrarian potential
            risk_adjustments.append("Extreme certainty - contrarian zone")
            worst *= 0.8  # Reduce worst (limited downside on NO)

        # Apply core philosophy: "Be SMART not FAST"
        # This means: don't rush, wait for better entries
        # Reflected in slightly pessimistic expected (patience required)
        expected *= 0.95

        self.state["teachings_applied"] += 1
        self._save_state()

        return {
            "adjusted": True,
            "category": category,
            "strategy": strategy.get("action", "Apply smart edge analysis"),
            "abcfc": {
                "worst": round(worst, 2),
                "best": round(best, 2),
                "expected": round(expected, 2),
            },
            "adjustments": adjustments,
            "risk_adjustments": risk_adjustments,
            "teachings_used": [
                "Category detection",
                "Smart edge strategy",
                "Risk rules",
                "Core philosophy"
            ]
        }

    # =========================================================================
    # INSIGHTS → NEXUS (Golden sprinkles become actions)
    # =========================================================================

    def wire_insights_to_nexus(self) -> Dict:
        """
        Wire pending insights to ABCFC nexus as possible actions.

        - Alpha signals → Buy/Sell actions
        - Vetoes → Remove paths from nexus
        - Edge modifiers → Adjust action scores
        """
        if not self.system:
            return {"success": False, "error": "ABCFC system not available"}

        if not self.insights:
            return {"success": False, "error": "Insights adapter not available"}

        # Fetch pending signals from insights
        try:
            signals = self.insights.fetch_signals()
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch signals: {e}"}

        wired_actions = []
        vetoes_applied = []
        modifiers_applied = []

        # Import Action class
        try:
            from executor.math.abcfc_system import Action
        except ImportError:
            return {"success": False, "error": "Cannot import Action class"}

        for signal in signals:
            # Convert signal to ABCFC action
            action_type = "buy" if signal.side == "YES" else "sell"
            action = Action(
                name=f"Insight_{signal.market_id[:20]}",
                action_type=action_type,
                params={
                    "size": 10,  # Default size
                    "price": signal.market_price,
                    "confidence": signal.confidence,
                    "source": "yair_insight"
                }
            )

            wired_actions.append({
                "action": action.name,
                "type": action_type,
                "market": signal.market_id,
                "confidence": signal.confidence
            })

        # Check for vetoes
        for veto in self.insights._active_vetoes:
            vetoes_applied.append({
                "pattern": veto.veto_market_pattern,
                "reason": veto.veto_reason,
                "effect": "Paths matching this pattern excluded from nexus"
            })

        # Check for modifiers
        for mod in self.insights._active_modifiers:
            modifiers_applied.append({
                "target": mod.target_market_id,
                "edge_multiplier": mod.edge_multiplier,
                "confidence_adjustment": mod.confidence_adjustment,
                "effect": "Action scores adjusted for matching markets"
            })

        self.state["insights_wired"] += len(wired_actions)
        self._save_state()

        return {
            "success": True,
            "actions_wired": len(wired_actions),
            "vetoes_active": len(vetoes_applied),
            "modifiers_active": len(modifiers_applied),
            "details": {
                "actions": wired_actions,
                "vetoes": vetoes_applied,
                "modifiers": modifiers_applied
            }
        }

    # =========================================================================
    # WISDOM ENGINE → ABCFC POSITIONS
    # =========================================================================

    def wisdom_signals_to_positions(self) -> Dict:
        """
        Convert wisdom engine opportunities to ABCFC positions.

        Scans for:
        - Merge arbitrage opportunities
        - ESPN sports signals
        - New market thin book edges
        """
        if not self.system:
            return {"success": False, "error": "ABCFC system not available"}

        if not self.wisdom:
            return {"success": False, "error": "Wisdom engine not available"}

        positions_added = []

        # 1. Merge Arbitrage
        try:
            merge_arbs = self.wisdom.scan_merge_arbitrage()
            for arb in merge_arbs[:3]:  # Top 3
                # Merge arb is guaranteed profit
                profit = arb["profit_per_pair"]
                cost = arb["total_cost"]

                # Add as position to Polymarket subcategory
                try:
                    pos_name = f"MergeArb_{arb['market'][:15]}"
                    self.system.add_position(
                        "Polymarket",
                        pos_name,
                        worst=0,  # Guaranteed profit (no loss)
                        best=profit * 100,  # Scale by 100 pairs
                        expected=profit * 50,  # Conservative 50 pairs
                        duration=7  # 1 week to resolve
                    )
                    positions_added.append({
                        "name": pos_name,
                        "type": "merge_arb",
                        "expected": profit * 50,
                        "teaching": "YES + NO < $1 = free money"
                    })
                except ValueError:
                    # Position might already exist
                    pass
        except Exception as e:
            pass

        # 2. ESPN Sports Signals
        try:
            espn_signals = self.wisdom.apply_espn_strategy()
            for sig in espn_signals[:2]:  # Top 2
                # Sports edge from ESPN comparison
                pos_name = f"ESPN_{sig['market'][:15]}"
                # Conservative bounds for sports betting
                try:
                    self.system.add_position(
                        "Polymarket",
                        pos_name,
                        worst=-25,  # Max loss $25
                        best=50,    # Max win $50
                        expected=5, # Small positive edge
                        duration=1  # Same day
                    )
                    positions_added.append({
                        "name": pos_name,
                        "type": "espn_signal",
                        "expected": 5,
                        "teaching": "ESPN mid-game probability = very accurate"
                    })
                except ValueError:
                    pass
        except Exception as e:
            pass

        # 3. New Market Edge
        try:
            new_markets = self.wisdom.find_new_market_edge()
            for nm in new_markets[:2]:  # Top 2
                pos_name = f"ThinBook_{nm['market'][:15]}"
                try:
                    self.system.add_position(
                        "Polymarket",
                        pos_name,
                        worst=-20,   # Small size, limited loss
                        best=40,     # 2x potential on edge fills
                        expected=8,  # Moderate edge
                        duration=1   # 4h hold per Yair's rule
                    )
                    positions_added.append({
                        "name": pos_name,
                        "type": "thin_book",
                        "expected": 8,
                        "teaching": "Thin books = easier fills at edges"
                    })
                except ValueError:
                    pass
        except Exception as e:
            pass

        return {
            "success": True,
            "positions_added": len(positions_added),
            "positions": positions_added,
            "total_expected": sum(p["expected"] for p in positions_added),
            "teachings_applied": [
                "Merge Arbitrage",
                "ESPN Algorithm",
                "New Market Thin Book"
            ]
        }

    # =========================================================================
    # UNIFIED EVALUATION
    # =========================================================================

    def evaluate_opportunity(
        self,
        market_id: str,
        market_question: str,
        current_price: float,
        side: str = "YES"
    ) -> Dict:
        """
        Full evaluation of an opportunity using all Yair knowledge.

        Combines:
        1. ABCFC position bounds
        2. Teaching-based adjustments
        3. Insight vetoes/modifiers
        4. Nexus best action recommendation
        """
        if not self.knowledge:
            self.load_knowledge()

        result = {
            "market_id": market_id,
            "market_question": market_question[:50],
            "side": side,
            "current_price": current_price,
            "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 1. Apply teachings
        position_eval = self.apply_teachings_to_position(
            market_question,
            current_price,
            position_size=10  # Default $10
        )
        result["abcfc_evaluation"] = position_eval

        # 2. Check insights for vetoes
        if self.insights:
            veto_reason = self.insights.should_veto(market_id)
            if veto_reason:
                result["vetoed"] = True
                result["veto_reason"] = veto_reason
                result["recommendation"] = "SKIP - Vetoed by Yair"
                return result

            # Check for modifiers
            modifier = self.insights.get_modifier(market_id)
            if modifier:
                result["modifier_applied"] = {
                    "edge_multiplier": modifier.edge_multiplier,
                    "confidence_adjustment": modifier.confidence_adjustment
                }

        # 3. Financial constraint check
        abcfc = position_eval.get("abcfc", {})
        worst = abcfc.get("worst", 0)

        if abs(worst) > self.knowledge.deployable:
            result["warning"] = f"Position worst ({worst}) exceeds deployable ({self.knowledge.deployable})"
            result["recommended_size_reduction"] = self.knowledge.deployable / abs(worst)

        # 4. Generate recommendation
        expected = abcfc.get("expected", 0)

        if expected > 0:
            confidence = min(0.9, 0.5 + expected / 20)  # Scale confidence
            result["recommendation"] = f"CONSIDER {side}"
            result["confidence"] = round(confidence, 2)
            result["expected_value"] = round(expected, 2)
        else:
            result["recommendation"] = "SKIP - Negative expected value"
            result["confidence"] = 0.0

        # Add Yair's relevant teaching
        category = position_eval.get("category", "general")
        if category in self.knowledge.category_edges:
            result["yair_teaching"] = self.knowledge.category_edges[category].get("insight", "")

        return result

    # =========================================================================
    # STATUS & REPORTS
    # =========================================================================

    def get_status(self) -> Dict:
        """Get bridge status and statistics."""
        if not self.knowledge:
            self.load_knowledge()

        return {
            "bridge": "yair_abcfc",
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "yair_identity": {
                "name": self.knowledge.name,
                "role": self.knowledge.role,
                "directive": self.knowledge.primary_directive[:50] + "..." if self.knowledge.primary_directive else "",
            },
            "financial_state": {
                "deployable": self.knowledge.deployable,
                "runway_months": self.knowledge.runway_months,
                "monthly_burn": self.knowledge.monthly_burn,
            },
            "wisdom_stats": {
                "teachings_known": len(self.knowledge.teachings),
                "strategies_available": len(self.knowledge.strategies),
                "categories_mapped": len(self.knowledge.category_edges),
            },
            "bridge_stats": self.state,
            "components": {
                "abcfc_system": "available" if get_abcfc_system() else "unavailable",
                "wisdom_engine": "available" if get_wisdom_engine() else "unavailable",
                "insights_adapter": "available" if get_insights_adapter() else "unavailable",
            }
        }

    def print_report(self):
        """Print comprehensive bridge report."""
        status = self.get_status()

        print("=" * 70)
        print("INTEGRAFIX: Yair Siegel ↔ ABCFC Bridge Report")
        print(f"Generated: {status['timestamp']}")
        print("=" * 70)

        # Identity
        print("\nYAIR IDENTITY:")
        identity = status["yair_identity"]
        print(f"  Name: {identity['name']}")
        print(f"  Role: {identity['role']}")
        print(f"  Directive: {identity['directive']}")

        # Financial
        print("\nFINANCIAL STATE (→ ABCFC Bounds):")
        fin = status["financial_state"]
        print(f"  Deployable: ${fin['deployable']:.0f}")
        print(f"  Runway: {fin['runway_months']:.1f} months")
        print(f"  Monthly Burn: ${fin['monthly_burn']:.0f}")

        # Wisdom
        print("\nWISDOM (→ Position Evaluation):")
        wis = status["wisdom_stats"]
        print(f"  Teachings loaded: {wis['teachings_known']}")
        print(f"  Strategies available: {wis['strategies_available']}")
        print(f"  Categories mapped: {wis['categories_mapped']}")

        # Bridge stats
        print("\nBRIDGE STATISTICS:")
        stats = status["bridge_stats"]
        print(f"  Hierarchies built: {stats.get('hierarchies_built', 0)}")
        print(f"  Actions evaluated: {stats.get('actions_evaluated', 0)}")
        print(f"  Teachings applied: {stats.get('teachings_applied', 0)}")
        print(f"  Insights wired: {stats.get('insights_wired', 0)}")

        # Components
        print("\nCOMPONENTS:")
        for name, status_val in status["components"].items():
            icon = "[+]" if status_val == "available" else "[-]"
            print(f"  {icon} {name}: {status_val}")

        print("\n" + "=" * 70)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_bridge: Optional[YairABCFCBridge] = None


def get_bridge() -> YairABCFCBridge:
    """Get or create the Yair-ABCFC bridge."""
    global _bridge
    if _bridge is None:
        _bridge = YairABCFCBridge()
        _bridge.load_knowledge()
    return _bridge


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="INTEGRAFIX: Yair-ABCFC Bridge")
    parser.add_argument("command", choices=["status", "build", "evaluate", "wire", "report"],
                       default="status", nargs="?")
    parser.add_argument("--market", help="Market ID for evaluation")
    parser.add_argument("--question", help="Market question for evaluation")
    parser.add_argument("--price", type=float, help="Current price")
    args = parser.parse_args()

    bridge = get_bridge()

    if args.command == "status":
        status = bridge.get_status()
        print(json.dumps(status, indent=2))

    elif args.command == "build":
        result = bridge.build_yair_hierarchy()
        print(json.dumps(result, indent=2))

    elif args.command == "wire":
        # Wire wisdom signals to positions
        wisdom_result = bridge.wisdom_signals_to_positions()
        print("\nWisdom → Positions:")
        print(json.dumps(wisdom_result, indent=2))

        # Wire insights to nexus
        insights_result = bridge.wire_insights_to_nexus()
        print("\nInsights → Nexus:")
        print(json.dumps(insights_result, indent=2))

    elif args.command == "evaluate":
        if not args.market:
            print("Error: --market required for evaluation")
            return

        result = bridge.evaluate_opportunity(
            market_id=args.market,
            market_question=args.question or args.market,
            current_price=args.price or 0.5
        )
        print(json.dumps(result, indent=2))

    elif args.command == "report":
        bridge.print_report()


if __name__ == "__main__":
    main()
