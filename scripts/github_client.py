#!/usr/bin/env python3
"""
GitHub Client: Authenticated GitHub API Client

This module provides an authenticated GitHub API client with rate limit
handling and retry logic. It uses the GITHUB_TOKEN environment variable
for authentication.

Usage:
    from scripts.github_client import GitHubClient

    client = GitHubClient()
    rate_limit = client.get_rate_limit()
    print(f"Remaining: {rate_limit['rate']['remaining']}")
"""

import os
import sys
import time
import json
from typing import Dict, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class GitHubClient:
    """
    Authenticated GitHub API client with rate limit handling.
    
    Attributes:
        base_url: GitHub API base URL
        token: GitHub API token (from GITHUB_TOKEN env var)
        max_retries: Maximum number of retries for failed requests
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None, max_retries: int = 3):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub API token. If not provided, uses GITHUB_TOKEN env var.
            max_retries: Maximum number of retries for failed requests.
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.max_retries = max_retries
        
        if not self.token:
            print("WARNING: No GITHUB_TOKEN found. API rate limits will be restricted (60/hour).", 
                  file=sys.stderr)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Hands-Off-Engine/1.0"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _make_request(self, endpoint: str, method: str = "GET", 
                      data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated request to GitHub API.
        
        Args:
            endpoint: API endpoint (relative to base URL)
            method: HTTP method
            data: Request body data (for POST/PUT)
            
        Returns:
            Parsed JSON response
            
        Raises:
            HTTPError: If request fails after retries
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        body = None
        if data:
            body = json.dumps(data).encode('utf-8')
            headers["Content-Type"] = "application/json"
        
        for attempt in range(self.max_retries):
            try:
                req = Request(url, data=body, headers=headers, method=method)
                with urlopen(req, timeout=30) as response:
                    return json.loads(response.read().decode('utf-8'))
                    
            except HTTPError as e:
                # Check if it's a rate limit error
                if e.code == 403:
                    rate_reset = e.headers.get('X-RateLimit-Reset')
                    if rate_reset:
                        wait_time = int(rate_reset) - int(time.time())
                        if wait_time > 0 and wait_time < 300:  # Max 5 min wait
                            print(f"Rate limited. Waiting {wait_time}s...", file=sys.stderr)
                            time.sleep(wait_time + 1)
                            continue
                
                if attempt == self.max_retries - 1:
                    raise
                    
                # Exponential backoff
                wait = (2 ** attempt) + 1
                print(f"Request failed, retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                
            except URLError as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Rate limit info including:
            - rate.limit: Max requests per hour
            - rate.remaining: Requests remaining
            - rate.reset: Unix timestamp when limit resets
        """
        return self._make_request("/rate_limit")
    
    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        return self._make_request(f"/repos/{owner}/{repo}")
    
    def list_issues(self, owner: str, repo: str, 
                    state: str = "open", per_page: int = 30) -> list:
        """List repository issues."""
        return self._make_request(
            f"/repos/{owner}/{repo}/issues?state={state}&per_page={per_page}"
        )
    
    def list_pulls(self, owner: str, repo: str,
                   state: str = "open", per_page: int = 30) -> list:
        """List pull requests."""
        return self._make_request(
            f"/repos/{owner}/{repo}/pulls?state={state}&per_page={per_page}"
        )
    
    def is_authenticated(self) -> bool:
        """Check if client has valid authentication."""
        if not self.token:
            return False
        try:
            rate_info = self.get_rate_limit()
            # Authenticated users get 5000 requests/hour
            return rate_info.get('rate', {}).get('limit', 0) > 60
        except Exception:
            return False
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        Get detailed authentication status.
        
        Returns:
            Dict with:
            - authenticated: bool
            - rate_limit: int
            - remaining: int
            - reset_at: ISO timestamp
            - message: Human-readable status
        """
        try:
            rate_info = self.get_rate_limit()
            rate = rate_info.get('rate', {})
            limit = rate.get('limit', 0)
            remaining = rate.get('remaining', 0)
            reset = rate.get('reset', 0)
            
            from datetime import datetime
            reset_at = datetime.utcfromtimestamp(reset).isoformat() + "Z"
            
            authenticated = limit > 60
            
            if authenticated:
                message = f"✓ Authenticated: {remaining}/{limit} requests remaining"
            else:
                message = f"⚠ Unauthenticated: {remaining}/{limit} requests (set GITHUB_TOKEN)"
            
            return {
                "authenticated": authenticated,
                "rate_limit": limit,
                "remaining": remaining,
                "reset_at": reset_at,
                "message": message
            }
            
        except Exception as e:
            return {
                "authenticated": False,
                "rate_limit": 0,
                "remaining": 0,
                "reset_at": None,
                "message": f"✗ Failed to check status: {e}"
            }


def main():
    """CLI entry point for testing the client."""
    client = GitHubClient()
    status = client.get_auth_status()
    print(json.dumps(status, indent=2))
    return 0 if status["authenticated"] else 1


if __name__ == "__main__":
    sys.exit(main())
