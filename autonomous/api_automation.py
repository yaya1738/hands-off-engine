#!/usr/bin/env python3
"""
API-Powered Automation - Direct API Execution
Uses all available API credentials for maximum automation.

Serving: Yair Siegel

APIS LEVERAGED:
1. Polymarket CLOB API - Live trading
2. DigitalOcean API - Infrastructure management
3. GitHub API - Code contribution
4. Gamma API - Market data
"""

import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
AUTOMATION_STATE = STATE_DIR / "api_automation.json"
ACTION_LOG = STATE_DIR / "api_actions.jsonl"

# API Credentials
POLYMARKET_KEY = "0x644444ab1d39e9074b01f085a27a4bbf5a8536f411b9b2bea04eb3934f038493"
POLYMARKET_FUNDER = "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
POLYMARKET_HOST = "https://clob.polymarket.com"

DO_API_TOKEN = "dop_v1_e08e7243de8b4abe69c76767f17919de4caacc2889135d0d9e558e6f300d22be"
DO_API_BASE = "https://api.digitalocean.com/v2"

GAMMA_API = "https://gamma-api.polymarket.com"


class APIAutomation:
    """Direct API automation for maximum efficiency."""

    def __init__(self):
        self.state = self._load_state()
        self.poly_client = None
        self._init_polymarket()

    def _load_state(self) -> Dict:
        if AUTOMATION_STATE.exists():
            with open(AUTOMATION_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "api_calls_made": 0,
            "successful_trades": 0,
            "infrastructure_actions": 0,
            "last_run": None
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(AUTOMATION_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_action(self, action: Dict):
        action["timestamp"] = datetime.now(timezone.utc).isoformat()
        action["master"] = MASTER
        with open(ACTION_LOG, 'a') as f:
            f.write(json.dumps(action) + "\n")

    def _init_polymarket(self):
        """Initialize Polymarket client."""
        try:
            from py_clob_client.client import ClobClient
            self.poly_client = ClobClient(
                POLYMARKET_HOST,
                key=POLYMARKET_KEY,
                chain_id=137,
                funder=POLYMARKET_FUNDER
            )
            creds = self.poly_client.create_or_derive_api_creds()
            self.poly_client.set_api_creds(creds)
            print("✓ Polymarket API connected")
        except Exception as e:
            print(f"✗ Polymarket init: {e}")

    # ==================== POLYMARKET AUTOMATION ====================

    def get_polymarket_balances(self) -> Dict:
        """Get current Polymarket positions and balances."""
        if not self.poly_client:
            return {"error": "No client"}

        try:
            orders = self.poly_client.get_orders() or []
            total_exposure = sum(
                float(o.get("price", 0)) * float(o.get("original_size", o.get("size", 0)))
                for o in orders
            )
            return {
                "open_orders": len(orders),
                "total_exposure": total_exposure,
                "orders": orders[:10]
            }
        except Exception as e:
            return {"error": str(e)}

    def find_arbitrage_opportunities(self) -> List[Dict]:
        """Find arbitrage in prediction markets."""
        opportunities = []

        try:
            response = requests.get(
                f"{GAMMA_API}/markets",
                params={"closed": "false", "limit": 50},
                timeout=10
            )

            if response.status_code != 200:
                return []

            markets = response.json()

            for market in markets:
                prices = json.loads(market.get("outcomePrices", "[]"))
                if len(prices) >= 2:
                    yes_price = float(prices[0])
                    no_price = float(prices[1])
                    total = yes_price + no_price

                    # Arbitrage exists if total != 1
                    if total < 0.98 or total > 1.02:
                        opportunities.append({
                            "market": market.get("question", "")[:60],
                            "yes_price": yes_price,
                            "no_price": no_price,
                            "total": total,
                            "arbitrage": abs(1 - total),
                            "volume": float(market.get("volume", 0)),
                            "token_ids": json.loads(market.get("clobTokenIds", "[]"))
                        })

            return sorted(opportunities, key=lambda x: x["arbitrage"], reverse=True)[:10]
        except Exception as e:
            print(f"Error finding arbitrage: {e}")
            return []

    def get_high_value_signals(self) -> List[Dict]:
        """Get high-value trading signals."""
        signals = []

        try:
            response = requests.get(
                f"{GAMMA_API}/markets",
                params={"closed": "false", "limit": 100},
                timeout=10
            )

            if response.status_code != 200:
                return []

            markets = response.json()

            for market in markets:
                prices = json.loads(market.get("outcomePrices", "[]"))
                volume = float(market.get("volume", 0))
                liquidity = float(market.get("liquidity", 0))

                if len(prices) < 2 or liquidity < 10000:
                    continue

                yes_price = float(prices[0])

                # Extreme value plays
                if yes_price < 0.02 and volume > 500000:
                    signals.append({
                        "type": "DEEP_VALUE",
                        "market": market.get("question", "")[:60],
                        "outcome": "YES",
                        "price": yes_price,
                        "volume": volume,
                        "potential_return": (1 / yes_price) - 1,
                        "risk": "HIGH",
                        "token_ids": json.loads(market.get("clobTokenIds", "[]"))
                    })
                elif yes_price > 0.98 and volume > 500000:
                    no_price = float(prices[1])
                    signals.append({
                        "type": "CONTRARIAN",
                        "market": market.get("question", "")[:60],
                        "outcome": "NO",
                        "price": no_price,
                        "volume": volume,
                        "potential_return": (1 / max(no_price, 0.01)) - 1,
                        "risk": "HIGH",
                        "token_ids": json.loads(market.get("clobTokenIds", "[]"))
                    })

            return sorted(signals, key=lambda x: x["potential_return"], reverse=True)[:10]
        except Exception as e:
            print(f"Error getting signals: {e}")
            return []

    # ==================== DIGITALOCEAN AUTOMATION ====================

    def get_do_account_status(self) -> Dict:
        """Get DigitalOcean account status."""
        try:
            headers = {"Authorization": f"Bearer {DO_API_TOKEN}"}
            response = requests.get(f"{DO_API_BASE}/account", headers=headers, timeout=10)

            if response.status_code == 200:
                account = response.json().get("account", {})
                return {
                    "status": "active",
                    "email": account.get("email"),
                    "droplet_limit": account.get("droplet_limit"),
                    "floating_ip_limit": account.get("floating_ip_limit")
                }
            return {"status": "error", "code": response.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def list_do_droplets(self) -> List[Dict]:
        """List all DigitalOcean droplets."""
        try:
            headers = {"Authorization": f"Bearer {DO_API_TOKEN}"}
            response = requests.get(f"{DO_API_BASE}/droplets", headers=headers, timeout=10)

            if response.status_code == 200:
                droplets = response.json().get("droplets", [])
                return [
                    {
                        "id": d.get("id"),
                        "name": d.get("name"),
                        "status": d.get("status"),
                        "ip": d.get("networks", {}).get("v4", [{}])[0].get("ip_address") if d.get("networks", {}).get("v4") else None,
                        "region": d.get("region", {}).get("slug"),
                        "size": d.get("size_slug"),
                        "monthly_price": d.get("size", {}).get("price_monthly")
                    }
                    for d in droplets
                ]
            return []
        except Exception as e:
            print(f"Error listing droplets: {e}")
            return []

    def get_do_billing(self) -> Dict:
        """Get DigitalOcean billing info."""
        try:
            headers = {"Authorization": f"Bearer {DO_API_TOKEN}"}
            response = requests.get(f"{DO_API_BASE}/customers/my/balance", headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            return {"error": response.status_code}
        except Exception as e:
            return {"error": str(e)}

    # ==================== GITHUB AUTOMATION ====================

    def find_github_opportunities(self) -> List[Dict]:
        """Find GitHub contribution opportunities."""
        opportunities = []

        # Topics to search for bounties/paid issues
        topics = [
            "good-first-issue",
            "help-wanted",
            "bounty",
            "paid"
        ]

        try:
            for topic in topics[:2]:  # Limit to avoid rate limits
                response = requests.get(
                    "https://api.github.com/search/issues",
                    params={
                        "q": f"label:{topic} state:open language:python",
                        "sort": "created",
                        "order": "desc",
                        "per_page": 5
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    items = response.json().get("items", [])
                    for item in items:
                        opportunities.append({
                            "title": item.get("title", "")[:60],
                            "repo": item.get("repository_url", "").split("/")[-1],
                            "url": item.get("html_url"),
                            "labels": [l.get("name") for l in item.get("labels", [])],
                            "created": item.get("created_at"),
                            "topic": topic
                        })

        except Exception as e:
            print(f"Error searching GitHub: {e}")

        return opportunities[:10]

    # ==================== MASTER AUTOMATION ====================

    def run_full_automation(self) -> Dict:
        """Run full automation cycle leveraging all APIs."""
        print("=" * 70)
        print("API-POWERED AUTOMATION")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "apis_used": []
        }

        # 1. Polymarket Status
        print("[POLYMARKET STATUS]")
        balances = self.get_polymarket_balances()
        results["polymarket"] = balances
        results["apis_used"].append("polymarket")
        if "error" not in balances:
            print(f"  Open orders: {balances['open_orders']}")
            print(f"  Total exposure: ${balances['total_exposure']:.2f}")
        else:
            print(f"  Error: {balances.get('error')}")
        print()

        # 2. Trading Signals
        print("[HIGH-VALUE SIGNALS]")
        signals = self.get_high_value_signals()
        results["signals"] = signals[:5]
        for sig in signals[:3]:
            print(f"  {sig['type']}: {sig['market'][:40]}...")
            print(f"    {sig['outcome']} @ {sig['price']:.3f} | Return: {sig['potential_return']:.0%}")
        print()

        # 3. Arbitrage Opportunities
        print("[ARBITRAGE SCAN]")
        arbs = self.find_arbitrage_opportunities()
        results["arbitrage"] = arbs[:5]
        for arb in arbs[:3]:
            print(f"  {arb['market'][:40]}...")
            print(f"    YES: {arb['yes_price']:.3f} + NO: {arb['no_price']:.3f} = {arb['total']:.3f}")
            print(f"    Arbitrage: {arb['arbitrage']:.1%}")
        print()

        # 4. DigitalOcean Status
        print("[DIGITALOCEAN STATUS]")
        do_status = self.get_do_account_status()
        results["digitalocean"] = do_status
        results["apis_used"].append("digitalocean")
        print(f"  Status: {do_status.get('status')}")
        if do_status.get("droplet_limit"):
            print(f"  Droplet limit: {do_status.get('droplet_limit')}")
        print()

        # 5. Droplets
        droplets = self.list_do_droplets()
        results["droplets"] = droplets[:5]
        print(f"  Active droplets: {len(droplets)}")
        for d in droplets[:3]:
            print(f"    - {d['name']} ({d['status']}) @ {d.get('ip', 'N/A')}")
        print()

        # 6. GitHub Opportunities
        print("[GITHUB OPPORTUNITIES]")
        gh_ops = self.find_github_opportunities()
        results["github_opportunities"] = gh_ops[:5]
        results["apis_used"].append("github")
        print(f"  Found: {len(gh_ops)} opportunities")
        for op in gh_ops[:3]:
            print(f"    - {op['title'][:50]}...")
            print(f"      Repo: {op['repo']} | Labels: {', '.join(op['labels'][:3])}")
        print()

        # Summary
        print("=" * 70)
        print("API AUTOMATION SUMMARY")
        print("=" * 70)
        print(f"  APIs connected: {len(results['apis_used'])}")
        print(f"  Trading signals: {len(signals)}")
        print(f"  Arbitrage opportunities: {len(arbs)}")
        print(f"  Active droplets: {len(droplets)}")
        print(f"  GitHub opportunities: {len(gh_ops)}")
        print()

        print("RECOMMENDED ACTIONS:")
        if signals:
            best = signals[0]
            print(f"  1. TRADE: {best['outcome']} on {best['market'][:40]}")
            print(f"     Price: {best['price']:.3f} | Potential: {best['potential_return']:.0%}")
        if arbs:
            best_arb = arbs[0]
            print(f"  2. ARBITRAGE: {best_arb['market'][:40]}")
            print(f"     Gap: {best_arb['arbitrage']:.1%}")
        if gh_ops:
            best_gh = gh_ops[0]
            print(f"  3. CONTRIBUTE: {best_gh['title'][:40]}")
            print(f"     Repo: {best_gh['repo']}")
        print()

        # Update state
        self.state["api_calls_made"] += len(results["apis_used"])
        self.state["last_run"] = results["timestamp"]
        self._save_state()

        self._log_action({
            "type": "full_automation",
            "apis_used": results["apis_used"],
            "signals_found": len(signals),
            "arbitrage_found": len(arbs)
        })

        return results


def main():
    automation = APIAutomation()
    return automation.run_full_automation()


if __name__ == "__main__":
    main()
