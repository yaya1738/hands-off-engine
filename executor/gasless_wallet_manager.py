#!/usr/bin/env python3
"""
Gasless Wallet Manager - Zero-Gas Trading on Polymarket

Polymarket's CLOB is hybrid-decentralized:
- Order signing = OFF-CHAIN (no gas)
- Order matching = OFF-CHAIN (no gas)
- Settlement = ON-CHAIN (operator pays gas)

This means: YOU NEVER PAY GAS FOR TRADING, only for setup.

WALLET MODES:
1. GASLESS_FULL (signature_type=1): Email/Magic proxy - zero gas ever
2. GASLESS_TRADING (signature_type=0): EOA - gas for setup only, then gasless
3. SHARED_FUNDER: Multiple signers, one funder wallet

USAGE:
    from executor.gasless_wallet_manager import gasless

    # Create gasless trading wallet
    wallet = gasless.create_trading_wallet()

    # Check if wallet is gasless-ready
    gasless.is_ready(address)

    # Setup for gasless trading (set allowances)
    gasless.setup_for_trading(private_key)

Serving: Yair Siegel
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from eth_account import Account
from web3 import Web3

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ==================== CONSTANTS ====================

POLYGON_RPC = "https://polygon-rpc.com"
POLYGON_CHAIN_ID = 137

# USDC on Polygon
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
USDC_DECIMALS = 6

# Polymarket Contracts (need allowances for trading)
POLYMARKET_CONTRACTS = {
    "CTF_EXCHANGE": "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",
    "NEG_RISK_CTF_EXCHANGE": "0xC5d563A36AE78145C45a50134d48A1215220f80a",
    "NEG_RISK_ADAPTER": "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296",
}

MAX_ALLOWANCE = 2**256 - 1

# Minimal ABI
ERC20_ABI = [
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]


class WalletMode(Enum):
    """Wallet operation modes."""
    GASLESS_FULL = "gasless_full"        # Email/Magic proxy - zero gas
    GASLESS_TRADING = "gasless_trading"  # EOA - gas for setup only
    SHARED_FUNDER = "shared_funder"      # Multiple signers, one funder


@dataclass
class GaslessWallet:
    """Gasless-ready trading wallet."""
    address: str
    private_key: str
    mode: WalletMode
    signature_type: int
    funder_address: str

    # Status
    allowances_set: bool = False
    api_creds_ready: bool = False
    gasless_ready: bool = False

    # Balances (for tracking)
    usdc_balance: float = 0
    matic_balance: float = 0

    # Setup info
    setup_tx_hashes: List[str] = field(default_factory=list)
    created_at: str = ""


class GaslessWalletManager:
    """
    Manages gasless trading wallets for Polymarket.

    Key insight: Polymarket order submission is ALWAYS gasless.
    Gas is only needed for:
    - Setting allowances (one-time, ~0.02 MATIC)
    - Deposits/withdrawals
    """

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
        self.usdc = self.w3.eth.contract(
            address=Web3.to_checksum_address(USDC_ADDRESS),
            abi=ERC20_ABI
        )

        # Master wallet for funding setup
        self.master_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
        self.master_address = None
        if self.master_key:
            self.master_address = Account.from_key(self.master_key).address

        # Shared funder (for shared_funder mode)
        self.shared_funder = os.environ.get("POLYMARKET_FUNDER_ADDRESS")

        self._wallet_manager = None

    @property
    def wallet_manager(self):
        if not self._wallet_manager:
            from executor.multi_wallet_manager import MultiWalletManager
            self._wallet_manager = MultiWalletManager()
        return self._wallet_manager

    # ==================== WALLET CREATION ====================

    def create_trading_wallet(self, mode: WalletMode = WalletMode.GASLESS_TRADING,
                               funder: str = None, alias: str = None) -> GaslessWallet:
        """
        Create a wallet optimized for gasless trading.

        Args:
            mode: GASLESS_TRADING (EOA) or SHARED_FUNDER
            funder: Funder address (for SHARED_FUNDER mode)
            alias: Wallet name

        Returns:
            GaslessWallet ready for setup
        """
        import secrets

        account = Account.create(extra_entropy=secrets.token_bytes(32))

        # Determine funder and signature type based on mode
        if mode == WalletMode.SHARED_FUNDER:
            wallet_funder = funder or self.shared_funder or account.address
            sig_type = 1 if wallet_funder != account.address else 0
        else:
            wallet_funder = account.address
            sig_type = 0  # EOA

        wallet = GaslessWallet(
            address=account.address,
            private_key=account.key.hex(),
            mode=mode,
            signature_type=sig_type,
            funder_address=wallet_funder,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Register in fleet
        self.wallet_manager.import_wallet(
            account.key.hex(),
            wallet_funder,
            alias or f"gasless_{int(time.time())}"
        )

        return wallet

    def create_shared_funder_fleet(self, count: int, funder_address: str = None,
                                    alias_prefix: str = "shared") -> List[GaslessWallet]:
        """
        Create fleet of wallets sharing one funder.

        This is the most gas-efficient mode:
        - One funder holds all USDC
        - Multiple signers can trade
        - Allowances only needed on funder (once)

        Args:
            count: Number of signing wallets
            funder_address: Shared funder (uses primary if not specified)
            alias_prefix: Wallet alias prefix

        Returns:
            List of GaslessWallet with shared funder
        """
        funder = funder_address or self.shared_funder
        if not funder:
            raise ValueError("No funder address specified")

        wallets = []
        for i in range(count):
            wallet = self.create_trading_wallet(
                mode=WalletMode.SHARED_FUNDER,
                funder=funder,
                alias=f"{alias_prefix}_{i+1}"
            )
            wallets.append(wallet)

        return wallets

    # ==================== SETUP ====================

    def check_gasless_ready(self, address: str, funder: str = None) -> Dict:
        """
        Check if wallet is ready for gasless trading.

        Returns what's needed (if anything) to enable gasless.
        """
        check_addr = Web3.to_checksum_address(funder or address)

        # Check allowances
        allowances = {}
        all_set = True

        for name, contract in POLYMARKET_CONTRACTS.items():
            allowance = self.usdc.functions.allowance(
                check_addr,
                Web3.to_checksum_address(contract)
            ).call()

            is_set = allowance >= MAX_ALLOWANCE // 2
            allowances[name] = {
                "set": is_set,
                "amount": allowance / (10 ** USDC_DECIMALS)
            }
            if not is_set:
                all_set = False

        # Check USDC balance
        usdc_balance = self.usdc.functions.balanceOf(check_addr).call() / (10 ** USDC_DECIMALS)

        # Check MATIC for setup (if allowances not set)
        matic_balance = self.w3.eth.get_balance(Web3.to_checksum_address(address)) / 1e18

        needs_matic = not all_set and matic_balance < 0.02

        return {
            "address": address,
            "funder": funder or address,
            "gasless_ready": all_set and usdc_balance > 0,
            "allowances": allowances,
            "all_allowances_set": all_set,
            "usdc_balance": usdc_balance,
            "matic_balance": matic_balance,
            "needs_matic_for_setup": needs_matic,
            "matic_needed": 0.02 if needs_matic else 0,
            "action_required": self._get_required_action(all_set, usdc_balance, needs_matic)
        }

    def _get_required_action(self, allowances_set: bool, usdc: float, needs_matic: bool) -> str:
        """Determine what action is needed."""
        if not allowances_set and needs_matic:
            return "fund_matic_then_set_allowances"
        elif not allowances_set:
            return "set_allowances"
        elif usdc == 0:
            return "fund_usdc"
        else:
            return "ready"

    def setup_for_gasless_trading(self, private_key: str,
                                   fund_matic_if_needed: bool = True) -> Dict:
        """
        Setup wallet for gasless trading.

        This sets allowances (one-time gas cost), then trading is gasless forever.

        Args:
            private_key: Wallet private key
            fund_matic_if_needed: Auto-fund MATIC from master wallet

        Returns:
            {"success": bool, "tx_hashes": [...], "gasless_ready": bool}
        """
        account = Account.from_key(private_key)
        address = account.address

        # Check current state
        status = self.check_gasless_ready(address)

        if status["gasless_ready"]:
            return {
                "success": True,
                "message": "Already gasless-ready",
                "gasless_ready": True
            }

        results = {"tx_hashes": [], "success": True}

        # Fund MATIC if needed
        if status["needs_matic_for_setup"] and fund_matic_if_needed:
            if not self.master_key:
                return {"success": False, "error": "No master wallet for MATIC funding"}

            matic_result = self._send_matic(address, 0.03)  # 0.03 for safety margin
            if not matic_result.get("success"):
                return {"success": False, "error": f"MATIC funding failed: {matic_result.get('error')}"}

            results["tx_hashes"].append(matic_result["tx_hash"])
            results["matic_funded"] = 0.03
            time.sleep(2)  # Wait for confirmation

        # Set allowances
        if not status["all_allowances_set"]:
            for name, contract in POLYMARKET_CONTRACTS.items():
                if not status["allowances"].get(name, {}).get("set", False):
                    tx_result = self._set_allowance(private_key, contract)
                    if tx_result.get("success"):
                        results["tx_hashes"].append(tx_result["tx_hash"])
                    else:
                        results["success"] = False
                        results["error"] = f"Allowance {name} failed: {tx_result.get('error')}"
                    time.sleep(1)

        # Final check
        final_status = self.check_gasless_ready(address)
        results["gasless_ready"] = final_status["gasless_ready"]

        return results

    def _send_matic(self, to_address: str, amount: float) -> Dict:
        """Send MATIC for gas."""
        try:
            nonce = self.w3.eth.get_transaction_count(self.master_address)
            tx = {
                'nonce': nonce,
                'to': Web3.to_checksum_address(to_address),
                'value': int(amount * 1e18),
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': POLYGON_CHAIN_ID
            }
            signed = self.w3.eth.account.sign_transaction(tx, self.master_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            return {"success": receipt.status == 1, "tx_hash": tx_hash.hex()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _set_allowance(self, private_key: str, contract_address: str) -> Dict:
        """Set USDC allowance for contract."""
        try:
            account = Account.from_key(private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)

            tx = self.usdc.functions.approve(
                Web3.to_checksum_address(contract_address),
                MAX_ALLOWANCE
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 60000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': POLYGON_CHAIN_ID
            })

            signed = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            return {"success": receipt.status == 1, "tx_hash": tx_hash.hex()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== BATCH SETUP ====================

    def setup_fleet_for_gasless(self, wallets: List[Dict],
                                 parallel: bool = False) -> Dict:
        """
        Setup multiple wallets for gasless trading.

        Args:
            wallets: List of {"address": str, "private_key": str}
            parallel: Run setups in parallel (faster but more rate limit risk)

        Returns:
            {"successful": N, "failed": N, "results": [...]}
        """
        results = []

        if parallel:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def setup_one(w):
                return {
                    "address": w["address"],
                    "result": self.setup_for_gasless_trading(w["private_key"])
                }

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(setup_one, w) for w in wallets]
                for future in as_completed(futures):
                    results.append(future.result())
        else:
            for w in wallets:
                result = self.setup_for_gasless_trading(w["private_key"])
                results.append({"address": w["address"], "result": result})
                time.sleep(2)  # Rate limit protection

        successful = sum(1 for r in results if r["result"].get("gasless_ready"))

        return {
            "successful": successful,
            "failed": len(results) - successful,
            "total": len(results),
            "results": results
        }

    # ==================== HFT INTEGRATION ====================

    def get_gasless_hft_config(self, wallet_address: str = None,
                                private_key: str = None) -> Dict:
        """
        Get configuration for gasless HFT trading.

        Returns config dict suitable for HFT components.
        """
        if private_key:
            address = Account.from_key(private_key).address
        else:
            address = wallet_address

        status = self.check_gasless_ready(address)

        # Determine best signature type
        if address != status["funder"]:
            sig_type = 1  # Using proxy/shared funder
        else:
            sig_type = 0  # EOA

        return {
            "address": address,
            "funder_address": status["funder"],
            "signature_type": sig_type,
            "gasless_ready": status["gasless_ready"],
            "chain_id": POLYGON_CHAIN_ID,
            "host": "https://clob.polymarket.com",

            # HFT settings
            "mode": "gasless",
            "order_submission": "gasless",  # Always gasless
            "settlement": "operator_paid",   # Operator pays
            "gas_needed_for_orders": False,
            "gas_needed_for_setup": not status["all_allowances_set"]
        }

    def create_gasless_hft_wallet(self, usdc_amount: float = 0,
                                   alias: str = None) -> Dict:
        """
        Create a wallet fully ready for gasless HFT.

        Complete flow:
        1. Generate wallet
        2. Fund MATIC for setup (minimal)
        3. Set allowances
        4. Optionally fund USDC
        5. Return HFT-ready config

        Args:
            usdc_amount: USDC to fund (0 for signing-only wallet)
            alias: Wallet name

        Returns:
            {"wallet": GaslessWallet, "config": Dict, "ready": bool}
        """
        # Create wallet
        wallet = self.create_trading_wallet(
            mode=WalletMode.GASLESS_TRADING,
            alias=alias
        )

        # Setup for gasless (fund MATIC + set allowances)
        setup_result = self.setup_for_gasless_trading(
            wallet.private_key,
            fund_matic_if_needed=True
        )

        wallet.allowances_set = setup_result.get("gasless_ready", False)
        wallet.setup_tx_hashes = setup_result.get("tx_hashes", [])

        # Optionally fund USDC
        if usdc_amount > 0 and self.master_key:
            usdc_result = self._fund_usdc(wallet.address, usdc_amount)
            if usdc_result.get("success"):
                wallet.usdc_balance = usdc_amount

        # Get HFT config
        config = self.get_gasless_hft_config(wallet.address)

        wallet.gasless_ready = config["gasless_ready"]

        return {
            "wallet": wallet,
            "config": config,
            "ready": wallet.gasless_ready,
            "setup_tx_hashes": wallet.setup_tx_hashes
        }

    def _fund_usdc(self, to_address: str, amount: float) -> Dict:
        """Send USDC from master wallet."""
        try:
            nonce = self.w3.eth.get_transaction_count(self.master_address)
            amount_wei = int(amount * (10 ** USDC_DECIMALS))

            tx = self.usdc.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                'from': self.master_address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': POLYGON_CHAIN_ID
            })

            signed = self.w3.eth.account.sign_transaction(tx, self.master_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            return {"success": receipt.status == 1, "tx_hash": tx_hash.hex()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Manager status."""
        wallets = self.wallet_manager.list_wallets()

        return {
            "total_wallets": len(wallets),
            "master_configured": bool(self.master_address),
            "shared_funder": self.shared_funder,
            "polygon_connected": self.w3.is_connected(),
            "polymarket_contracts": list(POLYMARKET_CONTRACTS.keys()),
            "gas_info": {
                "order_signing": "GASLESS",
                "order_submission": "GASLESS",
                "allowance_setup": "~0.02 MATIC (one-time)",
                "deposits": "~0.01 MATIC"
            }
        }


