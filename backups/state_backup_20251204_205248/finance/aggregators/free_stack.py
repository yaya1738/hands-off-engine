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
import requests
from datetime import datetime
from pathlib import Path

FINANCE_DIR = Path(__file__).parent.parent
HUB_PATH = FINANCE_DIR / "yair_finance_hub.json"

class FreeAggregator:
    """Zero-cost financial data aggregation"""
    
    def __init__(self):
        self.hub = self._load_hub()
    
    def _load_hub(self):
        if HUB_PATH.exists():
            with open(HUB_PATH) as f:
                return json.load(f)
        return {}
    
    def _save_hub(self):
        self.hub["last_updated"] = datetime.utcnow().isoformat() + "Z"
        with open(HUB_PATH, 'w') as f:
            json.dump(self.hub, f, indent=2)
    
    # ═══════════════════════════════════════════════════════════
    # POLYMARKET - FREE via blockchain RPC
    # ═══════════════════════════════════════════════════════════
    def fetch_polymarket(self, wallet_address):
        """Fetch USDC balance from Polygon - completely free"""
        usdc_contract = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
        rpc_url = "https://polygon-rpc.com"
        
        data = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": usdc_contract,
                "data": f"0x70a08231000000000000000000000000{wallet_address[2:].lower()}"
            }, "latest"],
            "id": 1
        }
        
        try:
            resp = requests.post(rpc_url, json=data, timeout=10)
            result = resp.json()
            if "result" in result and result["result"] != "0x":
                balance = int(result["result"], 16) / 1e6
                return {"balance_usdc": balance, "status": "success"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}
        return {"error": "unknown", "status": "failed"}
    
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
        """Refresh all available data sources"""
        results = {}
        
        # Polymarket (always works - public blockchain)
        pm_wallet = self.hub.get("accounts", {}).get("polymarket", {}).get("wallet_address")
        if pm_wallet:
            pm_result = self.fetch_polymarket(pm_wallet)
            if pm_result.get("status") == "success":
                self.hub["accounts"]["polymarket"]["balance_usdc"] = pm_result["balance_usdc"]
                self.hub["accounts"]["polymarket"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
            results["polymarket"] = pm_result
        
        self._save_hub()
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
