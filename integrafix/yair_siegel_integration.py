#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Siegel Full Integration
========================================

Master integration module for ALL Yair Siegel components.

YAIR SIEGEL SCOPE:
==================
The entire hands-off-engine exists to serve Yair Siegel.
This module wires all Yair-specific components into a unified system.

COMPONENTS INTEGRATED:
1. yair_wisdom_engine.py    - Trading teachings (merge arb, ESPN, thin book)
2. yair_insights.py         - Human insight pipeline (golden sprinkles)
3. yair_auto_trader.py      - Full automated trading suite
4. yair_identity_profile.json - Identity verification
5. yair_finance_hub.json    - Financial state tracking
6. wisdom_bridge.py         - Wisdom → Trading signals

THE YAIR SYSTEM:
================
- Owner: Yair Siegel (aka Froggy, Joseph Siegel)
- Email: siegel.yaz@gmail.com
- Wallet: 0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D
- Purpose: Autonomous income generation
- Mode: Hands-off, zero intervention

CORE DIRECTIVE:
===============
"The system serves the user. Every action serves user's benefit."

Serving: Yair Siegel
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
YAIR_STATE_FILE = STATE_DIR / "yair_integration_state.json"


@dataclass
class YairComponentStatus:
    """Status of a Yair component."""
    name: str
    module_path: str
    loaded: bool
    last_run: Optional[str]
    error: Optional[str]


