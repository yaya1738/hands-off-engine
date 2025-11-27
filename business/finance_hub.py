#!/usr/bin/env python3
"""
Business Integration Module

Provides a unified interface to all financial data sources in the Hands-Off Engine.
This module consolidates access to:
- Account balances (external_accounts.json)
- Credit card data (cards.json)
- Manual balances (balances_manual.yaml)
- Performance metrics
- Trading positions

Usage:
    from business.finance_hub import FinanceHub
    hub = FinanceHub()
    summary = hub.get_unified_summary()
"""

import json
import os
import pathlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import yaml


@dataclass
class AccountBalance:
    """Represents a single account balance."""
    name: str
    balance: float
    account_type: str  # 'cash', 'credit', 'investment', 'crypto'
    last_updated: Optional[str] = None


@dataclass
class CreditCard:
    """Represents a credit card account."""
    name: str
    limit: float
    balance: float
    statement_day: int
    utilization: float = 0.0

    def __post_init__(self):
        if self.limit > 0:
            self.utilization = self.balance / self.limit


@dataclass
class TradingPosition:
    """Represents a trading position."""
    platform: str
    asset: str
    quantity: float
    cost_basis: float
    current_value: float
    unrealized_pnl: float = 0.0

    def __post_init__(self):
        self.unrealized_pnl = self.current_value - self.cost_basis


