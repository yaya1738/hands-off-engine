#!/usr/bin/env python3
"""
REALITY FEEDBACK - Grounded in External Outcomes
=================================================

THE PROBLEM: Internal metrics mean nothing if external reality doesn't change.

THIS SYSTEM:
1. Measures REAL outcomes (actual money, actual clients, actual trades)
2. Tracks conversion rates (action → external result)
3. Adapts strategy based on what ACTUALLY works
4. Is grounded in external reality, not internal fantasy

EXTERNAL SIGNALS:
- Polymarket balance (actual money)
- USDC wallet balance (actual crypto)
- Client inquiries (actual interest)
- Trade resolutions (actual P&L)
- Landing page visits (actual traffic)

If an action doesn't produce external results, STOP DOING IT.
If an action produces results, DO MORE OF IT.

Serving: Yair Siegel
"""

import json
import subprocess
import os
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
REALITY_FILE = STATE_DIR / 'reality_feedback.json'
OUTCOME_LOG = STATE_DIR / 'external_outcomes.jsonl'


@dataclass
class ExternalSignal:
    """A signal from the external world."""
    source: str
    signal_type: str
    value: float
    timestamp: str
    raw_data: Dict = None


@dataclass
class ActionOutcome:
    """Maps an action to its external outcome."""
    action_type: str
    action_timestamp: str
    outcome_type: str
    outcome_value: float
    outcome_timestamp: str
    conversion: bool
    notes: str = ""


