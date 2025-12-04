#!/usr/bin/env python3
"""
API Manager with ABCFC Optimization
====================================

Intelligent API orchestration system that:
1. Routes API calls through optimal providers
2. Tracks costs and usage in real-time
3. Uses ABCFC to decide which APIs to call
4. Handles rate limiting and retries
5. Provides unified interface for all operations

Master: Yair Siegel
"Good ABCFC-age of the APIs"
"""

import json
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from integrafix.api_registry import APIRegistry, APIEndpoint

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"


@dataclass
class APICallResult:
    """Result of an API call."""
    success: bool
    data: Any
    cost: float
    duration: float
    error: Optional[str] = None
    abcfc_score: float = 0.0


class APIManager:
    """Intelligent API manager with ABCFC optimization."""

    def __init__(self):
        self.registry = APIRegistry()
        self.state_file = STATE_DIR / "api_manager.json"
        self.state = self._load_state()

        # Load API credentials from environment
        self.credentials = {
            "github": os.environ.get("GITHUB_TOKEN", ""),
            "polymarket": {
                "api_key": os.environ.get("POLYMARKET_API_KEY", ""),
                "api_secret": os.environ.get("POLYMARKET_API_SECRET", ""),
                "passphrase": os.environ.get("POLYMARKET_PASSPHRASE", "")
            },
            "hackerone": os.environ.get("HACKERONE_API_TOKEN", ""),
            "aws": {
                "access_key": os.environ.get("AWS_ACCESS_KEY_ID", ""),
                "secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "")
            },
            "telegram": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            "etherscan": os.environ.get("ETHERSCAN_API_KEY", ""),
            "polygonscan": os.environ.get("POLYGONSCAN_API_KEY", "")
        }

    def _load_state(self) -> Dict:
        """Load manager state."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_cost": 0.0,
            "total_value_generated": 0.0,
            "call_history": []
        }

    def _save_state(self):
        """Save manager state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_DIR.mkdir(exist_ok=True)
        # Keep only last 1000 calls in history
        if len(self.state["call_history"]) > 1000:
            self.state["call_history"] = self.state["call_history"][-1000:]
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def _get_auth_headers(self, api: APIEndpoint) -> Dict[str, str]:
        """Get authentication headers for an API."""
        headers = {}

        if api.auth_type == "bearer":
            if api.provider == "github":
                token = self.credentials.get("github", "")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
            elif api.provider == "telegram":
                # Token goes in URL for Telegram
                pass

        elif api.auth_type == "api_key":
            if api.provider == "polymarket":
                # Polymarket uses custom headers
                headers["CLOB-API-KEY"] = self.credentials["polymarket"]["api_key"]
            elif api.provider == "hackerone":
                headers["Authorization"] = f"Bearer {self.credentials.get('hackerone', '')}"
            elif api.provider in ["etherscan", "polygonscan"]:
                # API key goes in query params
                pass

        return headers

    def call_api(
        self,
        api_name: str,
        params: Dict[str, Any],
        force: bool = False
    ) -> APICallResult:
        """
        Call an API with ABCFC decision making.

        Args:
            api_name: Name of the API to call
            params: Parameters for the API call
            force: If True, skip ABCFC check and call anyway

        Returns:
            APICallResult with success status and data
        """
        api = self.registry.get_api(api_name)
        if not api:
            return APICallResult(
                success=False,
                data=None,
                cost=0.0,
                duration=0.0,
                error=f"API '{api_name}' not found in registry"
            )

        # Check if API is enabled
        if not api.enabled:
            return APICallResult(
                success=False,
                data=None,
                cost=0.0,
                duration=0.0,
                error=f"API '{api_name}' is disabled"
            )

        # Calculate ABCFC score
        abcfc_score = self.registry.calculate_abcfc_score(api)

        # Decision gate: Only call if ABCFC score is positive (unless forced)
        if not force and abcfc_score < 0:
            return APICallResult(
                success=False,
                data=None,
                cost=0.0,
                duration=0.0,
                error=f"ABCFC score too low: {abcfc_score:.2f}",
                abcfc_score=abcfc_score
            )

        # Make the API call
        start_time = time.time()
        try:
            result = self._execute_api_call(api, params)
            duration = time.time() - start_time

            # Record success
            self.registry.record_api_call(api_name, success=True, cost=api.cost_per_call)

            # Update state
            self.state["total_calls"] += 1
            self.state["successful_calls"] += 1
            self.state["total_cost"] += api.cost_per_call
            self.state["total_value_generated"] += api.expected_value
            self.state["call_history"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "api": api_name,
                "success": True,
                "cost": api.cost_per_call,
                "duration": duration,
                "abcfc_score": abcfc_score
            })
            self._save_state()

            return APICallResult(
                success=True,
                data=result,
                cost=api.cost_per_call,
                duration=duration,
                abcfc_score=abcfc_score
            )

        except Exception as e:
            duration = time.time() - start_time

            # Record failure
            self.registry.record_api_call(api_name, success=False)

            # Update state
            self.state["total_calls"] += 1
            self.state["failed_calls"] += 1
            self.state["call_history"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "api": api_name,
                "success": False,
                "error": str(e),
                "duration": duration,
                "abcfc_score": abcfc_score
            })
            self._save_state()

            return APICallResult(
                success=False,
                data=None,
                cost=0.0,
                duration=duration,
                error=str(e),
                abcfc_score=abcfc_score
            )

    def _execute_api_call(self, api: APIEndpoint, params: Dict[str, Any]) -> Any:
        """Execute the actual API call."""
        # Build URL
        url = api.url_template
        for key, value in params.items():
            url = url.replace(f"{{{key}}}", str(value))

        # Get auth headers
        headers = self._get_auth_headers(api)
        headers["User-Agent"] = "hands-off-engine/1.0"

        # Add query params for GET requests
        query_params = {}
        if api.method == "GET":
            for key, value in params.items():
                if f"{{{key}}}" not in api.url_template:
                    query_params[key] = value

        # Make request
        if api.method == "GET":
            response = requests.get(url, headers=headers, params=query_params, timeout=30)
        elif api.method == "POST":
            # Extract body params
            body_data = {k: v for k, v in params.items() if f"{{{k}}}" not in api.url_template}
            response = requests.post(url, headers=headers, json=body_data, timeout=30)
        elif api.method == "PUT":
            body_data = {k: v for k, v in params.items() if f"{{{k}}}" not in api.url_template}
            response = requests.put(url, headers=headers, json=body_data, timeout=30)
        elif api.method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {api.method}")

        # Check response
        response.raise_for_status()

        # Parse response
        if api.response_format == "json":
            return response.json()
        else:
            return response.text

    def call_best_api(
        self,
        category: str,
        operation: str,
        params: Dict[str, Any]
    ) -> APICallResult:
        """
        Call the best API for a given operation based on ABCFC score.

        Args:
            category: API category (trading, github, security, etc.)
            operation: Type of operation (search, create, update, etc.)
            params: Parameters for the API call

        Returns:
            APICallResult from the best API
        """
        # Get all APIs in category
        category_apis = self.registry.get_apis_by_category(category)

        if not category_apis:
            return APICallResult(
                success=False,
                data=None,
                cost=0.0,
                duration=0.0,
                error=f"No APIs found for category: {category}"
            )

        # Filter by operation (in API name or description)
        matching_apis = [
            api for api in category_apis
            if operation.lower() in api.name.lower() or operation.lower() in api.description.lower()
        ]

        if not matching_apis:
            return APICallResult(
                success=False,
                data=None,
                cost=0.0,
                duration=0.0,
                error=f"No APIs found for operation: {operation} in category: {category}"
            )

        # Calculate ABCFC scores and sort
        api_scores = [
            (api, self.registry.calculate_abcfc_score(api))
            for api in matching_apis
        ]
        api_scores.sort(key=lambda x: x[1], reverse=True)

        # Try APIs in order of ABCFC score
        for api, score in api_scores:
            result = self.call_api(api.name, params)
            if result.success:
                return result

        # All failed
        return APICallResult(
            success=False,
            data=None,
            cost=0.0,
            duration=0.0,
            error=f"All APIs failed for operation: {operation}"
        )

    def batch_call(
        self,
        calls: List[Dict[str, Any]],
        max_parallel: int = 5
    ) -> List[APICallResult]:
        """
        Make multiple API calls with ABCFC optimization.

        Args:
            calls: List of dicts with 'api_name' and 'params'
            max_parallel: Maximum parallel calls

        Returns:
            List of APICallResult
        """
        # Sort calls by ABCFC score
        call_scores = []
        for call in calls:
            api = self.registry.get_api(call["api_name"])
            if api:
                score = self.registry.calculate_abcfc_score(api)
                call_scores.append((call, score))

        call_scores.sort(key=lambda x: x[1], reverse=True)

        # Execute calls (for now, sequentially)
        results = []
        for call, score in call_scores:
            result = self.call_api(call["api_name"], call["params"])
            results.append(result)

        return results

    def get_api_stats(self) -> Dict:
        """Get API manager statistics."""
        success_rate = (
            self.state["successful_calls"] / self.state["total_calls"]
            if self.state["total_calls"] > 0
            else 0
        )

        roi = (
            (self.state["total_value_generated"] - self.state["total_cost"]) / self.state["total_cost"]
            if self.state["total_cost"] > 0
            else float('inf')
        )

        return {
            "total_calls": self.state["total_calls"],
            "successful_calls": self.state["successful_calls"],
            "failed_calls": self.state["failed_calls"],
            "success_rate": success_rate,
            "total_cost": self.state["total_cost"],
            "total_value_generated": self.state["total_value_generated"],
            "net_value": self.state["total_value_generated"] - self.state["total_cost"],
            "roi": roi
        }

    def display_status(self):
        """Display API manager status."""
        print("=" * 80)
        print("🎯 API MANAGER")
        print("=" * 80)
        print()

        stats = self.get_api_stats()

        print("📊 PERFORMANCE:")
        print("-" * 80)
        print(f"  Total API Calls: {stats['total_calls']}")
        print(f"  Successful: {stats['successful_calls']}")
        print(f"  Failed: {stats['failed_calls']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")
        print()

        print("💰 ECONOMICS:")
        print("-" * 80)
        print(f"  Total Cost: ${stats['total_cost']:.4f}")
        print(f"  Total Value Generated: ${stats['total_value_generated']:.2f}")
        print(f"  Net Value: ${stats['net_value']:.2f}")
        if stats['roi'] != float('inf'):
            print(f"  ROI: {stats['roi']:.1f}x")
        else:
            print(f"  ROI: ∞ (zero cost)")
        print()

        print("📈 RECENT CALLS:")
        print("-" * 80)
        recent = self.state["call_history"][-5:]
        if recent:
            for call in recent:
                status = "✅" if call["success"] else "❌"
                print(f"  {status} {call['api']}")
                print(f"     Time: {call['timestamp'][:19]}")
                print(f"     Duration: {call['duration']:.2f}s")
                if "abcfc_score" in call:
                    print(f"     ABCFC Score: {call['abcfc_score']:.2f}")
                if "error" in call:
                    print(f"     Error: {call['error']}")
                print()
        else:
            print("  No calls yet")

        print("=" * 80)


