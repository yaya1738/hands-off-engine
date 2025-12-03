#!/usr/bin/env python3
"""
Wallet Flow Coordinator - Cross-Wallet Fund Management
Move funds between wallets, coordinate capital allocation.

CAPABILITIES:
- Transfer USDC between wallets (Polygon)
- Rebalance capital across wallet fleet
- Coordinate order positions
- Merge operations across wallets

Serving: Yair Siegel
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
import time

# Web3 for Polygon transfers
try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"

# Polygon mainnet
POLYGON_RPC = "https://polygon-rpc.com"
POLYGON_CHAIN_ID = 137

# USDC on Polygon
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC.e on Polygon
USDC_DECIMALS = 6

# ERC20 ABI for transfers
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


@dataclass
class TransferRecord:
    """Record of fund transfer."""
    from_wallet: str
    to_wallet: str
    amount_usdc: float
    tx_hash: str
    status: str
    timestamp: str
    gas_used: int = 0


class WalletFlowCoordinator:
    """
    Coordinate fund flows between Polymarket wallets.

    Enables capital rebalancing across wallet fleet.
    """

    def __init__(self):
        self.wallets: Dict[str, Dict] = {}
        self.web3 = None
        self.usdc_contract = None
        self.transfer_history: List[TransferRecord] = []
        self._init_web3()
        self._load_wallets()

    def _init_web3(self):
        """Initialize Web3 for Polygon."""
        if not WEB3_AVAILABLE:
            print("Web3 not available - install with: pip install web3")
            return

        try:
            self.web3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
            if self.web3.is_connected():
                self.usdc_contract = self.web3.eth.contract(
                    address=Web3.to_checksum_address(USDC_ADDRESS),
                    abi=ERC20_ABI
                )
        except Exception as e:
            print(f"Web3 init error: {e}")

    def _load_wallets(self):
        """Load wallets from registry."""
        registry_path = STATE_DIR / "wallets" / "registry.json"
        if registry_path.exists():
            with open(registry_path) as f:
                registry = json.load(f)
            self.wallets = registry.get("wallets", {})

    def add_wallet(self, address: str, private_key: str, alias: str = None):
        """Add wallet to coordinator."""
        self.wallets[address] = {
            "address": address,
            "private_key": private_key,
            "alias": alias or address[:10]
        }

    # ==================== BALANCE QUERIES ====================

    def get_usdc_balance(self, address: str) -> float:
        """Get USDC balance for wallet."""
        if not self.web3 or not self.usdc_contract:
            return 0.0

        try:
            balance_wei = self.usdc_contract.functions.balanceOf(
                Web3.to_checksum_address(address)
            ).call()
            return balance_wei / (10 ** USDC_DECIMALS)
        except Exception as e:
            print(f"Error getting balance for {address[:10]}...: {e}")
            return 0.0

    def get_matic_balance(self, address: str) -> float:
        """Get MATIC balance for gas."""
        if not self.web3:
            return 0.0

        try:
            balance_wei = self.web3.eth.get_balance(
                Web3.to_checksum_address(address)
            )
            return self.web3.from_wei(balance_wei, 'ether')
        except Exception as e:
            print(f"Error getting MATIC balance: {e}")
            return 0.0

    def get_all_balances(self) -> Dict[str, Dict]:
        """Get balances for all wallets."""
        balances = {}

        def get_balance(addr):
            return addr, {
                "usdc": self.get_usdc_balance(addr),
                "matic": self.get_matic_balance(addr),
                "alias": self.wallets.get(addr, {}).get("alias", addr[:10])
            }

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_balance, addr) for addr in self.wallets]
            for future in as_completed(futures):
                addr, balance = future.result()
                balances[addr] = balance

        return balances

    # ==================== TRANSFERS ====================

    def transfer_usdc(
        self,
        from_address: str,
        to_address: str,
        amount_usdc: float,
        max_gas_gwei: float = 100
    ) -> TransferRecord:
        """
        Transfer USDC between wallets on Polygon.
        """
        record = TransferRecord(
            from_wallet=from_address,
            to_wallet=to_address,
            amount_usdc=amount_usdc,
            tx_hash="",
            status="pending",
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        if not self.web3 or not self.usdc_contract:
            record.status = "failed"
            record.tx_hash = "Web3 not initialized"
            return record

        from_wallet = self.wallets.get(from_address)
        if not from_wallet:
            record.status = "failed"
            record.tx_hash = "From wallet not found"
            return record

        try:
            # Check balance
            current_balance = self.get_usdc_balance(from_address)
            if current_balance < amount_usdc:
                record.status = "failed"
                record.tx_hash = f"Insufficient balance: {current_balance} < {amount_usdc}"
                return record

            # Convert to wei
            amount_wei = int(amount_usdc * (10 ** USDC_DECIMALS))

            # Build transaction
            account = Account.from_key(from_wallet["private_key"])
            nonce = self.web3.eth.get_transaction_count(
                Web3.to_checksum_address(from_address)
            )

            # Get gas price
            gas_price = self.web3.eth.gas_price
            max_gas_wei = self.web3.to_wei(max_gas_gwei, 'gwei')
            if gas_price > max_gas_wei:
                record.status = "failed"
                record.tx_hash = f"Gas too high: {self.web3.from_wei(gas_price, 'gwei')} gwei"
                return record

            # Build transfer
            tx = self.usdc_contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                'chainId': POLYGON_CHAIN_ID,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            # Sign and send
            signed_tx = self.web3.eth.account.sign_transaction(tx, from_wallet["private_key"])
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            record.tx_hash = tx_hash.hex()
            record.status = "submitted"

            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            record.gas_used = receipt['gasUsed']

            if receipt['status'] == 1:
                record.status = "confirmed"
            else:
                record.status = "failed"

        except Exception as e:
            record.status = "error"
            record.tx_hash = str(e)

        self.transfer_history.append(record)
        return record

    # ==================== REBALANCING ====================

    def calculate_rebalance(
        self,
        target_distribution: str = "equal"
    ) -> List[Tuple[str, str, float]]:
        """
        Calculate transfers needed to rebalance capital.

        Returns list of (from, to, amount) transfers.
        """
        balances = self.get_all_balances()

        if not balances:
            return []

        total_usdc = sum(b["usdc"] for b in balances.values())
        wallet_count = len(balances)

        if wallet_count == 0 or total_usdc == 0:
            return []

        if target_distribution == "equal":
            target_per_wallet = total_usdc / wallet_count
        else:
            target_per_wallet = total_usdc / wallet_count

        # Find surplus and deficit wallets
        surplus = []  # (address, excess_amount)
        deficit = []  # (address, needed_amount)

        for addr, bal in balances.items():
            diff = bal["usdc"] - target_per_wallet
            if diff > 1:  # More than $1 surplus
                surplus.append((addr, diff))
            elif diff < -1:  # More than $1 deficit
                deficit.append((addr, abs(diff)))

        # Match surplus to deficit
        transfers = []
        surplus = sorted(surplus, key=lambda x: x[1], reverse=True)
        deficit = sorted(deficit, key=lambda x: x[1], reverse=True)

        for def_addr, def_amount in deficit:
            remaining_need = def_amount

            for i, (sur_addr, sur_amount) in enumerate(surplus):
                if remaining_need <= 0 or sur_amount <= 0:
                    continue

                transfer_amount = min(remaining_need, sur_amount)
                if transfer_amount > 1:  # Only transfer if > $1
                    transfers.append((sur_addr, def_addr, transfer_amount))
                    remaining_need -= transfer_amount
                    surplus[i] = (sur_addr, sur_amount - transfer_amount)

        return transfers

    def execute_rebalance(
        self,
        transfers: List[Tuple[str, str, float]] = None,
        dry_run: bool = True
    ) -> List[TransferRecord]:
        """Execute rebalancing transfers."""
        if transfers is None:
            transfers = self.calculate_rebalance()

        results = []

        for from_addr, to_addr, amount in transfers:
            if dry_run:
                record = TransferRecord(
                    from_wallet=from_addr,
                    to_wallet=to_addr,
                    amount_usdc=amount,
                    tx_hash="DRY_RUN",
                    status="simulated",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            else:
                record = self.transfer_usdc(from_addr, to_addr, amount)

            results.append(record)
            print(f"  Transfer: ${amount:.2f} from {from_addr[:10]}... to {to_addr[:10]}... [{record.status}]")

        return results

    # ==================== POLYMARKET INTEGRATION ====================

    def get_polymarket_working_capital(self, address: str) -> float:
        """Get working capital in Polymarket orders for wallet."""
        try:
            from py_clob_client.client import ClobClient

            wallet = self.wallets.get(address)
            if not wallet:
                return 0.0

            client = ClobClient(
                "https://clob.polymarket.com",
                key=wallet["private_key"],
                chain_id=137,
                funder=address
            )
            creds = client.create_or_derive_api_creds()
            client.set_api_creds(creds)

            orders = client.get_orders() or []
            working = sum(
                float(o.get("price", 0)) * float(o.get("original_size", o.get("size", 0)))
                for o in orders
            )
            return working

        except Exception as e:
            print(f"Error getting Polymarket capital for {address[:10]}...: {e}")
            return 0.0

    def get_full_capital_view(self) -> Dict:
        """Get complete capital view across all wallets."""
        view = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wallets": {},
            "totals": {
                "usdc_balance": 0,
                "matic_balance": 0,
                "polymarket_working": 0,
                "total_capital": 0
            }
        }

        for addr in self.wallets:
            usdc = self.get_usdc_balance(addr)
            matic = self.get_matic_balance(addr)
            poly_working = self.get_polymarket_working_capital(addr)

            wallet_view = {
                "alias": self.wallets[addr].get("alias", addr[:10]),
                "usdc_balance": usdc,
                "matic_balance": matic,
                "polymarket_working": poly_working,
                "total": usdc + poly_working
            }

            view["wallets"][addr] = wallet_view
            view["totals"]["usdc_balance"] += usdc
            view["totals"]["matic_balance"] += matic
            view["totals"]["polymarket_working"] += poly_working
            view["totals"]["total_capital"] += wallet_view["total"]

        return view

    # ==================== DEMO ====================

    def run_demo(self):
        """Demo wallet flow coordination."""
        print("=" * 70)
        print("WALLET FLOW COORDINATOR - Cross-Wallet Fund Management")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[INFRASTRUCTURE]")
        print(f"  Web3 available: {WEB3_AVAILABLE}")
        print(f"  Web3 connected: {self.web3.is_connected() if self.web3 else False}")
        print(f"  Polygon RPC: {POLYGON_RPC}")
        print(f"  USDC contract: {USDC_ADDRESS[:20]}...")
        print()

        print("[REGISTERED WALLETS]")
        for addr, data in self.wallets.items():
            alias = data.get("alias", addr[:10])
            print(f"  {alias}: {addr[:20]}...")
        print(f"  Total: {len(self.wallets)} wallets")
        print()

        if not self.wallets:
            print("[NO WALLETS] Run multi_wallet_manager.py first")
            return

        print("[CAPABILITIES]")
        print("  get_all_balances()      - USDC + MATIC for all wallets")
        print("  transfer_usdc()         - Move USDC between wallets")
        print("  calculate_rebalance()   - Plan rebalancing transfers")
        print("  execute_rebalance()     - Execute rebalancing")
        print("  get_full_capital_view() - Complete capital overview")
        print()

        if self.web3 and self.web3.is_connected():
            print("[BALANCE CHECK]")
            balances = self.get_all_balances()
            total_usdc = 0
            total_matic = 0

            for addr, bal in balances.items():
                alias = bal.get("alias", addr[:10])
                usdc = bal.get("usdc", 0)
                matic = bal.get("matic", 0)
                total_usdc += usdc
                total_matic += matic
                print(f"  {alias}: ${usdc:.2f} USDC, {matic:.4f} MATIC")

            print(f"  ----------------")
            print(f"  TOTAL: ${total_usdc:.2f} USDC, {total_matic:.4f} MATIC")
            print()

            # Rebalance calculation
            if len(self.wallets) > 1:
                print("[REBALANCE CALCULATION]")
                transfers = self.calculate_rebalance()
                if transfers:
                    print(f"  Transfers needed: {len(transfers)}")
                    for from_addr, to_addr, amount in transfers[:5]:
                        from_alias = self.wallets.get(from_addr, {}).get("alias", from_addr[:10])
                        to_alias = self.wallets.get(to_addr, {}).get("alias", to_addr[:10])
                        print(f"    ${amount:.2f}: {from_alias} → {to_alias}")
                else:
                    print("  Already balanced!")
                print()

        print("=" * 70)
        print("FUND FLOW COORDINATION READY")
        print("=" * 70)


def main():
    coordinator = WalletFlowCoordinator()
    coordinator.run_demo()
    return coordinator


if __name__ == "__main__":
    main()
