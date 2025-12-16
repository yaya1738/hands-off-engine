#!/usr/bin/env python3
"""
CAPITAL BRIDGE - The Missing INTEGRAFIX

Wires Yair's actual assets (skills, time, system) to trading wallet funding.
This is the bridge the system should have built on day 1.

The trading system is useless with $0. This module:
1. Tracks income sources and their status
2. Monitors wallet balance
3. Triggers LIVE mode when threshold reached
4. Provides ABCFC-scored recommendations for capital generation

Author: Claude + Yair
Created: 2025-12-04
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

# Paths
STATE_DIR = Path("/root/hands-off-engine/state")
CAPITAL_STATE_FILE = STATE_DIR / "capital_bridge.json"
ENV_FILE = Path("/root/hands-off-engine/.env.polymarket")


class CapitalBridge:
    """
    The missing link between Yair's assets and the trading system.

    INTEGRAFIX principle: Wire reality to capability.
    Reality = Yair's skills and current situation
    Capability = Trading system that needs capital
    """

    # Minimum USDC to activate live trading
    ACTIVATION_THRESHOLD = 50.0

    # Risk aversion from ABCFC
    RISK_AVERSION = 0.6

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load or initialize capital bridge state."""
        if CAPITAL_STATE_FILE.exists():
            with open(CAPITAL_STATE_FILE) as f:
                return json.load(f)

        # Initialize with default income sources
        default_state = {
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "wallet_balance_usdc": 0.0,
            "activation_threshold": self.ACTIVATION_THRESHOLD,
            "live_mode_active": False,
            "income_sources": {
                "freelance_dev": {
                    "name": "Freelance Development",
                    "status": "available",
                    "effort_hours_weekly": 10,
                    "est_hourly_rate": 50,
                    "est_weekly_usd": 500,
                    "probability": 0.6,
                    "notes": "Upwork, direct clients, contract work"
                },
                "ai_consulting": {
                    "name": "AI/ML Consulting",
                    "status": "available",
                    "effort_hours_weekly": 5,
                    "est_hourly_rate": 75,
                    "est_weekly_usd": 375,
                    "probability": 0.4,
                    "notes": "Leverage this system as portfolio"
                },
                "system_productization": {
                    "name": "Productize Trading System",
                    "status": "not_started",
                    "effort_hours_once": 40,
                    "est_once_usd": 2000,
                    "probability": 0.3,
                    "notes": "SaaS, open source with paid tier, or sell"
                },
                "quick_gigs": {
                    "name": "Quick Technical Gigs",
                    "status": "available",
                    "effort_hours_weekly": 5,
                    "est_hourly_rate": 30,
                    "est_weekly_usd": 150,
                    "probability": 0.7,
                    "notes": "Bug bounties, small fixes, code reviews"
                }
            },
            "income_history": [],
            "capital_injections": [],
            "abcfc_recommendations": []
        }

        self._save_state(default_state)
        return default_state

    def _save_state(self, state: Optional[Dict] = None):
        """Persist state to disk."""
        if state is None:
            state = self.state
        state["last_updated"] = datetime.now().isoformat()

        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CAPITAL_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)

    def inject_capital(self, amount: float, source: str, notes: str = "") -> Dict:
        """
        Inject capital from income sources.

        INTEGRAFIX: Called by payment_handler when payments received.
        """
        # Ensure fields exist
        if "total_earned" not in self.state:
            self.state["total_earned"] = 0
        if "total_injected" not in self.state:
            self.state["total_injected"] = 0
        if "injection_history" not in self.state:
            self.state["injection_history"] = []

        injection = {
            "amount": amount,
            "source": source,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.state["total_earned"] += amount
        self.state["total_injected"] += amount
        self.state["injection_history"].append(injection)

        self._save_state()

        print(f"✓ Capital injected: ${amount:.2f} from {source}")
        return injection

    def get_wallet_balance(self) -> float:
        """Get current wallet USDC balance from Polymarket."""
        try:
            # Try to get balance from existing state files first
            reality_file = STATE_DIR / "reality_snapshot.json"
            if reality_file.exists():
                with open(reality_file) as f:
                    reality = json.load(f)
                    balance = reality.get("polymarket_balance", 0.0)
                    self.state["wallet_balance_usdc"] = balance
                    self._save_state()
                    return balance

            # Fallback: check trading pipeline state
            pipeline_file = STATE_DIR / "trading_pipeline.json"
            if pipeline_file.exists():
                with open(pipeline_file) as f:
                    pipeline = json.load(f)
                    balance = pipeline.get("current_balance", 0.0)
                    self.state["wallet_balance_usdc"] = balance
                    self._save_state()
                    return balance

        except Exception as e:
            print(f"Error getting wallet balance: {e}")

        return self.state.get("wallet_balance_usdc", 0.0)

    def check_activation_ready(self) -> Dict:
        """Check if wallet has enough to activate live trading."""
        balance = self.get_wallet_balance()
        threshold = self.state["activation_threshold"]
        ready = balance >= threshold
        gap = max(0, threshold - balance)

        return {
            "ready": ready,
            "balance": balance,
            "threshold": threshold,
            "gap": gap,
            "message": f"Ready to trade!" if ready else f"Need ${gap:.2f} more to activate"
        }

    def flip_to_live(self) -> bool:
        """
        Switch from DRY_RUN to LIVE mode.
        Only call when activation threshold is met.
        """
        activation = self.check_activation_ready()
        if not activation["ready"]:
            print(f"Cannot activate: {activation['message']}")
            return False

        try:
            # Read current env
            if ENV_FILE.exists():
                with open(ENV_FILE) as f:
                    env_content = f.read()

                # Update DRY_RUN to false
                if "DRY_RUN=true" in env_content:
                    env_content = env_content.replace("DRY_RUN=true", "DRY_RUN=false")
                    with open(ENV_FILE, 'w') as f:
                        f.write(env_content)

                    self.state["live_mode_active"] = True
                    self.state["live_activated_at"] = datetime.now().isoformat()
                    self._save_state()

                    print(f"LIVE MODE ACTIVATED at balance ${activation['balance']:.2f}")
                    return True
                elif "DRY_RUN=false" in env_content:
                    print("Already in LIVE mode")
                    self.state["live_mode_active"] = True
                    self._save_state()
                    return True

        except Exception as e:
            print(f"Error flipping to live: {e}")

        return False

    def record_income(self, source: str, amount: float, notes: str = ""):
        """Record income received from a source."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "amount_usd": amount,
            "notes": notes
        }
        self.state["income_history"].append(entry)
        self._save_state()

        print(f"Recorded ${amount:.2f} from {source}")
        return entry

    def record_capital_injection(self, amount: float, source: str, tx_hash: str = ""):
        """Record USDC deposited to trading wallet."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "amount_usdc": amount,
            "source": source,
            "tx_hash": tx_hash
        }
        self.state["capital_injections"].append(entry)
        self.state["wallet_balance_usdc"] += amount
        self._save_state()

        print(f"Capital injection: ${amount:.2f} USDC from {source}")

        # Check if we can activate
        activation = self.check_activation_ready()
        if activation["ready"]:
            print("Activation threshold reached!")

        return entry

    def abcfc_score_source(self, source_key: str) -> Dict:
        """
        Calculate ABCFC score for an income source.
        Score = expected × probability - risk_aversion × |worst| × (1 - probability)
        """
        source = self.state["income_sources"].get(source_key)
        if not source:
            return {"error": f"Unknown source: {source_key}"}

        # Calculate expected weekly income
        if "est_weekly_usd" in source:
            expected = source["est_weekly_usd"]
            worst = 0  # Worst case: no income, time wasted
            best = expected * 1.5  # Best case: extra work/tips
        else:
            expected = source.get("est_once_usd", 0) / 4  # Amortize over 4 weeks
            worst = -source.get("effort_hours_once", 0) * 10  # Time cost
            best = expected * 2

        prob = source.get("probability", 0.5)

        # ABCFC formula
        score = expected * prob - self.RISK_AVERSION * abs(worst) * (1 - prob)

        return {
            "source": source_key,
            "name": source["name"],
            "expected": expected,
            "probability": prob,
            "best": best,
            "worst": worst,
            "abcfc_score": round(score, 2),
            "status": source["status"]
        }

    def get_recommendations(self) -> List[Dict]:
        """Get ABCFC-ranked recommendations for capital generation."""
        scores = []
        for source_key in self.state["income_sources"]:
            score = self.abcfc_score_source(source_key)
            if "error" not in score:
                scores.append(score)

        # Sort by ABCFC score descending
        scores.sort(key=lambda x: x["abcfc_score"], reverse=True)

        # Add recommendations
        recommendations = []
        for i, score in enumerate(scores):
            rec = {
                "rank": i + 1,
                **score,
                "recommendation": self._generate_recommendation(score)
            }
            recommendations.append(rec)

        self.state["abcfc_recommendations"] = recommendations
        self._save_state()

        return recommendations

    def _generate_recommendation(self, score: Dict) -> str:
        """Generate actionable recommendation based on score."""
        if score["abcfc_score"] > 200:
            return "HIGH PRIORITY: Start immediately"
        elif score["abcfc_score"] > 100:
            return "RECOMMENDED: Good risk-adjusted return"
        elif score["abcfc_score"] > 0:
            return "VIABLE: Positive expected value"
        else:
            return "LOW PRIORITY: Negative risk-adjusted score"

    def update_source_status(self, source_key: str, status: str, notes: str = ""):
        """Update status of an income source."""
        if source_key in self.state["income_sources"]:
            self.state["income_sources"][source_key]["status"] = status
            if notes:
                self.state["income_sources"][source_key]["notes"] = notes
            self._save_state()
            print(f"Updated {source_key} status to: {status}")

    def add_income_source(self, key: str, name: str, est_weekly: float,
                          probability: float, effort_hours: int = 10, notes: str = ""):
        """Add a new income source."""
        self.state["income_sources"][key] = {
            "name": name,
            "status": "available",
            "effort_hours_weekly": effort_hours,
            "est_hourly_rate": est_weekly / effort_hours if effort_hours > 0 else 0,
            "est_weekly_usd": est_weekly,
            "probability": probability,
            "notes": notes
        }
        self._save_state()
        print(f"Added income source: {name}")

    def status_report(self) -> Dict:
        """Generate full status report."""
        activation = self.check_activation_ready()
        recommendations = self.get_recommendations()

        total_income = sum(e["amount_usd"] for e in self.state["income_history"])
        total_injected = sum(e["amount_usdc"] for e in self.state["capital_injections"])

        report = {
            "timestamp": datetime.now().isoformat(),
            "wallet": {
                "balance_usdc": self.state["wallet_balance_usdc"],
                "activation_threshold": self.state["activation_threshold"],
                "gap_to_activation": activation["gap"],
                "ready_to_trade": activation["ready"],
                "live_mode": self.state.get("live_mode_active", False)
            },
            "income": {
                "total_earned_usd": total_income,
                "total_injected_usdc": total_injected,
                "sources_available": sum(1 for s in self.state["income_sources"].values()
                                        if s["status"] == "available"),
                "sources_total": len(self.state["income_sources"])
            },
            "recommendations": recommendations[:3],  # Top 3
            "next_action": recommendations[0] if recommendations else None
        }

        return report

    def print_status(self):
        """Print human-readable status."""
        report = self.status_report()

        print("\n" + "="*60)
        print("CAPITAL BRIDGE STATUS")
        print("="*60)

        wallet = report["wallet"]
        print(f"\nWallet Balance: ${wallet['balance_usdc']:.2f} USDC")
        print(f"Activation Threshold: ${wallet['activation_threshold']:.2f}")
        print(f"Gap to Activation: ${wallet['gap_to_activation']:.2f}")
        print(f"Ready to Trade: {'YES' if wallet['ready_to_trade'] else 'NO'}")
        print(f"Live Mode: {'ACTIVE' if wallet['live_mode'] else 'DRY_RUN'}")

        income = report["income"]
        print(f"\nTotal Earned: ${income['total_earned_usd']:.2f}")
        print(f"Total Injected: ${income['total_injected_usdc']:.2f} USDC")
        print(f"Available Sources: {income['sources_available']}/{income['sources_total']}")

        print("\n" + "-"*60)
        print("TOP RECOMMENDATIONS (ABCFC-Ranked)")
        print("-"*60)

        for rec in report["recommendations"]:
            print(f"\n#{rec['rank']}: {rec['name']}")
            print(f"   ABCFC Score: {rec['abcfc_score']}")
            print(f"   Expected: ${rec['expected']:.0f}/week @ {rec['probability']*100:.0f}% probability")
            print(f"   Status: {rec['status']}")
            print(f"   -> {rec['recommendation']}")

        if report["next_action"]:
            print("\n" + "="*60)
            print(f"NEXT ACTION: {report['next_action']['name']}")
            print("="*60)


