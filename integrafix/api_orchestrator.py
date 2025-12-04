#!/usr/bin/env python3
"""
API Orchestrator - Unified System Controller
=============================================

The master orchestrator that connects all verticals through APIs:
- V1: Money Printer (Trading via Polymarket API)
- V2: GitHub Bounty Hunter (GitHub API)
- V3: Bug Bounty Hunter (HackerOne/Bugcrowd APIs)
- Infrastructure (Backups, Communication, Crypto)

All operations go through ABCFC-optimized API calls.
No CLI commands - pure API architecture.

Master: Yair Siegel
"API system using all sources in repo with good ABCFC-age"
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from api_manager import APIManager, APICallResult

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
BOUNTIES_DIR = PROJECT_ROOT / "bounties"
BUG_BOUNTIES_DIR = PROJECT_ROOT / "bug_bounties"


class APIOrchestrator:
    """Master orchestrator for all system operations via APIs."""

    def __init__(self):
        self.api_manager = APIManager()
        self.state_file = STATE_DIR / "orchestrator.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load orchestrator state."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "verticals": {
                "money_printer": {"status": "active", "operations": 0},
                "bounty_hunter": {"status": "active", "operations": 0},
                "bug_bounty_hunter": {"status": "active", "operations": 0},
                "backup_system": {"status": "active", "operations": 0},
                "communication": {"status": "active", "operations": 0}
            },
            "total_operations": 0,
            "total_value_generated": 0.0
        }

    def _save_state(self):
        """Save orchestrator state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_DIR.mkdir(exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    # ===== V1: MONEY PRINTER (Trading) =====

    def get_polymarket_markets(self, filters: Optional[Dict] = None) -> APICallResult:
        """Get active Polymarket markets."""
        params = filters or {}
        result = self.api_manager.call_api("polymarket_get_markets", params)

        if result.success:
            self.state["verticals"]["money_printer"]["operations"] += 1
            self.state["total_operations"] += 1
            self._save_state()

        return result

    def get_orderbook(self, token_id: str) -> APICallResult:
        """Get orderbook for a specific market."""
        result = self.api_manager.call_api(
            "polymarket_get_orderbook",
            {"token_id": token_id}
        )

        if result.success:
            self.state["verticals"]["money_printer"]["operations"] += 1
            self.state["total_operations"] += 1
            self._save_state()

        return result

    def place_order(
        self,
        market: str,
        side: str,
        price: float,
        size: float
    ) -> APICallResult:
        """Place a trading order on Polymarket."""
        result = self.api_manager.call_api(
            "polymarket_place_order",
            {
                "market": market,
                "side": side,
                "price": price,
                "size": size
            }
        )

        if result.success:
            self.state["verticals"]["money_printer"]["operations"] += 1
            self.state["total_operations"] += 1
            self.state["total_value_generated"] += result.data.get("expected_profit", 0)
            self._save_state()

        return result

    # ===== V2: GITHUB BOUNTY HUNTER =====

    def search_github_bounties(
        self,
        query: str = "label:bounty is:open",
        per_page: int = 30
    ) -> APICallResult:
        """Search for GitHub bounties."""
        result = self.api_manager.call_api(
            "github_search_issues",
            {
                "q": query,
                "per_page": per_page
            }
        )

        if result.success:
            self.state["verticals"]["bounty_hunter"]["operations"] += 1
            self.state["total_operations"] += 1
            self._save_state()

            # Parse and enrich bounties
            bounties = []
            for item in result.data.get("items", []):
                bounty = self._parse_github_bounty(item)
                bounties.append(bounty)

            result.data["parsed_bounties"] = bounties

        return result

    def _parse_github_bounty(self, issue: Dict) -> Dict:
        """Parse GitHub issue into bounty format."""
        # Extract bounty amount from labels or body
        amount = 0.0
        for label in issue.get("labels", []):
            label_name = label.get("name", "").lower()
            if "$" in label_name:
                # Try to extract amount
                try:
                    amount_str = label_name.split("$")[1].replace("k", "000").replace(",", "")
                    amount = float(amount_str)
                except:
                    pass

        return {
            "repo": issue["repository_url"].split("/")[-2:],
            "issue_number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "amount": amount,
            "state": issue["state"],
            "created_at": issue["created_at"],
            "labels": [l["name"] for l in issue.get("labels", [])]
        }

    def get_issue_details(
        self,
        owner: str,
        repo: str,
        issue_number: int
    ) -> APICallResult:
        """Get detailed info about a specific issue."""
        result = self.api_manager.call_api(
            "github_get_issue",
            {
                "owner": owner,
                "repo": repo,
                "issue_number": issue_number
            }
        )

        if result.success:
            self.state["verticals"]["bounty_hunter"]["operations"] += 1
            self.state["total_operations"] += 1
            self._save_state()

        return result

    def claim_bounty(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        message: str
    ) -> APICallResult:
        """Claim a bounty by commenting on the issue."""
        result = self.api_manager.call_api(
            "github_create_comment",
            {
                "owner": owner,
                "repo": repo,
                "issue_number": issue_number,
                "body": message
            }
        )

        if result.success:
            self.state["verticals"]["bounty_hunter"]["operations"] += 1
            self.state["total_operations"] += 1
            self._save_state()

        return result

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str
    ) -> APICallResult:
        """Create a pull request for a bounty."""
        result = self.api_manager.call_api(
            "github_create_pr",
            {
                "owner": owner,
                "repo": repo,
                "title": title,
                "head": head,
                "base": base,
                "body": body
            }
        )

        if result.success:
            self.state["verticals"]["bounty_hunter"]["operations"] += 1
            self.state["total_operations"] += 1
            self._save_state()

        return result

    # ===== V3: BUG BOUNTY HUNTER =====

    def list_bug_bounty_programs(self) -> APICallResult:
        """List available bug bounty programs."""
        result = self.api_manager.call_api(
            "hackerone_list_programs",
            {}
        )

        if result.success:
            self.state["verticals"]["bug_bounty_hunter"]["operations"] += 1
            self.state["total_operations"] += 1
            self._save_state()

        return result

    def submit_bug_report(
        self,
        program_id: str,
        title: str,
        vulnerability_info: str,
        severity: str = "medium",
        impact: str = ""
    ) -> APICallResult:
        """Submit a bug bounty report."""
        result = self.api_manager.call_api(
            "hackerone_submit_report",
            {
                "program_id": program_id,
                "title": title,
                "vulnerability_information": vulnerability_info,
                "severity": severity,
                "impact": impact
            }
        )

        if result.success:
            self.state["verticals"]["bug_bounty_hunter"]["operations"] += 1
            self.state["total_operations"] += 1
            self._save_state()

        return result

    # ===== INFRASTRUCTURE =====

    def check_wallet_balance(
        self,
        address: str,
        network: str = "ethereum"
    ) -> APICallResult:
        """Check crypto wallet balance."""
        api_map = {
            "ethereum": "etherscan_get_balance",
            "polygon": "polygonscan_get_balance"
        }

        api_name = api_map.get(network)
        if not api_name:
            return APICallResult(
                success=False,
                data=None,
                cost=0.0,
                duration=0.0,
                error=f"Unsupported network: {network}"
            )

        result = self.api_manager.call_api(
            api_name,
            {"address": address}
        )

        if result.success:
            self.state["total_operations"] += 1
            self._save_state()

        return result

    def send_notification(
        self,
        channel: str,
        message: str,
        **kwargs
    ) -> APICallResult:
        """Send notification via specified channel."""
        if channel == "telegram":
            return self.api_manager.call_api(
                "telegram_send_message",
                {
                    "chat_id": kwargs.get("chat_id", ""),
                    "text": message
                }
            )
        elif channel == "email":
            # Would integrate with email API
            return APICallResult(
                success=False,
                data=None,
                cost=0.0,
                duration=0.0,
                error="Email not yet implemented"
            )
        else:
            return APICallResult(
                success=False,
                data=None,
                cost=0.0,
                duration=0.0,
                error=f"Unknown channel: {channel}"
            )

    # ===== HIGH-LEVEL OPERATIONS =====

    def run_full_cycle(self) -> Dict[str, Any]:
        """Run a complete autonomous cycle across all verticals."""
        print("\n" + "=" * 80)
        print(f"🤖 AUTONOMOUS CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verticals": {}
        }

        # V1: Money Printer (check markets)
        print("\n🖨️  [V1: MONEY PRINTER]")
        markets_result = self.get_polymarket_markets()
        if markets_result.success:
            market_count = len(markets_result.data)
            print(f"✅ Found {market_count} active markets")
            results["verticals"]["money_printer"] = {
                "status": "success",
                "markets": market_count
            }
        else:
            print(f"❌ Failed: {markets_result.error}")
            results["verticals"]["money_printer"] = {
                "status": "failed",
                "error": markets_result.error
            }

        # V2: GitHub Bounty Hunter
        print("\n🎯 [V2: GITHUB BOUNTY HUNTER]")
        bounties_result = self.search_github_bounties()
        if bounties_result.success:
            bounty_count = len(bounties_result.data.get("parsed_bounties", []))
            print(f"✅ Found {bounty_count} bounties")
            results["verticals"]["bounty_hunter"] = {
                "status": "success",
                "bounties": bounty_count
            }
        else:
            print(f"❌ Failed: {bounties_result.error}")
            results["verticals"]["bounty_hunter"] = {
                "status": "failed",
                "error": bounties_result.error
            }

        # V3: Bug Bounty Hunter
        print("\n🔒 [V3: BUG BOUNTY HUNTER]")
        programs_result = self.list_bug_bounty_programs()
        if programs_result.success:
            print(f"✅ Tracking bug bounty programs")
            results["verticals"]["bug_bounty_hunter"] = {
                "status": "success"
            }
        else:
            print(f"⚠️  API not available (needs credentials)")
            results["verticals"]["bug_bounty_hunter"] = {
                "status": "no_credentials"
            }

        # Infrastructure checks
        print("\n💰 [INFRASTRUCTURE]")
        wallet = "0xB314345D218ED4CF75C17636a2307244E7dA761b"
        balance_result = self.check_wallet_balance(wallet, "ethereum")
        if balance_result.success:
            print(f"✅ Wallet balance checked")
            results["infrastructure"] = {"status": "success"}
        else:
            print(f"⚠️  {balance_result.error}")
            results["infrastructure"] = {"status": "limited"}

        print("\n" + "=" * 80)
        print("✅ Cycle complete")
        print("=" * 80)

        return results

    def get_system_status(self) -> Dict:
        """Get overall system status."""
        api_stats = self.api_manager.get_api_stats()

        return {
            "orchestrator": self.state,
            "api_manager": api_stats,
            "verticals": {
                "active": sum(
                    1 for v in self.state["verticals"].values()
                    if v["status"] == "active"
                ),
                "total": len(self.state["verticals"])
            }
        }

    def display_status(self):
        """Display orchestrator status."""
        print("=" * 80)
        print("🎯 API ORCHESTRATOR")
        print("=" * 80)
        print()

        print("🟢 ACTIVE VERTICALS:")
        print("-" * 80)
        for name, data in self.state["verticals"].items():
            status_icon = "✅" if data["status"] == "active" else "⏸️"
            print(f"  {status_icon} {name.replace('_', ' ').title()}")
            print(f"     Operations: {data['operations']}")
        print()

        print("📊 SYSTEM METRICS:")
        print("-" * 80)
        print(f"  Total Operations: {self.state['total_operations']}")
        print(f"  Total Value Generated: ${self.state['total_value_generated']:.2f}")
        print()

        api_stats = self.api_manager.get_api_stats()
        print("💰 API ECONOMICS:")
        print("-" * 80)
        print(f"  Total API Calls: {api_stats['total_calls']}")
        print(f"  Success Rate: {api_stats['success_rate']:.1%}")
        print(f"  Total Cost: ${api_stats['total_cost']:.4f}")
        print(f"  Net Value: ${api_stats['net_value']:.2f}")
        print()

        print("=" * 80)


def main():
    """Test orchestrator."""
    print("🚀 Initializing API Orchestrator...")
    print()

    orchestrator = APIOrchestrator()
    orchestrator.display_status()

    print("\n🎯 Running full autonomous cycle...")
    results = orchestrator.run_full_cycle()

    print("\n📊 Cycle Results:")
    print(json.dumps(results, indent=2))
    print()


if __name__ == "__main__":
    main()
