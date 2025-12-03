#!/usr/bin/env python3
"""
Polymarket Wallet Factory - Full Stack Account Creation & Onboarding

Creates FULLY FUNCTIONAL Polymarket trading accounts:
1. Generate ETH keypair
2. Fund with USDC from master wallet
3. Fund with MATIC for gas
4. Set Polymarket contract allowances
5. Derive API credentials
6. Register in fleet

USAGE:
    from executor.polymarket_wallet_factory import factory

    # Create one fully onboarded wallet
    wallet = factory.create_trading_wallet(usdc_amount=100)

    # Create fleet of trading wallets
    wallets = factory.create_trading_fleet(count=10, usdc_per_wallet=50)

    # Onboard existing wallet
    factory.onboard_wallet(address, private_key)

Serving: Yair Siegel
"""

import os
import sys
import json
import time
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Crypto imports
from eth_account import Account
from web3 import Web3

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
WALLETS_DIR = STATE_DIR / "wallets"
WALLETS_DIR.mkdir(parents=True, exist_ok=True)

# ==================== POLYGON CONSTANTS ====================

POLYGON_RPC = "https://polygon-rpc.com"
POLYGON_CHAIN_ID = 137

# USDC on Polygon
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC.e (bridged)
USDC_DECIMALS = 6

# Polymarket Contract Addresses (Polygon Mainnet)
# These are the contracts that need allowances for trading
POLYMARKET_CONTRACTS = {
    "CTF_EXCHANGE": "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",      # Conditional Token Exchange
    "NEG_RISK_CTF_EXCHANGE": "0xC5d563A36AE78145C45a50134d48A1215220f80a",  # Neg Risk Exchange
    "NEG_RISK_ADAPTER": "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296",      # Neg Risk Adapter
}

# ERC20 ABI for approve/allowance
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

# Maximum allowance (2^256 - 1)
MAX_ALLOWANCE = 2**256 - 1


@dataclass
class OnboardedWallet:
    """Fully onboarded Polymarket trading wallet."""
    address: str
    private_key: str
    alias: str
    created_at: str
    status: str

    # Onboarding status
    usdc_balance: float = 0
    matic_balance: float = 0
    allowances_set: bool = False
    api_creds_derived: bool = False

    # Polymarket specific
    signature_type: int = 0  # EOA for programmatic wallets
    funder_address: str = ""  # Self for EOA

    # Onboarding details
    onboarding_tx_hashes: List[str] = field(default_factory=list)


