#!/usr/bin/env python3
"""
FREE Financial Aggregation Stack
No Plaid, no expensive APIs - built for $0

Sources:
- Polymarket: Direct blockchain RPC (FREE)
- Robinhood: robin_stocks library (FREE, unofficial)
- PayPal: REST API with OAuth (FREE)
- Credit Cards: Manual input + reminders
- Schwab: Official OAuth (FREE)
"""

import os
import json
import hashlib
import requests
from datetime import datetime
from pathlib import Path

from finance.hub_store import load_hub, update_account

FINANCE_DIR = Path(__file__).parent.parent
HUB_PATH = Path(__file__).resolve().parents[2] / "state" / "private_finance_hub.json"

class FreeAggregator:
    """Zero-cost financial data aggregation"""
    
    def __init__(self):
        self.hub = self._load_hub()
    
    def _load_hub(self):
        return load_hub(HUB_PATH)

    def _save_hub(self, account_updates, remove_account_keys=("wallet_address",)):
        """Persist only this refresh's account delta; never write a stale full snapshot."""
        self.hub = update_account(
            HUB_PATH,
            "polymarket",
            account_updates,
            remove_keys=remove_account_keys,
            top_level_updates={"last_updated": datetime.now().astimezone().isoformat()},
        )
    
    # ═══════════════════════════════════════════════════════════
    # POLYMARKET - FREE via blockchain RPC
    # ═══════════════════════════════════════════════════════════
    def fetch_polymarket(self, wallet_address):
        """Fetch both supported USDC contracts; partial data is never a total."""
        from finance.refresh_balances import (
            USDC_BRIDGED,
            USDC_NATIVE,
            get_erc20_balance,
            get_native_balance,
            get_chain_id,
            POLYGON_CHAIN_ID,
        )

        chain_id = get_chain_id()
        if chain_id == POLYGON_CHAIN_ID:
            bridged = get_erc20_balance(wallet_address, USDC_BRIDGED)
            native = get_erc20_balance(wallet_address, USDC_NATIVE)
            gas = get_native_balance(wallet_address)
        else:
            bridged = native = gas = None
        complete = chain_id == POLYGON_CHAIN_ID and bridged is not None and native is not None
        observed_at = datetime.now().astimezone().isoformat()

        proof = {
            "status": "verified" if complete else "partial",
            "source": "polygon_rpc",
            "chain": "polygon",
            "chain_id": chain_id,
            "wallet_fingerprint": hashlib.sha256(wallet_address.lower().encode("ascii")).hexdigest(),
            "observed_at": observed_at,
            "tokens": {
                "usdc_bridged": {
                    "contract": USDC_BRIDGED,
                    "balance": bridged,
                    "status": "verified" if bridged is not None else "unknown",
                },
                "usdc_native": {
                    "contract": USDC_NATIVE,
                    "balance": native,
                    "status": "verified" if native is not None else "unknown",
                },
            },
        }
        return {
            "balance_usdc": bridged + native if complete else None,
            "balance_matic": gas,
            "balance_verification": proof,
            "status": proof["status"],
        }

    # ═══════════════════════════════════════════════════════════
    # ROBINHOOD - FREE via robin_stocks (unofficial)
    # ═══════════════════════════════════════════════════════════
    def fetch_robinhood(self, username=None, password=None, mfa_code=None):
        """
        Fetch Robinhood data - FREE but requires credentials
        Uses robin_stocks library
        
        WARNING: Unofficial API, may break, use at own risk
        """
        try:
            import robin_stocks.robinhood as rh
        except ImportError:
            return {"error": "robin_stocks not installed. Run: pip install robin_stocks", "status": "failed"}
        
        if not username or not password:
            return {"error": "credentials required", "status": "needs_auth"}
        
        try:
            # Login (will prompt for MFA if needed)
            login = rh.login(username, password, mfa_code=mfa_code)
            
            # Get portfolio
            profile = rh.profiles.load_portfolio_profile()
            positions = rh.account.build_holdings()
            
            total_value = float(profile.get('equity', 0))
            
            return {
                "total_value": total_value,
                "positions": positions,
                "status": "success"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    # ═══════════════════════════════════════════════════════════
    # PAYPAL - FREE via REST API
    # ═══════════════════════════════════════════════════════════
    def fetch_paypal(self, client_id=None, client_secret=None):
        """
        Fetch PayPal balance - FREE with API credentials
        
        Get credentials at: https://developer.paypal.com/dashboard/applications
        """
        if not client_id or not client_secret:
            return {"error": "PayPal API credentials required", "status": "needs_auth"}
        
        try:
            # Get OAuth token
            auth_url = "https://api-m.paypal.com/v1/oauth2/token"
            auth_resp = requests.post(
                auth_url,
                auth=(client_id, client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"}
            )
            
            if auth_resp.status_code != 200:
                return {"error": "OAuth failed", "status": "auth_failed"}
            
            access_token = auth_resp.json().get("access_token")
            
            # Get balance (requires partner status for full access)
            # For now, return auth success - balance API limited
            return {
                "auth_status": "success",
                "note": "Balance API requires PayPal Partner status",
                "status": "partial"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    # ═══════════════════════════════════════════════════════════
    # SCHWAB - FREE via Official OAuth
    # ═══════════════════════════════════════════════════════════
    def fetch_schwab(self, app_key=None, app_secret=None, refresh_token=None):
        """
        Fetch Schwab data - FREE with official OAuth
        
        Setup required:
        1. Register at developer.schwab.com
        2. Create app, get App Key + Secret
        3. Complete OAuth flow to get refresh token
        """
        if not app_key or not refresh_token:
            return {"error": "Schwab OAuth credentials required", "status": "needs_auth"}
        
        try:
            # Exchange refresh token for access token
            token_url = "https://api.schwabapi.com/v1/oauth/token"
            token_resp = requests.post(
                token_url,
                auth=(app_key, app_secret),
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )
            
            if token_resp.status_code != 200:
                return {"error": "Token refresh failed", "status": "auth_failed"}
            
            access_token = token_resp.json().get("access_token")
            
            # Get accounts
            accounts_url = "https://api.schwabapi.com/trader/v1/accounts"
            accounts_resp = requests.get(
                accounts_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if accounts_resp.status_code == 200:
                return {
                    "accounts": accounts_resp.json(),
                    "status": "success"
                }
            else:
                return {"error": "Account fetch failed", "status": "failed"}
                
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    # ═══════════════════════════════════════════════════════════
    # CREDIT CARDS - Manual with smart reminders
    # ═══════════════════════════════════════════════════════════
    def update_credit_cards(self, cards):
        """
        Manual credit card update with cycling optimization
        
        cards = [
            {"name": "Chase", "limit": 5000, "balance": 4000, "apr": 24.99, "min_payment": 100, "due_date": 15},
            ...
        ]
        """
        total_limit = sum(c.get("limit", 0) for c in cards)
        total_balance = sum(c.get("balance", 0) for c in cards)
        total_available = total_limit - total_balance
        
        # Calculate optimal cycling
        cycling_advice = self._calculate_cycling(cards)
        
        return {
            "total_limit": total_limit,
            "total_balance": total_balance,
            "total_available": total_available,
            "utilization": (total_balance / total_limit * 100) if total_limit > 0 else 0,
            "cycling_advice": cycling_advice,
            "status": "success"
        }
    
    def _calculate_cycling(self, cards):
        """Calculate optimal credit card cycling strategy"""
        advice = []
        
        # Sort by APR (pay highest first)
        sorted_by_apr = sorted(cards, key=lambda x: x.get("apr", 0), reverse=True)
        
        # Sort by utilization (reduce highest utilization cards first for score)
        for card in sorted_by_apr:
            util = card.get("balance", 0) / card.get("limit", 1) * 100
            if util > 30:
                advice.append({
                    "card": card.get("name"),
                    "action": f"Reduce balance to improve utilization (currently {util:.0f}%)",
                    "priority": "high" if util > 50 else "medium"
                })
        
        # Find balance transfer opportunities
        low_util_cards = [c for c in cards if c.get("balance", 0) / c.get("limit", 1) < 0.3]
        high_apr_cards = [c for c in cards if c.get("apr", 0) > 20 and c.get("balance", 0) > 0]
        
        if low_util_cards and high_apr_cards:
            advice.append({
                "action": f"Consider balance transfer from high APR cards to low utilization cards",
                "from": [c.get("name") for c in high_apr_cards],
                "to": [c.get("name") for c in low_util_cards],
                "priority": "high"
            })
        
        return advice
    
    # ═══════════════════════════════════════════════════════════
    # REFRESH ALL
    # ═══════════════════════════════════════════════════════════
    def refresh_all(self):
        """Refresh sources and merge only verified deltas into the latest hub state."""
        results = {}
        try:
            from dotenv import load_dotenv
            load_dotenv(Path(__file__).resolve().parents[2] / ".env.polymarket", override=False)
        except ImportError:
            pass
        wallet = os.getenv("POLYMARKET_FUNDER_ADDRESS")
        account_updates = {}
        if wallet:
            result = self.fetch_polymarket(wallet)
            account_updates["balance_verification"] = result["balance_verification"]
            account_updates["balance_status"] = result["status"]
            if result["status"] == "verified":
                account_updates["balance_usdc"] = result["balance_usdc"]
                account_updates["last_updated"] = result["balance_verification"]["observed_at"]
            if result["balance_matic"] is not None:
                account_updates["balance_matic"] = result["balance_matic"]
            results["polymarket"] = result
        else:
            account_updates["balance_status"] = "unknown"
            results["polymarket"] = {
                "status": "unknown",
                "balance_usdc": None,
                "reason": "POLYMARKET_FUNDER_ADDRESS is not configured",
            }

        self._save_hub(account_updates)
        return results


def main():
    """CLI for free aggregator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Free Financial Aggregator")
    parser.add_argument("command", choices=["refresh", "status", "cycling"])
    args = parser.parse_args()
    
    agg = FreeAggregator()
    
    if args.command == "refresh":
        results = agg.refresh_all()
        print(json.dumps(results, indent=2))
    
    elif args.command == "status":
        print(json.dumps(agg.hub, indent=2))
    
    elif args.command == "cycling":
        # Example - would need real card data
        print("Credit card cycling optimizer - update cards in hub first")


if __name__ == "__main__":
    main()
