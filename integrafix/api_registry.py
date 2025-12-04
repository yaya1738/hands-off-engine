#!/usr/bin/env python3
"""
API Registry System
===================

Central registry of ALL APIs available to the system.
Tracks capabilities, costs, rate limits, and ABCFC scores.

Master: Yair Siegel
"We can do anything, it's just about what's worth our time"
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
CONFIG_DIR = PROJECT_ROOT / "config"


@dataclass
class APIEndpoint:
    """Represents a single API endpoint."""
    name: str
    provider: str
    category: str  # trading, github, security, infrastructure, communication
    method: str  # GET, POST, PUT, DELETE
    url_template: str
    auth_type: str  # bearer, api_key, oauth, none

    # ABCFC factors
    cost_per_call: float  # in dollars
    rate_limit_per_hour: int
    success_probability: float
    expected_value: float  # Expected value this API provides

    # Metadata
    description: str
    required_params: List[str]
    optional_params: List[str]
    response_format: str

    # Status
    enabled: bool = True
    last_used: Optional[str] = None
    total_calls: int = 0
    failed_calls: int = 0


class APIRegistry:
    """Central registry for all APIs."""

    def __init__(self):
        self.registry_file = CONFIG_DIR / "api_registry.json"
        self.state_file = STATE_DIR / "api_registry_state.json"

        self.apis: Dict[str, APIEndpoint] = {}
        self.state = self._load_state()

        self._initialize_apis()

    def _load_state(self) -> Dict:
        """Load API usage state."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_api_calls": 0,
            "total_cost": 0.0,
            "apis": {}
        }

    def _save_state(self):
        """Save API usage state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_DIR.mkdir(exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def _initialize_apis(self):
        """Initialize all available APIs."""

        # ===== TRADING APIs =====
        self._register_api(APIEndpoint(
            name="polymarket_get_markets",
            provider="polymarket",
            category="trading",
            method="GET",
            url_template="https://clob.polymarket.com/markets",
            auth_type="api_key",
            cost_per_call=0.0,  # Free
            rate_limit_per_hour=1000,
            success_probability=0.99,
            expected_value=10.0,  # Value of market data
            description="Get all active Polymarket markets",
            required_params=[],
            optional_params=["closed", "archived"],
            response_format="json"
        ))

        self._register_api(APIEndpoint(
            name="polymarket_place_order",
            provider="polymarket",
            category="trading",
            method="POST",
            url_template="https://clob.polymarket.com/order",
            auth_type="api_key",
            cost_per_call=0.01,  # Gas fees
            rate_limit_per_hour=100,
            success_probability=0.95,
            expected_value=5.0,  # Expected profit per order
            description="Place a limit order on Polymarket",
            required_params=["market", "side", "price", "size"],
            optional_params=["expiration"],
            response_format="json"
        ))

        self._register_api(APIEndpoint(
            name="polymarket_get_orderbook",
            provider="polymarket",
            category="trading",
            method="GET",
            url_template="https://clob.polymarket.com/book",
            auth_type="api_key",
            cost_per_call=0.0,
            rate_limit_per_hour=2000,
            success_probability=0.99,
            expected_value=15.0,  # Value of orderbook data
            description="Get orderbook for a specific market",
            required_params=["token_id"],
            optional_params=[],
            response_format="json"
        ))

        # ===== GITHUB APIs =====
        self._register_api(APIEndpoint(
            name="github_search_issues",
            provider="github",
            category="github",
            method="GET",
            url_template="https://api.github.com/search/issues",
            auth_type="bearer",
            cost_per_call=0.0,  # Free
            rate_limit_per_hour=30,  # Authenticated
            success_probability=0.98,
            expected_value=100.0,  # Value of finding bounties
            description="Search GitHub issues (for bounties)",
            required_params=["q"],
            optional_params=["sort", "order", "per_page"],
            response_format="json"
        ))

        self._register_api(APIEndpoint(
            name="github_get_issue",
            provider="github",
            category="github",
            method="GET",
            url_template="https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
            auth_type="bearer",
            cost_per_call=0.0,
            rate_limit_per_hour=5000,
            success_probability=0.99,
            expected_value=10.0,
            description="Get details of a specific issue",
            required_params=["owner", "repo", "issue_number"],
            optional_params=[],
            response_format="json"
        ))

        self._register_api(APIEndpoint(
            name="github_create_comment",
            provider="github",
            category="github",
            method="POST",
            url_template="https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
            auth_type="bearer",
            cost_per_call=0.0,
            rate_limit_per_hour=5000,
            success_probability=0.99,
            expected_value=50.0,  # Value of claiming bounty
            description="Post a comment on an issue (claim bounty)",
            required_params=["owner", "repo", "issue_number", "body"],
            optional_params=[],
            response_format="json"
        ))

        self._register_api(APIEndpoint(
            name="github_list_prs",
            provider="github",
            category="github",
            method="GET",
            url_template="https://api.github.com/repos/{owner}/{repo}/pulls",
            auth_type="bearer",
            cost_per_call=0.0,
            rate_limit_per_hour=5000,
            success_probability=0.99,
            expected_value=5.0,
            description="List pull requests for a repo",
            required_params=["owner", "repo"],
            optional_params=["state", "sort"],
            response_format="json"
        ))

        self._register_api(APIEndpoint(
            name="github_create_pr",
            provider="github",
            category="github",
            method="POST",
            url_template="https://api.github.com/repos/{owner}/{repo}/pulls",
            auth_type="bearer",
            cost_per_call=0.0,
            rate_limit_per_hour=5000,
            success_probability=0.95,
            expected_value=500.0,  # Expected bounty value
            description="Create a pull request",
            required_params=["owner", "repo", "title", "head", "base"],
            optional_params=["body"],
            response_format="json"
        ))

        # ===== SECURITY APIs (Bug Bounty) =====
        self._register_api(APIEndpoint(
            name="hackerone_list_programs",
            provider="hackerone",
            category="security",
            method="GET",
            url_template="https://api.hackerone.com/v1/hackers/programs",
            auth_type="api_key",
            cost_per_call=0.0,
            rate_limit_per_hour=100,
            success_probability=0.95,
            expected_value=200.0,  # Value of program discovery
            description="List available bug bounty programs",
            required_params=[],
            optional_params=["page"],
            response_format="json"
        ))

        self._register_api(APIEndpoint(
            name="hackerone_submit_report",
            provider="hackerone",
            category="security",
            method="POST",
            url_template="https://api.hackerone.com/v1/hackers/reports",
            auth_type="api_key",
            cost_per_call=0.0,
            rate_limit_per_hour=10,
            success_probability=0.60,  # Lower - depends on finding quality
            expected_value=2000.0,  # Average bounty value
            description="Submit a vulnerability report",
            required_params=["program_id", "title", "vulnerability_information"],
            optional_params=["severity", "impact"],
            response_format="json"
        ))

        # ===== INFRASTRUCTURE APIs =====
        self._register_api(APIEndpoint(
            name="aws_s3_upload",
            provider="aws",
            category="infrastructure",
            method="PUT",
            url_template="https://s3.amazonaws.com/{bucket}/{key}",
            auth_type="aws_sig",
            cost_per_call=0.0001,  # Storage cost
            rate_limit_per_hour=10000,
            success_probability=0.99,
            expected_value=1.0,  # Value of backup
            description="Upload file to S3 bucket",
            required_params=["bucket", "key", "data"],
            optional_params=["metadata"],
            response_format="json"
        ))

        self._register_api(APIEndpoint(
            name="cloudflare_dns_update",
            provider="cloudflare",
            category="infrastructure",
            method="PUT",
            url_template="https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}",
            auth_type="bearer",
            cost_per_call=0.0,
            rate_limit_per_hour=1200,
            success_probability=0.99,
            expected_value=5.0,  # Value of DNS management
            description="Update DNS record",
            required_params=["zone_id", "dns_record_id", "type", "name", "content"],
            optional_params=["ttl", "proxied"],
            response_format="json"
        ))

        # ===== COMMUNICATION APIs =====
        self._register_api(APIEndpoint(
            name="email_send_smtp",
            provider="gmail",
            category="communication",
            method="POST",
            url_template="smtp://smtp.gmail.com:587",
            auth_type="password",
            cost_per_call=0.0,
            rate_limit_per_hour=100,
            success_probability=0.98,
            expected_value=10.0,  # Value of communication
            description="Send email via SMTP",
            required_params=["to", "subject", "body"],
            optional_params=["cc", "bcc", "attachments"],
            response_format="status"
        ))

        self._register_api(APIEndpoint(
            name="telegram_send_message",
            provider="telegram",
            category="communication",
            method="POST",
            url_template="https://api.telegram.org/bot{token}/sendMessage",
            auth_type="bearer",
            cost_per_call=0.0,
            rate_limit_per_hour=30,
            success_probability=0.99,
            expected_value=5.0,
            description="Send Telegram message",
            required_params=["chat_id", "text"],
            optional_params=["parse_mode"],
            response_format="json"
        ))

        # ===== CRYPTO APIs =====
        self._register_api(APIEndpoint(
            name="etherscan_get_balance",
            provider="etherscan",
            category="crypto",
            method="GET",
            url_template="https://api.etherscan.io/api",
            auth_type="api_key",
            cost_per_call=0.0,
            rate_limit_per_hour=5,  # Free tier
            success_probability=0.99,
            expected_value=10.0,
            description="Get wallet balance from Ethereum",
            required_params=["address"],
            optional_params=["tag"],
            response_format="json"
        ))

        self._register_api(APIEndpoint(
            name="polygonscan_get_balance",
            provider="polygonscan",
            category="crypto",
            method="GET",
            url_template="https://api.polygonscan.com/api",
            auth_type="api_key",
            cost_per_call=0.0,
            rate_limit_per_hour=5,
            success_probability=0.99,
            expected_value=10.0,
            description="Get wallet balance from Polygon",
            required_params=["address"],
            optional_params=["tag"],
            response_format="json"
        ))

    def _register_api(self, api: APIEndpoint):
        """Register an API in the registry."""
        self.apis[api.name] = api

        # Initialize state if needed
        if api.name not in self.state["apis"]:
            self.state["apis"][api.name] = {
                "total_calls": 0,
                "failed_calls": 0,
                "total_cost": 0.0,
                "last_used": None,
                "abcfc_score": 0.0
            }

    def get_api(self, name: str) -> Optional[APIEndpoint]:
        """Get API by name."""
        return self.apis.get(name)

    def get_apis_by_category(self, category: str) -> List[APIEndpoint]:
        """Get all APIs in a category."""
        return [api for api in self.apis.values() if api.category == category]

    def get_apis_by_provider(self, provider: str) -> List[APIEndpoint]:
        """Get all APIs from a provider."""
        return [api for api in self.apis.values() if api.provider == provider]

    def calculate_abcfc_score(self, api: APIEndpoint) -> float:
        """Calculate ABCFC score for an API call."""
        # Expected value considering success probability
        expected = api.expected_value * api.success_probability

        # Risk (cost of failure)
        worst_case = api.cost_per_call + 1.0  # Cost + wasted time (~$10/hr)
        risk_aversion = 0.3
        risk = risk_aversion * worst_case * (1 - api.success_probability)

        score = expected - risk
        return score

    def record_api_call(
        self,
        api_name: str,
        success: bool,
        cost: Optional[float] = None
    ):
        """Record an API call for tracking."""
        if api_name not in self.apis:
            return

        api = self.apis[api_name]
        api_state = self.state["apis"][api_name]

        # Update counts
        api_state["total_calls"] += 1
        if not success:
            api_state["failed_calls"] += 1

        # Update cost
        actual_cost = cost if cost is not None else api.cost_per_call
        api_state["total_cost"] += actual_cost
        self.state["total_cost"] += actual_cost

        # Update timestamp
        api_state["last_used"] = datetime.now(timezone.utc).isoformat()

        # Update ABCFC score
        api_state["abcfc_score"] = self.calculate_abcfc_score(api)

        # Update global
        self.state["total_api_calls"] += 1

        self._save_state()

    def get_api_stats(self, api_name: str) -> Dict:
        """Get statistics for an API."""
        if api_name not in self.state["apis"]:
            return {}

        api_state = self.state["apis"][api_name]
        api = self.apis[api_name]

        total_calls = api_state["total_calls"]
        failed_calls = api_state["failed_calls"]

        return {
            "name": api_name,
            "category": api.category,
            "provider": api.provider,
            "total_calls": total_calls,
            "failed_calls": failed_calls,
            "success_rate": (total_calls - failed_calls) / total_calls if total_calls > 0 else 0,
            "total_cost": api_state["total_cost"],
            "avg_cost": api_state["total_cost"] / total_calls if total_calls > 0 else 0,
            "abcfc_score": api_state["abcfc_score"],
            "last_used": api_state["last_used"]
        }

    def get_all_stats(self) -> Dict:
        """Get statistics for all APIs."""
        return {
            "total_api_calls": self.state["total_api_calls"],
            "total_cost": self.state["total_cost"],
            "apis": {name: self.get_api_stats(name) for name in self.apis.keys()}
        }

    def get_best_apis(self, category: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get best APIs by ABCFC score."""
        apis = self.apis.values()
        if category:
            apis = [api for api in apis if api.category == category]

        # Calculate scores
        api_scores = [
            {
                "name": api.name,
                "category": api.category,
                "provider": api.provider,
                "abcfc_score": self.calculate_abcfc_score(api),
                "cost_per_call": api.cost_per_call,
                "expected_value": api.expected_value,
                "success_probability": api.success_probability
            }
            for api in apis
        ]

        # Sort by ABCFC score
        api_scores.sort(key=lambda x: x["abcfc_score"], reverse=True)

        return api_scores[:limit]

    def export_registry(self) -> Dict:
        """Export full registry as JSON."""
        return {
            "apis": {
                name: asdict(api)
                for name, api in self.apis.items()
            },
            "stats": self.get_all_stats()
        }

    def display_status(self):
        """Display registry status."""
        print("=" * 80)
        print("📡 API REGISTRY")
        print("=" * 80)
        print()

        print("📊 GLOBAL STATS:")
        print("-" * 80)
        print(f"  Total APIs: {len(self.apis)}")
        print(f"  Total API Calls: {self.state['total_api_calls']}")
        print(f"  Total Cost: ${self.state['total_cost']:.4f}")
        print()

        print("📋 APIS BY CATEGORY:")
        print("-" * 80)
        categories = {}
        for api in self.apis.values():
            categories[api.category] = categories.get(api.category, 0) + 1

        for category, count in sorted(categories.items()):
            print(f"  {category}: {count} APIs")
        print()

        print("🏆 TOP 10 APIS (by ABCFC Score):")
        print("-" * 80)
        top_apis = self.get_best_apis(limit=10)
        for i, api in enumerate(top_apis, 1):
            print(f"  {i}. {api['name']}")
            print(f"     Category: {api['category']}, Provider: {api['provider']}")
            print(f"     ABCFC Score: {api['abcfc_score']:.2f}")
            print(f"     Cost: ${api['cost_per_call']:.4f}, Value: ${api['expected_value']:.2f}")
            print()

        print("=" * 80)


def main():
    """Test API registry."""
    print("Initializing API Registry...")
    print()

    registry = APIRegistry()
    registry.display_status()

    # Save registry to file
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(CONFIG_DIR / "api_registry.json", "w") as f:
        json.dump(registry.export_registry(), f, indent=2)

    print(f"✅ Registry saved to: {CONFIG_DIR / 'api_registry.json'}")
    print()


if __name__ == "__main__":
    main()