class PolymarketWalletFactory:
    """
    Full-stack Polymarket wallet creation and onboarding.

    Creates wallets that are READY TO TRADE:
    - Generated keypair
    - Funded with USDC
    - Funded with MATIC (gas)
    - Allowances set for Polymarket contracts
    - API credentials derived
    """

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
        self.usdc_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(USDC_ADDRESS),
            abi=ERC20_ABI
        )
        self.lock = threading.Lock()

        # Load master wallet from env
        self.master_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
        self.master_address = None
        if self.master_key:
            self.master_address = Account.from_key(self.master_key).address

        # Registry integration
        self._wallet_manager = None

    @property
    def wallet_manager(self):
        if not self._wallet_manager:
            from executor.multi_wallet_manager import MultiWalletManager
            self._wallet_manager = MultiWalletManager()
        return self._wallet_manager

    # ==================== WALLET CREATION ====================

    def generate_wallet(self, alias: str = None) -> OnboardedWallet:
        """Generate new ETH keypair (step 1)."""
        account = Account.create(extra_entropy=secrets.token_bytes(32))

        wallet = OnboardedWallet(
            address=account.address,
            private_key=account.key.hex(),
            alias=alias or f"poly_{int(time.time())}",
            created_at=datetime.now(timezone.utc).isoformat(),
            status="created",
            funder_address=account.address,  # Self-funded EOA
            signature_type=0  # EOA
        )

        return wallet

    # ==================== FUNDING ====================

    def get_master_balances(self) -> Dict:
        """Get master wallet balances."""
        if not self.master_address:
            return {"error": "No master wallet configured"}

        matic = self.w3.eth.get_balance(self.master_address) / 1e18
        usdc = self.usdc_contract.functions.balanceOf(
            Web3.to_checksum_address(self.master_address)
        ).call() / (10 ** USDC_DECIMALS)

        return {
            "address": self.master_address,
            "matic": matic,
            "usdc": usdc
        }

    def fund_with_matic(self, to_address: str, amount_matic: float = 0.1) -> Dict:
        """
        Send MATIC for gas fees (step 2a).

        Args:
            to_address: Destination wallet
            amount_matic: Amount of MATIC (0.1 is good for ~100 transactions)

        Returns:
            {"success": bool, "tx_hash": "0x...", "amount": float}
        """
        if not self.master_key:
            return {"success": False, "error": "No master wallet configured"}

        try:
            to_addr = Web3.to_checksum_address(to_address)
            amount_wei = int(amount_matic * 1e18)

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.master_address)
            gas_price = self.w3.eth.gas_price

            tx = {
                'nonce': nonce,
                'to': to_addr,
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': POLYGON_CHAIN_ID
            }

            # Sign and send
            signed = self.w3.eth.account.sign_transaction(tx, self.master_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            return {
                "success": receipt.status == 1,
                "tx_hash": tx_hash.hex(),
                "amount": amount_matic,
                "to": to_address
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def fund_with_usdc(self, to_address: str, amount_usdc: float) -> Dict:
        """
        Send USDC for trading (step 2b).

        Args:
            to_address: Destination wallet
            amount_usdc: Amount of USDC to send

        Returns:
            {"success": bool, "tx_hash": "0x...", "amount": float}
        """
        if not self.master_key:
            return {"success": False, "error": "No master wallet configured"}

        try:
            to_addr = Web3.to_checksum_address(to_address)
            amount_wei = int(amount_usdc * (10 ** USDC_DECIMALS))

            # Build transfer transaction
            nonce = self.w3.eth.get_transaction_count(self.master_address)
            gas_price = self.w3.eth.gas_price

            tx = self.usdc_contract.functions.transfer(
                to_addr, amount_wei
            ).build_transaction({
                'from': self.master_address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': gas_price,
                'chainId': POLYGON_CHAIN_ID
            })

            # Sign and send
            signed = self.w3.eth.account.sign_transaction(tx, self.master_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            return {
                "success": receipt.status == 1,
                "tx_hash": tx_hash.hex(),
                "amount": amount_usdc,
                "to": to_address
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== ALLOWANCES ====================

    def check_allowances(self, wallet_address: str) -> Dict:
        """Check current Polymarket allowances for wallet."""
        addr = Web3.to_checksum_address(wallet_address)
        allowances = {}

        for name, contract_addr in POLYMARKET_CONTRACTS.items():
            try:
                allowance = self.usdc_contract.functions.allowance(
                    addr,
                    Web3.to_checksum_address(contract_addr)
                ).call()
                allowances[name] = {
                    "contract": contract_addr,
                    "allowance": allowance,
                    "allowance_usdc": allowance / (10 ** USDC_DECIMALS),
                    "is_max": allowance >= MAX_ALLOWANCE // 2
                }
            except Exception as e:
                allowances[name] = {"error": str(e)}

        return allowances

    def set_allowance(self, wallet_private_key: str, contract_address: str,
                      amount: int = MAX_ALLOWANCE) -> Dict:
        """
        Set USDC allowance for a Polymarket contract.

        Args:
            wallet_private_key: Private key of wallet setting allowance
            contract_address: Polymarket contract to approve
            amount: Allowance amount (default: max)

        Returns:
            {"success": bool, "tx_hash": "0x..."}
        """
        try:
            account = Account.from_key(wallet_private_key)
            wallet_address = account.address

            nonce = self.w3.eth.get_transaction_count(wallet_address)
            gas_price = self.w3.eth.gas_price

            tx = self.usdc_contract.functions.approve(
                Web3.to_checksum_address(contract_address),
                amount
            ).build_transaction({
                'from': wallet_address,
                'nonce': nonce,
                'gas': 60000,
                'gasPrice': gas_price,
                'chainId': POLYGON_CHAIN_ID
            })

            # Sign and send
            signed = self.w3.eth.account.sign_transaction(tx, wallet_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            return {
                "success": receipt.status == 1,
                "tx_hash": tx_hash.hex(),
                "contract": contract_address
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_all_allowances(self, wallet_private_key: str) -> Dict:
        """
        Set allowances for ALL Polymarket contracts (step 3).

        Args:
            wallet_private_key: Private key of wallet

        Returns:
            {"success": bool, "allowances": {...}, "tx_hashes": [...]}
        """
        results = {"allowances": {}, "tx_hashes": [], "success": True}

        for name, contract_addr in POLYMARKET_CONTRACTS.items():
            result = self.set_allowance(wallet_private_key, contract_addr)
            results["allowances"][name] = result

            if result.get("success"):
                results["tx_hashes"].append(result.get("tx_hash"))
            else:
                results["success"] = False

            # Small delay between transactions
            time.sleep(1)

        return results

    # ==================== API CREDENTIALS ====================

    def derive_api_credentials(self, wallet_private_key: str) -> Dict:
        """
        Derive Polymarket API credentials (step 4).

        Args:
            wallet_private_key: Private key of wallet

        Returns:
            {"success": bool, "api_key": "...", "api_secret": "..."}
        """
        try:
            from py_clob_client.client import ClobClient

            account = Account.from_key(wallet_private_key)

            client = ClobClient(
                "https://clob.polymarket.com",
                key=wallet_private_key,
                chain_id=POLYGON_CHAIN_ID,
                signature_type=0,  # EOA
                funder=account.address  # Self-funded
            )

            # Derive credentials
            creds = client.create_or_derive_api_creds()
            client.set_api_creds(creds)

            # Test connection
            health = client.get_ok()

            return {
                "success": True,
                "api_key": creds.api_key if hasattr(creds, 'api_key') else str(creds)[:20],
                "health": health
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== FULL ONBOARDING ====================

    def create_trading_wallet(self, usdc_amount: float = 100,
                              matic_amount: float = 0.1,
                              alias: str = None) -> OnboardedWallet:
        """
        Create a FULLY ONBOARDED Polymarket trading wallet.

        Complete flow:
        1. Generate keypair
        2. Fund with MATIC (gas)
        3. Fund with USDC (trading capital)
        4. Set Polymarket allowances
        5. Derive API credentials
        6. Register in fleet

        Args:
            usdc_amount: USDC to fund wallet with
            matic_amount: MATIC for gas (0.1 = ~100 transactions)
            alias: Wallet alias

        Returns:
            OnboardedWallet: Fully functional trading wallet
        """
        print(f"[Factory] Creating trading wallet with ${usdc_amount} USDC...")

        # Step 1: Generate wallet
        wallet = self.generate_wallet(alias)
        print(f"  1. Generated: {wallet.address[:20]}...")

        # Step 2a: Fund with MATIC
        matic_result = self.fund_with_matic(wallet.address, matic_amount)
        if matic_result.get("success"):
            wallet.matic_balance = matic_amount
            wallet.onboarding_tx_hashes.append(matic_result["tx_hash"])
            print(f"  2a. Funded {matic_amount} MATIC")
        else:
            print(f"  2a. MATIC funding failed: {matic_result.get('error')}")
            wallet.status = "matic_funding_failed"
            return wallet

        # Step 2b: Fund with USDC
        usdc_result = self.fund_with_usdc(wallet.address, usdc_amount)
        if usdc_result.get("success"):
            wallet.usdc_balance = usdc_amount
            wallet.onboarding_tx_hashes.append(usdc_result["tx_hash"])
            print(f"  2b. Funded ${usdc_amount} USDC")
        else:
            print(f"  2b. USDC funding failed: {usdc_result.get('error')}")
            wallet.status = "usdc_funding_failed"
            return wallet

        # Step 3: Set allowances
        allowance_result = self.set_all_allowances(wallet.private_key)
        if allowance_result.get("success"):
            wallet.allowances_set = True
            wallet.onboarding_tx_hashes.extend(allowance_result["tx_hashes"])
            print(f"  3. Set {len(POLYMARKET_CONTRACTS)} allowances")
        else:
            print(f"  3. Allowances failed: {allowance_result}")
            wallet.status = "allowance_failed"
            return wallet

        # Step 4: Derive API credentials
        api_result = self.derive_api_credentials(wallet.private_key)
        if api_result.get("success"):
            wallet.api_creds_derived = True
            print(f"  4. API credentials derived")
        else:
            print(f"  4. API creds failed: {api_result.get('error')}")
            wallet.status = "api_creds_failed"
            return wallet

        # Step 5: Register in fleet
        self.wallet_manager.import_wallet(
            wallet.private_key,
            wallet.address,  # Self-funded EOA
            wallet.alias
        )
        print(f"  5. Registered in fleet")

        wallet.status = "active"
        print(f"[Factory] Wallet {wallet.alias} READY TO TRADE")

        return wallet

    def create_trading_fleet(self, count: int, usdc_per_wallet: float = 50,
                             matic_per_wallet: float = 0.1,
                             alias_prefix: str = "fleet") -> List[OnboardedWallet]:
        """
        Create multiple fully onboarded trading wallets.

        Args:
            count: Number of wallets to create
            usdc_per_wallet: USDC per wallet
            matic_per_wallet: MATIC per wallet
            alias_prefix: Alias prefix

        Returns:
            List[OnboardedWallet]: Fleet of trading wallets
        """
        print(f"[Factory] Creating fleet of {count} wallets...")
        print(f"  Total USDC needed: ${count * usdc_per_wallet}")
        print(f"  Total MATIC needed: {count * matic_per_wallet}")

        # Check master balances
        balances = self.get_master_balances()
        if "error" in balances:
            print(f"  ERROR: {balances['error']}")
            return []

        print(f"  Master wallet: ${balances['usdc']:.2f} USDC, {balances['matic']:.4f} MATIC")

        if balances["usdc"] < count * usdc_per_wallet:
            print(f"  ERROR: Insufficient USDC")
            return []

        if balances["matic"] < count * matic_per_wallet + 0.5:  # +0.5 for gas
            print(f"  ERROR: Insufficient MATIC")
            return []

        wallets = []
        for i in range(count):
            alias = f"{alias_prefix}_{i+1}"
            wallet = self.create_trading_wallet(usdc_per_wallet, matic_per_wallet, alias)
            wallets.append(wallet)

            if wallet.status != "active":
                print(f"  WARNING: Wallet {alias} failed at {wallet.status}")

        successful = sum(1 for w in wallets if w.status == "active")
        print(f"[Factory] Fleet created: {successful}/{count} successful")

        return wallets

    def onboard_existing_wallet(self, private_key: str,
                                fund_usdc: float = 0,
                                fund_matic: float = 0,
                                alias: str = None) -> OnboardedWallet:
        """
        Onboard an existing wallet (set allowances, derive creds).

        Args:
            private_key: Existing wallet private key
            fund_usdc: Optional USDC to add
            fund_matic: Optional MATIC to add
            alias: Wallet alias

        Returns:
            OnboardedWallet: Onboarded wallet
        """
        account = Account.from_key(private_key)

        wallet = OnboardedWallet(
            address=account.address,
            private_key=private_key,
            alias=alias or f"imported_{account.address[:8]}",
            created_at=datetime.now(timezone.utc).isoformat(),
            status="onboarding",
            funder_address=account.address,
            signature_type=0
        )

        print(f"[Factory] Onboarding existing wallet {wallet.address[:20]}...")

        # Optional funding
        if fund_matic > 0:
            result = self.fund_with_matic(wallet.address, fund_matic)
            if result.get("success"):
                print(f"  Funded {fund_matic} MATIC")

        if fund_usdc > 0:
            result = self.fund_with_usdc(wallet.address, fund_usdc)
            if result.get("success"):
                print(f"  Funded ${fund_usdc} USDC")

        # Check current allowances
        current = self.check_allowances(wallet.address)
        needs_allowances = any(
            not v.get("is_max", False) for v in current.values()
            if isinstance(v, dict) and "is_max" in v
        )

        if needs_allowances:
            # Check if wallet has MATIC for gas
            matic_balance = self.w3.eth.get_balance(account.address) / 1e18
            if matic_balance < 0.01:
                print(f"  Need MATIC for allowance transactions")
                self.fund_with_matic(wallet.address, 0.05)
                time.sleep(2)

            result = self.set_all_allowances(private_key)
            if result.get("success"):
                wallet.allowances_set = True
                print(f"  Set allowances")
        else:
            wallet.allowances_set = True
            print(f"  Allowances already set")

        # Derive API credentials
        api_result = self.derive_api_credentials(private_key)
        if api_result.get("success"):
            wallet.api_creds_derived = True
            print(f"  API credentials derived")

        # Get balances
        wallet.matic_balance = self.w3.eth.get_balance(account.address) / 1e18
        wallet.usdc_balance = self.usdc_contract.functions.balanceOf(
            account.address
        ).call() / (10 ** USDC_DECIMALS)

        # Register
        self.wallet_manager.import_wallet(private_key, account.address, wallet.alias)

        wallet.status = "active"
        print(f"[Factory] Wallet onboarded: ${wallet.usdc_balance:.2f} USDC ready")

        return wallet

    # ==================== STATUS ====================

    def get_wallet_status(self, address: str) -> Dict:
        """Get comprehensive status of a wallet."""
        addr = Web3.to_checksum_address(address)

        matic = self.w3.eth.get_balance(addr) / 1e18
        usdc = self.usdc_contract.functions.balanceOf(addr).call() / (10 ** USDC_DECIMALS)
        allowances = self.check_allowances(address)

        all_approved = all(
            v.get("is_max", False) for v in allowances.values()
            if isinstance(v, dict) and "is_max" in v
        )

        return {
            "address": address,
            "matic_balance": matic,
            "usdc_balance": usdc,
            "allowances": allowances,
            "all_approved": all_approved,
            "ready_to_trade": usdc > 0 and all_approved and matic > 0.001
        }

    def status(self) -> Dict:
        """Factory status."""
        master = self.get_master_balances()
        wallets = self.wallet_manager.list_wallets()

        return {
            "master_wallet": master,
            "fleet_size": len(wallets),
            "polymarket_contracts": list(POLYMARKET_CONTRACTS.keys()),
            "rpc": POLYGON_RPC
        }


# Singleton instance
factory = PolymarketWalletFactory()


# ==================== CONVENIENCE FUNCTIONS ====================

def create_wallet(usdc: float = 100, matic: float = 0.1, alias: str = None) -> OnboardedWallet:
    """Quick function: create one trading wallet."""
    return factory.create_trading_wallet(usdc, matic, alias)

def create_fleet(count: int, usdc_per: float = 50) -> List[OnboardedWallet]:
    """Quick function: create trading fleet."""
    return factory.create_trading_fleet(count, usdc_per)

def onboard(private_key: str, alias: str = None) -> OnboardedWallet:
    """Quick function: onboard existing wallet."""
    return factory.onboard_existing_wallet(private_key, alias=alias)

def check_wallet(address: str) -> Dict:
    """Quick function: check wallet status."""
    return factory.get_wallet_status(address)


# ==================== CLI ====================

def main():
    import sys

    if len(sys.argv) < 2:
        print("""
Polymarket Wallet Factory - Full Stack Account Creation
========================================================

COMMANDS:
  status              Show factory status & master wallet
  create [usdc]       Create one trading wallet (default $100 USDC)
  fleet N [usdc]      Create N trading wallets
  onboard KEY         Onboard existing wallet by private key
  check ADDRESS       Check wallet status & readiness

EXAMPLES:
  python polymarket_wallet_factory.py status
  python polymarket_wallet_factory.py create 50
  python polymarket_wallet_factory.py fleet 10 25
  python polymarket_wallet_factory.py check 0x1234...
""")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(factory.status(), indent=2, default=str))

    elif cmd == "create":
        usdc = float(sys.argv[2]) if len(sys.argv) > 2 else 100
        wallet = create_wallet(usdc)
        print(f"\nCreated: {wallet.alias}")
        print(f"Address: {wallet.address}")
        print(f"Status: {wallet.status}")

    elif cmd == "fleet":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        usdc = float(sys.argv[3]) if len(sys.argv) > 3 else 50
        wallets = create_fleet(count, usdc)
        print(f"\nCreated {len([w for w in wallets if w.status == 'active'])}/{count} wallets")

    elif cmd == "onboard":
        key = sys.argv[2]
        wallet = onboard(key)
        print(f"\nOnboarded: {wallet.alias}")
        print(f"USDC: ${wallet.usdc_balance:.2f}")
        print(f"Status: {wallet.status}")

    elif cmd == "check":
        address = sys.argv[2]
        status = check_wallet(address)
        print(json.dumps(status, indent=2, default=str))

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