# Golden Bridge integration
def wire_to_golden_bridge():
    """Make capital bridge accessible via Golden Bridge natural language."""
    bridge = CapitalBridge()
    return {
        "check_status": bridge.print_status,
        "record_income": bridge.record_income,
        "record_deposit": bridge.record_capital_injection,
        "get_recommendations": bridge.get_recommendations,
        "activate_trading": bridge.flip_to_live
    }


# CLI interface
if __name__ == "__main__":
    import sys

    bridge = CapitalBridge()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "status":
            bridge.print_status()

        elif cmd == "recommend":
            recs = bridge.get_recommendations()
            for r in recs:
                print(f"{r['rank']}. {r['name']}: ABCFC={r['abcfc_score']} - {r['recommendation']}")

        elif cmd == "income" and len(sys.argv) >= 4:
            source = sys.argv[2]
            amount = float(sys.argv[3])
            notes = sys.argv[4] if len(sys.argv) > 4 else ""
            bridge.record_income(source, amount, notes)

        elif cmd == "deposit" and len(sys.argv) >= 3:
            amount = float(sys.argv[2])
            source = sys.argv[3] if len(sys.argv) > 3 else "manual"
            bridge.record_capital_injection(amount, source)

        elif cmd == "activate":
            bridge.flip_to_live()

        else:
            print("Usage:")
            print("  python capital_bridge.py status      - Show full status")
            print("  python capital_bridge.py recommend   - Get ABCFC recommendations")
            print("  python capital_bridge.py income <source> <amount> [notes]")
            print("  python capital_bridge.py deposit <amount> [source]")
            print("  python capital_bridge.py activate    - Try to activate live trading")
    else:
        bridge.print_status()