@dataclass
class FinancialSummary:
    """Unified financial summary."""
    timestamp: str
    total_assets: float
    total_liabilities: float
    net_worth: float
    liquid_cash: float
    credit_utilization: float
    accounts: List[AccountBalance] = field(default_factory=list)
    credit_cards: List[CreditCard] = field(default_factory=list)
    positions: List[TradingPosition] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class FinanceHub:
    """
    Central hub for all financial data in the Hands-Off Engine.
    
    Provides unified access to:
    - External accounts (PayPal, Monzo, Robinhood, etc.)
    - Credit cards and utilization
    - Trading positions (Polymarket, crypto)
    - Manual balance inputs
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the Finance Hub.
        
        Args:
            base_path: Base path for the hands-off-engine repository.
                      Defaults to detecting from common locations.
        """
        self.base_path = self._detect_base_path(base_path)
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = 60  # Cache TTL in seconds

    def _detect_base_path(self, provided_path: Optional[str]) -> pathlib.Path:
        """Detect the base path for the repository."""
        if provided_path:
            return pathlib.Path(provided_path)
        
        # Try common locations
        candidates = [
            pathlib.Path.home() / "hands-off",
            pathlib.Path.home() / "hands-off-engine",
            pathlib.Path("/data/data/com.termux/files/home/hands-off"),
            pathlib.Path.cwd(),
            pathlib.Path(__file__).parent.parent,
        ]
        
        for candidate in candidates:
            if (candidate / "termux-hands-off").exists():
                return candidate
            if (candidate / "agents").exists():
                return candidate
        
        return pathlib.Path.cwd()

    def _load_json(self, filepath: pathlib.Path) -> Dict:
        """Load a JSON file with error handling."""
        try:
            if filepath.exists():
                return json.loads(filepath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError) as e:
            print(f"[warn] Could not load {filepath}: {e}")
        return {}

    def _load_yaml(self, filepath: pathlib.Path) -> Dict:
        """Load a YAML file with error handling."""
        try:
            if filepath.exists():
                return yaml.safe_load(filepath.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, IOError) as e:
            print(f"[warn] Could not load {filepath}: {e}")
        return {}

    def get_external_accounts(self) -> Dict[str, float]:
        """
        Get external account balances from external_accounts.json.
        
        Returns:
            Dictionary mapping account names to balances.
        """
        paths = [
            self.base_path / "termux-hands-off" / "agents" / "external_accounts.json",
            self.base_path / "agents" / "external_accounts.json",
        ]
        
        for path in paths:
            data = self._load_json(path)
            if data:
                # Filter out non-numeric and metadata fields
                accounts = {}
                for k, v in data.items():
                    if isinstance(v, (int, float)):
                        accounts[k] = float(v)
                    elif isinstance(v, str):
                        try:
                            accounts[k] = float(v)
                        except ValueError:
                            pass
                return accounts
        return {}

    def get_credit_cards(self) -> List[CreditCard]:
        """
        Get credit card information from cards.json.
        
        Returns:
            List of CreditCard objects.
        """
        paths = [
            self.base_path / "termux-hands-off" / "agents" / "cards.json",
            self.base_path / "agents" / "cards.json",
        ]
        
        cards = []
        for path in paths:
            data = self._load_json(path)
            if data:
                for key, card_data in data.items():
                    try:
                        cards.append(CreditCard(
                            name=card_data.get("name", key),
                            limit=float(card_data.get("limit", 0)),
                            balance=float(card_data.get("balance", 0)),
                            statement_day=int(card_data.get("statement_day", 1))
                        ))
                    except (TypeError, ValueError):
                        continue
                break
        return cards

    def get_manual_balances(self) -> Dict[str, Dict[str, float]]:
        """
        Get manual balance inputs from balances_manual.yaml.
        
        Returns:
            Dictionary with categories (cash, crypto, etc.) and balances.
        """
        paths = [
            self.base_path / "termux-hands-off" / "agent" / "balances_manual.yaml",
            self.base_path / "agent" / "balances_manual.yaml",
        ]
        
        for path in paths:
            data = self._load_yaml(path)
            if data:
                return data
        return {}

    def get_polymarket_data(self) -> Dict[str, Any]:
        """
        Get Polymarket position and balance data.
        
        Returns:
            Dictionary with Polymarket-specific data.
        """
        accounts = self.get_external_accounts()
        return {
            "wallet": accounts.get("polymarket_wallet", ""),
            "cash": accounts.get("polymarket_cash", 0),
            "total": accounts.get("polymarket_total", 0),
            "cost_basis": accounts.get("polymarket_cost_basis", 0),
            "unrealized_est": accounts.get("polymarket_unrealized_est", 0),
        }

    def calculate_total_credit_utilization(self) -> float:
        """
        Calculate the overall credit utilization across all cards.
        
        Returns:
            Credit utilization as a decimal (0.0 to 1.0).
        """
        cards = self.get_credit_cards()
        total_limit = sum(c.limit for c in cards)
        total_balance = sum(c.balance for c in cards)
        
        if total_limit > 0:
            return total_balance / total_limit
        return 0.0

    def get_liquid_cash(self) -> float:
        """
        Calculate total liquid cash available.
        
        Returns:
            Total liquid cash in USD.
        """
        accounts = self.get_external_accounts()
        liquid_keys = [
            "paypal", "paypal_business", "monzo", 
            "robinhood_cash", "polymarket_cash", "schwab"
        ]
        return sum(accounts.get(k, 0) for k in liquid_keys if accounts.get(k, 0) > 0)

    def get_total_assets(self) -> float:
        """
        Calculate total assets across all accounts.
        
        Returns:
            Total assets in USD.
        """
        accounts = self.get_external_accounts()
        manual = self.get_manual_balances()
        
        # Sum positive values from external accounts
        total = sum(v for v in accounts.values() if isinstance(v, (int, float)) and v > 0)
        
        # Add manual cash and crypto
        if "cash" in manual:
            total += sum(v for v in manual["cash"].values() if isinstance(v, (int, float)) and v > 0)
        if "crypto" in manual:
            total += sum(v for v in manual["crypto"].values() if isinstance(v, (int, float)) and v > 0)
        
        return total

    def get_total_liabilities(self) -> float:
        """
        Calculate total liabilities (credit card balances, debts).
        
        Returns:
            Total liabilities in USD (as a positive number).
        """
        cards = self.get_credit_cards()
        accounts = self.get_external_accounts()
        
        # Credit card balances
        card_debt = sum(c.balance for c in cards)
        
        # Negative values in external accounts (debts)
        other_debt = sum(abs(v) for v in accounts.values() 
                        if isinstance(v, (int, float)) and v < 0)
        
        return card_debt + other_debt

    def get_unified_summary(self) -> FinancialSummary:
        """
        Generate a comprehensive financial summary.
        
        Returns:
            FinancialSummary object with all financial data.
        """
        accounts = self.get_external_accounts()
        cards = self.get_credit_cards()
        
        # Build account list
        account_list = []
        for name, balance in accounts.items():
            if isinstance(balance, (int, float)):
                if "credit" in name.lower():
                    acct_type = "credit"
                elif any(x in name.lower() for x in ["poly", "robin", "schwab"]):
                    acct_type = "investment"
                elif any(x in name.lower() for x in ["btc", "eth", "usdc"]):
                    acct_type = "crypto"
                else:
                    acct_type = "cash"
                account_list.append(AccountBalance(
                    name=name, balance=float(balance), account_type=acct_type
                ))
        
        # Calculate totals
        total_assets = self.get_total_assets()
        total_liabilities = self.get_total_liabilities()
        credit_util = self.calculate_total_credit_utilization()
        
        # Generate warnings
        warnings = []
        if credit_util >= 0.50:
            warnings.append(f"CRITICAL: Credit utilization at {credit_util*100:.1f}% (>=50%)")
        elif credit_util >= 0.45:
            warnings.append(f"WARNING: Credit utilization at {credit_util*100:.1f}% (>=45%)")
        
        for card in cards:
            if card.utilization >= 0.50:
                warnings.append(f"Card {card.name} utilization at {card.utilization*100:.1f}%")
        
        return FinancialSummary(
            timestamp=datetime.utcnow().isoformat() + "Z",
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_worth=total_assets - total_liabilities,
            liquid_cash=self.get_liquid_cash(),
            credit_utilization=credit_util,
            accounts=account_list,
            credit_cards=cards,
            positions=[],  # TODO: Add position tracking
            warnings=warnings
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Export all financial data as a dictionary.
        
        Returns:
            Dictionary with all financial data.
        """
        summary = self.get_unified_summary()
        return {
            "timestamp": summary.timestamp,
            "net_worth": summary.net_worth,
            "total_assets": summary.total_assets,
            "total_liabilities": summary.total_liabilities,
            "liquid_cash": summary.liquid_cash,
            "credit_utilization": summary.credit_utilization,
            "accounts": [
                {"name": a.name, "balance": a.balance, "type": a.account_type}
                for a in summary.accounts
            ],
            "credit_cards": [
                {
                    "name": c.name,
                    "limit": c.limit,
                    "balance": c.balance,
                    "utilization": c.utilization,
                    "statement_day": c.statement_day
                }
                for c in summary.credit_cards
            ],
            "warnings": summary.warnings,
            "polymarket": self.get_polymarket_data()
        }

    def print_summary(self) -> None:
        """Print a human-readable financial summary."""
        summary = self.get_unified_summary()
        
        print("=" * 60)
        print("UNIFIED FINANCIAL SUMMARY")
        print(f"Generated: {summary.timestamp}")
        print("=" * 60)
        
        print(f"\n📊 NET WORTH: ${summary.net_worth:,.2f}")
        print(f"   Assets:      ${summary.total_assets:,.2f}")
        print(f"   Liabilities: ${summary.total_liabilities:,.2f}")
        print(f"   Liquid Cash: ${summary.liquid_cash:,.2f}")
        
        print(f"\n💳 CREDIT UTILIZATION: {summary.credit_utilization*100:.1f}%")
        for card in summary.credit_cards:
            status = "⚠️" if card.utilization >= 0.45 else "✅"
            print(f"   {status} {card.name}: ${card.balance:,.0f} / ${card.limit:,.0f} ({card.utilization*100:.1f}%)")
        
        if summary.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in summary.warnings:
                print(f"   - {warning}")
        
        print("\n" + "=" * 60)


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Finance Hub")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--path", help="Base path for hands-off-engine")
    args = parser.parse_args()
    
    hub = FinanceHub(base_path=args.path)
    
    if args.json:
        print(json.dumps(hub.to_dict(), indent=2))
    else:
        hub.print_summary()


if __name__ == "__main__":
    main()
