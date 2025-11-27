#!/usr/bin/env python3
"""
GitHub Rate Limit Status Checker

Quick utility to check your GitHub API rate limit status.
Shows 5000/hour when authenticated (vs 60/hour when not).

Usage:
    python3 scripts/github_ratelimit_status.py
    
Environment:
    GITHUB_TOKEN - GitHub Personal Access Token (required)

Output Examples:
    Authenticated (good):
        ✓ GitHub API authenticated
        Rate Limit: 4892/5000
        Used: 108
        Resets in: 42 minutes
        
    Unauthenticated (bad):
        ✗ GitHub API NOT authenticated
        Rate Limit: 12/60
        (anonymous limit - very low!)
"""

import os
import sys
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime


def get_rate_limit_status() -> dict:
    """
    Get GitHub API rate limit status.
    
    Returns:
        dict with rate limit info and auth status
    """
    token = os.environ.get("GITHUB_TOKEN", "")
    
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "hands-off-engine-ratelimit-check",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    
    request = Request(
        "https://api.github.com/rate_limit",
        headers=headers
    )
    
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            core = data.get("resources", {}).get("core", {})
            
            limit = core.get("limit", 0)
            remaining = core.get("remaining", 0)
            used = core.get("used", 0)
            reset = core.get("reset", 0)
            
            # 5000 limit means authenticated, 60 means anonymous
            is_authenticated = limit >= 5000
            
            reset_dt = datetime.fromtimestamp(reset)
            now = datetime.now()
            reset_in_seconds = max(0, (reset_dt - now).total_seconds())
            reset_in_minutes = int(reset_in_seconds / 60)
            
            return {
                "authenticated": is_authenticated,
                "limit": limit,
                "remaining": remaining,
                "used": used,
                "reset_timestamp": reset,
                "reset_in_seconds": int(reset_in_seconds),
                "reset_in_minutes": reset_in_minutes,
                "token_configured": bool(token)
            }
            
    except HTTPError as e:
        return {
            "authenticated": False,
            "error": f"HTTP {e.code}: {e.reason}",
            "token_configured": bool(token)
        }
    except URLError as e:
        return {
            "authenticated": False,
            "error": f"Network error: {e.reason}",
            "token_configured": bool(token)
        }
    except Exception as e:
        return {
            "authenticated": False,
            "error": str(e),
            "token_configured": bool(token)
        }


def main():
    """Print rate limit status."""
    status = get_rate_limit_status()
    
    if "error" in status:
        print(f"✗ Error checking rate limit: {status['error']}")
        sys.exit(1)
    
    if status["authenticated"]:
        print("✓ GitHub API authenticated")
        print(f"Rate Limit: {status['remaining']}/{status['limit']}")
        print(f"Used: {status['used']}")
        print(f"Resets in: {status['reset_in_minutes']} minutes")
        sys.exit(0)
    else:
        print("✗ GitHub API NOT authenticated")
        if status.get("limit"):
            print(f"Rate Limit: {status['remaining']}/{status['limit']}")
            print("(anonymous limit - very low!)")
        if not status["token_configured"]:
            print("\nFix: Set GITHUB_TOKEN environment variable")
            print("See: docs/QUICK_GITHUB_FIX.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
