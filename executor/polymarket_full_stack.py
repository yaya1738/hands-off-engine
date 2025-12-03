#!/usr/bin/env python3
"""
Polymarket Full Stack - Unified API for Complete Trading Infrastructure

Combines:
- Wallet Factory (create fully onboarded accounts)
- Auto-Scaler (scale wallets based on frequency demands)
- HFT Agent API (trading operations)
- Fleet Management (coordinate multiple wallets)

ONE IMPORT FOR EVERYTHING:
    from executor.polymarket_full_stack import poly

    # Create trading wallet
    poly.create_wallet(usdc=100)

    # Scale to frequency
    poly.scale_to_frequency(100000)  # 100k orders/sec

    # Trade
    poly.fire(token_id, count=1000)

    # Status
    poly.status()

Serving: Yair Siegel
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class PolymarketFullStack:
    """
    Unified API for complete Polymarket trading infrastructure.

    Combines wallet creation, scaling, and trading into one interface.
    All trading is GASLESS - gas only needed for initial setup.
    """

    def __init__(self):
        self._factory = None
        self._scaler = None
        self._hft = None
        self._wallet_manager = None
        self._gasless = None

    # ==================== LAZY LOADING ====================

    @property
    def factory(self):
        """Wallet factory for creating/onboarding accounts."""
        if not self._factory:
            from executor.polymarket_wallet_factory import factory
            self._factory = factory
        return self._factory

    @property
    def scaler(self):
        """Auto-scaler for frequency-based scaling."""
        if not self._scaler:
            from executor.hft_auto_scaler import scaler
            self._scaler = scaler
        return self._scaler

    @property
    def hft(self):
        """HFT API for trading operations."""
        if not self._hft:
            from executor.hft_agent_api import hft
            self._hft = hft
        return self._hft

    @property
    def wallet_manager(self):
        """Wallet manager for fleet operations."""
        if not self._wallet_manager:
            from executor.multi_wallet_manager import MultiWalletManager
            self._wallet_manager = MultiWalletManager()
        return self._wallet_manager

    @property
    def gasless(self):
        """Gasless wallet manager for zero-gas trading."""
        if not self._gasless:
            from executor.gasless_wallet_manager import gasless
            self._gasless = gasless
        return self._gasless

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """
        Complete system status.

        Returns everything you need to know about the trading infrastructure.
        """
        # HFT status
        hft_status = self.hft.status()

        # Scaler status
        scaler_status = self.scaler.status()

        # Master wallet
        master = self.factory.get_master_balances()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),

            # Fleet
            "wallets": {
                "total": hft_status["wallets"]["total"],
                "active": hft_status["wallets"]["active"],
                "master_usdc": master.get("usdc", 0),
                "master_matic": master.get("matic", 0)
            },

            # Capacity
            "capacity": {
                "current": scaler_status["current_capacity"],
                "target": scaler_status["target_frequency"],
                "utilization": scaler_status["utilization"],
                "rate_per_wallet": scaler_status["config"]["rate_per_wallet"]
            },

            # Trading
            "orders": {
                "open": hft_status["orders"]["total"],
                "working_capital": hft_status["orders"]["working_capital"]
            },

            # Ready status
            "ready": hft_status["ready"],
            "can_create_wallets": master.get("usdc", 0) > 50 and master.get("matic", 0) > 0.1
        }

    def quick_status(self) -> str:
        """One-line status."""
        s = self.status()
        return f"Poly: {s['wallets']['active']} wallets, {s['capacity']['current']:,}/sec capacity, ${s['orders']['working_capital']:.2f} working"

    # ==================== WALLET CREATION ====================

    def create_wallet(self, usdc: float = 100, matic: float = 0.1,
                      alias: str = None) -> Dict:
        """
        Create one FULLY ONBOARDED trading wallet.

        Complete flow:
        1. Generate keypair
        2. Fund with MATIC (gas)
        3. Fund with USDC (capital)
        4. Set Polymarket allowances
        5. Derive API credentials
        6. Register in fleet

        Args:
            usdc: Trading capital (default $100)
            matic: Gas funds (default 0.1 MATIC)
            alias: Wallet name

        Returns:
            {"address": "0x...", "status": "active", "usdc": float}
        """
        wallet = self.factory.create_trading_wallet(usdc, matic, alias)

        return {
            "address": wallet.address,
            "alias": wallet.alias,
            "status": wallet.status,
            "usdc": wallet.usdc_balance,
            "matic": wallet.matic_balance,
            "allowances_set": wallet.allowances_set,
            "api_creds_derived": wallet.api_creds_derived,
            "ready_to_trade": wallet.status == "active"
        }

    def create_fleet(self, count: int, usdc_per_wallet: float = 50) -> Dict:
        """
        Create multiple fully onboarded trading wallets.

        Args:
            count: Number of wallets
            usdc_per_wallet: USDC per wallet

        Returns:
            {"created": N, "successful": N, "wallets": [...]}
        """
        wallets = self.factory.create_trading_fleet(count, usdc_per_wallet)

        return {
            "created": len(wallets),
            "successful": sum(1 for w in wallets if w.status == "active"),
            "total_usdc": sum(w.usdc_balance for w in wallets),
            "wallets": [
                {"address": w.address[:20] + "...", "alias": w.alias, "status": w.status}
                for w in wallets
            ]
        }

    def onboard_wallet(self, private_key: str, fund_usdc: float = 0) -> Dict:
        """
        Onboard an existing wallet (set allowances, derive creds).

        Args:
            private_key: Wallet private key
            fund_usdc: Optional USDC to add

        Returns:
            {"address": "0x...", "status": "active"}
        """
        wallet = self.factory.onboard_existing_wallet(private_key, fund_usdc)

        return {
            "address": wallet.address,
            "alias": wallet.alias,
            "status": wallet.status,
            "usdc": wallet.usdc_balance,
            "ready_to_trade": wallet.status == "active"
        }

    # ==================== SCALING ====================

    def scale_to_frequency(self, orders_per_second: int,
                           create_funded_wallets: bool = False,
                           usdc_per_wallet: float = 50) -> Dict:
        """
        Scale infrastructure to handle target frequency.

        Args:
            orders_per_second: Target orders/sec
            create_funded_wallets: If True, creates FUNDED wallets (costs USDC)
                                   If False, creates basic wallets (no funding)
            usdc_per_wallet: USDC per wallet if creating funded wallets

        Returns:
            {"target": N, "current_capacity": N, "wallets_created": N}
        """
        # Calculate wallets needed
        needed = self.scaler.wallets_needed_for(orders_per_second)
        current = self.hft.wallet_count()
        to_create = max(0, needed - current)

        if to_create == 0:
            return {
                "target": orders_per_second,
                "current_capacity": current * 1000,
                "wallets_needed": needed,
                "wallets_current": current,
                "action": "none_needed"
            }

        if create_funded_wallets:
            # Create fully funded wallets (costs USDC + MATIC)
            wallets = self.create_fleet(to_create, usdc_per_wallet)
            created = wallets["successful"]
        else:
            # Create basic wallets (no funding - for HFT signing only)
            result = self.hft.create_wallets(to_create, "scale")
            created = result.get("created", 0)

        # Update scaler target
        self.scaler.set_target_frequency(orders_per_second)

        new_capacity = self.hft.wallet_count() * 1000

        return {
            "target": orders_per_second,
            "wallets_needed": needed,
            "wallets_created": created,
            "new_wallet_count": self.hft.wallet_count(),
            "new_capacity": new_capacity,
            "target_met": new_capacity >= orders_per_second,
            "funded": create_funded_wallets
        }

    def ensure_capacity(self, min_orders_per_second: int) -> Dict:
        """
        Ensure at least this much capacity exists.

        Creates unfunded wallets if needed (for HFT signing).
        """
        current = self.scaler.get_current_capacity()

        if current["current_capacity"] >= min_orders_per_second:
            return {
                "action": "none_needed",
                "current_capacity": current["current_capacity"],
                "requested": min_orders_per_second
            }

        return self.scale_to_frequency(min_orders_per_second, create_funded_wallets=False)

    # ==================== TRADING ====================

    def fire(self, token_id: str, count: int = 100) -> Dict:
        """Fire orders at maximum speed."""
        return self.hft.fire(token_id, count)

    def place_order(self, token_id: str, price: float,
                    size: float, side: str) -> Dict:
        """Place single order."""
        return self.hft.place_order(token_id, price, size, side)

    def place_grid(self, token_id: str, center_price: float,
                   spread_bps: int = 100, levels: int = 5,
                   size: float = 10) -> Dict:
        """Place order grid around price."""
        return self.hft.place_grid(token_id, center_price, spread_bps, levels, size)

    def cancel_all(self) -> Dict:
        """Cancel all orders on all wallets."""
        return self.hft.cancel_all()

    def market_maker(self, token_id: str, center_price: float = None) -> Dict:
        """Quick market maker: cancel all and place new grid."""
        return self.hft.market_maker(token_id, center_price)

    # ==================== WALLET MANAGEMENT ====================

    def list_wallets(self) -> List[Dict]:
        """List all wallets."""
        return self.hft.list_wallets()

    def wallet_count(self) -> int:
        """Active wallet count."""
        return self.hft.wallet_count()

    def check_wallet(self, address: str) -> Dict:
        """Check wallet readiness."""
        return self.factory.get_wallet_status(address)

    def fund_wallet(self, address: str, usdc: float, matic: float = 0) -> Dict:
        """Fund a wallet with USDC and optionally MATIC."""
        results = {}

        if matic > 0:
            results["matic"] = self.factory.fund_with_matic(address, matic)

        results["usdc"] = self.factory.fund_with_usdc(address, usdc)

        return results

    # ==================== BENCHMARKING ====================

    def benchmark(self) -> Dict:
        """Run throughput benchmark."""
        return self.hft.benchmark()

    # ==================== GASLESS OPERATIONS ====================

    def is_gasless_ready(self, address: str) -> bool:
        """Check if wallet is ready for gasless trading."""
        return self.gasless.check_gasless_ready(address)["gasless_ready"]

    def setup_gasless(self, private_key: str) -> Dict:
        """
        Setup wallet for gasless trading.

        Sets allowances (one-time ~0.02 MATIC), then trading is free forever.

        Args:
            private_key: Wallet private key

        Returns:
            {"success": bool, "gasless_ready": bool}
        """
        return self.gasless.setup_for_gasless_trading(private_key)

    def create_gasless_wallet(self, usdc: float = 0, alias: str = None) -> Dict:
        """
        Create a fully gasless-ready trading wallet.

        Complete flow:
        1. Generate wallet
        2. Fund MATIC for setup (~0.03)
        3. Set all allowances
        4. Optionally fund USDC
        5. Ready for gasless trading

        Args:
            usdc: USDC to fund (0 for signing-only)
            alias: Wallet name

        Returns:
            {"wallet": {...}, "config": {...}, "ready": bool}
        """
        result = self.gasless.create_gasless_hft_wallet(usdc, alias)
        return {
            "address": result["wallet"].address,
            "alias": result["wallet"].address[:10] + "...",
            "mode": result["wallet"].mode.value,
            "gasless_ready": result["ready"],
            "config": result["config"]
        }

    def create_gasless_fleet(self, count: int, usdc_per: float = 0) -> Dict:
        """
        Create fleet of gasless-ready trading wallets.

        Args:
            count: Number of wallets
            usdc_per: USDC per wallet (0 for signing-only)

        Returns:
            {"created": N, "successful": N}
        """
        wallets = []
        for i in range(count):
            result = self.create_gasless_wallet(usdc_per, f"gasless_{i+1}")
            wallets.append(result)

        return {
            "created": len(wallets),
            "successful": sum(1 for w in wallets if w["gasless_ready"]),
            "wallets": wallets
        }

    def check_gasless_status(self, address: str) -> Dict:
        """
        Detailed gasless status for wallet.

        Returns what's needed (if anything) for gasless trading.
        """
        return self.gasless.check_gasless_ready(address)

    def get_gasless_config(self, address: str) -> Dict:
        """Get HFT config for gasless trading."""
        return self.gasless.get_gasless_hft_config(address)

    # ==================== AUTONOMOUS HOOKS ====================

    def autonomous_check(self) -> Dict:
        """
        Check for autonomous system - what actions are recommended?

        Returns recommendations for scaling, trading, etc.
        """
        status = self.status()
        recommendations = []

        # Check wallet count
        if status["wallets"]["active"] < 10:
            recommendations.append({
                "action": "scale_wallets",
                "reason": "Low wallet count",
                "command": "poly.scale_to_frequency(10000)"
            })

        # Check capacity vs target
        if status["capacity"]["target"] > 0:
            utilization = float(status["capacity"]["utilization"].rstrip("%")) / 100
            if utilization > 0.8:
                recommendations.append({
                    "action": "scale_up",
                    "reason": "High utilization",
                    "command": f"poly.scale_to_frequency({int(status['capacity']['target'] * 1.5)})"
                })

        # Check master wallet for funded wallet creation
        if status["wallets"]["master_usdc"] > 500:
            recommendations.append({
                "action": "create_funded_fleet",
                "reason": "Sufficient funds for new trading wallets",
                "command": f"poly.create_fleet(10, usdc_per_wallet=50)"
            })

        return {
            "status": status,
            "recommendations": recommendations,
            "ready": status["ready"]
        }


# Singleton instance
poly = PolymarketFullStack()


# ==================== CLI ====================

def main():
    import sys

    if len(sys.argv) < 2:
        print("""
