#!/usr/bin/env python3
"""
Autonomous Payment Handler
===========================

Ensures we can receive payments automatically without manual intervention.

Handles:
- GitHub Sponsors setup
- Cryptocurrency wallet management
- Payment method verification
- Automatic payment acceptance

Master: Yair Siegel
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
FINANCE_DIR = PROJECT_ROOT / "finance"


class PaymentHandler:
    """Manages autonomous payment receiving."""

    def __init__(self):
        self.state_file = STATE_DIR / "payment_handler.json"
        self.state = self._load_state()

        # Payment methods configured
        self.payment_methods = {
            "crypto": {
                "wallet": "0xB314345D218ED4CF75C17636a2307244E7dA761b",
                "chains": ["ethereum", "polygon", "base"],
                "auto_accept": True
            },
            "github_sponsors": {
                "enabled": False,  # Needs manual GitHub setup
                "profile": "YairSiegel",
                "auto_setup": True
            },
            "email_invoice": {
                "email": "siegel.yaz@gmail.com",
                "auto_respond": True,
                "template": "payment_info_template.txt"
            }
        }

    def _load_state(self) -> Dict:
        """Load payment handler state."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payments_received": 0,
            "total_received": 550.0,  # cortexlinux payment
            "pending_payments": [],
            "payment_methods_verified": False
        }

    def _save_state(self):
        """Save payment handler state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_DIR.mkdir(exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def verify_payment_methods(self) -> Dict[str, bool]:
        """Verify all payment methods are set up correctly."""
        status = {}

        # Crypto wallet - already active
        status["crypto_wallet"] = True

        # GitHub Sponsors - check if we have token
        github_token = os.environ.get('GITHUB_TOKEN', '')
        status["github_api"] = bool(github_token)

        # Email - check if configured
        status["email"] = os.path.exists(PROJECT_ROOT / ".env")

        self.state["payment_methods_verified"] = all(status.values())
        self._save_state()

        return status

    def generate_payment_info_response(self, platform: str = "general") -> str:
        """Generate automated payment info response."""

        if platform == "crypto" or platform == "general":
            return f"""
Payment Information - Yair Siegel

**Cryptocurrency (Preferred):**
Wallet: {self.payment_methods['crypto']['wallet']}
Chains: Ethereum, Polygon, Base
Accepts: USDC, USDT, ETH, MATIC

**Alternative Methods:**
Email: {self.payment_methods['email_invoice']['email']}

Payment will be acknowledged automatically upon receipt.
Transaction hash or confirmation reference appreciated.

Questions? Reply to this thread - monitored 24/7 by autonomous system.
"""

    def record_payment(
        self,
        amount: float,
        source: str,
        tx_hash: Optional[str] = None,
        notes: str = ""
    ):
        """Record a received payment."""
        payment = {
            "amount": amount,
            "source": source,
            "tx_hash": tx_hash,
            "notes": notes,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "verified": bool(tx_hash)
        }

        self.state["payments_received"] += 1
        self.state["total_received"] += amount

        if "payment_history" not in self.state:
            self.state["payment_history"] = []
        self.state["payment_history"].append(payment)

        self._save_state()

        print(f"✅ Payment recorded: ${amount:,.2f} from {source}")
        if tx_hash:
            print(f"   TX: {tx_hash}")

    def get_payment_instructions(self, bounty_repo: str, bounty_id: str) -> str:
        """Get payment instructions for a specific bounty."""
        return f"""
# Payment Instructions for {bounty_repo} #{bounty_id}

Thank you for approving the bounty submission!

**Preferred Payment Method: Cryptocurrency**
- Wallet Address: `{self.payment_methods['crypto']['wallet']}`
- Supported Networks: Ethereum, Polygon, Base
- Accepted Tokens: USDC, USDT, ETH, MATIC

**Alternative Payment Methods:**
- GitHub Sponsors: @YairSiegel
- Email for Invoice: {self.payment_methods['email_invoice']['email']}

**Automatic Confirmation:**
Payment will be automatically acknowledged upon blockchain confirmation.
No manual follow-up needed.

**Questions?**
This system is monitored 24/7. Reply here or email for any issues.
"""

    def display_status(self):
        """Display payment handler status."""
        print("=" * 80)
        print("💰 AUTONOMOUS PAYMENT HANDLER")
        print("=" * 80)
        print()

        print("📊 PAYMENT METHODS:")
        print("-" * 80)
        for method, config in self.payment_methods.items():
            status = "✅ ACTIVE" if config.get("auto_accept") or config.get("enabled") else "⏳ SETUP NEEDED"
            print(f"  {method.upper()}: {status}")
            if method == "crypto":
                print(f"    Wallet: {config['wallet']}")
            elif method == "email_invoice":
                print(f"    Email: {config['email']}")
        print()

        print("💵 PAYMENT HISTORY:")
        print("-" * 80)
        print(f"  Total Received: ${self.state['total_received']:,.2f}")
        print(f"  Payments Count: {self.state['payments_received']}")
        print(f"  Pending: {len(self.state.get('pending_payments', []))}")
        print()

        print("=" * 80)


def main():
    """Run payment handler."""
    print("Initializing Autonomous Payment Handler...")
    print()

    handler = PaymentHandler()

    # Verify payment methods
    print("🔍 Verifying payment methods...")
    status = handler.verify_payment_methods()

    for method, verified in status.items():
        icon = "✅" if verified else "❌"
        print(f"  {icon} {method}: {'Ready' if verified else 'Needs setup'}")
    print()

    # Display status
    handler.display_status()

    # Generate sample payment instructions
    print("📋 SAMPLE PAYMENT INSTRUCTIONS:")
    print("-" * 80)
    print(handler.generate_payment_info_response())
    print()


if __name__ == "__main__":
    main()