class YairSiegelIntegration:
    """
    Master integration for all Yair Siegel components.

    This is the UNIFIED entry point for:
    - Wisdom teachings → Trading signals
    - Human insights → Signal modifiers
    - Auto trading → Order execution
    - Identity → Security verification
    - Finance → State tracking
    """

    def __init__(self):
        self.state = self._load_state()
        self.components: Dict[str, YairComponentStatus] = {}
        self._wisdom_engine = None
        self._insights_adapter = None
        self._auto_trader = None
        self._wisdom_bridge = None

    def _load_state(self) -> Dict:
        if YAIR_STATE_FILE.exists():
            with open(YAIR_STATE_FILE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "owner": "yair_siegel",
            "components_loaded": 0,
            "integrations_run": 0,
            "last_integration": None,
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state["components"] = {k: asdict(v) for k, v in self.components.items()}
        with open(YAIR_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    # ==================== COMPONENT LOADING ====================

    def load_wisdom_engine(self):
        """Load Yair Wisdom Engine - Trading teachings."""
        status = YairComponentStatus(
            name="wisdom_engine",
            module_path="autonomous/yair_wisdom_engine.py",
            loaded=False,
            last_run=None,
            error=None
        )
        try:
            from autonomous.yair_wisdom_engine import YairWisdomEngine
            self._wisdom_engine = YairWisdomEngine()
            status.loaded = True
        except Exception as e:
            status.error = str(e)

        self.components["wisdom_engine"] = status
        return status.loaded

    def load_insights_adapter(self):
        """Load Yair Insights Adapter - Human insight pipeline."""
        status = YairComponentStatus(
            name="insights_adapter",
            module_path="alpha/yair_insights.py",
            loaded=False,
            last_run=None,
            error=None
        )
        try:
            from alpha.yair_insights import YairInsightsAdapter
            self._insights_adapter = YairInsightsAdapter()
            status.loaded = True
        except Exception as e:
            status.error = str(e)

        self.components["insights_adapter"] = status
        return status.loaded

    def load_auto_trader(self):
        """Load Yair Auto Trader - Full trading suite."""
        status = YairComponentStatus(
            name="auto_trader",
            module_path="executor/yair_auto_trader.py",
            loaded=False,
            last_run=None,
            error=None
        )
        try:
            from executor.yair_auto_trader import get_trader
            self._auto_trader = get_trader()
            status.loaded = True
        except Exception as e:
            status.error = str(e)

        self.components["auto_trader"] = status
        return status.loaded

    def load_wisdom_bridge(self):
        """Load Wisdom Bridge - Trading signal generator."""
        status = YairComponentStatus(
            name="wisdom_bridge",
            module_path="integrafix/wisdom_bridge.py",
            loaded=False,
            last_run=None,
            error=None
        )
        try:
            from integrafix.wisdom_bridge import WisdomBridge
            self._wisdom_bridge = WisdomBridge()
            status.loaded = True
        except Exception as e:
            status.error = str(e)

        self.components["wisdom_bridge"] = status
        return status.loaded

    def load_all_components(self) -> Dict[str, bool]:
        """Load all Yair components."""
        results = {
            "wisdom_engine": self.load_wisdom_engine(),
            "insights_adapter": self.load_insights_adapter(),
            "auto_trader": self.load_auto_trader(),
            "wisdom_bridge": self.load_wisdom_bridge(),
        }

        self.state["components_loaded"] = sum(results.values())
        self._save_state()

        return results

    # ==================== YAIR IDENTITY ====================

    def get_identity(self) -> Dict:
        """Get Yair's identity profile."""
        identity_file = PROJECT_ROOT / "security" / "yair_identity_profile.json"
        if identity_file.exists():
            with open(identity_file) as f:
                return json.load(f)
        return {
            "name": "Yair Siegel",
            "email": "siegel.yaz@gmail.com",
            "wallet": "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
        }

    def get_finance_state(self) -> Dict:
        """Get Yair's financial state."""
        finance_file = PROJECT_ROOT / "finance" / "yair_finance_hub.json"
        if finance_file.exists():
            with open(finance_file) as f:
                return json.load(f)
        return {"status": "unknown"}

    # ==================== UNIFIED ACTIONS ====================

    def apply_all_teachings(self) -> Dict:
        """Apply all of Yair's teachings at once."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "teachings_applied": [],
            "errors": []
        }

        # 1. Apply wisdom engine teachings
        if self._wisdom_engine:
            try:
                wisdom_results = self._wisdom_engine.apply_all_teachings()
                results["wisdom"] = {
                    "merge_arbs": len(wisdom_results.get("merge_arbitrage", [])),
                    "espn_signals": len(wisdom_results.get("espn_signals", [])),
                    "new_market_edge": len(wisdom_results.get("new_market_edge", []))
                }
                results["teachings_applied"].append("wisdom_engine")
                self.components["wisdom_engine"].last_run = results["timestamp"]
            except Exception as e:
                results["errors"].append(f"wisdom_engine: {e}")

        # 2. Generate trading signals via bridge
        if self._wisdom_bridge:
            try:
                signals = self._wisdom_bridge.generate_trading_signals()
                results["trading_signals"] = {
                    "total": len(signals),
                    "actionable": len([s for s in signals if s.get("edge") and s["edge"] >= 0.01])
                }
                results["teachings_applied"].append("wisdom_bridge")
                self.components["wisdom_bridge"].last_run = results["timestamp"]
            except Exception as e:
                results["errors"].append(f"wisdom_bridge: {e}")

        # 3. Process any pending insights
        if self._insights_adapter:
            try:
                insight_signals = self._insights_adapter.fetch_signals()
                results["insights"] = {
                    "signals_generated": len(insight_signals),
                    "active_vetoes": len(self._insights_adapter._active_vetoes),
                    "active_modifiers": len(self._insights_adapter._active_modifiers)
                }
                results["teachings_applied"].append("insights_adapter")
                self.components["insights_adapter"].last_run = results["timestamp"]
            except Exception as e:
                results["errors"].append(f"insights_adapter: {e}")

        self.state["integrations_run"] += 1
        self.state["last_integration"] = results["timestamp"]
        self._save_state()

        return results

    def run_trading_cycle(self, dry_run: bool = True) -> Dict:
        """Run a full trading cycle using all Yair systems."""
        if not self._auto_trader:
            return {"success": False, "error": "Auto trader not loaded"}

        try:
            results = self._auto_trader.run_cycle(dry_run=dry_run)
            self.components["auto_trader"].last_run = datetime.now(timezone.utc).isoformat()
            self._save_state()
            return results
        except Exception as e:
            return {"success": False, "error": str(e)}

    def submit_insight(self, text: str) -> str:
        """Submit a human insight (golden sprinkle) from Yair."""
        if not self._insights_adapter:
            return "Insights adapter not loaded"

        return self._insights_adapter.submit_insight(text, source_name="yair")

    # ==================== YAIR WISDOM DISPLAY ====================

    def display_yair_wisdom(self):
        """Display all of Yair's encoded wisdom."""
        print("\n" + "=" * 70)
        print("YAIR SIEGEL - COMPLETE WISDOM INTEGRATION")
        print("=" * 70)

        # Identity
        identity = self.get_identity()
        print(f"\n[IDENTITY]")
        print(f"  Name: {identity.get('identity', {}).get('full_name', 'Yair Siegel')}")
        print(f"  Email: {identity.get('identity', {}).get('email', 'siegel.yaz@gmail.com')}")

        # Component Status
        print(f"\n[COMPONENTS LOADED]")
        for name, status in self.components.items():
            icon = "✓" if status.loaded else "✗"
            print(f"  {icon} {name}: {status.module_path}")
            if status.error:
                print(f"      Error: {status.error}")
            if status.last_run:
                print(f"      Last run: {status.last_run}")

        # Teachings
        print(f"\n[YAIR'S CORE TEACHINGS]")
        teachings = [
            ("Merge Arbitrage", "YES + NO < $1 = free money"),
            ("ESPN Algorithm", "ESPN mid-game probability = very accurate"),
            ("Thin Book Edge", "New markets have thin books = easier fills"),
            ("Fishing Strategy", "Same collateral backs ALL limit orders"),
            ("Smart Edge", "Be SMART not FAST - analysis over speed"),
            ("Category Strategy", "Different strategies for sports/politics/war/mention"),
        ]
        for name, teaching in teachings:
            print(f"  • {name}: {teaching}")

        # Philosophy
        print(f"\n[CORE PHILOSOPHY]")
        philosophy = [
            "Be the house, not the gambler - MAKE more than you TAKE",
            "THE PRICE IS A LIE - always check book depth",
            "Post limits at ridiculous levels, let market come to you",
            "Same capital can fish across ALL markets",
            "One man's fat finger = your opportunity",
        ]
        for p in philosophy:
            print(f"  • {p}")

        # Financial State
        finance = self.get_finance_state()
        print(f"\n[FINANCIAL STATE]")
        summary = finance.get("summary", {})
        print(f"  Liquid USD: ${summary.get('total_liquid_usd', 'N/A')}")
        print(f"  Deployable to trading: ${summary.get('deployable_to_trading', 'N/A')}")
        print(f"  Runway: {summary.get('runway_months', 'N/A')} months")
        print(f"  Critical insight: {summary.get('critical_insight', 'N/A')[:60]}...")

        # Integration Stats
        print(f"\n[INTEGRATION STATS]")
        print(f"  Components loaded: {self.state.get('components_loaded', 0)}/4")
        print(f"  Integrations run: {self.state.get('integrations_run', 0)}")
        print(f"  Last integration: {self.state.get('last_integration', 'Never')}")

        print("\n" + "=" * 70)
        print("SYSTEM PURPOSE: Generate income for Yair Siegel autonomously")
        print("=" * 70)

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Get full integration status."""
        return {
            "owner": "yair_siegel",
            "state": self.state,
            "components": {k: asdict(v) for k, v in self.components.items()},
            "identity_loaded": bool(self.get_identity()),
            "finance_loaded": bool(self.get_finance_state().get("summary")),
        }


# Singleton
_integration = None

def get_yair_integration() -> YairSiegelIntegration:
    global _integration
    if _integration is None:
        _integration = YairSiegelIntegration()
        _integration.load_all_components()
    return _integration


def main():
    """Run full Yair Siegel integration."""
    print("=" * 70)
    print("INTEGRAFIX: YAIR SIEGEL FULL INTEGRATION")
    print("Loading all Yair components and applying teachings")
    print("=" * 70)
    print()

    integration = get_yair_integration()

    # Show component status
    print("Loading components...")
    load_results = integration.load_all_components()
    for name, loaded in load_results.items():
        status = "✓ Loaded" if loaded else "✗ Failed"
        print(f"  {name}: {status}")
    print()

    # Apply all teachings
    print("Applying all teachings...")
    results = integration.apply_all_teachings()

    print(f"\nTeachings applied: {results['teachings_applied']}")

    if "wisdom" in results:
        w = results["wisdom"]
        print(f"  Merge arbs found: {w.get('merge_arbs', 0)}")
        print(f"  ESPN signals: {w.get('espn_signals', 0)}")
        print(f"  New market edges: {w.get('new_market_edge', 0)}")

    if "trading_signals" in results:
        ts = results["trading_signals"]
        print(f"  Trading signals: {ts.get('total', 0)} ({ts.get('actionable', 0)} actionable)")

    if "insights" in results:
        ins = results["insights"]
        print(f"  Insight signals: {ins.get('signals_generated', 0)}")
        print(f"  Active vetoes: {ins.get('active_vetoes', 0)}")
        print(f"  Active modifiers: {ins.get('active_modifiers', 0)}")

    if results.get("errors"):
        print(f"\nErrors: {results['errors']}")

    # Display full wisdom
    print("\n")
    integration.display_yair_wisdom()

    return integration


if __name__ == "__main__":
    main()