Polymarket Full Stack - Unified Trading Infrastructure
======================================================

COMMANDS:
  status              Complete system status
  create [USDC]       Create one funded trading wallet
  fleet N [USDC]      Create N funded trading wallets
  scale FREQ [funded] Scale to handle FREQ orders/sec
  fire TOKEN [N]      Fire N orders at token
  benchmark           Run throughput benchmark
  check               Autonomous system check

EXAMPLES:
  python polymarket_full_stack.py status
  python polymarket_full_stack.py create 200
  python polymarket_full_stack.py scale 100000
  python polymarket_full_stack.py scale 100000 funded
""")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(poly.status(), indent=2))

    elif cmd == "create":
        usdc = float(sys.argv[2]) if len(sys.argv) > 2 else 100
        print(json.dumps(poly.create_wallet(usdc), indent=2))

    elif cmd == "fleet":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        usdc = float(sys.argv[3]) if len(sys.argv) > 3 else 50
        print(json.dumps(poly.create_fleet(count, usdc), indent=2))

    elif cmd == "scale":
        freq = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
        funded = "funded" in sys.argv
        print(json.dumps(poly.scale_to_frequency(freq, create_funded_wallets=funded), indent=2))

    elif cmd == "fire":
        token = sys.argv[2] if len(sys.argv) > 2 else "test"
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        print(json.dumps(poly.fire(token, count), indent=2))

    elif cmd == "benchmark":
        print(json.dumps(poly.benchmark(), indent=2))

    elif cmd == "check":
        print(json.dumps(poly.autonomous_check(), indent=2))

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
