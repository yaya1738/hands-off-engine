#!/usr/bin/env python3
"""
GitHub Rate Limit Status Checker

Quick utility to check GitHub API rate limit status.
Shows remaining requests and when limits reset.

Usage:
    python3 scripts/github_ratelimit_status.py
    
Environment:
    GITHUB_TOKEN - Optional. If set, shows authenticated limits (5000/hour).
                   Without it, shows unauthenticated limits (60/hour).
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.github_client import GitHubClient


def format_timestamp(unix_ts: int) -> str:
    """Convert Unix timestamp to human-readable format."""
    dt = datetime.utcfromtimestamp(unix_ts)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def get_minutes_until_reset(unix_ts: int) -> int:
    """Get minutes until rate limit resets."""
    now = datetime.utcnow()
    reset = datetime.utcfromtimestamp(unix_ts)
    delta = reset - now
    return max(0, int(delta.total_seconds() / 60))


def main():
    """Check and display GitHub rate limit status."""
    print("\n" + "=" * 60)
    print("  GITHUB API RATE LIMIT STATUS")
    print("=" * 60 + "\n")
    
    # Check if token is set
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        # Mask token for display
        masked = token[:4] + "..." + token[-4:] if len(token) > 8 else "****"
        print(f"🔑 Token: {masked}")
    else:
        print("⚠️  No GITHUB_TOKEN set - using unauthenticated limits")
        print("   Run: export GITHUB_TOKEN=your_token_here")
    
    print()
    
    # Create client and get status
    client = GitHubClient()
    
    try:
        rate_info = client.get_rate_limit()
        
        # Core rate limit
        core = rate_info.get('rate', {})
        limit = core.get('limit', 0)
        remaining = core.get('remaining', 0)
        reset = core.get('reset', 0)
        used = limit - remaining
        pct_used = (used / limit * 100) if limit > 0 else 0
        
        # Format output
        print("📊 Core Rate Limit:")
        print(f"   Limit:     {limit:,} requests/hour")
        print(f"   Used:      {used:,} ({pct_used:.1f}%)")
        print(f"   Remaining: {remaining:,}")
        print(f"   Resets at: {format_timestamp(reset)}")
        print(f"   (in {get_minutes_until_reset(reset)} minutes)")
        
        # Status indicator
        print()
        if remaining == 0:
            print("🔴 RATE LIMITED - Wait for reset or use authenticated token")
            status_code = 2
        elif remaining < limit * 0.1:
            print("🟡 WARNING - Less than 10% remaining")
            status_code = 1
        else:
            print("🟢 OK - Sufficient requests available")
            status_code = 0
        
        # Show search rate limit if available
        resources = rate_info.get('resources', {})
        search = resources.get('search', {})
        if search:
            print()
            print("🔍 Search Rate Limit:")
            print(f"   Remaining: {search.get('remaining', 0)}/{search.get('limit', 0)}")
        
        # Authentication status
        print()
        if limit > 60:
            print("✅ Authenticated - 5000 requests/hour available")
        else:
            print("⚠️  Unauthenticated - Only 60 requests/hour")
            print("   To fix: export GITHUB_TOKEN=ghp_your_token")
        
        print()
        return status_code
        
    except Exception as e:
        print(f"❌ Error checking rate limit: {e}")
        print()
        print("Possible causes:")
        print("  - Network issues")
        print("  - Invalid GITHUB_TOKEN")
        print("  - GitHub API down")
        return 3


if __name__ == "__main__":
    sys.exit(main())
