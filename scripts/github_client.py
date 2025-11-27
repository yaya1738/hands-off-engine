#!/usr/bin/env python3
"""
GitHub API Client with Authentication and Rate Limiting

Provides a reusable GitHub API client with:
- Personal Access Token (PAT) authentication
- Rate limit awareness and handling
- Automatic retries with exponential backoff
- Proper error handling

Usage:
    from github_client import GitHubClient
    
    client = GitHubClient()  # Uses GITHUB_TOKEN from environment
    rate_info = client.get_rate_limit()
    print(f"Remaining: {rate_info['remaining']}/{rate_info['limit']}")
"""

import os
import sys
import time
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class RateLimitInfo:
    """GitHub API rate limit information."""
    limit: int
    remaining: int
    reset_timestamp: int
    used: int
    
    @property
    def reset_in_seconds(self) -> int:
        """Seconds until rate limit resets."""
        return max(0, self.reset_timestamp - int(time.time()))
    
    @property
    def is_exhausted(self) -> bool:
        """True if rate limit is exhausted."""
        return self.remaining == 0


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""
    pass


class GitHubAuthError(GitHubClientError):
    """Authentication error (invalid or missing token)."""
    pass


class GitHubRateLimitError(GitHubClientError):
    """Rate limit exceeded error."""
    def __init__(self, message: str, reset_in: int):
        super().__init__(message)
        self.reset_in = reset_in


class GitHubClient:
    """
    Authenticated GitHub API client with rate limiting and retries.
    
    Args:
        token: GitHub Personal Access Token. If None, uses GITHUB_TOKEN env var.
        base_url: GitHub API base URL (default: https://api.github.com)
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Exponential backoff multiplier (default: 2)
    
    Raises:
        GitHubAuthError: If no token is provided or found in environment.
    """
    
    DEFAULT_BASE_URL = "https://api.github.com"
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 2
    
    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    ):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise GitHubAuthError(
                "No GitHub token provided. Set GITHUB_TOKEN environment variable "
                "or pass token to GitHubClient constructor."
            )
        
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._last_rate_limit: Optional[RateLimitInfo] = None
    
    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the GitHub API.
        
        Args:
            endpoint: API endpoint (e.g., "/rate_limit")
            method: HTTP method
            data: Request body data (will be JSON encoded)
            headers: Additional headers
        
        Returns:
            Parsed JSON response
        
        Raises:
            GitHubAuthError: On authentication failure
            GitHubRateLimitError: When rate limit is exceeded
            GitHubClientError: On other API errors
        """
        url = f"{self.base_url}{endpoint}"
        
        req_headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "hands-off-engine-github-client",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if headers:
            req_headers.update(headers)
        
        body = None
        if data:
            body = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        
        request = Request(url, data=body, headers=req_headers, method=method)
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                with urlopen(request, timeout=30) as response:
                    # Update cached rate limit info from headers
                    self._update_rate_limit_from_headers(response.headers)
                    
                    content = response.read().decode("utf-8")
                    if content:
                        return json.loads(content)
                    return {}
                    
            except HTTPError as e:
                if e.code == 401:
                    raise GitHubAuthError(
                        "GitHub authentication failed. Check your token."
                    )
                elif e.code == 403:
                    # Check if it's rate limiting
                    remaining = e.headers.get("X-RateLimit-Remaining", "1")
                    if remaining == "0":
                        reset = int(e.headers.get("X-RateLimit-Reset", "0"))
                        reset_in = max(0, reset - int(time.time()))
                        raise GitHubRateLimitError(
                            f"GitHub API rate limit exceeded. Resets in {reset_in}s.",
                            reset_in=reset_in
                        )
                    raise GitHubClientError(f"GitHub API forbidden: {e}")
                elif e.code == 404:
                    raise GitHubClientError(f"GitHub API resource not found: {endpoint}")
                elif e.code >= 500:
                    # Server error - retry with backoff
                    last_error = e
                    wait_time = self.backoff_factor ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    raise GitHubClientError(f"GitHub API error {e.code}: {e}")
                    
            except URLError as e:
                # Network error - retry with backoff
                last_error = e
                wait_time = self.backoff_factor ** attempt
                time.sleep(wait_time)
                continue
        
        raise GitHubClientError(f"Request failed after {self.max_retries} retries: {last_error}")
    
    def _update_rate_limit_from_headers(self, headers) -> None:
        """Update cached rate limit info from response headers."""
        try:
            self._last_rate_limit = RateLimitInfo(
                limit=int(headers.get("X-RateLimit-Limit", 0)),
                remaining=int(headers.get("X-RateLimit-Remaining", 0)),
                reset_timestamp=int(headers.get("X-RateLimit-Reset", 0)),
                used=int(headers.get("X-RateLimit-Used", 0))
            )
        except (ValueError, TypeError):
            pass  # Ignore header parsing errors
    
    def get_rate_limit(self) -> RateLimitInfo:
        """
        Get current API rate limit status.
        
        Returns:
            RateLimitInfo with current rate limit details
        """
        response = self._make_request("/rate_limit")
        core = response.get("resources", {}).get("core", {})
        
        return RateLimitInfo(
            limit=core.get("limit", 0),
            remaining=core.get("remaining", 0),
            reset_timestamp=core.get("reset", 0),
            used=core.get("used", 0)
        )
    
    def get_user(self) -> Dict[str, Any]:
        """
        Get authenticated user info.
        
        Returns:
            User information dict
        """
        return self._make_request("/user")
    
    def is_authenticated(self) -> bool:
        """
        Check if the client is properly authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        try:
            self.get_user()
            return True
        except GitHubAuthError:
            return False
        except GitHubClientError:
            return False
    
    @property
    def cached_rate_limit(self) -> Optional[RateLimitInfo]:
        """Return the last cached rate limit info, or None if not yet fetched."""
        return self._last_rate_limit


def check_github_auth() -> bool:
    """
    Quick check if GitHub authentication is working.
    
    Returns:
        True if authenticated, False otherwise
    """
    try:
        client = GitHubClient()
        return client.is_authenticated()
    except GitHubAuthError:
        return False


def main():
    """Command-line interface for GitHub client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub API Client")
    parser.add_argument(
        "--check-auth",
        action="store_true",
        help="Check if GitHub authentication is working"
    )
    parser.add_argument(
        "--rate-limit",
        action="store_true",
        help="Show current rate limit status"
    )
    parser.add_argument(
        "--user",
        action="store_true",
        help="Show authenticated user info"
    )
    
    args = parser.parse_args()
    
    try:
        client = GitHubClient()
        
        if args.check_auth:
            if client.is_authenticated():
                print("✓ GitHub authentication successful")
                sys.exit(0)
            else:
                print("✗ GitHub authentication failed")
                sys.exit(1)
        
        elif args.rate_limit:
            info = client.get_rate_limit()
            print(f"Rate Limit: {info.remaining}/{info.limit}")
            print(f"Used: {info.used}")
            print(f"Resets in: {info.reset_in_seconds}s")
            sys.exit(0)
        
        elif args.user:
            user = client.get_user()
            print(f"Login: {user.get('login')}")
            print(f"Name: {user.get('name')}")
            print(f"Email: {user.get('email')}")
            sys.exit(0)
        
        else:
            # Default: show rate limit
            info = client.get_rate_limit()
            print(f"Rate Limit: {info.remaining}/{info.limit}")
            sys.exit(0)
            
    except GitHubAuthError as e:
        print(f"Auth Error: {e}", file=sys.stderr)
        sys.exit(1)
    except GitHubClientError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