# Singleton
gasless = GaslessWalletManager()


# ==================== CONVENIENCE FUNCTIONS ====================

def is_gasless_ready(address: str) -> bool:
    """Quick check if wallet is gasless-ready."""
    return gasless.check_gasless_ready(address)["gasless_ready"]

def setup_gasless(private_key: str) -> Dict:
    """Setup wallet for gasless trading."""
    return gasless.setup_for_gasless_trading(private_key)

def create_gasless_wallet(usdc: float = 0, alias: str = None) -> Dict:
    """Create gasless HFT wallet."""
    return gasless.create_gasless_hft_wallet(usdc, alias)

def get_hft_config(address: str) -> Dict:
    """Get gasless HFT config for address."""
    return gasless.get_gasless_hft_config(address)


# ==================== CLI ====================

def main():
    import sys

    if len(sys.argv) < 2:
        print("""
Gasless Wallet Manager - Zero-Gas Polymarket Trading
=====================================================

Gas is only needed for setup (~0.02 MATIC), trading is ALWAYS gasless.

COMMANDS:
  status                Show manager status
  check ADDRESS         Check if wallet is gasless-ready
  setup KEY             Setup wallet for gasless trading
  create [USDC]         Create gasless-ready HFT wallet

EXAMPLES:
  python gasless_wallet_manager.py status
  python gasless_wallet_manager.py check 0x1234...
  python gasless_wallet_manager.py create 100
""")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(gasless.status(), indent=2))

    elif cmd == "check":
        if len(sys.argv) < 3:
            print("Usage: check ADDRESS")
            return
        result = gasless.check_gasless_ready(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "setup":
        if len(sys.argv) < 3:
            print("Usage: setup PRIVATE_KEY")
            return
        result = gasless.setup_for_gasless_trading(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "create":
        usdc = float(sys.argv[2]) if len(sys.argv) > 2 else 0
        result = gasless.create_gasless_hft_wallet(usdc)
        print(f"Created: {result['wallet'].address}")
        print(f"Ready: {result['ready']}")
        print(f"Config: {json.dumps(result['config'], indent=2)}")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