def main():
    """Test API manager."""
    print("Initializing API Manager...")
    print()

    manager = APIManager()
    manager.display_status()

    print()
    print("🧪 TESTING API CALLS:")
    print("-" * 80)

    # Test GitHub search (if token available)
    if manager.credentials.get("github"):
        print("\n1. Testing GitHub search for bounties...")
        result = manager.call_api(
            "github_search_issues",
            {
                "q": "label:bounty is:open",
                "per_page": 5
            }
        )
        if result.success:
            print(f"   ✅ Found {len(result.data.get('items', []))} issues")
            print(f"   Cost: ${result.cost:.4f}, Duration: {result.duration:.2f}s")
            print(f"   ABCFC Score: {result.abcfc_score:.2f}")
        else:
            print(f"   ❌ Failed: {result.error}")
    else:
        print("\n1. Skipping GitHub test (no token)")

    # Test best API selection
    print("\n2. Testing best API selection...")
    print("   Finding best 'search' API in 'github' category...")
    best_apis = manager.registry.get_best_apis(category="github", limit=3)
    for i, api in enumerate(best_apis, 1):
        print(f"   {i}. {api['name']} (Score: {api['abcfc_score']:.2f})")

    print()
    print("✅ API Manager ready!")
    print()


if __name__ == "__main__":
    main()
