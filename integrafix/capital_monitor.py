#!/usr/bin/env python3
"""
INTEGRAFIX: Capital Source Monitor
===================================

Automatically detects capital injections from multiple sources and
wires them to capital_bridge for trading activation.

CAPITAL SOURCES:
1. Crypto wallet deposits (on-chain monitoring)
2. Payment handler (job payments received)
3. Bank transfers (manual entry with auto-detect)
4. Test injections (for development)

Integration with capital_bridge:
- Monitors all sources continuously
- Auto-calls capital_bridge.inject_capital()
- Triggers flip_to_live() when threshold met

Author: Claude + Yair
Created: 2025-12-16
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
MONITOR_STATE = STATE_DIR / "capital_monitor.json"


class CapitalMonitor:
    """
    Monitors multiple capital sources and auto-injects to capital_bridge.

    INTEGRAFIX: Wires capital detection to trading activation.
    """

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load monitor state."""
        if MONITOR_STATE.exists():
            with open(MONITOR_STATE) as f:
                return json.load(f)

        # Default state
        default = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sources": {
                "crypto_wallet": {
                    "enabled": True,
                    "address": "0xB314345D218ED4CF75C17636a2307244E7dA761b",
                    "last_check": None,
                    "total_detected": 0
                },
                "payment_handler": {
                    "enabled": True,
                    "last_check": None,
                    "total_detected": 0
                },
                "bank_transfer": {
                    "enabled": False,  # Manual entry only
                    "last_check": None,
                    "total_detected": 0
                },
                "test_injection": {
                    "enabled": True,  # For development
                    "last_check": None,
                    "total_detected": 0
                }
            },
            "total_injected": 0.0,
            "injection_history": [],
            "last_check": None
        }

        self._save_state(default)
        return default

    def _save_state(self, state: Optional[Dict] = None):
        """Save monitor state."""
        if state is None:
            state = self.state

        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_DIR.mkdir(parents=True, exist_ok=True)

        with open(MONITOR_STATE, 'w') as f:
            json.dump(state, f, indent=2)

    def check_all_sources(self) -> Dict:
        """
        Check all enabled capital sources for new deposits.

        Returns dict with detected amounts per source.
        """
        detected = {}

        # 1. Check payment_handler
        if self.state["sources"]["payment_handler"]["enabled"]:
            amount = self._check_payment_handler()
            if amount > 0:
                detected["payment_handler"] = amount

        # 2. Check crypto wallet (placeholder - needs on-chain integration)
        if self.state["sources"]["crypto_wallet"]["enabled"]:
            amount = self._check_crypto_wallet()
            if amount > 0:
                detected["crypto_wallet"] = amount

        # Update last check
        self.state["last_check"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        return detected

    def _check_payment_handler(self) -> float:
        """
        Check payment_handler for new payments since last check.

        Returns total new payment amount.
        """
        payment_state_file = STATE_DIR / "payment_handler.json"
        if not payment_state_file.exists():
            return 0.0

        try:
            with open(payment_state_file) as f:
                payment_state = json.load(f)

            last_check = self.state["sources"]["payment_handler"]["last_check"]
            payment_history = payment_state.get("payment_history", [])

            # Get payments since last check
            new_payments = []
            for payment in payment_history:
                received_at = payment.get("received_at")
                if not received_at:
                    continue

                # If first check or payment is after last check
                if not last_check or received_at > last_check:
                    new_payments.append(payment)

            total = sum(p.get("amount", 0) for p in new_payments)

            # Update last check
            self.state["sources"]["payment_handler"]["last_check"] = datetime.now(timezone.utc).isoformat()
            self.state["sources"]["payment_handler"]["total_detected"] += len(new_payments)

            return total

        except Exception as e:
            print(f"Error checking payment_handler: {e}")
            return 0.0

    def _check_crypto_wallet(self) -> float:
        """
        Check crypto wallet for new deposits (placeholder).

        TODO: Integrate with on-chain monitoring (Etherscan API, etc.)
        """
        # Placeholder - would query blockchain for deposits to wallet address
        return 0.0

    def inject_detected(self, detected: Dict) -> List[Dict]:
        """
        Inject all detected capital into capital_bridge.

        Returns list of injection results.
        """
        results = []

        for source, amount in detected.items():
            if amount <= 0:
                continue

            try:
                # Import here to avoid circular dependency
                import sys
                sys.path.insert(0, str(PROJECT_ROOT))
                from integrafix.capital_bridge import CapitalBridge

                bridge = CapitalBridge()
                result = bridge.inject_capital(
                    amount=amount,
                    source=f"auto_detected_{source}",
                    notes=f"Auto-detected from {source} by capital_monitor"
                )

                # Record injection
                injection = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": source,
                    "amount": amount,
                    "bridge_result": result
                }

                self.state["injection_history"].append(injection)
                self.state["total_injected"] += amount

                results.append({
                    "source": source,
                    "amount": amount,
                    "status": "success",
                    "bridge_result": result
                })

                print(f"✓ Injected ${amount:.2f} from {source}")

                # Check if activation threshold met
                activation = bridge.check_activation_ready()
                if activation["ready"] and not bridge.state.get("live_mode_active"):
                    print(f"🚀 Activation threshold met! Triggering flip_to_live()...")
                    live_result = bridge.flip_to_live()
                    if live_result:
                        print(f"✓ LIVE MODE ACTIVATED")
                    else:
                        print(f"⚠ Live mode activation failed")

            except Exception as e:
                results.append({
                    "source": source,
                    "amount": amount,
                    "status": "error",
                    "error": str(e)
                })
                print(f"✗ Failed to inject ${amount:.2f} from {source}: {e}")

        self._save_state()
        return results

    def manual_inject(self, amount: float, source: str, notes: str = "") -> Dict:
        """
        Manually inject capital (e.g., bank transfer, cash deposit).

        This allows human to record capital that can't be auto-detected.
        """
        try:
            import sys
            sys.path.insert(0, str(PROJECT_ROOT))
            from integrafix.capital_bridge import CapitalBridge

            bridge = CapitalBridge()
            result = bridge.inject_capital(
                amount=amount,
                source=f"manual_{source}",
                notes=notes
            )

            # Record injection
            injection = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": f"manual_{source}",
                "amount": amount,
                "notes": notes,
                "bridge_result": result
            }

            self.state["injection_history"].append(injection)
            self.state["total_injected"] += amount
            self._save_state()

            print(f"✓ Manual injection: ${amount:.2f} from {source}")

            # Check activation
            activation = bridge.check_activation_ready()
            if activation["ready"]:
                print(f"🚀 Ready to activate LIVE mode!")

            return {
                "status": "success",
                "amount": amount,
                "source": source,
                "bridge_result": result,
                "activation_ready": activation["ready"]
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_status(self) -> Dict:
        """Get capital monitor status."""
        # Get capital_bridge status
        try:
            import sys
            sys.path.insert(0, str(PROJECT_ROOT))
            from integrafix.capital_bridge import CapitalBridge

            bridge = CapitalBridge()
            bridge_status = bridge.check_activation_ready()
        except:
            bridge_status = {}

        return {
            "total_injected": self.state["total_injected"],
            "injection_count": len(self.state["injection_history"]),
            "sources_enabled": sum(
                1 for s in self.state["sources"].values() if s.get("enabled")
            ),
            "last_check": self.state.get("last_check"),
            "capital_bridge": bridge_status,
            "recent_injections": self.state["injection_history"][-5:]
        }


# CLI interface
if __name__ == "__main__":
    import sys

    monitor = CapitalMonitor()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "check":
            print("Checking all capital sources...")
            detected = monitor.check_all_sources()
            if detected:
                print(f"Detected: {detected}")
                results = monitor.inject_detected(detected)
                print(f"Injection results: {results}")
            else:
                print("No new capital detected")

        elif cmd == "status":
            status = monitor.get_status()
            print(json.dumps(status, indent=2))

        elif cmd == "inject" and len(sys.argv) >= 4:
            amount = float(sys.argv[2])
            source = sys.argv[3]
            notes = sys.argv[4] if len(sys.argv) > 4 else ""
            result = monitor.manual_inject(amount, source, notes)
            print(json.dumps(result, indent=2))

        else:
            print("Usage:")
            print("  python capital_monitor.py check          - Check all sources")
            print("  python capital_monitor.py status         - Show status")
            print("  python capital_monitor.py inject <amount> <source> [notes]")
    else:
        status = monitor.get_status()
        print(json.dumps(status, indent=2))
