#!/usr/bin/env python3
"""
GitHub Rate Limit Status Checker

Shows current GitHub API rate limit status:
- Whether authenticated or unauthenticated
- Remaining requests
- Reset time
"""
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_rate_limit(token: Optional[str] = None) -> dict:
    """
    Fetch GitHub API rate limit information.
    
    Args:
        token: Optional GitHub token. If None, uses GITHUB_TOKEN from env.
        
    Returns:
        Dict with rate limit info or error details
    """
    token = token or os.environ.get("GITHUB_TOKEN")
    
    url = "https://api.github.com/rate_limit"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Hands-Off-Engine-RateLimit-Checker",
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {
                "success": True,
                "authenticated": token is not None,
                "resources": data.get("resources", {}),
            }
    except HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP {e.code}: {e.reason}",
            "authenticated": token is not None,
        }
    except URLError as e:
        return {
            "success": False,
            "error": f"Network error: {e.reason}",
            "authenticated": token is not None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "authenticated": token is not None,
        }


def format_reset_time(reset_timestamp: int) -> str:
    """Format Unix timestamp to human-readable time remaining."""
    reset_dt = datetime.fromtimestamp(reset_timestamp, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    
    if reset_dt <= now:
        return "now (refreshed)"
    
    delta = reset_dt - now
    minutes = int(delta.total_seconds() // 60)
    seconds = int(delta.total_seconds() % 60)
    
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def print_rate_limit_status(result: dict) -> None:
    """Print rate limit status in a readable format."""
    print("=" * 50)
    print("  GITHUB API RATE LIMIT STATUS")
    print("=" * 50)
    print()
    
    if not result.get("success"):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        print()
        return
    
    auth_status = "✅ Authenticated" if result["authenticated"] else "⚠️  Unauthenticated"
    print(f"Auth Status: {auth_status}")
    print()
    
    resources = result.get("resources", {})
    
    # Core API (most important)
    core = resources.get("core", {})
    core_limit = core.get("limit", 0)
    core_remaining = core.get("remaining", 0)
    core_reset = core.get("reset", 0)
    core_used = core_limit - core_remaining
    
    print("Core API:")
    print(f"  Limit:     {core_limit:,} requests/hour")
    print(f"  Remaining: {core_remaining:,} requests")
    print(f"  Used:      {core_used:,} requests")
    if core_reset:
        print(f"  Resets in: {format_reset_time(core_reset)}")
    print()
    
    # Expected vs actual limit
    expected_limit = 5000 if result["authenticated"] else 60
    if core_limit == expected_limit:
        print(f"✅ Rate limit is correct for {'authenticated' if result['authenticated'] else 'unauthenticated'} access")
    else:
        print(f"⚠️  Unexpected rate limit: {core_limit} (expected {expected_limit})")
        if result["authenticated"] and core_limit == 60:
            print("   Token may be invalid or expired")
    print()
    
    # Search API
    search = resources.get("search", {})
    if search:
        search_remaining = search.get("remaining", 0)
        search_limit = search.get("limit", 0)
        print(f"Search API: {search_remaining}/{search_limit} remaining")
    
    # GraphQL API
    graphql = resources.get("graphql", {})
    if graphql:
        graphql_remaining = graphql.get("remaining", 0)
        graphql_limit = graphql.get("limit", 0)
        print(f"GraphQL:    {graphql_remaining}/{graphql_limit} remaining")
    
    print()
    print("=" * 50)


def main() -> int:
    """Main entry point."""
    result = get_rate_limit()
    print_rate_limit_status(result)
    
    if not result.get("success"):
        return 1
    
    # Return non-zero if unauthenticated (to catch configuration issues)
    if not result.get("authenticated"):
        print("💡 Tip: Set GITHUB_TOKEN to get 5000 requests/hour")
        print("   Run: ./scripts/setup_github_token.sh")
        print()
        return 2
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