class RealityFeedback:
    """
    Feedback system grounded in external reality.

    Measures real outcomes, adapts based on what works.
    """

    def __init__(self):
        self.state = self._load_state()
        self.signals: List[ExternalSignal] = []
        self.outcomes: List[ActionOutcome] = []

    def _load_state(self) -> Dict:
        """Load reality state."""
        if REALITY_FILE.exists():
            try:
                with open(REALITY_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "master": MASTER,
            "last_reality_check": None,
            "external_balance": 0.0,
            "total_income": 0.0,
            "conversion_rates": {},
            "strategy_effectiveness": {},
            "what_works": [],
            "what_doesnt": []
        }

    def _save_state(self):
        """Save reality state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(REALITY_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_outcome(self, outcome: ActionOutcome):
        """Log an outcome to the external outcomes log."""
        with open(OUTCOME_LOG, 'a') as f:
            f.write(json.dumps(asdict(outcome)) + "\n")

    # ========================================================================
    # EXTERNAL SIGNAL COLLECTION
    # ========================================================================

    def collect_polymarket_reality(self) -> Optional[ExternalSignal]:
        """Get actual Polymarket balance - the real truth."""
        print("\n[POLYMARKET REALITY]")

        try:
            # Try to get actual balance from API
            from dotenv import load_dotenv
            load_dotenv(BASE_DIR / '.env.polymarket')

            api_key = os.environ.get('POLY_API_KEY')
            api_secret = os.environ.get('POLY_API_SECRET')

            if api_key and api_secret:
                # Would use py-clob-client here for real balance
                # For now, check the model file
                pass

            # Check stored balance
            poly_file = STATE_DIR / 'polymarket-model.json'
            if poly_file.exists():
                with open(poly_file) as f:
                    data = json.load(f)
                    balance = float(data.get('balance', 0))

                    signal = ExternalSignal(
                        source="polymarket",
                        signal_type="balance",
                        value=balance,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        raw_data={"positions": len(data.get('positions', []))}
                    )

                    print(f"  Actual balance: ${balance:.2f}")
                    print(f"  Positions: {signal.raw_data['positions']}")

                    self.signals.append(signal)
                    self.state["external_balance"] = balance
                    return signal

        except Exception as e:
            print(f"  ✗ Error: {e}")

        return None

    def collect_wallet_reality(self) -> Optional[ExternalSignal]:
        """Get actual USDC wallet balance."""
        print("\n[WALLET REALITY]")

        try:
            # Wallet address from .env
            from dotenv import load_dotenv
            load_dotenv(BASE_DIR / '.env')

            wallet = os.environ.get('WALLET_ADDRESS')
            if not wallet:
                print("  ✗ No wallet address configured")
                return None

            # Check Polygon network for USDC balance
            # Using public RPC
            print(f"  Wallet: {wallet[:10]}...{wallet[-6:]}")

            # For now, would query etherscan/polygonscan API
            # Placeholder - in production would use web3.py

            signal = ExternalSignal(
                source="polygon_wallet",
                signal_type="usdc_balance",
                value=0,  # Would be actual balance
                timestamp=datetime.now(timezone.utc).isoformat(),
                raw_data={"wallet": wallet}
            )

            self.signals.append(signal)
            return signal

        except Exception as e:
            print(f"  ✗ Error: {e}")

        return None

    def collect_traffic_reality(self) -> Optional[ExternalSignal]:
        """Get actual landing page traffic."""
        print("\n[TRAFFIC REALITY]")

        try:
            # Check nginx access log for actual visits
            log_file = Path('/var/log/nginx/access.log')
            if log_file.exists():
                # Count recent unique IPs
                result = subprocess.run(
                    ['tail', '-1000', str(log_file)],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    unique_ips = set()
                    for line in lines:
                        if line:
                            ip = line.split()[0]
                            unique_ips.add(ip)

                    visits = len(unique_ips)
                    print(f"  Recent unique visitors: {visits}")

                    signal = ExternalSignal(
                        source="landing_page",
                        signal_type="unique_visitors",
                        value=visits,
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )

                    self.signals.append(signal)
                    return signal
            else:
                print("  ✗ No nginx log found")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        return None

    def collect_github_reality(self) -> Optional[ExternalSignal]:
        """Get actual GitHub engagement."""
        print("\n[GITHUB REALITY]")

        try:
            # Check GitHub API for repo stats
            result = subprocess.run(
                ['gh', 'api', 'repos/yaya1738/hands-off-engine'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                stars = data.get('stargazers_count', 0)
                watchers = data.get('watchers_count', 0)
                forks = data.get('forks_count', 0)

                engagement = stars + watchers + forks
                print(f"  Stars: {stars}, Watchers: {watchers}, Forks: {forks}")
                print(f"  Total engagement: {engagement}")

                signal = ExternalSignal(
                    source="github",
                    signal_type="engagement",
                    value=engagement,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    raw_data={"stars": stars, "watchers": watchers, "forks": forks}
                )

                self.signals.append(signal)
                return signal

        except Exception as e:
            print(f"  ✗ Error: {e}")

        return None

    # ========================================================================
    # OUTCOME TRACKING
    # ========================================================================

    def track_action_outcome(
        self,
        action_type: str,
        action_timestamp: str,
        outcome_type: str,
        outcome_value: float,
        conversion: bool,
        notes: str = ""
    ):
        """Track the external outcome of an action."""
        outcome = ActionOutcome(
            action_type=action_type,
            action_timestamp=action_timestamp,
            outcome_type=outcome_type,
            outcome_value=outcome_value,
            outcome_timestamp=datetime.now(timezone.utc).isoformat(),
            conversion=conversion,
            notes=notes
        )

        self.outcomes.append(outcome)
        self._log_outcome(outcome)

        # Update conversion rates
        if action_type not in self.state.get("conversion_rates", {}):
            self.state["conversion_rates"][action_type] = {
                "total": 0,
                "converted": 0,
                "rate": 0.0
            }

        self.state["conversion_rates"][action_type]["total"] += 1
        if conversion:
            self.state["conversion_rates"][action_type]["converted"] += 1

        total = self.state["conversion_rates"][action_type]["total"]
        converted = self.state["conversion_rates"][action_type]["converted"]
        self.state["conversion_rates"][action_type]["rate"] = converted / total if total > 0 else 0

        self._save_state()

    # ========================================================================
    # ADAPTATION ENGINE
    # ========================================================================

    def analyze_what_works(self) -> Dict:
        """Analyze which actions produce external results."""
        print("\n[ANALYZING WHAT WORKS]")

        analysis = {
            "effective": [],
            "ineffective": [],
            "unknown": []
        }

        conversion_rates = self.state.get("conversion_rates", {})

        for action_type, stats in conversion_rates.items():
            rate = stats.get("rate", 0)
            total = stats.get("total", 0)

            if total < 3:
                analysis["unknown"].append({
                    "action": action_type,
                    "reason": f"Not enough data ({total} attempts)"
                })
            elif rate >= 0.1:  # 10%+ conversion
                analysis["effective"].append({
                    "action": action_type,
                    "conversion_rate": f"{rate*100:.1f}%",
                    "recommendation": "DO MORE"
                })
            else:
                analysis["ineffective"].append({
                    "action": action_type,
                    "conversion_rate": f"{rate*100:.1f}%",
                    "recommendation": "STOP or CHANGE APPROACH"
                })

        # Update state
        self.state["what_works"] = [a["action"] for a in analysis["effective"]]
        self.state["what_doesnt"] = [a["action"] for a in analysis["ineffective"]]
        self._save_state()

        # Print analysis
        print("\n  EFFECTIVE (do more):")
        for item in analysis["effective"]:
            print(f"    ✓ {item['action']}: {item['conversion_rate']}")

        print("\n  INEFFECTIVE (stop/change):")
        for item in analysis["ineffective"]:
            print(f"    ✗ {item['action']}: {item['conversion_rate']}")

        print("\n  NEED MORE DATA:")
        for item in analysis["unknown"]:
            print(f"    ? {item['action']}: {item['reason']}")

        return analysis

    def generate_adapted_strategy(self) -> Dict:
        """Generate adapted strategy based on what works."""
        print("\n[ADAPTED STRATEGY]")

        strategy = {
            "increase": [],
            "decrease": [],
            "experiment": [],
            "focus": None
        }

        what_works = self.state.get("what_works", [])
        what_doesnt = self.state.get("what_doesnt", [])

        # Increase what works
        for action in what_works:
            strategy["increase"].append({
                "action": action,
                "change": "2x effort",
                "reason": "Proven conversion"
            })
            print(f"  ↑ INCREASE: {action}")

        # Decrease what doesn't
        for action in what_doesnt:
            strategy["decrease"].append({
                "action": action,
                "change": "Stop or pivot",
                "reason": "No conversion"
            })
            print(f"  ↓ DECREASE: {action}")

        # If nothing works yet, experiment
        if not what_works:
            experiments = [
                "Try different pricing",
                "Change outreach message",
                "Target different market",
                "Offer free sample first"
            ]
            strategy["experiment"] = experiments
            print("\n  EXPERIMENT (nothing proven yet):")
            for exp in experiments:
                print(f"    → {exp}")

        # Focus on highest conversion
        if what_works:
            strategy["focus"] = what_works[0]
            print(f"\n  PRIMARY FOCUS: {strategy['focus']}")

        return strategy

    # ========================================================================
    # REALITY CHECK
    # ========================================================================

    def reality_check(self) -> Dict:
        """
        Full reality check - collect all external signals and adapt.
        """
        print("\n" + "="*60)
        print("REALITY CHECK - EXTERNAL GROUND TRUTH")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("="*60)

        results = {
            "signals": [],
            "analysis": None,
            "strategy": None
        }

        # Collect all external signals
        print("\n[COLLECTING EXTERNAL SIGNALS]")

        pm_signal = self.collect_polymarket_reality()
        if pm_signal:
            results["signals"].append(asdict(pm_signal))

        wallet_signal = self.collect_wallet_reality()
        if wallet_signal:
            results["signals"].append(asdict(wallet_signal))

        traffic_signal = self.collect_traffic_reality()
        if traffic_signal:
            results["signals"].append(asdict(traffic_signal))

        github_signal = self.collect_github_reality()
        if github_signal:
            results["signals"].append(asdict(github_signal))

        # Analyze what works
        results["analysis"] = self.analyze_what_works()

        # Generate adapted strategy
        results["strategy"] = self.generate_adapted_strategy()

        # Summary
        print("\n" + "="*60)
        print("REALITY SUMMARY")
        print("="*60)

        total_external_value = sum(s.value for s in self.signals if s.signal_type in ['balance', 'usdc_balance'])
        print(f"  External value detected: ${total_external_value:.2f}")
        print(f"  Signals collected: {len(self.signals)}")
        print(f"  What works: {len(self.state.get('what_works', []))} actions")
        print(f"  What doesn't: {len(self.state.get('what_doesnt', []))} actions")

        # Key insight
        if total_external_value == 0:
            print("\n  ⚠ ZERO EXTERNAL VALUE - All actions must be reviewed")
            print("  → Either actions aren't working OR outcomes aren't being tracked")
        else:
            print(f"\n  ✓ External value exists: ${total_external_value:.2f}")

        self.state["last_reality_check"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        return results

    def get_status(self) -> Dict:
        """Get reality feedback status."""
        return {
            "master": MASTER,
            "last_reality_check": self.state.get("last_reality_check"),
            "external_balance": self.state.get("external_balance", 0),
            "total_income": self.state.get("total_income", 0),
            "what_works": self.state.get("what_works", []),
            "what_doesnt": self.state.get("what_doesnt", []),
            "conversion_rates": self.state.get("conversion_rates", {})
        }


# ============================================================================
# INTEGRATION WITH ACTIVE PURSUIT
# ============================================================================

def integrate_with_pursuit():
    """
    Integrate reality feedback with active pursuit.

    When pursuit takes action, reality feedback measures outcome.
    When reality shows what works, pursuit adapts.
    """
    reality = RealityFeedback()

    # Check reality
    results = reality.reality_check()

    # If we have effective strategies, update pursuit
    what_works = reality.state.get("what_works", [])

    if what_works:
        print("\n[UPDATING PURSUIT STRATEGY]")
        print(f"  Focusing on: {what_works}")

        # Would update active_pursuit.py priorities here

    return results


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Reality Feedback System")
    parser.add_argument("command", choices=[
        "status", "check", "analyze", "track", "integrate"
    ])
    parser.add_argument("--action", help="Action type")
    parser.add_argument("--outcome", help="Outcome type")
    parser.add_argument("--value", type=float, help="Outcome value")
    parser.add_argument("--converted", action="store_true", help="Did it convert?")

    args = parser.parse_args()
    reality = RealityFeedback()

    if args.command == "status":
        status = reality.get_status()
        print(f"\n{'='*60}")
        print("REALITY FEEDBACK STATUS")
        print(f"{'='*60}")
        print(f"Last check: {status['last_reality_check']}")
        print(f"External balance: ${status['external_balance']:.2f}")
        print(f"Total income: ${status['total_income']:.2f}")
        print(f"\nWhat works: {status['what_works']}")
        print(f"What doesn't: {status['what_doesnt']}")
        print(f"\nConversion rates:")
        for action, stats in status['conversion_rates'].items():
            print(f"  {action}: {stats['rate']*100:.1f}% ({stats['converted']}/{stats['total']})")

    elif args.command == "check":
        reality.reality_check()

    elif args.command == "analyze":
        reality.analyze_what_works()

    elif args.command == "track":
        if not all([args.action, args.outcome, args.value is not None]):
            print("Error: --action, --outcome, and --value required")
            return
        reality.track_action_outcome(
            action_type=args.action,
            action_timestamp=datetime.now(timezone.utc).isoformat(),
            outcome_type=args.outcome,
            outcome_value=args.value,
            conversion=args.converted
        )
        print(f"Tracked: {args.action} → {args.outcome} (${args.value}, converted={args.converted})")

    elif args.command == "integrate":
        integrate_with_pursuit()


if __name__ == "__main__":
    main()
